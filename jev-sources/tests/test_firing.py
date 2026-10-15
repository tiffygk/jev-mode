import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "hooks"))
import pytest
from firing import decide, RULES, step, WINDOW

CONT = "This session is being continued from a previous conversation that ran out of context. Jev plans ..."


def test_current_matches_todays_hook():
    assert decide("is a Noul right here?", "current")[0]
    assert not decide("make a choice of font", "current")[0]


def test_continuation_skipped_except_current():
    assert decide(CONT, "current")[0]
    for r in ("skip_continuations", "needs_design_word", "once_per_topic", "combined"):
        assert decide(CONT, r) == (False, "continuation", ["jev"])


def test_design_word_needed():
    assert decide("fix the table in the jevaluate README", "needs_design_word")[:2] == (False, "no_design_word")
    assert decide("should Jev get one request with all the questions?", "needs_design_word")[0]


def test_repeat_only_suppresses_same_words():
    assert decide("does Jev batch questions?", "once_per_topic", frozenset({"jev"}))[1] == "repeat"
    assert decide("is a Noul right for this?", "once_per_topic", frozenset({"jev"}))[0]


def test_handback_and_non_text():
    assert decide("<task-notification> Jev done", "combined")[1] == "handback"
    assert decide(None, "combined") == (False, "handback", [])


def test_unknown_rule():
    with pytest.raises(ValueError):
        decide("Jev", "nope")


def test_1_14_terms_count_except_in_current():
    q = "should I use a Box question to find the mug in this photo?"
    assert not decide(q, "current")[0]
    assert decide(q, "skip_continuations")[0]
    assert not decide("put the logo in a box on the slide", "skip_continuations")[0]


def test_danger_zone_header_in_backticks():
    q = "does `TypeSafe-Danger-Zone-Images` change the limits?"
    assert decide(q, "skip_continuations")[0]
    assert not decide(q, "current")[0]


def test_step_walks_a_session():
    state = {}
    fire, reason, words, state = step(state, "does Jev batch questions?", "once_per_topic")
    assert (fire, reason, words) == (True, "jev_design", ["jev"])
    fire, reason, words, state = step(state, "<task-notification> done", "once_per_topic")
    assert (fire, reason) == (False, "handback")
    fire, reason, words, state = step(state, "fix the README table", "once_per_topic")
    assert (fire, reason) == (False, "no_jev_word")
    fire, reason, words, state = step(state, "and does Jev cap tokens?", "once_per_topic")
    assert (fire, reason) == (False, "repeat")
    fire, reason, words, state = step(state, "is a Noul right here?", "once_per_topic")
    assert fire and words == ["noul"]
    fire, reason, words, state = step(state, "is a Noul still right?", "once_per_topic")
    assert (fire, reason) == (False, "repeat")
    assert state["n"] == 6
    for _ in range(10):
        fire, reason, words, state = step(state, "fix the README table", "once_per_topic")
    fire, reason, words, state = step(state, "does Jev batch questions?", "once_per_topic")
    assert fire and words == ["jev"]


# firing_report.py, on small invented logs in the shapes route.py, read.py and the ledger write.
import hashlib, json
SCRIPTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts")


def _report(data, since=None):
    sys.path.insert(0, SCRIPTS)
    import firing_report
    return firing_report.report(str(data), since)


def _write(data, name, rows):
    d = data / "logs"; d.mkdir(parents=True, exist_ok=True)
    (d / name).write_text("".join(json.dumps(r) + "\n" for r in rows))


def _rem(ts, session, fire, reason, words, cwd="/w"):
    return {"ts": ts, "session": session, "cwd": cwd, "fire": fire, "reason": reason, "rule": "skip_continuations",
            "words": words, "chars": 10, "prompt": "p"}


