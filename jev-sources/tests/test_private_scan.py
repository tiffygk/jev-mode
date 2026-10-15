"""build_index and refresh.sh scan <data>/blog/ with the local privacy checker. Everything here is invented:
the checker is the repo copy, the config and source sit in tmp_path, and env paths keep the real ones out."""
import importlib, json, os, shutil, subprocess, sys
import pytest

CODE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(CODE)
CHECKER = os.path.join(REPO, "scripts", "private_text_check.py")
sys.path.insert(0, os.path.join(CODE, "scripts"))

H = "alex" + "q"  # invented handle, assembled so a scan of this file finds no handle line
RUN = "knab revir teiuq eht raen god yzal eht revo spmuj xof nworb kciuq eht"[::-1]
SOURCE = f"**21:04:34 · {H}:** {RUN}\n"


@pytest.fixture
def lib(tmp_path, monkeypatch):
    data = tmp_path / "data"
    (data / "docs").mkdir(parents=True)
    (data / "blog").mkdir()
    (data / "docs" / "page.md").write_text("# Page\nbody\n")
    (data / "blog" / "clean.txt").write_text("The docs say the limit is 64k.\n")
    (data / "blog" / "dirty.txt").write_text(f"fine line\nthanks {H}\n")
    src = tmp_path / "source.md"
    src.write_text(SOURCE)
    cfg = tmp_path / "private.json"
    cfg.write_text(json.dumps({"sources": [str(src)], "names": ["Pat" + " Example"]}))
    monkeypatch.setenv("JEV_SOURCES_DATA", str(data))
    monkeypatch.setenv("JEV_PRIVATE_CONFIG", str(cfg))
    monkeypatch.setenv("JEV_PRIVATE_CHECKER", CHECKER)
    import paths
    importlib.reload(paths)
    import build_index
    importlib.reload(build_index)
    monkeypatch.setattr(build_index, "embed", lambda rows: None)
    yield build_index, data, tmp_path
    monkeypatch.undo()
    importlib.reload(paths)


def test_blocked_blog_files_names_only_the_file_with_a_hit(lib):
    bi, data, _ = lib
    assert bi.blocked_blog_files() == ["blog/dirty.txt"]


def test_a_blocked_blog_file_is_left_out_of_the_index_and_a_clean_one_is_in(lib):
    bi, data, _ = lib
    bi.main()
    paths = {json.loads(l)["path"] for l in open(data / "sections.jsonl")}
    assert "blog/clean.txt" in paths and "blog/dirty.txt" not in paths


def test_notice_names_the_file_and_never_the_private_text(lib, capsys):
    bi, data, _ = lib
    bi.main()
    out = capsys.readouterr().out
    assert "blog/dirty.txt" in out and "not indexed" in out
    assert H not in out and "quick" not in out
    assert "blog/clean.txt" not in out


def test_a_config_without_its_checker_blocks_every_blog_file(lib, monkeypatch):
    bi, data, tmp = lib
    monkeypatch.setenv("JEV_PRIVATE_CHECKER", str(tmp / "absent.py"))
    assert bi.blocked_blog_files() == ["blog/clean.txt", "blog/dirty.txt"]  # fail closed: the owner's config says check


def test_no_config_means_no_scan(lib, monkeypatch):
    bi, data, tmp = lib
    monkeypatch.setenv("JEV_PRIVATE_CONFIG", str(tmp / "absent.json"))
    assert bi.blocked_blog_files() == []


def test_no_blog_folder_is_fine(lib):
    bi, data, _ = lib
    shutil.rmtree(str(data / "blog"))
    assert bi.blocked_blog_files() == []


def run_refresh(tmp_path, extra_env):
    bin_ = tmp_path / "bin"
    bin_.mkdir(exist_ok=True)
    py = bin_ / "python3"  # runs the real checker and nothing else: build and route scripts are skipped
    py.write_text('#!/bin/bash\ncase "$1" in *private_text_check.py) exec %s "$@";; esac\nexit 0\n' % sys.executable)
    py.chmod(0o755)
    env = dict(os.environ, PATH="%s:%s" % (bin_, os.environ["PATH"]), JEV_SEMANTIC="off", **extra_env)
    env.pop("JEV_VAULT", None)
    return subprocess.run(["bash", os.path.join(CODE, "refresh.sh")], capture_output=True, text=True, env=env)


def test_refresh_reports_a_blog_hit_and_keeps_going(lib):
    _, data, tmp = lib
    r = run_refresh(tmp, {"JEV_SOURCES_DATA": str(data)})
    assert r.returncode == 0, r.stderr
    assert "dirty.txt:2" in r.stdout + r.stderr
    assert H not in r.stdout + r.stderr


def test_refresh_without_config_does_not_scan(lib):
    _, data, tmp = lib
    r = run_refresh(tmp, {"JEV_SOURCES_DATA": str(data), "JEV_PRIVATE_CONFIG": str(tmp / "absent.json")})
    assert r.returncode == 0
    assert "dirty.txt" not in r.stdout + r.stderr


def test_a_crashing_checker_blocks_every_blog_file(lib, monkeypatch, capsys):
    bi, data, tmp = lib
    bad = tmp / "broken.json"
    bad.write_text("{not json")
    monkeypatch.setenv("JEV_PRIVATE_CONFIG", str(bad))
    assert bi.blocked_blog_files() == ["blog/clean.txt", "blog/dirty.txt"]
    bi.main()
    out = capsys.readouterr().out
    assert "privacy check failed" in out


def test_refresh_says_the_check_failed_when_the_checker_crashes(lib):
    _, data, tmp = lib
    bad = tmp / "broken.json"
    bad.write_text("{not json")
    r = run_refresh(tmp, {"JEV_SOURCES_DATA": str(data), "JEV_PRIVATE_CONFIG": str(bad)})
    assert r.returncode == 0
    assert "privacy check failed" in r.stdout + r.stderr
    assert "JSONDecodeError" in r.stderr or "Expecting" in r.stderr
