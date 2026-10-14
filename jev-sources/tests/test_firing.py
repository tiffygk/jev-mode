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
