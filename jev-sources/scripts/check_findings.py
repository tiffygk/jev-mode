#!/usr/bin/env python3
"""Check the replies of a reading plan's readers against the saved plan. Replies come on stdin.
  python3 scripts/check_findings.py <plan_id> < replies.txt

Prints one line per finding: OK | b1 | <CITE AS>, QUOTE NOT FOUND | b1 | <CITE AS>[ | found under <ref>],
NOT IN BATCH | b1 | <CITE AS>, MALFORMED | b1 | <first 80 characters>, TOO LONG | b1 | <CITE AS> for a sentence or
quote over 300 characters or a CITE AS over 200; PAGE TEXT | b1 | line starting "<first 5 words>" (<n> characters) for a
line over 200 characters or one holding 8 words in a row from a section of its batch, PAGE TEXT | b1 | <n> characters
outside finding lines when a reply's other lines pass 600 characters, TOO MANY | b1 | <count> for more than 12 findings in
a batch, EMPTY | b1 | no findings for a reply with no finding line. Then one summary line.
Exit 0 only when every batch reported and every finding is OK; 1 otherwise; 2 when the plan file is missing.
Never prints section text: every echoed string passes through read._safe."""
import json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
import read as RD

MAX_FINDINGS = 12
PAGE_TEXT = 200
MAX_SENTENCE = 300  # live readers wrote at most 226 characters
MAX_QUOTE = 300  # and quoted at most 201
MAX_CITE = 200
VERBATIM_WORDS = 8  # a shorter run copied from a section is a phrase, not page text
OTHER_TEXT = 600  # characters a reply may hold outside its finding lines (live readers wrote none)
WORD = re.compile(r"[a-z0-9]+")
HEADER = re.compile(r"^JEV-READER:\s*plan\s+([A-Za-z0-9_-]+)\s+batch\s+(\d+)(?=[\s).:]|$)")  # the hook keeps an identical copy
MARKS = re.compile(r"[*`]|^_+|_+$")  # underscores only at the line's ends, so a plan id keeps its own
FINDING = re.compile(r"^FINDING:\s*(.+?)\s*\|\s*CITE AS:\s*(.+?)\s*\|\s*QUOTE:\s*(.+)$")
PLAN_ID = re.compile(r"[A-Za-z0-9_-]+")


def _load(plan_id):
    if not PLAN_ID.fullmatch(plan_id):
        return None
    try:
        with open(os.path.join(paths.DATA, "plans", plan_id + ".json"), encoding="utf-8") as f:
            plan = json.load(f)
    except (OSError, ValueError):
        return None
    ok = isinstance(plan, dict) and isinstance(plan.get("batches"), list) and all(
        isinstance(b, dict) and isinstance(b.get("n"), int) and isinstance(b.get("ids"), list) for b in plan["batches"])
    return plan if ok else None  # a damaged plan file reads as no plan, never a crash


ID_TAIL = re.compile(r"\s*\(([^()\s]+#\d+)\)\s*$")


def _cited(cite):
    """The index rows a CITE AS names (a numeric id, path#heading with or without its label, or a page); [] if none.
    A numeric id in parentheses at the end, where readers sometimes put it instead of the label, names its section."""
    m = ID_TAIL.search(cite)
    for c in ([m.group(1)] if m else []) + [cite]:
        try:
            rows = RD._page_rows(c) or RD._rows(c)
        except SystemExit:
            continue
        if rows:
            return rows
    return []


def _echo(cite):
    """What a row shows for a CITE AS: the reader's own citation when it is at most 80 characters; a longer one is shown
    as its section's short reference when it resolves, else cut to 80 characters (a long cite may carry page text)."""
    if len(cite) <= 80:
        return RD._safe(cite)
    m = ID_TAIL.search(cite)
    rows = _cited(m.group(1)) if m and _cited(m.group(1)) else _cited(cite)
    return RD._ref(rows[0]) if len(rows) == 1 else RD._safe(cite[:80])


def _runs(text):
    """Every run of VERBATIM_WORDS words in text, lowercased, with punctuation and markup dropped."""
    w = WORD.findall(text.lower())
    return {tuple(w[i:i + VERBATIM_WORDS]) for i in range(len(w) - VERBATIM_WORDS + 1)}


def _batch_runs(batch_ids):
    """The word runs of every section in a batch, for spotting copied page text."""
    runs = set()
    for sid in sorted(batch_ids):
        try:
            r = RD._row(sid)
            with open(os.path.join(RD.ROOT, r["path"]), encoding="utf-8") as f:
                runs |= _runs("\n".join(f.read().split("\n")[r["line_start"] - 1:r["line_end"]]))
        except (SystemExit, OSError, KeyError):
            continue
    return runs


def _page_text(line, runs):
    """A non-finding line that is long, or that holds 8 words in a row from a section of its batch, wherever they sit
    in the line (after a label, inside a lead-in, before a citation) and whatever punctuation or markup is changed."""
    return len(line) > PAGE_TEXT or not _runs(line).isdisjoint(runs)


