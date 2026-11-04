#!/usr/bin/env python3
"""Check a jevaluate-report file before a team's agents work from it.

  report_check.py <file.md> [--private-terms <path>] [--fragment] [--skip rule,...]

Prints one line per finding, "<rule>: <line>: <why>", then "counts fixes N, labels L, links M, chars C".
Exit 0 with no findings, 1 otherwise. --fragment checks a snippet: it skips the whole-file rules
(front-matter, table-match, order, opening, opening-test). --skip drops named rules (the tests use it to run
a probe set against the rules it was written for). Rule names and what each checks are in SKILL.md, Enforced by.
Why: the skimmer report (2026-10-16) broke a fix label in an edit after review, and nothing reran.
"""
import argparse, os, re, sys

LABELS = ["**What we saw.**", "**Why it matters.**", "**Source.**", "**Suggested change.**", "**How to check it.**"]
FIX_HEAD = re.compile(r"^### (S\d+)\b:?\s*(.*)$")
# A home folder only at the start of a path, or reached by "../": a repo folder named Users inside src is code, a home folder followed by a name is not.
PATH_RE = re.compile(r"(?<![\w./-])(?:/Users|/home)/[^/\s]+|(?:\.\.[\\/])+(?:Users|home)[\\/][^/\\\s]+|\b[A-Za-z]:[\\/]Users[\\/]|(?<![\w/])~[/\\]|\$HOME\b|file://|Obsidian[ ]Vaults|(?<![\w-])scratchpad[/]", re.I)
ID_IN_ADDRESS = re.compile(r"/Q\d{2,3}(?:$|[/?#.])")
PRIVATE_RE = [
    (PATH_RE, "a local path"),
    (re.compile(r"(?<![\w#/-])Q\d{2,3}(?![\w-])"), "an internal claim ID"),
    (re.compile(r"\(F\d{1,2}\)|\bF\d{1,2} (?:yes|no|n\.a\.)(?!\w)|\bF\d{1,2}-F\d{1,2}\b"), "a rubric fact ID"),
    (re.compile(r"\b(?:owner|her|my) rulings?\b", re.I), "an owner ruling"),
]
# Promise phrases. OPEN: a promise about a change still to try. DONE: a result stated as certain ("it now rates 3").
# Singular subjects only: "these three fixes" is a noun phrase in the template's opening, never a promise.
SUBJECT = r"(?:this|that|it|which|doing this|the change|the fix|this change|that change|the split)"
OPEN = [rf"\b{SUBJECT}\s+(?:\w+\s+)?(?:fixes|ensures|guarantees|eliminates|prevents|solves|stops|removes|resolves|corrects|cures)\b",
        r"(?<!\bI )(?<!\bwe )\bwill\s+(?:\w+ly\s+)?(?!(?:be\s+(?:able|glad|happy|asked)|need|want|have|depend|vary|update|add|read|look)\b)[a-z]+\b",
        r"\b(?:it|this|that|you|they|these)(?:'|\u2019)ll\b",
        r"\bshould\s+(?:fix|resolve|solve|cure|stop|eliminate|prevent|ensure|remove)\b",
        r"\b(?:solves|must|you should have|the correct|guaranteed|guarantees|goes away|disappears)\b",
        rf"\b{SUBJECT}\s+(?:\w+\s+)?makes?\s+(?:the\s+)?\w+(?:\s+\w+)?\s+(?:stable|reliable|consistent|correct|accurate|deterministic|safe)\b"]
DONE = [r"\bfixes the\b", r"\b(?:rates|scores|earns)\s+(?:an?\s+)?\d\b", r"\bwould\s+(?:rate|score|earn|reach|get|be)\s+(?:an?\s+)?\d\b",
        r"\b(?:gets|moves|brings|takes|lifts|raises|pushes)\b[^.\n]{0,40}?\bto\s+(?:an?\s+)?\d\b"]
CERTAIN = re.compile("|".join(OPEN + DONE), re.I)
MEASURE = re.compile(r"\d|\b(more|fewer|less|at least|under|over|same|compare[sd]?|held-out|baseline|rerun|rate|count|recall|"
                     r"precision|accuracy|number|figure|interval|zero|with and without|report whether|per|n|fails|passes|"
                     r"is flagged|appears)\b", re.I)
