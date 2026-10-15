import datetime, glob, importlib, json, os, subprocess, sys
import pytest
CODE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(CODE, "scripts"))
UTC = datetime.timezone.utc
T13 = datetime.datetime(2026, 10, 13, 12, tzinfo=UTC)
T14 = datetime.datetime(2026, 10, 14, 23, tzinfo=UTC)
RUN14 = "2026-10-14T230000Z"


def _reload():
    import paths, pages, blog, check_new, fetch
    importlib.reload(paths); importlib.reload(pages); importlib.reload(blog); importlib.reload(check_new); importlib.reload(fetch)
    return pages, check_new


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("JEV_SOURCES_DATA", str(tmp_path))
    pg, cn = _reload()
    monkeypatch.setattr(pg, "extras", lambda: [])  # urls.txt lists real pages; the fake site has none
    yield pg, cn
    monkeypatch.undo()  # put the env back, then reload so no other test sees this tmp_path
    _reload()


POST_HTML = "<html><body><h1>A post</h1><p>" + "A sentence of invented body text that is long enough to keep. " * 3 + "</p></body></html>"


def site(pg, texts, sitemap, llms, calls, posts=None, site_down=False):
    """posts: blog slug -> html, 404 or an exception; typesafe.ai's own sitemap lists them. site_down: that sitemap raises."""
    def fetch(url, tries=3):
        calls.append(url)
        if url.startswith("https://typesafe.ai/"):
            if url.endswith("sitemap.xml"):
                if site_down: raise OSError("down")
                return "<urlset>" + "".join(f"<url><loc>https://typesafe.ai/blog/{s}</loc></url>" for s in (posts or {})) + "</urlset>"
            v = (posts or {}).get(url.rsplit("/", 1)[1], 404)
            if v == 404: raise pg.Gone(url)
            if isinstance(v, Exception): raise v
            return v
        if url.endswith("sitemap.xml"):
            if sitemap is None: raise OSError("down")
            return "<urlset>" + "".join(f"<url><loc>https://docs.typesafe.ai/{s}</loc>" + (f"<lastmod>{d}</lastmod>" if d else "") + "</url>" for s, d in sitemap.items()) + "</urlset>"
        if url.endswith("llms.txt"):
            if llms is None: raise OSError("down")
            return " ".join(f"[x](https://docs.typesafe.ai/{s}.md)" for s in llms)
        slug = url[len(pg.BASE):-3]
        v = texts.get(slug, 404)
        if v == 404: raise pg.Gone(url)
        if isinstance(v, tuple): raise pg.Gone(url, v[1])
        if isinstance(v, Exception): raise v
        return v
    return fetch


def archived(tmp_path, run, reason):
    return sorted(glob.glob(str(tmp_path / "archive" / run / reason / "*" / "*.md")))


def test_changed_page_downloaded_archived_and_named(env, tmp_path):
    pg, cn = env
    pg.write_page("models", "old", T13)
    calls = []
    res = cn.run(site(pg, {"models": "new"}, {"models": "2026-10-14T21:00:00Z"}, ["models"], calls), now=T14, rebuild=False)
    assert pg.body(pg.dest("models")).strip() == "new"
    old = archived(tmp_path, RUN14, "changed")
    assert len(old) == 1 and open(old[0]).read().endswith("old")
    assert "models" in res["changed"] and "models" in res["notice"]


def test_refresh_run_logs_one_line_with_counts(env, tmp_path, monkeypatch):
    pg, cn = env
    monkeypatch.delenv("JEV_LOG", raising=False)
    import usage_log
    importlib.reload(usage_log)  # picks up this test's JEV_SOURCES_DATA
    pg.write_page("models", "old", T13)
    cn.run(site(pg, {"models": "new"}, {"models": "2026-10-14T21:00:00Z"}, ["models"], []), now=T14, rebuild=False)
    lines = open(tmp_path / "logs" / "refresh.jsonl", encoding="utf-8").read().splitlines()
    assert len(lines) == 1
    rec = json.loads(lines[0])
    assert rec["changed"] == 1 and rec["ts"].endswith("Z")


