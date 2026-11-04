#!/usr/bin/env python3
"""Check that every quote in a jevaluate-report file is real: docs quotes against the Jev Sources library, code
quotes against the repo at the front-matter commit.

  trace_check.py <file.md> [--checkout <clone of the repo>] [--library <Jev Sources data folder>]

A quote is a double-quoted passage of three or more words, an inline code span holding a space, or a fenced code
block. It belongs to the nearest link before it in its paragraph (else the first link after it); a fenced block
belongs to the last link in the paragraph just above it; a quote wrapped around a link belongs to that link, and
each list item is a paragraph. A quote not found at its own link passes when another checked link in the same
paragraph holds it. A quote whose link is a docs.typesafe.ai page or a
typesafe.ai/blog post must be on that page in the library (--library, else $JEV_SOURCES_DATA, else
~/.claude/jev-sources-data). A quote whose link is a blob permalink of the report's repo at its commit must be in
that file at that commit, inside the linked lines when the link names them; files are read with `git show` from
--checkout, which must hold the commit. Quotes linked anywhere else are listed as "unchecked", never failed.

Matching mirrors jev-sources' read.py --check-quote: whitespace, *, _, backticks and | are ignored, so are quote
marks and sentence punctuation at a quote's ends and the case of its first letter; an ellipsis (..., ... or [...],
or a fenced-block line holding only one) splits a quote into parts found in order; a part may not start or end
inside a word or number.

Prints one line per finding, "<rule>: <line>: <why>" (rules docs-page, docs-quote, code-file, code-quote), one
"unchecked: <line>: ..." line per quote linked elsewhere, then "counts docs N, code M, unchecked K".
Exit 0 when every checked quote is found, 1 on a finding, 2 when the library or checkout can't be used.
Why: review agents add facts to a report, and a quote that reads right can still be made up.
"""
import argparse, os, re, subprocess, sys

FENCE = re.compile(r"^\s*(```|~~~)")
LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
LINK_DEF = re.compile(r"^\s{0,3}\[([^\]]+)\]:\s*<?(\S+?)>?(?:\s+.*)?$")
INLINE_LINK = re.compile(r"\[((?:[^\[\]]|\[[^\]]*\])*)\]\(\s*<?([^)\s>]+)>?(?:\s+(?:\"[^\"]*\"|'[^']*'))?\s*\)")
REF_LINK = re.compile(r"\[((?:[^\[\]]|\[[^\]]*\])*)\]\[([^\]]*)\]")
AUTO_LINK = re.compile(r"<(https?://[^>\s]+)>")
CODE_SPAN = re.compile(r"(`+)(.+?)\1", re.S)
MAX_PARA = 20000
STRAIGHT = re.compile(r"\"([^\"]+)\"")
CURLY = re.compile(r"“([^”]+)”")
DOCS = re.compile(r"^https?://docs\.typesafe\.ai/([^#?]*)", re.I)
BLOG = re.compile(r"^https?://(?:www\.)?typesafe\.ai/blog/([^#?/]+)/?(?:[#?].*)?$", re.I)
BLOB = re.compile(r"^https?://github\.com/([^/]+)/([^/]+)/blob/([^/]+)/([^#?]+)(?:\?[^#]*)?(?:#L(\d+)(?:-L(\d+))?)?$", re.I)
SAFE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*(/[A-Za-z0-9][A-Za-z0-9_.-]*)*$")
ELISION = re.compile(r"\[?(?:\.\.\.|…)\]?")
ELISION_LINE = re.compile(r"^\s*\[?(?:\.\.\.|…)\]?\s*$")
EDGE = "\"'“”‘’.,;:!? \t\r\n"
SKIP = re.compile(r"[\s*_`|]")  # | too, so a quote can join a table row's cells


def front_matter(lines):
    """(fields, index of the first body line)."""
    if not lines or lines[0].strip() != "---":
        return {}, 0
    fm = {}
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return fm, i + 1
        m = re.match(r"^([A-Za-z_]+):\s*(.*)$", lines[i])
        if m:
            fm[m.group(1)] = m.group(2).strip().strip('"')
    return {}, 0


