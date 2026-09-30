"""Grader view by step: what a rater reads at the start, what step.py serves at each step, and the eval grader's prompt.
Usage: build_grader_view.py <out.html> [notes.md]. Finds the repo from this file's own location; the served text comes from step.serve
for an invented project, and the comparison cards from an invented past rating in a temporary library, so nothing private is read."""
import html, pathlib, re, subprocess, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent
SK = HERE.parent / "jevaluate"
REPO = HERE.parent
sys.path.insert(0, str(SK / "scripts")); sys.path.insert(0, str(HERE))
import rubric_text as rt  # noqa: E402
import library as lib  # noqa: E402
import step  # noqa: E402
import run_eval  # noqa: E402

# An invented rating with one failed fact, so the verdict step shows the fix rows it would serve.
SAMPLE = """---
project: ticket-router
url: https://github.com/example/ticket-router
owner: example
project_type: workflow
verdict_1_code: none
top_stakes: high
lineage: new
stages: [question-state, decision]
---
## Decisions
- which team gets the ticket | Choice | high | acts at router.py:30 | moves the ticket to that team's queue
## Facts (with evidence)
- F0 Calls hosted Jev -- yes. client.ask in router.py:12
- F1 One question per decision -- no. Asks two things in one Noul (router.py:20). https://docs.typesafe.ai/primitives/noul.md
"""
# An invented past rating, so the compare step has a card to show.
PAST = """---
project: mail-sorter
url: https://github.com/example/mail-sorter
owner: example
rated: 2026-09-29
rubric: 2026-09-29
project_type: workflow
verdict: 4
verdict_1_code: none
why: Clean batching and gated routing; no measured results.
lineage: new
stages: [question-state, decision]
---
## Facts (with evidence)
- F1 One question per decision -- yes. One property per question (sort.py:8)
"""

def md(text, note=""):
    parts = re.split(r"```mermaid\n(.*?)```", text, flags=re.S)
    out = [f'<pre class="mermaid">{html.escape(p)}</pre>' if i % 2 else f'<div class="md" data-md="{html.escape(p, quote=True)}"></div>' for i, p in enumerate(parts)]
    return ((f"<p class='note'>{note}</p>" if note else "")
            + "<div class='tw'><button class='tg' onclick='tog(this)'>Show the raw text the grader gets</button>"
            f"<div class='rendered'>{''.join(out)}</div><pre class='raw' hidden>{html.escape(text)}</pre></div>")

def raw(text, note=""): return (f"<p class='note'>{note}</p>" if note else "") + f"<pre class='raw'>{html.escape(text)}</pre>"

def stakes_table():
    """Every F11, F13, F20 and F22 row, with its stakes level as the first column."""
    sec = rt.section(2).splitlines()
    hdr = next(l for l in sec if l.startswith("| Fact "))
    out = ["| Level " + hdr, "|---|---|---|---|---|---|"]
    for l in sec:
        m = re.match(r"\| F(\d+) ([^|]*)\|", l)
        if m and int(m.group(1)) in step.STAKES_FACTS: out.append(f"| {m.group(2).strip().rsplit(', ', 1)[-1]} " + l)
    return "\n".join(out)

def served_steps():
    """step.serve for the invented project, against an invented library, restoring the real library paths afterward."""
    saved = (lib.LIB, lib.RAT, lib.PROJ)
    with tempfile.TemporaryDirectory() as tmp:
        lib.LIB = pathlib.Path(tmp); lib.RAT = lib.LIB / "ratings"; lib.PROJ = lib.LIB / "projects"
        (lib.PROJ / "example__mail-sorter").mkdir(parents=True); (lib.PROJ / "example__mail-sorter" / "2026-09-29.md").write_text(PAST)
        try: return {s: step.serve(s, SAMPLE).replace(tmp, "<library>") for s in ("routing", "facts", "scores", "compare", "verdict")}
        finally: lib.LIB, lib.RAT, lib.PROJ = saved

