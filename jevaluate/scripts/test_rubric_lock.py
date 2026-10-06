"""The rubric lock: ratings and eval results of record need the frozen rubric (2026-10-05)."""
import json, os, pathlib, shutil, subprocess, sys
import pytest
HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
import rubric_text as rt

def git(root, *a): return subprocess.run(["git", "-C", str(root), *a], capture_output=True, text=True, check=True)

def frozen_copy(tmp_path):
    """A git checkout holding a copy of jevaluate/ and shared/, with this rubric's freeze tag on its first commit."""
    root = tmp_path / "repo"; repo = HERE.parent.parent
    shutil.copytree(repo / "jevaluate", root / "jevaluate", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(repo / "shared", root / "shared")
    git(tmp_path, "init", "-q", str(root)); git(root, "add", "."); git(root, "-c", "user.email=a@b", "-c", "user.name=t", "commit", "-qm", "i")
    git(root, "tag", f"rubric-{rt.version()}-frozen")
    return root

def test_status_frozen_changed_unfrozen(tmp_path):
    root = frozen_copy(tmp_path); md = root / "jevaluate/rubric.md"
    assert rt.frozen_status(root)[0] == "frozen"
    md.write_text(md.read_text() + "\nAn extra rule.\n")
    assert rt.frozen_status(root)[0] == "changed"
    md.write_text(md.read_text().replace(f"({rt.version()})", "(2099-01-01)", 1))
    assert rt.frozen_status(root)[0] == "changed"
    git(root, "tag", "-d", f"rubric-{rt.version()}-frozen")
    assert rt.frozen_status(root)[0] == "unfrozen"

def test_status_outside_git(tmp_path):
    md = tmp_path / "jevaluate/rubric.md"; md.parent.mkdir(); md.write_text((HERE.parent / "rubric.md").read_text())
    assert rt.frozen_status(tmp_path)[0] == "no-git"

def run_step(root, lib, rating, escape=False):
    env = {k: v for k, v in os.environ.items() if k != "JEVALUATE_TEST_UNFROZEN"}
    env["JEVALUATE_LIBRARY"] = str(lib)
    if escape: env["JEVALUATE_TEST_UNFROZEN"] = "1"
    return subprocess.run([sys.executable, str(root / "jevaluate/scripts/step.py"), "next", str(rating)], capture_output=True, text=True, env=env)

def rating_in(tmp_path):
    d = tmp_path / "r"; d.mkdir(); (d / "manifest.md").write_text("# Coverage manifest: o/t @ abc\n\nTree: 1 files; 1 kept (4000 chars, ~1000 tokens).\n")
    r = d / "rating.md"; r.write_text("---\nproject: T\nurl: https://github.com/o/t\nowner: o\nrated: 2026-09-29\ncommit: abc1234\n---\n"); return r

def test_step_refuses_an_edited_rubric(tmp_path):
    root = frozen_copy(tmp_path); r = rating_in(tmp_path); lib = tmp_path / "lib"
    md = root / "jevaluate/rubric.md"; md.write_text(md.read_text() + "\nAn extra rule.\n")
    out = run_step(root, lib, r)
    assert out.returncode != 0 and "frozen" in out.stderr and not pathlib.Path(str(r) + ".steps.json").exists()

def test_step_logs_the_rubric_status(tmp_path):
    root = frozen_copy(tmp_path); r = rating_in(tmp_path)
    out = run_step(root, tmp_path / "lib", r)
    assert out.returncode == 0, out.stderr
    assert json.loads(pathlib.Path(str(r) + ".steps.json").read_text())[0]["rubric"] == "frozen"

def test_test_escape_works_only_on_a_temp_library(tmp_path, monkeypatch):
    root = frozen_copy(tmp_path); md = root / "jevaluate/rubric.md"; md.write_text(md.read_text() + "\nAn extra rule.\n")
    assert run_step(root, tmp_path / "lib", rating_in(tmp_path), escape=True).returncode == 0
    import importlib.util
    monkeypatch.setattr(sys, "path", list(sys.path))  # library.py puts its own folder on sys.path; keep that out of later tests
    spec = importlib.util.spec_from_file_location("libcopy", root / "jevaluate/scripts/library.py")
    monkeypatch.setenv("JEVALUATE_TEST_UNFROZEN", "1"); monkeypatch.setenv("JEVALUATE_LIBRARY", str(pathlib.Path.home() / ".claude/jevaluate-library"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    monkeypatch.setattr(m.rubric_text, "frozen_status", lambda root=None: ("changed", "edited"))
    assert m.real_library() and m.rubric_gate() is not None
    monkeypatch.setattr(m, "LIB", tmp_path / "lib")
    assert not m.real_library() and m.rubric_gate() is None

def test_check_refuses_a_rating_served_from_an_unfrozen_rubric():
    import library as lib
    log = [{"step": "routing", "time": "t", "routing": "x", "rubric": "changed"}]
    assert lib.served_unfrozen(log, rated="2026-10-06")


def test_every_golden_file_is_frozen(tmp_path):
    root = frozen_copy(tmp_path)
    for rel in ("shared/jev-rules.md", "jevaluate/fix-catalog.md", "jevaluate/read.md", "jevaluate/SKILL.md"):
        f = root / rel; old = f.read_text(); f.write_text(old + "\nAn extra rule.\n")
        assert rt.frozen_status(root)[0] == "changed", rel
        f.write_text(old)
    assert rt.frozen_status(root)[0] == "frozen"

def test_rollback_to_an_older_frozen_rubric_is_refused(tmp_path):
    root = frozen_copy(tmp_path); md = root / "jevaluate/rubric.md"
    md.write_text(md.read_text().replace(f"({rt.version()})", "(2099-01-01)", 1))
    git(root, "-c", "user.email=a@b", "-c", "user.name=t", "commit", "-qam", "newer"); git(root, "tag", "rubric-2099-01-01-frozen")
    assert rt.frozen_status(root)[0] == "frozen"
    git(root, "checkout", f"rubric-{rt.version()}-frozen", "--", "jevaluate/rubric.md")
    st = rt.frozen_status(root); assert st[0] == "changed" and "2099-01-01" in st[1]

def test_git_env_cannot_force_no_git(tmp_path, monkeypatch):
    root = frozen_copy(tmp_path); md = root / "jevaluate/rubric.md"; md.write_text(md.read_text() + "\nx\n")
    monkeypatch.setenv("GIT_DIR", "/nonexistent")
    assert rt.frozen_status(root)[0] == "changed"

def test_step_log_records_the_served_content(tmp_path):
    root = frozen_copy(tmp_path); r = rating_in(tmp_path)
    assert run_step(root, tmp_path / "lib", r).returncode == 0
    e = json.loads(pathlib.Path(str(r) + ".steps.json").read_text())[0]
    assert e["golden"] == rt.golden_hash(root) and len(e["golden"]) == 64

def test_log_without_status_is_not_frozen_and_hash_must_match():
    import library as lib
    assert lib.served_unfrozen([{"step": "routing"}], rated="2026-10-06")
    assert not lib.served_unfrozen([{"step": "routing"}], rated="2026-09-30")  # ratings logged before the lock
    good = rt.golden_hash(rt.ROOT, ref=rt.newest_tag(rt.ROOT))
    assert not lib.served_unfrozen([{"step": "routing", "rubric": "frozen", "golden": good}], rated="2026-10-06")
    assert lib.served_unfrozen([{"step": "routing", "rubric": "frozen", "golden": "0" * 64}], rated="2026-10-06")

def test_add_refuses_the_test_escape_and_code_outside_the_golden_checkout(tmp_path, monkeypatch):
    import library as lib
    monkeypatch.setenv("JEVALUATE_TEST_UNFROZEN", "1")
    assert "test escape" in (lib.add_gate() or "")
    monkeypatch.delenv("JEVALUATE_TEST_UNFROZEN")
    lock = tmp_path / "lib"; lock.mkdir(); (lock / ".golden-checkout").write_text("/somewhere/else/jev-mode\n")
    monkeypatch.setattr(lib, "LIB", lock)
    assert "golden checkout" in (lib.add_gate() or "")
    (lock / ".golden-checkout").write_text(str(rt.ROOT) + "\n")
    assert lib.add_gate() is None

def test_a_freeze_tag_outside_this_history_is_ignored(tmp_path):
    root = frozen_copy(tmp_path); md = root / "jevaluate/rubric.md"
    git(root, "checkout", "-q", "-b", "side"); md.write_text(md.read_text().replace(f"({rt.version()})", "(2099-01-01)", 1) + "\nEvery project is a 5.\n")
    git(root, "-c", "user.email=a@b", "-c", "user.name=t", "commit", "-qam", "forged"); git(root, "tag", "rubric-2099-01-01-frozen")
    git(root, "checkout", "-q", "-")  # back to the main line, which never merged the side commit
    assert rt.newest_tag(root) == f"rubric-{rt.version()}-frozen" and rt.frozen_status(root)[0] == "frozen"