def test_redated_same_text_is_quiet(env):
    pg, cn = env
    pg.write_page("models", "same", T13)
    res = cn.run(site(pg, {"models": "same"}, {"models": "2026-10-14T21:00:00Z"}, ["models"], []), now=T14, rebuild=False)
    assert res["redated"] == ["models"] and res["changed"] == [] and res["notice"] == ""
    assert pg.saved_at(pg.dest("models")) == T14


def test_older_date_not_downloaded(env):
    pg, cn = env
    pg.write_page("models", "old", T13)
    calls = []
    cn.run(site(pg, {"models": "new"}, {"models": "2026-10-12T00:00:00Z"}, ["models"], calls), now=T14, rebuild=False)
    assert not any(c.endswith("models.md") for c in calls)


def test_same_day_edit_after_save_is_caught(env):
    pg, cn = env
    pg.write_page("models", "old", datetime.datetime(2026, 10, 14, 10, tzinfo=UTC))
    res = cn.run(site(pg, {"models": "new"}, {"models": "2026-10-14T15:00:00Z"}, ["models"], []), now=T14, rebuild=False)
    assert res["changed"] == ["models"]


def test_edit_just_before_save_is_caught(env):
    pg, cn = env
    pg.write_page("models", "old", datetime.datetime(2026, 10, 14, 22, tzinfo=UTC))
    res = cn.run(site(pg, {"models": "new"}, {"models": "2026-10-14T21:30:00Z"}, ["models"], []), now=T14, rebuild=False)
    assert res["changed"] == ["models"]


def test_date_only_header_counts_as_midnight(env):
    pg, cn = env
    p = pg.dest("models")
    os.makedirs(os.path.dirname(p))
    open(p, "w").write("<!-- saved 2026-10-14 from https://docs.typesafe.ai/models.md -->\n\nold")
    res = cn.run(site(pg, {"models": "new"}, {"models": "2026-10-14T09:00:00Z"}, ["models"], []), now=T14, rebuild=False)
    assert res["changed"] == ["models"]


def test_new_sitemap_page_added(env):
    pg, cn = env
    res = cn.run(site(pg, {"images": "# Images"}, {"images": None}, [], []), now=T14, rebuild=False)
    assert res["added"] == ["images"] and "images" in res["notice"]
    assert os.path.exists(pg.dest("images"))


def test_gone_from_both_lists_and_404_is_archived(env, tmp_path):
    pg, cn = env
    pg.write_page("old-page", "x", T13)
    res = cn.run(site(pg, {}, {"other": None}, ["other"], []), now=T14, rebuild=False)
    assert res["removed"] == ["old-page"] and "old-page" in res["notice"]
    assert not os.path.exists(pg.dest("old-page"))
    assert len(archived(tmp_path, RUN14, "removed")) == 1


def test_in_one_list_never_pruned(env):
    pg, cn = env
    pg.write_page("only-llms", "x", T13)
    res = cn.run(site(pg, {}, {"other": None}, ["other", "only-llms"], []), now=T14, rebuild=False)
    assert res["removed"] == [] and os.path.exists(pg.dest("only-llms"))


def test_unlisted_but_served_is_kept(env):
    pg, cn = env
    pg.write_page("hidden", "x", T13)
    res = cn.run(site(pg, {"hidden": "x"}, {"other": None}, ["other"], []), now=T14, rebuild=False)
    assert res["removed"] == [] and os.path.exists(pg.dest("hidden"))


def test_redirect_records_moved_to(env, tmp_path):
    pg, cn = env
    pg.write_page("sdk/python/usage", "x", T13)
    res = cn.run(site(pg, {"sdk/python/usage": ("moved", "sdk/python/usage/basic")}, {"other": None}, ["other"], []), now=T14, rebuild=False)
    assert res["moved"] == {"sdk/python/usage": "sdk/python/usage/basic"}
    assert res["removed"] == ["sdk/python/usage"] and not os.path.exists(pg.dest("sdk/python/usage"))


