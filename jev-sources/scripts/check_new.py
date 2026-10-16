#!/usr/bin/env python3
"""Check TypeSafe's docs for changed, new and removed pages and update the library.
A page is flagged when its sitemap date is newer than its saved time (or it has no raw copy); only flagged and new pages
are downloaded, and a download is kept only when its text changed against the raw copy (the old copies, raw and
cleaned, go to archive/<run time>/changed/). A cleaner version change re-cleans pages from raw and is never a change.
A library page that is in neither the sitemap nor llms.txt and returns 404 or redirects goes to archive/<run time>/removed/.
Blog posts (typesafe.ai's sitemap): only posts not yet saved are fetched, and a saved post is never pruned.
Writes NEW_PAGES.txt (shown once by the reminder hook), section_changes.json and last_check.json.
Started in the background by hooks/refresh_trigger.py; safe to run by hand."""
import datetime, json, os, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pages, blog
from paths import DATA, SCRIPTS, REFRESH
import usage_log

STATE, NOTICE = os.path.join(DATA, "last_check.json"), os.path.join(DATA, "NEW_PAGES.txt")
NOTICE_CAP = 1500  # the hook shows this to the model; page names and errors come from TypeSafe's site
CHANGES, LOCK = os.path.join(DATA, "section_changes.json"), pages.LOCK
take_lock = pages.take_lock  # the lock lives in pages.py; build_index and fetch take it too


def state_read():
    try:
        return json.load(open(STATE))
    except (OSError, ValueError):
        return {}


def state_update(**kv):
    s = state_read()
    s.update(kv)
    os.makedirs(DATA, exist_ok=True)
    with open(STATE + ".tmp", "w") as f:
        json.dump(s, f)
    os.replace(STATE + ".tmp", STATE)


def headings():
    try:
        return {(r["path"], r["heading"]) for r in map(json.loads, open(os.path.join(DATA, "sections.jsonl")))}
    except OSError:
        return set()


def after_change(result):
    lines = []
    try:
        import route_check
        lines.append(route_check.summary(route_check.run()))
    except BaseException as e:  # route.py calls sys.exit on a missing index
        lines.append(f"Routing check couldn't run ({type(e).__name__}).")
    try:
        import applicability
        lib = pages.library()
        texts = {os.path.relpath(lib[s], DATA).replace(os.sep, "/"): pages.body(lib[s])
                 for s in result.get("changed", []) + result.get("added", []) if s in lib}
        gaps = applicability.uncovered(texts)
        if gaps:
            lines.append(f"{len(gaps)} new page(s) state a model or readiness limit not yet in applicability.json: {', '.join(gaps[:8])}.")
    except BaseException as e:
        lines.append(f"Applicability check couldn't run ({type(e).__name__}).")
    try:
        import citations
        rows, path = citations.report()
        if rows:
            lines.append(f"{len(rows)} citation(s) to check: {path}.")
    except FileNotFoundError:  # no section_changes.json: nothing changed, nothing to check
        pass
    except BaseException as e:
        lines.append(f"Citation check couldn't run ({type(e).__name__}).")
    return lines


def record_changes(res, now, rebuild=True):
    """After pages changed: rebuild the index, record which sections went and came in section_changes.json, then run
    the routing, applicability and citation checks. Returns their notice lines. Shared with fetch.py (full refresh)."""
    before = headings()
    if rebuild:
        subprocess.run([sys.executable, os.path.join(SCRIPTS, "build_index.py"), "--no-prepare"], check=False, capture_output=True)
        after = headings()
        res["removed_sections"] = sorted([p, h] for p, h in before - after)
        res["added_sections"] = sorted([p, h] for p, h in after - before)
    with open(CHANGES, "w") as f:
        json.dump({"date": pages.stamp(now), **{k: res[k] for k in ("changed", "added", "removed", "moved", "removed_sections", "added_sections")}}, f, indent=1)
    return after_change(res)


MARGIN = datetime.timedelta(hours=12)  # sitemap dates look like build time; a fetch between build and deploy saves
                                       # old text with a newer stamp, so compare against saved time minus a margin


