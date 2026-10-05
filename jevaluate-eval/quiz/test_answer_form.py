import json, pathlib, re, subprocess, sys
HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[1] / "scripts"))
import build_answer_form as baf
import library, rubric_text

def _form(n=3): return baf.build_form(n)

def test_answer_form_asks_observed_fields_only():
    page = _form(4)
    assert set(re.findall(r"data-f='(\w+)'", page)) == {"project_type", "calls_jev", "verdict_1_code", "stakes"}
    assert page.count("data-f='project_type'") == 4
    # No select offers kind, or n.a. as an answer for stakes: code derives both.
    for sel in re.findall(r"<select data-id='q\d+' data-f='(?:stakes|calls_jev)'>.*?</select>", page):
        assert "n.a." not in sel
    assert "<option value='n.a.'" not in page and "value='kind'" not in page

def test_answer_form_type_panel_comes_from_the_rubric_section():
    page = _form(1).split("<script")[0]
    sec = rubric_text.section(1)
    for line in sec.splitlines():
        m = re.match(r"\| `([\w-]+)` \| (\w+) \| (.+?) \| ", line)
        if m: assert m.group(1) in page and m.group(3) in baf.html.unescape(page), m.group(1)
    assert "<details" in page and "Does its non-test code call hosted Jev?" in baf.html.unescape(page)
    assert "Pick the type by what the code does when it runs" in baf.html.unescape(page)

def test_answer_form_copies_to_clipboard_first():
    js = _form(1).split("<script>")[1]
    save = js[js.index("function save"):]
    assert save.index("clipboard.writeText") < save.index("download")
    assert ".then(" in save  # the download waits for the copy to settle

def test_answer_form_js_embeds_the_codes_derivation():
    for t in baf.NA_TYPES: assert library.derive_top_stakes({"project_type": t, "verdict_1_code": "none"}, "") == "n.a."
    others = [t for t in rubric_text.allowed_values()["project_type"] if t not in baf.NA_TYPES]
    for t in others: assert library.derive_top_stakes({"project_type": t, "verdict_1_code": "none"}, "") is None
    assert tuple(library.ROUTED_CODES) == tuple(baf.ROUTED)

def test_key_derives_kind_and_na():
    saved = {"q01": {"project_type": "jev-mention-only", "calls_jev": "no", "verdict_1_code": "1a", "stakes": "very high"},
             "q02": {"project_type": "workflow", "calls_jev": "yes", "verdict_1_code": "none", "stakes": "low"},
             "q03": {"project_type": "guide", "calls_jev": "no", "verdict_1_code": "1t", "stakes": "high"},
             "q04": {"project_type": "client", "calls_jev": "yes", "verdict_1_code": "none", "stakes": "low"},
             "q05": {"project_type": "workflow", "calls_jev": "yes", "verdict_1_code": "1c", "stakes": "high"}}
    key, problems = baf.derive_key(saved)
    assert problems == []
    assert key["q01"] == {"kind": "mentions", "type": "jev-mention-only", "f0": "no", "code": "1a", "top_stakes": "n.a."}
    assert key["q02"] == {"kind": "uses", "type": "workflow", "f0": "yes", "code": "none", "top_stakes": "low"}
    assert key["q03"]["kind"] == "teaches" and key["q03"]["f0"] == "n.a." and key["q03"]["top_stakes"] == "n.a."
    assert key["q04"]["top_stakes"] == "n.a." and key["q05"]["top_stakes"] == "n.a."

def test_key_refuses_incomplete_answers_in_plain_words():
    key, problems = baf.derive_key({"q01": {"project_type": "workflow", "calls_jev": "yes", "verdict_1_code": "none"},
                                    "q02": {"project_type": "app", "calls_jev": "maybe", "verdict_1_code": "none", "stakes": "low"}})
    assert any("q01" in p and "stakes" in p for p in problems) and any("q02" in p and "app" in p for p in problems) and any("q02" in p and "maybe" in p for p in problems)

def test_key_cli_writes_expected_json_and_will_not_overwrite(tmp_path):
    saved = tmp_path / "saved.json"; saved.write_text(json.dumps({"q01": {"project_type": "workflow", "calls_jev": "yes", "verdict_1_code": "none", "stakes": "low"}}))
    out = tmp_path / "expected.json"
    run = lambda *a: subprocess.run([sys.executable, str(HERE / "build_answer_form.py"), *a], capture_output=True, text=True)
    r = run("--key", str(saved), "--out", str(out)); assert r.returncode == 0, r.stderr
    assert json.loads(out.read_text())["q01"]["kind"] == "uses"
    assert run("--key", str(saved), "--out", str(out)).returncode != 0