def test_sitemap_down_still_checks_llms_and_prunes_nothing(env):
    pg, cn = env
    pg.write_page("a", "old", T13)
    pg.write_page("b", "x", T13)
    res = cn.run(site(pg, {"a": "new"}, None, ["a"], []), now=T14, rebuild=False)
    assert res["removed"] == [] and os.path.exists(pg.dest("b"))
    assert "sitemap" in res["notice"] and "couldn't be read" in res["notice"]
    assert json.load(open(cn.STATE))["last_success"]


def test_llms_down_prunes_nothing(env):
    pg, cn = env
    pg.write_page("gone", "x", T13)
    res = cn.run(site(pg, {}, {"other": None}, None, []), now=T14, rebuild=False)
    assert res["removed"] == [] and os.path.exists(pg.dest("gone"))
    assert "llms.txt" in res["notice"]


def test_no_list_readable_keeps_old_success(env, capsys):
    pg, cn = env
    cn.state_update(last_success=111)
    assert cn.main(site(pg, {}, None, None, [])) == 1
    s = json.load(open(cn.STATE))
    assert s["last_success"] == 111 and "could not read" in s["last_error"]
    assert not os.path.exists(cn.LOCK)


def test_lock_removed_on_exit(env):
    pg, cn = env
    assert cn.main(site(pg, {}, {}, [], [])) == 0
    assert not os.path.exists(cn.LOCK)


def test_lock_held_by_another_run(env):
    pg, cn = env
    assert cn.take_lock()
    calls = []
    assert cn.main(site(pg, {}, {}, [], calls)) == 0
    assert calls == [] and os.path.exists(cn.LOCK)  # not ours: left alone


def test_listed_but_404_named_once(env):
    pg, cn = env
    r1 = cn.run(site(pg, {}, {"ghost": None}, ["ghost"], []), now=T14, rebuild=False)
    assert r1["listed_missing"] == ["ghost"] and "ghost" in r1["notice"]
    r2 = cn.run(site(pg, {}, {"ghost": None}, ["ghost"], []), now=T14, rebuild=False)
    assert r2["listed_missing"] == ["ghost"] and "ghost" not in r2["notice"]
    cn.run(site(pg, {}, {"other": None}, ["other"], []), now=T14, rebuild=False)
    r4 = cn.run(site(pg, {}, {"ghost": None}, ["ghost"], []), now=T14, rebuild=False)
    assert "ghost" in r4["notice"]  # it recovered in between, so a new failure is news


def test_failed_fetch_named_once(env):
    pg, cn = env
    texts = {"flaky": OSError("boom")}
    r1 = cn.run(site(pg, texts, {"flaky": None}, ["flaky"], []), now=T14, rebuild=False)
    assert len(r1["failed"]) == 1 and "flaky" in r1["notice"]
    r2 = cn.run(site(pg, texts, {"flaky": None}, ["flaky"], []), now=T14, rebuild=False)
    assert len(r2["failed"]) == 1 and "flaky" not in r2["notice"]


def _change(pg, cn, text, now, lastmod):
    return cn.run(site(pg, {"models": text}, {"models": lastmod}, ["models"], []), now=now, rebuild=False)


def test_second_run_same_day_keeps_first_archive(env, tmp_path):
    pg, cn = env
    pg.write_page("models", "old", T13)
    _change(pg, cn, "new1", T14, "2026-10-14T21:00:00Z")
    _change(pg, cn, "new2", T14 + datetime.timedelta(seconds=1), "2026-10-14T23:00:30Z")
    first = open(archived(tmp_path, RUN14, "changed")[0]).read()
    second = open(archived(tmp_path, "2026-10-14T230001Z", "changed")[0]).read()
    assert first.endswith("old") and second.endswith("new1")


def test_unshown_notice_is_appended_not_overwritten(env):
    pg, cn = env
    pg.write_page("models", "old", T13)
    _change(pg, cn, "new1", T14, "2026-10-14T21:00:00Z")
    _change(pg, cn, "new2", T14 + datetime.timedelta(seconds=1), "2026-10-14T23:00:30Z")
    assert len(open(cn.NOTICE).read().strip().split("\n")) == 2


