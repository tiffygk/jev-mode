#!/usr/bin/env python3
"""Print one source section in full, with the file's scope caveats and captions.

  python3 scripts/read.py 'cookbooks/rerank_typesafe#7'
  python3 scripts/read.py 'cookbooks/rerank_typesafe.md#Setup (cookbook example)'   a CITE AS line works too
  ... --extract "<terms>"   12 lines around each hit, capped at 1,500 tokens (marked as an extract)
  ... --check-quote "<quote>"   is the quote in that section? Prints one QUOTE FOUND / QUOTE NOT FOUND line, never the text;
                                a NOT FOUND line names another section of the same page that holds the quote, if one does

The first line is the citation to quote: SOURCE: <path>#<heading> | KIND | READ.
A section with a model or readiness limit gets a second line: APPLIES: needs <model> or newer | experimental (<source>).
"""
import json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import DATA, REFRESH
import usage_log
import applicability
ROOT = DATA
LABEL = {"reference": "reference rule", "pattern": "pattern", "example": "cookbook example", "sdk": "sdk reference",
         "vendor": "vendor claim", "other": "other"}
EXAMPLE_NOTE = ("JEV-SOURCES NOTE (not TypeSafe's words; never quote it): one build TypeSafe published. Its layout, call counts and diagrams are not API limits; "
                "check the scope notes below and the reference rules.")


_INDEX = {}


def _index():
    """The library index, read once per version of sections.jsonl (an answer check looks it up once per citation)."""
    path = os.path.join(ROOT, "sections.jsonl")
    try:
        st = os.stat(path)
        key = (path, st.st_mtime_ns, st.st_size, st.st_ctime_ns, st.st_ino)  # ctime moves on any write
        if _INDEX.get("key") != key:
            _INDEX.update(key=key, rows=[json.loads(l) for l in open(path)])
        return _INDEX["rows"]
    except FileNotFoundError:
        sys.exit(f"library index missing; run {REFRESH}")


def _rows(sid):
    """Every section a section id names. A numeric id (docs/primitives__box#2) names one. A path#heading, with or
    without .md and with or without a trailing (label) from CITE AS, names every section of that file with that
    heading, which is more than one where a page repeats a heading. Exits 1 when none matches."""
    sid = sid.strip()
    rows = _index()
    hit = [x for x in rows if x["id"] == sid]
    if hit:
        return hit
    if "#" in sid:
        path, heading = sid.split("#", 1)
        if not path.endswith((".md", ".txt")):
            path += ".md"
        heads = [heading]
        m = re.search(r" \((?:%s)(?:,[^()]*)?\)$" % "|".join(re.escape(x) for x in LABEL.values()), heading)
        if m:  # a trailing label counts only when it starts with one of ours ("(reference rule, experimental)" too)
            heads.append(heading[:m.start()])
        for h in heads:  # the whole text first: a heading may really end in a parenthesis
            hit = [x for x in rows if x["path"] == path and x["heading"] == h]
            if hit:
                return hit
    sys.exit(f"no section {sid!r}; run route.py to get ids")


def _row(sid):
    hit = _rows(sid)
    if len(hit) > 1:
        sys.exit(f"several sections named {hit[0]['heading']!r} in {hit[0]['path']}: use one of " + ", ".join(x["id"] for x in hit))
    r = hit[0]
    if not os.path.exists(os.path.join(ROOT, r["path"])):
        sys.exit(f"missing source {r['path']}; run {REFRESH}")
    return r


_ESCAPED = re.compile(r"\\([*_`\s\"])")  # a backslash before markup, a space or a quote mark (a reader's \" in a QUOTE)
_SKIP = re.compile(r"[\s*_`]")


TYPO = str.maketrans({"\u2019": "'", "\u2018": "'", "\u201c": '"', "\u201d": '"', "\u2013": "-", "\u2014": "-"})  # curly quotes, dashes


def _squash(text):
    return _SKIP.sub("", _ESCAPED.sub(r"\1", text.translate(TYPO)))


def _kept(line):
    """(squashed line, the line column of each kept character); the squashing is _squash, with columns."""
    keep, cols = [], []
    for i, ch in enumerate(line):
        if _SKIP.match(ch) or (ch == "\\" and i + 1 < len(line) and _SKIP.match(line[i + 1])):
            continue
        keep.append(ch.translate(TYPO))
        cols.append(i)
    return "".join(keep), cols


LINK = re.compile(r'!?\[([^\]\n]*)\]\([^)\s]*(?:\s+"[^"]*")?\)')  # a Markdown link or image: matched as its text
_ELISION = re.compile(r"\[?(?:\.\.\.|…)\]?")
_EDGE = "\"'“”‘’.,;:!? \t\r\n"


