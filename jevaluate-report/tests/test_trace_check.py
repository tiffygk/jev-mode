"""trace_check.py against its blind probe set (fixtures/trace-probes.json, written once from the rules by an agent
that never saw the script, never edited to fit it) and a few cases the probes leave out."""
import importlib.util, json, os, pathlib, subprocess, sys

import pytest

HERE = pathlib.Path(__file__).parent
CHECK = HERE.parent / "scripts" / "trace_check.py"
spec = importlib.util.spec_from_file_location("trace_check", CHECK)
tc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tc)
PROBES = json.loads((HERE / "fixtures" / "trace-probes.json").read_text())


def git(cwd, *args):
    env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.com", GIT_COMMITTER_NAME="t",
               GIT_COMMITTER_EMAIL="t@example.com")
    return subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, check=True, env=env).stdout.strip()


def library_as_of(tmp, date):
    """A copy of the Jev Sources library as it stood on `date`: each page TypeSafe changed or removed since then is
    taken from the first archive run after that date, which kept the copy it replaced. A report quotes the pages of
    its day, so a later docs change must not fail it."""
    import shutil
    lib = pathlib.Path(os.path.expanduser(os.environ.get("JEV_SOURCES_DATA", "~/.claude/jev-sources-data")))
    if not (lib / "archive").is_dir():
        pytest.skip(f"the Jev Sources library has no archive, so its pages as of {date} can't be rebuilt")
    assert (lib / "docs").is_dir(), f"the Jev Sources library at {lib} has no docs/ folder"
    out = tmp / "lib-as-of"
    for kind in ("docs", "cookbooks", "patterns", "blog"):
        if (lib / kind).is_dir():
            shutil.copytree(lib / kind, out / kind)
    runs = sorted(r for r in (lib / "archive").iterdir() if r.name[:10] > date)
    for run in reversed(runs):
        for state in ("changed", "removed"):
            for f in (run / state).glob("*/*.md"):
                if f.parent.name in ("docs", "cookbooks", "patterns", "blog"):
                    (out / f.parent.name).mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(f, out / f.parent.name / f.name)
    return out


def test_library_as_of_skips_a_library_with_no_archive(tmp_path, monkeypatch):
    """A library with no archive/ folder can't be rolled back to a report's date, so the dated tests skip rather than
    check today's pages."""
    lib = tmp_path / "lib"
    (lib / "docs").mkdir(parents=True)
    monkeypatch.setenv("JEV_SOURCES_DATA", str(lib))
    with pytest.raises(pytest.skip.Exception, match="no archive"):
        library_as_of(tmp_path, "2026-10-01")


def build(tmp, docs, files):
    lib, repo = tmp / "lib", tmp / "repo"
    lib.mkdir()
    for url, text in docs.items():
        path, _ = tc.library_path(url, str(lib))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        pathlib.Path(path).write_text(text)
    repo.mkdir()
    git(repo, "init", "-q")
    for path, text in files.items():
        (repo / path).parent.mkdir(parents=True, exist_ok=True)
        (repo / path).write_text(text)
    (repo / ".keep").write_text("")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "x")
    return lib, repo, git(repo, "rev-parse", "HEAD")


def run(tmp, text, docs=None, files=None, extra=()):
    lib, repo, sha = build(tmp, docs or {}, files or {})
    report = tmp / "report.md"
    report.write_text(f"---\nrepo: https://github.com/acme/widget\ncommit: {sha}\n---\n\n" + text.replace("{commit}", sha))
    r = subprocess.run([sys.executable, "-I", str(CHECK), str(report), "--library", str(lib), "--checkout", str(repo), *extra],
                       capture_output=True, text=True)
    rules = [l.split(":")[0] for l in r.stdout.splitlines() if not l.startswith(("counts ", "unchecked:"))]
    return r.returncode, rules, r.stdout


@pytest.mark.parametrize("p", PROBES, ids=[p["id"] for p in PROBES])
def test_probe(tmp_path, p):
    code, rules, out = run(tmp_path, p["text"], p["docs"], p["files"])
    if p["expect"] == "pass":
        assert code == 0 and rules == [], out
    else:
        assert code == 1 and rules == [p["expect"]], out


