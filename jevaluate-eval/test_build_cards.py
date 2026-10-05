import json, pathlib, sys
import pytest
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import build_cards as bc

PACKET = """# PROJECT: o/r

## FILE: README.md
# r
A bot powered by Jev from TypeSafe.
Install it.

## FILE: src/app.py
(keyword lines, numbered)
3: from typesafe_sdk import TypeSafeClient
5: client = TypeSafeClient(api_key=k)
9: r = client.system_one(model="jev-1.13.0", state=s, questions=q)
10: if r.answers["spam"].probability > 0.8:
11:     msg.delete()
"""

def notes(**kw):
    base = {"summary": "A chat bot.", "lines": {"README.md:2": "The README says a TypeSafe model powers the bot.",
            "src/app.py:3": "Imports the TypeSafe SDK.", "src/app.py:5": "Connects to TypeSafe with an API key.",
            "src/app.py:9": "Sends the state and questions to the model."},
            "actions": [["src/app.py", 10, "Checks whether the spam answer is above 0.8."], ["src/app.py", 11, "Deletes the message."]]}
    base.update(kw); return base

def test_parse_numbers_whole_and_excerpted_files():
    files = bc.parse(PACKET)
    assert files["README.md"][2] == "A bot powered by Jev from TypeSafe."
    assert files["src/app.py"][11].strip() == "msg.delete()"

def test_card_has_calls_claims_and_actions():
    card = bc.card("x", PACKET, notes())
    assert [c["where"] for c in card["calls"]] == ["src/app.py:3", "src/app.py:5", "src/app.py:9"]
    assert card["claims"][0]["where"] == "README.md:2" and "powered by Jev" in card["claims"][0]["line"]
    assert card["actions"][1] == {"where": "src/app.py:11", "line": "msg.delete()", "says": "Deletes the message."}

def test_no_hosted_call_found():
    card = bc.card("x", "# PROJECT: o/r\n\n## FILE: README.md\nThis tool uses Jev for every decision.\n", {"summary": "s", "lines": {"README.md:1": "The README names the model."}, "actions": []})
    assert card["calls"] == [] and card["claims"][0]["where"] == "README.md:1"

def test_refuses_undescribed_line():
    n = notes(); del n["lines"]["src/app.py:5"]
    with pytest.raises(SystemExit, match="src/app.py:5"): bc.card("x", PACKET, n)

def test_refuses_action_not_in_packet():
    with pytest.raises(SystemExit, match="not in the packet"): bc.card("x", PACKET, notes(actions=[["src/app.py", 40, "Does a thing."]]))

@pytest.mark.parametrize("word", ["workflow", "very high", "false marketing", "stakes", "1a", "display", "agent-tool", "low",
                                  "high-stakes", "very-high", "name-only", "integrations", "libraries", "Mentioned", "clients", "not-yet-rated"])
def test_refuses_verdict_words(word):
    n = notes(); n["actions"][1][2] = f"Deletes the message, {word}."
    with pytest.raises(SystemExit, match="verdict word"): bc.card("x", PACKET, n)

def test_claims_capped_at_six_sentences_and_short_lines_skipped():
    readme = "# Jev bot\n" + "\n".join(f"Line {i} says the bot runs on TypeSafe Jev today." for i in range(9))
    card = bc.card("x", "# PROJECT: o/r\n\n## FILE: README.md\n" + readme + "\n", {"summary": "s", "lines": {f"README.md:{i}": "Names the model." for i in range(2, 11)}, "actions": []})
    assert [c["where"] for c in card["claims"]] == [f"README.md:{i}" for i in range(2, 8)] and card["more_claims"] == 3

def test_wrapped_readme_sentence_joined_and_image_tags_skipped():
    readme = '<img alt="Logo for the Jev Agent Harness project" src="x.svg">\nThe "Jev" call in this demo is a\nmocked stand-in, a rule-based stub.\nNext.'
    card = bc.card("x", "# PROJECT: o/r\n\n## FILE: README.md\n" + readme + "\n", {"summary": "s", "lines": {"README.md:2": "Says the call is a stub."}, "actions": []})
    assert card["claims"] == [{"where": "README.md:2-3", "line": 'The "Jev" call in this demo is a mocked stand-in, a rule-based stub.', "says": "Says the call is a stub."}]

def test_headings_are_not_claims():
    readme = "# Jev Sentiment Analyzer for support teams\nWe use Jev to route every support ticket fast.\n"
    card = bc.card("x", "# PROJECT: o/r\n\n## FILE: README.md\n" + readme, {"summary": "s", "lines": {"README.md:2": "Says tickets are routed."}, "actions": []})
    assert [c["where"] for c in card["claims"]] == ["README.md:2"]


# --- Review fix 7 (2026-09-30): a fixture packet's own line numbers are the line numbers ---
def test_parse_keeps_the_numbers_a_fixture_packet_carries():
    packet = (pathlib.Path(__file__).parent / "cases" / "email-tagger.md").read_text()
    app = bc.parse(packet)["app.py"]
    assert sorted(app) == [1, 2, 3, 5, 6, 14, 23, 24, 25]
    assert "client.system_one(" in app[23] and app[5].startswith("client = TypeSafeClient(")

def test_a_fixture_call_line_is_found_at_its_own_number():
    import build_cards, jev_callsites
    packet = (pathlib.Path(__file__).parent / "cases" / "email-tagger.md").read_text()
    assert 23 in jev_callsites.calls_in(build_cards.parse(packet).items())["app.py"]

def test_a_whole_file_with_a_line_that_is_not_numbered_still_counts_from_one():
    files = bc.parse("## FILE: a.py\nx = 1\n7: y = 2\n")
    assert files["a.py"] == {1: "x = 1", 2: "7: y = 2"}
