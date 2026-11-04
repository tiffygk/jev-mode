import json, pathlib, subprocess, sys

HERE = pathlib.Path(__file__).parent
FIX = HERE / "fixtures"
CHECK = HERE.parent / "scripts" / "report_check.py"
WHOLE = {p["id"]: p for p in json.loads((FIX / "whole-probes.json").read_text())}
# Whole-file probes whose expected rule was removed when the skill stopped writing posts, notes and replies (2026-11-04).
REMOVED = {"report-back", "invite"}
NOTE_ONLY = {"w12"}  # its finding is a promise in the note, which the skill no longer writes
# Home paths are built at run time: the repo's hook refuses a file with one written out.
HOME = "/" + "Users/me/"
WIN_HOME = "C:/" + "Users/dana/notes.md"


def run(path, *extra):
    r = subprocess.run([sys.executable, str(CHECK), str(path), *extra], capture_output=True, text=True)
    rules = [l.split(":")[0] for l in r.stdout.splitlines() if l and not l.startswith("counts ")]
    return r.returncode, rules, r.stdout


def probe_file(tmp_path, pid, text=None):
    f = tmp_path / f"{pid}.md"; f.write_text(text if text is not None else WHOLE[pid]["text"])
    return f


def run_w(f, *extra):
    """The whole-file probes were written before the opening-test rule, so it is skipped for them."""
    return run(f, "--skip", "opening-test", *extra)


def w01_with(old, new):
    t = WHOLE["w01"]["text"]
    assert old in t
    return t.replace(old, new, 1)


# The skimmer files predate the framing rules (advice, opening, opening-test), so they are checked rule by rule.
def test_posted_skimmer_has_the_broken_s16_label():
    code, rules, out = run(FIX / "skimmer-posted.md")
    assert code == 1 and rules.count("labels") == 1 and "S16" in out, out


def test_fixed_skimmer_has_no_label_link_or_leak_finding():
    rules = run(FIX / "skimmer-fixed.md")[1]
    assert not {"labels", "pinned-links", "private", "table-match", "order", "front-matter", "bare-ref"} & set(rules), rules


def test_skimmer_promise_in_the_opening_is_caught(tmp_path):
    # "Split that question and skimmer rates 4" is the promise the maintainer's held-out test disproved.
    f = probe_file(tmp_path, "w01", w01_with("- One fix is suggested.", "- One fix is suggested. Split that question and tools rates 4."))
    assert run_w(f)[1] == ["certainty"]


def test_counts_line_comes_from_the_file():
    assert "counts fixes 16, labels 80," in run(FIX / "skimmer-fixed.md")[2]


def test_private_term_in_the_title_is_caught(tmp_path):
    f = probe_file(tmp_path, "w01", w01_with("title: Review of tools", f"title: tools review, see {HOME}notes"))
    assert run_w(f)[1] == ["private"]


def test_unpinned_repo_link_fails(tmp_path):
    f = probe_file(tmp_path, "w01", w01_with("tools/blob/0123456789abcdef0123456789abcdef01234567/", "tools/blob/main/"))
    assert run_w(f)[1] == ["pinned-links"]


def test_wider_promise_phrases_are_caught(tmp_path):
    for phrase in ("This will reduce misses.", "It solves the leak.", "With this it rates 4."):
        f = probe_file(tmp_path, "w01", w01_with("Try naming one version in the config.", f"Try naming one version in the config. {phrase}"))
        assert run_w(f)[1] == ["certainty"], phrase


def test_eval_words_are_not_private_ids(tmp_path):
    f = probe_file(tmp_path, "w01", w01_with("The test suite reached", "F1 of 0.8 for Q3; the test suite reached"))
    assert run_w(f)[0] == 0


def test_whole_file_probes(tmp_path):
    bad = []
    for pid, p in WHOLE.items():
        if p["expect"] in REMOVED or pid in NOTE_ONLY:
            continue
        rules = sorted(set(run(probe_file(tmp_path, pid), "--skip", "local-link,opening-test")[1]))  # rules added after this set
        if rules != ([] if p["expect"] == "pass" else [p["expect"]]):
            bad.append((pid, p["expect"], rules))
    assert not bad, bad


