"""Private Jevaluate (2026-10-06): a private rating lives only in a private library, export refuses both, and a local
folder can be gathered like a GitHub repo."""
import json, pathlib, subprocess, sys
from test_library import make_rating, run
HERE = pathlib.Path(__file__).parent


def private(r):
    r = pathlib.Path(r); r.write_text(r.read_text().replace("rater: claude-sonnet-5-5", "rater: claude-sonnet-5-5\nvisibility: private")); return r


def test_private_rating_refused_by_public_library(tmp_path):
    lib = tmp_path / "lib"
    r = private(make_rating(tmp_path / "r.md", "Graph", "acme", "local:acme-graph", "2026-10-06"))
    p = run(lib, "add", str(r))
    assert p.returncode != 0 and "private library" in (p.stdout + p.stderr)
    assert not list(lib.glob("projects/*/*.md"))


def test_private_library_refuses_public_rating(tmp_path):
    lib = tmp_path / "priv"; assert run(lib, "init-private", str(lib)).returncode == 0
    r = make_rating(tmp_path / "r.md", "Proj", "o", "https://github.com/o/proj", "2026-10-06")
    p = run(lib, "add", str(r))
    assert p.returncode != 0 and "visibility: private" in (p.stdout + p.stderr)


def test_private_end_to_end(tmp_path):
    lib = tmp_path / "priv"
    p = run(lib, "init-private", str(lib)); assert p.returncode == 0, p.stderr
    assert (lib / "PRIVATE").exists()
    r = private(make_rating(tmp_path / "r.md", "Graph", "acme", "local:acme-graph", "2026-10-06"))
    p = run(lib, "add", str(r)); assert p.returncode == 0, p.stdout + p.stderr
    assert (lib / "projects" / "local__acme-graph" / "2026-10-06.md").exists()
    out = tmp_path / "out"; p = run(lib, "export", str(out))
    assert p.returncode != 0 and not out.exists()


def test_local_folder_manifest_skips_like_github(tmp_path):
    src = tmp_path / "proj"; (src / ".git").mkdir(parents=True); (src / "src").mkdir()
    (src / ".git" / "config").write_text("[core]\n")
    (src / "README.md").write_text("# Graph\nUses Jev to rank retrieval results.\n")
    (src / "src" / "rank.py").write_text("from typesafe import TypeSafe\nclient = TypeSafe()\nans = client.noul('relevant?')\n")
    (src / "logo.png").write_bytes(b"\x89PNG\r\n\x1a\n" + bytes(range(256)) * 10)
    (src / "big.py").write_text("# typesafe\n" + "x = 1\n" * 50_000)
    out = tmp_path / "out"
    p = subprocess.run([sys.executable, str(HERE / "coverage_manifest.py"), "--local", str(src), str(out)], capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    kept = {f.name for f in (out / "files").iterdir()}
    assert "src__rank.py" in kept and "README.md" in kept
    assert not any(n.startswith((".git", "logo", "big")) for n in kept), kept
    meta = json.loads((out / "meta.json").read_text())
    assert meta["repo"] == "local:proj" and meta["commit"].startswith("local-")
