import datetime, importlib, os, sys
import pytest
CODE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(CODE, "scripts"))
UTC = datetime.timezone.utc

@pytest.fixture
def pg(tmp_path, monkeypatch):
    monkeypatch.setenv("JEV_SOURCES_DATA", str(tmp_path))
    import paths, pages
    importlib.reload(paths); importlib.reload(pages)
    yield pages
    monkeypatch.undo()  # put the env back, then reload so no other test sees this tmp_path
    importlib.reload(paths); importlib.reload(pages)

SITEMAP = ("<urlset><url><loc>https://docs.typesafe.ai/models</loc><lastmod>2026-10-14T21:07:12.427Z</lastmod></url>"
           "<url><loc>https://docs.typesafe.ai/images</loc></url><url><loc>https://docs.typesafe.ai/</loc></url></urlset>")

def test_parse_sitemap_dates_and_missing_lastmod(pg):
    s = pg.parse_sitemap(SITEMAP)
    assert s["models"] == datetime.datetime(2026, 10, 14, 21, 7, 12, tzinfo=UTC)
    assert s["images"] is None and "" not in s

def test_live_pages_unions_both_lists_and_survives_one_failure(pg):
    def f(url, tries=3):
        if url.endswith("sitemap.xml"): raise OSError("down")
        return "[a](https://docs.typesafe.ai/primitives/noul.md)"
    found, read = pg.live_pages(f)
    assert "primitives/noul" in found and read == {"llms"}
    def none(url, tries=3): raise OSError("down")
    with pytest.raises(RuntimeError): pg.live_pages(none)

def test_a_sitemap_with_no_url_entries_counts_as_unread(pg):
    llms = "[a](https://docs.typesafe.ai/primitives/noul.md)"
    for body in ("<sitemapindex><sitemap><loc>https://docs.typesafe.ai/sitemap-0.xml</loc></sitemap></sitemapindex>",
                 "<html><body>Please try again later</body></html>"):
        def f(url, tries=3, body=body):
            return body if url.endswith("sitemap.xml") else llms
        found, read = pg.live_pages(f)
        assert read == {"llms"} and "primitives/noul" in found

def test_only_an_empty_sitemap_and_no_llms_raises_with_the_sitemap_named(pg):
    def f(url, tries=3):
        if url.endswith("sitemap.xml"): return "<html></html>"
        raise OSError("down")
    with pytest.raises(RuntimeError, match="sitemap"):
        pg.live_pages(f)

def test_live_pages_default_fetch_is_patchable(pg, monkeypatch):
    monkeypatch.setattr(pg, "get", lambda url, tries=3: SITEMAP if url.endswith("sitemap.xml") else "")
    found, read = pg.live_pages()
    assert "models" in found and read == {"sitemap", "llms"}

def test_header_round_trip_and_date_only(pg, tmp_path):
    t = datetime.datetime(2026, 10, 14, 15, 0, 0, tzinfo=UTC)
    p = pg.write_page("models", "# Models\n", t)
    assert pg.saved_at(p) == t and pg.body(p) == "# Models\n"
    old = tmp_path / "docs" / "api.md"
    old.write_text("<!-- saved 2026-10-13 from https://docs.typesafe.ai/api.md -->\n\n# API\n")
    assert pg.saved_at(str(old)) == datetime.datetime(2026, 10, 13, tzinfo=UTC)

def test_slugs_round_trip(pg):
    for s in ["models", "sdk/python/usage/basic", "cookbooks/rerank_typesafe", "patterns/fan-out"]:
        assert pg.slug_of_path(os.path.relpath(pg.dest(s), pg.DATA)) == s
    assert pg.slug_of_url("https://docs.typesafe.ai/images.md") == pg.slug_of_url("https://docs.typesafe.ai/images/") == "images"

def test_library_skips_duplicates(pg, tmp_path):
    (tmp_path / "docs").mkdir(exist_ok=True)
    (tmp_path / "docs" / "cookbooks__x.md").write_text("x")
    (tmp_path / "docs" / "models.md").write_text("x")
    assert set(pg.library()) == {"models"}

def test_archive_moves_by_reason(pg):
    p = pg.write_page("models", "a", datetime.datetime(2026, 10, 14, tzinfo=UTC))
    a = pg.archive(p, "changed", datetime.datetime(2026, 10, 14, tzinfo=UTC))
    assert not os.path.exists(p) and a.endswith(os.path.join("archive", "2026-10-14T000000Z", "changed", "docs", "models.md"))



@pytest.mark.parametrize("bad", ["patterns/../../CLAUDE", "cookbooks/../x", "../etc", "docs/a/../../b", "a//b", ".hidden", "a b"])
def test_unsafe_page_names_are_dropped_from_both_lists(pg, bad):
    xml = "<urlset><url><loc>https://docs.typesafe.ai/%s</loc></url><url><loc>https://docs.typesafe.ai/models</loc></url></urlset>" % bad
    assert list(pg.parse_sitemap(xml)) == ["models"]
    assert pg.parse_llms("[x](https://docs.typesafe.ai/%s.md) [m](https://docs.typesafe.ai/models.md)" % bad) == {"models"}


def test_real_page_names_are_kept(pg):
    for ok in ("models", "primitives/box", "sdk/javascript/api/classes/APIError", "cookbooks/rerank_typesafe", "patterns/fan-out", "model-jaggedness/jev-1.13"):
        assert pg.parse_llms("[x](https://docs.typesafe.ai/%s.md)" % ok) == {ok}


def test_dest_refuses_a_path_outside_the_library(pg):
    with pytest.raises(ValueError):
        pg.dest("patterns/../../CLAUDE")


def test_get_refuses_a_page_over_the_size_cap(pg, monkeypatch):
    class R:
        def geturl(self): return "https://docs.typesafe.ai/models.md"
        def read(self, n=-1): return b"x" * (pg.MAX_BYTES + 10 if n == -1 else min(n, pg.MAX_BYTES + 10))
    monkeypatch.setattr(pg.urllib.request, "urlopen", lambda *a, **k: R())
    with pytest.raises(ValueError):
        pg.get("https://docs.typesafe.ai/models.md")
