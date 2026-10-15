import importlib, os, sys, pytest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

@pytest.fixture
def blog(tmp_path, monkeypatch):
    monkeypatch.setenv("JEV_SOURCES_DATA", str(tmp_path))
    import paths, pages, blog as b
    for m in (paths, pages, b):
        importlib.reload(m)
    yield b
    monkeypatch.undo()
    importlib.reload(paths); importlib.reload(pages)

SITEMAP = """<urlset><url><loc>https://typesafe.ai/blog</loc></url>
<url><loc>https://typesafe.ai/blog/new-model</loc></url>
<url><loc>https://typesafe.ai/blog/launch-post</loc></url>
<url><loc>https://typesafe.ai/team</loc></url></urlset>"""

POST = """<html><head><title>x</title><script>var a=1;</script></head><body>
<nav><a>Docs</a><a>Sign In</a></nav>
<main><article><h1>A new model</h1><p>First paragraph of the post.</p>
<h2>Speed</h2><p>It is 40x faster, we think.</p><ul><li>one point</li></ul></article></main>
<footer><p>Copyright TypeSafe</p></footer></body></html>"""

# the shape the live site serves: no nav/article tags, menu and footer text in plain <p> elements
SITE_POST = """<html><body><div><a href="/"><p>Menu item</p></a><a href="/docs"><p>Docs link</p></a></div>
<div><p>Back</p><p>Company News</p><h1>A new model</h1>
<p>Oct 14, 2026</p><p>Oct 14, 2026</p><p>Oct 14, 2026</p>
<p>Body paragraph one.</p><h2>Speed</h2><p>Body paragraph two.</p><p>***</p></div>
<div><p>∵ ⩆</p><p>TypeSafe AI © 2026</p><p>Contact</p><p>Terms of Use</p></div></body></html>"""

def test_list_posts_reads_the_site_sitemap(blog):
    assert blog.list_posts(lambda u: SITEMAP) == ["launch-post", "new-model"]

def test_post_text_keeps_title_headings_paragraphs_and_lists(blog):
    t = blog.post_text(POST)
    assert t.splitlines()[0] == "# A new model"
    assert "## Speed" in t and "It is 40x faster, we think." in t and "- one point" in t

def test_post_text_drops_nav_script_and_footer(blog):
    t = blog.post_text(POST)
    assert "Sign In" not in t and "var a" not in t and "Copyright" not in t

def test_post_text_on_the_live_layout_starts_at_the_title_and_stops_before_the_footer(blog):
    t = blog.post_text(SITE_POST)
    assert t.splitlines()[0] == "# A new model"
    assert "Menu item" not in t and "Docs link" not in t and "Company News" not in t
    assert "Body paragraph one." in t and "Body paragraph two." in t
    assert "Terms of Use" not in t and "©" not in t and "Contact" not in t
    assert t.count("Oct 14, 2026") == 1  # the page repeats the date once per screen size

def test_post_text_without_h1_still_returns_paragraphs(blog):
    t = blog.post_text("<html><body><div><p>Only a paragraph here.</p></div></body></html>")
    assert "Only a paragraph here." in t

def test_inline_link_text_stays_in_its_sentence_and_menu_links_still_go(blog):
    t = blog.post_text("<html><body><a><p>Menu</p></a><h1>T</h1><p>See <a href='x'>the docs page</a> for more.</p>"
                       "<ul><li><a href='y'>Link only item</a></li></ul><p>Last.</p></body></html>")
    assert "See the docs page for more." in t and "- Link only item" in t and "Menu" not in t and "Last." in t

def test_a_line_repeated_later_in_the_body_survives(blog):
    t = blog.post_text("<html><body><h1>T</h1><p>Date</p><p>Date</p><p>Intro one.</p><p>Intro two.</p><p>Intro three.</p>"
                       "<p>Intro four.</p><p>Intro five.</p><p>Again and again.</p><p>Again and again.</p></body></html>")
    assert t.count("Date") == 1 and t.count("Again and again.") == 2

def test_a_write_error_names_that_post_and_the_loop_carries_on(blog, monkeypatch):
    real = blog.save
    def flaky(slug, text, now=None):
        if slug == "bad":
            raise OSError("disk full")
        return real(slug, text, now)
    monkeypatch.setattr(blog, "save", flaky)
    saved, failed = blog.fetch_posts(["bad", "new-model"], lambda u: POST)
    assert saved == ["new-model"] and failed[0][0] == "bad" and "disk full" in failed[0][1]

