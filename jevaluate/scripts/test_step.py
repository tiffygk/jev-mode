import json, os, pathlib, re, subprocess, sys
HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))

def step(lib, *args):
    env = dict(os.environ, JEVALUATE_LIBRARY=str(lib))
    return subprocess.run([sys.executable, str(HERE / "step.py"), *args], capture_output=True, text=True, env=env)

INTAKE = "---\nproject: T\nurl: https://github.com/o/t\nowner: o\nrated: 2026-09-29\ncommit: abc1234\n---\n"
MANIFEST = "# Coverage manifest: o/t @ abc\n\nTree: 1 files; 1 kept (4000 chars, ~{n} tokens).\n"

import pytest
@pytest.fixture(autouse=True)
def _manifest(tmp_path):  # a real manifest's header: the token count is on line 3
    (tmp_path / "manifest.md").write_text(MANIFEST.format(n=1000))

def test_over_200k_needs_controller_approval(tmp_path):
    (tmp_path / "manifest.md").write_text(MANIFEST.format(n=250000))
    r = tmp_path / "t.md"; r.write_text(INTAKE)
    assert step(tmp_path / "lib", "next", str(r)).returncode == 3
    (tmp_path / "approved_cost.json").write_text('{"approved": 295000}')
    assert "## 1. Routing" in step(tmp_path / "lib", "next", str(r)).stdout

def test_no_manifest_refused(tmp_path):
    (tmp_path / "manifest.md").unlink(); r = tmp_path / "t.md"; r.write_text(INTAKE)
    assert step(tmp_path / "lib", "next", str(r)).returncode == 3

def test_first_call_serves_routing_only(tmp_path):
    r = tmp_path / "t.md"; r.write_text(INTAKE)
    out = step(tmp_path / "lib", "next", str(r)).stdout
    assert "## 1. Routing" in out and "## 2. Facts" not in out

def test_facts_withheld_until_routing_written(tmp_path):
    r = tmp_path / "t.md"; r.write_text(INTAKE); step(tmp_path / "lib", "next", str(r))
    res = step(tmp_path / "lib", "next", str(r))
    assert res.returncode != 0 and "project_type" in res.stdout + res.stderr and "kind" not in res.stdout + res.stderr

def test_routed_to_1r_skips_to_verdict(tmp_path):
    r = tmp_path / "t.md"
    r.write_text(INTAKE.replace("---\n", "---\nkind: replaces\nproject_type: jev-replacement\nverdict_1_code: 1r\ntop_stakes: n.a.\ncitation: none\n", 1)
                 + "## Facts\n- F0 Calls hosted Jev -- no. Serves its own model (serve.py:3)\n")
    step(tmp_path / "lib", "next", str(r)); out = step(tmp_path / "lib", "next", str(r)).stdout
    assert "## 5. Verdict" in out

def test_log_records_each_step(tmp_path):
    r = tmp_path / "t.md"; r.write_text(INTAKE); step(tmp_path / "lib", "next", str(r))
    assert [e["step"] for e in json.loads((tmp_path / "t.md.steps.json").read_text())] == ["routing"]

def test_full_rating_only_for_two_closest(tmp_path):
    r = tmp_path / "t.md"; r.write_text(INTAKE)
    res = step(tmp_path / "lib", "full", str(r), "/nonexistent/other.md")
    assert res.returncode != 0 and "two closest" in res.stdout + res.stderr

def test_estimate_command_prints_45k_plus_manifest(tmp_path):
    assert step(tmp_path / "lib", "estimate", str(tmp_path / "manifest.md")).stdout.strip() == "46000"

# --- fix round 1 ---
ROUTED = INTAKE.replace("---\n", "---\nkind: replaces\nproject_type: jev-replacement\nverdict_1_code: 1r\ntop_stakes: n.a.\ncitation: none\n", 1)

def test_verdict_serves_g_rows_and_unkeyed_rows(tmp_path):
    r = tmp_path / "t.md"
    r.write_text(ROUTED + "## Facts\n- F0 Calls hosted Jev -- no. Serves its own model (serve.py:3)\n"
                 "- F1 Atomic -- no. Compound question (a.py:1)\n- G1 Rules match -- no. Contradicts the page (SKILL.md:2)\n")
    step(tmp_path / "lib", "next", str(r)); out = step(tmp_path / "lib", "next", str(r)).stdout
    assert "| F1 " in out and "| G1 " in out and "| F2 " not in out and "| G2 " not in out
    assert "Measured once, loop not closed" in out and "A Choice with a very large or deep option list" in out

def _card_lib(tmp_path):
    d = tmp_path / "lib" / "projects" / "x__y"; d.mkdir(parents=True)
    p = d / "2026-09-28.md"
    p.write_text("---\nproject: Y\nowner: x\nurl: https://github.com/x/y\nproject_type: workflow\nverdict: 3\nrubric: 2026-09-29\n---\n## Summary\nA card.\n")
    return p