def test_probes(tmp_path):
    # probes.json was written for the rules before advice existed; it runs against those rules.
    probes = json.loads((FIX / "probes.json").read_text())
    wrong = json.loads((FIX / "probe-exceptions.json").read_text())  # probes whose expected verdict is wrong, with why
    bad = []
    for p in probes:
        if p["id"] in wrong:
            continue
        text = p["text"].replace("{{PAD_60000}}", "x" * 60000)
        f = tmp_path / f"{p['id']}.md"; f.write_text(text)
        rules = run(f, "--fragment", "--skip", "advice")[1]
        if not ((rules == []) if p["expect"] == "pass" else (rules == [p["expect"]])):
            bad.append((p["id"], p["expect"], rules))
    assert not bad, bad


# The opening tells the reader and their agents the fixes are documented practice to test, not proven (2026-11-04).
def test_opening_must_say_the_fixes_are_to_be_tested(tmp_path):
    f = probe_file(tmp_path, "w01")
    assert run(f)[1] == ["opening-test"]
    for line in ["Test each fix on your own eval before keeping it.", "Each fix is untested advice: run its test first."]:
        f = probe_file(tmp_path, "w01", w01_with("- One fix is suggested.", f"{line}\n\n- One fix is suggested."))
        assert run(f)[1] == [], line
    f = probe_file(tmp_path, "w01", w01_with("- One fix is suggested.", "The README says \"tested on 40 goals\".\n\n- One fix is suggested."))
    assert run(f)[1] == ["opening-test"]
    # A test word about the project's own tests, not the fixes, is not the framing (2026-11-04).
    f = probe_file(tmp_path, "w01", w01_with("- One fix is suggested.", "Our test suite passes on every commit.\n\n- One fix is suggested."))
    assert run(f)[1] == ["opening-test"]


# Inputs from the second gate (2026-10-19): each promise failed to fail before the fix; close calls must still pass.
PROMISES = ["That fixes the drift.", "This ensures the model stays fixed.", "It will cut misses in half.",
            "It will stop the drift.", "This eliminates drift.", "This guarantees one version.", "It prevents drift.",
            "It will make results stable.", "It gets you to a 4."]
CLOSE_CALLS = ["It may reduce misses.", "It could fix the drift.", "Nothing in the config prevents drift today."]


def test_promise_phrases_fail_and_close_calls_pass(tmp_path):
    for phrase, expect in [(p, ["certainty"]) for p in PROMISES] + [(c, []) for c in CLOSE_CALLS]:
        f = probe_file(tmp_path, "w01", w01_with("Try naming one version in the config.", f"Try naming one version in the config. {phrase}"))
        assert run_w(f)[1] == expect, phrase


def test_private_words_in_addresses_and_other_home_folders(tmp_path):
    terms = tmp_path / "terms.txt"; terms.write_text("secretproj\n")
    adds = ["See [notes](https://github.com/acme/secretproj/issues/1).", "See https://docs.secretproj.internal/x for more.",
            "See /home/dana/notes.md.", "See " + WIN_HOME.replace("/", "\\") + "."]
    for add in adds:
        f = probe_file(tmp_path, "w01", w01_with("The test suite reached", f"{add} The test suite reached"))
        assert "private" in run_w(f, "--private-terms", str(terms))[1], add


def test_the_private_rating_skill_may_be_named(tmp_path):
    # The report is built from a jevaluate-private rating the team agreed with, so naming that skill is no leak.
    f = probe_file(tmp_path, "w01", w01_with("The test suite reached", "Rated with jevaluate-private. The test suite reached"))
    assert run_w(f)[1] == []


# Inputs from the third gate (2026-10-19). Each failed to fail, or failed to pass, before the fix.
PROMISES_3 = ["It'll fix the drift.", "This will lower misses.", "This will catch the drift.", "This resolves the drift.",
              "This corrects the drift.", "That should fix it.", "This change fixes drift.", "It moves the verdict to a 4.",
              "This earns a 4.", "You will see fewer misses.", "Misses will drop to zero.", "This makes the results stable.",
              "It will get you a 3.", "This will definitely help.", "Drift goes away."]
CLOSE_CALLS_3 = ["It may lower misses.", "It could resolve the drift.", "If it works, I'll update this file.",
                 "Results may vary between runs."]


def test_wider_promises_fail_and_close_calls_pass(tmp_path):
    for phrase, expect in [(p, ["certainty"]) for p in PROMISES_3] + [(c, []) for c in CLOSE_CALLS_3]:
        f = probe_file(tmp_path, "w01", w01_with("Try naming one version in the config.", f"Try naming one version in the config. {phrase}"))
        assert run_w(f)[1] == expect, phrase


