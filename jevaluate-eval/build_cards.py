"""Evidence cards for new eval cases: what the owner answers from, never a verdict.
Each card quotes, from the case's packet: the hosted-call lines jev_callsites finds (or none), the README lines that name
Jev or TypeSafe, and the acting lines the controller lists, each with one neutral sentence from a notes file.
Refuses a quoted line with no sentence, an acting line the packet doesn't show, and any type, code or stakes word.

Usage: build_cards.py <packets dir> <notes.json> <out cards.json>
notes.json: {"<case>": {"summary": "...", "lines": {"<path>:<n>": "sentence"}, "actions": [["<path>", n, "sentence"]]}}
"""
import json, pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "jevaluate" / "scripts"))
import jev_callsites, rubric_text

CLAIM = re.compile(r"\bjev\b|typesafe|system one", re.I)
MAX_CLAIMS, MIN_WORDS = 6, 6  # the first six README sentences that name Jev; headings, badges and commands are skipped
NUMBERED = re.compile(r"^(\d+): ?(.*)$")

def verdict_words():
    vals = rubric_text.allowed_values()
    words = set(vals["project_type"]) | {c for c in vals["verdict_1_code"] if c != "none"} | {"very high", "high", "low", "stakes", "n.a."}
    words |= {"false marketing", "name only", "not a jev integration", "answers unused", "not yet rated", "integration", "replacement", "mention"}
    return sorted(words, key=len, reverse=True)

def norm(text):
    """Lowercase, hyphens and punctuation to single spaces; dots kept only inside a token (n.a.)."""
    t = re.sub(r"[^a-z0-9.]+", " ", text.lower().replace("-", " "))
    return re.sub(r"\s+", " ", re.sub(r"\.(?=\s|$)|(?<=\s)\.", " ", t)).strip()

def parse(packet):
    """{path: {line number: text}} from a build_packets packet; a file whose lines all start with `NN: ` keeps those numbers, any other whole file is numbered from 1."""
    files = {}
    for sec in re.split(r"^## FILE: ", packet, flags=re.M)[1:]:
        path, _, body = sec.partition("\n"); lines = body.rstrip("\n").splitlines(); out = {}
        if lines and lines[0] == "(keyword lines, numbered)":
            for l in lines[1:]:
                m = NUMBERED.match(l)
                if m: out[int(m.group(1))] = m.group(2)
        elif lines and all(NUMBERED.match(l) for l in lines if l.strip()):  # a fixture packet: every line carries its own number
            out = {int(m.group(1)): m.group(2) for m in map(NUMBERED.match, lines) if m}
        else:
            if lines and lines[0] == "(head)": lines = lines[1:]
            out = {i: l for i, l in enumerate(lines, 1)}
        files[path.strip()] = out
    return files

def card(case, packet, note):
    files = parse(packet); errs = []
    calls, claims, rest, covered = [], [], [], set()
    for path, lines in files.items():
        if not jev_callsites.counts_as_hosted_path(pathlib.PurePath(path)): continue
        calls += [(path, n, lines[n]) for n in jev_callsites.lines_with_calls(lines)]
    for path, lines in files.items():
        if path.lower() == "readme.md":
            hits = [(path, n, t) for n, t in sorted(lines.items()) if CLAIM.search(t) and not re.match(r"\s*(#|```)", t) and len(re.findall(r"[A-Za-z]{2,}", re.sub(r"<[^>]*>|\([^)]*\)|\S*://\S*|`[^`]*`", "", t))) >= MIN_WORDS]
            claims += hits[:MAX_CLAIMS]; rest = hits[MAX_CLAIMS:]
    def item(path, n, text, says, join=False):
        if says is None: errs.append(f"{case}: {path}:{n} has no sentence in the notes"); says = ""
        where, lines = f"{path}:{n}", files.get(path, {})
        if join:  # a README sentence that wraps: add following lines until the sentence ends (at most 2)
            end = n
            nxt = lambda i: lines.get(i, "").strip()
            while (not re.search(r"[.!?:|]\W*$", nxt(end) or ".") and nxt(end + 1) and not re.match(r"([-*|#]|```|\d+\.)\s?", nxt(end + 1))
                   and end < n + 2):
                end += 1; text += " " + re.sub(r"^>\s*", "", nxt(end))
            covered.update(range(n, end + 1))
            if end > n: where = f"{path}:{n}-{end}"
        return {"where": where, "line": text.strip(), "says": says}
    out = {"id": case, "summary": note.get("summary", ""),
           "calls": [item(p, n, t, note["lines"].get(f"{p}:{n}")) for p, n, t in calls],
           "claims": [item(p, n, t, note["lines"].get(f"{p}:{n}"), join=True) for p, n, t in claims if n not in covered], "actions": []}
    out["more_claims"] = sum(1 for _, n, _ in rest if n not in covered)
    for path, n, says in note.get("actions", []):
        text = files.get(path, {}).get(n)
        if text is None: errs.append(f"{case}: action {path}:{n} is not in the packet"); continue
        out["actions"].append(item(path, n, text, says))
    words = verdict_words()
    for s in [out["summary"]] + [x["says"] for k in ("calls", "claims", "actions") for x in out[k]]:
        flat = " " + norm(s) + " "  # hyphens, case and punctuation can't hide a word
        for w in words:
            stem = re.escape(norm(w))
            if re.search(r" " + stem + r"(s|es|ed|ies)? ", flat) or (w.endswith("y") and re.search(r" " + stem[:-1] + r"ies ", flat)):
                errs.append(f"{case}: verdict word '{w}' in: {s}")
    if errs: raise SystemExit("cards not written:\n- " + "\n- ".join(errs))
    return out

if __name__ == "__main__":
    if len(sys.argv) != 4: print(__doc__); sys.exit(0 if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help") else 2)
    pk, notes = pathlib.Path(sys.argv[1]), json.loads(pathlib.Path(sys.argv[2]).read_text())
    cards = [card(c, (pk / f"{c}.md").read_text(), n) for c, n in notes.items()]
    pathlib.Path(sys.argv[3]).write_text(json.dumps(cards, indent=1)); print(sys.argv[3])
