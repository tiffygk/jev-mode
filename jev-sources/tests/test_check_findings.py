"""check_findings.py: checks every reader's finding lines against the saved reading plan, and never prints section text.
The library is invented and lives in tmp_path; the plan file is written by the test."""
import json, os, subprocess, sys
import pytest

CODE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(CODE, "scripts")
PID = "p1a2b3c4d"
ALPHA = "Alpha holds the first secret rule: every box answers within five seconds."
BETA = "Beta holds the other rule: a state carries at most nine fields."
GAMMA = "Gamma says nothing about limits at all."
PAGES = {
    "docs/one.md": f"# One\n\nIntro.\n\n## Alpha\n\n{ALPHA}\n\n## Beta\n\n{BETA}\n",
    "docs/two.md": f"# Two\n\n## Gamma\n\n{GAMMA}\n\nLine with a bell \x07 inside.\n",
}


@pytest.fixture
def lib(tmp_path, monkeypatch):
    data = tmp_path / "data"
    for p, text in PAGES.items():
        (data / p).parent.mkdir(parents=True, exist_ok=True)
        (data / p).write_text(text)
    monkeypatch.setenv("JEV_SOURCES_DATA", str(data))
    monkeypatch.setenv("JEV_SEMANTIC", "off")
    monkeypatch.setenv("JEV_PRIVATE_CONFIG", str(tmp_path / "absent.json"))
    monkeypatch.syspath_prepend(SCRIPTS)
    for n in ("paths", "build_index", "route", "read", "check_findings", "usage_log", "applicability"):
        sys.modules.pop(n, None)
    import build_index
    monkeypatch.setattr(build_index, "embed", lambda rows: None)
    build_index.main()
    return data


def sid(data, path, heading):
    return [r["id"] for r in map(json.loads, open(data / "sections.jsonl")) if r["path"] == path and r["heading"] == heading][0]


def save_plan(data, batches, pid=PID):
    (data / "plans").mkdir(exist_ok=True)
    (data / "plans" / (pid + ".json")).write_text(json.dumps(
        {"plan_id": pid, "created": "2026-10-20T10:00:00Z", "goal": ["g"],
         "batches": [{"n": i, "ids": ids, "tokens": 100} for i, ids in enumerate(batches, 1)]}))


def finding(cite, quote, sentence="A rule."):
    return f'FINDING: {sentence} | CITE AS: {cite} | QUOTE: "{quote}"'


def reply(n, *lines, pid=PID):
    return "\n".join([f"JEV-READER: plan {pid} batch {n}", *lines]) + "\n"


@pytest.fixture
def plan(lib):
    a, b, g = sid(lib, "docs/one.md", "Alpha"), sid(lib, "docs/one.md", "Beta"), sid(lib, "docs/two.md", "Gamma")
    save_plan(lib, [[a, b], [g]])
    import check_findings
    return check_findings, a, b, g


def test_all_findings_ok_prints_ok_rows_and_a_summary_and_exits_0(plan):
    cf, a, b, g = plan
    text = reply(1, finding("docs/one.md#Alpha (reference rule)", "every box answers within five seconds"),
                 finding(b, "a state carries at most nine fields")) + reply(2, finding("docs/two.md#Gamma", "says nothing about limits"))
    rows, summary, ok = cf.check(PID, text)
    assert rows == ["OK | b1 | docs/one.md#Alpha (reference rule)", f"OK | b1 | {b}", "OK | b2 | docs/two.md#Gamma"]
    assert summary == f"plan {PID}: 2 batches, 2 reported, 0 missing; 3 findings, 3 OK, 0 failed" and ok is True


def test_an_altered_quote_is_flagged_with_the_section_it_is_found_under(plan):
    cf, a, b, g = plan
    rows, summary, ok = cf.check(PID, reply(1, finding(a, "every box answers within five seconds"), finding(a, "every box answers within nine fields"),
                                           finding("docs/one.md#Alpha", "a state carries at most nine fields")) + reply(2, finding(g, "x")))
    assert rows[0] == f"OK | b1 | {a}"
    assert rows[1] == f"QUOTE NOT FOUND | b1 | {a}"
    assert rows[2].startswith("QUOTE NOT FOUND | b1 | docs/one.md#Alpha | found under docs/one.md#Beta")
    assert not ok and "failed" in summary


def test_a_finding_from_another_batch_is_not_in_batch(plan):
    cf, a, b, g = plan
    rows, summary, ok = cf.check(PID, reply(1, finding(g, "says nothing about limits at all")) + reply(2, finding(g, "says nothing")))
    assert rows[0] == f"NOT IN BATCH | b1 | {g}" and rows[1] == f"OK | b2 | {g}"
    assert not ok


def test_a_cite_that_names_no_section_is_not_in_batch(plan):
    cf, *_ = plan
    rows, _, ok = cf.check(PID, reply(1, finding("docs/none.md#Nope", "x")) + reply(2))
    assert rows[0] == "NOT IN BATCH | b1 | docs/none.md#Nope" and not ok


def test_a_malformed_line_is_flagged_with_its_first_80_characters(plan):
    cf, a, *_ = plan
    bad = "FINDING: no cite or quote here " + "x" * 100
    rows, summary, ok = cf.check(PID, reply(1, bad, "FINDING: s | CITE AS: docs/one.md#Alpha | QUOTE: \"\"") + reply(2))
    assert rows[0] == "MALFORMED | b1 | " + bad[:80] and rows[1].startswith("MALFORMED | b1 | ")
    assert not ok and "2 findings, 0 OK, 2 failed" in summary


