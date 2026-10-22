#!/usr/bin/env python3
"""Check every docs quote in an answer against the section it cites. The answer comes on stdin.
  python3 scripts/check_answer.py < answer.md

A quote is text of 4 or more words in double quotes (straight or curly), outside code spans. Its citations are the
library ids (docs/, cookbooks/, patterns/, blog/) in the same bullet, table row or paragraph; with none there, the
citations of its parent bullet and every other citation under the same heading, before or after it (a table under
its lead-in line, a "Sources:" line after a list). Prints one row per quote:
  FOUND | <first words> | <section>
  NOT FOUND | <first words> | cited <section>[ | found under <section>]
  BAD CITE | <first words> | <citation>          (no section has that id)
  UNCITED | <first words> | no citation under this heading
  LABELED | <first words> | <section>           (not found, but labeled unverified or unconfirmed beside it)
then one summary line. Quotation marks are for the docs' words only: every quote is checked, whoever's words it holds
(the user's own error, log or message goes in backticks, which are not checked). With no citation anywhere, a quote
holding a specific fact is still checked. An answer with no library citation that does not mention Jev is not a Jev
answer: nothing is printed and it passes.
unquoted_facts(text) lists, apart from the quote check, each sentence that states a specific Jev fact (a price, a
number with a unit, a status code, a backticked name) with no quote or citation on its line, before "My read" and
not marked unconfirmed: UNQUOTED | <first words>. They never change the exit code; the Stop hook asks once.
Exit 0 when every quote is FOUND or LABELED; 1 otherwise; 2 on bad usage. Never prints page text: a quote is shown
by its first 5 words, at most 60 characters."""
import os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import read as RD
import check_findings as CF
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "hooks"))
from jev_terms import JEV

MIN_WORDS = 4  # a shorter quoted string is a term or a name ("danger zone"), not a quote
MAX_SENTENCE = 500  # characters of one sentence the unquoted-fact check reads
MAX_CITE = 200  # characters of a bare citation tried against the index; a longer run is not a citation
MAX_CUTS = 10  # comma cuts tried on one bare citation
MAX_CITES = 30  # distinct citations read from one block
MAX_QUOTES = 200  # quotes checked in one answer; past it, one TOO MANY row fails the answer
UNCITED_WORDS = 8  # with no citation of its own, a shorter quoted phrase reads as a term, not a claimed quote
KINDS = r"(?:docs|cookbooks|patterns|blog)/"
TICKED = re.compile(r"`([^`\n]+)`")
BARE = re.compile(r"(?<![\w/`])(" + KINDS + r"[\w.-]+(?:#[^;()`\"*\n]*[^;()`\"*\s,])?)")
QUOTE = re.compile(r"\"([^\"\n]+)\"")
HEADING = re.compile(r"^\s{0,3}#{1,6}\s")
ITEM = re.compile(r"^\s{0,3}(?:[-*+]|\d+[.)])\s")
DOCS_URL = re.compile(r"https?://docs\.typesafe\.ai/([\w/-]+?)(?:\.md)?/?(?=[)#\s>\]]|$)")
NOFOLDER = re.compile(r"(?<![\w/`.-])([\w-]+\.(?:md|txt)#[^;()`\"*\n]*[^;()`\"*\s,])")
NESTED = re.compile(r"^\s+(?:[-*+]|\d+[.)])\s")
LABEL = re.compile(r"\b(?:unverified|unconfirmed)\b", re.I)
LABEL_NEXT = re.compile(r"^\s*(?:This|That|The) (?:quote|wording|line|figure)s? (?:is|are) (?:unverified|unconfirmed)\b", re.I)
CLAUSE_END = re.compile(r"[;.!?](?=\s|$)")
NOT_LABEL = re.compile(r"\b(?:not|no|nothing|never|none|isn't|aren't|without)\b[^.;:]{0,30}\b(?:unverified|unconfirmed)\b",
                       re.I)  # "Nothing here is unverified" labels nothing
DOCS_SAY = re.compile(r"\b(?:docs?|documentation|TypeSafe|reference|cookbook|guide|blog(?: post)?|page)\b[^\"]{0,40}$", re.I)
SENTENCE = re.compile(r"^[A-Z].*[.!?]$")
# unquoted facts: a Jev term and a specific in one sentence
FACT_TERM = re.compile(r"\b(?:Jevs?|Nouls?|System One|TypeSafe|SDK|API|endpoint|rate[ -]limits?|models?|alias|"
                       r"bills?|billed|charges?|priced?|pricing|context)\b", re.I)