def test_other_commit_and_other_repo_are_unchecked(tmp_path):
    text = ('The [old file](https://github.com/acme/widget/blob/' + "1" * 40 + '/a.py) says "this is made up".\n\n'
            'The [fork](https://github.com/other/widget/blob/{commit}/a.py) says "this is made up too".\n')
    code, rules, out = run(tmp_path, text)
    assert code == 0 and rules == [] and out.count("unchecked:") == 2, out


def test_code_quotes_need_a_checkout(tmp_path):
    report = tmp_path / "r.md"
    report.write_text("---\nrepo: https://github.com/acme/widget\ncommit: " + "a" * 40 + "\n---\n\n"
                      "The [file](https://github.com/acme/widget/blob/" + "a" * 40 + '/x.py) has "one two three".\n')
    r = subprocess.run([sys.executable, "-I", str(CHECK), str(report), "--library", str(tmp_path)], capture_output=True, text=True)
    assert r.returncode == 2 and "--checkout" in r.stderr


def test_checkout_without_the_commit_is_refused(tmp_path):
    lib, repo, sha = build(tmp_path, {}, {"x.py": "one two three\n"})
    report = tmp_path / "r.md"
    report.write_text("---\nrepo: https://github.com/acme/widget\ncommit: " + "b" * 40 + "\n---\n\n"
                      "The [file](https://github.com/acme/widget/blob/" + "b" * 40 + '/x.py) has "one two three".\n')
    r = subprocess.run([sys.executable, "-I", str(CHECK), str(report), "--library", str(lib), "--checkout", str(repo)],
                       capture_output=True, text=True)
    assert r.returncode == 2 and "does not hold commit" in r.stderr


def test_docs_slug_cannot_leave_the_library(tmp_path):
    code, rules, out = run(tmp_path, 'The [page](https://docs.typesafe.ai/a/../../etc/passwd) says "root is here now".\n')
    assert code == 1 and rules == ["docs-page"], out


def test_cases_from_real_reports(tmp_path):
    """Found running the check on the skimmer report and a Codex report (2026-10-22): each list item is its own
    paragraph; a quote wrapped around a link belongs to that link; a quote not at its nearest link passes when
    another link in the paragraph holds it; table pipes are ignored."""
    files = {"a.md": "intro\n| cross-draw delta | mean 0.003 |\n", "b.go": "x := 1\nWould chunk \"{{.ID}}\" help?\n"}
    text = ("- [a](https://github.com/acme/widget/blob/{commit}/a.md#L1) holds intro.\n"
            "- \"cross-draw delta mean 0.003\" is one row ([a](https://github.com/acme/widget/blob/{commit}/a.md#L2)).\n\n"
            "It asks, \u201c[Would chunk \"{{.ID}}\" help?](https://github.com/acme/widget/blob/{commit}/b.go#L2)\u201d\n\n"
            "The file ([b](https://github.com/acme/widget/blob/{commit}/b.go#L1)) asks `Would chunk \"{{.ID}}\" help?` "
            "([#L2](https://github.com/acme/widget/blob/{commit}/b.go#L2)).\n")
    code, rules, out = run(tmp_path, text, files=files)
    assert code == 0 and rules == [], out
    bad = "The note ([b](https://github.com/acme/widget/blob/{commit}/b.go#L1)) shows `chunk \"item_3\"` as its id.\n"
    (tmp_path / "again").mkdir()
    code, rules, out = run(tmp_path / "again", bad, files=files)
    assert code == 1 and rules == ["code-quote"], out


def test_quote_across_blockquote_lines(tmp_path):
    """Found correcting the skimmer report (2026-11-03): a cookbook quote that wraps inside a > block."""
    docs = {"https://docs.typesafe.ai/cookbooks/rag": "> We picked these. Treat them as a starting point, not\n> defaults.\n"}
    link = "The [cookbook](https://docs.typesafe.ai/cookbooks/rag) says "
    code, rules, out = run(tmp_path, link + '"Treat them as a starting point, not defaults."\n', docs)
    assert code == 0 and rules == [], out
    (tmp_path / "again").mkdir()
    code, rules, out = run(tmp_path / "again", link + '"Treat them as a starting point, not as defaults."\n', docs)
    assert code == 1 and rules == ["docs-quote"], out


SKIMMER_COMMIT_RE =r"^commit:\s*([0-9a-f]{40})"


@pytest.mark.skipif(not os.path.isdir(os.path.expanduser(os.environ.get("JEV_SOURCES_DATA", "~/.claude/jev-sources-data"))),
                    reason="no Jev Sources library here (the script reads $JEV_SOURCES_DATA, else this default)")
