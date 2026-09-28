import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from people_words import scan  # noqa: E402


def test_flags_gender_pronouns_age_and_relationship(tmp_path):
    (tmp_path / "state.json").write_text(json.dumps({
        "regions": [{"id": "r1", "contents": "a bench behind her"}],
        "people": [{"id": "p1", "clothing": "the young woman wears a cap"},
                   {"id": "p2", "contact": "arm around his girlfriend"}]}))
    words = {w for _, _, w, _ in scan([tmp_path / "state.json"])}
    assert {"her", "young", "woman", "his", "girlfriend"} <= words


def test_clean_text_and_substrings_pass(tmp_path):
    (tmp_path / "d.json").write_text(json.dumps({
        "people": [{"id": "p1", "clothing": "navy polo shirt, manual watch, hershey bar wrapper"},
                   {"id": "p2", "posture": "their hands rest on the bench"}]}))
    assert scan([tmp_path / "d.json"]) == []


def test_user_context_is_exempt(tmp_path):
    (tmp_path / "s.json").write_text(json.dumps({"context": {"role": {"value": "p1 is her manager", "source": "user"}}}))
    assert scan([tmp_path / "s.json"]) == []


def test_image_text_is_exempt_but_raw_is_not(tmp_path):
    (tmp_path / "d.json").write_text(json.dumps({"raw": "p1 stirs a bowl beside her", "sections": {
        "text": [{"id": "t1", "reading": {"value": "she is doing her part", "certainty": "clear"}}]}}))
    hits = scan([tmp_path / "d.json"])
    assert [(p, w) for _, p, w, _ in hits] == [("raw", "her")]


def test_quoted_image_text_in_raw_is_exempt(tmp_path):
    (tmp_path / "d.json").write_text(json.dumps({"raw": "t1 reads 'she is doing her part'; p1 stands beside him"}))
    assert [w for _, _, w, _ in scan([tmp_path / "d.json"])] == ["him"]