def quote_parts(quote):
    """The quote's parts between elisions (..., … or [...]), squashed, each without the quote marks and the
    sentence punctuation a writer adds or drops at a quote's ends. [] means the quote is empty."""
    parts = (_squash(p.strip(_EDGE)) for p in _ELISION.split(LINK.sub(r"\1", quote)))
    return [p for p in parts if p]


def _joins(nxt, ch):
    """Does the page continue the quote's end character ch? nxt is the two page characters beyond it, nearest
    first. A letter or digit continues a word; a "." or "," then a digit continues a number ("0" in "0.5")."""
    return nxt[0].isalnum() or (ch.isdigit() and nxt[0] in ".," and nxt[1].isdigit())


def _find(text, lines, owner, cols, want, start):
    """The (first, last) index of want in text at or after start, not starting or ending inside a run of letters
    or digits or inside a number; the first letter may differ in case. None if absent."""
    best = None
    for w in {want, want[0].swapcase() + want[1:]}:
        pos = start - 1
        while True:
            pos = text.find(w, pos + 1)
            if pos < 0:
                break
            first, last = pos, pos + len(w) - 1
            head, tail = lines[owner[first]], lines[owner[last]]
            before = head[max(0, cols[first] - 2):cols[first]].rjust(2)
            after = tail[cols[last] + 1:cols[last] + 3].ljust(2)
            if (w[0].isalnum() and _joins(before[::-1], w[0])) or (w[-1].isalnum() and _joins(after, w[-1])):
                continue
            if best is None or first < best[0]:
                best = (first, last)
            break
    return best


_FLAT = {}


def _flat(r):
    """(lines, squashed text, line of each character, column of each character) of section r, kept per file version,
    since one answer check matches many quotes against the same sections."""
    path = os.path.join(ROOT, r["path"])
    if not os.path.exists(path):
        sys.exit(f"missing source {r['path']}; run {REFRESH}")
    st = os.stat(path)
    key = (path, r["line_start"], r["line_end"], st.st_mtime_ns, st.st_size, st.st_ctime_ns, st.st_ino)
    if key not in _FLAT:
        if len(_FLAT) > 2000:
            _FLAT.clear()
        lines = open(path, encoding="utf-8").read().split("\n")[r["line_start"] - 1:r["line_end"]]
        lines = [LINK.sub(r"\1", ln) for ln in lines]  # a quote of a link's text matches the page's [text](url)
        flat, owner, cols = [], [], []
        for i, ln in enumerate(lines):
            sq, c = _kept(ln)
            flat.append(sq)
            owner += [i] * len(sq)
            cols += c
        _FLAT[key] = (lines, "".join(flat), owner, cols)
    return _FLAT[key]


def _in_row(r, parts):
    """(line_no, line) where the quote's parts start in section r, all found in order; None if they are not."""
    lines, text, owner, cols = _flat(r)
    start, spans = 0, []
    for want in parts:
        span = _find(text, lines, owner, cols, want, start)
        if span is None:
            return None
        spans.append(span)
        start = span[1] + 1
    if not spans:
        return None
    i = owner[spans[0][0]]
    return r["line_start"] + i, lines[i]


def _page_rows(sid):
    """Every section of the page a page-only id names (docs/models.md or docs/models); [] for any other id."""
    sid = sid.strip()
    if "#" in sid:
        return []
    path = sid if sid.endswith((".md", ".txt")) else sid + ".md"
    return [x for x in _index() if x["path"] == path]


def check_quote(sid, quote):
    """(found, row, line_no, line): is the quote in the section sid names? When a heading repeats, every same-named
    section is checked and row is the one that holds it; a page-only id (docs/models.md) checks every section of
    that page. Matching ignores whitespace, *, _ and ` (and a backslash before them), quote marks and sentence
    punctuation at the quote's ends, and the case of its first letter; it is otherwise case-sensitive, and the
    quote may span lines. An elision (..., … or [...]) splits the quote into parts that must all be found, in
    order. A part must not start or end inside a run of letters or digits ("up to 5" is not in "up to 50").
    line_no is the file line the quote starts on.
    When it is not found, row is the first section checked and line_no and line are None."""
    parts = quote_parts(quote)
    rows = _page_rows(sid) or _rows(sid)
    for r in rows:
        at = _in_row(r, parts)
        if at:
            return True, r, at[0], at[1]
    return False, rows[0], None, None


def elsewhere_on_page(sid, quote):
    """(row, line_no, line) for the first other section of the cited page that holds the quote, or None. Run after
    check_quote finds nothing, so a quote cited under the wrong heading can be re-cited, not called unverified."""
    if _page_rows(sid):
        return None  # a page-only id already checked the whole page
    cited = _rows(sid)
    ids = {x["id"] for x in cited}
    parts = quote_parts(quote)
    for r in _index():
        if r["path"] == cited[0]["path"] and r["id"] not in ids:
            at = _in_row(r, parts)
            if at:
                return r, at[0], at[1]
    return None