FACT_NAME = re.compile(r"\b(?:Choice|Score|Box)\b")  # common words in lower case, question types when capitalized
SPECIFIC = re.compile(r"\b[a-z]+_[a-z_]+\b|\$\s?\d|\b\d[\d,.]{0,20}\s*(?:%|ms\b|seconds?\b|tokens?\b|requests?\b|options?\b|questions?\b|levels?\b|"
                      r"[KMGB]i?B\b|[KMB]\b|[MB]tok\b|dollars?\b|cents?\b|"
                      r"characters?\b|per\b|million\b|billion\b|k\b|MB\b)|\b[45]\d\d\b|`[^`\n]+`")
YOU_HEDGE = re.compile(r"\b(?:you|your)\b", re.I)  # about the person's own case, unless the sentence quotes a specific
HEDGED = re.compile(r"\b(?:unconfirmed|unverified|my read|I'd|I would)\b|(?:pages?|docs|sections?) I (?:read|routed)\b"
                    r"|\bI (?:didn't|did not|haven't|have not) (?:read|check|see)|\bthe docs (?:don't|do not) (?:say|show|cover|list)", re.I)
MY_READ = re.compile(r"^\s*(?:#+\s*|\*\*)My read\b", re.I)
ESCAPE = re.compile(r"\\([^\w\s])")
CURLY = str.maketrans({"\u201c": '"', "\u201d": '"', "\u201e": '"'})


def _blocks(text):
    """(heading number, block text, indent) for each bullet (with its indented lines), table row and paragraph; indent
    is a bullet's leading spaces, None for anything else."""
    out, cur, head, in_code = [], [], 0, False
    def close():
        if cur:
            m = ITEM.match(cur[0]) or NESTED.match(cur[0])
            out.append((head, " ".join(x.strip() for x in cur), len(cur[0]) - len(cur[0].lstrip()) if m else None))
            cur.clear()
    for line in text.split("\n"):
        if line.lstrip().startswith("```"):
            close()
            in_code = not in_code
            continue
        if in_code:
            continue
        if not line.strip():
            close()
        elif HEADING.match(line):
            close()
            head += 1
            out.append((head, line.lstrip("# ").strip(), None))  # a citation in a heading reaches the blocks under it
        elif line.lstrip().startswith("|") or ITEM.match(line) or NESTED.match(line):
            close()
            cur.append(line)
            if line.lstrip().startswith("|"):
                close()
        else:
            cur.append(line)
    close()
    return out


def _bare(cite):
    """A citation written without code marks runs to the end of its phrase; a heading may hold commas, so the longest
    prefix, cut at a comma, that names a section is the citation."""
    cut = cite = cite[:MAX_CITE]
    for _ in range(MAX_CUTS):
        if _resolve(cut):
            return cut
        if "," not in cut:
            break
        cut = cut.rsplit(",", 1)[0].rstrip()
    return cite


def _cites(block):
    """The library citations in a block: code spans that name a library id, bare ids (plain or in italics), and links
    to a docs.typesafe.ai page (which name that page)."""
    def first(xs):
        return list(dict.fromkeys(xs))[:MAX_CITES]
    found = first(s.strip() for s in TICKED.findall(block) if re.match(KINDS, s.strip()))
    found += first("docs/" + u.strip("/").replace("/", "__") + ".md" for u in DOCS_URL.findall(block))
    plain = TICKED.sub(" ", block)
    found += [_bare(c) for c in first(BARE.findall(plain))]
    found += [_bare(k + c) for c in first(NOFOLDER.findall(plain)) for k in ("docs/", "cookbooks/", "patterns/", "blog/")
              if _resolve(_bare(k + c))]  # "models.md#Current models", written without its folder
    return first(found)


_CACHE = {}


def _idx():
    """The library index, read once per change of sections.jsonl (one answer looks it up many times)."""
    path = os.path.join(RD.ROOT, "sections.jsonl")
    stamp = os.path.getmtime(path) if os.path.exists(path) else None
    if _CACHE.get("stamp") != stamp or "rows" not in _CACHE:
        _CACHE.update(stamp=stamp, rows=RD._index())
    return _CACHE["rows"]


