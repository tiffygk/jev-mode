"""Owner's answer form for the comprehension quiz, and the key built from its saved answers.
  build_answer_form.py --count N [--out quiz-answers.html]   an HTML form over the first N scenarios
  build_answer_form.py --cards cards.json [--out case-answers.html]   the same form over evidence cards (build_cards.py) for new eval cases
  build_answer_form.py --key saved.json [--out expected.json] [--force]   the saved answers -> the key the scorer reads
The form asks only what the owner observes: the type, whether the project calls Jev, the verdict-1 code and the stakes as read.
The key derives everything else by the rules the code enforces: kind from the type, F0 n.a. for a guide,
top stakes n.a. for a guide, a client and any verdict-1 code."""
import argparse, html, json, pathlib, re, sys

HERE = pathlib.Path(__file__).resolve().parent
SKILL = HERE.parents[1] / "jevaluate"
sys.path.insert(0, str(SKILL / "scripts"))
import rubric_text
import library

NA_TYPES = ("guide", "client")            # top stakes n.a. by type (library.derive_top_stakes); a test keeps this in step with the code
ROUTED = library.ROUTED_CODES
LEVELS = library.LEVELS
CALLS = ("yes", "no")
STORAGE_KEY = "jev-quiz-key-v2"
CASES_KEY = "jev-cases-key-v1"

def type_panel():
    """The type-choosing help, taken from rubric section 1 so it never drifts from it: the guidance, the table and the questions."""
    sec = rubric_text.section(1)
    block = sec.split("### Kind and type", 1)[-1].split("\n### ", 1)[0]
    intro = re.search(r"^Pick the type by what the code does.*$", block, re.M)
    rows = [re.match(r"\| `([\w-]+)` \| (\w+) \| (.+?) \| (.+?) \| (.+) \|$", l) for l in block.splitlines()]
    rows = [m for m in rows if m]
    rules = re.findall(r"^\*\*(.+?)\*\* (.+)$", block, re.M)
    flow = re.search(r"```mermaid\n(.*?)```", sec, re.S)
    qs = []
    for m in re.finditer(r"\w+\{\"?`?([^{}`\"]+)`?\"?\}", flow.group(1) if flow else ""):
        q = re.sub(r"\s+F0$", "", m.group(1).strip())
        if q not in qs: qs.append(q)
    e = html.escape
    out = ["<details class='p'><summary>Type definitions</summary>"]
    if intro: out.append(f"<p>{e(intro.group(0))}</p>")
    out.append("<p><b>Questions, in order</b></p><ol>" + "".join(f"<li>{e(q)}</li>" for q in qs) + "</ol>")
    out.append("<table><tr><th>Type</th><th>Kind</th><th>Means</th><th>Example</th></tr>"
               + "".join(f"<tr><td><code>{e(m.group(1))}</code></td><td>{e(m.group(2))}</td><td>{e(m.group(3))}</td><td>{e(m.group(4))}</td></tr>" for m in rows) + "</table>")
    out += [f"<p><b>{e(h)}</b> {e(b)}</p>" for h, b in rules]
    out.append("</details>")
    return "".join(out)

def _select(i, field, label, options):
    opts = "<option value=''>choose</option>" + "".join(f"<option value='{html.escape(v)}'>{html.escape(t)}</option>" for v, t in options)
    return f"<label><span>{label}</span><select data-id='{i}' data-f='{field}'>{opts}</select></label>"

def build_form(count):
    scen = json.loads((HERE / "scenarios.json").read_text())
    if count < 1 or count > len(scen): raise SystemExit(f"--count must be between 1 and {len(scen)} (scenarios.json has {len(scen)})")
    vals = rubric_text.allowed_values(); panel = type_panel(); arts = []
    for s in scen[:count]:
        i = s["id"]
        fields = _fields(i, vals)
        arts.append(f"<article><h2>{i}</h2><p>{html.escape(s['text'])}</p><div class='row'><div class='f'>{fields}</div>{panel}</div></article>")
    return _page(arts, STORAGE_KEY, "Quiz answer form", QUIZ_INTRO.replace("@@N@@", str(count)), "quiz-answers.json")

def _fields(i, vals):
    return "".join([
        _select(i, "project_type", "Type", [(v, v) for v in vals["project_type"]]),
        _select(i, "calls_jev", "Calls Jev", [(v, v) for v in CALLS]),
        _select(i, "verdict_1_code", "Verdict-1 code", [(c, c if c == "none" else f"{c}: {library.CODE_LABEL[c]}") for c in vals["verdict_1_code"]]),
        _select(i, "stakes", "Stakes, as you read them", [(v, v) for v in LEVELS])])

def _evidence(title, items, empty):
    e = html.escape
    if not items: return f"<h3>{title}</h3><p class='none'>{empty}</p>"
    return f"<h3>{title}</h3><ul class='ev'>" + "".join(
        f"<li><code class='w'>{e(x['where'])}</code><pre>{e(x['line'])}</pre><p>{e(x['says'])}</p></li>" for x in items) + "</ul>"

