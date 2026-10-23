#!/usr/bin/env python3
"""Stop: before the main session's answer reaches the user, every docs quote in it is checked against the section it
cites (scripts/check_answer.py). An answer that neither cites a library section nor mentions Jev passes untouched and
unlogged. One that mentions Jev but cites nothing has the quotes it gives as the docs' words, and any quote holding a
specific fact (a number with a unit, a price, a status code, a name, an error line), checked. A quote that is not on its
cited section, a citation that names no section, or a quote with no citation in reach blocks the stop once, with the
failing rows (never page text), so the model corrects the quote, cites the section that holds it, or labels it
unverified beside it. Every citation must name a real section; an answer may paraphrase the docs with citations.
Quotation marks are for the docs' words only: the user's own text goes in backticks, which are not checked. The next
stop passes (Claude Code sets stop_hook_active). Any fault passes and is logged.
A quality check, not a security boundary. Logs counts to <data>/logs/answer_check.jsonl unless JEV_LOG=off."""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jev_terms import ROOT, JEV, data_dir, log_event

CITES = re.compile(r"(?:docs|cookbooks|patterns|blog)/")
REASON_CAP = 4000
TAIL = ("fix each line: for a citation that names no section, cite the section that holds the fact (run jev.py or "
        "read.py to find it); for a quote, correct it from its section (read.py '<id>'), put it in your own words with "
        "its citation, or label it unverified in the parentheses beside it. Wording you made up and the user's own text "
        "(their error, log or message) go in backticks, not quotation marks. Then send the whole corrected answer, "
        "with no note about this check.")


TAIL_BYTES = 4_000_000  # the end of the transcript read for the last answer; a long session is never read whole


def _from_transcript(path):
    """The text of the last assistant message that has text, from the last TAIL_BYTES of a Claude Code transcript
    (JSON lines). None when no such message is in that window; the hook then passes."""
    size = os.path.getsize(path)
    with open(path, "rb") as f:
        if size > TAIL_BYTES:
            f.seek(size - TAIL_BYTES)
            f.readline()  # the window may start mid-line
        lines = f.read().decode("utf-8", errors="replace").split("\n")
    for line in reversed(lines):
        if '"assistant"' not in line:
            continue
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if not isinstance(e, dict) or e.get("type") != "assistant":
            continue
        parts = (e.get("message") or {}).get("content") or []
        text = "\n".join(p.get("text", "") for p in parts if isinstance(p, dict) and p.get("type") == "text")
        if text.strip():
            return text
    return None


def _reason(rows):
    tail = f"\n{TAIL}"
    out, used = [], len(tail)
    for i, r in enumerate(rows):
        more = f"\n... and {len(rows) - i} more failing quotes"
        if used + len(r) + 1 + len(more) > REASON_CAP:
            out.append(more.strip("\n"))
            break
        out.append(r)
        used += len(r) + 1
    return ("\n".join(out) + tail)[:REASON_CAP]


def main():
    sid = None
    try:
        p = json.load(sys.stdin)
        if not isinstance(p, dict):
            raise ValueError("input is not an object")
        sid = p.get("session_id") if isinstance(p.get("session_id"), str) else "-"
        msg = p.get("last_assistant_message")
        if msg is None and isinstance(p.get("transcript_path"), str):
            msg = _from_transcript(p["transcript_path"])
        if msg is None:
            return 0
        if not isinstance(msg, str):
            raise ValueError("last_assistant_message is not text")
        if not CITES.search(msg) and not JEV.search(msg):
            return 0  # neither cites the library nor mentions Jev: say nothing, log nothing
        if not os.path.exists(os.path.join(data_dir(), "sections.jsonl")):
            return 0
        if p.get("stop_hook_active"):
            log_event("answer_check", decision="loop_guard", session=sid)
            return 0
        sys.path.insert(0, os.path.join(ROOT, "scripts"))
        import check_answer
        rows, summary, ok = check_answer.check(msg)
        if summary is None:
            return 0
        bad = [r for r in rows if not r.startswith(("FOUND", "LABELED"))]
        counts = dict(quotes=len(rows), failed=len(bad))
        if not bad:
            log_event("answer_check", decision="clean", session=sid, **counts)
            return 0
        log_event("answer_check", decision="block", session=sid, **counts)
        print(json.dumps({"decision": "block", "reason": _reason(bad)}))
        return 0
    except BaseException as e:  # fail open: a fault in this check must never hold an answer back
        if isinstance(e, SystemExit) and e.code in (0, None):
            return 0
        log_event("answer_check", decision="error", session=sid or "-", error=f"{type(e).__name__}: {e}"[:200])
        return 0


if __name__ == "__main__":
    sys.exit(main())