def test_rebuild_drops_pruned_page_from_index(env, monkeypatch):
    pg, cn = env
    monkeypatch.setenv("JEV_SEMANTIC", "off")
    for s in ("a", "b", "c"):
        pg.write_page(s, f"# {s.upper()}\n\n## {s} intro\n\ntext\n", T13)
    build = os.path.join(cn.SCRIPTS, "build_index.py")
    subprocess.run([sys.executable, build], check=True, capture_output=True)
    assert "docs/c.md" in open(os.path.join(cn.DATA, "sections.jsonl")).read()
    texts = {"d": "# D\n\n## d intro\n\ntext\n"}
    res = cn.run(site(pg, texts, {"a": None, "b": None, "d": None}, ["a", "b", "d"], []), now=T14)
    rows = [json.loads(l) for l in open(os.path.join(cn.DATA, "sections.jsonl"))]
    assert not any(r["path"] == "docs/c.md" for r in rows) and any(r["path"] == "docs/d.md" for r in rows)
    assert ["docs/c.md", "c intro"] in res["removed_sections"]
    assert ["docs/d.md", "d intro"] in res["added_sections"]
    assert json.load(open(cn.CHANGES))["removed"] == ["c"]


def test_check_fetches_only_unsaved_posts(env):
    pg, cn = env
    import blog
    blog.save("old-post", "# Old\n\nKept as it was.", T13)
    calls = []
    res = cn.run(site(pg, {}, {"other": None}, ["other"], calls, posts={"old-post": POST_HTML, "new-post": POST_HTML}), now=T14, rebuild=False)
    post_calls = [c for c in calls if "/blog/" in c]
    assert post_calls == ["https://typesafe.ai/blog/new-post"]
    assert "blog/new-post" in res["added"] and "blog/new-post" in res["notice"]
    assert os.path.exists(blog.dest("new-post"))
    assert open(blog.dest("old-post")).read().rstrip().endswith("Kept as it was.")


def test_site_sitemap_down_still_checks_docs(env):
    pg, cn = env
    pg.write_page("models", "old", T13)
    pg.write_page("kept", "x", T13)
    res = cn.run(site(pg, {"models": "new"}, {"models": "2026-10-14T21:00:00Z", "kept": None}, ["models", "kept"], [], site_down=True), now=T14, rebuild=False)
    assert res["changed"] == ["models"] and res["removed"] == []
    assert "blog list" in res["notice"] and "couldn't be read" in res["notice"]


def test_failed_post_named_once(env):
    pg, cn = env
    posts = {"gone-post": 404}
    first = cn.run(site(pg, {}, {"other": None}, ["other"], [], posts=posts), now=T14, rebuild=False)
    assert first["failed"] == ["blog/gone-post (gone)"] and first["notice"].count("blog/gone-post") == 1
    second = cn.run(site(pg, {}, {"other": None}, ["other"], [], posts=posts), now=T14 + datetime.timedelta(hours=1), rebuild=False)
    assert second["failed"] == ["blog/gone-post (gone)"] and "blog/gone-post" not in second["notice"]


def test_failed_post_with_changing_error_named_once(env):
    pg, cn = env
    first = cn.run(site(pg, {}, {"other": None}, ["other"], [], posts={"slow-post": OSError("timed out after 30s")}), now=T14, rebuild=False)
    assert first["notice"].count("blog/slow-post") == 1
    second = cn.run(site(pg, {}, {"other": None}, ["other"], [], posts={"slow-post": OSError("connection reset")}),
                    now=T14 + datetime.timedelta(hours=1), rebuild=False)
    assert second["failed"] == ["blog/slow-post (fetch failed (OSError: connection reset))"] and "blog/slow-post" not in second["notice"]


EMPTY_HTML = "<html><body><nav>menu</nav><h1>A video</h1><p>Oct 14, 2026</p></body></html>"