def kept(text):
    """(text without whitespace, *, _ and backticks, a backslash before them, or a blockquote > at a line's start; the
    original index of each kept character)."""
    out, idx, line_start = [], [], True
    for i, ch in enumerate(text):
        if ch == "\n":
            line_start = True
        elif line_start and ch == ">":
            continue
        elif not ch.isspace():
            line_start = False
        if SKIP.match(ch) or (ch == "\\" and i + 1 < len(text) and SKIP.match(text[i + 1])):
            continue
        out.append(ch)
        idx.append(i)
    return "".join(out), idx


def parts_of(quote, fenced=False):
    if fenced:
        chunks, cur = [], []
        for ln in quote.split("\n"):
            if ELISION_LINE.match(ln):
                chunks.append("\n".join(cur))
                cur = []
            else:
                cur.append(ln)
        chunks.append("\n".join(cur))
        return [p for p in (kept(c)[0] for c in chunks) if p]
    return [p for p in (kept(c.strip(EDGE))[0] for c in ELISION.split(quote)) if p]


def joins(nxt, ch):
    """Does the text go on past the quote's end character ch? nxt is the next two characters, nearest first."""
    return nxt[0].isalnum() or (ch.isdigit() and nxt[0] in ".," and nxt[1].isdigit())


def found(text, parts):
    """The original index where the parts start, all found in order in text, or None."""
    flat, idx = kept(text)
    start, first = 0, None
    for want in parts:
        best = None
        for w in {want, want[0].swapcase() + want[1:]}:
            pos = start - 1
            while True:
                pos = flat.find(w, pos + 1)
                if pos < 0:
                    break
                a, b = idx[pos], idx[pos + len(w) - 1]
                before = text[max(0, a - 2):a][::-1].ljust(2)
                after = text[b + 1:b + 3].ljust(2)
                if (w[0].isalnum() and joins(before, w[0])) or (w[-1].isalnum() and joins(after, w[-1])):
                    continue
                if best is None or pos < best:
                    best = pos
                break
        if best is None:
            return None
        if first is None:
            first = idx[best]
        start = best + len(want)
    return first


def blocks(body, offset):
    """Paragraphs and fenced blocks, in order: (kind, first file line, text, the paragraph just above or None)."""
    out, para, para_start, fence, fence_start, fence_mark, last_para = [], [], 0, None, 0, "", None
    for n, ln in enumerate(body, offset + 1):
        if fence is not None:
            if ln.strip().startswith(fence_mark):
                out.append(("fence", fence_start, "\n".join(fence), last_para))
                fence, last_para = None, None
            else:
                fence.append(ln)
            continue
        m = FENCE.match(ln)
        if m:
            if para:
                last_para = ("para", para_start, "\n".join(para), None)
                out.append(last_para)
                para = []
            fence, fence_start, fence_mark = [], n + 1, m.group(1)
            continue
        if not ln.strip() or LINK_DEF.match(ln):
            if para:
                last_para = ("para", para_start, "\n".join(para), None)
                out.append(last_para)
                para = []
            elif not ln.strip():
                pass
            continue
        if para and LIST_ITEM.match(ln):  # each list item is its own paragraph
            last_para = ("para", para_start, "\n".join(para), None)
            out.append(last_para)
            para = []
        if not para:
            para_start = n
            last_para = None
        para.append(ln)
    if para:
        out.append(("para", para_start, "\n".join(para), None))
    return out


def mask(text, spans):
    t = list(text)
    for a, b in spans:
        t[a:b] = " " * (b - a)
    return "".join(t)


def links_in(text, defs):
    """(start, end, url) for every link in a paragraph, and the spans to hide when looking for quotes."""
    found_links, hide = [], []
    for m in INLINE_LINK.finditer(text):
        found_links.append((m.start(), m.end(), m.group(2)))
        hide.append((m.start(2), m.end(2)))
    for m in REF_LINK.finditer(text):
        ref = (m.group(2) or m.group(1)).strip().lower()
        if ref in defs:
            found_links.append((m.start(), m.end(), defs[ref]))
    for m in AUTO_LINK.finditer(text):
        found_links.append((m.start(), m.end(), m.group(1)))
        hide.append((m.start(1), m.end(1)))
    return sorted(found_links), hide


