#!/usr/bin/env python3
"""List every place that cites a TypeSafe page or section the last refresh changed, with a proposed class:
superseded (a redirect target or a section that now covers it, named), obsolete (gone, nothing replaces it), or
changed (the cited page changed: read the archived and current copies and decide whether the fact is outdated).
Reads <data>/section_changes.json; writes <data>/STALE_CITATIONS.md. Usage: citations.py [--root <repo>]"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import CODE, DATA
import pages

SCAN = ("jev-sources", "shared", "jevaluate", "jevaluate-harness", "jevaluate-eval", "jev-lens", "ratings", "README.md")
EXT = (".md", ".json", ".py", ".txt")
PATH_RX = re.compile(r"\b((?:docs|cookbooks|patterns)/[A-Za-z0-9_.-]+?)\.md(?:#([^`\"')\]\n|]+))?")
URL_RX = re.compile(r"https://docs\.typesafe\.ai/([A-Za-z0-9_./-]+?)(?:\.md)?(?:#([A-Za-z0-9-]+))?(?=[\s)\]`\"'>,|]|$)")
TICK_RX = re.compile(r"`([a-z0-9_.-]+(?:/[a-z0-9_.-]+)*)`")
FLOOR = 0.35


def anchor(h):
    return re.sub(r"[^a-z0-9]+", "-", h.lower()).strip("-")


def find(root, known, scan=SCAN):
    for top in scan:
        base = os.path.join(root, top)
        if os.path.isfile(base):
            files = [base]
        else:
            files = [os.path.join(d, f) for d, _, fs in os.walk(base) for f in fs
                     if f.endswith(EXT) and "__pycache__" not in d and ".pytest_cache" not in d]
        for f in sorted(files):
            for i, ln in enumerate(open(f, encoding="utf-8", errors="ignore"), 1):
                for m in PATH_RX.finditer(ln):
                    yield f, i, pages.slug_of_path(m.group(1) + ".md"), (m.group(2) or "").strip() or None, ln.strip()
                for m in URL_RX.finditer(ln):
                    yield f, i, m.group(1).strip("/"), m.group(2), ln.strip()
                for m in TICK_RX.finditer(ln):
                    if m.group(1) in known:
                        yield f, i, m.group(1), None, ln.strip()


def nearest(query, rows):
    try:
        import semantic
        sc, _ = semantic.scores(query, rows)
    except Exception:
        return None
    if not sc:
        return None
    best = max(rows, key=lambda r: sc.get(r["id"], 0))
    return f"{pages.slug_of_path(best['path'])}#{best['heading']}" if sc.get(best["id"], 0) >= FLOOR else None


def fit_head(head, known_heads):
    """A heading captured past its end in prose is cut back to the longest known heading it starts with."""
    if not head or any(h == head or anchor(h) == head for h in known_heads):
        return head
    starts = [h for h in known_heads if head.startswith(h)]
    return max(starts, key=len) if starts else head


def judge(slug, head, ch, new_heads, near, text=""):
    """near(query, only_slug=None, only_added=False) -> 'slug#heading' or None."""
    moved, removed, changed = ch.get("moved", {}), set(ch.get("removed", [])), set(ch.get("changed", []))
    gone = {(pages.slug_of_path(p), h) for p, h in ch.get("removed_sections", [])}
    added_here = [h for p, h in ch.get("added_sections", []) if pages.slug_of_path(p) == slug]
    if slug in moved:
        return "superseded", moved[slug]
    if slug in removed:
        r = near(f"{slug} {head or ''} {text}")
        return ("superseded", r) if r else ("obsolete", "")
    if head:
        if any(h == head or anchor(h) == head for h in new_heads.get(slug, [])):
            if slug not in changed:
                return None, None
            if added_here:  # the cited section stayed, but the page grew a section that may now hold the fact
                r = near(text, only_slug=slug, only_added=True)
                if r:
                    return "superseded", r
            return "changed", f"{slug}#{head}"
        if any(g[0] == slug and (g[1] == head or anchor(g[1]) == head) for g in gone):
            elsewhere = [s for s, hs in new_heads.items() if head in hs]
            if elsewhere:
                return "superseded", f"{elsewhere[0]}#{head}"
            r = near(f"{slug} {head} {text}")
            return ("superseded", r) if r else ("obsolete", "")
        return None, None
    return ("changed", slug) if slug in changed else (None, None)


def report(root=None, near=None):
    given, root = root, root or os.path.dirname(CODE)
    if os.path.isdir(os.path.join(root, "jevaluate")):
        scan = SCAN
    elif os.path.isdir(os.path.join(root, "jev-sources")):
        scan = ("jev-sources",)
    elif given:  # an explicit --root that holds neither skill is a mistake, not a plugin install
        raise SystemExit(f"citations: {given} holds neither jevaluate/ nor jev-sources/")
    else:  # a plugin install has no repo around it, and its folder may not be named jev-sources: scan the skill's own
        root, scan = CODE, (".",)
    ch = json.load(open(os.path.join(DATA, "section_changes.json")))
    try:
        rows = [json.loads(l) for l in open(os.path.join(DATA, "sections.jsonl"))]
    except OSError:
        rows = []
    new_heads = {}
    for r in rows:
        new_heads.setdefault(pages.slug_of_path(r["path"]), []).append(r["heading"])
    old_heads = {}
    for p, h in ch.get("removed_sections", []):
        old_heads.setdefault(pages.slug_of_path(p), []).append(h)
    known = set(new_heads) | set(ch.get("removed", [])) | set(ch.get("moved", {}))
    added = {(p, h) for p, h in ch.get("added_sections", [])}

    def default_near(query, only_slug=None, only_added=False):
        pool = [r for r in rows if (only_slug is None or pages.slug_of_path(r["path"]) == only_slug)
                and (not only_added or (r["path"], r["heading"]) in added)]
        return nearest(query, pool) if pool else None

    near = near or default_near
    out = []
    for f, i, slug, head, text in find(root, known, scan):
        head = fit_head(head, new_heads.get(slug, []) + old_heads.get(slug, []))
        cls, repl = judge(slug, head, ch, new_heads, near, text)
        if cls:
            note = "dated record: flag only" if "/ratings/" in f.replace(os.sep, "/") else ""
            out.append({"file": os.path.relpath(f, root), "line": i, "cites": f"{slug}#{head}" if head else slug,
                        "class": cls, "replacement": repl, "note": note})
    path = os.path.join(DATA, "STALE_CITATIONS.md")
    with open(path, "w") as fh:
        fh.write(f"# Citations to check after the refresh of {ch.get('date', '')}\n\n"
                 "For each `changed` row, compare the archived copy (archive/<run time>/changed/) with the current page "
                 "and mark it outdated or still true. Locked files change only through their own pull request.\n\n"
                 "| File:line | Cites | Class | Replacement | Note |\n|---|---|---|---|---|\n")
        for r in out:
            fh.write(f"| {r['file']}:{r['line']} | `{r['cites']}` | {r['class']} | {r['replacement']} | {r['note']} |\n")
    return out, path


if __name__ == "__main__":
    a = sys.argv[1:]
    rows, path = report(a[a.index("--root") + 1] if "--root" in a else None)
    print(f"{len(rows)} citation(s) to check: {path}")
