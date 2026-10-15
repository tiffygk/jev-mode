#!/usr/bin/env python3
"""Refuse text that copies a private source or credits a named person with saying something.
The private side lives only on the owner's machine: $JEV_PRIVATE_CONFIG, default
~/.claude/jevaluate-library/private-sources.json = {"sources": [paths], "names": [names or handles]}.
Speaker handles written '**hh:mm:ss · handle:**' in a source are added to the names.
Usage: private_text_check.py [--require-config] FILE...  Prints file:line for each hit; exit 1 on any hit."""
import json, os, re, sys

N = 8
WORD = re.compile(r"[a-z0-9']+")
VERBS = r"(said|says|say|told|tells|mentioned|mentions|reported|reports|confirmed|confirms|explained|noted|announced|asked|according to)"
GENERIC = re.compile(r"\b(discord|community|server|typesafe)\s+(user|member|person|people|folks|staff|engineer|researcher|founder|employee|team)s?\b\W+(?:\w+\W+){0,3}?" + VERBS + r"\b", re.I)
SPEAKER = re.compile(r"^\*\*~?\d{1,2}:\d{2}:\d{2} · ([^:*]+):\*\*", re.M)
DEFAULT = "~/.claude/jevaluate-library/private-sources.json"
WORD_LIST = "/usr/share/dict/words"  # $JEV_WORD_LIST overrides it; a missing file means no handle counts as a word


def english_words():
    path = os.path.expanduser(os.environ.get("JEV_WORD_LIST") or WORD_LIST)
    try:
        with open(path, encoding="utf-8", errors="ignore") as fh:
            return {ln.strip().lower() for ln in fh if ln.strip()}
    except OSError:
        return set()


def words(t):
    return WORD.findall(t.lower())


def load(path):
    """(shingles, names, handles). Names come from the config and are refused as attributions; handles come from
    the sources' speaker lines and are also refused on their own when 4+ characters long and not an ordinary
    English word (a handle like that is refused only as an attribution)."""
    with open(os.path.expanduser(path), encoding="utf-8") as fh:
        cfg = json.load(fh)
    sh, names, handles = set(), {n.strip() for n in cfg.get("names", []) if n.strip()}, set()
    for src in cfg.get("sources", []):
        with open(os.path.expanduser(src), encoding="utf-8", errors="ignore") as fh:
            t = fh.read()
        handles.update(h.strip() for h in SPEAKER.findall(t) if h.strip())
        w = words(SPEAKER.sub(" ", t))
        sh.update(" ".join(w[i:i + N]) for i in range(len(w) - N + 1))
    common = english_words()
    bare = [h for h in handles if len(h) >= 4 and not (h.isalpha() and h.lower() in common)]
    return sh, sorted(names | handles), sorted(bare)


def check(text, sh, names, handles=()):
    hits = []
    rxs = [(n, re.compile(r"(?<!\w)" + re.escape(n) + r"(?!\w)\W+(?:\w+\W+){0,5}?" + VERBS + r"\b|\b" + VERBS
                          + r"\W+(?:\w+\W+){0,3}?" + re.escape(n) + r"(?!\w)", re.I)) for n in names]
    bare = [re.compile(r"(?<![\w@])" + re.escape(h) + r"(?!\w)(?!/\w)") for h in handles]  # case-sensitive
    lines = text.splitlines()
    for i, ln in enumerate(lines, 1):
        if GENERIC.search(ln):
            hits.append((i, "credits a community member or a vendor employee with saying something"))
        if any(rx.search(ln) for _, rx in rxs):
            hits.append((i, "credits a named person with saying something"))
        elif any(b.search(ln) for b in bare):
            hits.append((i, "names a speaker from a private source"))
    seq = [(w, i) for i, ln in enumerate(lines, 1) for w in words(ln)]
    flagged = set()
    for j in range(len(seq) - N + 1):
        if seq[j][1] not in flagged and " ".join(w for w, _ in seq[j:j + N]) in sh:
            flagged.add(seq[j][1])
            hits.append((seq[j][1], f"{N}+ words copied from a private source"))
    return sorted(hits)


def main(argv):
    req = "--require-config" in argv
    files = [a for a in argv if a != "--require-config"]
    cfg = os.path.expanduser(os.environ.get("JEV_PRIVATE_CONFIG") or DEFAULT)
    if not os.path.exists(cfg):
        print(f"private_text_check: no config at {cfg}" + ("; refusing" if req else "; skipped"), file=sys.stderr)
        return 1 if req else 0
    sh, names, handles = load(cfg)
    bad = 0
    for f in files:
        try:
            with open(f, encoding="utf-8", errors="ignore") as fh:
                text = fh.read()
        except OSError as e:
            print(f"private_text_check: cannot read {f}: {e.strerror}", file=sys.stderr)
            bad += 1
            continue
        for i, why in check(text, sh, names, handles):
            print(f"{f}:{i}: {why}")
            bad += 1
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
