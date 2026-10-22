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
    "docs/three.md": "# Three\n\n## How to build with the box\n\nBuild steps go here in order.\n\n## Price\n\n| Price | \\$42 / \\$0.042 |\n",
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


def test_a_quoted_question_not_on_the_page_is_the_answers_own_example(ca):
    rows, _, ok = ca.check('- Ask one Noul per line ("Is this line a billed line item for the order?") (`docs/one.md#Alpha`)\n')
    assert rows == [] and ok, rows


def test_a_docs_url_cites_its_page_and_a_heading_cut_at_a_word_boundary_resolves(ca):
    _lib_page("primitives__seven.md", "# Seven\n\n## Step 3: check whether an answer exists\n\nA Seven answer is the selected option here.\n")
    rows, _, ok = ca.check('- "A Seven answer is the selected option here." ([Seven](https://docs.typesafe.ai/primitives/seven))\n'
                           '- "A Seven answer is the selected option here." (`docs/primitives__seven.md#Step 3`)\n')
    assert verdicts(rows) == ["FOUND", "FOUND"] and ok, rows
    rows, _, ok = ca.check('- "A Seven answer is the selected option here." (`docs/primitives__seven.md#Step`)\n')
    assert verdicts(rows) == ["FOUND"], rows  # one heading starts with "Step"


# --- unquoted facts: a specific Jev fact stated with no quote ---------------------------------------------------

CITED = 'Speed: "every box answers within five seconds" (`docs/one.md#Alpha`, reference rule)\n\n'


def test_a_price_or_status_code_about_jev_with_no_quote_is_listed(ca):
    facts = ca.unquoted_facts(CITED + "Jev bills $42 per billion input tokens.\n\nWhen a body is wrong, the API returns a `422`.\n")
    assert [f.split(" | ")[0] for f in facts] == ["UNQUOTED", "UNQUOTED"]
    assert facts[0].startswith("UNQUOTED | Jev bills $42 per billion")


def test_a_fact_with_its_quote_on_the_line_or_under_my_read_or_marked_unconfirmed_is_not_listed(ca):
    text = (CITED + 'Price: "You pay per input token." (`docs/one.md#Alpha`)\n\n'
            "Jev allows 255 options per Choice (unconfirmed: the pages I read don't show it).\n\n"
            "**My read:** at 10 million questions a month, Jev would cost about $4.\n")
    assert ca.unquoted_facts(text) == []


def test_the_persons_own_numbers_code_blocks_and_answers_with_no_jev_are_not_listed(ca):
    text = CITED + "You send 2 million texts a month, 5 questions each.\n\n```\nclient.system_one(model=\"jev-1.13.0\")  # 255 options\n```\n"
    assert ca.unquoted_facts(text) == []
    assert ca.unquoted_facts("The 3 queues cost $5 a day to run.\n") == []


def test_unquoted_facts_never_change_the_quote_verdict(ca):
    rows, summary, ok = ca.check(CITED + "Jev bills $42 per billion input tokens.\n")
    assert ok and verdicts(rows) == ["FOUND"]


def test_cli_prints_unquoted_rows_and_keeps_its_exit_code(ca, tmp_path):
    env = {**os.environ, "JEV_SOURCES_DATA": os.environ["JEV_SOURCES_DATA"], "JEV_LOG": "off", "JEV_SEMANTIC": "off"}
    r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "check_answer.py")], input=CITED + "Jev bills $42 per billion input tokens.\n",
                       capture_output=True, text=True, env=env)
    assert r.returncode == 0 and "UNQUOTED | Jev bills $42 per billion" in r.stdout


def test_a_gap_statement_is_not_an_unquoted_fact_but_a_flat_denial_is(ca):
    assert ca.unquoted_facts(CITED + "The pages I read don't give a limit on 255 options.\n\nI didn't read the SDK errors page for `422`.\n") == []
    assert len(ca.unquoted_facts(CITED + "The API doesn't stream partial answers over 3 requests.\n")) == 1


# --- gate round 1 must-fixes ------------------------------------------------------------------------------------

def test_a_quoted_heading_title_is_not_a_quote(ca):
    rows, _, ok = ca.check('Retry (`docs/one.md#Alpha`). The guide "How to build with the box" explains composing.\n')
    assert ok and "NOT FOUND" not in " ".join(rows)