def test_skimmer_docs_quotes_are_in_the_library(tmp_path):
    """Every TypeSafe docs quote the corrected skimmer report links is in the library as of the report's date (the posted one cites a 1.13 page
    TypeSafe has since removed, and two quotes with no docs link). Its code links are moved to
    another commit, so they are listed as unchecked (checking them needs a clone of the repo)."""
    import re
    text = re.sub(SKIMMER_COMMIT_RE, "commit: " + "0" * 40, (HERE / "fixtures" / "skimmer-corrected.md").read_text(), flags=re.M)
    report = tmp_path / "skimmer.md"
    report.write_text(text)
    lib = library_as_of(tmp_path, re.search(r"^date: (\S+)", text, re.M).group(1))
    r = subprocess.run([sys.executable, "-I", str(CHECK), str(report), "--library", str(lib)], capture_output=True, text=True)
    assert r.returncode == 0 and "counts docs 15," in r.stdout, r.stdout + r.stderr



@pytest.mark.skipif(not os.path.isdir(os.path.expanduser(os.environ.get("JEV_SOURCES_DATA", "~/.claude/jev-sources-data"))),
                    reason="no Jev Sources library here (the script reads $JEV_SOURCES_DATA, else this default)")
def test_report_in_the_current_template_docs_quotes_are_in_the_library(tmp_path):
    """The same docs quotes, as of the report's date, in the report rebuilt in the current template; its code links move to another commit."""
    import re
    text = re.sub(SKIMMER_COMMIT_RE, "commit: " + "0" * 40, (HERE / "fixtures" / "skimmer-report.md").read_text(), flags=re.M)
    report = tmp_path / "skimmer.md"
    report.write_text(text)
    lib = library_as_of(tmp_path, re.search(r"^date: (\S+)", text, re.M).group(1))
    r = subprocess.run([sys.executable, "-I", str(CHECK), str(report), "--library", str(lib)], capture_output=True, text=True)
    assert r.returncode == 0 and "counts docs 15," in r.stdout, r.stdout + r.stderr


@pytest.mark.skipif(not os.environ.get("JEVALUATE_REPORT_SKIMMER_CHECKOUT"),
                    reason="set JEVALUATE_REPORT_SKIMMER_CHECKOUT to a clone of dorkitude/skimmer to check its code quotes")
def test_report_in_the_current_template_code_quotes_are_at_the_commit():
    r = subprocess.run([sys.executable, "-I", str(CHECK), str(HERE / "fixtures" / "skimmer-report.md"),
                        "--checkout", os.environ["JEVALUATE_REPORT_SKIMMER_CHECKOUT"]], capture_output=True, text=True)
    assert r.returncode == 0 and "counts docs 15, code 18," in r.stdout, r.stdout + r.stderr

# Security review (2026-11-04): an option-shaped commit never reaches git, a very long paragraph is skipped rather than
# scanned, and text from the report is printed as printable characters only.
def test_option_shaped_commit_is_refused_before_git_runs(tmp_path):
    lib, repo, sha = build(tmp_path, {}, {"x.py": "one two three\n"})
    bad = "--output=written"  # no slash, so the link's commit segment matches it
    report = tmp_path / "r.md"
    report.write_text(f"---\nrepo: https://github.com/acme/widget\ncommit: {bad}\n---\n\n"
                      f'The [file](https://github.com/acme/widget/blob/{bad}/x.py) has "one two three".\n')
    r = subprocess.run([sys.executable, "-I", str(CHECK), str(report), "--library", str(lib), "--checkout", str(repo)],
                       capture_output=True, text=True, cwd=tmp_path)
    assert r.returncode == 2 and "40 hex characters" in r.stderr
    assert not list(tmp_path.rglob("written*"))


def test_very_long_paragraph_is_listed_not_scanned(tmp_path):
    text = "See [it](https://example.com/a) " + "`" * (tc.MAX_PARA + 10) + "\n"
    code, rules, out = run(tmp_path, text)
    assert code == 0 and rules == [] and "not scanned for quotes" in out, out


def test_control_characters_are_not_printed(tmp_path):
    text = 'The [file](https://github.com/acme/widget/blob/{commit}/a\x1b[2Jb.py) says "this is made up".\n'
    code, rules, out = run(tmp_path, text)
    assert code == 1 and "\x1b" not in out and "a?[2Jb.py" in out, out
