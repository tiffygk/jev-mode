"""The update check: does the saved index still describe the saved pages? It only reports, and a real update with
nothing wrong stays quiet. Each test seeds one fault, or one thing that must not read as a fault, in a temporary library."""
import datetime, json, os, stat, subprocess, sys
import pytest

CODE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(CODE, "scripts"))
from test_check_new import site  # the fake TypeSafe site
from test_refresh import fake_python, run_refresh
import landing_check

UTC = datetime.timezone.utc
T13 = datetime.datetime(2026, 10, 13, 12, tzinfo=UTC)
T14 = datetime.datetime(2026, 10, 14, 23, tzinfo=UTC)
MODULES = ("paths", "pages", "blog", "check_new", "fetch", "build_index", "semantic", "route", "route_check", "citations",
           "applicability", "jev", "read", "sources", "usage_log")
REAL = os.path.expanduser(os.environ.get("JEV_SOURCES_DATA") or "~/.claude/jev-sources-data")
needs_lib = pytest.mark.skipif(not os.path.exists(os.path.join(REAL, "sections.jsonl")),
                               reason="no fetched library (sections.jsonl) in JEV_SOURCES_DATA")


def fresh_modules():
    """Modules that read the library path at import see this test's folder."""
    for name in MODULES:
        sys.modules.pop(name, None)


class Lib:
    """A temporary library holding docs/a.md, docs/b.md and docs/c.md, two headings each: 6 sections from 3 pages."""
    def __init__(self, root, monkeypatch):
        self.root, self.monkeypatch = str(root), monkeypatch
        import pages, check_new
        self.pg, self.cn = pages, check_new
        monkeypatch.setattr(pages, "extras", lambda: [])  # urls.txt lists real pages; the fake site has none
        for slug in ("a", "b", "c"):
            self.page(slug, 2)

    def page(self, slug, headings):
        self.pg.write_page(slug, "".join(f"# {slug} heading {n}\n\nSome words about {slug}.\n\n" for n in range(headings)), T13)

    def path(self, rel):
        return os.path.join(self.root, rel)

    def build(self):
        import build_index
        self.monkeypatch.setattr(build_index, "embed", lambda rows: None)  # no model in a temporary library
        build_index.main(prepare=False)

    def rows(self):
        return [json.loads(l) for l in open(self.path("sections.jsonl"))]

    def keep_rows(self, keep):
        rows = self.rows()
        with open(self.path("sections.jsonl"), "w") as f:
            f.writelines(json.dumps(r) + "\n" for r in rows if keep(r))

    def quiet_site(self):
        """TypeSafe's site as it stands: every page listed with an old date, so nothing changes."""
        slugs = list(self.pg.library())
        return site(self.pg, {}, {s: "2026-10-12T00:00:00Z" for s in slugs}, slugs, [])


@pytest.fixture
def empty(tmp_path, monkeypatch):
    monkeypatch.setenv("JEV_SOURCES_DATA", str(tmp_path))
    monkeypatch.setenv("JEV_SEMANTIC", "off")
    monkeypatch.setenv("JEV_PRIVATE_CONFIG", str(tmp_path / "absent.json"))
    fresh_modules()
    return tmp_path


@pytest.fixture
def lib(empty, monkeypatch):
    built = Lib(empty, monkeypatch)
    built.build()
    return built


def failed_result(*problems):
    return {"state": "failed", "problems": list(problems), "notes": [], "sections": 6, "pages": 3}


# --- index against pages -------------------------------------------------------------------------------------

def test_a_matching_library_passes_and_names_its_counts(lib):
    r = landing_check.run()
    assert (r["state"], r["sections"], r["pages"], r["problems"]) == ("passed", 6, 3, [])


def test_a_page_missing_from_the_index_fails(lib):
    lib.keep_rows(lambda row: row["path"] != "docs/b.md")
    r = landing_check.run()
    assert r["state"] == "failed" and "docs/b.md" in r["problems"][0]