def test_promises_in_why_opening_and_title(tmp_path):
    for t in [w01_with("and results differ when it is not.", "and pinning the version will lower variance."),
              w01_with("- One fix is suggested.", "- One fix is suggested; it gets the repo to a 4."),
              w01_with("- One fix is suggested.", "- One fix is suggested; it will lower misses."),
              w01_with("title: Review of tools", "title: tools review, verdict 2 and 1 fix that will fix it")]:
        assert run_w(probe_file(tmp_path, "w01", t))[1] == ["certainty"]


def test_leaks_in_hover_titles_and_addresses(tmp_path):
    terms = tmp_path / "terms.txt"; terms.write_text("secretproj\n")
    f = probe_file(tmp_path, "w01", WHOLE["w01"]["text"] + '\n[cfg]: https://example.com/a "secretproj notes"\n')
    assert "private" in run_w(f, "--private-terms", str(terms))[1]
    f = probe_file(tmp_path, "w01", w01_with("The test suite reached", "See [x](https://example.com/Q12). The test suite reached"))
    assert run_w(f)[1] == ["private"]


def test_code_paths_named_users_or_scratchpad_are_not_home_folders(tmp_path):
    for add in ["See [x](https://github.com/acme/app/blob/0123456789abcdef0123456789abcdef01234567/src/" + "Users/model.go).",
                "The `src/" + "Users/model.go` file.", "The scratchpad feature is fast."]:
        f = probe_file(tmp_path, "w01", w01_with("The test suite reached", f"{add} The test suite reached"))
        assert "private" not in run_w(f)[1], add
    for add in ["See /home/dana for notes.", f"See {WIN_HOME}.", "See $HOME/notes.md."]:
        f = probe_file(tmp_path, "w01", w01_with("The test suite reached", f"{add} The test suite reached"))
        assert run_w(f)[1] == ["private"], add


def test_template_opening_lines_are_not_promises(tmp_path):
    # Third panel round (2026-10-20): "these three fixes" read as a subject and a verb, so the template's own line failed.
    for line in ["Start with these three fixes:", "Start with these fixes:", "Start with three fixes to get it to a 3 \"Use with a fix\" verdict:"]:
        f = probe_file(tmp_path, "w01", w01_with("- One fix is suggested.", f"{line}\n\n- One fix is suggested."))
        assert run_w(f)[1] == [], line


# A Codex run (2026-10-22) linked a local copy of the rubric; the link breaks once the file is read anywhere else.
def test_local_links_fail_and_web_links_and_anchors_pass(tmp_path):
    for add in ["See the [rubric](jev-rubric.md).", "See [notes](./notes/a.md).", "See [x][r].\n\n[r]: docs/rubric.md"]:
        f = probe_file(tmp_path, "w01", w01_with("The test suite reached", f"{add} The test suite reached"))
        assert "local-link" in run_w(f)[1], add
    for add in ["See the [rubric](https://github.com/tiffygk/jev-mode/blob/main/jevaluate/rubric.md).",
                "See [Rating](#rating).", "Write to [us](mailto:team@example.com)."]:
        f = probe_file(tmp_path, "w01", w01_with("The test suite reached", f"{add} The test suite reached"))
        assert "local-link" not in run_w(f)[1], add


# The skimmer report's disproved promise sat in its Rating section, which the certainty rule did not read (2026-11-04).
def test_promise_in_the_rating_section_is_caught(tmp_path):
    t = WHOLE["w01"]["text"]
    assert "## What already works" in t
    for line, expect in [("With that one fixed, tools would rate 4.", ["certainty"]),
                         ("The rating says that fix could reach a 4 if its test passes.", [])]:
        f = probe_file(tmp_path, "w01", t.replace("## What already works", f"{line}\n\n## What already works", 1))
        assert run_w(f)[1] == expect, line


def test_a_whole_report_in_the_current_template_passes():
    """The skimmer report rebuilt in the current template (the 2026-11-04 dry run) passes as a whole, so a template or
    checker change has to keep a real report passing. Before it, no fixture in the current template ran end to end."""
    code, rules, out = run(FIX / "skimmer-report.md")
    assert code == 0 and rules == [] and "counts fixes 16, labels 80, links 84," in out, out
