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


def test_file_added_then_deleted_still_fails(repo):
    add(repo, "docs/superpowers/plans/p.md", "a\n")
    git(repo, "rm", "-q", "docs/superpowers/plans/p.md")
    git(repo, "commit", "-q", "-m", "remove")
    add(repo, "jev-sources/route.py", "x = 5\n")
    found = check()
    assert any("plan or working note" in w and "removed later" in w for w in found)


def test_existing_kind_of_image_passes(repo):
    add(repo, "jev-sources/images/diagram.png", b"\x89PNG\r\n\x1a\n\0\0")
    assert check() == []


def test_commit_message_with_plan_text_fails(repo):
    (repo / "jev-sources/route.py").write_text("x = 6\n")
    git(repo, "commit", "-q", "-am", "wip\n\n**Status (" + "2026-10-07):** handoff")
    assert any("message reads like" in w for w in check())


def test_unfilled_template_counts_as_no_scope(repo):
    add(repo, "jev-sources/route.py", "x = 7\n")
    assert any("no Scope line" in w for w in check(body="Scope: \n\n## What changes\n"))


def test_any_home_folder_path_fails(repo):
    add(repo, "jev-sources/c.py", "P = '/" + "Users/x/.claude/settings.json'\n")
    assert any("private note" in w for w in check())


# 2026-10-07 security audit

def test_file_added_only_in_a_merge_commit_fails(repo):
    git(repo, "checkout", "-q", "-b", "side", "main")
    add(repo, "jev-sources/side.py", "s = 1\n")
    git(repo, "checkout", "-q", "pr")
    git(repo, "merge", "-q", "--no-ff", "--no-commit", "side")
    (repo / "jev-sources/evil.md").write_text("**Status (" + "2026-10-07):** x\n")
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", "merge")
    git(repo, "rm", "-q", "jev-sources/evil.md")
    git(repo, "commit", "-q", "-m", "remove")
    assert any("evil.md" in f for f, _ in pc.problems("main", "HEAD", "Scope: jev-sources/")[1])


def test_file_turned_into_a_symlink_is_checked(repo):
    (repo / "jev-sources/route.py").unlink()
    os.symlink("/" + "Users/x/Documents/secret", repo / "jev-sources/route.py")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "link")
    assert any("private note" in w for w in check())


def test_utf16_text_cannot_hide_a_marker(repo):
    add(repo, "jev-sources/u16.dat", ("Obsidian" + " Vaults").encode("utf-16"))
    assert any("private note" in w for w in check())


def test_file_names_cannot_start_a_workflow_command(repo, capsys):
    add(repo, "jev-sources/plans/x\n::stop-commands::abc", "a\n")
    pc.main(["--base", "main", "--head", "HEAD", "--body", "Scope: jev-sources/"])
    assert not any(l.startswith("::stop-commands") for l in capsys.readouterr().out.splitlines())


def test_too_many_files_fails_closed(repo, monkeypatch):
    monkeypatch.setattr(pc, "MAX_BLOBS", 2)
    for i in range(3):
        add(repo, f"jev-sources/f{i}.py", f"x = {i}\n")
    assert any("split the PR" in w for w in check())



# A job named pr-contents in another workflow could report a pass under the required check's name.

def test_other_workflow_borrowing_the_check_name_fails(repo):
    add(repo, ".github/workflows/fake.yml", "jobs:\n  pr-contents:\n    runs-on: ubuntu-22.04\n")
    assert any("uses the name pr-contents" in w for w in check(body="Scope: .github/"))


def test_name_split_by_an_expression_still_fails(repo):
    add(repo, ".github/workflows/fake.yml", "jobs:\n  x:\n    name: pr-${{ 'contents' }}\n")
    assert any("uses the name pr-contents" in w for w in check(body="Scope: .github/"))


def test_check_own_workflow_and_other_workflows_pass(repo):
    add(repo, ".github/workflows/pr-contents.yml", "name: pr-contents\njobs:\n  pr-contents:\n    runs-on: x\n")
    add(repo, ".github/workflows/tests.yml", "name: tests\njobs:\n  test:\n    permissions:\n      contents: read\n")
    assert check(body="Scope: .github/") == []
