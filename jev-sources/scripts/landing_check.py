#!/usr/bin/env python3
"""Did the docs update land? Compares the saved index with the saved pages, using the build's own code and its own rule
for skipped files, then asks the router whether the vectors match, and looks for a page or a library that collapsed.
It runs on every background check and every refresh, and only reports: it never blocks a refresh, never restores an
old index and never raises. It makes no network call; a missing model only leaves routing keyword-only.
Run by hand: python3 landing_check.py"""
import datetime, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

NOTICE_PREFIX = "Update check:"
NOTICE_MATCH = "Update check"  # check_new keeps a line with this start ahead of its notice cap; it covers UNAVAILABLE too
UNAVAILABLE = "Update check couldn't confirm this update ({})."
SHRINK_LIMIT = 0.30
SECTION_DROP_LIMIT = 0.10
COMPARED = ("id", "path", "heading", "line_start", "line_end", "tokens")
NAMES_SHOWN, PROBLEMS_SHOWN = 5, 3


def shrunk(old_bytes, new_bytes):
    return old_bytes > 0 and new_bytes < SHRINK_LIMIT * old_bytes


def looks_like_html(text):
    top = text[:400].lower()
    return "<!doctype" in top or "<html" in top


def _saved_rows(data):
    """The saved index as a list of rows; None when it is missing or a line of it can't be read."""
    try:
        with open(os.path.join(data, "sections.jsonl"), encoding="utf-8") as f:
            return [json.loads(line) for line in f]
    except (FileNotFoundError, ValueError):
        return None


def _by_page(rows):
    out = {}
    for r in rows:
        out.setdefault(str(r.get("path")), []).append([r.get(k) for k in COMPARED])
    return out


def _index_problem(saved, expected):
    a, b = _by_page(saved), _by_page(expected)
    differing = sorted(p for p in set(a) | set(b) if a.get(p) != b.get(p))
    if not differing:
        return None
    more = len(differing) - NAMES_SHOWN
    return f"the index doesn't match {len(differing)} page(s): {', '.join(differing[:NAMES_SHOWN])}{f' and {more} more' if more > 0 else ''}"


def _check_vectors(rows, result):
    """A library that can't use vectors says so in a note; one that can has them checked."""
    if os.environ.get("JEV_SEMANTIC") == "off":
        why = "JEV_SEMANTIC=off"
    else:
        try:
            import semantic
        except ImportError as e:  # semantic.py needs numpy, which a stranger's install may not have
            why = type(e).__name__
        else:
            ok, why = semantic.available()
            if ok:
                stale = semantic.stale(rows)
                if stale:  # the failure line gives the command, so the reason's own hint would repeat it
                    result["problems"].append(stale.replace("; run refresh.sh", ""))
                return
    result["notes"].append(f"routing is keyword-only ({why})")


def _check_pages(changed, added, now, result):
    """Blog posts aren't in pages.library(): they are converted from HTML by design and have no size to compare."""
    import pages
    lib = pages.library()
    run_folder = os.path.join(pages.DATA, "archive", (now or datetime.datetime.now(pages.UTC)).strftime("%Y-%m-%dT%H%M%SZ"), "changed")
    for slug in changed:
        if slug in lib:
            rel = os.path.relpath(lib[slug], pages.DATA)
            old = os.path.join(run_folder, rel)
            if os.path.exists(old) and shrunk(os.path.getsize(old), os.path.getsize(lib[slug])):
                result["problems"].append(f"{rel.replace(os.sep, '/')} shrank to under {SHRINK_LIMIT:.0%} of its old size")
    for slug in dict.fromkeys(list(changed) + list(added)):
        if slug in lib and looks_like_html(pages.body(lib[slug])):
            result["problems"].append(f"{os.path.relpath(lib[slug], pages.DATA).replace(os.sep, '/')} opens as HTML")


def _check(changed, added, before, now, result):
    # Imported here: these read the library path when imported, and check_new imports this file.
    import build_index, check_new, pages
    saved, expected = _saved_rows(pages.DATA), build_index.expected_rows()
    result["sections"], result["pages"] = len(saved or []), len({r.get("path") for r in saved or []})
    if not expected:
        result["problems"].append("the library has no pages")
    if not saved:
        result["problems"].append("the index is missing, empty or unreadable")
    if not (expected and saved):
        return
    problem = _index_problem(saved, expected)
    if problem:
        result["problems"].append(problem)
    _check_vectors(saved, result)
    _check_pages(changed, added, now, result)
    if before:
        count = len(check_new.headings())
        if count < (1 - SECTION_DROP_LIMIT) * len(before):
            result["problems"].append(f"the section count fell from {len(before):,} to {count:,}")


def run(changed=(), added=(), before=None, now=None):
    """The check, as a dict: state (passed, failed or unavailable), problems, notes, sections and pages. Never raises."""
    result = {"state": "passed", "problems": [], "notes": [], "sections": 0, "pages": 0}
    try:
        _check(changed, added, before, now, result)
        if result["problems"]:
            result["state"] = "failed"
    except Exception as e:
        result["state"] = "unavailable"
        result["notes"].append(type(e).__name__)
    return result


def notice_lines(result, changes):
    """What a reader sees. A pass or a note shows only when something changed; a failure or a check that couldn't run always shows."""
    import paths
    lines = [f"{NOTICE_PREFIX} {p}; run {paths.REFRESH}." for p in result["problems"][:PROBLEMS_SHOWN]]
    if result["state"] == "unavailable":
        return lines + [UNAVAILABLE.format(result["notes"][-1])]
    if changes:
        if result["state"] == "passed":
            lines.append(f"{NOTICE_PREFIX} {result['sections']:,} sections from {result['pages']:,} pages match the saved pages.")
        lines += [f"{NOTICE_PREFIX} {n}." for n in result["notes"]]
    return lines


def main():
    try:
        import pages
        if not pages.take_lock():
            print(f"{NOTICE_PREFIX} skipped, another check is running.")
            return 0
        try:
            result = run()
        finally:
            pages.drop_lock()
        for line in notice_lines(result, True):
            print(line)
    except Exception as e:
        print(UNAVAILABLE.format(type(e).__name__))
    return 0


if __name__ == "__main__":
    sys.exit(main())