REMINDERS = [
    _rem("2026-10-14T10:00:00Z", "s1", True, "jev_design", ["jev"]),
    _rem("2026-10-14T10:05:00Z", "s1", False, "no_jev_word", []),
    _rem("2026-10-14T11:00:00Z", "s2", True, "jev_word", ["noul", "jev"]),
    _rem("2026-10-15T09:00:00Z", "s3", False, "continuation", ["jev"]),
]


def test_report_counts_per_day_and_since(tmp_path):
    _write(tmp_path, "reminder.jsonl", REMINDERS)
    out = _report(tmp_path)
    assert "2026-10-14  prompts=3  fires=2  rate=67%" in out
    assert "2026-10-15  prompts=1  fires=0  rate=0%" in out
    assert "jev_design=1" in out and "no_jev_word=1" in out and "continuation=1" in out
    assert "jev=2" in out and "noul=1" in out
    assert "2026-10-14  prompts" not in _report(tmp_path, "2026-10-15")


def test_report_without_plan_b_logs_has_no_join_section(tmp_path):
    _write(tmp_path, "reminder.jsonl", REMINDERS)
    assert "Join:" not in _report(tmp_path)


def _route(ts, question, sections, cwd="/w"):
    return {"ts": ts, "question": question, "constraint": None, "topics": [], "semantic": False, "cwd": cwd,
            "sections": [{"id": i, "depth": d, "kind": "reference", "by": "topic"} for i, d in sections]}


def test_report_joins_by_session_ledger(tmp_path):
    h = lambda s: hashlib.sha1(s.encode()).hexdigest()[:16]
    _write(tmp_path, "reminder.jsonl", REMINDERS)
    _write(tmp_path, "route.jsonl", [_route("2026-10-14T10:02:00Z", "q1", [("docs/a#1", "READ FULL")]),
                                     _route("2026-10-15T09:30:00Z", "q-missed", [("docs/c#3", "READ FULL")])])
    _write(tmp_path, "read.jsonl", [{"ts": "2026-10-14T10:03:00Z", "id": "docs/a#1", "extract": None, "tokens": 10}])
    led = tmp_path / "logs" / "ledger"; led.mkdir()
    (led / (h("s1") + ".jsonl")).write_text("".join(json.dumps(r) + "\n" for r in [
        {"ts": "2026-10-14T10:02:00Z", "session": "s1", "cwd": "/w", "event": "routed", "refs": ["a.md#One", "b.md#Two"]},
        {"ts": "2026-10-14T10:03:00Z", "session": "s1", "cwd": "/w", "event": "read", "refs": ["a.md#One"]}]))
    (led / (h("s3") + ".jsonl")).write_text(json.dumps(
        {"ts": "2026-10-15T09:30:00Z", "session": "s3", "cwd": "/w", "event": "routed", "refs": ["c.md#Three"]}) + "\n")
    out = _report(tmp_path)
    assert "Join: by session (ledger)" in out
    assert "Fires with no route call afterwards: 1" in out   # s2 fired at 11:00, never routed
    assert "2026-10-14T11:00:00Z" in out
    assert "Route calls with no fire before them: 1" in out  # s3 routed with no fire
    assert "2026-10-15T09:30:00Z" in out
    assert "b.md#Two" in out and "c.md#Three" in out and "a.md#One" not in out.split("READ FULL")[-1]


