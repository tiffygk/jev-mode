"""Search the frozen package for words from the question sketch, before any batch decoder sees it.

Usage: python audit_package.py <questions.json> <package folder> [--allow word,word]
questions.json: {"id": {"type": "noul", "instructions": "..."},
                 "id2": {"type": "choice", "instructions": "...", "options": {"key": "description"}}}
Every hit is either reworded or removed, or allowed with --allow and a reason written in brief.md.
Matching strips one common suffix, so "romance" matches "romantic" but "related" does not match "relationship".
Field names from package/template.json are allowed automatically (questions have to name the state's fields);
category values are still checked. Exit code 1 if anything is found.
Standard library only.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from lenslib import load_json

STOP = set("""a about above after all also an and any are as at be been being between both but by can could
did do does each either for from had has have how i if in into is it its make may more most much no nor not
of on one or other our out over own same should so some such than that the their them then there these they
this those through to too two under up very was were what when where whether which while who whom why will
with would you your yes best guess likely most-likely based described scene image photo state people person
item items field fields none only just describe describes description visible anything something
kind kinds show shows shown contain contains any other others each need needs""".split())

SUFFIXES = ("ations", "ation", "ically", "ical", "ness", "ments", "ment", "ings", "ing", "tic", "ies", "ied",
            "ers", "er", "ed", "es", "ly", "ce", "al", "s", "e", "y")


def _words(text: str) -> list:
    text = re.sub(r"`[^`]*`", " ", text)  # backticked paths are pointers, not answers
    return [w for w in re.findall(r"[a-z][a-z'-]+", text.lower()) if len(w) > 2 and w not in STOP]


def answer_words(questions: dict) -> set:
    out = set()
    for q in questions.values():
        out.update(_words(str(q.get("instructions", ""))))
        for k, v in (q.get("options") or {}).items():
            out.update(_words(k.replace("_", " ")))
            out.update(_words(str(v)))
    return out


def _stem(w: str) -> str:
    for suf in SUFFIXES:
        if w.endswith(suf) and len(w) - len(suf) >= 4:
            return w[: -len(suf)]
    return w


def template_field_words(path) -> set:
    """Words in the template's section and field names (not its category values)."""
    p = Path(path)
    if not p.exists():
        return set()
    names = []
    for sec, spec in load_json(p).get("sections", {}).items():
        names += [sec] + list(spec.get("fields", {}))
    return {w for n in names for w in re.findall(r"[a-z]+", n.lower()) if len(w) > 2}


def audit(folder, words: set, allow: set = frozenset()) -> list:
    """[(file, line number, answer word, line text)] for every stem match in the package."""
    stems = {_stem(w): w for w in words if w not in allow}
    allow_stems = {_stem(w) for w in allow}
    hits = []
    root = Path(folder)
    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in (".md", ".json", ".txt"):
            continue
        for n, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            for tok in re.findall(r"[a-z][a-z'-]+", line.lower()):
                s = _stem(tok)
                if s in stems and s not in allow_stems:
                    hits.append((str(p.relative_to(root)), n, stems[s], line.strip()))
                    break
    return hits


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("questions"); ap.add_argument("package"); ap.add_argument("--allow", default="")
    a = ap.parse_args(argv[1:])
    words = answer_words(load_json(a.questions))
    allow = {w.strip().lower() for w in a.allow.split(",") if w.strip()}
    allow |= template_field_words(Path(a.package) / "template.json")
    print("Answer words:", ", ".join(sorted(words - allow)))
    hits = audit(a.package, words, allow)
    for f, n, w, line in hits:
        print(f"{f}:{n}  [{w}]  {line}")
    print(f"{len(hits)} hits" + ("" if hits else ": the package is clean"))
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
