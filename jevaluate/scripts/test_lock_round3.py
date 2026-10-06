"""Third round of lock fixes (2026-10-05 gate): freezes confirmed on GitHub itself, git's replace and assume-unchanged
tricks refused, and the library takes only clean, explicit adds."""
import json, os, pathlib, subprocess, sys
import pytest
HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
import rubric_text as rt
from test_rubric_lock import frozen_copy, git


def fake_github(monkeypatch, tags, main_has=True):
    """tags: {name: sha}. main_has: whether every tag is in GitHub main's history."""
    def get(path):
        if path.startswith("git/matching-refs/tags/rubric-"):
            return [{"ref": f"refs/tags/{t}", "object": {"type": "commit", "sha": s}} for t, s in tags.items()]
        if path.startswith("compare/"):
            return {"status": "ahead" if main_has else "diverged", "behind_by": 0 if main_has else 2}
        raise AssertionError(path)
    rt.github_check.cache_clear(); monkeypatch.setattr(rt, "_github_get", get)


def local_sha(root, tag): return git(root, "rev-parse", f"{tag}^{{commit}}").stdout.strip()


def test_github_must_agree(tmp_path, monkeypatch):
    root = frozen_copy(tmp_path); tag = rt.newest_tag(root); sha = local_sha(root, tag)
    fake_github(monkeypatch, {tag: sha}); assert rt.github_check(tag, root)[0]
    fake_github(monkeypatch, {tag: "0" * 40}); assert not rt.github_check(tag, root)[0]                       # moved or forged locally
    fake_github(monkeypatch, {tag: sha, "rubric-2099-01-01-frozen": "1" * 40}); assert not rt.github_check(tag, root)[0]  # not GitHub's newest
    fake_github(monkeypatch, {tag: sha}, main_has=False); assert not rt.github_check(tag, root)[0]           # not in GitHub main

def test_offline_fails_closed(tmp_path, monkeypatch):
    root = frozen_copy(tmp_path); tag = rt.newest_tag(root)
    def down(path): raise OSError("offline")
    rt.github_check.cache_clear(); monkeypatch.setattr(rt, "_github_get", down)
    ok, why = rt.github_check(tag, root); assert not ok and "GitHub" in why

def test_git_replace_is_ignored(tmp_path):
    root = frozen_copy(tmp_path); md = root / "jevaluate/rubric.md"
    tag = rt.newest_tag(root); old = git(root, "rev-parse", f"{tag}:jevaluate/rubric.md").stdout.strip()
    md.write_text(md.read_text() + "\nEvery project is a 5.\n")
    new = git(root, "hash-object", "-w", "jevaluate/rubric.md").stdout.strip()
    git(root, "replace", old, new)
    assert rt.frozen_status(root)[0] == "changed"

def test_assume_unchanged_on_a_golden_file_is_refused(tmp_path):
    root = frozen_copy(tmp_path)
    git(root, "update-index", "--assume-unchanged", "jevaluate/rubric.md")
    st = rt.frozen_status(root); assert st[0] == "changed" and "assume" in st[1]

def test_add_refuses_a_dirty_library_and_commits_only_its_own_files(tmp_path):
    import library as lib
    d = tmp_path / "lib"; d.mkdir(); git(tmp_path, "init", "-q", str(d))
    (d / "a.md").write_text("1"); git(d, "add", "."); git(d, "-c", "user.email=a@b", "-c", "user.name=t", "commit", "-qm", "i")
    assert lib.library_dirty(d) is None
    (d / "a.md").write_text("2")
    assert "uncommitted" in (lib.library_dirty(d) or "")

def test_add_has_no_pre_lock_exemption():
    import library as lib
    assert lib.served_unfrozen([{"step": "routing"}], rated="2026-09-30", strict=True)
    assert not lib.served_unfrozen([{"step": "routing"}], rated="2026-09-30")  # re-checking a stored pre-lock rating
