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
    assert rows[0] == f'PAGE TEXT | b1 | line starting "The box answers within five" ({len(prose.strip())} characters)' and not ok
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


def test_page_text_before_the_header_is_flagged(plan):
    cf, a, b, g = plan
    rows, _, ok = cf.check(PID, ALPHA + "\n" + reply(1, finding(a, ALPHA)) + reply(2, finding(g, GAMMA)))
    assert f'PAGE TEXT | b1 | line starting "Alpha holds the first secret" ({len(ALPHA)} characters)' in rows and not ok


def test_a_section_pasted_line_by_line_is_page_text(plan):
    cf, a, b, g = plan
    rows, _, ok = cf.check(PID, reply(1, finding(a, ALPHA), BETA) + reply(2, finding(g, GAMMA)))
    assert any(r.startswith("PAGE TEXT | b1") for r in rows) and not ok
    rows, _, ok = cf.check(PID, reply(1, "Here are my findings.", finding(a, ALPHA)) + reply(2, finding(g, GAMMA)))
    assert ok, rows  # a short note of the reader's own is not page text


def test_a_quote_or_sentence_over_the_cap_is_flagged(plan):
    cf, a, b, g = plan
    long_q = (ALPHA + " ") * 5
    rows, _, ok = cf.check(PID, reply(1, finding(a, long_q.strip())) + reply(2, finding(g, GAMMA)))
    assert rows[0].startswith("TOO LONG | b1") and not ok
    rows, _, ok = cf.check(PID, reply(1, finding(a, ALPHA, sentence=BETA * 6)) + reply(2, finding(g, GAMMA)))
    assert rows[0].startswith("TOO LONG | b1") and not ok


def test_a_cite_holding_section_text_echoes_at_most_80_characters(plan):
    cf, a, b, g = plan
    rows, _, ok = cf.check(PID, reply(1, finding((BETA + " ") * 4, ALPHA)) + reply(2, finding(g, GAMMA)))
    assert not ok and all(len(r.split(" | ", 2)[2]) <= 80 for r in rows if r.count(" | ") >= 2)


def test_a_damaged_plan_file_reads_as_no_plan(lib):
    (lib / "plans").mkdir(exist_ok=True)
    (lib / "plans" / (PID + ".json")).write_text('{"batches": [{"x": 1}]}')
    import check_findings
    rows, summary, ok = check_findings.check(PID, "")
    assert summary is None and rows[0].startswith("NO PLAN")


@pytest.mark.parametrize("line", [f"- **Rule:** {BETA}", f'The page says "{BETA}"', f"{BETA} (docs/one#2)",
                                  BETA.replace(":", "").replace(",", "")])
def test_page_text_behind_a_label_lead_in_or_citation_is_flagged(plan, line):
    cf, a, b, g = plan
    rows, _, ok = cf.check(PID, reply(1, finding(a, ALPHA), line) + reply(2, finding(g, GAMMA)))
    assert any(r.startswith("PAGE TEXT | b1") for r in rows) and not ok, rows


def test_seven_words_in_a_row_from_a_section_pass_and_eight_are_page_text(plan):
    cf, a, b, g = plan
    seven = "Note: beta holds the other rule, a state."  # 7 words in a row from Beta, plus one of the reader's own
    rows, _, ok = cf.check(PID, reply(1, finding(a, ALPHA), seven) + reply(2, finding(g, GAMMA)))
    assert ok, rows
    rows, _, ok = cf.check(PID, reply(1, finding(a, ALPHA), seven[:-1] + " carries.") + reply(2, finding(g, GAMMA)))
    assert any(r.startswith("PAGE TEXT | b1") for r in rows) and not ok, rows


def test_many_short_lines_outside_findings_pass_the_budget_and_are_flagged(plan):
    cf, a, b, g = plan
    notes = ["Line %d of my own notes here." % i for i in range(25)]  # about 750 characters, no copied run
    rows, _, ok = cf.check(PID, reply(1, finding(a, ALPHA), *notes) + reply(2, finding(g, GAMMA)))
    assert any(r.startswith("PAGE TEXT | b1 |") and "characters outside finding lines" in r for r in rows) and not ok
    rows, _, ok = cf.check(PID, reply(1, finding(a, ALPHA), *notes[:5]) + reply(2, finding(g, GAMMA)))
    assert ok, rows


