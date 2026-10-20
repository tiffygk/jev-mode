#!/usr/bin/env python3
"""Check the replies of a reading plan's readers against the saved plan. Replies come on stdin.
  python3 scripts/check_findings.py <plan_id> < replies.txt

Prints one line per finding: OK | b1 | <CITE AS>, QUOTE NOT FOUND | b1 | <CITE AS>[ | found under <ref>],
NOT IN BATCH | b1 | <CITE AS>, MALFORMED | b1 | <first 80 characters>; and PAGE TEXT | b1 | <first 80 characters> for a line
over 200 characters, TOO MANY | b1 | <count> for more than 12 findings in a batch, EMPTY | b1 | no findings for a reply
with no finding line. Then one summary line.
Exit 0 only when every batch reported and every finding is OK; 1 otherwise; 2 when the plan file is missing.
Never prints section text: every echoed string passes through read._safe."""
import json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paths
import read as RD

MAX_FINDINGS = 12
PAGE_TEXT = 200
HEADER = re.compile(r"^JEV-READER: plan (\S+) batch (\d+)\s*$")
FINDING = re.compile(r"^FINDING:\s*(.+?)\s*\|\s*CITE AS:\s*(.+?)\s*\|\s*QUOTE:\s*(.+)$")
PLAN_ID = re.compile(r"[A-Za-z0-9_-]+")


def _load(plan_id):
    if not PLAN_ID.fullmatch(plan_id):
        return None
    try:
        with open(os.path.join(paths.DATA, "plans", plan_id + ".json"), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def _cited(cite):
    """The index rows a CITE AS names (a numeric id, path#heading with or without its label, or a page); [] if none."""
    try:
        return RD._page_rows(cite) or RD._rows(cite)
    except SystemExit:
        return []


def _judge(cite, quote, batch_ids):
    """(verdict, hint) for one well-formed finding."""
    if not _cited(cite):
        return "NOT IN BATCH", ""
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
    rows, count, extra = {}, {}, {}
    reported, cur = set(), None
    for raw in text.split("\n"):
        line = raw.strip()
        m = HEADER.match(line)
        if m:
            cur = int(m.group(2)) if m.group(1) == plan_id and int(m.group(2)) in batches else None
            if cur is not None:
                reported.add(cur)
            continue
        if cur is None or not line:
            continue
        out = rows.setdefault(cur, [])
        if line.startswith("FINDING:"):
            count[cur] = count.get(cur, 0) + 1
            m = FINDING.match(line)
            if not m or not RD.quote_parts(m.group(3)):
                out.append((False, f"MALFORMED | b{cur} | {RD._safe(line[:80])}"))
                continue
            cite = m.group(2)
            verdict, hint = _judge(cite, m.group(3), batches[cur])
            out.append((verdict == "OK", f"{verdict} | b{cur} | {RD._safe(cite[:200])}{hint}"))
        elif len(line) > PAGE_TEXT:
            extra[cur] = extra.get(cur, 0) + 1
            out.append((None, f"PAGE TEXT | b{cur} | {RD._safe(line[:80])}"))
    flat = []
    for n in sorted(set(rows) | reported):
        flat += rows.get(n, [])
        if not count.get(n):  # a reader that returned nothing is flagged, never counted as a clean report
            flat.append((None, f"EMPTY | b{n} | no findings"))
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
