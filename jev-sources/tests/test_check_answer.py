"""check_answer.py: every docs quote in an answer is checked against the section it cites, and no page text is printed.
The library is invented and lives in tmp_path."""
import json, os, subprocess, sys
import pytest

CODE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(CODE, "scripts")
ALPHA = "Alpha holds the first secret rule: every box answers within five seconds."
BETA = "Beta holds the other rule: a state carries at most nine fields."
GAMMA = "Gamma says the body is over 32 MiB when it is rejected."
PAGES = {
    "docs/one.md": f"# One\n\nIntro.\n\n## Alpha\n\n{ALPHA}\n\n## Beta\n\n{BETA}\n",
    "docs/two.md": f"# Two\n\n## Gamma\n\n{GAMMA}\n",
}


@pytest.fixture
def ca(tmp_path, monkeypatch):
    data = tmp_path / "data"
    for p, text in PAGES.items():
        (data / p).parent.mkdir(parents=True, exist_ok=True)
        (data / p).write_text(text)
    monkeypatch.setenv("JEV_SOURCES_DATA", str(data))
    monkeypatch.setenv("JEV_SEMANTIC", "off")
    monkeypatch.setenv("JEV_PRIVATE_CONFIG", str(tmp_path / "absent.json"))
    monkeypatch.syspath_prepend(SCRIPTS)
    for n in ("paths", "build_index", "route", "read", "check_findings", "check_answer", "usage_log", "applicability"):
        sys.modules.pop(n, None)
    import build_index
    monkeypatch.setattr(build_index, "embed", lambda rows: None)
    build_index.main()
    import check_answer
    return check_answer


def verdicts(rows):
    return [r.split(" | ")[0] for r in rows]


def test_a_quote_on_its_cited_section_is_found(ca):
    rows, summary, ok = ca.check(f'- **Speed:** "every box answers within five seconds" (`docs/one.md#Alpha`, reference rule)\n')
    assert verdicts(rows) == ["FOUND"] and ok and "1 quote" in summary


def test_curly_quotes_a_cite_before_the_quote_and_an_elision(ca):
    rows, _, ok = ca.check("- `docs/one.md#Alpha` says “Alpha holds the first … within five seconds.”\n")
    assert verdicts(rows) == ["FOUND"] and ok, rows


def test_an_altered_quote_is_not_found_and_fails(ca):
    rows, summary, ok = ca.check('- "every box answers within five minutes" (`docs/one.md#Alpha`)\n')
    assert verdicts(rows) == ["NOT FOUND"] and not ok and "1 not found" in summary


def test_a_quote_cited_under_the_wrong_heading_names_the_section_that_holds_it(ca):
    rows, _, ok = ca.check('- "a state carries at most nine fields" (`docs/one.md#Alpha`)\n')
    assert rows[0].startswith("NOT FOUND") and "found under docs/one.md#Beta" in rows[0] and not ok


def test_a_table_row_uses_the_citation_in_the_line_above_the_table(ca):
    answer = ("## Errors\n\n- **Codes** (`docs/two.md#Gamma`, reference rule):\n\n| Code | Meaning |\n|---|---|\n"
              '| 413 | "the body is over 32 MiB" |\n')
    rows, _, ok = ca.check(answer)
    assert verdicts(rows) == ["FOUND"] and ok, rows


def test_an_earlier_citation_does_not_reach_past_a_heading(ca):
    answer = '## One\n\n- (`docs/two.md#Gamma`)\n\n## Two\n\n- "the body is over 32 MiB when it is rejected"\n'
    rows, _, ok = ca.check(answer)
    assert verdicts(rows) == ["UNCITED"] and not ok, rows


def test_numeric_ids_page_only_cites_and_labels_inside_the_backticks_resolve(ca):
    for cite in ("docs/one#1", "docs/one.md", "docs/one.md#Alpha (reference rule)"):
        rows, _, ok = ca.check(f'- "every box answers within five seconds" (`{cite}`)\n')
        assert verdicts(rows) == ["FOUND"] and ok, (cite, rows)


def test_a_cite_that_names_no_section_fails(ca):
    rows, _, ok = ca.check('- "every box answers within five seconds" (`docs/nowhere.md#Alpha`)\n')
    assert verdicts(rows) == ["BAD CITE"] and not ok, rows


def test_a_short_quoted_term_and_code_spans_are_not_checked(ca):
    rows, summary, ok = ca.check('- The "danger zone" header and `{"request_id": "abc def ghi jkl"}` (`docs/one.md#Alpha`)\n')
    assert rows == [] and ok and summary.startswith("answer check: 0 quotes")


def test_a_quote_in_a_block_labeled_unverified_is_labeled_not_failed(ca):
    rows, _, ok = ca.check('- "every box answers within an hour" (`docs/one.md#Alpha`). This quote is unverified.\n')
    assert verdicts(rows) == ["LABELED"] and ok, rows


def test_an_answer_with_no_library_citation_is_not_a_jev_answer(ca):
    rows, summary, ok = ca.check('She said "this is a quote of four words or more" in the meeting.\n')
    assert rows == [] and ok and summary is None


def test_escaped_markdown_inside_a_quote_still_matches(ca):
    rows, _, ok = ca.check('- "a state carries at most nine fields\\." (`docs/one.md#Beta`)\n')
    assert verdicts(rows) == ["FOUND"] and ok, rows


def test_output_never_holds_page_text(ca):
    answer = (f'- "{ALPHA}" (`docs/one.md#Beta`)\n- "{BETA}" (`docs/one.md#Beta`)\n- "{GAMMA} extra words" (`docs/two.md#Gamma`)\n')
    rows, summary, _ = ca.check(answer)
    out = "\n".join(rows) + summary
    assert ALPHA not in out and BETA not in out and GAMMA not in out
    assert all(len(r.split(" | ")[1]) <= 60 for r in rows)


