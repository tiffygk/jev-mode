#!/usr/bin/env python3
"""Build sections.jsonl: one row per heading across docs/, cookbooks/, patterns/ and blog/ (blog captures are kind vendor).

Each row: id, path, heading, level, line_start, line_end (1-based, inclusive), kind,
tokens (chars/4), caveats (scope notes inside the section), file_caveats (scope notes
anywhere in the file; a cookbook's "for clarity" note often sits in a later section
than the one it scopes), captions (diagram captions, image alt text).
"""
import json, os, re, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import CODE, DATA, REFRESH
ROOT = DATA
CAVEAT = re.compile(r"this walkthrough|for clarity|a real application|in a real (app|system)|in practice|"
                    r"for simplicity|to keep (it|this|the example) simple|note:|caveat|not (a|an) (rule|requirement)",
                    re.I)
CAPTION = re.compile(r"^\s*(!\[[^\]]*\]|<figcaption>|caption=|\*Figure|_Figure)", re.I)
SKIP = ("docs/cookbooks__", "docs/patterns__")  # MDX duplicates of cookbooks/ and patterns/


def blocked_blog_files():
    """Blog captures the local privacy checker refuses, as library paths (blog/x.txt). Empty when the owner's
    config is absent, so a stranger's clone indexes everything; every file when the config exists but the checker
    doesn't. Env overrides are for tests."""
    repo_copy = os.path.join(os.path.dirname(CODE), "scripts", "private_text_check.py")  # same default as refresh.sh
    checker = os.path.expanduser(os.environ.get("JEV_PRIVATE_CHECKER")
                                 or (repo_copy if os.path.exists(repo_copy) else "~/.claude/scripts/private_text_check.py"))
    config = os.path.expanduser(os.environ.get("JEV_PRIVATE_CONFIG")
                                or "~/.claude/jevaluate-library/private-sources.json")
    folder = os.path.join(ROOT, "blog")
    if not (os.path.exists(config) and os.path.isdir(folder)):
        return []
    files = [os.path.join(folder, f) for f in sorted(os.listdir(folder)) if f.endswith((".txt", ".md"))]
    if not files:
        return []
    if not os.path.exists(checker):  # the owner's config says check, but the checker is gone: fail closed
        print("NOTICE: the privacy checker is missing, so no blog file was indexed. Restore it, then rebuild.")
        return ["blog/" + os.path.basename(f) for f in files]
    r = subprocess.run([sys.executable, checker] + files, capture_output=True, text=True,
                       env=dict(os.environ, JEV_PRIVATE_CONFIG=config))
    bad = {line.split(":", 1)[0] for line in r.stdout.splitlines() if ":" in line}
    if r.returncode != 0 and not bad:  # the checker itself failed (bad config, crash): fail closed
        print("NOTICE: the privacy check failed, so no blog file was indexed. Fix the check, then rebuild.")
        return ["blog/" + os.path.basename(f) for f in files]
    return ["blog/" + os.path.basename(f) for f in files if f in bad]


def kind_of(path):
    if path.startswith("cookbooks/"):
        return "example"
    if path.startswith("patterns/"):
        return "pattern"
    if path.startswith("blog/"):
        return "vendor"
    name = path[len("docs/"):]
    if name.startswith("sdk"):
        return "sdk"
    if name.startswith(("demos", "legal")):
        return "other"
    return "reference"


def paragraphs_matching(lines, rx):
    out, buf = [], []
    for ln in lines + [""]:
        if ln.strip():
            buf.append(ln.strip())
        elif buf:
            para = " ".join(buf)
            if rx.search(para):
                out.append(para[:600])
            buf = []
    return out


PART_CHARS = 1600  # about 400 tokens


def blog_parts(path, lines):
    """A blog capture with no headings: sections of about 400 tokens cut at paragraph breaks, each headed
    'Part N: <its first eight words>', so a claim comes back as a small READ FULL section, not one page-sized extract."""
    paras, start = [], None
    for i, ln in enumerate(lines + [""]):
        if ln.strip() and start is None:
            start = i
        elif not ln.strip() and start is not None:
            paras.append((start, i - 1))
            start = None
    prose = lambda a, b: re.search(r"\b\w+(?:\W+\w+){6,}[^\w]*[.!?:][\"')\]*]*\s*$", " ".join(lines[a:b + 1]).strip())
    while paras and not prose(*paras[0]):  # page chrome before the first prose paragraph (menu, byline, date)
        paras.pop(0)
    groups = []
    for a, b in paras:
        size = len("\n".join(lines[a:b + 1]))
        if groups and groups[-1][2] + size <= PART_CHARS:
            groups[-1][1], groups[-1][2] = b, groups[-1][2] + size
        else:
            groups.append([a, b, size])
    file_cav = paragraphs_matching(lines, CAVEAT)
    rows = []
    for n, (a, b, _) in enumerate(groups):
        text = "\n".join(lines[a:b + 1])
        rows.append({
            "id": f"{os.path.splitext(path)[0]}#{n}", "path": path, "heading": f"Part {n + 1}: " + " ".join(text.split()[:8]),
            "level": 1, "line_start": a + 1, "line_end": b + 1, "kind": kind_of(path), "tokens": len(text) // 4,
            "caveats": paragraphs_matching(lines[a:b + 1], CAVEAT), "file_caveats": file_cav,
            "captions": [l.strip()[:200] for l in lines[a:b + 1] if CAPTION.match(l)],
        })
    return rows