# The opening says the fixes are to be tested: they come from documented practice, not from the project's own eval.
TO_TEST = re.compile(r"\b(?:un)?test(?:s|ed|ing)?\b", re.I)
FIX_WORD = re.compile(r"\b(?:fix(?:es)?|advice|change|changes|suggest\w*)\b", re.I)
SENTENCE = re.compile(r"(?<=[.!?:;])\s+|\n\s*\n")


def says_to_test(opening):
    """True when one sentence of the opening names a test word and the fixes: "Our test suite passes" is not enough."""
    return any(TO_TEST.search(s) and FIX_WORD.search(s) for s in SENTENCE.split(unquoted(opening)))
ADVICE = re.compile(r"^\s*(Try|Consider)\b")
EMOJI = re.compile("[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F2FF]")
REQUIRED_FM = ["title", "date", "method", "verdict", "scores", "fixes"]
SCORE_ROWS = ["Execution", "Fit", "Coverage", "Evidence"]


NO_TERMS = "no private-terms list"


def default_terms():
    """The Jevaluate library's private-terms.txt, found the way library.py finds the library."""
    lib = os.environ.get("JEVALUATE_LIBRARY")
    if not lib:
        old = os.path.expanduser("~/.claude/jevaluate-library")
        lib = old if os.path.isdir(old) else os.path.expanduser("~/.jevaluate-library")
    return os.path.join(lib, "private-terms.txt")


def front_matter(lines):
    if not lines or lines[0].strip() != "---":
        return {}, 0
    fm = {}
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return fm, i + 1
        m = re.match(r"^([A-Za-z_]+):\s*(.*)$", lines[i])
        if m:
            fm[m.group(1)] = m.group(2).strip().strip('"')
        elif re.match(r"^\s+-\s*(S\d+)", lines[i]):
            fm.setdefault("_fix_ids", []).append(re.match(r"^\s+-\s*(S\d+)", lines[i]).group(1))
    return {}, 0


def unquoted(text):
    """Text with blockquotes, quotations and inline code removed, for the certainty rule."""
    text = "\n".join(x for x in text.split("\n") if not x.lstrip().startswith(">"))
    text = re.sub(r"`[^`]*`", "", text)
    return re.sub(r"\"[^\"]*\"|“[^”]*”", "", text)


def paragraphs(lines, start):
    para, first = [], None
    for i in range(start, len(lines)):
        if lines[i].strip() == "":
            if para:
                yield first, para
            para, first = [], None
        else:
            if first is None:
                first = i + 1
            para.append(lines[i])
    if para:
        yield first, para


def load_terms(path):
    try:
        return [t.strip() for t in open(path, encoding="utf-8") if t.strip() and not t.startswith("#")]
    except OSError:
        return []


def check_private(text, where, terms, out, line_of=None):
    for n, line in enumerate(text.splitlines(), 1):
        at = line_of(n) if line_of else f"{where}:{n}"
        targets = re.findall(r"\]\(([^)\s]+)", line) + re.findall(r"^\s*\[[^\]]+\]:\s*(\S+)", line)
        for t in targets:
            if PATH_RE.search(t):
                out.append(("private", at, f"a link to a local path: {t!r}"))
        addresses = targets + re.findall(r"https?://\S+", line)
        for u in addresses:
            low_u = u.lower()
            for hit in [x for x in terms if x.lower() in low_u] + ID_IN_ADDRESS.findall(u):
                out.append(("private", at, f"a private word in a link or address: {hit!r}"))
        # a link definition: its target is checked above; its hover title is checked below like prose
        bare = re.sub(r"^\s*\[[^\]]+\]:\s*\S+", "", line)
        bare = re.sub(r"\]\([^)]*\)", "]", bare)
        bare = re.sub(r"https?://\S+", "", bare)
        for rx, why in PRIVATE_RE:
            if rx.search(bare):
                out.append(("private", at, f"{why}: {rx.search(bare).group(0)!r}"))
        low = bare.lower()
        for t in terms:
            if t.lower() in low:
                out.append(("private", at, "a private term"))