def _norm(s):
    return " ".join(re.sub(r"[^\w\s]", " ", s.lower()).split())


def _headings():
    """Every heading in the library, normalized, read once per index."""
    rows = _idx()
    if _CACHE.get("heads_of") is not rows:
        _CACHE.update(heads_of=rows, heads={_norm(r["heading"]) for r in rows if len(r["heading"].split()) >= MIN_WORDS})
    return _CACHE["heads"]


def _quote_text(block):
    """The block with code spans that hold a double quote blanked, and other code spans kept as their text, so a quote
    that holds `code` still reads as the page does."""
    return TICKED.sub(lambda m: " " if '"' in m.group(1) else m.group(1), block)


def _short(quote):
    return RD._safe(" ".join(quote.split()[:5]))[:60]


ELLIPSIS = re.compile(r"\s*(?:…|\.\.\.)\s*(?:\([^()]*\))?\s*$")


def _family(row):
    """A section and its subsections: the rows after it on its page, up to the next heading at its level or above."""
    out, inside = [], False
    for x in _idx():
        if x["path"] != row["path"]:
            if inside:
                break
            continue
        if x is row or x["id"] == row["id"]:
            inside = True
            out.append(x)
        elif inside:
            if x.get("level", 9) <= row.get("level", 0):
                break
            out.append(x)
    return out or [row]


def _resolve(cite):
    rows = _idx()
    memo = _CACHE.setdefault("resolved", {})
    if memo.get("of") is not rows:
        memo.clear()
        memo["of"] = rows
    if cite not in memo:
        memo[cite] = _resolve_uncached(cite)
    return list(memo[cite])


def _resolve_uncached(cite):
    """The rows a citation names, each with its subsections; a duplicate page (docs/patterns__x) names its twin
    (patterns/x); a heading shortened with an ellipsis names the one heading on its page that starts with what is left."""
    cite = re.sub(r"^docs/(cookbooks|patterns)__", r"\1/", cite.strip())
    r = _resolve_one(cite)
    out, ids = [], set()
    for x in r:
        for y in _family(x):
            if y["id"] not in ids:
                ids.add(y["id"])
                out.append(y)
    return out


def _resolve_one(cite):
    r = CF._cited(cite)
    if r or "#" not in cite:
        return r
    cut = bool(ELLIPSIS.search(cite))  # "Good practice…" may stop mid-word; without an ellipsis, only at a word end
    path, head = ELLIPSIS.sub("", cite).split("#", 1)
    path = path if path.endswith((".md", ".txt")) else path + ".md"
    head = re.sub(r"\s*\([^()]*\)\s*$", "", head).strip()  # a trailing label
    hits = [x for x in _idx() if x["path"] == path and x["heading"].startswith(head)
            and (cut or len(x["heading"]) == len(head) or not x["heading"][len(head)].isalnum())]
    return hits if len(hits) == 1 and head else []


def _holder(parts, paths):
    """The first section on one of these pages that holds the quote, or None."""
    return next((r for r in _idx() if parts and r["path"] in paths and RD._in_row(r, parts)), None)


def _rows_for(cites):
    """(resolved section rows, cites that resolve to nothing)."""
    rows, bad = [], []
    for c in cites:
        r = _resolve(c)
        if r:
            rows += [x for x in r if x not in rows]
        else:
            bad.append(c)
    return rows, bad


def _clause(block, q):
    """(start, end) of the clause around the quote's first appearance: back to the last sentence end within 400
    characters, forward to the next one within 400; None when the quote is not in the block."""
    i = block.find('"' + q + '"')
    if i < 0:
        return None
    lo = max(0, i - 400)
    ends = list(CLAUSE_END.finditer(block[lo:i]))
    after = CLAUSE_END.search(block, i + len(q) + 2, i + len(q) + 402)
    return (lo + ends[-1].end() if ends else lo), (after.start() if after else min(len(block), i + len(q) + 402))


def _claimed(q):
    """A quoted string read as a claimed quote: 4 or more words, or any length when it holds a specific fact."""
    return len(q.split()) >= MIN_WORDS or bool(SPECIFIC.search(q))


def _ref(row):
    """RD._ref, kept per index: it reads the index to number a section."""
    rows = _idx()
    memo = _CACHE.setdefault("refs", {})
    if memo.get("of") is not rows:
        memo.clear()
        memo["of"] = rows
    if row["id"] not in memo:
        memo[row["id"]] = RD._ref(row)
    return memo[row["id"]]


