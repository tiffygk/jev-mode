import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from audit_package import answer_words, audit, template_field_words  # noqa: E402

QUESTIONS = {
    "romantic": {"type": "noul", "instructions": "Are `people[0]` and `people[1]` a romantic couple?"},
    "rel": {"type": "choice", "instructions": "What is the relationship between them?",
            "options": {"dating": "A couple who are dating", "coworkers": "Colleagues from the same company"}},
}


def test_answer_words_skip_stopwords_and_paths():
    w = answer_words(QUESTIONS)
    assert {"romantic", "couple", "dating", "coworkers", "colleagues", "relationship"} <= w
    assert "the" not in w and "people" not in w and "are" not in w


def test_audit_finds_stem_matches_with_line(tmp_path):
    (tmp_path / "brief.md").write_text("Describe posture.\nNote any romance cues.\n")
    (tmp_path / "template.json").write_text(json.dumps({"sections": {"scene": {"fields": {"setting": {}}}}}))
    hits = audit(tmp_path, answer_words(QUESTIONS))
    assert ("brief.md", 2, "romantic") in [(h[0], h[1], h[2]) for h in hits]
    assert all(h[0] != "template.json" for h in hits)


def test_allow_list_suppresses(tmp_path):
    (tmp_path / "brief.md").write_text("Record the relationship of each object to the table.\n")
    assert audit(tmp_path, answer_words(QUESTIONS), allow={"relationship"}) == []


def test_no_collisions_on_shared_prefixes(tmp_path):
    q = {"q": {"type": "noul", "instructions": "Is there a close relationship or physical contact?"}}
    (tmp_path / "brief.md").write_text("List related objects and what each bag may contain.\n")
    assert audit(tmp_path, answer_words(q)) == []


def test_template_field_names_become_allowed(tmp_path):
    (tmp_path / "template.json").write_text(json.dumps({"sections": {"people": {"fields": {
        "contact": {"type": "text"}, "mood": {"type": "category", "values": ["romantic", "neutral"]}}}}}))
    allow = template_field_words(tmp_path / "template.json")
    assert "contact" in allow and "romantic" not in allow
    q = {"q": {"type": "noul", "instructions": "Is there physical contact that looks romantic?"}}
    hits = audit(tmp_path, answer_words(q), allow)
    assert [h[2] for h in hits] == ["romantic"]