def test_full_refused_before_compare_step(tmp_path):
    past = _card_lib(tmp_path)
    r = tmp_path / "t.md"; r.write_text(INTAKE.replace("---\n", "---\nproject_type: workflow\n", 1)); step(tmp_path / "lib", "next", str(r))
    res = step(tmp_path / "lib", "full", str(r), str(past))
    assert res.returncode != 0 and "compare" in res.stdout + res.stderr

def test_full_allowed_after_compare_step(tmp_path):
    past = _card_lib(tmp_path)
    r = tmp_path / "t.md"; r.write_text(INTAKE.replace("---\n", "---\nproject_type: workflow\n", 1))
    (tmp_path / "t.md.steps.json").write_text(json.dumps([{"step": s, "time": "t", "routing": "x"} for s in ("routing", "facts", "scores", "compare")]))
    res = step(tmp_path / "lib", "full", str(r), str(past))
    assert res.returncode == 0 and "A card." in res.stdout

def test_facts_served_with_jev_rules(tmp_path):
    r = tmp_path / "t.md"
    r.write_text(INTAKE.replace("---\n", "---\nkind: uses\nproject_type: workflow\nverdict_1_code: none\ntop_stakes: low\ncitation: none\n", 1)
                 + "## Decisions\n- flag it | Noul | low | acts at a.py:9 | shows it\n## Facts\n- F0 Calls hosted Jev -- yes. Calls it (a.py:3)\n")
    step(tmp_path / "lib", "next", str(r)); out = step(tmp_path / "lib", "next", str(r)).stdout
    assert "## 2. Facts" in out and "## Jev rules and sources" in out and "# Jev rules" in out


# --- Task 4c: decisions gate the facts; only the stakes rows that apply are served ---
USES = INTAKE.replace("---\n", "---\nkind: uses\nproject_type: workflow\nverdict_1_code: none\ntop_stakes: {top}\ncitation: none\n", 1)
F0LINE = "## Facts\n- F0 Calls hosted Jev -- yes. Calls it (a.py:3)\n"

def _facts_out(tmp_path, top, decisions):
    r = tmp_path / "t.md"
    r.write_text(USES.format(top=top) + ("## Decisions\n" + "\n".join(decisions) + "\n" if decisions else "") + F0LINE)
    step(tmp_path / "lib", "next", str(r)); return step(tmp_path / "lib", "next", str(r)), r

def test_facts_withheld_until_decisions_written(tmp_path):
    res, _ = _facts_out(tmp_path, "low", [])
    assert res.returncode != 0 and "## Decisions" in res.stdout + res.stderr

def test_client_needs_no_decisions(tmp_path):
    r = tmp_path / "t.md"
    r.write_text(INTAKE.replace("---\n", "---\nkind: uses\nproject_type: client\nverdict_1_code: none\ntop_stakes: n.a.\ncitation: none\n", 1) + F0LINE)
    step(tmp_path / "lib", "next", str(r)); assert "## 2. Facts" in step(tmp_path / "lib", "next", str(r)).stdout

def test_facts_step_for_a_very_high_choice_shows_only_its_rows(tmp_path):
    res, _ = _facts_out(tmp_path, "very high", ["- grant access | Choice | very high | acts at a.py:9 | grants it"])
    out = res.stdout
    assert "| F13 Choice order handled, very high " in out and "| F13 Choice order handled, high " not in out and "| F13 Choice order handled, low " not in out
    assert "| F11 Confidence drives action, high or very high " in out and "| F11 Confidence drives action, low " not in out
    assert "| F20 Data as fields, not templates, very high " in out and "| F20 Data as fields, not templates, high or low " not in out
    assert "| F1 " in out and "| F23 " in out

def test_facts_step_for_only_low_decisions_never_shows_a_very_high_row(tmp_path):
    res, _ = _facts_out(tmp_path, "low", ["- flag it | Noul | low | acts at a.py:9 | shows it"])
    out = res.stdout
    rows = [l.split("|")[1].strip() for l in out.splitlines() if l.startswith("| F")]
    assert not [c for c in rows if c.endswith("very high")] and "F13 Choice order handled, high" not in rows
    assert "| F13 Choice order handled, low " in out and "| F11 Confidence drives action, low " in out and "| F20 Data as fields, not templates, high or low " in out

def test_a_two_level_row_counts_for_both_levels(tmp_path):
    res, _ = _facts_out(tmp_path, "high", ["- route it | Choice | high | acts at a.py:9 | routes", "- flag it | Noul | low | acts at a.py:12 | shows"])
    out = res.stdout
    assert "| F20 Data as fields, not templates, high or low " in out and "| F11 Confidence drives action, high or very high " in out
    assert "| F11 Confidence drives action, low " in out and "| F13 Choice order handled, high " in out and "| F13 Choice order handled, very high " not in out

