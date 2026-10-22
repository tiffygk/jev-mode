#!/usr/bin/env python3
"""Stop: before the main session's answer reaches the user, every docs quote in it is checked against the section it
cites (scripts/check_answer.py). An answer that neither cites a library section nor mentions Jev passes untouched and
unlogged; one that mentions Jev but cites nothing has only the quotes it gives as the docs' words checked. A quote that
is not on its cited section, a citation that names no section, or a quote with no citation in reach blocks the stop
once, with the failing rows (never page text), so the model corrects the quote, cites the section that holds it, or
labels it unverified. The next stop passes (Claude Code sets stop_hook_active). Any fault passes and is logged.
A quality check, not a security boundary. Logs counts to <data>/logs/answer_check.jsonl unless JEV_LOG=off."""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jev_terms import ROOT, JEV, data_dir, log_event

CITES = re.compile(r"(?:docs|cookbooks|patterns|blog)/")
REASON_CAP = 4000
TAIL = ("fix each line: correct the quote from its section (read.py '<id>'), cite the section that holds it, or label "
        "it unverified; wording you made up (an example question or option) goes in backticks, not quotation marks. "
        "Then send the whole corrected answer, with no note about this check.")


def _from_transcript(path):
    """The text of the last assistant message that has text, from a Claude Code transcript (JSON lines)."""
    last = None
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if e.get("type") != "assistant":
                continue
            parts = (e.get("message") or {}).get("content") or []
            text = "\n".join(p.get("text", "") for p in parts if isinstance(p, dict) and p.get("type") == "text")
            if text.strip():
                last = text
    return last


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
