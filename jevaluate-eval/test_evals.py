import pytest


@pytest.fixture(autouse=True)
def _runs_folder_unset(monkeypatch):
    """Tests see the contributor default (.work/) unless they set JEVALUATE_RUNS themselves."""
    monkeypatch.delenv("JEVALUATE_RUNS", raising=False)
import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import build_packets as bp

def test_excerpt_puts_request_lines_first():
    lines = ["# filler %d choice" % i for i in range(300)] + ["resp = fetch('/api/jevs')"]
    out = bp.excerpt("\n".join(lines), 400)
    assert "fetch('/api/jevs')" in out.split("\n")[1]

def test_excerpt_keeps_short_text_whole():
    assert bp.excerpt("a\nb", 100) == "a\nb"

def test_build_marks_fetch_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(bp, "fetch", lambda src, path: None)
    st = bp.build({"x": {"kind": "github", "repo": "o/r", "commit": "c", "files": [["a.py", 100]]}}, tmp_path)
    assert st["x"] == "fetch failed" and not (tmp_path / "x.md").exists()

def test_build_skips_missing_local(tmp_path):
    st = bp.build({"y": {"kind": "local", "dir": str(tmp_path / "nope"), "files": [["a", 10]]}}, tmp_path)
    assert st["y"] == "skipped: local missing"

def test_build_copies_fixture(tmp_path):
    st = bp.build({"z": {"kind": "fixture", "path": "cases/refund-bot.md"}}, tmp_path)
    assert st["z"] == "ok" and "refund-bot" in (tmp_path / "z.md").read_text()

import score as sc