def quotes_in(text, hide):
    """(start, end, quote text) for each quote in a paragraph."""
    out, spans = [], []
    for m in CODE_SPAN.finditer(mask(text, hide)):
        spans.append((m.start(), m.end()))
        body = m.group(2).strip()
        if re.search(r"\s", body):
            out.append((m.start(), m.end(), body))
    plain = mask(text, hide + spans)
    for rx in (STRAIGHT, CURLY):
        for m in rx.finditer(plain):
            q = re.sub(r"\[((?:[^\[\]]|\[[^\]]*\])*)\]\([^)]*\)", r"\1", text[m.start(1):m.end(1)])
            if len(q.split()) >= 3:
                out.append((m.start(), m.end(), q))
    return sorted(out)


def owner(links, a, b):
    inside = [u for s, e, u in links if s >= a and e <= b]  # a quote wrapped around its own link
    if inside:
        return inside[0]
    before = [u for s, e, u in links if e <= a]
    if before:
        return before[-1]
    after = [u for s, e, u in links if s >= b]
    return after[0] if after else None


def library_path(url, lib):
    """(path under the library, readable name) for a docs or blog URL, or None for any other URL."""
    m = DOCS.match(url)
    if m:
        slug = m.group(1).strip("/")
        slug = slug[:-3] if slug.endswith(".md") else slug
        if not slug:
            slug = "index"
        if not SAFE.match(slug):
            return "", "docs.typesafe.ai/" + slug
        for kind in ("cookbooks", "patterns"):
            if slug.startswith(kind + "/"):
                return os.path.join(lib, kind, slug[len(kind) + 1:] + ".md"), "docs.typesafe.ai/" + slug
        return os.path.join(lib, "docs", slug.replace("/", "__") + ".md"), "docs.typesafe.ai/" + slug
    m = BLOG.match(url)
    if m:
        slug = m.group(1)
        if not SAFE.match(slug):
            return "", "typesafe.ai/blog/" + slug
        return os.path.join(lib, "blog", slug + ".txt"), "typesafe.ai/blog/" + slug
    return None


def short(q):
    q = " ".join(q.split())
    q = q if len(q) <= 60 else q[:57] + "..."
    return clean(q)


