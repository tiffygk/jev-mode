import json, os, subprocess, sys
import pytest

CODE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(CODE, "scripts")
REAL = os.path.expanduser(os.environ.get("JEV_SOURCES_DATA") or "~/.claude/jev-sources-data")


@pytest.fixture
def usage(monkeypatch, tmp_path):
    monkeypatch.delenv("JEV_LOG", raising=False)
    monkeypatch.setenv("JEV_SOURCES_DATA", str(tmp_path))
    monkeypatch.syspath_prepend(SCRIPTS)
    for name in ("usage_log", "paths"):
        sys.modules.pop(name, None)
    import usage_log
    yield usage_log, tmp_path
    for name in ("usage_log", "paths"):
        sys.modules.pop(name, None)


def read_lines(path):
    return [json.loads(l) for l in open(path, encoding="utf-8")]


def test_write_appends_one_line_with_timestamp(usage):
    usage_log, data = usage
    usage_log.write("route", question="q")
    usage_log.write("route", question="r")
    rows = read_lines(os.path.join(str(data), "logs", "route.jsonl"))
    assert [r["question"] for r in rows] == ["q", "r"]
    assert rows[0]["ts"].endswith("Z") and "T" in rows[0]["ts"]


def test_jev_log_off_writes_nothing(usage, monkeypatch):
    usage_log, data = usage
    monkeypatch.setenv("JEV_LOG", "off")
    usage_log.write("route", question="q")
    assert not os.path.exists(os.path.join(str(data), "logs"))


def test_unwritable_data_dir_does_not_raise(usage, monkeypatch, tmp_path):
    usage_log, _ = usage
    blocker = tmp_path / "not-a-folder"
    blocker.write_text("x")
    monkeypatch.setattr(usage_log, "DATA", str(blocker))
    usage_log.write("route", question="q")  # must not raise


@pytest.fixture
def library(tmp_path):
    """A copy of the index plus links to the real page folders; nothing is written to the real library."""
    if not os.path.exists(os.path.join(REAL, "sections.jsonl")):
        pytest.skip("no library on this machine")
    lib = tmp_path / "lib"
    lib.mkdir()
    (lib / "sections.jsonl").write_text(open(os.path.join(REAL, "sections.jsonl"), encoding="utf-8").read(), encoding="utf-8")
    for name in ("docs", "cookbooks", "patterns", "blog"):
        if os.path.isdir(os.path.join(REAL, name)):
            os.symlink(os.path.join(REAL, name), lib / name)
    return lib


def env_for(lib):
    return {**{k: v for k, v in os.environ.items() if k != "JEV_LOG"}, "JEV_SOURCES_DATA": str(lib), "JEV_SEMANTIC": "off"}


def test_route_logs_sections_and_how_each_was_found(library):
    q = "can I put 30 passages in one call"
    subprocess.run([sys.executable, os.path.join(SCRIPTS, "route.py"), q], capture_output=True, text=True,
                   env=env_for(library), check=True)
    rows = read_lines(os.path.join(str(library), "logs", "route.jsonl"))
    assert len(rows) == 1
    rec = rows[0]
    assert rec["question"] == q and rec["sections"]
    assert all(s["by"] in ("keyword", "meaning") for s in rec["sections"])
    assert rec["sections"][0]["by"] == "keyword"


def test_read_logs_section_id_and_extract(library):
    out = subprocess.run([sys.executable, os.path.join(SCRIPTS, "route.py"), "--json", "can I put 30 passages in one call"],
                         capture_output=True, text=True, env=env_for(library), check=True).stdout
    sid = json.loads(out)["sections"][0]["id"]
    subprocess.run([sys.executable, os.path.join(SCRIPTS, "read.py"), sid], capture_output=True, text=True,
                   env=env_for(library), check=True)
    subprocess.run([sys.executable, os.path.join(SCRIPTS, "read.py"), sid, "--extract", "passage"], capture_output=True,
                   text=True, env=env_for(library), check=True)
    rows = read_lines(os.path.join(str(library), "logs", "read.jsonl"))
    assert [(r["id"], r["extract"]) for r in rows] == [(sid, False), (sid, True)]
    assert all(isinstance(r["tokens"], int) for r in rows)


@pytest.mark.parametrize("script", ["route.py", "jev.py"])
def test_route_log_includes_the_read_full_definitions(library, script):
    subprocess.run([sys.executable, os.path.join(SCRIPTS, script), "how do I write a Noul question?"],
                   capture_output=True, text=True, env=env_for(library), check=True)
    rec = read_lines(os.path.join(str(library), "logs", "route.jsonl"))[0]
    assert rec["definitions"] and all(d["depth"] == "READ FULL" for d in rec["definitions"])