def test_routed_to_1t_skips_to_verdict(tmp_path):
    r = tmp_path / "t.md"
    r.write_text(INTAKE.replace("---\n", "---\nkind: teaches\nproject_type: guide\nverdict_1_code: 1t\ntop_stakes: n.a.\ncitation: none\n", 1)
                 + "## Facts\n- F0 Calls hosted Jev -- n.a. A guide\n")
    step(tmp_path / "lib", "next", str(r)); assert "## 5. Verdict" in step(tmp_path / "lib", "next", str(r)).stdout


def test_every_stakes_row_label_in_the_rubric_maps_to_a_level():
    import step as st
    rows = [l for l in st.rt.section(2).splitlines() if re.match(r"\| F(\d+) ", l) and int(re.match(r"\| F(\d+) ", l).group(1)) in st.STAKES_FACTS]
    assert len(rows) == 9
    for l in rows:
        label = l.split("|")[1].strip().rsplit(", ", 1)[-1]
        assert label in st.ROW_LEVELS, f"row label {label!r} in {l[:40]!r} maps to no stakes level"


# --- Task 4d: the rater never enters top_stakes ---
def test_routing_step_does_not_ask_for_top_stakes(tmp_path):
    r = tmp_path / "t.md"
    r.write_text(INTAKE.replace("---\n", "---\nkind: uses\nproject_type: workflow\nverdict_1_code: none\ncitation: none\n", 1)
                 + "## Decisions\n- flag it | Noul | low | acts at a.py:9 | shows it\n" + F0LINE)
    step(tmp_path / "lib", "next", str(r)); res = step(tmp_path / "lib", "next", str(r))
    assert res.returncode == 0 and "## 2. Facts" in res.stdout, res.stdout + res.stderr
    assert "top_stakes" not in res.stderr

def test_routing_fingerprint_follows_the_derived_stakes(tmp_path):
    import step as S
    a = INTAKE.replace("---\n", "---\nkind: uses\nproject_type: workflow\nverdict_1_code: none\n", 1) + "## Decisions\n- x | Noul | low | acts at a.py:9 | shows it\n"
    b = a.replace("| low |", "| high |")
    assert S.routing_print(a) != S.routing_print(b)


def test_routing_step_does_not_ask_for_kind():
    import step as S
    t = INTAKE.replace("---\n", "---\nproject_type: workflow\nverdict_1_code: none\n", 1) + "- F0 Calls hosted Jev -- yes. x (a.py:1)\n"
    assert not any("kind" in n for n in S.missing("routing", t))


# --- Review fix 5 (2026-09-30): text copied from read.md's template is not a written section ---
READ = (HERE.parent / "read.md").read_text()
TEMPLATE = READ.split("Template:", 1)[1].split("```markdown\n", 1)[1].split("\n```", 1)[0]
def tline(prefix): return next(l for l in TEMPLATE.splitlines() if l.startswith(prefix))

def test_template_f0_line_does_not_satisfy_the_routing_gate():
    import step as S
    t = INTAKE.replace("---\n", "---\nproject_type: client\nverdict_1_code: none\n", 1) + "## Facts (with evidence)\n" + tline("- F0 ") + "\n"
    assert any("F0" in n for n in S.missing("routing", t)), S.missing("routing", t)
    t = t.replace(tline("- F0 "), "- F0 Calls hosted Jev -- yes. Builds the client and sends (bot.py:14)")
    assert not any("F0" in n for n in S.missing("routing", t))

def test_template_f0_line_keeps_the_next_step_from_being_served(tmp_path):
    r = tmp_path / "t.md"
    r.write_text(INTAKE.replace("---\n", "---\nkind: uses\nproject_type: client\nverdict_1_code: none\ntop_stakes: n.a.\ncitation: none\n", 1) + "## Facts (with evidence)\n" + tline("- F0 ") + "\n")
    step(tmp_path / "lib", "next", str(r)); res = step(tmp_path / "lib", "next", str(r))
    assert res.returncode != 0 and "F0" in res.stderr and "## 2. Facts" not in res.stdout

def test_template_scores_and_closes_loop_do_not_satisfy_the_scores_gate():
    import step as S
    head = "---\n" + tline("scores:") + "\n" + tline("closes_loop:") + "\n---\n"
    assert S.missing("scores", head) == ["scores", "closes_loop"]
    done = "---\nscores: {execution: 2, fit: 3, coverage: 2, evidence: 1}\ncloses_loop: none\n---\n"
    assert S.missing("scores", done) == []

def test_template_fact_lines_are_not_written_facts():
    import step as S
    t = INTAKE + "## Facts (with evidence)\n" + "\n".join(f"- F{n} Check{n} -- yes. Found it (a.py:{n})" for n in range(1, 24)) + "\n"
    assert S.missing("facts", t) == []
    t = t.replace("- F1 Check1 -- yes. Found it (a.py:1)", tline("- F1 "))
    assert S.missing("facts", t) == ["F1"]
