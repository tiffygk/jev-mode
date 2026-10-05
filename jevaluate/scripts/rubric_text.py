"""Read rubric.md: its version, allowed-value lines and numbered sections. One source for code and instructions."""
import functools, hashlib, os, pathlib, re, shutil, subprocess

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

# The golden set: every file a rater is served or instructed by, and the eval's keys. A freeze tag snapshots them all;
# ratings and eval results of record need every one to match the newest rubric-*-frozen tag (2026-10-05).
GOLDEN = ("jevaluate/rubric.md", "jevaluate/SKILL.md", "jevaluate/read.md", "jevaluate/fix-catalog.md",
          "shared/jev-rules.md", "jevaluate-harness/rater-brief.md", "jevaluate-eval/gold.json", "jevaluate-eval/task.md",
          "jevaluate-eval/sources.json", "jevaluate-eval/quiz/expected.json", "jevaluate-eval/quiz/scenarios.json")
ROOT = RUBRIC_MD.parent.parent
GIT = "/usr/bin/git" if pathlib.Path("/usr/bin/git").exists() else (shutil.which("git") or "git")

def _git(root, *a):
    """git with every GIT_* variable dropped, so the environment can't point it at another repository or none."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    return subprocess.run([GIT, "-C", str(root), *a], capture_output=True, env=env)

def newest_tag(root=None):
    out = _git(root or ROOT, "tag", "-l", "rubric-*-frozen", "--sort=-v:refname").stdout.decode().split()
    return out[0] if out else None

@functools.lru_cache(maxsize=None)
def _at_ref(root, rel, ref):
    r = _git(root, "show", f"{ref}:{rel}"); return r.stdout if r.returncode == 0 else b"<missing>"

def _content(root, rel, ref=None):
    if ref: return _at_ref(str(pathlib.Path(root).resolve()), rel, ref)
    if False:
        r = _git(root, "show", f"{ref}:{rel}"); return r.stdout if r.returncode == 0 else b"<missing>"
    f = pathlib.Path(root) / rel; return f.read_bytes() if f.is_file() else b"<missing>"

def golden_hash(root=None, ref=None):
    """sha256 over the golden set, from disk or from a git ref."""
    h = hashlib.sha256()
    for rel in GOLDEN: h.update(rel.encode() + b"\0" + _content(root or ROOT, rel, ref) + b"\0")
    return h.hexdigest()

def frozen_status(root=None):
    """(status, detail): "frozen" when every golden file matches the newest rubric-*-frozen tag and rubric.md carries that
    version; "changed" when any differs (an edit, or a rollback to an older frozen rubric); "unfrozen" when there is no
    freeze tag; "no-git" outside a git checkout (a copy install)."""
    root = pathlib.Path(root or ROOT).resolve()
    if _git(root, "rev-parse", "--git-dir").returncode != 0: return "no-git", "not a git checkout, so the freeze can't be checked"
    tag = newest_tag(root)
    if not tag: return "unfrozen", "no rubric-*-frozen tag here (run git fetch --tags)"
    v = version(_content(root, "jevaluate/rubric.md").decode(errors="ignore"))
    if f"rubric-{v}-frozen" != tag: return "changed", f"rubric.md is version {v}, but the newest frozen rubric is {tag}"
    diff = [rel for rel in GOLDEN if _content(root, rel) != _content(root, rel, tag)]
    return ("frozen", tag) if not diff else ("changed", f"{', '.join(diff)} differ from the frozen {tag}")

def allowed_values(text=None):
    return {m.group(1): [v.strip() for v in re.sub(r"\s*\([^)]*\)\s*$", "", m.group(2)).split(",")]
            for m in re.finditer(r"^- `(\w+)` values: (.+)$", _text(text), re.M)}

def section(n, text=None):
    m = re.search(rf"^## {n}\. .*?(?=^## |\Z)", _text(text), re.M | re.S)
    return m.group(0) if m else ""
