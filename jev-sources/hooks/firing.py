"""When the reminder fires. decide() is used by the hook, the scoring script and the tests, so the rule that was
measured is the rule that runs. Candidate rules were fixed on 2026-10-14 before any labels existed."""
import re
from jev_terms import JEV, HANDBACK, DESIGN, topic_text

CONTINUATION = re.compile(r"^\s*This session is being continued from a previous conversation", re.I)
# Jev 1.14 terms today's JEV pattern misses ("Box" alone is a common word, so only the compound counts).
EXTRA = re.compile(r"\bbox (primitive|question)s?\b|\btypesafe-danger-zone[\w-]*", re.I)
RULES = ("current", "skip_continuations", "needs_design_word", "once_per_topic", "combined")
WINDOW = 10  # prompts in one session within which the same Jev words don't fire again
DEFAULT_RULE = "skip_continuations"  # picked on blind-labeled real prompts


def jev_words(prompt, extra=True):
    t = topic_text(prompt)
    found = {m.group(0).lower() for m in JEV.finditer(t)}
    if extra:
        # header names are usually in backticks, which topic_text strips, so EXTRA also reads the raw prompt
        for s in (t, prompt):
            found |= {m.group(0).lower() for m in EXTRA.finditer(s)}
    return sorted(found)


def decide(prompt, rule="current", recent=frozenset()):
    """(fire, reason, words). recent: Jev words that fired in this session within the last WINDOW prompts."""
    if rule not in RULES:
        raise ValueError(f"unknown rule {rule!r}")
    if not isinstance(prompt, str) or HANDBACK.search(prompt):
        return False, "handback", []
    words = jev_words(prompt, extra=(rule != "current"))  # "current" stays exactly today's hook
    if not words:
        return False, "no_jev_word", []
    if rule == "current":
        return True, "jev_word", words
    if CONTINUATION.search(prompt):
        return False, "continuation", words
    design = bool(DESIGN.search(topic_text(prompt)))
    if rule in ("needs_design_word", "combined") and not design:
        return False, "no_design_word", words
    if rule in ("once_per_topic", "combined") and set(words) <= set(recent):
        return False, "repeat", words
    return True, "jev_design" if design else "jev_word", words


def step(state, prompt, rule):
    """One prompt through the rule, advancing the session state. The hook and score_rules.py both call this, so the
    window is computed one way. Every prompt the hook sees advances n, handbacks and notifications included."""
    state = {"n": state.get("n", 0), "fires": list(state.get("fires", []))}
    recent = {w for n, ws in state["fires"] if state["n"] - n < WINDOW for w in ws}
    fire, reason, words = decide(prompt, rule, recent)
    state["n"] += 1
    if fire:
        state["fires"] = (state["fires"] + [[state["n"], words]])[-50:]
    return fire, reason, words, state
