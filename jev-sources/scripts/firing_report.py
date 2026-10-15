#!/usr/bin/env python3
"""Report on the prompt reminder's decisions: per day, prompts seen, fires, fire rate, reasons and top words. When the
route log (route.py, jev.py) or a session ledger (the jev-ledger hook) exists it also lists likely needless fires, likely missed fires,
and READ FULL sections that were routed but never read.

Usage: firing_report.py [--since YYYY-MM-DD]. Reads <data>/logs/ ($JEV_SOURCES_DATA or ~/.claude/jev-sources-data)."""
import argparse, hashlib, json, os, sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta

WINDOW = timedelta(minutes=15)


def _rows(path):
    out = []
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                if isinstance(r, dict):
                    out.append(r)
    except OSError:
        pass
    return out


def _t(ts):
    try:
        return datetime.strptime(str(ts)[:19], "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        return None


def _sid_hash(sid):
    return hashlib.sha1(str(sid).encode("utf-8")).hexdigest()[:16]


def _top(counter, n=8):
    return ", ".join(f"{k}={v}" for k, v in counter.most_common(n)) or "none"


def _ledger(logs):
    """{sha1(session)[:16]: [rows]} from <logs>/ledger/*.jsonl, or None when there is no ledger."""
    d = os.path.join(logs, "ledger")
    if not os.path.isdir(d):
        return None
    led = {}
    for name in sorted(os.listdir(d)):
        if name.endswith(".jsonl"):
            led[name[:-6]] = _rows(os.path.join(d, name))
    return led or None


def _day_table(rem):
    days = defaultdict(list)
    for r in rem:
        days[str(r.get("ts", ""))[:10]].append(r)
    lines = []
    for day in sorted(days):
        rs = days[day]
        fires = sum(1 for r in rs if r.get("fire"))
        lines.append(f"{day}  prompts={len(rs)}  fires={fires}  rate={round(100 * fires / len(rs))}%")
        lines.append("    reasons: " + _top(Counter(r.get("reason") for r in rs)))
        lines.append("    top words: " + _top(Counter(w for r in rs for w in (r.get("words") or []))))
    return lines


def _ref_ids(r):
    """Section ids in a ledger row: refs is a list of "path#heading"; a routed ref ends in " (READ FULL)" or " (EXTRACT)"."""
    v = r.get("refs")
    return [v] if isinstance(v, str) else [x for x in (v or []) if isinstance(x, str)]


def _routed_full(ref):
    """The "path#heading" of a routed READ FULL ref, or None for an EXTRACT."""
    if ref.endswith(" (EXTRACT)"):
        return None
    return ref[:-len(" (READ FULL)")] if ref.endswith(" (READ FULL)") else ref


def _read_full_ids(routes):
    """Ids a route call marked READ FULL (route.jsonl: sections is a list of {id, depth, ...})."""
    return {s["id"] for r in routes for s in (r.get("sections") or [])
            if isinstance(s, dict) and s.get("depth") == "READ FULL" and s.get("id")}


def _read_in_full_ids(reads):
    """Ids read in full (read.jsonl, from read.py and jev.py: extract is true for an extract, false for a full read)."""
    return {r["id"] for r in reads if r.get("id") and not r.get("extract")}


def _join_by_session(fires, routes, led):
    """Return (fires without a later source call, source calls without an earlier fire), joined on the hashed session
    id. A source call is a ledger row: "routed" from route.py, "read" from read.py or jev.py (jev.py writes only "read")."""
    routed = defaultdict(list)
    for h, rows in led.items():
        for r in rows:
            if r.get("event") in ("routed", "read") and _t(r.get("ts")):
                routed[h].append(_t(r["ts"]))
    fire_ts = defaultdict(list)
    for r in fires:
        fire_ts[_sid_hash(r.get("session"))].append(_t(r.get("ts")))
    needless = [r for r in fires if not any(x >= _t(r.get("ts")) for x in routed[_sid_hash(r.get("session"))])]
    missed = []
    for h, ts in sorted(routed.items()):
        for x in ts:
            if not any(f <= x for f in fire_ts[h]):
                missed.append((x.strftime("%Y-%m-%dT%H:%M:%SZ"), h))
    return needless, missed


def _same_place(route, fire):
    """jev.py's route lines carry no cwd; those match on the time window alone."""
    return "cwd" not in route or route.get("cwd") == fire.get("cwd")


def _join_by_cwd(fires, routes):
    needless = []
    for r in fires:
        t = _t(r.get("ts"))
        if not any(_same_place(x, r) and t <= _t(x["ts"]) <= t + WINDOW for x in routes):
            needless.append(r)
    calls, seen = [], set()
    for x in routes:  # jev.py writes one route line per phrasing, all with the same ts: one call
        if x.get("via") == "jev.py":
            if x.get("ts") in seen:
                continue
            seen.add(x.get("ts"))
        calls.append(x)
    missed = []
    for x in calls:
        t = _t(x["ts"])
        if not any(_same_place(x, r) and t - WINDOW <= _t(r["ts"]) <= t for r in fires):
            missed.append((str(x.get("ts")), x.get("question") or x.get("cwd")))
    return needless, missed


def report(data, since=None):
    logs = os.path.join(os.path.expanduser(data), "logs")
    rem = [r for r in _rows(os.path.join(logs, "reminder.jsonl")) if not since or str(r.get("ts", ""))[:10] >= since]
    out = ["Reminder decisions" + (f" since {since}" if since else "")]
    out += _day_table(rem) or ["no reminder log lines"]
    route_p, read_p = os.path.join(logs, "route.jsonl"), os.path.join(logs, "read.jsonl")
    led = _ledger(logs)
    if not (os.path.exists(route_p) or led):
        return "\n".join(out) + "\n"
    routes = [r for r in _rows(route_p) if _t(r.get("ts")) and (not since or str(r["ts"])[:10] >= since)]
    reads = _rows(read_p)  # empty when read.py never logged: every READ FULL item then counts as unread
    fires = [r for r in rem if r.get("fire") and _t(r.get("ts"))]
    if led:
        out += ["", "Join: by session (ledger)"]
        needless, missed = _join_by_session(fires, routes, led)
        missed = [(ts, "session " + h) for ts, h in missed if not since or ts[:10] >= since]
    else:
        out += ["", "Join: by cwd + 15-minute window (no session ledger)"]
        needless, missed = _join_by_cwd(fires, routes)
    out.append(f"Fires with no source call afterwards: {len(needless)} (likely needless)")
    out += [f"    {r.get('ts')}  {r.get('prompt')!r}" for r in needless]
    out.append(f"Source calls with no fire before them: {len(missed)} (likely missed)")
    out += [f"    {ts}  {what}" for ts, what in missed]
    # READ FULL sections a route call returned that nothing read: from the ledger when there is one, else route/read logs
    if led:
        returned = {_routed_full(ref) for rows in led.values() for r in rows if r.get("event") == "routed" for ref in _ref_ids(r)}
        returned.discard(None)
        was_read = {ref for rows in led.values() for r in rows if r.get("event") == "read" for ref in _ref_ids(r)}
    else:
        returned = _read_full_ids(routes)
        was_read = _read_in_full_ids(reads)
    unread = sorted(returned - was_read)
    out.append(f"READ FULL sections routed but never read: {len(unread)}")
    out += [f"    {ref}" for ref in unread]
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", help="YYYY-MM-DD")
    a = ap.parse_args()
    data = os.environ.get("JEV_SOURCES_DATA") or "~/.claude/jev-sources-data"
    sys.stdout.write(report(data, a.since))


if __name__ == "__main__":
    main()