def test_report_falls_back_to_cwd_and_window(tmp_path):
    _write(tmp_path, "reminder.jsonl", [
        _rem("2026-10-14T10:00:00Z", "s1", True, "jev_word", ["jev"], cwd="/a"),
        _rem("2026-10-14T12:00:00Z", "s2", True, "jev_word", ["jev"], cwd="/b")])
    _write(tmp_path, "route.jsonl", [
        _route("2026-10-14T10:10:00Z", "in window", [("docs/a#1", "READ FULL"), ("docs/b#2", "EXTRACT")], cwd="/a"),  # 10 min after the /a fire: matched
        _route("2026-10-14T12:20:00Z", "too late", [("docs/c#3", "READ FULL")], cwd="/b")])                          # 20 min after: not matched
    _write(tmp_path, "read.jsonl", [
        {"ts": "2026-10-14T10:11:00Z", "id": "docs/a#1", "extract": ["batch"], "tokens": 5},   # an extract is not a full read
        {"ts": "2026-10-14T10:12:00Z", "id": "docs/b#2", "extract": None, "tokens": 50}])      # read in full, but never READ FULL
    out = _report(tmp_path)
    assert "Join: by cwd + 15-minute window (no session ledger)" in out
    assert "Fires with no route call afterwards: 1" in out
    assert "2026-10-14T12:00:00Z" in out
    assert "Route calls with no fire before them: 1" in out
    assert "too late" in out and "in window" not in out.split("Route calls with no fire")[1]
    assert "READ FULL sections routed but never read: 2" in out
    assert "    docs/a#1" in out and "    docs/c#3" in out and "    docs/b#2" not in out


def test_report_with_routes_and_no_read_log(tmp_path):
    _write(tmp_path, "reminder.jsonl", [_rem("2026-10-14T10:00:00Z", "s1", True, "jev_word", ["jev"], cwd="/a"),
                                        _rem("2026-10-14T12:00:00Z", "s2", True, "jev_word", ["jev"], cwd="/b")])
    _write(tmp_path, "route.jsonl", [_route("2026-10-14T10:10:00Z", "q", [("docs/a#1", "READ FULL"), ("docs/b#2", "EXTRACT")], cwd="/a")])
    out = _report(tmp_path)
    assert "Join: by cwd + 15-minute window" in out
    assert "Fires with no route call afterwards: 1" in out
    assert "READ FULL sections routed but never read: 1" in out and "    docs/a#1" in out


# Bars: the picked rule's recall (69/77 = 0.8961) and specificity (197/321 = 0.6137) on blind-labeled real prompts
# (per prompt, empty `recent`), each minus 0.05, rounded down to 3 decimals.
CASES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "firing_cases.json")
with open(CASES_PATH, encoding="utf-8") as _f:
    CASES = json.load(_f)
RECALL_BAR, SPECIFICITY_BAR = 0.846, 0.563
# The invented set weighs messages that only name Jev tools or TypeSafe far more than real prompts do, so it has its
# own specificity bar. Today's rule ("current") scores 18/36 on these cases; the picked rule must not be worse.
# Widening the matcher lowers this number.
PUBLIC_SPECIFICITY_BAR = 0.5


def rates(rows, rule):
    pos = [r for r in rows if r[1]]
    neg = [r for r in rows if not r[1]]
    fired = lambda p: decide(p, rule)[0]
    return sum(fired(p) for p, _ in pos) / max(len(pos), 1), sum(not fired(p) for p, _ in neg) / max(len(neg), 1)


def test_public_cases():
    from firing import DEFAULT_RULE
    rows = [(c["prompt"], c["should_fire"]) for c in CASES]
    recall, spec = rates(rows, DEFAULT_RULE)
    print(f"public recall={recall} specificity={spec}")
    assert recall >= RECALL_BAR, f"recall {recall:.2f}"
    assert spec >= PUBLIC_SPECIFICITY_BAR, f"specificity {spec:.2f}"


@pytest.mark.skipif(not os.environ.get("JEV_FIRING_PRIVATE_CASES"), reason="real labeled prompts live only on the owner's machine")
def test_private_cases():
    from firing import DEFAULT_RULE
    with open(os.environ["JEV_FIRING_PRIVATE_CASES"], encoding="utf-8") as f:
        rows = [json.loads(l) for l in f if l.strip()]
    recall, spec = rates([(r["prompt"], r["label"] == "yes") for r in rows if r["label"] != "unsure"], DEFAULT_RULE)
    assert recall >= RECALL_BAR and spec >= SPECIFICITY_BAR, f"recall {recall:.2f}, specificity {spec:.2f}"