def head_line():
    r = subprocess.run(["git", "-C", str(REPO), "log", "-1", "--format=%h %s"], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else "(not a git checkout)"

def lint_line():
    r = subprocess.run([sys.executable, str(HERE / "lint_materials.py")], capture_output=True, text=True)
    return r.stdout.strip() or r.stderr.strip()

def build(out, notes=""):
    out = pathlib.Path(out)
    brief = (REPO / "jevaluate-harness/rater-brief.md").read_text().replace("PROJECT", "example/ticket-router").replace("SLUG", "example__ticket-router") \
        .replace("PREV", "(none)").replace("VIA", "direct").replace("SCOPE", "full")
    served = served_steps()
    task = (HERE / "task.md").read_text()
    sections = [
        ("Checks", raw(f"Branch head: {head_line()}\nLint: {lint_line()}") + (f"<div class='md' data-md=\"{html.escape(notes, quote=True)}\"></div>" if notes else "")),
        ("Rater, before anything: the brief", raw(brief, "What the controller hands each rater subagent, filled for an invented project.")),
        ("Rater, reads at the start: SKILL.md", md((SK / "SKILL.md").read_text())),
        ("Rater, reads at the start: read.md", md((SK / "read.md").read_text(), "The procedure. Every phase starts with <code>step.py next</code>; the rater never opens the rubric itself.")),
        ("Step 1 (served first): routing", md(served["routing"], "Printed by the first <code>step.py next</code>, after the cost check (it stops above 200k until the controller approves).")),
        ("Step 2 (after the routing answers are written): facts, with the Jev rules", md(served["facts"], "Shown for the invented project, whose one decision is a high Choice: only the rows for high stakes appear.")),
        ("Stakes rows in full: F11, F13, F20 and F22 at each level", md(stakes_table(), "The rows for the four facts whose test or penalty changes with stakes. A rater sees only the rows for the levels its project's decisions have; this table shows all of them together, each labelled with its level.")),
        ("Step 3 (after every fact is written): scores and build stages", md(served["scores"])),
        ("Step 4 (after scores and stages are written): comparison cards", md(served["compare"], "Cards come from an invented past rating, ranked for the invented project. The two closest, and the project's previous rating, can then be read in full with <code>step.py full</code>.")),
        ("Step 5 (after the comparison is written): verdict, with fix rows for the failed checks", md(served["verdict"], "Shown for the invented project, which failed F1: the F1 row plus the rows that aren't tied to one check.")),
        ("Eval grader, system prompt: SKILL.md plus rubric section 1 only", md(run_eval.system_prompt(), "One eval call answers the routing questions only, so it gets the routing section and nothing after it.")),
        ("Eval grader, the question: jevaluate-eval/task.md", raw(task)),
    ]
    nav = "".join(f"<li><a href='#s{i}'>{html.escape(t)}</a></li>" for i, (t, _) in enumerate(sections))
    body = "".join(f"<section id='s{i}'><h2>{html.escape(t)}</h2>{c}</section>" for i, (t, c) in enumerate(sections))
    out.write_text(PAGE.replace("@@NAV@@", nav).replace("@@BODY@@", body))
    return out

PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Grader View by Step</title>
<script src="https://cdn.jsdelivr.net/npm/marked@12/marked.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<style>
:root{--bg:#fbfaf7;--fg:#1f1d1a;--muted:#6b665e;--line:#e3dfd6;--card:#fff;--accent:#8a4b12;--code:#f3f0ea}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#161514;--fg:#ece8e1;--muted:#a39d93;--line:#34312d;--card:#1f1e1c;--accent:#e0a060;--code:#262420}}
:root[data-theme="dark"]{--bg:#161514;--fg:#ece8e1;--muted:#a39d93;--line:#34312d;--card:#1f1e1c;--accent:#e0a060;--code:#262420}
body{background:var(--bg);color:var(--fg);font:15px/1.55 -apple-system,system-ui,sans-serif;margin:0;padding:24px 16px 64px}
main{max-width:1040px;margin:0 auto}h1{font-size:26px}h2{font-size:19px;color:var(--accent);padding-top:6px}
section{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:4px 20px 16px;margin:18px 0}
table{border-collapse:collapse;width:100%;font-size:13.5px}th,td{border:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}
pre.raw{white-space:pre-wrap;background:var(--code);padding:12px;border-radius:6px;font-size:13px}code{background:var(--code);padding:1px 4px;border-radius:3px;font-size:13px}
.note{color:var(--muted);font-style:italic}.wrap{overflow-x:auto}.tg{font:13px -apple-system,system-ui,sans-serif;padding:6px 12px;margin:10px 0;border:1px solid var(--line);border-radius:6px;background:var(--code);color:var(--fg);cursor:pointer}p,li{max-width:80ch}
</style></head><body><main>
<h1>What a grader sees, step by step</h1>
<p>A rater reads the brief, SKILL.md and read.md, then gets the rubric from <code>step.py</code> one step at a time; each step is served only after the previous step's answers are in the rating file. The steps below are the literal text <code>step.py</code> prints. The eval grader is separate: one call with SKILL.md and the routing section only.</p>
<ol>@@NAV@@</ol>@@BODY@@
</main><script>
document.querySelectorAll('.md').forEach(d=>{d.innerHTML=marked.parse(d.dataset.md);d.querySelectorAll('table').forEach(t=>{const w=document.createElement('div');w.className='wrap';t.parentNode.insertBefore(w,t);w.appendChild(t);});});
function tog(b){const w=b.parentNode,r=w.querySelector('.rendered'),x=w.querySelector('pre.raw');const showRaw=x.hidden;x.hidden=!showRaw;r.hidden=showRaw;b.textContent=showRaw?'Show the rendered view':'Show the raw text the grader gets';}
mermaid.initialize({startOnLoad:true,theme:matchMedia('(prefers-color-scheme: dark)').matches?'dark':'default'});
</script></body></html>"""

if __name__ == "__main__":
    if sys.argv[1:2] in (["-h"], ["--help"]): print(__doc__); sys.exit(0)
    if len(sys.argv) < 2: print(__doc__, file=sys.stderr); sys.exit(2)
    print(build(sys.argv[1], pathlib.Path(sys.argv[2]).read_text() if len(sys.argv) > 2 else ""))