def _write(run, name, answers, usage=1000):
    run.mkdir(parents=True, exist_ok=True)
    (run / name).write_text(json.dumps({"result": json.dumps(answers), "usage": {"input_tokens": usage, "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0, "output_tokens": 0}}))

GOLD = {"a": {"set": "tuning", "match": ["alpha"], "kind": "uses", "type": "workflow", "f0": "yes", "code": "none", "top_stakes": "very high"},
        "b": {"set": "heldout", "match": ["beta"], "kind": "replaces", "type": "jev-replacement", "f0": "no", "code": "1r", "top_stakes": None}}
OK_A = {"project": "o/alpha", "kind": "uses", "project_type": "workflow", "calls_jev": "yes", "verdict_1_code": "none", "top_stakes": "very high", "decisions": [{"stakes": "Very High"}]}
OK_B = {"project": "beta model", "kind": "replaces", "project_type": "jev-replacement", "calls_jev": "no", "verdict_1_code": "1r", "top_stakes": "n.a.", "decisions": []}

def test_score_matches_by_substring(tmp_path):
    for r in (1, 2, 3): _write(tmp_path, f"r{r}_g0.json", [OK_A, OK_B])
    rows, passed, _ = sc.score(tmp_path, GOLD, reps=3)
    assert passed and {x["slug"]: x["type_ok"] for x in rows} == {"a": 3, "b": 3}

def test_score_normalizes_stakes(tmp_path):
    for r in (1, 2, 3): _write(tmp_path, f"r{r}_g0.json", [dict(OK_A, top_stakes="Very High"), OK_B])
    rows, _, _ = sc.score(tmp_path, GOLD, reps=3)
    assert [x for x in rows if x["slug"] == "a"][0]["stakes_ok"] == 3

def test_score_unparsable_counts_unanswered(tmp_path):
    for r in (1, 2, 3): _write(tmp_path, f"r{r}_g0.json", "sorry, here is prose")
    rows, passed, _ = sc.score(tmp_path, GOLD, reps=3)
    assert not passed and all(x["answered"] == 0 for x in rows)

def test_score_fails_tuning_below_bar(tmp_path):
    bad = dict(OK_A, project_type="library")
    _write(tmp_path, "r1_g0.json", [bad, OK_B]); _write(tmp_path, "r2_g0.json", [OK_A, OK_B]); _write(tmp_path, "r3_g0.json", [OK_A, OK_B])
    _, passed, _ = sc.score(tmp_path, GOLD, reps=3)
    assert not passed

def test_score_skips_cases_that_did_not_run(tmp_path):
    for r in (1, 2, 3): _write(tmp_path, f"r{r}_g0.json", [OK_A])
    (tmp_path / "status.json").write_text(json.dumps({"a": "ok", "b": "skipped: local missing"}))
    rows, passed, _ = sc.score(tmp_path, GOLD, reps=3)
    b = [x for x in rows if x["slug"] == "b"][0]
    assert not passed and b["pass"] == "skipped" and b["answered"] == "skipped: local missing"
    assert "skipped: local missing" in sc.table(rows, 0)

def test_score_survives_non_json_and_null_result(tmp_path):
    (tmp_path / "r1_g0.json").write_text("not json at all")
    (tmp_path / "r2_g0.json").write_text(json.dumps({"result": None, "usage": None}))
    rows, passed, tok = sc.score(tmp_path, GOLD, reps=3)
    assert not passed and tok == 0 and all(x["answered"] == 0 for x in rows)

def test_table_uses_real_rep_count(tmp_path):
    for r in (1, 2): _write(tmp_path, f"r{r}_g0.json", [OK_A, OK_B])
    rows, _, _ = sc.score(tmp_path, GOLD, reps=2)
    assert "2/2" in sc.table(rows, 0) and "2/3" not in sc.table(rows, 0)

def test_stakes_normalizes_levels():
    assert sc._stakes("high") == "high" and sc._stakes("Very High") == "very high" and sc._stakes("low") == "low"


import subprocess
import pytest
import run_eval as re_

def test_all_skipped_fails(tmp_path):
    (tmp_path / "status.json").write_text(json.dumps({"a": "fetch failed", "b": "skipped: local missing"}))
    _, passed, _ = sc.score(tmp_path, GOLD, reps=3)
    assert not passed

def test_preflight_rejects_unknown_type():
    assert any("app" in p for p in sc.preflight({"x": dict(GOLD["a"], type="app")}))

def test_preflight_rejects_unknown_kind_and_code():
    probs = sc.preflight({"x": dict(GOLD["a"], kind="likes", code="9z")})
    assert any("likes" in p for p in probs) and any("9z" in p for p in probs)

def test_preflight_accepts_good_gold():
    assert sc.preflight(GOLD) == []

def test_code_scored(tmp_path):
    for r in (1, 2, 3): _write(tmp_path, f"r{r}_g0.json", [OK_A, dict(OK_B, verdict_1_code="1b")])
    rows, _, _ = sc.score(tmp_path, GOLD, reps=3)
    assert [x for x in rows if x["slug"] == "b"][0]["code_ok"] == 0

def test_kind_derived_from_the_answers_type(tmp_path):
    # The answer's own kind is ignored; the kind is what the answer's type gives.
    for r in (1, 2, 3): _write(tmp_path, f"r{r}_g0.json", [dict(OK_A, kind="teaches"), OK_B])
    rows, passed, _ = sc.score(tmp_path, GOLD, reps=3)
    assert [x for x in rows if x["slug"] == "a"][0]["kind_ok"] == 3 and passed
    for r in (1, 2, 3): _write(tmp_path, f"r{r}_g0.json", [dict(OK_A, project_type="guide"), OK_B])
    rows, passed, _ = sc.score(tmp_path, GOLD, reps=3)
    assert [x for x in rows if x["slug"] == "a"][0]["kind_ok"] == 0 and not passed

def test_task_does_not_ask_for_kind():
    task = (pathlib.Path(__file__).parent / "task.md").read_text()
    assert "kind" not in task.replace("kind of", "")

def test_calls_jev_falls_back_to_old_name(tmp_path):
    old = {k: v for k, v in OK_A.items() if k != "calls_jev"}; old["calls_hosted_jev"] = "yes"
    for r in (1, 2, 3): _write(tmp_path, f"r{r}_g0.json", [old, OK_B])
    rows, passed, _ = sc.score(tmp_path, GOLD, reps=3)
    assert passed and [x for x in rows if x["slug"] == "a"][0]["f0_ok"] == 3

def test_top_stakes_compared_directly(tmp_path):
    for r in (1, 2, 3): _write(tmp_path, f"r{r}_g0.json", [dict(OK_A, decisions=[{"stakes": "low"}]), OK_B])
    rows, passed, _ = sc.score(tmp_path, GOLD, reps=3)
    assert [x for x in rows if x["slug"] == "a"][0]["stakes_ok"] == 0 and not passed

def test_synthetic_rows_reported_apart(tmp_path):
    g = dict(GOLD); g["a"] = dict(g["a"], synthetic=True)
    for r in (1, 2, 3): _write(tmp_path, f"r{r}_g0.json", [OK_A, OK_B])
    rows, _, tok = sc.score(tmp_path, g, reps=3)
    t = sc.table(rows, tok)
    assert "Synthetic cases" in t and "Not measured" in t

def test_table_says_n_of_m_cases_ran(tmp_path):
    for r in (1, 2, 3): _write(tmp_path, f"r{r}_g0.json", [OK_A])
    (tmp_path / "status.json").write_text(json.dumps({"a": "ok", "b": "fetch failed"}))
    rows, _, tok = sc.score(tmp_path, GOLD, reps=3)
    assert "1 of 2 cases ran" in sc.table(rows, tok)

def _git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout

def _repo(tmp_path):
    repo = tmp_path / "repo"; (repo / "jevaluate").mkdir(parents=True)
    _git(repo, "init", "-q", "-b", "main"); _git(repo, "config", "user.email", "t@t"); _git(repo, "config", "user.name", "t")
    (repo / "jevaluate" / "rubric.md").write_text("v1\n"); _git(repo, "add", "."); _git(repo, "commit", "-qm", "one")
    _git(repo, "checkout", "-qb", "feature")
    return repo

def test_preflight_repo_clean_passes(tmp_path):
    assert re_.preflight_repo(_repo(tmp_path)) == []

def test_preflight_repo_refuses_uncommitted(tmp_path):
    repo = _repo(tmp_path); (repo / "jevaluate" / "rubric.md").write_text("edited\n")
    assert any("uncommitted" in p.lower() for p in re_.preflight_repo(repo))

def test_preflight_repo_refuses_unmerged_rubric_on_main(tmp_path):
    repo = _repo(tmp_path)
    _git(repo, "checkout", "-q", "main"); (repo / "jevaluate" / "rubric.md").write_text("v2\n")
    _git(repo, "commit", "-qam", "rubric change on main"); _git(repo, "checkout", "-q", "feature")
    probs = re_.preflight_repo(repo)
    assert any("rubric change on main" in p for p in probs)

def test_preflight_repo_ignores_main_commits_outside_skill(tmp_path):
    repo = _repo(tmp_path)
    _git(repo, "checkout", "-q", "main"); (repo / "other.txt").write_text("x\n"); _git(repo, "add", "."); _git(repo, "commit", "-qm", "other")
    _git(repo, "checkout", "-q", "feature")
    assert re_.preflight_repo(repo) == []

def test_system_prompt_is_skill_plus_routing_only():
    text = re_.system_prompt()
    assert (re_.SKILL / "SKILL.md").read_text() in text and "## 1. Routing" in text
    assert "## 2. " not in text and (re_.SKILL / "read.md").read_text() not in text

def test_stamp_records_phase_head_and_fingerprint(tmp_path):
    repo = _repo(tmp_path); out = tmp_path / "out"; out.mkdir()
    re_.write_stamp(out, "baseline", repo, 3)
    d = json.loads((out / "run.json").read_text())
    assert d["phase"] == "baseline" and d["head"] == _git(repo, "rev-parse", "--short", "HEAD").strip() and d["gold_fingerprint"] == sc.fingerprint()

def test_out_must_be_under_work():
    assert re_.preflight_out("/x/jevaluate-eval/.work/run-1") == [] and re_.preflight_out("/x/results/run-1")

def test_score_refuses_run_after_gold_changed(tmp_path):
    (tmp_path / "run.json").write_text(json.dumps({"phase": "baseline", "head": "abc", "gold_fingerprint": "000000000000"}))
    assert sc.check_stamp(tmp_path)
    (tmp_path / "run.json").write_text(json.dumps({"phase": "baseline", "head": "abc", "gold_fingerprint": sc.fingerprint()}))
    assert sc.check_stamp(tmp_path) == []


def test_preflight_real_gold_is_clean():
    import json as _j
    real = _j.loads((pathlib.Path(__file__).parent / "gold.json").read_text())
    assert sc.preflight(real) == []

def test_stakes_not_compared_where_gold_is_na(tmp_path):
    g = {"b": dict(GOLD["b"], top_stakes="n.a.")}
    for r in (1, 2, 3): _write(tmp_path, f"r{r}_g0.json", [dict(OK_B, top_stakes="high")])
    rows, passed, _ = sc.score(tmp_path, g, reps=3)
    assert passed and rows[0]["pass"] is True

def test_stakes_still_compared_where_gold_gives_one(tmp_path):
    for r in (1, 2, 3): _write(tmp_path, f"r{r}_g0.json", [dict(OK_A, decisions=[{"stakes": "low"}]), OK_B])
    rows, passed, _ = sc.score(tmp_path, GOLD, reps=3)
    assert not passed and [x for x in rows if x["slug"] == "a"][0]["stakes_ok"] == 0

def test_guide_f0_exact_match(tmp_path):
    g = {"g": {"set": "tuning", "match": ["guide"], "kind": "teaches", "type": "guide", "f0": "n.a.", "code": "1t", "top_stakes": "n.a."}}
    base = {"project": "guide", "kind": "teaches", "project_type": "guide", "verdict_1_code": "1t", "top_stakes": "n.a."}
    for r in (1, 2, 3): _write(tmp_path, f"r{r}_g0.json", [dict(base, calls_jev="yes")])
    assert sc.score(tmp_path, g, reps=3)[0][0]["f0_ok"] == 0
    for r in (1, 2, 3): _write(tmp_path, f"r{r}_g0.json", [dict(base, calls_jev="no")])
    assert sc.score(tmp_path, g, reps=3)[0][0]["f0_ok"] == 3
    for r in (1, 2, 3): _write(tmp_path, f"r{r}_g0.json", [dict(base, calls_jev="n.a.")])
    rows, passed, _ = sc.score(tmp_path, g, reps=3)
    assert rows[0]["f0_ok"] == 3 and passed


def test_real_gold_guide_is_1t_and_client_stakes_na():
    import json as _j
    real = _j.loads((pathlib.Path(__file__).parent / "gold.json").read_text())
    assert real["building-with-jev-skill"]["code"] == "1t"
    assert real["typesafe-sdk-js"]["top_stakes"] == "n.a."

def test_grader_task_names_1t_and_decision_lines():
    task = (pathlib.Path(__file__).parent / "task.md").read_text()
    assert "1t" in task and "1g" not in task


def test_no_current_replacement_case_carries_a_claim():
    import json as _j
    real = _j.loads((pathlib.Path(__file__).parent / "gold.json").read_text())
    assert {k: v["code"] for k, v in real.items() if v["type"] == "jev-replacement"} == {"jev-omni": "1r", "jevmlx": "1r", "kev": "1r"}

def test_task_asks_for_stakes_as_read_never_na():
    task = (pathlib.Path(__file__).parent / "task.md").read_text()
    line = next(l for l in task.splitlines() if "top_stakes" in l and l.startswith("5b"))
    assert "never n.a." in line and "grader reads" in line

def test_rubric_wording_from_the_quiz_key():
    rub = (pathlib.Path(__file__).parent.parent / "jevaluate" / "rubric.md").read_text()
    for phrase in ("**An AI agent is not a background program.**", "**A project that ignores Jev's answers keeps its type.**",
                   "- **1a False marketing: Jev in name only**: a jev-mention-only or jev-replacement that claims to be or to call Jev.",
                   "- **1r Replaces Jev, not yet rated**: a jev-replacement that doesn't claim to be Jev, until its track exists.",
                   "Never enter n.a.: `library.py add` sets `top_stakes` to n.a. for a guide, a client and any verdict-1 code.",
                   "- **A confirm step lowers the stakes, not the type.**", "Claims to be or call Jev?"):
        assert phrase in rub, phrase
    read = (pathlib.Path(__file__).parent.parent / "jevaluate" / "read.md").read_text()
    assert not any(l.startswith("top_stakes:") for l in read.splitlines()) and "library.py add" in read and "fills" in read

def test_rubric_says_kind_follows_from_type():
    rub = (pathlib.Path(__file__).parent.parent / "jevaluate" / "rubric.md").read_text()
    assert "Four calls come before any fact: type, calls Jev (F0), the verdict-1 code and each decision's stakes. Kind follows from type; `library.py add` fills it in." in rub
    assert "- `kind` values: uses, teaches, replaces, mentions (filled in by code from the type)" in rub


# --- Review fix 5 (2026-09-30): the planned rep count is the denominator ---

def test_a_one_rep_run_of_a_three_rep_plan_fails(tmp_path):
    _write(tmp_path, "r1_g0.json", [OK_A, OK_B])
    rows, passed, _ = sc.score(tmp_path, GOLD, reps=3)
    assert not passed and [x["answered"] for x in rows] == [1, 1]
    assert "1/3" in sc.table(rows, 0, 3)

def test_a_two_rep_run_with_a_heldout_case_right_one_of_two_fails(tmp_path):
    _write(tmp_path, "r1_g0.json", [OK_A, OK_B]); _write(tmp_path, "r2_g0.json", [OK_A, dict(OK_B, project_type="library")])
    _, passed, _ = sc.score(tmp_path, GOLD, reps=2)
    assert not passed
    _write(tmp_path, "r2_g0.json", [OK_A, OK_B]); assert sc.score(tmp_path, GOLD, reps=2)[1]

def test_score_needs_the_planned_rep_count(tmp_path):
    with pytest.raises(ValueError, match="--reps"): sc.score(tmp_path, GOLD)

def _cli(run, *extra):
    """score.py's command line, run in this process so conftest's GitHub stub applies (no API calls from tests)."""
    import contextlib, io, runpy, types
    out, err, argv = io.StringIO(), io.StringIO(), sys.argv
    sys.argv = [sc.__file__, str(run), *extra]; code = 0
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err): runpy.run_path(sc.__file__, run_name="__main__")
    except SystemExit as e:
        code = e.code if isinstance(e.code, int) else (0 if e.code is None else (print(e.code, file=err) or 1))
    finally: sys.argv = argv
    return types.SimpleNamespace(returncode=code, stdout=out.getvalue(), stderr=err.getvalue())

def test_cli_refuses_an_old_run_without_a_rep_count_unless_given_reps(tmp_path):
    for r in (1, 2, 3): _write(tmp_path, f"r{r}_g0.json", [OK_A, OK_B])
    (tmp_path / "run.json").write_text(json.dumps({"phase": "baseline", "head": "abc", "gold_fingerprint": sc.fingerprint()}))
    p = _cli(tmp_path); assert p.returncode == 2 and "--reps" in p.stderr and "no rep count" in p.stderr
    p = _cli(tmp_path, "--reps", "3"); assert "--reps" not in p.stderr and "Traceback" not in p.stderr

@pytest.mark.skipif(sc.rubric_text.frozen_status()[0] != "frozen", reason="needs a frozen checkout (a rubric-change branch isn't one until its freeze)")
def test_cli_takes_the_rep_count_from_run_json_and_refuses_a_mismatch(tmp_path):
    _write(tmp_path, "r1_g0.json", [OK_A, OK_B])
    (tmp_path / "run.json").write_text(json.dumps({"phase": "baseline", "head": "abc", "gold_fingerprint": sc.fingerprint(), "reps": 3, "rubric_status": "frozen", "golden": sc.rubric_text.golden_hash(ref=sc.rubric_text.newest_tag())}))
    p = _cli(tmp_path); assert p.returncode == 1 and "/3 |" in p.stdout and "/1 |" not in p.stdout
    p = _cli(tmp_path, "--reps", "1"); assert p.returncode == 2 and "reps" in p.stderr

def test_stamp_records_the_planned_reps(tmp_path):
    repo = _repo(tmp_path); out = tmp_path / "out"; out.mkdir()
    re_.write_stamp(out, "baseline", repo, 3)
    assert json.loads((out / "run.json").read_text())["reps"] == 3


# --- Review fix 3 (2026-09-30): top stakes come from the decisions list, as library.py derives them ---
def _stakes_row(tmp_path, answer):
    for r in (1, 2, 3): _write(tmp_path, f"r{r}_g0.json", [answer, OK_B])
    rows, _, _ = sc.score(tmp_path, GOLD, reps=3)
    return [x for x in rows if x["slug"] == "a"][0]

def test_stated_top_stakes_that_the_decisions_do_not_support_does_not_score(tmp_path):
    row = _stakes_row(tmp_path, dict(OK_A, top_stakes="very high", decisions=[{"stakes": "low"}, {"stakes": "high"}]))
    assert row["stakes_ok"] == 0 and not row["pass"]

def test_top_stakes_is_the_highest_level_in_the_decisions_whatever_the_grader_stated(tmp_path):
    row = _stakes_row(tmp_path, dict(OK_A, top_stakes="low", decisions=[{"stakes": "low"}, {"stakes": "Very High"}, {"stakes": "high"}]))
    assert row["stakes_ok"] == 3 and row["pass"]

def test_no_decisions_means_no_top_stakes(tmp_path):
    assert _stakes_row(tmp_path, dict(OK_A, top_stakes="very high", decisions=[]))["stakes_ok"] == 0

def test_score_uses_the_ordering_function_library_uses():
    import library
    assert sc.highest_stakes.__code__.co_filename == library.highest_stakes.__code__.co_filename  # not a copy (another test file may load a second library module object)
    assert library.highest_stakes(["low", "very high", "high"]) == "very high" and library.highest_stakes([]) is None


# --- Review fix 4 (2026-09-30): a skipped tuning case fails the run; a used --out folder is refused ---
def test_a_skipped_tuning_case_fails_the_run_and_is_listed(tmp_path):
    for r in (1, 2, 3): _write(tmp_path, f"r{r}_g0.json", [OK_B])
    (tmp_path / "status.json").write_text(json.dumps({"a": "skipped: fetch failed", "b": "ok"}))
    rows, passed, tok = sc.score(tmp_path, GOLD, reps=3)
    assert not passed
    out = sc.table(rows, tok, 3)
    assert "Skipped, so the run fails: a (skipped: fetch failed)" in out

def test_a_run_with_nothing_skipped_lists_no_skips(tmp_path):
    for r in (1, 2, 3): _write(tmp_path, f"r{r}_g0.json", [OK_A, OK_B])
    rows, passed, tok = sc.score(tmp_path, GOLD, reps=3)
    assert passed and "Skipped" not in sc.table(rows, tok, 3)

def test_run_eval_refuses_a_non_empty_out_folder(tmp_path):
    import run_eval
    out = tmp_path / ".work" / "run"; out.mkdir(parents=True)
    assert run_eval.preflight_out(out) == []
    (out / "r1_g0.json").write_text("{}")
    probs = run_eval.preflight_out(out)
    assert len(probs) == 1 and "not empty" in probs[0] and "r1_g0.json" in probs[0] and "new --out" in probs[0]

def test_runs_folder_setting_moves_run_output_outside_the_repo(tmp_path, monkeypatch):
    import run_eval
    runs = tmp_path / "vault-runs"
    monkeypatch.setenv("JEVALUATE_RUNS", str(runs))
    assert run_eval.runs_dir() == runs.resolve()
    assert run_eval.preflight_out(runs / "baseline-1") == []
    probs = run_eval.preflight_out(tmp_path / "jevaluate-eval" / ".work" / "run-1")
    assert len(probs) == 1 and "JEVALUATE_RUNS" in probs[0]

def test_runs_folder_setting_must_be_absolute_and_outside_the_repo(tmp_path, monkeypatch):
    import run_eval
    repo = run_eval.HERE.parent
    for bad, why in [("", "blank"), ("   ", "blank"), ("rel/runs", "relative"), (str(repo / "jevaluate-eval"), "inside the repo"),
                     (str(repo), "inside the repo"), (str(repo.parent), "inside the repo or holds it")]:
        monkeypatch.setenv("JEVALUATE_RUNS", bad)
        probs = run_eval.preflight_out(tmp_path / "x")
        assert len(probs) == 1 and why.split()[0] in probs[0], (bad, probs)

def test_out_equal_to_the_runs_folder_is_refused(tmp_path, monkeypatch):
    import run_eval
    runs = tmp_path / "runs"; runs.mkdir()
    monkeypatch.setenv("JEVALUATE_RUNS", str(runs))
    assert run_eval.preflight_out(runs) and not run_eval.preflight_out(runs / "r1")

def test_work_rule_reads_the_resolved_path(tmp_path):
    import run_eval
    assert run_eval.preflight_out(tmp_path / "x" / ".work" / ".." / ".." / "y")

def test_without_the_setting_runs_stay_under_work(monkeypatch):
    import run_eval
    monkeypatch.delenv("JEVALUATE_RUNS", raising=False)
    assert run_eval.runs_dir().name == ".work"

def test_run_eval_accepts_an_out_folder_that_does_not_exist_yet(tmp_path):
    import run_eval
    assert run_eval.preflight_out(tmp_path / ".work" / "new") == []


@pytest.mark.skipif(sc.rubric_text.frozen_status()[0] != "frozen", reason="needs a frozen checkout (a rubric-change branch isn't one until its freeze)")
def test_stamp_line_reads_run_json(tmp_path):
    (tmp_path / "run.json").write_text(json.dumps({"phase": "after", "head": "abc1234", "rubric": "2026-09-29", "rubric_status": "frozen", "golden": sc.rubric_text.golden_hash(ref=sc.rubric_text.newest_tag())}))
    line = sc.stamp_line(tmp_path, True)
    assert line == "Run: phase=after rubric=2026-09-29 commit=abc1234 passed=yes"
    assert sc.stamp_line(tmp_path, False).endswith("passed=no")


def test_stamp_uses_the_rubric_the_run_was_made_on(tmp_path):
    (tmp_path / "run.json").write_text(json.dumps({"phase": "baseline", "head": "abc1234", "rubric": "2026-01-01"}))
    assert " rubric=2026-01-01 " in sc.stamp_line(tmp_path, True)

def test_a_run_with_no_recorded_rubric_is_stamped_unknown(tmp_path):
    (tmp_path / "run.json").write_text(json.dumps({"phase": "baseline", "head": "abc1234"}))
    assert " rubric=unknown " in sc.stamp_line(tmp_path, True)


def test_write_stamp_records_the_rubric_version(tmp_path):
    import run_eval as re_
    repo = tmp_path / "repo"; repo.mkdir()
    import subprocess
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "-c", "user.email=a@b", "-c", "user.name=a", "commit", "-q", "--allow-empty", "-m", "x"], check=True)
    out = tmp_path / "out"; out.mkdir()
    re_.write_stamp(out, "baseline", repo, 3)
    assert json.loads((out / "run.json").read_text())["rubric"] == sc.rubric_text.version()

def test_old_runs_answering_demo_score_as_display():
    import score
    g = {"type": "display", "kind": "uses"}
    assert score.type_matches({"project_type": "demo"}, g) and score.type_matches({"project_type": "display"}, g)
    assert not score.type_matches({"project_type": "workflow"}, g)

@pytest.mark.skipif(sc.rubric_text.frozen_status()[0] != "frozen", reason="needs a frozen checkout (a rubric-change branch isn't one until its freeze)")
def test_candidate_rubric_is_labeled_not_of_record(tmp_path):
    import json, score
    (tmp_path / "run.json").write_text(json.dumps({"phase": "after", "rubric": "2099-01-01", "rubric_status": "unfrozen", "rubric_detail": "no tag"}))
    assert "not a result of record" in score.rubric_note(tmp_path) and "CANDIDATE" in score.stamp_line(tmp_path, True)
    (tmp_path / "run.json").write_text(json.dumps({"phase": "after", "rubric": "2026-09-29.1", "rubric_status": "frozen", "golden": score.rubric_text.golden_hash(ref=score.rubric_text.newest_tag())}))
    assert score.rubric_note(tmp_path) == ""

@pytest.mark.skipif(sc.rubric_text.frozen_status()[0] != "frozen", reason="needs a frozen checkout (a rubric-change branch isn't one until its freeze)")
def test_scoring_fails_closed_without_a_verified_frozen_stamp(tmp_path, monkeypatch):
    import json, score
    good = score.rubric_text.golden_hash(score.rubric_text.ROOT, ref=score.rubric_text.newest_tag(score.rubric_text.ROOT))
    (tmp_path / "run.json").write_text(json.dumps({"rubric_status": "frozen", "golden": good}))
    assert score.of_record(tmp_path)[0]
    for bad in ({}, {"rubric_status": "frozen"}, {"rubric_status": "frozen", "golden": "0" * 64}, {"rubric_status": "changed", "golden": good}):
        (tmp_path / "run.json").write_text(json.dumps(bad)); assert not score.of_record(tmp_path)[0], bad
    (tmp_path / "run.json").write_text(json.dumps({"rubric_status": "frozen", "golden": good}))
    monkeypatch.setattr(score.rubric_text, "frozen_status", lambda root=None: ("changed", "edited"))
    assert not score.of_record(tmp_path)[0]
    assert score.overall_line(True, tmp_path).startswith("Overall: CANDIDATE") and "PASS" not in score.overall_line(True, tmp_path)


@pytest.mark.skipif(sc.rubric_text.frozen_status()[0] != "frozen", reason="needs a frozen checkout (a rubric-change branch isn't one until its freeze)")
def test_of_record_needs_the_freeze_on_github(tmp_path, monkeypatch):
    import json, score
    good = score.rubric_text.golden_hash(ref=score.rubric_text.newest_tag())
    (tmp_path / "run.json").write_text(json.dumps({"rubric_status": "frozen", "golden": good}))
    monkeypatch.setattr(score, "tag_on_origin", lambda tag: False)
    ok, why = score.of_record(tmp_path); assert not ok and "GitHub" in why
