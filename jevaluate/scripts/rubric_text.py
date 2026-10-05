"""Read rubric.md: its version, allowed-value lines and numbered sections. One source for code and instructions."""
import pathlib, re, subprocess

RUBRIC_MD = pathlib.Path(__file__).resolve().parent.parent / "rubric.md"
KIND_OF = {"workflow": "uses", "library": "uses", "client": "uses", "agent-tool": "uses", "display": "uses",
           "guide": "teaches", "jev-replacement": "replaces", "jev-mention-only": "mentions"}

# Renamed types: older answers and runs still score under the new name (demo became display on 2026-10-05).
RENAMED = {"demo": "display"}

def canon_type(t): t = str(t).strip().lower(); return RENAMED.get(t, t)

def _text(text): return text if text is not None else RUBRIC_MD.read_text()

def version(text=None):
    m = re.search(r"^# Jevaluate rubric \((\d{4}-\d\d-\d\d(?:\.\d+|[a-z])?)\)", _text(text), re.M)
    return m.group(1) if m else "unknown"

def frozen_status(md=None):
    """(status, detail): "frozen" when rubric.md matches its version's rubric-<version>-frozen tag byte for byte, "changed"
    when it doesn't, "unfrozen" when that version has no tag, "no-git" outside a git checkout (a copy install)."""
    md = pathlib.Path(md or RUBRIC_MD).resolve(); root = md.parent.parent
    git = lambda *a: subprocess.run(["git", "-C", str(root), *a], capture_output=True)
    if git("rev-parse", "--git-dir").returncode != 0: return "no-git", "not a git checkout, so the freeze can't be checked"
    tag = f"rubric-{version(md.read_text())}-frozen"
    r = git("show", f"{tag}:jevaluate/rubric.md")
    if r.returncode != 0: return "unfrozen", f"no tag {tag}: this rubric version isn't frozen (run git fetch --tags if it should be)"
    return ("frozen", tag) if r.stdout == md.read_bytes() else ("changed", f"rubric.md differs from the frozen {tag}")

def allowed_values(text=None):
    return {m.group(1): [v.strip() for v in re.sub(r"\s*\([^)]*\)\s*$", "", m.group(2)).split(",")]
            for m in re.finditer(r"^- `(\w+)` values: (.+)$", _text(text), re.M)}

def section(n, text=None):
    m = re.search(rf"^## {n}\. .*?(?=^## |\Z)", _text(text), re.M | re.S)
    return m.group(0) if m else ""