def test_cli_exit_codes(ca, tmp_path):
    env = dict(os.environ)
    run = lambda text: subprocess.run([sys.executable, os.path.join(SCRIPTS, "check_answer.py")], input=text,
                                      capture_output=True, text=True, env=env)
    assert run('- "every box answers within five seconds" (`docs/one.md#Alpha`)\n').returncode == 0
    r = run('- "every box answers within five hours" (`docs/one.md#Alpha`)\n')
    assert r.returncode == 1 and r.stdout.splitlines()[-1].startswith("answer check:")
    assert run("no citations here\n").returncode == 0


def test_a_short_uncited_phrase_is_a_term_and_a_long_one_is_uncited(ca):
    rows, _, ok = ca.check('- (`docs/one.md#Alpha`)\n\n## Next\n\nThe docs say to "test with your own data".\n')
    assert rows == [] and ok, rows


def test_a_quote_that_borrows_an_earlier_citation_which_lacks_it_is_uncited_and_names_its_section(ca):
    answer = '- "every box answers within five seconds" (`docs/one.md#Alpha`)\n- As another page says, "the other rule: a state carries at most nine fields" too.\n'
    rows, _, ok = ca.check(answer)
    assert verdicts(rows) == ["FOUND", "UNCITED"] and "found under docs/one.md#Beta" in rows[1] and not ok, rows


def test_a_heading_shortened_with_an_ellipsis_resolves_when_one_heading_starts_that_way(ca):
    rows, _, ok = ca.check('- "a state carries at most nine fields" (`docs/one.md#Be…`)\n')
    assert verdicts(rows) == ["FOUND"] and ok, rows


def test_a_code_span_inside_a_quote_and_a_markdown_link_on_the_page_still_match(ca, tmp_path):
    import build_index
    data = os.environ["JEV_SOURCES_DATA"]
    with open(os.path.join(data, "docs", "three.md"), "w") as f:
        f.write("# Three\n\n## Delta\n\nSet `model` and pay close attention to [Confidence](/confidence) when routing.\n")
    build_index.main()
    rows, _, ok = ca.check('- "Set `model` and pay close attention to Confidence when routing" (`docs/three.md#Delta`)\n')
    assert verdicts(rows) == ["FOUND"] and ok, rows


def test_a_nested_bullet_uses_its_parent_citation_and_italic_cites_with_commas_resolve(ca, tmp_path):
    import build_index
    data = os.environ["JEV_SOURCES_DATA"]
    with open(os.path.join(data, "docs", "four.md"), "w") as f:
        f.write("# Four\n\n## Frontiers, Old and New\n\nWe can’t prove it isn’t cheap – not yet, they said.\n")
    build_index.main()
    answer = ('- **Pricing** (`docs/one.md#Alpha`):\n  - "every box answers within five seconds"\n'
              '- "We can\'t prove it isn\'t cheap - not yet" *docs/four.md#Frontiers, Old and New*\n')
    rows, _, ok = ca.check(answer)
    assert verdicts(rows) == ["FOUND", "FOUND"] and ok, rows


def test_a_citation_after_the_quotes_and_one_without_its_folder_both_count(ca):
    answer = ('## Errors\n\n- **413:** "Gamma says the body is over 32 MiB"\n- **Alpha:** "every box answers within five seconds"\n\n'
              'All three: *docs/two.md#Gamma (reference rule)* and (one.md#Alpha)\n')
    rows, _, ok = ca.check(answer)
    assert verdicts(rows) == ["FOUND", "FOUND"] and ok, rows


def _lib_page(name, text):
    import build_index
    with open(os.path.join(os.environ["JEV_SOURCES_DATA"], "docs", name), "w") as f:
        f.write(text)
    build_index.main()


def test_a_citation_to_a_section_covers_its_subsections(ca):
    _lib_page("six.md", "# Six\n\n## Context length\n\nThe default rule.\n\n### Long context\n\nLong context is off by default here.\n\n## Other\n\nElse.\n")
    rows, _, ok = ca.check('- "Long context is off by default here." (`docs/six.md#Context length`)\n')
    assert verdicts(rows) == ["FOUND"] and ok, rows
    rows, _, ok = ca.check('- "Long context is off by default here." (`docs/six.md#Other`)\n')
    assert verdicts(rows) == ["NOT FOUND"] and not ok, rows


def test_the_users_own_words_in_quotes_are_not_checked(ca):
    rows, _, ok = ca.check('You asked "should I fan out or send one question at a time here?" and the docs answer.\n\n'
                           '- "every box answers within five seconds" (`docs/one.md#Alpha`)\n')
    assert verdicts(rows) == ["FOUND"] and ok, rows


def test_a_short_full_sentence_quote_under_a_source_line_that_lacks_it_fails(ca):
    rows, _, ok = ca.check("Source: `docs/one.md#Alpha`\n\n\"A state carries at most nine fields.\"\n")
    assert verdicts(rows) == ["UNCITED"] and "found under docs/one.md#Beta" in rows[0] and not ok, rows


def test_a_jev_answer_quoting_the_docs_with_no_citation_at_all_fails(ca):
    rows, summary, ok = ca.check('The docs say "Jev answers every box question within five seconds flat."\n')
    assert verdicts(rows) == ["UNCITED"] and not ok and summary
    rows, summary, ok = ca.check('The React docs say "effects run after every completed render by default here."\n')
    assert rows == [] and ok and summary is None


def test_a_jev_reply_with_no_citation_checks_only_quotes_given_as_the_docs_words(ca):
    rows, summary, ok = ca.check('I set the Jev client error to "Jev request failed after three retries, giving up now".\n')
    assert rows == [] and ok
