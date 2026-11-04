import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from validate_decodes import validate, value_stats  # noqa: E402

TEMPLATE = {"sections": {
    "scene": {"list": False, "fields": {
        "setting": {"type": "category", "values": ["outdoor/beach", "indoor/office"]},
        "lighting": {"type": "text"}}},
    "people": {"list": True, "id_prefix": "p", "fields": {
        "posture": {"type": "text"},
        "touching_other_person": {"type": "boolean"}}},
    "text": {"list": True, "id_prefix": "t", "fields": {
        "reading": {"type": "text"}, "steering_text": {"type": "boolean"}}},
}}

GOOD = {"image": "image_01.jpg", "raw": "Two people sit on sand.", "sections": {
    "scene": {"setting": {"value": "outdoor/beach", "certainty": "clear"},
              "lighting": {"value": "bright sun", "certainty": "likely"}},
    "people": [
        {"id": "p1", "posture": {"value": "sitting", "certainty": "clear"},
         "touching_other_person": {"value": False, "certainty": "clear"}},
        {"id": "p2", "posture": {"value": "not_visible", "certainty": "clear"},
         "touching_other_person": {"value": "unclear", "certainty": "unclear"}}],
    "text": [],
}}


def errs(decode):
    return validate(decode, TEMPLATE)[0]


def test_good_decode_passes():
    assert errs(GOOD) == []


def test_missing_field_in_list_item():
    d = copy.deepcopy(GOOD)
    del d["sections"]["people"][1]["posture"]
    assert any("people[1].posture" in e and "missing" in e for e in errs(d))


def test_missing_section():
    d = copy.deepcopy(GOOD)
    del d["sections"]["text"]
    assert any("text" in e and "missing section" in e for e in errs(d))


def test_missing_or_bad_certainty():
    d = copy.deepcopy(GOOD)
    del d["sections"]["scene"]["lighting"]["certainty"]
    d["sections"]["people"][0]["posture"]["certainty"] = "sure"
    e = errs(d)
    assert any("scene.lighting" in x and "certainty" in x for x in e)
    assert any("people[0].posture" in x and "certainty" in x for x in e)


def test_loose_absence_is_an_error():
    d = copy.deepcopy(GOOD)
    d["sections"]["scene"]["lighting"]["value"] = "None"
    d["sections"]["people"][0]["posture"]["value"] = None
    e = errs(d)
    assert any("scene.lighting" in x and "not_visible" in x for x in e)
    assert any("people[0].posture" in x and "not_visible" in x for x in e)


def test_category_out_of_list():
    d = copy.deepcopy(GOOD)
    d["sections"]["scene"]["setting"]["value"] = "outdoor/park"
    assert any("scene.setting" in x and "outdoor/park" in x for x in errs(d))


def test_boolean_must_be_bool_or_sentinel():
    d = copy.deepcopy(GOOD)
    d["sections"]["people"][0]["touching_other_person"]["value"] = "yes"
    assert any("touching_other_person" in x for x in errs(d))


def test_ids_required_prefixed_and_unique():
    d = copy.deepcopy(GOOD)
    d["sections"]["people"][1]["id"] = "p1"
    assert any("duplicate id" in x for x in errs(d))
    d["sections"]["people"][1]["id"] = "person2"
    assert any("id" in x and "p" in x for x in errs(d))
    del d["sections"]["people"][1]["id"]
    assert any("people[1]" in x and "id" in x for x in errs(d))


def test_field_not_an_object():
    d = copy.deepcopy(GOOD)
    d["sections"]["scene"]["lighting"] = "bright"
    assert any("scene.lighting" in x and "value" in x for x in errs(d))


def test_extra_field_is_a_warning_not_error():
    d = copy.deepcopy(GOOD)
    d["sections"]["scene"]["mood"] = {"value": "calm", "certainty": "likely"}
    e, w = validate(d, TEMPLATE)
    assert e == [] and any("scene.mood" in x for x in w)


def test_text_section_needs_steering_flag():
    t = copy.deepcopy(TEMPLATE)
    del t["sections"]["text"]["fields"]["steering_text"]
    _, w = validate(GOOD, t)
    assert any("steering_text" in x for x in w)


def test_missing_raw_pass():
    d = copy.deepcopy(GOOD)
    d["raw"] = ""
    assert any("raw" in x for x in errs(d))


def test_value_stats_counts_categories_and_booleans():
    st = value_stats([GOOD, GOOD], TEMPLATE)
    assert st["scene.setting"] == {"outdoor/beach": 2}
    assert st["people[].touching_other_person"] == {"False": 2, "unclear": 2}
    assert "scene.lighting" not in st