def test_count_cli_writes_a_form(tmp_path):
    out = tmp_path / "f.html"
    r = subprocess.run([sys.executable, str(HERE / "build_answer_form.py"), "--count", "2", "--out", str(out)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert out.read_text().count("<article>") == 2
    assert str(pathlib.Path.home()) not in out.read_text()


import shutil, pytest
@pytest.mark.skipif(not shutil.which("node"), reason="node not installed")
def test_saving_runs_the_copy_before_the_download(tmp_path):
    js = _form(1).split("<script>")[1].split("</script>")[0]
    harness = tmp_path / "h.js"
    harness.write_text("""const vm=require('vm');const log=[];
const el={dataset:{id:'q01',f:'project_type'},value:'workflow',addEventListener(){}};
globalThis.localStorage={getItem:()=>null,setItem(){}};
globalThis.document={querySelectorAll:()=>[el],getElementById:()=>({set textContent(v){log.push('status')}}),createElement:()=>({click(){log.push('download')}}),body:{appendChild(){}}};
Object.defineProperty(globalThis,'navigator',{configurable:true,value:{clipboard:{writeText:(t)=>{log.push('copy:'+t.length);return Promise.resolve()}}}});
globalThis.URL={createObjectURL:()=>'blob:x'};globalThis.Blob=class{};
vm.runInThisContext(require('fs').readFileSync(process.argv[2],'utf8')+';globalThis.save=save');
save();setTimeout(()=>console.log(JSON.stringify(log)),50);""")
    (tmp_path / "page.js").write_text(js)
    r = subprocess.run(["node", str(harness), str(tmp_path / "page.js")], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    log = [x for x in json.loads(r.stdout) if x != "status"]
    assert log[0].startswith("copy:") and log[1:] == ["download"]


def test_key_reproduces_the_existing_key():
    old = json.loads((HERE / "expected.json").read_text())
    saved = {q: {"project_type": k["type"], "calls_jev": "no" if k["f0"] == "n.a." else k["f0"], "verdict_1_code": k["code"],
                 "stakes": "low" if k["top_stakes"] == "n.a." else k["top_stakes"]} for q, k in old.items()}
    key, problems = baf.derive_key(saved)
    assert problems == [] and key == old


import pytest
CONTRADICTIONS = [
    ("workflow", "no", "none", "a workflow calls Jev, but calls Jev is no. A project that doesn't call Jev and isn't a guide or a replacement is a jev-mention-only, with 1a (False marketing: Jev in name only) or 1b (Not a Jev integration)"),
    ("jev-replacement", "yes", "1r", "a jev-replacement doesn't call Jev"),
    ("workflow", "yes", "1t", "1t (Guide, not yet rated) is only for a guide"),
    ("jev-replacement", "no", "1c", "1c (Jev answers unused) is only for a uses type"),
    ("jev-mention-only", "no", "none", "a jev-mention-only gets 1a (False marketing: Jev in name only) or 1b (Not a Jev integration)"),
]

@pytest.mark.parametrize("typ,calls,code,words", CONTRADICTIONS)
def test_key_refuses_contradictory_answers(typ, calls, code, words):
    key, problems = baf.derive_key({"q01": {"project_type": typ, "calls_jev": calls, "verdict_1_code": code, "stakes": "low"}})
    assert key == {} and len(problems) == 1 and problems[0].startswith("q01: ") and words in problems[0] and "Ask the owner" in problems[0]

def test_key_refuses_a_uses_type_routed_as_mention():
    _, problems = baf.derive_key({"q01": {"project_type": "library", "calls_jev": "yes", "verdict_1_code": "1b", "stakes": "low"}})
    assert problems and "q01" in problems[0]

def test_key_one_line_per_scenario_and_good_ones_still_build():
    key, problems = baf.derive_key({"q01": {"project_type": "workflow", "calls_jev": "no", "verdict_1_code": "1t", "stakes": "low"},
                                    "q02": {"project_type": "workflow", "calls_jev": "yes", "verdict_1_code": "none", "stakes": "low"}})
    assert len(problems) == 1 and "q02" in key

def test_key_refusals_use_no_bare_codes_or_f0():
    import re
    cases = [("workflow", "no", "none"), ("workflow", "yes", "1b"), ("workflow", "yes", "1t"), ("guide", "no", "1b"),
             ("jev-replacement", "no", "1c"), ("jev-mention-only", "no", "none")]
    for typ, calls, code in cases:
        _, problems = baf.derive_key({"q01": {"project_type": typ, "calls_jev": calls, "verdict_1_code": code, "stakes": "low"}})
        assert problems and "F0" not in problems[0], problems
        for m in re.finditer(r"\b1[a-z]\b(?! \()", problems[0]):
            assert False, f"bare code {m.group()} in: {problems[0]}"

CARDS = [{"id": "soter", "summary": "A chat moderation bot.", "calls": [{"where": "utils/jev.ts:20", "line": "fetch('https://api.typesafe.ai/v1/systemone')", "says": "Sends the message to the model."}],
          "claims": [{"where": "README.md:3", "line": "Powered by <Jev>.", "says": "The README names the model."}],
          "actions": [{"where": "index.ts:70", "line": "await m.delete();", "says": "Deletes the message."}]},
         {"id": "stub", "summary": "A scanner.", "calls": [], "claims": [], "actions": []}]

def test_cards_form_shows_evidence_and_the_same_fields(tmp_path):
    page = baf.build_cards_form(CARDS)
    assert page.count("data-f='project_type'") == 2 and "data-id='soter'" in page
    assert "utils/jev.ts:20" in page and "Deletes the message." in page and "Powered by &lt;Jev&gt;." in page
    assert "No hosted Jev call found in the evidence" in page and "case-answers.json" in page
    assert "jev-cases-key-v1" in page and "invented projects" not in page

def test_cards_cli_writes_a_form(tmp_path):
    (tmp_path / "cards.json").write_text(json.dumps(CARDS))
    out = tmp_path / "f.html"
    r = subprocess.run([sys.executable, str(HERE / "build_answer_form.py"), "--cards", str(tmp_path / "cards.json"), "--out", str(out)], capture_output=True, text=True)
    assert r.returncode == 0 and "data-id='stub'" in out.read_text()

def test_ids_form_shows_only_named_scenarios():
    page = baf.build_form(0, ids="q02,q05")
    assert "<h2>q02</h2>" in page and "<h2>q05</h2>" in page and "<h2>q01</h2>" not in page