def bare_refs(text_lines, offset, where, out):
    for n, line in enumerate(text_lines):
        if line.startswith("#") or re.match(r"^\[[^\]]+\]:\s", line):
            continue
        prose = "|".join(line.split("|")[2:]) if line.startswith("|") else line
        prose = re.sub(r"\]\([^)]*\)", "]", prose)
        m = re.search(r"(?<![\w#/-])S\d+(?![\w-])", prose)
        if m:
            at = f"{where}:{n + 1}" if where else n + offset + 1
            out.append(("bare-ref", at, f"'{m.group(0)}' in prose: link the section by its name"))


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--private-terms", default=default_terms()); ap.add_argument("--fragment", action="store_true")
    ap.add_argument("--skip", default="")
    a = ap.parse_args(argv)
    skip = {s.strip() for s in a.skip.split(",") if s.strip()}
    text = open(a.file, encoding="utf-8").read()
    lines = text.splitlines()
    fm, body_start = front_matter(lines)
    out = []
    terms = load_terms(a.private_terms)
    if not terms:
        print(f"note: {NO_TERMS} at {a.private_terms}; pass --private-terms <file> to check your own terms",
              file=sys.stderr)

    # fix sections
    sections, cur = [], None
    for i in range(body_start, len(lines)):
        m = FIX_HEAD.match(lines[i])
        if m:
            cur = {"id": m.group(1), "line": i + 1, "body": []}; sections.append(cur)
        elif lines[i].startswith("## ") or lines[i].startswith("# "):
            cur = None
        elif cur is not None and not re.match(r"^\[[^\]]+\]:\s", lines[i]):
            cur["body"].append((i + 1, lines[i]))

    # labels, certainty, advice, test-named
    for s in sections:
        starts = [(n, l) for n, l in s["body"] if l.startswith("**")]
        found = [lab for n, l in starts for lab in LABELS if l.startswith(lab)]
        if found != LABELS:
            bad = next((l.split("**")[1] for n, l in starts if not any(l.startswith(x) for x in LABELS)), None)
            why = f"label '{''.join(c if c.isprintable() else '?' for c in bad)}' is not one of the five" if bad else f"labels found {len(found)} of 5 or out of order"
            out.append(("labels", s["line"], f"{s['id']}: {why}"))
        paras, cur_label = {}, None
        for n, l in s["body"]:
            lab = next((x for x in LABELS if l.startswith(x)), None)
            if lab:
                cur_label = lab; paras[lab] = [n, l[len(lab):]]
            elif cur_label and l.strip():
                paras[cur_label][1] += "\n" + l
        for lab in ("**Suggested change.**", "**Why it matters.**"):
            if lab in paras:
                m = CERTAIN.search(unquoted(paras[lab][1]))
                if m:
                    out.append(("certainty", paras[lab][0], f"{s['id']}: '{m.group(0)}' states a suggestion as certain"))
        if "**Suggested change.**" in paras and not ADVICE.match(paras["**Suggested change.**"][1]):
            out.append(("advice", paras["**Suggested change.**"][0], f"{s['id']}: Suggested change starts with Try or Consider"))
        if "**How to check it.**" in paras:
            check = paras["**How to check it.**"]
            if not MEASURE.search(check[1]):
                out.append(("test-named", check[0], f"{s['id']}: names no measure, bar or comparison"))

    # pinned-links
    repo, commit = fm.get("repo", "").rstrip("/"), fm.get("commit", "")
    if repo.startswith("https://github.com/") and commit:
        rx = re.compile(re.escape(repo) + r"/(?:blob|tree)/([^/\s)#]+)")
        for n, line in enumerate(lines, 1):
            for ref in rx.findall(line):
                if ref != commit:
                    out.append(("pinned-links", n, f"link to '{ref}', not the commit {commit[:7]}"))

    # local-link: the file is read away from the code (another checkout, a chat, a browser), so a link to a file beside it breaks
    target_rx = re.compile(r"\]\(\s*(<[^>]*>|[^)\s]+)|^\s*\[[^\]]+\]:\s*(<[^>]*>|\S+)")
    for n in range(body_start + 1, len(lines) + 1):
        for a_, b_ in target_rx.findall(lines[n - 1]):
            t = a_ or b_
            if t.startswith("<"):
                t = t[1:-1].strip()
                if not re.search(r"[./]", t):
                    continue  # a template placeholder such as <permalink>
            if not re.match(r"(?:https?://|mailto:|#)", t, re.I):
                out.append(("local-link", n, f"link to '{t}' points at a local file; use a web address or a #section"))

    # bare-ref
    bare_refs(lines[body_start:], body_start, None, out)

    # dashes and emoji
    for first, para in paragraphs(lines, body_start):
        t = "\n".join(para)
        if "—" in t:
            out.append(("dashes", first, "em-dash"))
        if EMOJI.search(t):
            out.append(("dashes", first, "emoji"))
        if len(re.findall(r"(?<!-)--(?!-)", t)) > 1 and not t.lstrip().startswith("|"):
            out.append(("dashes", first, "'--' more than once in a paragraph"))

    if len(text) >= 60000:
        out.append(("size", 0, f"{len(text)} characters; the limit is under 60,000"))

    # private rule, on the front matter and body
    check_private("\n".join(lines[:body_start]), a.file, terms, out, line_of=lambda n: n)
    check_private("\n".join(lines[body_start:]), a.file, terms, out, line_of=lambda n: n + body_start)
    m = CERTAIN.search(unquoted(fm.get("title", "")))
    if m:
        out.append(("certainty", 1, f"title: '{m.group(0)}' states a suggestion as certain"))

    if not a.fragment:
        missing = [k for k in REQUIRED_FM if k not in fm]
        if not (("repo" in fm and re.fullmatch(r"[0-9a-f]{40}", fm.get("commit", ""))) or "target" in fm):
            missing.append("repo and a 40-character commit, or target")
        if missing:
            out.append(("front-matter", 1, "missing: " + ", ".join(missing)))
        table_ids = [m.group(1) for l in lines if (m := re.match(r"^\|\s*(S\d+)\s*\|", l))]
        sec_ids = [s["id"] for s in sections]
        fm_ids = fm.get("_fix_ids", [])
        if not (set(table_ids) == set(sec_ids) == set(fm_ids)) or len(table_ids) != len(set(table_ids)):
            out.append(("table-match", 1, f"table {sorted(set(table_ids))} / sections {sorted(sec_ids)} / front matter {sorted(fm_ids)} differ"))

        def first_line(pred):
            return next((i for i in range(body_start, len(lines)) if pred(lines[i])), None)
        marks = [("title", first_line(lambda l: l.startswith("# "))),
                 ("summary table", first_line(lambda l: re.match(r"^\|\s*ID\s*\|", l))),
                 ("Rating", first_line(lambda l: l.startswith("## Rating"))),
                 ("What already works", first_line(lambda l: l.startswith("## What already works"))),
                 ("first fix", first_line(lambda l: FIX_HEAD.match(l)))]
        absent = [k for k, v in marks if v is None]
        present = [(k, v) for k, v in marks if v is not None]
        if absent:
            out.append(("order", 0, "missing: " + ", ".join(absent)))
        for (k1, v1), (k2, v2) in zip(present, present[1:]):
            if v1 > v2:
                out.append(("order", v2 + 1, f"{k2} comes before {k1}"))
        start = marks[0][1] if marks[0][1] is not None else body_start
        opening = "\n".join(lines[start + 1:(marks[1][1] or len(lines))])
        if not says_to_test(opening):
            out.append(("opening-test", start + 1, "the opening never says the fixes are to be tested"))
        m = CERTAIN.search(unquoted(opening))
        if m:
            out.append(("certainty", start + 1, f"opening: '{m.group(0)}' states a suggestion as certain"))
        gaps = []
        if "(#rating)" not in opening:
            gaps.append("no link to the Rating section")
        if not re.search(r"(?m)^\s*[-*] ", opening):
            gaps.append("no bullet list of the top fixes")
        if marks[2][1] is not None:
            end = marks[3][1] if marks[3][1] is not None else len(lines)
            rating = lines[marks[2][1]:end]
            gaps += [f"Rating has no {r} row" for r in SCORE_ROWS
                     if not any(re.match(rf"^\|\s*\**{r}\**\s*\|", l) for l in rating)]
            # The verdict's reasoning is where a sure-win promise slips in ("With that fixed, it would rate 4", 2026-11-04).
            m = CERTAIN.search(unquoted("\n".join(rating)))
            if m:
                out.append(("certainty", marks[2][1] + 1, f"Rating: '{m.group(0)}' states a suggestion as certain"))
        if gaps:
            out.append(("opening", start + 1, "; ".join(gaps)))

    out = [f for f in out if f[0] not in skip]
    for rule, where, why in out:
        print(f"{rule}: {where}: {why}")
    links = len(re.findall(r"\]\((https?://[^)\s]+)\)|^\[[^\]]+\]:\s*https?://", text, re.M))
    print(f"counts fixes {len(sections)}, labels {sum(1 for s in sections for n, l in s['body'] if any(l.startswith(x) for x in LABELS))}, links {links}, chars {len(text)}")
    return 1 if out else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
