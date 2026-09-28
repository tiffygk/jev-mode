import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from agreement import compare, same_value  # noqa: E402

TEMPLATE = {"sections": {
    "scene": {"list": False, "fields": {"setting": {"type": "category", "values": ["a", "b"]},
                                         "lighting": {"type": "text"}}},
    "people": {"list": True, "id_prefix": "p", "fields": {"posture": {"type": "text"}}}}}


def f(v, c="clear"):
    return {"value": v, "certainty": c}


def dec(setting, lighting, postures):
    return {"raw": "x", "sections": {"scene": {"setting": f(setting), "lighting": f(lighting)},
                                     "people": [{"id": f"p{i+1}", "posture": f(p)} for i, p in enumerate(postures)]}}


def test_same_value_text_is_fuzzy_category_is_exact():
    assert same_value("Bright midday sun", "bright  midday sun.", "text")
    assert same_value("bright sun overhead", "bright sun", "text")
    assert not same_value("dim indoor light", "bright sun", "text")
    assert not same_value("a", "b", "category")


def test_full_agreement():
    a = {"i1": dec("a", "sun", ["sitting"])}
    r = compare(a, a, TEMPLATE)
    assert r["fields"]["scene.setting"]["agree"] == 1 and r["fields"]["scene.setting"]["n"] == 1
    assert r["disagreements"] == []


def test_disagreement_listed_with_both_readings():
    a = {"i1": dec("a", "sun", ["sitting"])}
    b = {"i1": dec("b", "sun", ["sitting"])}
    r = compare(a, b, TEMPLATE)
    assert r["fields"]["scene.setting"]["agree"] == 0
    assert ("i1", "scene.setting", "a", "b") in r["disagreements"]


def test_item_count_mismatch_counts_against_fields_and_count():
    a = {"i1": dec("a", "sun", ["sitting", "standing"])}
    b = {"i1": dec("a", "sun", ["sitting"])}
    r = compare(a, b, TEMPLATE)
    assert r["fields"]["people.count"]["agree"] == 0
    assert r["fields"]["people[].posture"]["n"] == 2 and r["fields"]["people[].posture"]["agree"] == 1


def test_unclear_is_flagged_not_disagreement():
    a = {"i1": dec("a", "unclear", ["sitting"])}
    b = {"i1": dec("a", "sun", ["sitting"])}
    r = compare(a, b, TEMPLATE)
    assert r["fields"]["scene.lighting"]["unclear"] == 1
    assert ("i1", "scene.lighting", "unclear", "sun") in r["flagged"]


def test_only_shared_images_compared():
    a = {"i1": dec("a", "sun", []), "i2": dec("a", "sun", [])}
    b = {"i1": dec("a", "sun", [])}
    r = compare(a, b, TEMPLATE)
    assert r["images"] == ["i1"] and r["only_one_side"] == ["i2"]
