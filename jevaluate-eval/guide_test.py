"""Guide test: does jevaluate, given the whole building-with-jev-skill guide, name the known gaps? Headless; costs ~150k tokens."""
import argparse, copy, json, pathlib, re, subprocess, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from build_packets import build

HERE = pathlib.Path(__file__).parent; SKILL = HERE.parent / "jevaluate"
SLUG = "building-with-jev-skill"; PASS_AT = 8; CAP = 20000

def wide_source(src):
    """Copy of a source entry with every file's cap raised, so the guide is seen whole."""
    s = copy.deepcopy(src); s["files"] = [[p, CAP] for p, _ in s.get("files", [])]; return s

def _reply(reply_json):
    """(parsed object or {}, tokens) from one `claude -p` JSON reply; never raises."""
    tok = 0
    try:
        u = reply_json.get("usage") or {}
        tok = sum(u.get(k, 0) or 0 for k in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens", "output_tokens"))
        m = re.search(r"\{.*\}", reply_json.get("result") or "", re.S)
        obj = json.loads(m.group(0)) if m else {}
        return (obj if isinstance(obj, dict) else {}), tok
    except (ValueError, AttributeError, TypeError):
        return {}, tok

def recall(reply_json, gold_misses):
    obj, _ = _reply(reply_json)
    misses = obj.get("misses")
    if not isinstance(misses, list): return 0, []
    which = [g for g, kws in gold_misses.items()
             if any(re.search(r"\b" + re.escape(k), str(m), re.I) for k in kws for m in misses)]
    return len(which), which

def n_misses(obj):
    m = obj.get("misses"); return len(m) if isinstance(m, list) else 0

def render(rows, wrongs, tokens, gold, ok, pass_at=PASS_AT):
    """rows: (rep, found, which, verdict, n_misses, note)."""
    md = ["# Guide test: building-with-jev-skill", "", f"Recall passes at {pass_at} of {len(gold)} in every rep: **{'PASS' if ok else 'FAIL'}**", "",
          "| rep | recall | misses listed | verdict | gaps found |", "|---|---|---|---|---|"]
    md += [f"| {r} | {f}/{len(gold)} found, from {n} misses listed | {n} | {v} | {', '.join(w) or '-'}{' (' + note + ')' if note else ''} |"
           for r, f, w, v, n, note in rows]
    md += ["", "## Missed gaps per rep", ""] + [f"- rep {r}: {', '.join(g for g in gold if g not in w) or 'none'}" for r, _, w, _, _, _ in rows]
    md += ["", "## \"wrong\" entries (claims, not findings; the owner checks each by hand)", ""]
    md += [f"- rep {r}: {json.dumps(x)}" for r, x in wrongs] or ["- none"]
    md += ["", "The recall result above is not the whole test: the \"wrong\" entries still need the owner's check before the test counts as passed.",
           "", f"Total tokens: {tokens} (headless; add to the budget by hand)"]
    return "\n".join(md) + "\n"

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--reps", type=int, default=3); ap.add_argument("--effort", default="medium")
    ap.add_argument("--out", required=True); a = ap.parse_args()
    out = pathlib.Path(a.out); pk = out / "packets"; out.mkdir(parents=True, exist_ok=True)
    src = json.loads((HERE / "sources.json").read_text())[SLUG]
    status = build({SLUG: wide_source(src)}, pk)
    if status.get(SLUG) != "ok": print("packet failed:", status); return 2
    gold = json.loads((HERE / "guide_gold.json").read_text())[SLUG]["misses"]
    (out / "system.md").write_text("\n\n".join((SKILL / f).read_text() for f in ("SKILL.md", "read.md", "rubric.md")))
    prompt = (HERE / "guide_task.md").read_text() + "\n\n" + (pk / f"{SLUG}.md").read_text()
    rows, wrongs, tokens = [], [], 0
    for rep in range(1, a.reps + 1):
        res = subprocess.run(["claude", "-p", "--setting-sources", "", "--strict-mcp-config", "--tools", "",
                              "--system-prompt-file", str(out / "system.md"), "--model", "claude-sonnet-5-5",
                              "--effort", a.effort, "--output-format", "json"], input=prompt, capture_output=True, text=True)
        (out / f"guide_r{rep}.json").write_text(res.stdout or json.dumps({"result": "", "error": res.stderr}))
        try: reply = json.loads(res.stdout)
        except ValueError: reply = {}
        found, which = recall(reply, gold); obj, tok = _reply(reply); tokens += tok
        note = f"call failed: exit {res.returncode}, see guide_r{rep}.json" if res.returncode != 0 and not res.stdout else ""
        w = obj.get("wrong"); rows.append((rep, found, which, obj.get("verdict", "?"), n_misses(obj), note))
        wrongs += [(rep, x) for x in (w if isinstance(w, list) else [])]
        print(f"rep {rep}: {found}/{len(gold)} found, from {n_misses(obj)} misses listed, exit {res.returncode}")
    ok = all(r[1] >= PASS_AT for r in rows)
    md = render(rows, wrongs, tokens, gold, ok)
    (out / "guide-summary.md").write_text(md); print(md)
    return 0 if ok else 1

if __name__ == "__main__": sys.exit(main())