def test_a_batch_with_no_reply_is_missing(plan):
    cf, a, b, g = plan
    rows, summary, ok = cf.check(PID, reply(1, finding(a, "every box answers")))
    assert summary == f"plan {PID}: 2 batches, 1 reported, 1 missing (b2); 1 findings, 1 OK, 0 failed" and not ok


def test_page_text_is_flagged_and_so_is_a_thirteenth_finding(plan):
    cf, a, *_ = plan
    prose = "The box answers within five seconds because " + "words " * 40
    rows, _, ok = cf.check(PID, reply(1, prose, finding(a, "every box")) + reply(2))
    assert rows[0] == "PAGE TEXT | b1 | " + prose[:80] and not ok
    many = [finding(a, "every box")] * 13
    rows, _, ok = cf.check(PID, reply(1, *many) + reply(2))
    assert "TOO MANY | b1 | 13" in rows and not ok
    rows, _, ok = cf.check(PID, reply(1, *many[:12]) + reply(2, finding(sid_gamma(plan), "says")))
    assert not any(r.startswith("TOO MANY") for r in rows)


def sid_gamma(plan):
    return plan[3]


def test_nothing_from_a_section_body_is_printed(plan):
    cf, a, *_ = plan
    rows, summary, _ = cf.check(PID, reply(1, finding(a, "every box answers within nine fields"), finding(a, "every box")) + reply(2))
    printed = "\n".join(rows) + summary
    assert "secret rule" not in printed and "five seconds" not in printed.replace("every box answers within five", "")


def test_a_control_character_in_an_echoed_string_prints_as_a_question_mark(plan):
    cf, *_ = plan
    rows, _, _ = cf.check(PID, reply(1, "FINDING: bad\x07 line") + reply(2))
    assert rows[0] == "MALFORMED | b1 | FINDING: bad? line"
    rows, _, _ = cf.check(PID, reply(1, finding("docs/none\x1b.md#Nope", "x")) + reply(2))
    assert "\x1b" not in rows[0] and "?" in rows[0]


def test_a_reply_for_another_plan_is_ignored_and_a_missing_plan_says_so(plan, lib):
    cf, a, *_ = plan
    rows, summary, ok = cf.check(PID, reply(1, finding(a, "every box"), pid="p00000000"))
    assert rows == [] and "2 missing (b1, b2)" in summary and not ok
    rows, summary, ok = cf.check("pdeadbeef", "x")
    assert rows == ["NO PLAN | pdeadbeef"] and summary is None and ok is False


def run_cli(lib, plan_id, text):
    env = {**os.environ, "JEV_SOURCES_DATA": str(lib), "JEV_LOG": "off", "JEV_SEMANTIC": "off"}
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, "check_findings.py"), plan_id], input=text, capture_output=True, text=True, env=env)


def test_cli_exit_codes_and_output(plan, lib):
    cf, a, b, g = plan
    good = reply(1, finding(a, "every box"), finding(b, "at most nine")) + reply(2, finding(g, "nothing about limits"))
    r = run_cli(lib, PID, good)
    assert r.returncode == 0 and r.stdout.splitlines()[-1] == f"plan {PID}: 2 batches, 2 reported, 0 missing; 3 findings, 3 OK, 0 failed"
    r = run_cli(lib, PID, reply(1, finding(a, "every box altered")) + reply(2))
    assert r.returncode == 1 and r.stdout.startswith(f"QUOTE NOT FOUND | b1 | {a}")
    r = run_cli(lib, "pdeadbeef", "")
    assert r.returncode == 2 and r.stdout == "NO PLAN | pdeadbeef\n"


def test_a_reader_that_returns_only_its_header_is_flagged_empty(plan):
    cf, a, b, g = plan
    rows, summary, ok = cf.check(PID, reply(1, finding(a, ALPHA)) + reply(2))
    assert "EMPTY | b2 | no findings" in rows and not ok
    rows, summary, ok = cf.check(PID, reply(1, finding(a, ALPHA)) + reply(2, "Nothing relevant here."))
    assert "EMPTY | b2 | no findings" in rows and not ok


def test_a_plan_id_with_a_trailing_newline_is_no_plan(plan):
    cf = plan[0]
    rows, summary, ok = cf.check(PID + "\n", "")
    assert summary is None and rows[0].startswith("NO PLAN")


def test_one_batch_summary_says_batch(lib):
    a = sid(lib, "docs/one.md", "Alpha")
    save_plan(lib, [[a]])
    import check_findings
    rows, summary, ok = check_findings.check(PID, reply(1, finding(a, ALPHA)))
    assert ok and summary.startswith(f"plan {PID}: 1 batch, 1 reported")


def test_invalid_utf8_on_stdin_is_flagged_not_a_crash(lib):
    a = sid(lib, "docs/one.md", "Alpha")
    save_plan(lib, [[a]])
    data = reply(1, finding(a, ALPHA)).encode() + b"FINDING: bad \xff bytes | CITE AS: x | QUOTE: \"y\"\n"
    r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "check_findings.py"), PID], input=data, capture_output=True,
                       env={**os.environ, "JEV_SOURCES_DATA": str(lib), "JEV_SEMANTIC": "off"})
    assert r.returncode == 1 and b"Traceback" not in r.stderr


def test_a_numeric_id_in_parentheses_in_place_of_the_label_is_accepted(plan):
    cf, a, b, g = plan
    rows, summary, ok = cf.check(PID, reply(1, finding(f"docs/one.md#Alpha ({a})", ALPHA)) + reply(2, finding(g, GAMMA)))
    assert ok and rows[0].startswith("OK | b1"), rows
    rows, summary, ok = cf.check(PID, reply(1, finding(f"docs/one.md#Alpha ({a})", "every box answers within nine seconds")) + reply(2, finding(g, GAMMA)))
    assert rows[0].startswith("QUOTE NOT FOUND | b1"), rows