LONG = " ".join("d%03d" % i for i in range(59))  # 294 characters


def test_quote_and_sentence_caps_sit_at_300_characters(lib):
    (lib / "docs" / "three.md").write_text(f"# Three\n\n## Delta\n\n{LONG} abc end.\n\n{LONG} abcd end.\n")
    import build_index
    build_index.main()
    d = sid(lib, "docs/three.md", "Delta")
    save_plan(lib, [[d]], pid="pcap00001")
    import check_findings as cf
    at, over = LONG + " abc", LONG + " abcd"  # with quote marks: 300 and 301 characters
    rows, _, _ = cf.check("pcap00001", reply(1, finding(d, at), pid="pcap00001"))
    assert rows[0].startswith("OK | b1"), rows
    rows, _, _ = cf.check("pcap00001", reply(1, finding(d, over), pid="pcap00001"))
    assert rows[0].startswith("TOO LONG | b1"), rows
    rows, _, _ = cf.check("pcap00001", reply(1, finding(d, at, sentence="s" * 300), pid="pcap00001"))
    assert rows[0].startswith("OK | b1"), rows
    rows, _, _ = cf.check("pcap00001", reply(1, finding(d, at, sentence="s" * 301), pid="pcap00001"))
    assert rows[0].startswith("TOO LONG | b1"), rows


def test_an_unresolved_cite_over_80_characters_echoes_80_and_one_over_200_is_too_long(plan):
    cf, a, b, g = plan
    cite = "docs/nowhere.md#" + "x" * 134  # 150 characters
    rows, _, ok = cf.check(PID, reply(1, finding(cite, ALPHA)) + reply(2, finding(g, GAMMA)))
    assert rows[0] == "NOT IN BATCH | b1 | " + cite[:80] and not ok, rows
    long_cite = f"{BETA} {BETA} {BETA} {BETA} ({a})"  # resolves by its id tail, but carries page text
    rows, _, ok = cf.check(PID, reply(1, finding(long_cite, ALPHA)) + reply(2, finding(g, GAMMA)))
    assert rows[0].startswith("TOO LONG | b1") and BETA not in rows[0] and not ok, rows


def test_a_short_code_sample_of_the_readers_own_is_not_page_text(plan):
    cf, a, b, g = plan
    code = ["```python", "client.ask(state=post, questions=qs)", "```"]
    rows, _, ok = cf.check(PID, reply(1, finding(a, ALPHA), *code) + reply(2, finding(g, GAMMA)))
    assert ok, rows


def test_a_page_only_cite_whose_quote_repeats_on_the_page_counts_the_section_in_the_batch(lib):
    (lib / "docs" / "five.md").write_text("# Five\n\n## First\n\nThe shared rule holds in both places here.\n\n## Second\n\nThe shared rule holds in both places here.\n")
    import build_index
    build_index.main()
    second = sid(lib, "docs/five.md", "Second")
    save_plan(lib, [[second]], pid="ppage0001")
    import check_findings as cf
    rows, _, ok = cf.check("ppage0001", reply(1, finding("docs/five.md", "The shared rule holds in both places here"), pid="ppage0001"))
    assert rows[0].startswith("OK | b1") and ok, rows


def test_a_cite_whose_label_carries_extra_marks_still_names_its_section(plan):
    cf, a, b, g = plan
    rows, _, ok = cf.check(PID, reply(1, finding("docs/one.md#Alpha (reference rule, experimental, needs jev-1.14.0+)", ALPHA))
                           + reply(2, finding(g, GAMMA)))
    assert rows[0].startswith("OK | b1") and ok, rows


def test_a_quote_with_escaped_quote_marks_matches_the_page(lib):
    (lib / "docs" / "eight.md").write_text('# Eight\n\n## Code\n\nWrite "relevance": probabilities.get(line_id(i), 0.0) for each line.\n')
    import build_index
    build_index.main()
    s = sid(lib, "docs/eight.md", "Code")
    save_plan(lib, [[s]], pid="pesc00001")
    import check_findings as cf
    rows, _, ok = cf.check("pesc00001", reply(1, 'FINDING: Code. | CITE AS: docs/eight.md#Code | QUOTE: "\\"relevance\\": probabilities.get(line_id(i), 0.0)"', pid="pesc00001"))
    assert rows[0].startswith("OK | b1") and ok, rows
