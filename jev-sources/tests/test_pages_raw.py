import datetime, json, os, subprocess, sys, time
import pytest
from test_check_new import env, site, archived, T13, T14, RUN14, CODE  # noqa: F401  (env is a fixture)
UTC = datetime.timezone.utc

RAW = ("# Models\n\nSome prose.\n\nexport const Widget = () => {\n  return 1;\n};\n\n"
       "Try it: https://console.typesafe.ai/playground#share/abcdef123\n")


def clean_mod():
    import clean
    return clean


def first_line(path):
    return open(path, encoding="utf-8").readline().rstrip("\n")


def old_style(pg, slug, text, stamp="2026-10-13T12:00:00Z"):
    """A page saved before raw copies existed: one file, a header without a cleaner field."""
    p = pg.dest(slug)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    data = f"<!-- saved {stamp} from {pg.BASE}{slug}.md -->\n\n{text}"
    with open(p, "w", encoding="utf-8") as f:
        f.write(data)
    return p, data


def test_write_page_writes_raw_first_and_both_carry_the_same_time(env, monkeypatch):
    pg, _ = env
    order = []
    real = pg._atomic_write
    monkeypatch.setattr(pg, "_atomic_write", lambda path, text: (order.append(path), real(path, text))[1])
    pg.write_page("models", RAW, T13)
    assert order == [pg.raw_dest("models"), pg.dest("models")]
    assert pg.saved_at(pg.raw_dest("models")) == pg.saved_at(pg.dest("models")) == T13
    assert first_line(pg.raw_dest("models")) == "<!-- saved 2026-10-13T12:00:00Z from https://docs.typesafe.ai/models.md -->"
    assert first_line(pg.dest("models")).endswith("models.md | cleaner 1 -->")
    assert pg.raw_text(pg.dest("models")) == RAW
    assert "#share/" not in pg.body(pg.dest("models"))


def test_a_failure_writing_the_cleaned_copy_leaves_the_raw_copy(env, monkeypatch):
    pg, _ = env
    real = pg._atomic_write

    def boom(path, text):
        if path == pg.dest("models"):
            raise OSError("disk full")
        real(path, text)
    monkeypatch.setattr(pg, "_atomic_write", boom)
    with pytest.raises(OSError):
        pg.write_page("models", RAW, T13)
    assert open(pg.raw_dest("models"), encoding="utf-8").read().endswith(RAW)
    assert not os.path.exists(pg.dest("models"))
    assert [f for f in os.listdir(os.path.dirname(pg.raw_dest("models"))) if f.endswith(".tmp")] == []


def test_migration_keeps_the_old_file_as_raw_and_its_saved_time(env):
    pg, cn = env
    p, data = old_style(pg, "models", RAW)
    assert pg.prepare() == ["models"]
    assert open(pg.raw_dest("models"), "rb").read() == data.encode("utf-8")
    assert pg.saved_at(p) == T13 and pg.cleaner_of(p) == 1
    assert "#share/" not in pg.body(p)
    calls = []
    cn.run(site(pg, {"models": "other"}, {"models": "2026-10-12T00:00:00Z"}, ["models"], calls), now=T14, rebuild=False)
    assert not any(c.endswith("models.md") for c in calls)
    assert open(pg.raw_dest("models"), "rb").read() == data.encode("utf-8")


def test_a_date_only_header_survives_migration(env):
    pg, _ = env
    p, _ = old_style(pg, "models", RAW, stamp="2026-10-13")
    pg.prepare()
    assert pg.saved_at(p) == datetime.datetime(2026, 10, 13, tzinfo=UTC)
    assert first_line(p).startswith("<!-- saved 2026-10-13 from ")