def test_a_cut_short_index_fails(lib):
    rows = lib.rows()
    kept = {row["id"] for row in rows[:len(rows) // 2]}
    lib.keep_rows(lambda row: row["id"] in kept)
    assert landing_check.run()["state"] == "failed"


def test_a_page_edited_after_the_build_fails(lib):
    with open(lib.path("docs/c.md"), "a") as f:
        f.write("\n# A new heading\n\nNew words.\n")
    r = landing_check.run()
    assert r["state"] == "failed" and "docs/c.md" in r["problems"][0]


def test_a_section_with_the_same_heading_but_a_new_size_fails(lib):
    rows = lib.rows()
    rows[0]["tokens"] += 1
    with open(lib.path("sections.jsonl"), "w") as f:
        f.writelines(json.dumps(row) + "\n" for row in rows)
    assert landing_check.run()["state"] == "failed"


def test_at_most_five_differing_pages_are_named_in_one_problem(lib):
    for slug in "defgh":
        lib.page(slug, 1)  # five more pages, on top of a, b and c, none of them indexed yet
    lib.keep_rows(lambda row: False)
    with open(lib.path("sections.jsonl"), "a") as f:
        f.write(json.dumps({"id": "unrelated", "path": "docs/unrelated.md"}) + "\n")
    r = landing_check.run()
    assert len(r["problems"]) == 1
    named = sum(f"docs/{s}.md" in r["problems"][0] for s in "abcdefgh") + ("docs/unrelated.md" in r["problems"][0])
    assert named == 5


def test_a_missing_index_fails(lib):
    os.remove(lib.path("sections.jsonl"))
    assert landing_check.run()["state"] == "failed"


def test_an_unreadable_index_fails(lib):
    with open(lib.path("sections.jsonl"), "a") as f:
        f.write('{"id": "half a ro')
    assert landing_check.run()["state"] == "failed"


def test_a_library_that_lost_every_page_says_so(lib):
    for slug in ("a", "b", "c"):
        os.remove(lib.pg.dest(slug))
    r = landing_check.run()
    assert r["state"] == "failed" and r["problems"] == ["the library has no pages"]


def test_an_empty_library_does_not_pass(empty):
    assert landing_check.run()["state"] != "passed"


def test_an_empty_index_over_an_empty_library_does_not_pass(empty):
    open(empty / "sections.jsonl", "w").close()
    assert landing_check.run()["state"] != "passed"


# --- files left out on purpose --------------------------------------------------------------------------------

def test_duplicate_mdx_files_are_not_flagged(lib):
    with open(lib.path("docs/cookbooks__x.md"), "w") as f:
        f.write("# A duplicate of a cookbook\n\nWords.\n")
    assert landing_check.run()["state"] == "passed"


def test_a_blocked_blog_file_is_not_flagged(lib, monkeypatch, tmp_path_factory):
    tools = tmp_path_factory.mktemp("tools")
    (tools / "checker.py").write_text("import sys\nfor f in sys.argv[1:]:\n    if f.endswith('refused.txt'):\n        print(f + ':1: refused')\nsys.exit(0)\n")
    (tools / "config.json").write_text("{}")
    monkeypatch.setenv("JEV_PRIVATE_CHECKER", str(tools / "checker.py"))
    monkeypatch.setenv("JEV_PRIVATE_CONFIG", str(tools / "config.json"))
    os.makedirs(lib.path("blog"))
    for name in ("kept", "refused"):
        with open(lib.path(f"blog/{name}.txt"), "w") as f:
            f.write(f"# Post {name}\n\nA sentence of invented body text that is long enough to keep.\n")
    lib.build()
    assert "blog/refused.txt" not in {row["path"] for row in lib.rows()}
    assert landing_check.run()["state"] == "passed"


# --- vectors --------------------------------------------------------------------------------------------------

def test_stale_vectors_fail(lib, monkeypatch):
    monkeypatch.delenv("JEV_SEMANTIC")
    pytest.importorskip("numpy")  # semantic.py needs numpy; CI installs only pytest and pyyaml
    import semantic
    monkeypatch.setattr(semantic, "available", lambda: (True, "ok"))
    monkeypatch.setattr(semantic, "stale", lambda rows: "stale semantic index; run refresh.sh")
    r = landing_check.run()
    assert r["state"] == "failed" and any("stale semantic index" in p for p in r["problems"])
    assert not any("refresh.sh" in p for p in r["problems"])  # the failure line gives the one command to run


def test_keyword_only_is_a_note_not_a_failure(lib, monkeypatch):
    pytest.importorskip("numpy")  # semantic.py needs numpy; CI installs only pytest and pyyaml
    import semantic
    def loads_the_model():
        raise AssertionError("JEV_SEMANTIC=off must not load the model")
    monkeypatch.setattr(semantic, "available", loads_the_model)
    r = landing_check.run()
    assert r["state"] == "passed" and len(r["notes"]) == 1 and "keyword-only" in r["notes"][0]


def test_a_missing_model_is_a_note_with_its_reason(lib, monkeypatch):
    monkeypatch.delenv("JEV_SEMANTIC")
    pytest.importorskip("numpy")  # semantic.py needs numpy; CI installs only pytest and pyyaml
    import semantic
    monkeypatch.setattr(semantic, "available", lambda: (False, "model unavailable (OSError)"))
    r = landing_check.run()
    assert r["state"] == "passed" and "keyword-only" in r["notes"][0] and "model unavailable (OSError)" in r["notes"][0]


def test_an_install_without_numpy_is_a_note(lib, monkeypatch):
    monkeypatch.delenv("JEV_SEMANTIC")
    monkeypatch.setitem(sys.modules, "semantic", None)  # importing it now raises ImportError, as a missing numpy does
    r = landing_check.run()
    assert r["state"] == "passed" and "keyword-only" in r["notes"][0]


def saved_vectors(semantic, rows):
    import numpy as np
    np.save(semantic.VEC, np.zeros((len(rows), 2), dtype=np.float32))
    with open(semantic.META, "w") as f:
        json.dump({"model": semantic.model_id(), "dim": 2, "ids": [r["id"] for r in rows], "owners": list(range(len(rows))),
                   "keys": {r["id"]: semantic._key(r) for r in rows}}, f)


def test_stale_says_nothing_when_vectors_match_and_loads_no_model(lib, monkeypatch):
    pytest.importorskip("numpy")  # semantic.py needs numpy; CI installs only pytest and pyyaml
    import semantic
    def no_model():
        raise AssertionError("stale must not load the model")
    monkeypatch.setattr(semantic, "_load_model", no_model)
    rows = lib.rows()
    saved_vectors(semantic, rows)
    assert semantic.stale(rows) is None


@pytest.mark.parametrize("fault, words", [("no files", "no semantic index"), ("other model", "index built with model"),
                                          ("moved section", "stale semantic index")])
def test_stale_names_each_way_vectors_go_wrong(lib, fault, words):
    pytest.importorskip("numpy")  # semantic.py needs numpy; CI installs only pytest and pyyaml
    import semantic
    rows = lib.rows()
    saved_vectors(semantic, rows)
    if fault == "no files":
        os.remove(semantic.VEC)
    elif fault == "other model":
        meta = json.load(open(semantic.META))
        meta["model"] = "another/model"
        json.dump(meta, open(semantic.META, "w"))
    else:
        rows[0] = dict(rows[0], line_start=rows[0]["line_start"] + 1)
    assert words in semantic.stale(rows)


def test_scores_gives_the_reason_stale_gives(lib, monkeypatch):
    pytest.importorskip("numpy")  # semantic.py needs numpy; CI installs only pytest and pyyaml
    import semantic
    monkeypatch.setattr(semantic, "stale", lambda rows: "the reason stale gave")
    assert semantic.scores("a question", lib.rows()) == (None, "the reason stale gave")


# --- a page that collapsed ------------------------------------------------------------------------------------

def test_shrink_limit_edges():
    assert landing_check.shrunk(100, 29) is True
    assert landing_check.shrunk(100, 30) is False
    assert landing_check.shrunk(0, 0) is False


def test_html_is_only_looked_for_at_the_top():
    assert landing_check.looks_like_html("<!DOCTYPE html>\n<p>x</p>") is True
    assert landing_check.looks_like_html("\n\n<HTML lang='en'>") is True
    assert landing_check.looks_like_html("# Title\n\nA page that mentions <html> at the start.") is True
    assert landing_check.looks_like_html("# Title\n\n" + "words " * 100 + "<html>") is False


def collapse(lib, slug):
    """A real update: the old copy goes to this run's archive, and a much smaller one takes its place."""
    lib.pg.write_page(slug, "# Big\n\n" + "Plenty of words on this page. " * 100, T13)
    lib.pg.archive(lib.pg.dest(slug), "changed", T14)
    lib.pg.write_page(slug, "# Big\n\nA stub.\n", T14)


def test_a_collapsed_changed_page_fails(lib):
    collapse(lib, "b")
    lib.build()
    r = landing_check.run(changed=["b"], now=T14)
    assert r["state"] == "failed" and any("docs/b.md" in p for p in r["problems"])


def test_a_changed_page_with_no_old_copy_has_no_size_check(lib):
    lib.pg.write_page("b", "# Big\n\nA stub.\n", T14)
    lib.build()
    assert landing_check.run(changed=["b"], now=T14)["state"] == "passed"


def test_a_page_not_in_the_changed_list_has_no_size_check(lib):
    collapse(lib, "b")
    lib.build()
    assert landing_check.run(changed=["a"], now=T14)["state"] == "passed"


def test_a_page_opening_as_html_fails(lib):
    lib.page("d", 0)
    with open(lib.pg.dest("d"), "a") as f:
        f.write("<!doctype html><html><body>An error page from a server.</body></html>\n")
    lib.build()
    r = landing_check.run(added=["d"], now=T14)
    assert r["state"] == "failed" and any("docs/d.md" in p for p in r["problems"])


def test_a_changed_page_replaced_by_an_html_error_page_fails(lib):
    """The likeliest real case: a server error page takes the place of a page that was fine."""
    lib.pg.write_page("b", "# Big\n\n" + "Plenty of words on this page. " * 5, T13)
    lib.pg.archive(lib.pg.dest("b"), "changed", T14)
    lib.pg.write_page("b", "<!doctype html><html><body>" + "An error page from a server. " * 5 + "</body></html>\n", T14)
    lib.build()
    r = landing_check.run(changed=["b"], now=T14)
    assert r["state"] == "failed" and any("docs/b.md opens as HTML" in p for p in r["problems"])


def test_a_blog_post_opening_as_html_is_not_flagged(lib):
    os.makedirs(lib.path("blog"))
    with open(lib.path("blog/post.txt"), "w") as f:
        f.write("<html>A sentence of invented body text that is long enough to keep around here.</html>\n")
    lib.build()
    assert landing_check.run(added=["blog/post"], now=T14)["state"] == "passed"


# --- the library as a whole -----------------------------------------------------------------------------------

def was_twenty_sections():
    return {("docs/old.md", f"old heading {n}") for n in range(20)}


def test_a_section_count_down_15_percent_fails(lib):
    lib.page("d", 11)  # 6 + 11 = 17 sections, against 20 before
    lib.build()
    r = landing_check.run(before=was_twenty_sections())
    assert r["state"] == "failed" and r["sections"] == 17


def test_a_section_count_down_5_percent_passes(lib):
    lib.page("d", 13)  # 6 + 13 = 19 sections, against 20 before
    lib.build()
    r = landing_check.run(before=was_twenty_sections())
    assert r["state"] == "passed" and r["sections"] == 19


# --- when the check itself breaks -----------------------------------------------------------------------------

def test_a_crash_inside_says_unavailable(lib, monkeypatch):
    import build_index
    def broken(blocked=None):
        raise KeyError("boom")
    monkeypatch.setattr(build_index, "expected_rows", broken)
    r = landing_check.run()
    assert r["state"] == "unavailable" and "KeyError" in r["notes"][0]


# --- the notice -----------------------------------------------------------------------------------------------

def test_a_pass_with_changes_names_its_counts():
    r = {"state": "passed", "problems": [], "notes": [], "sections": 1251, "pages": 142}
    assert landing_check.notice_lines(r, True) == ["Update check: 1,251 sections from 142 pages match the saved pages."]


def test_a_pass_with_no_changes_says_nothing():
    r = {"state": "passed", "problems": [], "notes": ["routing is keyword-only (JEV_SEMANTIC=off)"], "sections": 6, "pages": 3}
    assert landing_check.notice_lines(r, False) == []


def test_keyword_only_shows_after_an_update():
    r = {"state": "passed", "problems": [], "notes": ["routing is keyword-only (JEV_SEMANTIC=off)"], "sections": 6, "pages": 3}
    assert landing_check.notice_lines(r, True)[1] == "Update check: routing is keyword-only (JEV_SEMANTIC=off)."


def test_a_failure_line_says_how_to_fix_it_whatever_changed(empty):
    import paths
    for changes in (True, False):
        assert landing_check.notice_lines(failed_result("docs/a.md is short"), changes) == [
            f"Update check: docs/a.md is short; run {paths.REFRESH}."]


def test_at_most_three_failure_lines_show():
    assert len(landing_check.notice_lines(failed_result("one", "two", "three", "four"), True)) == 3


def test_failure_lines_cut_at_three_say_how_many_more(lib):
    lines = landing_check.notice_lines(failed_result("one", "two", "three", "four", "five", "six"), True)
    assert len(lines) == 3 and lines[2].endswith("and 3 more.") and "and" not in lines[1].split("; run")[1]
    assert len(" ".join(lines)) < lib.cn.NOTICE_CAP
    assert not any("more" in l for l in landing_check.notice_lines(failed_result("one", "two", "three"), True))


def test_a_check_that_could_not_run_says_so_either_way():
    r = {"state": "unavailable", "problems": [], "notes": ["KeyError"], "sections": 0, "pages": 0}
    for changes in (True, False):
        assert landing_check.notice_lines(r, changes) == ["Update check couldn't confirm this update (KeyError)."]


def test_the_failure_line_goes_first_past_the_notice_cap(lib):
    parts = ["TypeSafe changed 200 page(s): " + ", ".join(f"a-very-long-page-name-for-the-cap-{n}" for n in range(200)) + "."]
    line = landing_check.notice_lines(failed_result("docs/a.md is short"), True)[0]
    assert line in lib.cn.notice_text(parts, [line])


def test_the_could_not_confirm_line_goes_first_past_the_notice_cap(lib):
    parts = ["x" * 5000]
    line = "Update check couldn't confirm this update (KeyError)."
    assert line in lib.cn.notice_text(parts, [line])


def test_the_update_check_goes_ahead_of_the_library_tests_and_page_names(lib):
    line = "Update check: docs/a.md is short."
    text = lib.cn.notice_text(["TypeSafe changed 1 page(s): a."], ["Library tests: 1 failed.", "a later note", line])
    assert text == f"{line} Library tests: 1 failed. TypeSafe changed 1 page(s): a. a later note"


# --- wired into the background check, the fetch and the refresh ----------------------------------------------

def test_a_quiet_check_with_a_bad_index_writes_a_notice(lib):
    lib.keep_rows(lambda row: row["path"] != "docs/b.md")
    res = lib.cn.run(lib.quiet_site(), now=T14)
    assert res["changed"] == [] and "docs/b.md" in res["notice"]
    assert "Update check:" in open(lib.path("NEW_PAGES.txt")).read()


def test_a_quiet_check_with_a_good_index_writes_none(lib):
    res = lib.cn.run(lib.quiet_site(), now=T14)
    assert res["notice"] == "" and not os.path.exists(lib.path("NEW_PAGES.txt"))


def test_problems_reach_the_refresh_log(lib, monkeypatch):
    monkeypatch.delenv("JEV_LOG", raising=False)
    lib.keep_rows(lambda row: row["path"] != "docs/b.md")
    res = lib.cn.run(lib.quiet_site(), now=T14)
    assert isinstance(res["landing_problems"], list) and len(res["landing_problems"]) == 1
    log = open(lib.path("logs/refresh.jsonl"), encoding="utf-8").read().splitlines()
    assert json.loads(log[-1])["landing_problems"] == 1


def full_refresh_with_a_bad_index(lib, monkeypatch):
    import fetch
    monkeypatch.setattr("blog.list_posts", lambda f: [])
    lib.page("b", 3)
    new = "# b heading 0\n\nNew words about b, a little more than before.\n"
    slugs = list(lib.pg.library())
    f = site(lib.pg, {**{s: ("# %s\n\nx\n" % s) for s in slugs}, "b": new}, {s: None for s in slugs}, slugs, [])
    monkeypatch.setattr(lib.cn, "rebuild_index", lambda: None)  # the index stays as it was, so it can't match the new page
    return fetch.main(f)


def test_a_full_refresh_problem_reaches_the_refresh_log(lib, monkeypatch):
    monkeypatch.delenv("JEV_LOG", raising=False)
    assert full_refresh_with_a_bad_index(lib, monkeypatch) == 0
    log = [json.loads(l) for l in open(lib.path("logs/refresh.jsonl"), encoding="utf-8")]
    assert log[-1]["landing_problems"] >= 1 and "changed" in log[-1]


def test_a_full_refresh_writes_no_log_when_logging_is_off(lib, monkeypatch):
    monkeypatch.setenv("JEV_LOG", "off")
    assert full_refresh_with_a_bad_index(lib, monkeypatch) == 0
    assert not os.path.exists(lib.path("logs/refresh.jsonl"))


def test_a_collapsed_update_is_reported_from_a_real_change(lib, monkeypatch):
    """The whole path: the site serves a stub, the old copy is archived, the index is rebuilt, and the check finds it."""
    lib.pg.write_page("b", "# Big\n\n" + "Plenty of words on this page. " * 100, T13)
    lib.build()
    def rebuild():
        lib.build()
    monkeypatch.setattr(lib.cn, "rebuild_index", rebuild)
    slugs = list(lib.pg.library())
    dates = {s: "2026-10-12T00:00:00Z" for s in slugs}
    dates["b"] = "2026-10-14T21:00:00Z"
    res = lib.cn.run(site(lib.pg, {"b": "# Big\n\nA stub.\n"}, dates, slugs, []), now=T14)
    assert res["changed"] == ["b"]
    assert len(res["landing_problems"]) == 1 and "docs/b.md" in res["landing_problems"][0]
    assert res["notice"].startswith("Update check:") and "docs/b.md" in res["notice"]


def test_a_good_update_says_what_it_checked(lib, monkeypatch):
    monkeypatch.setattr(lib.cn, "rebuild_index", lib.build)
    slugs = list(lib.pg.library())
    dates = {s: "2026-10-12T00:00:00Z" for s in slugs}
    dates["b"] = "2026-10-14T21:00:00Z"
    new = "# b heading 0\n\nNew words about b, a little more than before.\n\n# b heading 1\n\nMore.\n"
    res = lib.cn.run(site(lib.pg, {"b": new}, dates, slugs, []), now=T14)
    assert res["landing_problems"] == []
    assert res["notice"].startswith("Update check: 6 sections from 3 pages match the saved pages.")


def test_the_check_keeps_the_section_list_from_before_the_update(lib, monkeypatch):
    """A rebuild that loses most of the library is compared with the list from before it, not with itself."""
    def rebuild():
        for slug in ("a", "c"):
            os.remove(lib.pg.dest(slug))
        lib.build()
    monkeypatch.setattr(lib.cn, "rebuild_index", rebuild)
    res = {"changed": ["b"], "added": [], "removed": [], "moved": {}, "removed_sections": [], "added_sections": []}
    lib.cn.record_changes(res, T14)
    assert any("6" in p and "2" in p for p in res["landing_problems"])


def test_a_site_that_cannot_be_read_still_shows_the_update_check_warning(lib):
    """A half-written page is recorded before the run gives up; its Update check line is kept with the test lines."""
    lib.pg.write_page("b", "# Big\n\n" + "Plenty of words on this page. " * 100, T13)
    lib.build()
    raw = lib.pg.raw_dest("b")
    with open(raw, "w", encoding="utf-8") as f:
        f.write(f"<!-- saved 2026-10-14T21:07:12Z from {lib.pg.BASE}b.md -->\n\n# Big\n\nA stub.\n")
    with pytest.raises(RuntimeError):
        lib.cn.run(site(lib.pg, {}, None, None, []), now=T14)
    assert "Update check:" in open(lib.path("NEW_PAGES.txt")).read()


def test_main_prints_the_result_and_returns_zero(lib, capsys):
    assert landing_check.main() == 0
    assert "Update check: 6 sections from 3 pages match the saved pages." in capsys.readouterr().out
    assert not os.path.exists(lib.path("check.lock"))


def test_main_steps_aside_for_a_running_check(lib, capsys):
    assert lib.pg.take_lock()
    assert landing_check.main() == 0
    assert "Update check: skipped, another check is running." in capsys.readouterr().out
    assert os.path.exists(lib.path("check.lock"))


def test_main_returns_zero_with_no_library(empty, capsys):
    assert landing_check.main() == 0
    assert "Update check:" in capsys.readouterr().out


def test_refresh_runs_the_check_after_the_change_check_and_before_the_tests(tmp_path):
    bin_, log = fake_python(tmp_path)
    assert run_refresh(tmp_path, bin_, JEV_SEMANTIC="off").returncode == 0
    calls = [line.split()[0] for line in log.read_text().splitlines() if line.split()[0].endswith(".py")]
    names = [os.path.basename(c) for c in calls]
    assert names.index("check_new.py") < names.index("landing_check.py") < names.index("library_tests.py")


def test_refresh_carries_on_when_the_check_fails(tmp_path):
    bin_ = tmp_path / "bin"
    bin_.mkdir()
    log = tmp_path / "calls.log"
    py = bin_ / "python3"
    py.write_text(f'#!/bin/bash\necho "$*" >> {log}\ncase "$1" in *landing_check.py) exit 3;; esac\nexit 0\n')
    py.chmod(py.stat().st_mode | stat.S_IEXEC)
    r = run_refresh(tmp_path, bin_, JEV_SEMANTIC="off")
    assert r.returncode == 0 and "library_tests.py" in log.read_text()


# --- the index file itself ------------------------------------------------------------------------------------

def test_a_killed_index_write_leaves_the_old_file(lib, monkeypatch):
    before = open(lib.path("sections.jsonl"), "rb").read()
    real, calls = json.dumps, []
    def dies_midway(*a, **k):
        calls.append(1)
        if len(calls) == 3:
            raise KeyboardInterrupt
        return real(*a, **k)
    import build_index
    monkeypatch.setattr(json, "dumps", dies_midway)
    with pytest.raises(KeyboardInterrupt):
        build_index.main(prepare=False)
    monkeypatch.undo()
    assert open(lib.path("sections.jsonl"), "rb").read() == before
    assert [f for f in os.listdir(lib.root) if f.endswith(".tmp")] == []


@pytest.mark.parametrize("call", ["fsync", "replace"])
def test_a_write_killed_after_the_temp_file_exists_leaves_the_old_file(lib, monkeypatch, call):
    before = open(lib.path("sections.jsonl"), "rb").read()
    lib.page("d", 3)  # the next build would write different rows
    def dies(*a, **k):
        raise KeyboardInterrupt
    monkeypatch.setattr(os, call, dies)
    import build_index
    with pytest.raises(KeyboardInterrupt):
        build_index.main(prepare=False)
    monkeypatch.undo()
    assert open(lib.path("sections.jsonl"), "rb").read() == before
    assert [f for f in os.listdir(lib.root) if f.endswith(".tmp")] == []


def test_the_rows_the_build_writes_are_the_rows_the_check_expects(lib):
    import build_index
    assert build_index.expected_rows() == lib.rows()


# --- the real library -----------------------------------------------------------------------------------------

@needs_lib
def test_the_real_library_raises_no_flags():
    fresh_modules()
    r = landing_check.run()
    assert r["state"] == "passed", r


def _crash(lib, monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("boom")
    monkeypatch.setattr(lib.cn.landing_check, "_check", boom)


def test_a_crashed_check_on_a_quiet_run_counts_as_a_problem_in_the_log(lib, monkeypatch):
    monkeypatch.delenv("JEV_LOG", raising=False)
    _crash(lib, monkeypatch)
    res = lib.cn.run(lib.quiet_site(), now=T14)
    assert len(res["landing_problems"]) >= 1
    log = open(lib.path("logs/refresh.jsonl"), encoding="utf-8").read().splitlines()
    assert json.loads(log[-1])["landing_problems"] >= 1


def test_a_crashed_check_after_a_change_counts_as_a_problem_in_the_log(lib, monkeypatch):
    monkeypatch.delenv("JEV_LOG", raising=False)
    _crash(lib, monkeypatch)
    monkeypatch.setattr(lib.cn, "rebuild_index", lib.build)
    slugs = list(lib.pg.library())
    dates = {s: "2026-10-12T00:00:00Z" for s in slugs}
    dates["b"] = "2026-10-14T21:00:00Z"
    new = "# b heading 0\n\nNew words about b, a little more than before.\n"
    res = lib.cn.run(site(lib.pg, {"b": new}, dates, slugs, []), now=T14)
    assert res["changed"] == ["b"] and len(res["landing_problems"]) >= 1
