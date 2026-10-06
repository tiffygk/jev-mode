"""Read rubric.md: its version, allowed-value lines and numbered sections. One source for code and instructions."""
import functools, hashlib, json, os, pathlib, re, shutil, subprocess

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
          "jevaluate-eval/sources.json", "jevaluate-eval/quiz/expected.json", "jevaluate-eval/quiz/scenarios.json",
          "jevaluate-eval/codex-notes.md")
ROOT = RUBRIC_MD.parent.parent
GIT = "/usr/bin/git" if pathlib.Path("/usr/bin/git").exists() else (shutil.which("git") or "git")

GITHUB_REPO = "tiffygk/jev-mode"  # where freezes are approved; checked directly, never through a git remote

def _git(root, *a):
    """git with GIT_* variables dropped, the user's and system git config ignored and replace objects off, so neither the
    environment nor config can point it at another repository or swap a file's content."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_NOSYSTEM="1")
    return subprocess.run([GIT, "--no-replace-objects", "-C", str(root), *a], capture_output=True, env=env)

def _github_get(path):
    """GitHub's REST API; a GH_TOKEN or GITHUB_TOKEN raises the hourly limit from 60 calls to 5,000."""
    import urllib.request
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token: headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(f"https://api.github.com/repos/{GITHUB_REPO}/{path}", headers=headers)
    with urllib.request.urlopen(req, timeout=15) as r: return json.loads(r.read())

def _vkey(tag):
    """Sort key for a freeze tag's version: numbers compare as numbers, any letters after them, never int against str."""
    v = tag[len("rubric-"):-len("-frozen")]
    return [(0, int(x), "") if x.isdigit() else (1, 0, x) for x in re.split(r"[-.]", v)]

GITHUB_CACHE = pathlib.Path.home() / ".cache" / "jevaluate" / "github-freeze.json"
GITHUB_CACHE_SECONDS = 600  # GitHub allows 60 unauthenticated calls an hour; raters run check many times (2026-10-06 ran out twice)

def _cached_ok(tag, here):
    try: e = json.loads(GITHUB_CACHE.read_text()).get(tag) or {}
    except (OSError, ValueError, AttributeError): return False
    return e.get("sha") == here and 0 <= __import__("time").time() - float(e.get("at", 0)) < GITHUB_CACHE_SECONDS

def _cache_ok(tag, here):
    try:
        try: d = json.loads(GITHUB_CACHE.read_text())
        except (OSError, ValueError): d = {}
        d = d if isinstance(d, dict) else {}
        d[tag] = {"sha": here, "at": __import__("time").time()}
        GITHUB_CACHE.parent.mkdir(parents=True, exist_ok=True); GITHUB_CACHE.write_text(json.dumps(d))
    except OSError: pass

@functools.lru_cache(maxsize=None)
def github_check(tag, root=None):
    """(True, "") when GitHub's newest rubric-*-frozen tag is this one, on the same commit as here, and that commit is in
    GitHub main's history; else (False, why). GitHub's rulesets stop anyone moving or deleting a freeze tag there and allow
    main to change only by a pull request, so this is the check a local edit, a fake remote or a forged tag can't pass."""
    root = root or ROOT
    here = _git(root, "rev-parse", f"{tag}^{{commit}}").stdout.decode().strip()
    # A confirmation is reused for GITHUB_CACHE_SECONDS, keyed by tag and commit; a failure is never stored.
    if here and _cached_ok(tag, here): return True, ""
    try:
        refs = _github_get("git/matching-refs/tags/rubric-")
        tags = {r["ref"].rsplit("/", 1)[-1]: r["object"] for r in refs if r["ref"].endswith("-frozen")}
        if not tags: return False, "GitHub has no freeze tag"
        newest = max(tags, key=_vkey)
        if newest != tag: return False, f"GitHub's newest freeze is {newest}, not {tag} (bash ~/.claude/hooks/jev-mode-sync.sh brings it here)"
        obj = tags[tag]
        sha = obj["sha"] if obj.get("type") == "commit" else _github_get(f"git/tags/{obj['sha']}")["object"]["sha"]
        if sha != here: return False, f"{tag} points at a different commit here than on GitHub"
        cmp = _github_get(f"compare/{tag}...main")
        if cmp.get("status") not in ("ahead", "identical") or cmp.get("behind_by", 1) != 0: return False, f"{tag} isn't in GitHub main's history"
        _cache_ok(tag, here)
        return True, ""
    except (OSError, ValueError, KeyError, TypeError) as e:
        if getattr(e, "code", None) in (403, 429):
            return False, "GitHub's API limit is used up (60 calls an hour without a token); retry after the hour, or set GH_TOKEN"
        return False, f"GitHub can't be reached to confirm the freeze ({type(e).__name__})"

def newest_tag(root=None):
    """The newest rubric-*-frozen tag whose commit is in this checkout's history; a tag on a commit main never merged
    is ignored, so a forged tag can't freeze an edited rubric."""
    root = root or ROOT
    for tag in _git(root, "tag", "-l", "rubric-*-frozen", "--sort=-v:refname").stdout.decode().split():
        if _git(root, "merge-base", "--is-ancestor", tag, "HEAD").returncode == 0: return tag
    return None

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
    if not tag:
        shallow = _git(root, "rev-parse", "--is-shallow-repository").stdout.decode().strip() == "true"
        return "unfrozen", "no rubric-*-frozen tag in this history (" + ("a shallow clone: run git fetch --unshallow --tags" if shallow else "run git fetch --tags") + ")"
    flagged = [l[2:] for l in _git(root, "ls-files", "-v", "--", *GOLDEN).stdout.decode().splitlines() if l[:1].islower() or l[:1] == "S"]
    if flagged: return "changed", f"{', '.join(flagged)} marked assume-unchanged or skip-worktree, so git can't see edits to them"
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
