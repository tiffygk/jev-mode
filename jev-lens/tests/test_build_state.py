import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from build_state import build_state, unassigned, left_out_md  # noqa: E402

TEMPLATE = {"sections": {
    "scene": {"list": False, "fields": {"setting": {"type": "text"}, "weather": {"type": "text"}}},
    "people": {"list": True, "id_prefix": "p", "fields": {"posture": {"type": "text"}, "shirt": {"type": "text"}}},
    "objects": {"list": True, "id_prefix": "obj", "fields": {"kind": {"type": "text"}}}}}

DECODE = {"image": "image_01.jpg", "raw": "x", "sections": {
    "scene": {"setting": {"value": "beach", "certainty": "clear"},
              "weather": {"value": "sunny", "certainty": "likely"}},
    "people": [{"id": "p1", "posture": {"value": "sitting", "certainty": "clear"},
                "shirt": {"value": "red", "certainty": "clear"}}],
    "objects": [{"id": "obj1", "kind": {"value": "umbrella", "certainty": "clear"}}]}}

KEEP = {"keep": ["scene.setting", "scene.weather", "people[].posture"],
        "drop": {"people[].shirt": "not relevant to the goal", "objects[].kind": "no bearing on the decision"}}


def test_clear_values_are_plain_others_keep_certainty():
    s = build_state(DECODE, KEEP["keep"])
    assert s["scene"]["setting"] == "beach"
    assert s["scene"]["weather"] == {"value": "sunny", "certainty": "likely"}


def test_list_items_keep_ids_and_only_kept_fields():
    s = build_state(DECODE, KEEP["keep"])
    assert s["people"] == [{"id": "p1", "posture": "sitting"}]


def test_sections_with_nothing_kept_are_dropped():
    assert "objects" not in build_state(DECODE, KEEP["keep"])


def test_context_and_between_added():
    s = build_state(DECODE, KEEP["keep"], context={"event": {"value": "a company offsite", "source": "user"}},
                    between={"p1_p2_distance": "about one metre"})
    assert s["context"]["event"]["source"] == "user"
    assert s["between"] == {"p1_p2_distance": "about one metre"}


def test_unassigned_fields_reported():
    assert unassigned(TEMPLATE, KEEP) == []
    assert unassigned(TEMPLATE, {"keep": ["scene.setting"], "drop": {}}) == [
        "objects[].kind", "people[].posture", "people[].shirt", "scene.weather"]


def test_left_out_lists_every_drop_with_reason():
    md = left_out_md(KEEP)
    assert "people[].shirt" in md and "not relevant to the goal" in md and "objects[].kind" in md


def test_user_supplied_value_keeps_source():
    d = {"sections": {"scene": {"setting": {"value": "company offsite", "certainty": "clear",
                                             "source": "user: event organiser"}}}}
    assert build_state(d, ["scene.setting"])["scene"]["setting"] == {"value": "company offsite",
                                                                     "source": "user: event organiser"}


def test_field_order_follows_keep_list_not_decode():
    d = {"sections": {"scene": {"weather": {"value": "sunny", "certainty": "clear"},
                                "setting": {"value": "beach", "certainty": "clear"}}}}
    s = build_state(d, ["scene.setting", "scene.weather"])
    assert list(s["scene"]) == ["setting", "weather"]