@pytest.mark.parametrize("lead", ["The error says", "The output is", "The response reads"])
def test_a_misquote_of_the_docs_is_not_excused_by_an_error_or_output_lead_in(ca, lead):
    rows, _, ok = ca.check(f'{lead} "every box answers within five minutes" (`docs/one.md#Alpha`).\n')
    assert not ok and verdicts(rows) == ["NOT FOUND"]


def test_a_short_quote_holding_a_specific_fact_is_checked_not_skipped(ca):
    text = '## Price\n\n- Speed: "every box answers within five seconds" (`docs/one.md#Alpha`)\n\nJev bills "$42 per billion input tokens" at list price.\n'
    rows, _, ok = ca.check(text)
    assert not ok and any(r.startswith(("UNCITED", "NOT FOUND")) and "$42" in r for r in rows)


def test_a_backticked_file_name_next_to_lowercase_score_is_not_a_jev_fact(ca):
    assert ca.unquoted_facts(CITED + "My code writes three spreadsheets: `flags.csv` with each score.\n") == []
    assert len(ca.unquoted_facts(CITED + "A Score question returns 3 levels.\n")) == 1


def test_long_comma_runs_and_long_digit_runs_stay_fast(ca):
    import time
    t = time.perf_counter()
    ca.check('Jev: "every box answers within five seconds" docs/one.md#' + "a," * 3000 + "x\n")
    ca.unquoted_facts("Jev costs " + "1," * 20000 + "x\n")
    assert time.perf_counter() - t < 2


@pytest.mark.parametrize("fake", ['"bodies over 64 MiB"', '"2M tokens of context"', '"0.042 dollars per Mtok"',
                                  '"`max_retries` to five"', '"returns status 503 here"'])
def test_a_short_made_up_quote_with_a_specific_never_passes_both_checks(ca, fake):
    for text in (f'## Price\n\n- Speed: "every box answers within five seconds" (`docs/one.md#Alpha`)\n\nJev sets {fake} for each call.\n',
                 f'Jev sets {fake} for each call.\n'):
        rows, _, ok = ca.check(text)
        assert not ok or ca.unquoted_facts(text), (fake, text, rows)


def test_many_citations_on_one_line_stay_fast(ca):
    import time
    t = time.perf_counter()
    ca.check("Jev " + "a.md#b; " * 2500 + "\n")
    ca.check('Jev "every box answers within five seconds" ' + "`docs/one.md#Alpha`; " * 2000 + "\n")
    assert time.perf_counter() - t < 3


@pytest.mark.parametrize("lead", ["The docs tell you", "You'd see", "If you go over, the docs say", "As you'd expect,",
                                  "Your limit works like this:", "You should know that"])
def test_a_bare_you_before_a_misquote_does_not_excuse_it(ca, lead):
    rows, _, ok = ca.check(f'{lead} "every box answers within five minutes" (`docs/one.md#Alpha`).\n')
    assert not ok and verdicts(rows) == ["NOT FOUND"]


def test_an_error_shaped_misquote_attributed_to_a_docs_page_is_checked(ca):
    rows, _, ok = ca.check('The page says "AlphaError is raised only for five second waits" (`docs/one.md#Alpha`).\n')
    assert not ok


@pytest.mark.parametrize("fake", ['"$0.40 per Mtok"', '"16 MiB"', '"2M tokens"', '"returns 503"', '"`max_batch`"'])
def test_a_quote_under_four_words_holding_a_specific_is_checked(ca, fake):
    for text in (f"Jev's body limit is {fake} (`docs/one.md#Alpha`).\n", f"For your requests, Jev's body limit is {fake} (`docs/one.md#Alpha`).\n"):
        rows, _, ok = ca.check(text)
        assert not ok or ca.unquoted_facts(text), (text, rows)


def test_a_price_quoted_with_the_pages_own_escapes_is_found(ca):
    rows, _, ok = ca.check('Price: "\\$42 / \\$0.042" (`docs/three.md#Price`)\n')
    assert ok and verdicts(rows) == ["FOUND"], rows


def test_a_line_labeled_unverified_is_not_an_unquoted_fact_even_with_a_specific_quote(ca):
    assert ca.unquoted_facts(CITED + 'Unverified: "Jev answers in under 50 ms" (a blog figure I did not find in the docs).\n') == []


# --- re-gate 3 must-fixes ---------------------------------------------------------------------------------------

MIS = "every box answers within six seconds"


