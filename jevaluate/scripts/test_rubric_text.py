import re
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import rubric_text as rt

T = "# Jevaluate rubric (2026-09-29)\n\n## 1. Routing\n- `kind` values: uses, teaches\nroute text\n## 2. Facts\nfact text\n"

def test_rubric_version_from_title():
    assert rt.version(T) == "2026-09-29"

def test_allowed_values():
    assert rt.allowed_values(T) == {"kind": ["uses", "teaches"]}

def test_section_stops_at_next_heading():
    s = rt.section(1, T)
    assert "route text" in s and "fact text" not in s

def test_real_rubric_parses():
    v = rt.allowed_values()
    assert v["verdict_1_code"] == ["1a", "1b", "1c", "1r", "1t", "none"] and re.fullmatch(r"\d{4}-\d\d-\d\d(\.\d+|[a-z])?", rt.version())

def test_trailing_note_is_not_a_value():
    assert rt.allowed_values("- `kind` values: uses, mentions (filled in by code from the type)\n") == {"kind": ["uses", "mentions"]}
    assert rt.allowed_values()["kind"] == ["uses", "teaches", "replaces", "mentions"]

def test_point_version_in_title():
    assert rt.version("# Jevaluate rubric (2026-09-29.1)\n") == "2026-09-29.1"

def test_demo_renamed_display():
    assert "display" in rt.allowed_values()["project_type"] and "demo" not in rt.allowed_values()["project_type"]
    assert rt.KIND_OF["display"] == "uses" and rt.canon_type("demo") == "display" and rt.canon_type("Workflow") == "workflow"