def test_an_empty_page_post_is_skipped_not_failed_and_not_refetched(env):
    pg, cn = env
    calls = []
    posts = {"video-post": EMPTY_HTML}
    first = cn.run(site(pg, {}, {"other": None}, ["other"], calls, posts=posts), now=T14, rebuild=False)
    assert first["failed"] == [] and first["notice"].count("blog/video-post") == 1 and "no text below the title" in first["notice"]
    assert [c for c in calls if "/blog/video-post" in c] == ["https://typesafe.ai/blog/video-post"]
    calls.clear()
    second = cn.run(site(pg, {}, {"other": None}, ["other"], calls, posts=posts), now=T14 + datetime.timedelta(hours=1), rebuild=False)
    assert not [c for c in calls if "/blog/video-post" in c] and "blog/video-post" not in second["notice"]


def test_a_post_that_failed_to_download_is_still_retried(env):
    pg, cn = env
    calls = []
    posts = {"slow-post": OSError("timed out")}
    cn.run(site(pg, {}, {"other": None}, ["other"], calls, posts=posts), now=T14, rebuild=False)
    cn.run(site(pg, {}, {"other": None}, ["other"], calls, posts=posts), now=T14 + datetime.timedelta(hours=1), rebuild=False)
    assert len([c for c in calls if "/blog/slow-post" in c]) == 2


def _build_index(tmp_path):
    subprocess.run([sys.executable, os.path.join(CODE, "scripts", "build_index.py")], check=True, capture_output=True,
                   env=dict(os.environ, JEV_SOURCES_DATA=str(tmp_path), JEV_SEMANTIC="off", JEV_LOG="off"))


def test_a_full_refresh_archives_a_changed_page_and_runs_the_citation_check(env, tmp_path, capsys):
    pg, cn = env
    import fetch
    pg.write_page("models", "# Models\n\n## Intro\n\ntext\n\n## Old section\n\nmore\n", T13)
    _build_index(tmp_path)
    code = fetch.main(site(pg, {"models": "# Models\n\n## Intro\n\ntext\n"}, {"models": None}, ["models"], []))
    assert code == 0
    old = glob.glob(str(tmp_path / "archive" / "*" / "changed" / "docs" / "models.md"))
    assert len(old) == 1 and "Old section" in open(old[0]).read()
    assert "Old section" not in open(pg.dest("models")).read()
    ch = json.load(open(cn.CHANGES))
    assert ch["changed"] == ["models"] and ["docs/models.md", "Old section"] in ch["removed_sections"]
    assert os.path.exists(tmp_path / "STALE_CITATIONS.md")


def test_a_full_refresh_with_no_changed_page_writes_no_change_record(env, tmp_path):
    pg, cn = env
    import fetch
    pg.write_page("models", "# Models\n\n## Intro\n\ntext\n", T13)
    fetch.main(site(pg, {"models": "# Models\n\n## Intro\n\ntext\n"}, {"models": None}, ["models"], []))
    assert not os.path.exists(cn.CHANGES) and not glob.glob(str(tmp_path / "archive" / "*"))


def test_a_full_refresh_records_only_new_posts_as_added(env, tmp_path):
    pg, cn = env
    import fetch, blog
    blog.save("old-post", "# Old\n\nKept as it was.", T13)
    pg.write_page("models", "# Models\n\n## Intro\n\ntext\n\n## Old section\n\nmore\n", T13)
    _build_index(tmp_path)
    fetch.main(site(pg, {"models": "# Models\n\n## Intro\n\ntext\n"}, {"models": None}, ["models"], [],
                    posts={"old-post": POST_HTML, "new-post": POST_HTML}))
    assert json.load(open(cn.CHANGES))["added"] == ["blog/new-post"]



def test_the_notice_is_capped(env):
    pg, cn = env
    many = {"p%03d" % i: OSError("x" * 200) for i in range(40)}
    res = cn.run(site(pg, {}, {"other": None}, ["other"], [], posts=many), now=T14, rebuild=False)
    assert len(res["notice"]) <= cn.NOTICE_CAP
