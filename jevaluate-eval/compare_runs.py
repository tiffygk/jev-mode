"""Compare a Codex eval run with the saved Sonnet run on equal terms.
Usage: compare_runs.py report <sonnet run> <codex run> [--reps N]
Checks the two runs saw the same system prompt and packets (byte for byte; Codex notes appended at the end are
reported apart), then scores both with today's score.py and prints one side-by-side table."""
import json, pathlib, sys
HERE = pathlib.Path(__file__).parent; sys.path.insert(0, str(HERE))
import score

FIELDS = ("kind_ok", "type_ok", "f0_ok", "code_ok", "stakes_ok")


def same_inputs(a, b):
    """([problems], appended text): what differs between run a's inputs and run b's."""
    a, b = pathlib.Path(a), pathlib.Path(b); probs = []
    sa, sb = (a / "system.md").read_bytes(), (b / "system.md").read_bytes()
    extra = ""
    if sb.startswith(sa): extra = sb[len(sa):].decode()
    else: probs.append("system.md differs")
    pa = {p.name: p.read_bytes() for p in (a / "packets").glob("*.md")}
    pb = {p.name: p.read_bytes() for p in (b / "packets").glob("*.md")}
    for n in sorted(set(pa) | set(pb)):
        if n not in pb: probs.append(f"packet {n} missing from {b.name}")
        elif n not in pa: probs.append(f"packet {n} not in {a.name}")
        elif pa[n] != pb[n]: probs.append(f"packet {n} differs")
    return probs, extra


def stamp(run):
    try: return json.loads((pathlib.Path(run) / "run.json").read_text())
    except (OSError, ValueError): return {}


def side_by_side(rs, rc):
    c = {r["slug"]: r for r in rc}
    head = "| case | set | Sonnet answered | Sol answered | " + " | ".join(f.replace("_ok", "") + " S/Sol" for f in FIELDS) + " | Sonnet pass | Sol pass |"
    out = [head, "|" + "---|" * (6 + len(FIELDS))]
    for r in rs:
        k = c.get(r["slug"], {})
        cells = [f"{r.get(f, '-')}/{k.get(f, '-')}" for f in FIELDS]
        out.append(f"| {r['slug']} | {r['set']} | {r['answered']}/{r['reps']} | {k.get('answered', '-')}/{k.get('reps', '-')} | " + " | ".join(cells) + f" | {r['pass']} | {k.get('pass', '-')} |")
    return "\n".join(out)


def tool_calls(run):
    n = []
    for f in sorted(pathlib.Path(run).glob("r*_g*.json")):
        try: d = json.loads(f.read_text())
        except ValueError: n.append(f"{f.name}: unreadable"); continue
        if d.get("commands"): n.append(f"{f.name}: {d['commands']}")
        if not d.get("result"): n.append(f"{f.name}: no answer ({str(d.get('error', ''))[:120]})")
    return n


def report(sonnet, codex, reps=None):
    gold = json.loads((HERE / "gold.json").read_text())
    ss, sc = stamp(sonnet), stamp(codex)
    if ss.get("gold_fingerprint") != sc.get("gold_fingerprint"):
        sys.exit(f"answer keys differ: Sonnet run {ss.get('gold_fingerprint')}, Codex run {sc.get('gold_fingerprint')}; not comparable")
    probs, extra = same_inputs(sonnet, codex)
    if probs: sys.exit("inputs differ, not comparable:\n" + "\n".join(probs))
    rs, ps, ts = score.score(sonnet, gold, reps or ss.get("reps"))
    rc, pc, tc = score.score(codex, gold, reps or sc.get("reps"))
    lines = [f"Sonnet: {ss.get('model', 'claude-sonnet-5-5')} commit {ss.get('head')} | Codex: {sc.get('model')} effort {sc.get('effort')} commit {sc.get('head')} | key {ss.get('gold_fingerprint')}",
             "Inputs: identical" + (f" (Codex notes appended: {len(extra.strip())} chars)" if extra.strip() else ""), "",
             side_by_side(rs, rc), "",
             f"Overall: Sonnet {'PASS' if ps else 'FAIL'}, Sol {'PASS' if pc else 'FAIL'} (today's score.py for both)",
             f"Tokens: Sonnet {ts:,}; Sol {tc:,} (Codex carries built-in tool overhead; not a quality measure)", "",
             "Sol calls with tool use or no answer:", *(tool_calls(codex) or ["none"])]
    return "\n".join(lines)


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 3 or a[0] != "report": print(__doc__); sys.exit(2)
    reps = int(a[a.index("--reps") + 1]) if "--reps" in a else None
    print(report(a[1], a[2], reps))