@pytest.mark.parametrize("lead", ["When you get a 429, the page says", "If you hit the limit, the docs say",
                                  "As you saw, the docs say", "your output should match", "You get",
                                  "The docs say your output will hit", "you copied the example, but the docs say",
                                  "In your run, the docs say", "You asked about speed; the docs say"])
def test_a_user_phrase_earlier_in_the_sentence_does_not_excuse_a_misquote(ca, lead):
    rows, _, ok = ca.check(f'- {lead} "{MIS}" (`docs/one.md#Alpha`)\n')
    assert not ok and verdicts(rows) == ["NOT FOUND"], rows


def test_an_error_line_in_a_paragraph_that_names_a_docs_page_is_checked(ca):
    pad = "The rate limit error reference page describes what the SDK raises when the server answers with a 429. "
    rows, _, ok = ca.check(f'{pad}It prints "RateLimitError: too many calls, retry in 60 seconds" (`docs/one.md#Alpha`).\n')
    assert not ok, rows


@pytest.mark.parametrize("text", ['Jev.\n\nThe body limit is "64 MiB".\n', 'Jev.\n\nYour body limit is "$40".\n',
                                  'Jev.\n\nI\'d note the Jev body limit is "2M".\n',
                                  'Jev.\n\nMy read is the Jev body limit is "`max_batch`".\n'])
def test_a_made_up_quote_holding_a_specific_fails_with_no_citation_in_the_answer(ca, text):
    rows, _, ok = ca.check(text)
    assert not ok and verdicts(rows) == ["UNCITED"], rows


def test_an_unverified_label_covers_only_its_own_quote(ca):
    assert not ca.check(f'- The speed is "{MIS}" (`docs/one.md#Alpha`); the retry header name is unverified.\n')[2]
    assert not ca.check(f'- "{MIS}" (`docs/one.md#Alpha`). Other details here are unverified.\n')[2]
    for ok_text in (f'- "{MIS}" (`docs/one.md#Alpha`, unverified)\n', f'- Unconfirmed: "{MIS}" (`docs/one.md#Alpha`)\n',
                    f'- "{MIS}" (`docs/one.md#Alpha`). This quote is unverified.\n'):
        rows, _, ok = ca.check(ok_text)
        assert ok and verdicts(rows) == ["LABELED"], (ok_text, rows)


def test_a_price_written_as_the_page_shows_it_matches_the_escaped_page_text(ca):
    rows, _, ok = ca.check('- The price is "$42 / $0.042" (`docs/three.md#Price`)\n')
    assert ok and verdicts(rows) == ["FOUND"], rows


def test_a_quoted_question_the_docs_are_said_to_ask_is_checked(ca):
    assert not ca.check('Jev.\n\nThe docs say "Is the body limit 64 MiB?"\n')[2]
    assert ca.check('Jev.\n\nAsk a Choice question such as "Which of these 3 tickets is urgent?"\n')[2]


def test_the_users_error_line_beside_a_citation_is_not_an_unquoted_fact(ca):
    assert ca.unquoted_facts('- You got "RateLimitError: 429 after 60 requests per second" (`docs/one.md#Alpha`).\n') == []


def test_many_quotes_stay_fast_and_past_the_cap_fail_once(ca):
    import time
    t = time.perf_counter()
    rows, _, ok = ca.check("Jev " + ('"2 MiB" ' * 25000)[:200000])
    rows2, _, _ = ca.check("Jev.\n\n" + '- "every box answers within five seconds" (`docs/one.md#Alpha`)\n' * 2000)
    ca.unquoted_facts("Jev.\n\n" + 'When you send, the body limit is "64 MiB" and "$40" per `x_y`. ' * 3000)
    assert time.perf_counter() - t < 3
    assert not ok and rows == [r for r in rows if r.startswith("UNCITED")] and len(rows) == 1  # one block: checked once
    assert rows2[-1].startswith("TOO MANY") and len(rows2) == ca.MAX_QUOTES + 1


# --- re-gate 4 must-fixes and Ruling 14: quotation marks are for the docs' words only ---------------------------------------------------------------------------------------

def test_an_error_line_given_a_page_is_checked(ca):
    err = "RateLimitError: too many calls, retry in 60 seconds"
    assert not ca.check(f'- The SDK error text: "{err}" (`docs/one.md#Alpha`)\n')[2]
    assert not ca.check(f'# Errors\n\n- The SDK error text: "{err}"\n\nSource: the docs page `docs/one.md#Alpha`.\n')[2]


