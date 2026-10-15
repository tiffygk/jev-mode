import datetime, importlib, os, subprocess, sys
import pytest
CODE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(CODE, "scripts"))
T = datetime.datetime(2026, 10, 14, 21, 7, tzinfo=datetime.timezone.utc)


@pytest.fixture
def lib(tmp_path, monkeypatch):
    monkeypatch.setenv("JEV_SOURCES_DATA", str(tmp_path))
    import paths, pages, blog, sources
    for m in (paths, pages, blog, sources):
        importlib.reload(m)
    pages.write_page("models", "# Models\n\n## Intro\n\ntext\n", T)
    pages.write_page("cookbooks/rerank", "# Rerank\n\n## Intro\n\ntext\n", T)
    blog.save("a-post", "# A post\n\nInvented body.", T)
    yield tmp_path, sources
    monkeypatch.undo()
    importlib.reload(paths); importlib.reload(pages); importlib.reload(blog); importlib.reload(sources)


def test_sources_lists_every_page_with_address_and_time(lib):
    tmp_path, sources = lib
    path = sources.write()
    assert path == str(tmp_path / "SOURCES.md")
    rows = [l for l in open(path).read().splitlines() if l.startswith("| ") and "---" not in l][1:]
    assert len(rows) == 3
    text = "\n".join(rows)
    assert "| docs/models.md | https://docs.typesafe.ai/models | 2026-10-14 21:07 | yes |" in text
    assert "| cookbooks/rerank.md | https://docs.typesafe.ai/cookbooks/rerank | 2026-10-14 21:07 | yes |" in text
    assert "| blog/a-post.txt | https://typesafe.ai/blog/a-post | 2026-10-14 21:07 | yes |" in text


def test_blocked_blog_post_marked_not_indexed(lib):
    tmp_path, sources = lib
    open(tmp_path / "blog" / "x.txt", "w").write("<!-- saved 2026-10-14T21:07:00Z from https://typesafe.ai/blog/x -->\nSECRET-STAFF-TEXT\n")
    out = open(sources.write(blocked=["blog/x.txt"])).read()
    row = next(l for l in out.splitlines() if "not indexed" in l)
    assert row.startswith("| blog/(withheld) | withheld |") and "x.txt" not in out and "blog/x" not in out
    assert "SECRET-STAFF-TEXT" not in out


def test_build_index_writes_sources(lib):
    tmp_path, _ = lib
    env = dict(os.environ, JEV_SOURCES_DATA=str(tmp_path), JEV_SEMANTIC="off", JEV_LOG="off")
    subprocess.run([sys.executable, os.path.join(CODE, "scripts", "build_index.py")], check=True, capture_output=True, env=env)
    assert (tmp_path / "sections.jsonl").exists() and (tmp_path / "SOURCES.md").exists()
    assert "https://typesafe.ai/blog/a-post" in (tmp_path / "SOURCES.md").read_text()


def test_a_build_after_pages_was_loaded_for_another_folder_writes_only_its_own_sources(tmp_path, monkeypatch):
    """The gate's ordering: an earlier test left `pages` cached for the real data folder; a later temp-library build
    must still write SOURCES.md beside its own index, never into the folder the cached module points at."""
    sentinel, mine = tmp_path / "sentinel", tmp_path / "mine"
    (sentinel / "docs").mkdir(parents=True)
    (sentinel / "docs" / "stale.md").write_text("# Stale\n\ntext\n")
    (mine / "docs").mkdir(parents=True)
    (mine / "docs" / "fresh.md").write_text("# Fresh\n\nsome text here\n")
    monkeypatch.setenv("JEV_SOURCES_DATA", str(sentinel))
    monkeypatch.setenv("JEV_SEMANTIC", "off")
    monkeypatch.setenv("JEV_PRIVATE_CONFIG", str(tmp_path / "absent.json"))
    monkeypatch.syspath_prepend(os.path.join(CODE, "scripts"))
    for n in ("paths", "pages", "build_index", "sources", "blog"):
        sys.modules.pop(n, None)
    import pages  # cached for the sentinel folder, as a fixture teardown leaves it
    monkeypatch.setenv("JEV_SOURCES_DATA", str(mine))
    for n in ("paths", "build_index", "sources"):
        sys.modules.pop(n, None)
    import build_index
    monkeypatch.setattr(build_index, "embed", lambda rows: None)
    build_index.main()
    assert not (sentinel / "SOURCES.md").exists()
    text = (mine / "SOURCES.md").read_text()
    assert "fresh.md" in text and "stale.md" not in text


def test_the_test_suite_drops_every_module_that_caches_the_data_folder():
    src = open(os.path.join(CODE, "tests", "conftest.py")).read()
    for name in ("pages", "check_new", "fetch", "blog", "sources"):
        assert f'"{name}"' in src