def run(fetch=None, now=None, rebuild=True):
    fetch = fetch or pages.get
    now = now or datetime.datetime.now(pages.UTC)
    notes = []
    prepared = pages.prepare(locked=True, now=now)
    half = [s for s in pages.HALF_WRITTEN]  # a crash left new raw text beside an old cleaned copy: a docs change, recorded below
    if prepared and rebuild and not half:  # migrated or re-cleaned pages: the index follows, and this is no docs change
        subprocess.run([sys.executable, os.path.join(SCRIPTS, "build_index.py"), "--no-prepare"], check=False, capture_output=True)
    live, read = pages.live_pages(fetch)  # RuntimeError when neither list reads
    both = read == {"sitemap", "llms"}
    if not both:
        notes.append(f"TypeSafe's {'sitemap' if 'sitemap' not in read else 'llms.txt'} couldn't be read, so changes may be missed and nothing was pruned.")
    lib = pages.library()
    new = sorted(s for s in live if s not in lib)
    flagged = sorted(s for s, p in lib.items() if live.get(s) and (pages.saved_at(p) is None or live[s] > pages.saved_at(p) - MARGIN))
    unraw = {s for s in pages.needs_raw() if s in lib}  # cleaned pages with no raw copy: refetched whatever their date
    flagged = sorted(set(flagged) | unraw)
    res = {"changed": list(half), "added": [], "redated": [], "reraw": [], "removed": [], "moved": {}, "failed": [], "listed_missing": [],
           "removed_sections": [], "added_sections": []}
    for s in flagged + new:
        try:
            text = fetch(pages.BASE + s + ".md")
        except pages.Gone as g:
            if g.moved_to:
                res["moved"][s] = g.moved_to
            elif s not in lib:
                res["listed_missing"].append(s)  # listed by TypeSafe but 404: named once in the notice
            continue  # still listed somewhere: not pruned
        except Exception as e:
            res["failed"].append(f"{s} ({e})")
            continue
        if s in lib:
            raw = pages.raw_text(lib[s])
            if raw is None:  # no raw copy to compare: this download becomes it; the unverified copy is kept in the archive
                differs = pages.differs_from_cleaned(lib[s], text)
                pages.archive(lib[s], "replaced", now)
                res["reraw"].append(s)
                if differs and s not in res["changed"]:  # new words the index never saw: a change, reported and indexed
                    res["changed"].append(s)
            elif pages.digest(raw) == pages.digest(text):
                pages.touch(lib[s], now)
                res["redated"].append(s)
                continue
            else:
                if s not in res["changed"]:  # prepare already archived a half-written page's old copy
                    pages.archive(lib[s], "changed", now)
                    res["changed"].append(s)
        else:
            res["added"].append(s)
        pages.write_page(s, text, now)
    if both:  # prune only when both lists were read
        for s in sorted(set(lib) - set(live)):
            try:
                fetch(pages.BASE + s + ".md")
                continue  # unlisted but still served: keep
            except pages.Gone as g:
                if g.moved_to:
                    res["moved"][s] = g.moved_to
            except Exception as e:
                res["failed"].append(f"{s} ({e})")
                continue
            pages.archive(lib[s], "removed", now)
            res["removed"].append(s)
    try:  # blog posts: only unsaved ones are fetched; a saved post is never refetched or pruned here
        empty = set(state_read().get("empty_posts", []))  # nothing below the title (a video post): retried only by refresh.sh --fetch
        unsaved = [p for p in blog.list_posts(fetch) if not os.path.exists(blog.dest(p)) and p not in empty]
    except Exception:
        unsaved = []
        notes.append("TypeSafe's blog list couldn't be read, so new posts may be missed.")
    saved, failed = blog.fetch_posts(unsaved, fetch, now)
    res["added"] += [f"blog/{p}" for p in saved]
    res["failed"] += [f"blog/{p} ({why})" for p, why in failed if why != blog.EMPTY]
    new_empty = [p for p, why in failed if why == blog.EMPTY]
    if new_empty:
        state_update(empty_posts=sorted(set(state_read().get("empty_posts", [])) | set(new_empty)))
    if res["changed"] or res["added"] or res["removed"]:
        notes += record_changes(res, now, rebuild)
    reported = state_read().get("reported", {})  # a page that stays listed-but-404 or unfetchable is named once
    name = lambda x: x.split(" (")[0]  # compare by page, not by its error text, which can vary run to run
    shown = {k: [x for x in res[k] if name(x) not in {name(y) for y in reported.get(k, [])}] for k in ("listed_missing", "failed")}
    parts = []
    for key, verb in (("changed", "changed"), ("added", "added"), ("removed", "removed (archived)")):
        if res[key]:
            parts.append(f"TypeSafe {verb} {len(res[key])} page(s): {', '.join(res[key][:12])}{' ...' if len(res[key]) > 12 else ''}.")
    if new_empty:  # named once: one is a video post; many at once means the blog layout changed
        parts.append(f"Skipped {len(new_empty)} blog post(s) with no text below the title: {', '.join('blog/' + p for p in new_empty[:5])}.")
    if res["moved"]:
        parts.append("Moved: " + ", ".join(f"{a} -> {b}" for a, b in res["moved"].items()) + ".")
    if shown["failed"]:
        parts.append(f"{len(shown['failed'])} page(s) couldn't be fetched: {', '.join(shown['failed'][:5])}.")
    if shown["listed_missing"]:
        parts.append(f"TypeSafe lists {len(shown['listed_missing'])} page(s) that return 404: {', '.join(shown['listed_missing'][:5])}.")
    res["notice"] = " ".join(parts + notes)[:NOTICE_CAP]
    if res["notice"]:
        with open(NOTICE, "a") as f:  # append: a notice not yet shown is never overwritten
            f.write(res["notice"] + "\n")
    state_update(last_success=time.time(), last_counts={k: len(v) for k, v in res.items() if isinstance(v, (list, dict))}, last_error=None,
                 reported={k: res[k] for k in ("listed_missing", "failed")})
    usage_log.write("refresh", **{k: len(v) for k, v in res.items() if isinstance(v, (list, dict))})
    return res


def main(fetch=None, locked=False):
    """locked=True when refresh_trigger already took the lock for this run (it passes --locked)."""
    if not locked and not take_lock():
        print("check_new: another check is running")
        return 0
    try:
        res = run(fetch)
        print(res["notice"] or "check_new: library matches TypeSafe's docs")
        return 0
    except Exception as e:
        state_update(last_error=f"{type(e).__name__}: {e}")
        print(f"check_new: {e}", file=sys.stderr)
        return 1
    finally:
        pages.drop_lock()  # only the run that owns the lock gets here


if __name__ == "__main__":
    sys.exit(main(locked="--locked" in sys.argv))