def test_a_label_counts_only_beside_its_quote_and_not_when_negated(ca):
    assert not ca.check(f'- The speed is "{MIS}" (`docs/one.md#Alpha`) and the retry header name is unverified.\n')[2]
    assert not ca.check(f'- Nothing here is unverified: the speed is "{MIS}" (`docs/one.md#Alpha`).\n')[2]
    assert ca.check(f'- The speed is "{MIS}" (unverified, `docs/one.md#Alpha`).\n')[2]


def test_unquoted_facts_reuses_the_checks_seen_quotes(ca, monkeypatch):
    t = f'- The limit is "{MIS}" (`docs/one.md#Alpha`)\n'
    seen = set()
    ca.check(t, seen)
    monkeypatch.setattr(ca, "check", lambda *a, **k: (_ for _ in ()).throw(AssertionError("checked twice")))
    ca.unquoted_facts(t, seen)


ERR = "RateLimitError: too many calls, retry in 60 seconds"


@pytest.mark.parametrize("lead", ["You got", "You pasted", "The error", "Your output shows", "When you see",
                                  "The line in your log,", "The traceback ends with", "You asked", ""])
def test_the_users_line_in_quotation_marks_is_checked(ca, lead):
    for q in (ERR, MIS):
        rows, _, ok = ca.check(f'- {lead} "{q}" (`docs/one.md#Alpha`)\n')
        assert not ok and verdicts(rows) == ["NOT FOUND"], (lead, rows)
    rows, _, ok = ca.check(CITED + f'{lead} "request failed after three retries with status four twenty nine".\n')
    assert not ok and "UNCITED" in verdicts(rows), rows


@pytest.mark.parametrize("lead", ["Under Alpha you see", "Per one.md you see", "In the limits table, you see",
                                  "That section is clear; you see", "As you see,", "Here is what you see:",
                                  "Look at Alpha and you see", "From the Jev limits you got",
                                  "When you get a 429, the page says", "The SDK error text:"])
def test_a_misquote_under_any_former_lead_in_fails(ca, lead):
    for q in (MIS, ERR):
        rows, _, ok = ca.check(f'- {lead} "{q}" (`docs/one.md#Alpha`)\n')
        assert not ok and verdicts(rows) == ["NOT FOUND"], (lead, rows)
    assert not ca.check(f'# Errors\n\n- {lead} "{ERR}"\n\nSource: the docs page `docs/one.md#Alpha`.\n')[2]


def test_the_users_text_in_backticks_or_a_fence_is_not_checked(ca):
    good = '"every box answers within five seconds" (`docs/one.md#Alpha`)'
    for t in (f"- You got `{ERR}` (`docs/one.md#Alpha`)\n",
              f"- You got `{ERR}`; the page says {good}\n",
              f"Your run printed:\n\n```\nTraceback (most recent call last):\n  {ERR}\n```\n\nThe page says {good}\n",
              f'- The run printed `print("hello world from the run")` and the page says {good}\n'):
        rows, _, ok = ca.check(t)
        assert ok and verdicts(rows) in ([], ["FOUND"]), (t, rows)


def test_curly_and_single_quotes(ca):
    rows, _, ok = ca.check(f"- You got \u201c{ERR}\u201d (`docs/one.md#Alpha`)\n")
    assert not ok and verdicts(rows) == ["NOT FOUND"], rows
    assert ca.check(f"- You got '{ERR}' (`docs/one.md#Alpha`)\n")[2]  # only double quotes mark a docs quote


def test_quoted_questions_terms_and_headings_stay_unchecked(ca):
    for t in ('- You asked "How do I batch these questions together?" (`docs/one.md#Alpha`)\n',
              '- Use a "danger zone" header (`docs/one.md#Alpha`)\n',
              '- See "How to build with the box" (`docs/three.md#Price`)\n'):
        rows, _, ok = ca.check(t)
        assert ok and rows == [], (t, rows)
    assert not ca.check('Jev.\n\nThe docs say "Is the body limit 64 MiB?"\n')[2]


def test_the_cli_takes_no_arguments(ca):
    r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "check_answer.py"), "--transcript", "x.jsonl"],
                       input="", capture_output=True, text=True)
    assert r.returncode == 2 and "usage" in r.stderr
    assert not hasattr(ca, "transcript_context")