def _url(path):
    """' | URL: <address>' from the page's saved header (a .md address loses its .md), or '' when it has none."""
    try:
        m = re.match(r"<!-- saved \S+ from (https?://\S+?)(?:\.md)? (?:\||-->)", open(os.path.join(ROOT, path), encoding="utf-8").readline())
    except OSError:
        return ""
    return f" | URL: {m.group(1)}" if m else ""


def render(sid, extract_terms=None):
    """The section as text. The first line is CITE AS: <path>#<heading> (<label>); from the second line on it is
    what read.py prints. extract_terms (a list) gives an extract instead of the full section. Does not log."""
    r = _row(sid)
    lines = open(os.path.join(ROOT, r["path"]), encoding="utf-8").read().split("\n")[r["line_start"] - 1:r["line_end"]]
    extract = extract_terms is not None
    if extract:
        terms = [t.lower() for t in extract_terms]
        keep = set()
        for i, ln in enumerate(lines):
            if any(t in ln.lower() for t in terms):
                keep.update(range(max(0, i - 6), min(len(lines), i + 6)))
        body = "\n".join(lines[i] for i in sorted(keep))[:6000]
    else:
        body = "\n".join(lines)
    label = LABEL[r["kind"]]
    out = [f"CITE AS: {r['path']}#{r['heading']} ({label})",
           f"SOURCE: {r['path']}#{r['heading']} | KIND: {label} | READ: {'extract, not a full read' if extract else 'full'}"
           + _url(r["path"])]
    if r["kind"] == "example":
        out.append(EXAMPLE_NOTE)
    ap = applicability.lookup(r["path"], r["heading"])
    if ap["needs"] or ap["status"]:
        out.append("APPLIES: " + " | ".join(([f"needs {ap['needs']} or newer"] if ap["needs"] else []) + ([ap["status"].replace("-", " ")] if ap["status"] else [])) + f" ({ap['source']})")
    out.append(f"(lines {r['line_start']}-{r['line_end']}, ~{r['tokens']} tokens)\n")
    out.append(body)
    cav = [c for c in r["file_caveats"] if c not in "\n".join(lines)]
    if cav:
        out.append("\n--- Scope notes elsewhere in this file (they may limit what this section shows) ---")
        out += ["- " + c for c in cav]
    if r["captions"]:
        out.append("\n--- Captions (diagram labels, not rules) ---")
        out += ["- " + c for c in r["captions"]]
    return "\n".join(out)


HEAD_MAX = 120  # the longest real heading is 75 characters; a longer one is cut and cited by its numeric id


def _safe(text):
    """Page text as printable characters only, so a control character on a saved page can't reach the terminal."""
    return "".join(c if c.isprintable() else "?" for c in text)


def _ref(r):
    """path#heading, plus the numeric id when the page repeats that heading or the heading is cut at HEAD_MAX."""
    several = len([x for x in _index() if x["path"] == r["path"] and x["heading"] == r["heading"]]) > 1
    cut = len(r["heading"]) > HEAD_MAX
    head = r["heading"][:HEAD_MAX] + "..." if cut else r["heading"]
    return _safe(f"{r['path']}#{head}") + (f" [{r['id']}]" if several or cut else "")


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: read.py <section id> [--extract terms | --check-quote \"<quote>\" | --check-quote -]")
    sid = sys.argv[1]
    if "--check-quote" in sys.argv:
        i = sys.argv.index("--check-quote")
        quote = sys.stdin.read() if sys.argv[i + 1:] == ["-"] else " ".join(sys.argv[i + 1:])  # "-": the quote comes on stdin
        if not quote_parts(quote):
            print("usage: read.py <section id> --check-quote \"<quote>\" (the quote is empty)", file=sys.stderr)
            return 2
        found, r, line_no, line = check_quote(sid, quote)
        page_only = bool(_page_rows(sid))
        usage_log.write("check_quote", id=r["id"], found=found)
        if found:
            print(f"QUOTE FOUND | {_ref(r)} | line {line_no}: {_safe(line.strip()[:200])}")
            return 0
        other = elsewhere_on_page(sid, quote)
        if other:
            o, o_line_no, o_line = other
            print(f"QUOTE NOT FOUND | {_ref(r)} | found on this page under {_ref(o)}, line {o_line_no}: "
                  f"{_safe(o_line.strip()[:200])} | cite that section")
            return 1
        print(f"QUOTE NOT FOUND | {_safe(r['path']) if page_only else _ref(r)}")
        return 1
    terms = sys.argv[sys.argv.index("--extract") + 1:] if "--extract" in sys.argv else None
    text = render(sid, terms)
    print(text.split("\n", 1)[1])  # the CITE AS line is for jev.py's bundle; this command's output starts at SOURCE
    usage_log.write("read", id=sid, extract=terms is not None, tokens=_row(sid)["tokens"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
