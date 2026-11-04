"""Flag words that state gender, age or relationships in decodes, inventories or states.

Usage: python people_words.py <files or folders ...>
Decoders are told to describe people only by what is visible and to refer to them by ID,
but they slip ("the woman", "beside him"). Run this before the review and again on the state.
The user's labeled `context` block and the image's own words in `text` are exempt. Exit code 1 if anything is found.
Standard library only.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

WORDS = set("""
he him his himself she her hers herself
man men woman women male female boy boys girl girls lady ladies gentleman gentlemen guy guys gal
mr mrs ms miss sir madam
young younger old older elderly teen teenage teenager adult child children kid kids baby toddler
aged middle-aged youthful
husband wife spouse partner boyfriend girlfriend couple couples dating lover lovers
mother father mom dad mum son daughter brother sister sibling siblings family
friend friends colleague colleagues coworker coworkers boss girlish boyish feminine masculine
""".split())


def _strings(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if path == "" and k in ("context", "text"):
                continue  # context is user-supplied and sourced; text is copied from the image word for word
            yield from _strings(v, f"{path}.{k}" if path else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _strings(v, f"{path}[{i}]")
    elif isinstance(obj, str):
        yield path, obj


def scan(paths) -> list:
    """[(file, field path, word, text)] for every flagged word."""
    files = []
    for p in map(Path, paths):
        files += sorted(p.rglob("*.json")) if p.is_dir() else [p]
    hits = []
    for f in files:
        data = json.loads(f.read_text(encoding="utf-8"))
        root = data.get("sections", data) if isinstance(data, dict) else data
        if isinstance(root, dict) and "raw" in root:
            root = {k: v for k, v in root.items() if k != "raw"}
        extra = [("raw", data["raw"])] if isinstance(data, dict) and isinstance(data.get("raw"), str) else []
        for path, text in extra + list(_strings(root)):
            text = re.sub(r"(?<![A-Za-z])'[^']*'(?![A-Za-z])|\"[^\"]*\"", " ", text)  # quoted image text is copied word for word
            for w in re.findall(r"[a-z]+(?:-[a-z]+)?", text.lower()):
                if w in WORDS:
                    hits.append((str(f), path, w, text))
    return hits


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    hits = scan(argv[1:])
    for f, path, w, text in hits:
        print(f"{Path(f).name}  {path}  [{w}]  {text[:100]}")
    print(f"{len(hits)} hits" + ("" if hits else ": no gender, age or relationship words"))
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