def sections(path):
    lines = open(os.path.join(ROOT, path), encoding="utf-8").read().split("\n")
    heads, fence = [], False
    for i, ln in enumerate(lines):
        if ln.lstrip().startswith(("```", "~~~")):
            fence = not fence
            continue
        m = re.match(r"^(#{1,4})\s+(.+?)\s*$", ln)
        if m and not fence and not ln.startswith(">"):
            heads.append((i, len(m.group(1)), m.group(2).strip()))
    if not heads and path.startswith("blog/"):
        return blog_parts(path, lines)
    if not heads:
        heads = [(0, 1, os.path.basename(path))]
    file_cav = paragraphs_matching([l for l in lines if not l.startswith(">")], CAVEAT)
    rows = []
    for n, (i, lvl, h) in enumerate(heads):
        end = heads[n + 1][0] - 1 if n + 1 < len(heads) else len(lines) - 1
        body = lines[i:end + 1]
        text = "\n".join(body)
        rows.append({
            "id": f"{os.path.splitext(path)[0]}#{n}", "path": path, "heading": h, "level": lvl,
            "line_start": i + 1, "line_end": end + 1, "kind": kind_of(path),
            "tokens": len(text) // 4,
            "caveats": paragraphs_matching(body, CAVEAT),
            "file_caveats": file_cav,
            "captions": [l.strip()[:200] for l in body if CAPTION.match(l)],
        })
    return rows


def main(prepare=True):
    if prepare:  # migrate old pages and re-clean after a cleaner version change; --no-prepare when the caller just did
        import pages
        pages.prepare()
        for slug, path in pages.library().items():
            if pages.cleaner_of(path) == f"failed:{pages.clean.VERSION}" and slug not in pages.FAILED_NOW:
                print(f"NOTICE: could not clean {os.path.relpath(path, ROOT).replace(os.sep, '/')} (cleaner failed {pages.clean.VERSION}; the raw text is indexed)")
    out = []
    blocked = blocked_blog_files()
    for b in blocked:
        print(f"NOTICE: {b} was not indexed: the local privacy check refused it. Fix the text, then rebuild.")
    for sub in ("docs", "cookbooks", "patterns", "blog"):
        for f in sorted((os.listdir(os.path.join(ROOT, sub)) if os.path.isdir(os.path.join(ROOT, sub)) else [])):
            p = f"{sub}/{f}"
            if f.endswith((".md", ".txt") if sub == "blog" else ".md") and not p.startswith(SKIP) and p not in blocked:
                out += sections(p)
    if not out:
        sys.exit(f"no pages in {ROOT}; run {REFRESH}")
    try:
        import semantic
        semantic.clear()  # vectors from an older index must never outlive it
    except Exception:
        pass
    with open(os.path.join(ROOT, "sections.jsonl"), "w") as fh:
        for r in out:
            fh.write(json.dumps(r) + "\n")
    print(f"{len(out)} sections from {len({r['path'] for r in out})} files")
    try:
        import sources
        sources.write(blocked, data=ROOT)  # this build's own folder, whatever a cached module points at
    except Exception as e:  # the list of sources is a courtesy; the index is already written
        print(f"NOTICE: SOURCES.md was not written ({type(e).__name__}).")
    embed(out)


def embed(rows):
    """Write the semantic index beside sections.jsonl; a missing model only skips it."""
    try:
        import semantic
        semantic.ALLOW_DOWNLOAD = True  # the first refresh downloads the model once
        ok, why = semantic.available()
        if ok:
            texts = []
            for r in rows:
                lines = open(os.path.join(ROOT, r["path"]), encoding="utf-8").read().split("\n")
                texts.append(semantic.section_text(r, lines))
            semantic.build(rows, texts)
            print(f"semantic index: {len(rows)} sections, {semantic.model_id()}")
        else:
            print(f"semantic index skipped: {why}")
    except Exception as e:
        print(f"semantic index skipped: {type(e).__name__}: {e}")


if __name__ == "__main__":
    main(prepare="--no-prepare" not in sys.argv[1:])
