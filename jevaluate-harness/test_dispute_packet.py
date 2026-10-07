"""Blind tiebreaker packet: the rule, the cited code and two unlabeled answers; nothing that says which rater wrote which."""
import pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent / "scripts"))
import dispute_packet as dp

RATING = """---
project: Proj
rater: {rater}
---
## Facts
- F8 Options cover every case, no overlap -- {v}. {why} (`src/route.py:3`)
"""


def setup(tmp_path):
    ev = tmp_path / "ev" / "files"; ev.mkdir(parents=True)
    (ev / "src__route.py").write_text("TEAMS = ['refund', 'billing']\n\nanswer = choice('Which team?', TEAMS)\n")
    a = tmp_path / "a.md"; a.write_text(RATING.format(rater="claude-sonnet-5-5", v="yes", why="Sonnet read the options as distinct"))
    b = tmp_path / "b.md"; b.write_text(RATING.format(rater="gpt-6-sol", v="no", why="A refund is billing, as GPT-6 Sol notes"))
    return a, b, tmp_path / "ev"


def test_packet_has_rule_code_and_two_blind_answers(tmp_path):
    a, b, ev = setup(tmp_path)
    text = dp.packet(a, b, "F8", ev, seed=1)
    assert "| F8 Options cover every case, no overlap |" in text            # the rubric row, verbatim
    assert "answer = choice('Which team?', TEAMS)" in text                 # the cited excerpt
    assert "Answer A" in text and "Answer B" in text
    for name in ("sonnet", "claude", "gpt", "sol", "codex", str(a), str(b), "a.md", "b.md"):
        assert not re.search(rf"\b{re.escape(name)}\b", text, re.I), name


def test_order_is_seeded(tmp_path):
    a, b, ev = setup(tmp_path)
    assert dp.packet(a, b, "F8", ev, seed=1) == dp.packet(a, b, "F8", ev, seed=1)
    orders = {dp.packet(a, b, "F8", ev, seed=s).index("-- yes") < dp.packet(a, b, "F8", ev, seed=s).index("-- no") for s in range(12)}
    assert orders == {True, False}


def test_code_excerpt_is_left_exactly_as_written(tmp_path):
    a, b, ev = setup(tmp_path)
    (ev / "files" / "src__route.py").write_text("import anthropic\nsol = 1\nanswer = choice('Which team?', TEAMS)\n")
    text = dp.packet(a, b, "F8", ev, seed=1)
    assert "import anthropic" in text and "sol = 1" in text
    for name in ("gemini", "fable", "grok"):
        b.write_text(RATING.format(rater="x", v="no", why=f"{name.capitalize()} reads a refund as billing"))
        assert name not in dp.packet(a, b, "F8", ev, seed=1).split("## The two answers")[1].lower()