def _labeled(block, q):
    """Is this quote labeled unverified or unconfirmed beside it: in its clause before it, in the parentheses right
    after it, or after it up to the next comma or "and"/"but"; or by a next sentence that names it ("This quote is
    unverified")? A label further along the clause is about something else."""
    span = _clause(block, q)
    if span is None:
        return False
    i = block.find('"' + q + '"')
    j, end = i + len(q) + 2, span[1]
    before = re.split(r",|;|\b(?:and|but|while|whereas)\b", block[span[0]:i])[-1]
    paren = re.match(r"\s*\([^()]*\)", block[j:end])
    k = j + (paren.end() if paren else 0)
    tail = re.split(r",|\b(?:and|but|while|whereas)\b", block[k:end])[0]
    near = before + " " + (paren.group() if paren else "") + " " + tail
    if LABEL.search(near) and not NOT_LABEL.search(near):
        return True
    nxt = block[end:end + 1] if end < len(block) else ""
    return bool(nxt and CLAUSE_END.match(block, end) and block[end + 1:end + 2].isspace()
                and LABEL_NEXT.match(block[end + 1:]))


def _said_by_docs(block, q):
    """Is this quote given as the docs' words ("The docs say "...""), going by the words just before it?"""
    i = block.find('"' + q + '"')
    return i > 0 and bool(DOCS_SAY.search(block[max(0, i - 60):i]))


def check(text, seen=None):
    """(rows, summary, ok). summary is None when the answer neither cites a library section nor mentions Jev. seen, a
    set, collects each quote given a row, so unquoted_facts reads the lines whose quotes were passed over as terms."""
    text = text.translate(CURLY)
    blocks = _blocks(text)
    if not any(_cites(b) for _, b, _ in blocks) and not JEV.search(text):
        return [], None, True
    any_cite = any(_cites(b) for _, b, _ in blocks)
    out, counts = [], {}
    skipped = [0, 0]  # quotes looked at, quotes past MAX_QUOTES
    pages = {x["path"] for _, b, _ in blocks for c in _cites(b) for x in _resolve(c)}  # pages this answer cites
    items = []  # (indent, cites) of the bullets so far under this heading, for a nested bullet's parent
    under = {}  # every citation under each heading
    for h, b, _ in blocks:
        under.setdefault(h, []).extend(c for c in _cites(b) if c not in under.get(h, []))
    for head, block, indent in blocks:
        cites = _cites(block)
        if indent is None and not block.startswith("|"):
            items = []
        parent = next((c for i, c in reversed(items) if indent is not None and i < indent and c), [])
        if indent is not None:
            items.append((indent, cites))
        qtext = _quote_text(block)
        quotes = [q for q in QUOTE.findall(qtext) if _claimed(q)
                  and (any_cite or _said_by_docs(qtext, q) or SPECIFIC.search(q))]  # with no citation anywhere, quotes
        # given as the docs' words or holding a specific fact
        for q in dict.fromkeys(quotes):  # a quote repeated in one block is checked once
            if skipped[0] >= MAX_QUOTES:
                skipped[1] += 1
                continue
            skipped[0] += 1
            if _norm(q) in _headings():
                continue  # a page or section title in quotes ("the guide "How to build..."") is a name, not a quote
            use = cites or parent + [c for c in under.get(head, []) if c not in parent]
            q2 = ESCAPE.sub(r"\1", q)
            parts = RD.quote_parts(q2)
            rows, bad = _rows_for(use)
            if not use and len(q.split()) < UNCITED_WORDS and not SENTENCE.match(q.strip()) and not SPECIFIC.search(q):
                continue
            if not use:
                if q.strip().endswith("?") and not _said_by_docs(qtext, q):
                    continue  # the answer's own example question
                if _labeled(qtext, q):
                    counts["LABELED"] = counts.get("LABELED", 0) + 1
                    out.append(f"LABELED | {_short(q)} | no citation")
                    if seen is not None:
                        seen.add(q)
                    continue
                held = _holder(parts, pages)
                v, row = "UNCITED", (f"UNCITED | {_short(q)} | no citation under this heading"
                                     + (f" | found under {_ref(held)}" if held else ""))
            elif not rows:
                v, row = "BAD CITE", f"BAD CITE | {_short(q)} | {RD._safe(bad[0])[:80]}"
            else:
                raw = RD.quote_parts(q) if q2 != q else None  # the page may keep the escapes ("\\$42") the quote was read without
                esc = RD.quote_parts(re.sub(r"(?<!\\)\$", r"\\$", q2)) if "$" in q2 else None  # or the quote may drop them
                hit = next((r for r in rows if parts and (RD._in_row(r, parts) or (raw and RD._in_row(r, raw))
                                                          or (esc and RD._in_row(r, esc)))), None)
                if hit:
                    v, row = "FOUND", f"FOUND | {_short(q)} | {_ref(hit)}"
                elif q.strip().endswith("?") and not _said_by_docs(qtext, q):
                    continue  # a quoted question not on the page is the answer's own example question
                elif _labeled(qtext, q):
                    v, row = "LABELED", f"LABELED | {_short(q)} | {_ref(rows[0])}"
                elif not cites and len(q.split()) < UNCITED_WORDS and not SENTENCE.match(q.strip()) and not SPECIFIC.search(q):
                    continue  # a short phrase (not a whole sentence) with no citation of its own reads as a term
                elif not cites:  # it borrowed the citations around it, and none holds it
                    held = _holder(parts, pages)
                    v, row = "UNCITED", (f"UNCITED | {_short(q)} | no citation of its own, and none under this heading holds it"
                                         + (f" | found under {_ref(held)}" if held else ""))
                else:
                    other = next((r for r in _idx() if parts and r["path"] in {x["path"] for x in rows}
                                  and r not in rows and RD._in_row(r, parts)), None)
                    v = "NOT FOUND"
                    row = (f"NOT FOUND | {_short(q)} | cited {_ref(rows[0])}"
                           + (f" | found under {_ref(other)}" if other else ""))
            counts[v] = counts.get(v, 0) + 1
            out.append(row)
            if seen is not None:
                seen.add(q)
    if skipped[1]:
        counts["TOO MANY"] = 1
        out.append(f"TOO MANY | {skipped[1]} more quotes not checked | at most {MAX_QUOTES} are checked in one answer")
    n = sum(counts.values())
    summary = (f"answer check: {n} quote{'s' if n != 1 else ''}, {counts.get('FOUND', 0)} found, "
               f"{counts.get('NOT FOUND', 0)} not found, {counts.get('BAD CITE', 0)} bad cite, "
               f"{counts.get('UNCITED', 0)} uncited, {counts.get('LABELED', 0)} labeled unverified")
    ok = all(r.startswith(("FOUND", "LABELED")) for r in out)
    return out, summary, ok


