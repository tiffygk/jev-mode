#!/usr/bin/env python3
"""Download every page TypeSafe lists (sitemap and llms.txt) into the data folder: docs/, cookbooks/, patterns/. Also every blog post in typesafe.ai's sitemap, into blog/.
A page that fails (404, rate limit) or has moved is named and skipped; the run carries on. Exit 1 if any failed or is gone.
A blog post with nothing below its title (a video post) is named as skipped and does not fail the run.
A page whose text changed is archived first (archive/<run time>/changed/), and the changed and removed sections go
through the same record and checks as check_new.py: section_changes.json, STALE_CITATIONS.md, the routing retest."""
import datetime, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pages, blog, check_new


def main(fetch=None):
    if not pages.take_lock():
        print("fetch: another check is running; try again when it finishes")
        return 1
    try:
        return _main(fetch)
    finally:
        pages.drop_lock()


def _main(fetch):
    fetch = fetch or pages.get
    now = datetime.datetime.now(pages.UTC)
    before = check_new.headings()  # the sections as indexed before prepare rewrites any page
    prepared = pages.prepare(locked=True, now=now)
    half = list(pages.HALF_WRITTEN)  # new raw text beside an old cleaned copy (a crash): reported as changed below
    build_failed = False
    if prepared:  # migrated, re-cleaned or half-written pages: the index follows now, whatever happens next
        notice = check_new.rebuild_index()
        if notice:
            print(notice)
            build_failed = True
    try:
        found, _ = pages.live_pages(fetch)
    except RuntimeError as e:
        if half:  # already rewritten and indexed: record them before giving up
            check_new.record_changes({"changed": half, "added": [], "removed": [], "moved": {}, "removed_sections": [], "added_sections": []},
                                     now, False, before)
        sys.exit(f"fetch: {e}")
    slugs = sorted(found)
    lib = pages.library()
    ok, failed, changed, added = 0, [], list(half), []
    for slug in slugs:
        try:
            text = fetch(pages.BASE + slug + ".md")
            raw = pages.raw_text(lib[slug]) if slug in lib else None
            if slug in lib and raw is None:  # no raw copy to compare: the unverified copy is kept in the archive
                if pages.differs_from_cleaned(lib[slug], text) and slug not in changed:
                    changed.append(slug)
                pages.archive(lib[slug], "replaced", now)
            elif slug in lib and pages.digest(raw) != pages.digest(text):
                if slug not in changed:  # prepare already archived a half-written page's old copy
                    pages.archive(lib[slug], "changed", now)
                    changed.append(slug)
            elif slug not in lib:
                added.append(slug)
            pages.write_page(slug, text)
            ok += 1
        except pages.Gone as e:
            moved = f" -> {e.moved_to}" if e.moved_to else ""
            print(f"gone: {slug}{moved}")
            failed.append(slug)
        except Exception as e:
            print(f"fetch failed: {slug} ({e})")
            failed.append(slug)
    try:
        posts = blog.list_posts(fetch)
    except Exception as e:  # the docs are already saved; the blog list is a separate site
        print(f"blog list couldn't be read ({e}); no blog posts fetched")
        posts = []
    had = {p for p in posts if os.path.exists(blog.dest(p))}  # only posts not saved before count as added
    saved, bad = blog.fetch_posts(posts, fetch)
    skipped = [p for p, why in bad if why == blog.EMPTY]
    for p, why in bad:
        print(f"skipped: blog/{p} ({why})" if why == blog.EMPTY else f"gone: blog/{p}" if why == "gone" else f"blog/{p}: {why}")
    ok += len(saved)
    slugs += [f"blog/{p}" for p in posts if p not in skipped]
    failed += [f"blog/{p}" for p, why in bad if why != blog.EMPTY]
    print(f"fetched {ok} of {len(slugs)} pages into {pages.DATA}")
    if changed:  # first installs and unchanged refreshes have nothing to compare, so nothing to check
        res = {"changed": changed, "added": added + [f"blog/{p}" for p in saved if p not in had], "removed": [], "moved": {},
               "removed_sections": [], "added_sections": []}
        for line in check_new.record_changes(res, now, True, before):
            print(line)
        build_failed = build_failed or res.get("build_failed", False)
    return 1 if failed or build_failed else 0


if __name__ == "__main__":
    sys.exit(main())
