"""Read rubric.md: its version, allowed-value lines and numbered sections. One source for code and instructions."""
import pathlib, re

RUBRIC_MD = pathlib.Path(__file__).resolve().parent.parent / "rubric.md"
KIND_OF = {"workflow": "uses", "library": "uses", "client": "uses", "agent-tool": "uses", "demo": "uses",
           "guide": "teaches", "jev-replacement": "replaces", "jev-mention-only": "mentions"}

def _text(text): return text if text is not None else RUBRIC_MD.read_text()

def version(text=None):
    m = re.search(r"^# Jevaluate rubric \((\d{4}-\d\d-\d\d(?:\.\d+|[a-z])?)\)", _text(text), re.M)
    return m.group(1) if m else "unknown"

def allowed_values(text=None):
    return {m.group(1): [v.strip() for v in re.sub(r"\s*\([^)]*\)\s*$", "", m.group(2)).split(",")]
            for m in re.finditer(r"^- `(\w+)` values: (.+)$", _text(text), re.M)}

def section(n, text=None):
    m = re.search(rf"^## {n}\. .*?(?=^## |\Z)", _text(text), re.M | re.S)
    return m.group(0) if m else ""