def unquoted_facts(text, seen=None):
    """Rows for sentences stating a specific Jev fact with no quote or citation on their line (module docstring). seen,
    when given, is the set check() already filled for this text, so the quotes are not checked twice."""
    text = text.translate(CURLY)
    if not JEV.search(text) and not any(_cites(b) for _, b, _ in _blocks(text)):
        return []
    if seen is None:
        seen = set()
        check(text, seen)
    out, fence = [], False
    for line in text.split("\n"):
        if line.lstrip().startswith("```"):
            fence = not fence
            continue
        if fence:
            continue
        if MY_READ.match(line):
            break
        quotes = [q for q in QUOTE.findall(_quote_text(line)) if _claimed(q)]
        if (quotes and all(q in seen for q in quotes)) or (not quotes and _cites(line)):
            continue  # its quotes were checked, or it cites a section with no quote to check
        for s in re.split(r"(?<=[.!?])\s+", line.strip(" -*#>|")):
            s = s[:MAX_SENTENCE]  # a fact sits in an ordinary sentence; a very long run is not one
            hedged = HEDGED.search(s) or (YOU_HEDGE.search(s) and not any(SPECIFIC.search(q) for q in QUOTE.findall(s)))
            if (FACT_TERM.search(s) or FACT_NAME.search(s)) and SPECIFIC.search(s) and not hedged:
                out.append(f"UNQUOTED | {_short(s)}")
    return out


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv:
        print("usage: check_answer.py < answer.md", file=sys.stderr)
        return 2
    text = sys.stdin.buffer.read().decode("utf-8", errors="replace")
    seen = set()
    rows, summary, ok = check(text, seen)
    for r in rows + unquoted_facts(text, seen):
        print(r)
    if summary:
        print(summary)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