def test_a_cleaned_page_with_no_raw_copy_is_never_copied_to_raw(env, tmp_path):
    pg, cn = env
    p = pg.dest("models")
    os.makedirs(os.path.dirname(p))
    open(p, "w", encoding="utf-8").write("<!-- saved 2026-10-13T12:00:00Z from https://docs.typesafe.ai/models.md | cleaner 1 -->\n\ncleaned only")
    assert pg.prepare() == []
    assert not os.path.exists(pg.raw_dest("models"))
    assert json.load(open(tmp_path / "needs_raw.json")) == ["models"]
    calls = []
    res = cn.run(site(pg, {"models": RAW}, {"models": "2026-10-01T00:00:00Z"}, ["models"], calls), now=T14, rebuild=False)
    assert any(c.endswith("models.md") for c in calls)  # fetched whatever the sitemap date
    assert pg.raw_text(p) == RAW and res["changed"] == []
    assert len(archived(tmp_path, RUN14, "replaced")) == 1  # the unverified copy is kept, not deleted


def test_a_cleaner_version_bump_recleans_without_a_docs_change(env, tmp_path, monkeypatch):
    pg, cn = env
    clean = clean_mod()
    pg.write_page("models", RAW, T13)
    stale = tmp_path / "STALE_CITATIONS.md"
    stale.write_text("old")
    os.utime(stale, (1000, 1000))
    monkeypatch.setattr(clean, "VERSION", 2)
    res = cn.run(site(pg, {"models": RAW}, {"models": "2026-10-14T21:00:00Z"}, ["models"], []), now=T14, rebuild=False)
    assert res["changed"] == [] and res["added"] == []
    assert not os.path.exists(cn.CHANGES)
    assert os.path.getmtime(stale) == 1000
    assert pg.cleaner_of(pg.dest("models")) == 2
    assert pg.saved_at(pg.dest("models")) == pg.saved_at(pg.raw_dest("models"))


def test_recleaning_never_redates_a_page(env, monkeypatch):
    pg, _ = env
    pg.write_page("models", RAW, T13)
    monkeypatch.setattr(clean_mod(), "VERSION", 2)
    assert pg.prepare() == ["models"]
    assert pg.saved_at(pg.dest("models")) == T13 and pg.cleaner_of(pg.dest("models")) == 2
    assert pg.prepare() == []


def test_new_raw_text_is_a_change_and_both_copies_are_archived(env, tmp_path):
    pg, cn = env
    pg.write_page("models", RAW, T13)
    res = cn.run(site(pg, {"models": RAW + "A new paragraph.\n"}, {"models": "2026-10-14T21:00:00Z"}, ["models"], []), now=T14, rebuild=False)
    assert res["changed"] == ["models"]
    base = tmp_path / "archive" / RUN14 / "changed"
    assert (base / "docs" / "models.md").exists() and (base / "raw" / "docs" / "models.md").exists()
    assert open(base / "raw" / "docs" / "models.md", encoding="utf-8").read().endswith(RAW)
    assert pg.raw_text(pg.dest("models")).endswith("A new paragraph.\n")


def test_a_text_that_differs_only_in_a_share_payload_still_counts_as_changed(env):
    pg, cn = env
    pg.write_page("models", RAW, T13)
    other = RAW.replace("abcdef123", "zzzzzz999")
    assert pg.digest(pg.body(pg.dest("models"))) == pg.digest(pg.body(pg.dest("models")))
    res = cn.run(site(pg, {"models": other}, {"models": "2026-10-14T21:00:00Z"}, ["models"], []), now=T14, rebuild=False)
    assert res["changed"] == ["models"]
    assert pg.raw_text(pg.dest("models")) == other


def test_touch_rewrites_both_copies_with_the_new_time(env):
    pg, cn = env
    pg.write_page("models", RAW, T13)
    res = cn.run(site(pg, {"models": RAW}, {"models": "2026-10-14T21:00:00Z"}, ["models"], []), now=T14, rebuild=False)
    assert res["redated"] == ["models"]
    assert pg.saved_at(pg.raw_dest("models")) == pg.saved_at(pg.dest("models")) == T14
    assert pg.raw_text(pg.dest("models")) == RAW


def failing_write(pg):
    """Saves a page while the cleaner raises; the cleaner works again afterwards."""
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(clean_mod(), "clean", lambda text: (_ for _ in ()).throw(ValueError("bad page")))
        pg.write_page("models", RAW, T13)


