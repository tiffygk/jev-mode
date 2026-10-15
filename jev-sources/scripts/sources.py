"""<data>/SOURCES.md: every page the library holds, its address and when it was saved. Written after each index build."""
import datetime, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pages

DOCS_SITE = "https://docs.typesafe.ai/"
BLOG_SITE = "https://typesafe.ai/blog/"


def _rows(blocked, data):
    rows = []
    for slug, path in sorted(pages.library(data).items()):
        rel = os.path.relpath(path, data)
        rows.append((rel, DOCS_SITE + slug, pages.saved_at(path), "yes"))
    folder = os.path.join(data, "blog")
    if os.path.isdir(folder):
        for f in sorted(os.listdir(folder)):
            if f.endswith((".txt", ".md")):
                rel = "blog/" + f
                when = pages.saved_at(os.path.join(folder, f))
                if rel in blocked:  # the file name is the slug and may carry a name: show neither
                    rows.append(("blog/(withheld)", "withheld", when, "not indexed (privacy check)"))
                else:
                    rows.append((rel, BLOG_SITE + os.path.splitext(f)[0], when, "yes"))
    return rows


def write(blocked=(), data=None):
    data = data or pages.DATA
    out = os.path.join(data, "SOURCES.md")
    lines = ["# What this library holds", "",
             "Written by the last index build. Saved times are UTC.", "",
             "| Page | Address | Saved | Indexed |", "|---|---|---|---|"]
    for rel, url, when, note in _rows(set(blocked), data):
        t = when.strftime("%Y-%m-%d %H:%M") if isinstance(when, datetime.datetime) else "unknown"
        lines.append(f"| {rel} | {url} | {t} | {note} |")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return out
