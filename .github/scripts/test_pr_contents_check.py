import os, pathlib, subprocess, sys
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import pr_contents_check as pc


def git(d, *a):
    subprocess.run(["git", "-C", str(d), *a], check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path, monkeypatch):
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "config", "user.email", "t@example.com")
    git(tmp_path, "config", "user.name", "t")
    (tmp_path / "jev-sources").mkdir()
    (tmp_path / "jev-sources/route.py").write_text("x = 1\n")
    (tmp_path / "README.md").write_text("hi\n")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-q", "-m", "base")
    git(tmp_path, "checkout", "-q", "-b", "pr")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def add(repo, path, content):
    p = repo / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(content) if isinstance(content, bytes) else p.write_text(content)
    git(repo, "add", path)
    git(repo, "commit", "-q", "-m", path)


def check(body="Scope: jev-sources/"):
    return [why for _, why in pc.problems("main", "HEAD", body)[1]]


def test_clean_pr_passes(repo):
    add(repo, "jev-sources/route.py", "x = 2\n")
    add(repo, "jev-sources/tests/test_plan_parser.py", "def test(): pass\n")
    assert check() == []


def test_missing_scope_line_fails(repo):
    add(repo, "jev-sources/route.py", "x = 2\n")
    assert any("no Scope line" in w for w in check(body="Fixes the router."))


def test_file_outside_scope_fails(repo):
    add(repo, "README.md", "changed\n")
    assert any("outside the Scope" in w for w in check())


def test_plan_paths_and_names_fail(repo):
    add(repo, "docs/superpowers/plans/x.md", "a\n")
    add(repo, "jev-sources/handoff-2026-10-07.md", "a\n")
    found = check(body="Scope: jev-sources/ docs/")
    assert sum("plan or working note" in w for w in found) == 2


def test_plan_text_fails_whatever_the_name(repo):
    add(repo, "jev-sources/router-thoughts.md", "**Status (" + "2026-10-07):** in progress\n")
    add(repo, "jev-sources/b.py", "P = '/" + "Users/someone/Documents/x'\n")
    assert sum("private note" in w for w in check()) == 2


def test_binary_and_large_files_fail_outside_ratings(repo):
    add(repo, "jev-sources/blob.bin", b"\0\1\2")
    add(repo, "jev-sources/big.txt", "a" * 1000001)
    found = check()
    assert any("binary" in w for w in found) and any("over the 1 MB" in w for w in found)


def test_new_top_level_folder_needs_naming(repo):
    add(repo, "tools/x.py", "x = 1\n")
    assert any("new top-level" in w for w in check(body="Scope: jev-sources/ tools/x.py"))
    assert check(body="Scope: tools/") == []


def test_scope_line_formats(repo):
    add(repo, "jev-sources/route.py", "x = 3\n")
    assert check(body="Summary\n\n**Scope:** `jev-sources/`, README.md\n") == []


def test_dot_folders_in_scope(repo):
    add(repo, ".github/workflows/x.yml", "name: x\n")
    add(repo, "jev-sources/route.py", "x = 4\n")
    assert check(body="Scope: .github/, ./jev-sources/") == []


def test_the_check_passes_on_itself():
    here = pathlib.Path(pc.__file__).resolve().parent
    for name in ("pr_contents_check.py", "test_pr_contents_check.py"):
        assert not pc.MARKERS.search((here / name).read_text()), name
