#!/usr/bin/env python3
"""PostToolUse hook (matcher Bash): records, per session, which sections route.py listed and which read.py or jev.py
printed in full. One JSON line per command in <data>/logs/ledger/<sha1(session)[:16]>.jsonl, local only; JEV_LOG=off
turns it off. Prints nothing and exits 0 whatever happens."""
import datetime, hashlib, json, os, re, sys

SCRIPT = re.compile(r"""(?:^|[\s/'"=])(route|read|jev)\.py(?=$|[\s'"])""")
ROUTED = re.compile(r"^(READ FULL|EXTRACT)\s*\| [^|]*?\| (.+?) \| \d+ tok", re.M)
SOURCE = re.compile(r"^SOURCE: (.+?) \| KIND: .*?\| READ: (\S+)", re.M)
CITE = re.compile(r"^CITE AS: (.+?) \([^()]*\)(?: \||$)", re.M)


def _data():
    return os.path.expanduser(os.environ.get("JEV_SOURCES_DATA") or "~/.claude/jev-sources-data")


def _text(resp):
    if isinstance(resp, str):
        return resp
    if isinstance(resp, dict) and isinstance(resp.get("stdout"), str):
        return resp["stdout"]
    return ""


def _events(command, out):
    """[(event, refs)] for the scripts the command names. A section read as an extract is not a read."""
    names = set(SCRIPT.findall(command))
    found = []
    if "route" in names:
        refs = [f"{p} ({d})" for d, p in ROUTED.findall(out)]
        if refs:
            found.append(("routed", refs))
    if names & {"read", "jev"}:
        refs = [p for p, how in SOURCE.findall(out) if how != "extract,"]
        refs += [p for p in CITE.findall(out) if p not in refs]
        if refs:
            found.append(("read", list(dict.fromkeys(refs))))
    return found


def main():
    if os.environ.get("JEV_LOG") == "off":
        return
    p = json.loads(sys.stdin.read())
    session = p.get("session_id")
    command = p["tool_input"]["command"]
    if not session or not isinstance(session, str) or not isinstance(command, str):
        return
    events = _events(command, _text(p.get("tool_response")))
    if not events:
        return
    d = os.path.join(_data(), "logs", "ledger")
    os.makedirs(d, exist_ok=True)
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(os.path.join(d, hashlib.sha1(session.encode("utf-8")).hexdigest()[:16] + ".jsonl"), "a", encoding="utf-8") as f:
        for event, refs in events:
            f.write(json.dumps({"ts": ts, "session": session, "cwd": p.get("cwd"), "event": event, "refs": refs}) + "\n")


if __name__ == "__main__":
    try:
        main()
    except BaseException:
        pass
    sys.exit(0)