def test_a_clean_failure_keeps_the_raw_text_and_is_not_retried(env, capsys):
    pg, _ = env
    failing_write(pg)
    assert pg.cleaner_of(pg.dest("models")) == "failed:1"
    assert pg.body(pg.dest("models")) == RAW
    assert "NOTICE: could not clean" in capsys.readouterr().out
    assert pg.prepare() == []  # the cleaner works again, but this VERSION already failed on the page
    assert pg.cleaner_of(pg.dest("models")) == "failed:1"


def test_the_build_names_a_page_that_could_not_be_cleaned(env, tmp_path):
    pg, _ = env
    failing_write(pg)
    e = dict(os.environ, JEV_SOURCES_DATA=str(tmp_path), JEV_LOG="off", HF_HUB_OFFLINE="1")
    r = subprocess.run([sys.executable, os.path.join(CODE, "scripts", "build_index.py")], capture_output=True, text=True, env=e)
    assert r.returncode == 0, r.stderr
    assert "NOTICE: could not clean docs/models.md" in r.stdout


def test_a_higher_failed_version_is_retried(env, monkeypatch):
    pg, _ = env
    failing_write(pg)
    monkeypatch.setattr(clean_mod(), "VERSION", 2)
    assert pg.prepare() == ["models"]
    assert pg.cleaner_of(pg.dest("models")) == 2


def test_prepare_skips_when_another_check_holds_the_lock(env, capsys):
    pg, _ = env
    old_style(pg, "models", RAW)
    open(pg.LOCK, "w").close()
    assert pg.prepare() == []
    assert "another check is running" in capsys.readouterr().out
    assert not os.path.exists(pg.raw_dest("models")) and os.path.exists(pg.LOCK)  # untouched, and the lock is not ours


def test_prepare_takes_and_drops_its_own_lock(env):
    pg, _ = env
    old_style(pg, "models", RAW)
    assert pg.prepare() == ["models"]
    assert not os.path.exists(pg.LOCK)


def test_prepare_leaves_a_lock_it_was_given(env):
    pg, _ = env
    old_style(pg, "models", RAW)
    assert pg.take_lock()
    assert pg.prepare(locked=True) == ["models"]
    assert os.path.exists(pg.LOCK)
    pg.drop_lock()
    assert not os.path.exists(pg.LOCK)


def test_library_never_lists_raw_files_and_raw_dest_stays_inside(env):
    pg, _ = env
    pg.write_page("models", RAW, T13)
    pg.write_page("cookbooks/rerank", RAW, T13)
    assert set(pg.library()) == {"models", "cookbooks/rerank"}
    assert pg.raw_dest("cookbooks/rerank").endswith(os.path.join("raw", "cookbooks", "rerank.md"))
    with pytest.raises(ValueError):
        pg.raw_dest("patterns/../../escape")


def test_raw_dest_refuses_a_raw_folder_that_is_a_link_out_of_the_library(env, tmp_path_factory):
    pg, _ = env
    outside = tmp_path_factory.mktemp("outside")
    os.symlink(str(outside), os.path.join(pg.DATA, "raw"))
    with pytest.raises(ValueError):
        pg.raw_dest("models")


def test_fetch_main_compares_raw_and_takes_the_lock(env, tmp_path, monkeypatch):
    pg, cn = env
    import fetch
    monkeypatch.setattr("blog.list_posts", lambda f: [])
    pg.write_page("models", RAW, T13)
    f = site(pg, {"models": RAW}, {"models": None}, ["models"], [])
    monkeypatch.setattr(pg, "get", f)
    assert fetch.main(f) == 0
    assert not os.path.exists(cn.CHANGES)  # same raw text: nothing changed
    open(pg.LOCK, "w").close()
    assert fetch.main(f) == 1  # a check is running
    os.remove(pg.LOCK)
    new = site(pg, {"models": RAW + "more\n"}, {"models": None}, ["models"], [])
    monkeypatch.setattr(cn, "record_changes", lambda res, now, rebuild=True: [])
    assert fetch.main(new) == 0
    assert len(glob_changed(tmp_path)) == 2


def glob_changed(tmp_path):
    out = []
    for root, _, files in os.walk(tmp_path / "archive"):
        if os.sep + "changed" in root + os.sep:
            out += [os.path.join(root, f) for f in files]
    return out