def _start(line):
    """A flagged line's first words, fewer than VERBATIM_WORDS, so the row names the line without echoing page text."""
    return RD._safe(" ".join(line.split()[:VERBATIM_WORDS - 3]))[:60]


def _judge(cite, quote, batch_ids):
    """(verdict, hint) for one well-formed finding."""
    if not _cited(cite):
        return "NOT IN BATCH", ""
    m = ID_TAIL.search(cite)
    if m and _cited(m.group(1)):
        cite = m.group(1)
    page = RD._page_rows(cite)
    if page:  # a page-only cite: the section in this batch that holds the quote, when one does
        parts = RD.quote_parts(quote)
        hit = next((r for r in page if r["id"] in batch_ids and RD._in_row(r, parts)), None)
        if hit:
            return "OK", ""
    found, row, _, _ = RD.check_quote(cite, quote)
    if not found:
        other = RD.elsewhere_on_page(cite, quote)
        return "QUOTE NOT FOUND", (f" | found under {RD._ref(other[0])}" if other else "")
    return ("OK" if row["id"] in batch_ids else "NOT IN BATCH"), ""


def check(plan_id, text):
    """(rows, summary, ok). With no plan file: (["NO PLAN | <plan_id>"], None, False)."""
    plan = _load(plan_id)
    if plan is None:
        return [f"NO PLAN | {RD._safe(plan_id)[:80]}"], None, False
    batches = {b["n"]: set(b["ids"]) for b in plan["batches"]}
    rows, count, extra, other_chars, runs = {}, {}, {}, {}, {}
    reported, cur, pending = set(), None, []
    def other_line(n, line):
        other_chars[n] = other_chars.get(n, 0) + len(line)
        if n not in runs:
            runs[n] = _batch_runs(batches[n])
        if _page_text(line, runs[n]):
            extra[n] = extra.get(n, 0) + 1
            rows.setdefault(n, []).append((None, f'PAGE TEXT | b{n} | line starting "{_start(line)}" ({len(line)} characters)'))
    for raw in text.split("\n"):
        line = raw.strip()
        m = HEADER.match(MARKS.sub("", line))
        if m:
            cur = int(m.group(2)) if m.group(1) == plan_id and int(m.group(2)) in batches else None
            if cur is not None:
                reported.add(cur)
                for p in pending:  # lines before a reply's header belong to that reply
                    other_line(cur, p)
            pending = []
            continue
        if not line:
            continue
        if cur is None:
            if not line.startswith("FINDING:"):
                pending.append(line)
            continue
        out = rows.setdefault(cur, [])
        if line.startswith("FINDING:"):
            count[cur] = count.get(cur, 0) + 1
            m = FINDING.match(line)
            if not m or not RD.quote_parts(m.group(3)):
                out.append((False, f"MALFORMED | b{cur} | {RD._safe(line[:80])}"))
                continue
            cite = m.group(2)
            if len(m.group(1)) > MAX_SENTENCE or len(m.group(3)) > MAX_QUOTE or len(cite) > MAX_CITE:
                out.append((False, f"TOO LONG | b{cur} | {_echo(cite)}"))
                continue
            verdict, hint = _judge(cite, m.group(3), batches[cur])
            out.append((verdict == "OK", f"{verdict} | b{cur} | {_echo(cite)}{hint}"))
        else:
            other_line(cur, line)
    flat = []
    for n in sorted(set(rows) | reported):
        flat += rows.get(n, [])
        if not count.get(n):  # a reader that returned nothing is flagged, never counted as a clean report
            flat.append((None, f"EMPTY | b{n} | no findings"))
        if other_chars.get(n, 0) > OTHER_TEXT:  # many short lines of the reader's own still carry a section
            flat.append((None, f"PAGE TEXT | b{n} | {other_chars[n]} characters outside finding lines (at most {OTHER_TEXT})"))
        if count.get(n, 0) > MAX_FINDINGS:
            extra[n] = extra.get(n, 0) + 1
            flat.append((None, f"TOO MANY | b{n} | {count[n]}"))
    findings = [ok for ok, _ in flat if ok is not None]
    missing = [n for n in sorted(batches) if n not in reported]
    miss = f"{len(missing)} missing" + (f" ({', '.join('b%d' % n for n in missing)})" if missing else "")
    other = sum(1 for ok, _ in flat if ok is None)
    summary = (f"plan {plan_id}: {len(batches)} batch{'es' if len(batches) != 1 else ''}, {len(reported)} reported, {miss}; "
               f"{len(findings)} findings, {sum(findings)} OK, {len(findings) - sum(findings)} failed"
               + (f"; {other} other flagged line{'s' if other != 1 else ''}" if other else ""))
    ok = not missing and all(findings) and not other
    return [r for _, r in flat], summary, ok


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print("usage: check_findings.py <plan_id> < replies", file=sys.stderr)
        return 2
    rows, summary, ok = check(argv[0], sys.stdin.buffer.read().decode("utf-8", errors="replace"))
    for r in rows:
        print(r)
    if summary is None:
        return 2
    print(summary)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
