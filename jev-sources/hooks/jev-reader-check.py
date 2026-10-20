#!/usr/bin/env python3
"""SubagentStop: a reader subagent whose reply starts `JEV-READER: plan <id> batch <n>` has its findings checked by
scripts/check_findings.py before it returns. A bad quote, a finding outside its batch, page text, too many findings or
no findings blocks the stop once per agent, with the failing rows (never section text), so the reader fixes them while
it still holds the pages. A reply with finding lines but no JEV-READER line is sent back once to add it (its batch
would otherwise count as missing). The second stop of the same agent passes (loop guard). Any fault passes and is logged.
A quality check, not a security boundary. Logs to <data>/logs/reader_check.jsonl unless JEV_LOG=off."""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jev_terms import ROOT, data_dir, log_event

HEADER = re.compile(r"^JEV-READER: plan (\S+) batch (\d+)\s*$")
REASON_CAP = 4000
STATE_CAP = 500
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


def _remember(agent_id):
    """Add agent_id to the owner-only state file, keeping the newest STATE_CAP ids. The write is atomic."""
    ids = [x for x in _seen() if x != agent_id] + [agent_id]
    d = os.path.dirname(_state_path())
    os.makedirs(os.path.dirname(d), mode=0o700, exist_ok=True)
    os.makedirs(d, mode=0o700, exist_ok=True)
    os.chmod(d, 0o700)
    tmp = _state_path() + ".tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump({"agents": ids[-STATE_CAP:]}, f)
    os.chmod(tmp, 0o600)
    os.replace(tmp, _state_path())


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
        start = next((i for i, x in enumerate(lines) if HEADER.match(x.strip())), None)  # a short preamble may come first
        if start is None:
            if not any(x.strip().startswith("FINDING:") and "| CITE AS:" in x for x in lines):
                return 0  # not a reader reply: say nothing, log nothing
            if not isinstance(agent, str) or not agent or agent in _seen():
                return 0
            _remember(agent)  # finding lines with no header: the reader dropped it, so its batch would count as missing
            log_event("reader_check", decision="block_no_header", session=sid if isinstance(sid, str) else "-", agent_id=agent)
            print(json.dumps({"decision": "block", "reason": "NO HEADER | your reply has FINDING lines but no JEV-READER "
                              "line\nreply again, starting with the JEV-READER line from your brief"}))
            return 0
        lines = lines[start:]
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
        rows, summary, ok = check_findings.check(plan_id, "\n".join(own) + "\n")
        if summary is None:
            log_event("reader_check", decision="no_plan", **ctx)
            return 0
        bad = [r for r in rows if f"| b{batch} |" in r and not r.startswith("OK |")]
        counts = dict(findings=sum(1 for x in own if x.strip().startswith("FINDING:")), failed=len(bad))
        if not bad:
            log_event("reader_check", decision="clean", **ctx, **counts)
            return 0
        if agent in _seen():
            log_event("reader_check", decision="loop_guard", **ctx, **counts)
            return 0
        _remember(agent)
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
