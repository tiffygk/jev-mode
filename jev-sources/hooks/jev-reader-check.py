#!/usr/bin/env python3
"""SubagentStop: a reader subagent whose reply starts `JEV-READER: plan <id> batch <n>` has its findings checked by
scripts/check_findings.py before it returns. A bad quote, a finding outside its batch, page text, too many findings or
no findings blocks the stop once per agent, with the failing rows (never section text), so the reader fixes them while
it still holds the pages. A reply with finding lines but no JEV-READER line is sent back once to add it (its batch
would otherwise count as missing). The second stop of the same agent passes (loop guard). Any fault passes and is logged.
A quality check, not a security boundary. Logs to <data>/logs/reader_check.jsonl unless JEV_LOG=off."""
import json, os, re, sys, tempfile, time
try:
    import fcntl
except ImportError:  # Windows: no lock; the guard may then miss a record when readers stop together
    fcntl = None
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jev_terms import ROOT, data_dir, log_event, private_dirs

HEADER = re.compile(r"^JEV-READER:\s*plan\s+([A-Za-z0-9_-]+)\s+batch\s+(\d+)(?=[\s).:]|$)")  # same as check_findings.HEADER
MARKS = re.compile(r"[*`]|^_+|_+$")  # underscores only at the line's ends, so a plan id keeps its own
REASON_CAP = 4000
STATE_CAP = 500
LOCK_WAIT = 2.0  # seconds
TAIL = "fix these lines and reply again, starting with the JEV-READER line"


def _state_path():
    return os.path.join(data_dir(), "logs", "reader_check_state.json")


def _seen():
    try:
        with open(_state_path(), encoding="utf-8") as f:
            ids = json.load(f).get("agents")
        return [x for x in ids if isinstance(x, str)] if isinstance(ids, list) else []
    except (OSError, ValueError, AttributeError):
        return []


def _first_block(agent_id):
    """True, and agent_id recorded, when this agent has not been sent back before. The check and the record happen
    under one lock, with a uniquely named temp file, so readers stopping together each get exactly one block."""
    d = os.path.dirname(_state_path())
    private_dirs(d)
    lock = os.open(os.path.join(d, "reader_check_state.lock"), os.O_WRONLY | os.O_CREAT, 0o600)
    try:
        if fcntl:
            deadline = time.monotonic() + LOCK_WAIT
            while True:  # a stalled hook holding the lock must not hold every other reader: give up and pass
                try:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    if time.monotonic() > deadline:
                        raise TimeoutError("reader_check_state.lock held too long")
                    time.sleep(0.05)
        seen = _seen()
        if agent_id in seen:
            return False
        ids = seen + [agent_id]
        fd, tmp = tempfile.mkstemp(dir=d, prefix=".reader_check_state.", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump({"agents": ids[-STATE_CAP:]}, f)
            os.replace(tmp, _state_path())
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)
        return True
    finally:
        os.close(lock)  # closing releases the lock


def _reason(rows):
    tail = f"\n{TAIL}"
    out, used = [], len(tail)
    for i, r in enumerate(rows):
        more = f"\n... and {len(rows) - i} more failing lines"
        if used + len(r) + 1 + len(more) > REASON_CAP:
            out.append(more.strip("\n"))
            break
        out.append(r)
        used += len(r) + 1
    return ("\n".join(out) + tail)[:REASON_CAP]


def main():
    sid = agent = plan_id = batch = None
    try:
        p = json.load(sys.stdin)
        if not isinstance(p, dict):
            raise ValueError("input is not an object")
        sid, agent, msg = p.get("session_id"), p.get("agent_id"), p.get("last_assistant_message")
        if not isinstance(msg, str):
            raise ValueError("no last_assistant_message")
        lines = [x for x in msg.split("\n") if x.strip()]
        lines = [MARKS.sub("", x.strip()) if "JEV-READER" in x else x for x in lines]  # **bold** or `code` around the header
        start = next((i for i, x in enumerate(lines) if HEADER.match(x.strip())), None)  # a short preamble may come first
        if start is None:
            if not any(x.strip().startswith("FINDING:") and "| CITE AS:" in x for x in lines):
                return 0  # not a reader reply: say nothing, log nothing
            if not isinstance(agent, str) or not agent or not _first_block(agent):
                return 0  # finding lines with no header: the reader dropped it, so its batch would count as missing
            log_event("reader_check", decision="block_no_header", session=sid if isinstance(sid, str) else "-", agent_id=agent)
            print(json.dumps({"decision": "block", "reason": "NO HEADER | your reply has FINDING lines but no JEV-READER "
                              "line\nreply again, starting with the JEV-READER line from your brief, on a line of its own: "
                              "JEV-READER: plan <id> batch <n>. If you are not a reader for a Jev Sources reading plan, "
                              "reply again unchanged."}))
            return 0
        pre, lines = lines[:start], lines[start:]
        m = HEADER.match(lines[0].strip())
        plan_id, batch = m.group(1)[:80], int(m.group(2))
        if not isinstance(agent, str) or not agent:
            raise ValueError("no agent_id")
        ctx = dict(session=sid if isinstance(sid, str) else "-", agent_id=agent, plan=plan_id, batch=batch)
        # only this reply's own batch: drop anything from a second JEV-READER line on
        own = []
        for i, x in enumerate(lines):
            if i and x.strip().startswith("JEV-READER:"):
                break
            own.append(x)
        sys.path.insert(0, os.path.join(ROOT, "scripts"))
        import check_findings
        rows, summary, ok = check_findings.check(plan_id, "\n".join(pre + own) + "\n")  # the preamble is checked too
        if summary is None:
            log_event("reader_check", decision="no_plan", **ctx)
            return 0
        bad = [r for r in rows if f"| b{batch} |" in r and not r.startswith("OK |")]
        plan = check_findings._load(plan_id) or {}
        if batch not in {b.get("n") for b in plan.get("batches", [])}:
            bad = [f"BAD BATCH | b{batch} | batch {batch} is not in plan {plan_id}; copy the JEV-READER line from your brief"]
        counts = dict(findings=sum(1 for x in own if x.strip().startswith("FINDING:")), failed=len(bad))
        if not bad:
            log_event("reader_check", decision="clean", **ctx, **counts)
            return 0
        if not _first_block(agent):
            log_event("reader_check", decision="loop_guard", **ctx, **counts)
            return 0
        log_event("reader_check", decision="block", **ctx, **counts)
        print(json.dumps({"decision": "block", "reason": _reason(bad)}))
        return 0
    except BaseException as e:  # fail open: a fault in this check must never hold a reader back
        if isinstance(e, SystemExit) and e.code in (0, None):
            return 0
        log_event("reader_check", decision="error", session=sid if isinstance(sid, str) else "-",
                  agent_id=agent if isinstance(agent, str) else "-", plan=plan_id or "-", batch=batch,
                  error=f"{type(e).__name__}: {e}"[:200])
        return 0


if __name__ == "__main__":
    sys.exit(main())