def test_save_writes_the_saved_header_and_saved_at_reads_it(blog):
    import datetime
    now = datetime.datetime(2026, 10, 14, 21, 0, tzinfo=datetime.timezone.utc)
    p = blog.save("new-model", "# A new model\n\nText.", now)
    assert p.endswith(os.path.join("blog", "new-model.txt"))
    import pages
    assert pages.saved_at(p) == now

def test_fetch_posts_skips_404_and_empty_and_keeps_old_copy(blog):
    import pages
    old = blog.save("gone-post", "# Old\n\nKept.")
    def fake(u):
        if u.endswith("gone-post"):
            raise pages.Gone(u)
        if u.endswith("empty-post"):
            return "<html><body><nav>menu</nav></body></html>"
        return POST
    saved, failed = blog.fetch_posts(["gone-post", "empty-post", "new-model"], fake)
    assert saved == ["new-model"] and sorted(failed) == [("empty-post", "empty page"), ("gone-post", "gone")]
    assert open(old).read().rstrip().endswith("Kept.")
    assert not os.path.exists(blog.dest("empty-post"))


def _fetcher(pages, post_map, site_down=False):
    def fake(url, tries=3):
        if url.startswith("https://typesafe.ai/"):
            if url.endswith("sitemap.xml"):
                if site_down:
                    raise OSError("down")
                return "<urlset>" + "".join(f"<url><loc>https://typesafe.ai/blog/{s}</loc></url>" for s in post_map) + "</urlset>"
            v = post_map[url.rsplit("/", 1)[1]]
            if v == 404:
                raise pages.Gone(url)
            return v
        if url.endswith("llms.txt"):
            return "[a](https://docs.typesafe.ai/models.md)"
        if url.endswith("sitemap.xml"):
            raise OSError("down")
        return "# Models"
    return fake


@pytest.fixture
def fetch_mod(blog):
    import fetch, pages
    importlib.reload(fetch)
    return fetch, pages


def test_refresh_fetch_saves_every_post_and_names_a_gone_one(fetch_mod, capsys):
    fetch, pages = fetch_mod
    code = fetch.main(_fetcher(pages, {"new-model": POST, "gone-post": 404}))
    out = capsys.readouterr().out
    assert os.path.exists(os.path.join(pages.DATA, "blog", "new-model.txt"))
    assert "gone: blog/gone-post" in out and code == 1
    assert not any("fetch failed" in l for l in out.splitlines())


def test_refresh_fetch_survives_an_unreadable_site_sitemap(fetch_mod, capsys):
    fetch, pages = fetch_mod
    code = fetch.main(_fetcher(pages, {}, site_down=True))
    out = capsys.readouterr().out
    assert os.path.exists(os.path.join(pages.DATA, "docs", "models.md"))
    assert out.count("blog list") == 1 and code == 0


def test_save_failure_keeps_the_old_copy(blog, monkeypatch):
    old = blog.save("kept-post", "# Old\n\nKept.")
    real_replace = os.replace
    def boom(a, b):
        raise OSError("disk full")
    monkeypatch.setattr(os, "replace", boom)
    with pytest.raises(OSError):
        blog.save("kept-post", "# New\n\nNew text.")
    monkeypatch.setattr(os, "replace", real_replace)
    assert open(old).read().rstrip().endswith("Kept.")
    assert [f for f in os.listdir(os.path.dirname(old)) if f.endswith(".tmp")] == []


def test_video_post_with_only_title_and_date_is_an_empty_page(blog):
    page = ("<html><body><main><h1>Models: too clever to trust, too plain to be useful, a talk</h1><p>Jun 19, 2026</p><p>Jun 19, 2026</p>"
            "<iframe src='https://www.youtube.com/embed/x'></iframe></main></body></html>")
    saved, failed = blog.fetch_posts(["talk"], lambda u: page)
    assert saved == [] and failed == [("talk", "empty page")]
    assert not os.path.exists(blog.dest("talk"))


def test_refresh_fetch_reports_an_empty_page_post_as_skipped_and_exits_clean(fetch_mod, capsys):
    fetch, pages = fetch_mod
    code = fetch.main(_fetcher(pages, {"video-post": "<html><body><nav>menu</nav></body></html>", "new-model": POST}))
    out = capsys.readouterr().out
    assert code == 0 and "skipped: blog/video-post (empty page)" in out and "fetch failed" not in out
    assert "gone: blog/video-post" not in out
    assert not os.path.exists(os.path.join(pages.DATA, "blog", "video-post.txt"))