def build_cards_form(cards):
    """The answer form over evidence cards: quoted lines from each case's packet, one plain sentence each, never a verdict."""
    vals = rubric_text.allowed_values(); panel = type_panel(); arts = []
    for c in cards:
        i = c["id"]
        ev = (f"<p>{html.escape(c.get('summary', ''))}</p>"
              + _evidence("Calls to TypeSafe found by the scanner", c["calls"], "No hosted Jev call found in the evidence.")
              + _evidence("What the README says about Jev", c["claims"], "The README doesn't mention Jev or TypeSafe.")
              + _evidence("What the code does with the answers", c["actions"], "No line in the evidence acts on an answer."))
        arts.append(f"<article><h2>{html.escape(i)}</h2>{ev}<div class='row'><div class='f'>{_fields(i, vals)}</div>{panel}</div></article>")
    return _page(arts, CASES_KEY, "New eval cases: answer form", CASES_INTRO.replace("@@N@@", str(len(cards))), "case-answers.json")

def _page(arts, key, title, intro, fname):
    n = str(len(arts))
    js = JS.replace("@@KEY@@", key).replace("@@N@@", n).replace("@@NA@@", json.dumps(NA_TYPES)).replace("@@ROUTED@@", json.dumps(ROUTED)).replace("quiz-answers.json", fname)
    return (PAGE.replace("@@TITLE@@", html.escape(title)).replace("@@INTRO@@", intro).replace("@@N@@", n)
            .replace("@@ARTICLES@@", "\n".join(arts)).replace("@@JS@@", js))

def derive_key(saved):
    """(key, problems): the scorer's expected.json from the form's saved answers. Kind, F0 n.a. and top-stakes n.a. come from code."""
    vals = rubric_text.allowed_values(); key, problems = {}, []
    for i, a in sorted(saved.items()):
        typ, calls, code, stakes = (str(a.get(k, "")).strip() for k in ("project_type", "calls_jev", "verdict_1_code", "stakes"))
        bad = False
        for name, v, ok in (("type", typ, vals["project_type"]), ("calls Jev", calls, CALLS), ("verdict-1 code", code, vals["verdict_1_code"])):
            if v not in ok: problems.append(f"{i}: {name} '{v}' is not one of {', '.join(ok)}; answer it in the form"); bad = True
        if bad: continue
        clash = library.type_code_problems(typ, code, calls)
        if clash: problems.append(f"{i}: " + "; ".join(clash) + ". Ask the owner which of type, calls Jev and the code is wrong."); continue
        top = library.derive_top_stakes({"project_type": typ, "verdict_1_code": code}, "")
        if top is None:
            if stakes not in LEVELS: problems.append(f"{i}: stakes '{stakes}' is not one of {', '.join(LEVELS)}; a {typ} that is not routed to a verdict-1 code needs the stakes you read"); continue
            top = stakes
        key[i] = {"kind": rubric_text.KIND_OF[typ], "type": typ, "f0": "n.a." if typ == "guide" else calls, "code": code, "top_stakes": top}
    return key, problems

PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>@@TITLE@@</title><style>
:root{--bg:#fbfaf7;--fg:#1f1d1a;--muted:#6b665e;--line:#e3dfd6;--card:#fff;--accent:#8a4b12;--code:#f3f0ea}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#161514;--fg:#ece8e1;--muted:#a39d93;--line:#34312d;--card:#1f1e1c;--accent:#e0a060;--code:#262420}}
body{background:var(--bg);color:var(--fg);font:15px/1.55 -apple-system,system-ui,sans-serif;margin:0;padding:24px 16px 96px}
main{max-width:1100px;margin:0 auto}article{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:6px 18px 14px;margin:16px 0}
h2{color:var(--accent);font-size:17px}.row{display:flex;flex-wrap:wrap;gap:16px;align-items:flex-start}.f{display:flex;flex-direction:column;gap:10px;min-width:240px}
label{display:flex;flex-direction:column;font-size:13px;color:var(--muted)}
select{font:14px -apple-system,system-ui,sans-serif;padding:5px;border:1px solid var(--line);border-radius:5px;background:var(--code);color:var(--fg);max-width:100%}
details.p{flex:1;min-width:280px;font-size:13.5px;border:1px solid var(--line);border-radius:6px;padding:6px 10px}summary{cursor:pointer;color:var(--accent)}
table{border-collapse:collapse;width:100%}th,td{border:1px solid var(--line);padding:4px 6px;text-align:left;vertical-align:top}code{background:var(--code);padding:1px 4px;border-radius:3px}
h3{font-size:14px;margin:12px 0 4px}ul.ev{list-style:none;padding:0;margin:0}ul.ev li{border-left:3px solid var(--line);padding:2px 10px;margin:6px 0}ul.ev p{margin:2px 0}
pre{background:var(--code);padding:4px 8px;border-radius:4px;margin:2px 0;white-space:pre-wrap;overflow-wrap:anywhere;font-size:13px}.w{font-size:12px}.none{color:var(--muted)}
.bar{position:fixed;bottom:0;left:0;right:0;background:var(--card);border-top:1px solid var(--line);padding:10px 16px;display:flex;gap:12px;align-items:center;justify-content:center}
button{font:14px -apple-system,system-ui,sans-serif;padding:8px 14px;border-radius:6px;border:1px solid var(--accent);background:var(--accent);color:var(--bg);cursor:pointer}#st{color:var(--muted);font-size:13px}
</style></head><body><main><h1>@@TITLE@@</h1>
<p>@@INTRO@@</p>
@@ARTICLES@@
</main>
<div class="bar"><span id="st">0 of @@N@@ complete</span><button onclick="save()">Save answers</button></div>
<script>@@JS@@</script></body></html>"""

QUIZ_INTRO = "@@N@@ invented projects. Answer each one before seeing any model's answers; your answers become the key. You give only what you observe: the type, whether it calls Jev, the verdict-1 code and the stakes you read. The key's kind, and every n.a., are worked out by code. Open <b>Type definitions</b> beside a project for the type table and the questions. Answers save in this browser as you go. Press <b>Save answers</b>: it copies the JSON to the clipboard first, then downloads <code>quiz-answers.json</code>."
CASES_INTRO = ("@@N@@ real projects. Each card quotes lines from the evidence a grader sees, with one plain sentence per line; "
    "it never says what the answer is. Answer each one before seeing any model's labels. You give the type, whether it calls Jev, "
    "the verdict-1 code and the stakes you read; code works out the kind and every n.a. Open <b>Type definitions</b> beside a project. "
    "Answers save in this browser as you go. Press <b>Save answers</b>: it copies the JSON to the clipboard first, then downloads <code>case-answers.json</code>.")

JS = """const K='@@KEY@@',NA=@@NA@@,ROUTED=@@ROUTED@@;let A={};try{A=JSON.parse(localStorage.getItem(K)||'{}')}catch(e){}
const els=[...document.querySelectorAll('[data-id]')];
els.forEach(e=>{const v=(A[e.dataset.id]||{})[e.dataset.f];if(v)e.value=v;e.addEventListener('input',upd);e.addEventListener('change',upd)});
function upd(){A={};els.forEach(e=>{(A[e.dataset.id]=A[e.dataset.id]||{})[e.dataset.f]=e.value});try{localStorage.setItem(K,JSON.stringify(A))}catch(e){}
const done=Object.values(A).filter(r=>r.project_type&&r.calls_jev&&r.verdict_1_code&&(r.stakes||NA.includes(r.project_type)||ROUTED.includes(r.verdict_1_code))).length;document.getElementById('st').textContent=done+' of @@N@@ complete'}
function save(){upd();const t=JSON.stringify(A,null,1);
const fallback=()=>{const x=document.createElement('textarea');x.value=t;document.body.appendChild(x);x.select();let ok=false;try{ok=document.execCommand('copy')}catch(e){}x.remove();return ok};
let p;try{p=navigator.clipboard.writeText(t)}catch(e){p=Promise.reject(e)}
p.then(()=>'Copied to the clipboard and downloaded quiz-answers.json').catch(()=>fallback()?'Copied to the clipboard and downloaded quiz-answers.json':'Downloaded quiz-answers.json; the clipboard was blocked, so paste from the file').then(m=>{
const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([t],{type:'application/json'}));a.download='quiz-answers.json';a.click();document.getElementById('st').textContent=m})}
upd();"""

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True); g.add_argument("--count", type=int); g.add_argument("--cards"); g.add_argument("--key")
    ap.add_argument("--out"); ap.add_argument("--force", action="store_true"); a = ap.parse_args()
    if a.cards:
        out = pathlib.Path(a.out or HERE / "case-answers.html"); out.write_text(build_cards_form(json.loads(pathlib.Path(a.cards).read_text()))); print(out)
    elif a.count is not None:
        out = pathlib.Path(a.out or HERE / "quiz-answers.html"); out.write_text(build_form(a.count)); print(out)
    else:
        key, problems = derive_key(json.loads(pathlib.Path(a.key).read_text()))
        if problems: print("not written; fix these and rerun:\n- " + "\n- ".join(problems), file=sys.stderr); sys.exit(1)
        text = json.dumps(key, indent=1)
        if not a.out: print(text); sys.exit(0)
        out = pathlib.Path(a.out)
        if out.exists() and not a.force: print(f"{out} already exists; use --force to overwrite it", file=sys.stderr); sys.exit(1)
        out.write_text(text + "\n"); print(out)