def clean(s):
    """Report text as printable characters only, so a control character from a quoted file can't reach the terminal."""
    return "".join(c if c.isprintable() else "?" for c in str(s))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("file")
    ap.add_argument("--checkout", help="a clone of the report's repo that holds its commit")
    ap.add_argument("--library", help="the Jev Sources data folder")
    a = ap.parse_args()
    lib = a.library or os.environ.get("JEV_SOURCES_DATA") or os.path.expanduser("~/.claude/jev-sources-data")
    lines = open(a.file, encoding="utf-8").read().split("\n")
    fm, start = front_matter(lines)
    m = re.match(r"^https?://github\.com/([^/\s]+)/([^/\s]+?)(?:\.git)?/?$", fm.get("repo", ""))
    owner_repo = (m.group(1).lower(), m.group(2).lower()) if m else None
    commit = fm.get("commit", "").lower()
    body = lines[start:]
    defs = {}
    for ln in body:
        d = LINK_DEF.match(ln)
        if d:
            defs[d.group(1).strip().lower()] = d.group(2)

    checks, too_long = [], []  # checks: (line, quote, url, fenced); too_long: first lines of skipped paragraphs
    for kind, first, text, above in blocks(body, start):
        if kind == "fence":
            if above is None:
                continue
            links, _ = links_in(above[2], defs)
            if links:
                checks.append((first, text, links[-1][2], True, [u for _, _, u in links]))
            continue
        if len(text) > MAX_PARA:  # the link and code-span patterns slow sharply on very long runs of brackets or backticks
            too_long.append(first)
            continue
        links, hide = links_in(text, defs)
        if not links:
            continue
        for qa, qb, q in quotes_in(text, hide):
            url = owner(links, qa, qb)
            if url:
                checks.append((first + text.count("\n", 0, qa), q, url, False, [u for _, _, u in links]))

    findings, n_docs, n_code = [], 0, 0
    unchecked = [f"unchecked: {line}: paragraph over {MAX_PARA:,} characters, not scanned for quotes" for line in too_long]
    if not os.path.isdir(lib) and any(library_path(u, lib) for _, _, u, _, _ in checks):
        print(f"no Jev Sources library at {lib}; pass --library or run jev-sources' refresh", file=sys.stderr)
        return 2
    code = [c for c in checks if (lambda b: b and owner_repo and (b.group(1).lower(), b.group(2).lower()) == owner_repo
                                  and b.group(3).lower() == commit)(BLOB.match(c[2]))]
    if code:
        if not a.checkout:
            print(f"{len(code)} code quote(s) need --checkout <a clone of {clean(fm.get('repo'))}>", file=sys.stderr)
            return 2
        if not re.fullmatch(r"[0-9a-f]{40}", commit):  # never hand git an option-shaped value from the report
            print(f"front-matter commit {clean(commit)!r} is not 40 hex characters", file=sys.stderr)
            return 2
        r = subprocess.run(["git", "-C", a.checkout, "cat-file", "-e", commit + "^{commit}"], capture_output=True)
        if r.returncode != 0:
            print(f"{clean(a.checkout)} does not hold commit {commit}; fetch it first", file=sys.stderr)
            return 2

    pages, files = {}, {}

    def verdict(url, q, parts, line):
        """(kind, finding or None) for one quote at one link; kind is docs, code or None for a link not checked."""
        lp = library_path(url, lib)
        if lp is not None:
            path, name = lp
            if path not in pages:
                ok = path and os.path.realpath(path).startswith(os.path.realpath(lib) + os.sep) and os.path.isfile(path)
                pages[path] = open(path, encoding="utf-8").read() if ok else None
            if pages[path] is None:
                return "docs", f"docs-page: {line}: {clean(name)} is not in the Jev Sources library; refresh it, or cite a page it holds"
            if found(pages[path], parts) is None:
                return "docs", f"docs-quote: {line}: \"{short(q)}\" is not on {clean(name)}"
            return "docs", None
        b = BLOB.match(url)
        if not (b and (b.group(1).lower(), b.group(2).lower()) == owner_repo and b.group(3).lower() == commit):
            return None, None
        path = b.group(4)
        if path not in files:
            r = subprocess.run(["git", "-C", a.checkout, "show", f"{commit}:{path}"], capture_output=True)
            files[path] = r.stdout.decode("utf-8", "replace") if r.returncode == 0 else None
        text = files[path]
        if text is None:
            return "code", f"code-file: {line}: {clean(path)} does not exist at {commit[:7]}"
        if b.group(5):
            lo, hi = int(b.group(5)), int(b.group(6) or b.group(5))
            if found("\n".join(text.split("\n")[lo - 1:hi]), parts) is None:
                at = found(text, parts)
                where = (f"it is at line {text.count(chr(10), 0, at) + 1}, outside L{lo}" + (f"-L{hi}" if hi != lo else "")
                         if at is not None else f"it is not in {clean(path)} at {commit[:7]}")
                return "code", f"code-quote: {line}: \"{short(q)}\" is not in the linked lines; {where}"
        elif found(text, parts) is None:
            return "code", f"code-quote: {line}: \"{short(q)}\" is not in {clean(path)} at {commit[:7]}"
        return "code", None

    for line, q, url, fenced, others in checks:
        parts = parts_of(q, fenced)
        if not parts:
            continue
        kind, finding = verdict(url, q, parts, line)
        if kind is None:
            host = re.sub(r"^https?://([^/]+).*$", r"\1", url) if url.startswith("http") else url
            unchecked.append(f"unchecked: {line}: \"{short(q)}\" ({clean(host)})")
            continue
        n_docs += kind == "docs"
        n_code += kind == "code"
        # not at its nearest link: it passes if another checked link in its paragraph holds it
        if finding and not any(u != url and verdict(u, q, parts, line) in (("docs", None), ("code", None)) for u in others):
            findings.append(finding)

    for f in findings + unchecked:
        print(f)
    print(f"counts docs {n_docs}, code {n_code}, unchecked {len(unchecked)}")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
