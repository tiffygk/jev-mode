"""The Jevaluate ratings library: add a rating, rebuild the index, find similar ratings.

Location: $JEVALUATE_LIBRARY or ~/.claude/jevaluate-library/ (created on first use).
Usage:
  python3 library.py add [--link-docs] [--evidence DIR] [--supersedes OLD.md] <rating.md>
                                              copy into projects/<slug>/ (never overwrites) and rebuild the index;
                                              --link-docs fills a missing docs link per failed fact from fix-catalog.md,
                                              --evidence copies DIR to <rated>-evidence/ beside the rating,
                                              --supersedes removes OLD.md once the new rating is saved
  python3 library.py index                    rebuild index.md from projects/*/*.md
  python3 library.py similar [--lineage X] [--stage Y] [--limit 3] [--exclude owner/repo]
  python3 library.py check [--evidence DIR] <rating.md>
                                              check facts, fields, coverage vs the evidence manifest, docs links and the
                                              verdict cap (add runs this first)
  python3 library.py stale                    list ratings made under an older rubric than rubric.md
  python3 library.py export <outdir>          latest rating per project as a short public page, plus README, LICENSE
                                              (refuses if a line matches <library>/private-terms.txt)
  python3 library.py migrate-fields           fill missing rater/effort/project_type/via on existing ratings (idempotent)
  python3 library.py fill-docs                add a docs link to existing failed facts where fix-catalog names one page
  python3 library.py blind --exclude owner/repo --out DIR
                                              copy the library without that project, for a blind re-rate
  python3 library.py migrate                  move ratings/*.md into projects/<slug>/ (idempotent)
  python3 library.py list-add <list> <entries.tsv>
                                              save a dated copy of a screened list under lists/<list>/

Layout:
  projects/<slug>/<rated>.md         one rating; a second same-day rating is <rated>-2.md, etc.
  projects/<slug>/<date>-evidence/   supporting files for a rating; never read as a rating
  lists/<name>/entries-<date>.tsv, entries.tsv (latest)
Slugs: github.com/<owner>/<repo> -> <owner>__<repo> (case kept); huggingface.co/<user>/<model> ->
hf__<user>__<model>; any other URL -> site__<domain> (no www.), plus __<path segments> if the URL has one.
"""
import os, sys, re, shutil, pathlib, argparse, datetime, json, hashlib
from urllib.parse import urlparse
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import rubric_text
import jev_callsites

LIB = pathlib.Path(os.environ.get("JEVALUATE_LIBRARY", pathlib.Path.home() / ".claude/jevaluate-library"))
RAT = LIB / "ratings"
PROJ = LIB / "projects"

def front(p):
    return front_text(p.read_text(errors="ignore"))

def front_text(t):
    m = re.match(r"---\n(.*?)\n---", t, re.S); d = {}
    for line in (m.group(1).splitlines() if m else []):
        if ":" in line:
            k, v = line.split(":", 1); d[k.strip()] = v.strip()
    return d

def slug_for(url):
    if not url:
        return "unknown"
    u = urlparse(url if "://" in url else "https://" + url)
    host = u.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    segs = [s for s in u.path.split("/") if s]
    if host == "github.com" and len(segs) >= 2:
        return f"{segs[0]}__{segs[1]}"
    if host == "huggingface.co" and len(segs) >= 2:
        return f"hf__{segs[0]}__{segs[1]}"
    slug = f"site__{host}"
    if segs:
        slug += "__" + "__".join(segs)
    return slug

def ratings_glob():
    return PROJ.glob("*/*.md")

def rating_key(p):
    """Sort key for a rating file: its date, then its same-day number (2026-09-28-3 is the third that day)."""
    m = re.match(r"(\d{4}-\d\d-\d\d)(?:-(\d+))?$", p.stem)
    return (m.group(1), int(m.group(2) or 1)) if m else (p.stem, 1)

def latest_rating_for(url):
    """The newest stored rating of this project's URL, or None."""
    files = sorted((PROJ / slug_for(url)).glob("*.md"), key=rating_key)
    return files[-1] if files else None

def index():
    PROJ.mkdir(parents=True, exist_ok=True)
    rows = ["| Rated | Project | Owner | Commit | Lineage | Stages | Loop | Depth | Verdict | Via | File |",
            "|---|---|---|---|---|---|---|---|---|---|---|"]
    files = sorted(ratings_glob(), key=lambda p: (front(p).get("rated", ""), str(p)), reverse=True)
    for p in files:
        d = front(p)
        via = d.get("via", "").strip() or "direct"
        rel = f"projects/{p.parent.name}/{p.name}"
        rows.append(f"| {d.get('rated','')} | {d.get('project','')} | {d.get('owner','')} | {d.get('commit','')[:10]} | {d.get('lineage','')} | {d.get('stages','')} | {d.get('closes_loop','')} | {d.get('depth','')} | {d.get('verdict','')} | {via} | {rel} |")
    (LIB / "index.md").write_text("# Jevaluate ratings\n\nNewest first. One file per rating; re-ratings are new files.\n\n" + "\n".join(rows) + "\n")
    return len(rows) - 2

def add(src, link_docs=False, evidence=None, supersedes=None):
    src = pathlib.Path(src); text = src.read_text(errors="ignore")
    if link_docs: text, _ = fill_docs(text, single_only=False)
    d = front_text(text)
    problems = check(src, evidence=evidence, text=text)
    if problems:
        sys.exit("not added; fix these and rerun:\n- " + "\n- ".join(problems))
    for w in WARNINGS: print("warning: " + w, file=sys.stderr)
    text = store_derived(text); d = front_text(text)
    for k in ("project", "owner", "rated", "verdict"):
        if not d.get(k): sys.exit(f"missing front-matter field: {k}")
    require_date(d)
    slug = slug_for(d.get("url", ""))
    old = None
    if supersedes:
        old = pathlib.Path(supersedes).resolve()
        if not (old.is_file() and old.parent.parent == PROJ.resolve() and old.suffix == ".md"):
            sys.exit(f"--supersedes must name an existing rating inside {PROJ}")
        if old.parent.name != slug:
            sys.exit(f"--supersedes {old.parent.name} is a different project from the new rating ({slug})")
    pdir = PROJ / slug; pdir.mkdir(parents=True, exist_ok=True)
    # Number after the highest same-day rating, so the newest always sorts last, even when an earlier file was superseded.
    same = [int(m.group(1) or 1) for f in pdir.glob(f"{d['rated']}*.md")
            if (m := re.fullmatch(re.escape(d['rated']) + r"(?:-(\d+))?", f.stem))]
    dest = pdir / (f"{d['rated']}-{max(same) + 1}.md" if same else f"{d['rated']}.md")
    ev_dest = pdir / f"{dest.stem}-evidence"
    if evidence and ev_dest.exists(): sys.exit(f"{ev_dest} already exists; not overwriting another rating's evidence")
    dest.write_text(text)
    if evidence: shutil.copytree(evidence, ev_dest)
    log = pathlib.Path(str(src) + ".steps.json")
    if log.exists():
        ev_dest.mkdir(exist_ok=True); shutil.copy(log, ev_dest / (dest.name + ".steps.json"))
        if (src.parent / "routing_revised.json").exists(): shutil.copy(src.parent / "routing_revised.json", ev_dest / "routing_revised.json")
    if old and old.exists() and old != dest.resolve():
        old.unlink(); print(f"removed superseded {old}")
    print(dest); print(f"index: {index()} ratings")

SKILL = pathlib.Path(__file__).resolve().parent.parent

RUBRIC = rubric_text.version()
REQUIRED_FIELDS = ("project_type", "rater", "effort", "via")
FIELD_DEFAULTS = {"rater": "unknown", "effort": "medium", "project_type": "unrecorded", "via": "unrecorded"}
DOC_LINK = re.compile(r"docs\.typesafe\.ai/\S+|\b(?:cookbooks|concepts|patterns|primitives|model-jaggedness)/[\w\-]+(?:/[\w\-]+)*|`(?:primitives|confidence|models)`")
PARTIAL = re.compile(r"\b(skipped|selective(?:ly)?|skimmed|partial(?:ly)?|partly)\b", re.I)
NEGATED_SKIP = re.compile(r"\b(none|zero|0|no files?|not|nothing|never)\s+(?:were\s+|was\s+)?skipped", re.I)
VALS = ("yes", "no", "n.a.", "unknown")
G_BASE = 100  # guide facts G1, G2 are keyed 101, 102 so they sort after F23

def fid(n): return f"G{n - G_BASE}" if n > G_BASE else f"F{n}"

def is_guide(d): return (d.get("project_type", "").split() or [""])[0] == "guide"

FACT = re.compile(r"^\s*[-*]\s*\**([FG])(\d+)\b[^\n]*?(?:—|--|:|\*\*)\s*\**\s*(yes|no|n\.a\.|n/a|not applicable|unknown|unverified|partial|unclear)(?!\w)", re.I)

def facts(text):
    body = text.split("## Facts", 1)[-1].split("\n## ", 1)[0] if "## Facts" in text else ""
    out = {}
    for line in body.splitlines():
        m = FACT.match(line)
        if not m: continue
        n = int(m.group(2)) + (G_BASE if m.group(1).upper() == "G" else 0)
        if n not in out:
            v = m.group(3).lower()
            v = {"unclear": "invalid", "n/a": "n.a.", "not applicable": "n.a.", "unverified": "n.a."}.get(v, v)
            out[n] = (v, line)
    return out

def section(text, name):
    m = re.search(r"^## " + re.escape(name) + r"\b[^\n]*\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    return m.group(1) if m else ""

def evidence_dir_for(p):
    p = pathlib.Path(p)
    for stem in (p.stem, re.sub(r"-\d+$", "", p.stem)):
        e = p.parent / f"{stem}-evidence"
        if e.is_dir(): return e
    if (p.parent / "manifest.md").exists(): return p.parent  # a rater's folder: rating.md beside manifest.md and files/
    return None

def manifest_files(ev):
    m = ev / "manifest.md" if ev else None
    if not m or not m.exists(): return None
    out = []
    for line in m.read_text(errors="ignore").splitlines():
        if not line.startswith("|"): continue
        cell = line.strip().strip("|").split("|")[0].strip()
        if not cell or cell.lower() == "file" or set(cell) <= set("-: "): continue
        out.append(cell)
    return out

def check_coverage(t, d, ev, err, warn):
    cov = section(t, "Coverage"); full = d.get("depth", "") == "full"
    skip_line = re.search(r"^\s*[-*]?\s*skipped\s*:\s*\S", cov, re.I | re.M)
    if full:
        if skip_line: err.append("depth is full but Coverage has a 'skipped:' line; lower the depth or read the files")
        hit = PARTIAL.search(NEGATED_SKIP.sub("", cov))
        if hit: err.append(f"depth is full but Coverage says '{hit.group(1)}'; use depth extract, or read everything")
    files = manifest_files(ev)
    if files is None:
        warn.append("no evidence manifest.md found; Coverage was not checked against a file list")
        return
    if skip_line: return
    missing = [f for f in files if f not in cov]
    if missing:
        err.append(f"Coverage omits {len(missing)} manifest file(s): " + ", ".join(missing[:8]) + (" ..." if len(missing) > 8 else "")
                   + " (list each, or add a 'skipped: <reason>' line when depth is not full)")

def check_doc_links(f, t, err):
    fixes = section(t, "Core fixes")
    for n, (val, line) in sorted(f.items()):
        if val != "no" or DOC_LINK.search(line): continue
        entry = [l for l in fixes.splitlines() if re.search(rf"\b{fid(n)}\b", l)]
        if not any(DOC_LINK.search(l) for l in entry):
            err.append(f"{fid(n)} is no but has no TypeSafe docs link on its line or in its Core fixes entry (e.g. docs.typesafe.ai/primitives.md; --link-docs fills it from fix-catalog.md)")

PROCESS_NOTE = re.compile(r"\bsecond pass\b|\bfirst version of this rating\b|\b(?:added|raised|lowered|changed) in (?:a|the) revision\b|\brevision of \d{4}-\d\d-\d\d\b|\blabel updated\b|\brating library\b|\b(?:in|from) (?:this|the|my) library so far\b|\bI (?:kept|used|chose|went with)\b", re.I)

WARNINGS = []

ROUTED_CODES = ("1a", "1b", "1c", "1r", "1t")
LEVELS = ("very high", "high", "low")
PRIMITIVES = ("Noul", "Choice", "Score")
NEW_RUBRIC = "2026-09-29"
DERIVED = {}

def highest_stakes(levels):
    """The highest of a list of stakes levels (very high, high, low), or None for an empty list; the one ordering ratings and the eval use."""
    return min(levels, key=LEVELS.index) if levels else None

def derive_top_stakes(d, t):
    """top_stakes, worked out by code: n.a. for a guide, a client or any verdict-1 code; else the highest stakes under ## Decisions (None when none are listed)."""
    first = lambda k: d.get(k, "").split("#")[0].strip()
    if first("project_type") in ("guide", "client") or first("verdict_1_code") in ROUTED_CODES: return "n.a."
    ds, _ = decisions(t)
    return highest_stakes([x["stakes"] for x in ds])

def routing_print(d, t):
    """Fingerprint of the routing calls; the stakes in it are the derived ones."""
    first = lambda k: d.get(k, "").split("#")[0].strip()
    vals = [first("project_type"), rubric_text.KIND_OF.get(first("project_type"), ""), first("verdict_1_code"), derive_top_stakes(d, t) or ""]
    return hashlib.sha1("|".join(vals).encode()).hexdigest()

def is_new_rubric(d): return bool(d.get("rubric", "").split()[:1]) and d["rubric"].split()[0] >= NEW_RUBRIC

def store_derived(text):
    """The rating as stored: kind and top_stakes filled in by code, and a guide's F0 recorded n.a. (new rubric only)."""
    d = front_text(text); m = re.match(r"---\n(.*?)\n---", text, re.S)
    if not m or not is_new_rubric(d) or d.get("verdict", "").split()[:1] == ["cant-rate"]: return text
    head, top = m.group(1), derive_top_stakes(d, text)
    if top:
        if re.search(r"^top_stakes:.*$", head, re.M): head = re.sub(r"^top_stakes:.*$", f"top_stakes: {top}", head, count=1, flags=re.M)
        elif re.search(r"^verdict_1_code:.*$", head, re.M): head = re.sub(r"^(verdict_1_code:.*)$", lambda x: x.group(1) + f"\ntop_stakes: {top}", head, count=1, flags=re.M)
        else: head += f"\ntop_stakes: {top}"
    kind = rubric_text.KIND_OF.get(d.get("project_type", "").split("#")[0].strip())
    if kind:
        if re.search(r"^kind:.*$", head, re.M): head = re.sub(r"^kind:.*$", f"kind: {kind}", head, count=1, flags=re.M)
        elif re.search(r"^project_type:.*$", head, re.M): head = re.sub(r"^(project_type:.*)$", lambda x: x.group(1) + f"\nkind: {kind}", head, count=1, flags=re.M)
        else: head += f"\nkind: {kind}"
    text = "---\n" + head + "\n---" + text[m.end():]
    if is_guide(d):
        text = re.sub(r"^(\s*[-*]\s*\**F0\b[^\n]*?(?:\u2014|--|:|\*\*)\s*\**\s*)no\.?(?=\s|$)", r"\1n.a.", text, count=1, flags=re.M | re.I)
    return text
DECISION_FORMAT = "- <decision> | <Noul, Choice or Score> | <very high, high or low> | acts at <file:line> | <what code does with the answer>"
CITE = re.compile(r"`?([\w./@-]*[\w-]\.\w+):(\d+)")
NOT_CODE_EXT = (".md", ".txt")

def decisions(t):
    """([{text, prim, stakes, file, line}], [problems]) from a rating's ## Decisions section."""
    out, bad = [], []
    for raw in section(t, "Decisions").splitlines():
        line = raw.strip()
        if not line.startswith(("-", "*")): continue
        parts = [x.strip() for x in line.lstrip("-* ").split("|")]
        prim = next((p for p in PRIMITIVES if len(parts) > 1 and parts[1].lower() == p.lower()), None)
        lvl = parts[2].lower() if len(parts) > 2 else ""
        at = re.match(r"acts at\s+`?([^\s`:]+):(\d+)", parts[3]) if len(parts) > 3 else None
        why = None
        if len(parts) < 5 or not all(parts[:2]) or not parts[4]: why = "it needs five parts separated by ' | '"
        elif not prim: why = f"'{parts[1]}' is not Noul, Choice or Score"
        elif lvl not in LEVELS: why = f"'{parts[2]}' is not very high, high or low"
        elif not at: why = f"'{parts[3]}' is not 'acts at <file:line>'"
        if why: bad.append(f"Decisions line '{line[:70]}': {why}; write it as {DECISION_FORMAT}")
        else: out.append({"text": parts[0], "prim": prim, "stakes": lvl, "file": at.group(1), "line": int(at.group(2))})
    return out, bad

def repo_paths(ev):
    """Repo paths of every file the evidence folder saved under files/, or None when there is no files/ folder."""
    fd = ev / "files" if ev else None
    return None if not fd or not fd.is_dir() else [jev_callsites.unflatten(f.name) for f in fd.iterdir() if f.is_file()]

def is_capture(ev, cited):
    """A saved live response (rubric F0: a capture holding the request and typed answers) in the evidence folder's captures/ or responses/."""
    parts = pathlib.PurePath(cited).parts
    f = ev / cited
    if not ("captures" in parts or "responses" in parts) or not cited.endswith(".json") or not f.is_file(): return False
    text = f.read_text(errors="replace")
    return bool(re.search(r'\\*"(questions|state)\\*"\s*:', text) and re.search(r'\\*"(answers|probabilities|p_true|results)\\*"\s*:', text))

def same_file(cited, path): return path == cited or path.endswith("/" + cited)

def is_code_cite(path):
    parts = pathlib.PurePath(path).parts
    return not path.lower().endswith(NOT_CODE_EXT) and not any(x in ("docs", "tests", "test") for x in parts[:-1]) and not parts[-1].startswith("test_")

def no_reasoned(finding, path):
    """True when an F0 no line names `path` (or its file name) followed by at least three words of reason."""
    for name in (path, path.rsplit("/", 1)[-1]):
        i = finding.find(name)
        if i >= 0: return len(re.findall(r"[A-Za-z]{2,}", re.sub(r"^:\d+(?:-\d+)?", "", finding[i + len(name):]))) >= 3
    return False

def cites_a_call(code, citable):
    """True when one of the cited (file, line) pairs is a line jev_callsites.citable_lines found ({repo path: [lines]})."""
    return any(n in hs for f, n in code for p, hs in citable.items() if same_file(f, p))

def not_checked_msg(value):
    return (f"F0 is {value} but F0 was not checked: no evidence files/ folder was found (looked beside the rating for manifest.md and for a <rating>-evidence folder). "
            "Point at the evidence with --evidence DIR (the folder holding manifest.md and files/), or keep the rating beside them")

def check_guide_code(f0, ev, err):
    """A guide records n.a.; if its non-test code holds a hosted call, it is a uses type (and F0 yes is refused by type_code_problems)."""
    paths = repo_paths(ev)
    if paths is None:
        if f0 in ("yes", "no"): err.append(not_checked_msg(f0))
        return
    calls = jev_callsites.citable_lines(ev / "files")  # a call, not an import or dependency a guide's snippets may carry
    if calls and f0 != "yes":
        err.append(f"a guide, but the non-test code holds a hosted Jev call in {', '.join(f'{p}:{h[0]}' for p, h in calls.items())}: a project that calls Jev is typed by what its code does, "
                   "not by what it teaches; redo project_type as a uses type (workflow, library, client or agent-tool) with F0 yes citing the call")

def check_f0(finding, value, ev, err):
    """F0 must point at the call (yes) and must not hide a hosted call the callsites script finds (no)."""
    paths = repo_paths(ev)
    calls = jev_callsites.call_lines(ev / "files") if paths is not None else {}
    not_checked = lambda: err.append(not_checked_msg(value))
    cites = [(m.group(1), int(m.group(2))) for m in CITE.finditer(finding)]
    if value == "yes":
        if ev and any(is_capture(ev, f) for f, _ in cites): return
        code = [(f, n) for f, n in cites if is_code_cite(f)]
        if not code:
            seen = ", ".join(f"{f}:{n}" for f, n in cites)
            err.append("F0 is yes but " + (f"cites {seen}, which is not a code file (not .md, .txt, docs/ or tests/)" if cites else "cites no path:line")
                       + ": redo the F0 line and cite the code line that creates the TypeSafe client, posts to api.typesafe.ai, names the typesafe/jev or typesafe-ai/jev model, or calls it, as path:line in a code file")
            return
        if paths is None: return not_checked()
        found = [(f, n, next(p for p in paths if same_file(f, p))) for f, n in code if any(same_file(f, p) for p in paths)]
        if not found:
            err.append(f"F0 cites {', '.join(f'{f}:{n}' for f, n in code)}, but none is in the evidence files/ folder: redo the F0 line and cite a file you read")
            return
        if any("captures" in pathlib.PurePath(p).parts for _, _, p in found): return
        citable = jev_callsites.citable_lines(ev / "files")
        if not cites_a_call(code, citable):
            shown = ", ".join(f"{p}:{h[0]}" for p, h in list(citable.items())[:4])
            err.append(f"F0 cites {', '.join(f'{f}:{n}' for f, n, _ in found)}, but that line is not a hosted Jev call in non-test code: a comment, an import, a dependency line, a throw or error class, "
                       "a class or constructor declaration, and a regex or bare string do not count. Redo the F0 line and cite the line that creates the client (client = TypeSafe(...)), "
                       "posts to api.typesafe.ai, names the typesafe/jev or typesafe-ai/jev model ID, or calls it (client.noul(...)); the import is not the call" + (f"; citable lines found: {shown}" if citable else ""))
    elif value == "no" and paths is None: not_checked()
    elif value == "no" and calls:
        unnamed = [p for p in calls if not no_reasoned(finding, p)]
        if unnamed:
            err.append(f"F0 is no but jev_callsites.py finds hosted Jev calls (an import, a client construction, a call on the client, api.typesafe.ai or a model ID) in {', '.join(f'{p}:{calls[p][0]}' for p in unnamed)}: redo the F0 line; "
                       "if a file really isn't a call, name it there followed by at least three words of reason (a comment, dead code, a fixture), otherwise F0 is yes")

def check_decisions(d, t, typ, code, ev, f, err):
    """Decisions lines and F11/F13 against the stakes; applies to a uses type that isn't a client or routed."""
    if typ == "client": return
    if rubric_text.KIND_OF.get(typ) != "uses" or code in ROUTED_CODES: return
    ds, bad = decisions(t)
    err.extend(bad)
    if not ds and not bad:
        err.append(f"## Decisions is missing or empty: list each decision Jev makes, one line each, as {DECISION_FORMAT}")
    if not ds: return
    paths = repo_paths(ev)
    if paths is not None:
        for x in ds:
            if not any(same_file(x["file"], p) for p in paths):
                err.append(f"Decisions line '{x['text'][:40]}' acts at {x['file']}, which is not in the evidence files/ folder: redo that line with a file you read")
    val = lambda n: f.get(n, ("",))[0]
    vh = [x for x in ds if x["prim"] == "Choice" and x["stakes"] == "very high"]; hi = [x for x in ds if x["prim"] == "Choice" and x["stakes"] == "high"]
    if not vh and not hi and val(13) in ("yes", "no"):
        err.append("F13 is " + val(13) + " but no decision under Decisions is a Choice at high or very high stakes: redo F13 as n.a. (rubric F13 rows: the low row is always n.a.; the high and very high rows need a Choice at that level)")
    elif vh and val(13) == "n.a.":
        err.append(f"F13 is n.a. but the very high Choice '{vh[0]['text'][:40]}' is listed under Decisions: redo F13 as yes or no (rubric F13 very high row: several option orders are needed at very high stakes)")
    elif hi and not vh and val(13) == "n.a." and val(11) != "yes":
        err.append(f"F13 is n.a. for the high Choice '{hi[0]['text'][:40]}' but F11 is {val(11) or 'missing'}: at high stakes F13 may be n.a. only when F11 is yes (rubric F13 high row: a confidence gate is enough); redo F13, or F11 if the gate exists")
    if val(11) == "n.a." and any(x["stakes"] != "low" for x in ds):
        err.append("F11 is n.a. but a decision under Decisions is above low: redo F11 as yes or no (rubric F11 rows: n.a. only when the answer is just shown or returned, i.e. every decision is low)")

def type_code_problems(typ, code, f0=None):
    """Plain-word problems when the type, the verdict-1 code and (when given) calls Jev contradict each other. Shared by check_schema and the quiz key."""
    err, uses = [], rubric_text.KIND_OF.get(typ) == "uses"
    lab = lambda c: f"{c} ({CODE_LABEL[c]})" if c in CODE_LABEL else f"'{c}'"
    if typ == "jev-mention-only" and code not in ("1a", "1b"): err.append(f"a jev-mention-only gets {lab('1a')} or {lab('1b')}")
    if typ == "guide" and code != "1t": err.append(f"a guide gets {lab('1t')} until the guide rubric exists, not {lab(code)}: redo the verdict-1 code")
    if code == "1t" and typ != "guide": err.append(f"{lab('1t')} is only for a guide")
    if code == "1c" and not uses: err.append(f"{lab('1c')} is only for a uses type")
    if uses and code in ("1a", "1b", "1r"): err.append(f"a {typ} calls Jev, so it cannot get {lab(code)}; that code is for a project that doesn't call Jev")
    if f0 is None: return err
    if typ == "guide":
        if f0 == "yes": err.append("a guide records calls Jev n.a., but calls Jev is yes. A project that calls Jev is a uses type (workflow, library, client or agent-tool), typed by what its code does: redo project_type, or F0 as n.a.")
        return err
    if uses and f0 != "yes": err.append(f"a {typ} calls Jev, but calls Jev is {f0}. A project that doesn't call Jev and isn't a guide or a replacement is a jev-mention-only, with {lab('1a')} or {lab('1b')}")
    elif typ in ("jev-replacement", "jev-mention-only") and f0 != "no": err.append(f"a {typ} doesn't call Jev, but calls Jev is {f0}")
    return err

def require_date(d):
    """`rated` names the rating file, so it must be a plain date, never a path."""
    if not re.fullmatch(r"\d{4}-\d\d-\d\d", str(d.get("rated", ""))):
        sys.exit(f"front-matter rated must be a date (YYYY-MM-DD), got {d.get('rated')!r}")

def check_schema(d, t, err, ev=None):
    vals = rubric_text.allowed_values()
    first = lambda k: d.get(k, "").split("#")[0].strip()
    typ, code, v = first("project_type"), first("verdict_1_code"), first("verdict")
    for k, x in (("project_type", typ), ("verdict_1_code", code)):  # kind is derived from the type by code; a rater-entered kind is ignored
        if x not in vals.get(k, []): err.append(f"{k} '{x}' is not one of {vals.get(k)}")
    claim = first("citation") not in ("", "none")
    if typ == "jev-replacement" and claim and code != "1a":
        err.append(f"a jev-replacement whose citation quotes a claim to be or to call Jev gets 1a, not '{code}': redo verdict_1_code as 1a (or citation as none if the project makes no such claim)")
    elif typ == "jev-replacement" and not claim and code != "1r":
        err.append(f"a jev-replacement that makes no claim to be or to call Jev gets 1r, not '{code}': redo verdict_1_code as 1r, or quote the claim as citation with its file:line to get 1a")
    err.extend(type_code_problems(typ, code))
    if (v == "1") != (code != "none"): err.append(f"verdict {v} with verdict_1_code {code}: a code goes with verdict 1, and only there")
    if code == "1a" and typ != "jev-replacement" and first("citation") in ("", "none"): err.append("1a needs the claim quoted as citation")
    elif code == "1a" and not CITE.search(first("citation")): err.append("1a citation must give the claim's file:line (for example README.md:3): redo citation")
    if typ == "jev-mention-only":
        for k in ("type_best_match", "code_functionality", "replaces_jev", "intended_call"):
            if not first(k): err.append(f"a jev-mention-only records {k}")
    rows = {n: (val, finding) for n, _, val, finding in fact_rows(t)}
    f0 = rows.get(0, (None, ""))[0]
    if f0 is None: err.append("the F0 calls-Jev line is missing")
    else: err.extend(p for p in type_code_problems(typ, code, f0) if f"but calls Jev is {f0}" in p)
    if typ == "guide": check_guide_code(f0, ev, err)
    elif f0 in ("yes", "no"): check_f0(rows[0][1], f0, ev, err)
    check_decisions(d, t, typ, code, ev, {n: (val, "") for n, (val, _) in rows.items()}, err)
    return code in ROUTED_CODES

STEP_ORDER = ["routing", "facts", "scores", "compare", "verdict"]
STAGE_LABELS = ("data-prep", "question-state", "execution", "decision")

def check_steps(src, d, t, err, prefix=False):
    src = pathlib.Path(src); p = pathlib.Path(str(src) + ".steps.json"); ev = evidence_dir_for(src)
    if not p.exists() and ev and (ev / (src.name + ".steps.json")).exists(): p = ev / (src.name + ".steps.json")
    if not p.exists(): err.append("no step log: rate with step.py next, one section at a time"); return
    log = [e for e in json.loads(p.read_text()) if not e["step"].startswith("full:")]
    seen = [e["step"] for e in log]
    code = d.get("verdict_1_code", "").split("#")[0].strip()
    want = ["routing", "compare", "verdict"] if code in ROUTED_CODES else STEP_ORDER
    if prefix:  # a cant-rate stops early: any in-order start of the step order will do
        if not seen or seen != STEP_ORDER[:len(seen)]: err.append(f"step log {seen}, expected an in-order start of {STEP_ORDER} beginning with routing")
        return
    if seen != want: err.append(f"step log {seen}, expected {want}")
    cur = routing_print(d, t)
    later = [e for e in log if e["step"] != "routing"]
    cleared = (src.parent / "routing_revised.json").exists() or bool(ev and (ev / "routing_revised.json").exists())
    if later and later[0]["routing"] != cur and not cleared:
        err.append("routing changed after the facts were served; the controller clears a revision with routing_revised.json (reason and time) after checking it")

def check_mechanical(t, d, ev, err):
    """Word, sentence and label limits the rater brief states; enforced for rubric 2026-09-29 and later."""
    words = lambda s: len(re.sub(r"https?://\S+|`[^`]*`|\([^()]*\w[^()]*:\d+[^()]*\)", " ", s).split())
    if d.get("why") and words(d["why"]) > 20: err.append(f"why is {words(d['why'])} words; at most 20 words")
    for n, _, _, finding in fact_rows(t):
        if words(finding) > 20: err.append(f"{fid(n)} finding is {words(finding)} words; at most 20 words (the rest goes in Verdict and reasoning)")
    for name, cap in (("Summary", 3), ("Verdict and reasoning", 5)):
        body = section(t, name).strip()
        if body and len(sentences(body)) > cap: err.append(f"## {name} is {len(sentences(body))} sentences; at most {cap}")
    bad = [x for x in re.split(r"\s*,\s*", d.get("stages", "").split("#")[0].strip().strip("[]")) if x and x not in STAGE_LABELS]
    if bad: err.append(f"stages {bad} are not among {list(STAGE_LABELS)}")
    meta = ev / "meta.json" if ev else None
    if meta and meta.exists():
        want = str(json.loads(meta.read_text()).get("commit", "")); have = d.get("commit", "").split("#")[0].strip()
        if want and not (have == want or (len(have) >= 7 and want.startswith(have))): err.append(f"commit {have} does not match the evidence meta.json ({want})")

def check(src, evidence=None, text=None):
    p = pathlib.Path(src); t = text if text is not None else p.read_text(errors="ignore")
    d = front_text(t); err = []; WARNINGS.clear(); DERIVED.clear()
    for k in ("project", "owner", "rated", "commit", "depth", "verdict", "scores", "rubric") + REQUIRED_FIELDS:
        if not d.get(k): err.append(f"missing front-matter field: {k}")
    ev = pathlib.Path(evidence) if evidence else evidence_dir_for(p)
    check_coverage(t, d, ev, err, WARNINGS)
    if d.get("rubric") and d["rubric"].split()[0] < RUBRIC: err.append(f"rubric {d['rubric']} is older than {RUBRIC}; rate with the current rubric")
    if "not recorded" in d.get("commit", ""): err.append("commit not recorded")
    body = t.split("## Coverage")[0]
    for m in PROCESS_NOTE.finditer(body):
        err.append(f"process note '{m.group(0)}': a rating states findings only; cut revision history, first-person rater choices and references to other ratings or the library")
    v = d.get("verdict", "").split()[0] if d.get("verdict") else ""
    new = is_new_rubric(d)
    if v == "cant-rate":
        if new: check_steps(p, d, t, err, prefix=True)
        return err
    if new:
        DERIVED["top_stakes"] = derive_top_stakes(d, t) or ""
        check_steps(p, d, t, err); check_mechanical(t, d, ev, err)
    if new and check_schema(d, t, err, ev): return err
    f = facts(t)
    check_doc_links(f, t, err)
    # F0 (calls hosted Jev) gates everything: only a traced call allows a verdict above 1.
    f0 = f.get(0, ("",))[0]
    if 0 not in f and d.get("rubric", "").split()[:1] and d["rubric"].split()[0] >= "2026-09-28b":
        err.append("F0 missing from ## Facts: record the traced call ('- F0 Calls hosted Jev — yes. <file:line>')")
    if 0 in f and f0 != "yes" and v not in ("1",) and not is_guide(d):
        err.append(f"F0 is {f0}: verdict {v} needs a traced call; use verdict 1 when F0 is no, cant-rate when it is unknown")
    for n in list(range(1, 24)):
        if n not in f: err.append(f"F{n} missing from ## Facts (line format: '- F{n} <name> — yes|no|n.a.|unknown. <evidence>')")
    for n in ((G_BASE + 1, G_BASE + 2) if is_guide(d) else ()):
        if n not in f: err.append(f"{fid(n)} missing from ## Facts: a guide records G1-G2 after F23 ('- {fid(n)} <name> — yes|no|n.a.|unknown. <evidence>')")
    for n, (val, line) in f.items():
        if val == "invalid": err.append(f"{fid(n)} is 'unclear'; use yes, no, n.a. or unknown")
        if val == "partial": err.append(f"{fid(n)} is 'partial'; use yes, no or n.a.")
        if val == "unknown" and not re.search(r"--also|fetch failed|no file", line, re.I):
            err.append(f"{fid(n)} is unknown without a '--also' fetch noted (say 'fetch failed' or 'no file would answer it')")
    sc = dict(re.findall(r"(\w+):\s*(\d)", d.get("scores", "")))
    ex, fit, evd = (int(sc[k]) if k in sc else None for k in ("execution", "fit", "evidence"))
    no = lambda ns: [n for n in ns if f.get(n, ("",))[0] == "no"]
    core = no(list(range(1, 7)))
    if len(core) >= 2 and ex is not None and ex > 1: err.append(f"execution {ex} but {len(core)} of F1-F6 are no; anchor allows at most 1")
    elif len(core) == 1 and ex is not None and ex > 2: err.append(f"execution {ex} but F{core[0]} is no; anchor allows at most 2")
    if no([13]) and fit is not None and fit > 2: err.append("fit 3 but F13 is no; anchor allows at most 2")
    if v.isdigit():
        v = int(v); cap, why = 5, ""
        top = (derive_top_stakes(d, t) or "") if new else d.get("top_stakes", "").split("#")[0].strip()
        capping = list(range(1, 7)) + list(range(8, 12)) + list(range(19, 23))
        if new:
            capping = list(range(1, 7)) + list(range(8, 12)) + ([13, 20, 22] if top == "very high" else [])
            capping += [19, 21]
        if no([6]): cap, why = 2, "F6 is no (fatal)"
        elif no([11]) and top in ("high", "very high"): cap, why = 2, "F11 no on a high-stakes action (fatal)"
        elif ex is not None and ex <= 1: cap, why = 2, f"execution {ex}"
        elif no(capping):
            cap, why = 3, "failed " + ", ".join(f"F{n}" for n in no(capping))
        elif evd == 0: cap, why = 3, "evidence 0"
        elif (ex or 0) < 2 or (fit or 0) < 2: cap, why = 3, "execution or fit below 2"
        if v > cap: err.append(f"verdict {v} is above the cap of {cap} ({why})")
        if v == 5 and not (ex == 3 and fit == 3 and evd == 3 and d.get("closes_loop", "none") != "none"):
            err.append("verdict 5 needs execution 3, fit 3, evidence 3 and closes_loop other than none")
    return err

def catalog():
    """fix-catalog.md -> {fact number: [doc slugs]} for rows whose first cell starts with F<n> or G<n> (ranges skipped)."""
    out = {}
    try: rows = (SKILL / "fix-catalog.md").read_text().splitlines()
    except OSError: return out
    for row in rows:
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        if len(cells) < 3: continue
        m = re.match(r"([FG])(\d+)\b(?!-)", cells[0])
        if not m: continue
        out[int(m.group(2)) + (G_BASE if m.group(1) == "G" else 0)] = re.findall(r"`([a-z][\w\-]*(?:/[\w\-]+)*)`", cells[2])
    return out

def fill_docs(text, single_only):
    """Append a docs link to each 'no' fact lacking one. Returns (text, {n: 'filled'|'ambiguous'|'no page'})."""
    cat = catalog(); f = facts(text); fixes = section(text, "Core fixes"); lines = text.split("\n"); report = {}
    for n, (val, line) in sorted(f.items()):
        if val != "no" or DOC_LINK.search(line): continue
        if any(DOC_LINK.search(l) for l in fixes.splitlines() if re.search(rf"\b{fid(n)}\b", l)): continue
        slugs = cat.get(n, [])
        if not slugs: report[n] = "no page"; continue
        if single_only and len(slugs) != 1: report[n] = "ambiguous"; continue
        link = " Docs: " + ", ".join(f"https://docs.typesafe.ai/{s}.md" for s in slugs)
        lines[lines.index(line)] = line.rstrip() + link; report[n] = "filled"
    return "\n".join(lines), report

def stale():
    rows = []
    for p in sorted(ratings_glob()):
        r = front(p).get("rubric", "").split()
        r = r[0] if r else ""
        if r < RUBRIC: rows.append(f"{p.parent.name}/{p.name}  rubric {r or 'missing'} (current {RUBRIC})")
    print("\n".join(rows) if rows else "no stale ratings")
    return len(rows)

def migrate_fields():
    changed = 0
    for p in sorted(ratings_glob()):
        t = p.read_text(errors="ignore"); m = re.match(r"---\n(.*?)\n---\n", t, re.S)
        if not m: continue
        d = front_text(t); add_lines = [f"{k}: {v}" for k, v in FIELD_DEFAULTS.items() if not d.get(k)]
        if not add_lines: continue
        body = [l for l in m.group(1).split("\n") if not re.match(r"(%s):\s*$" % "|".join(FIELD_DEFAULTS), l)]
        p.write_text("---\n" + "\n".join(body + add_lines) + "\n---\n" + t[m.end():]); changed += 1
    print(f"migrate-fields: {changed} ratings updated")

def fill_docs_existing():
    filled = 0; left = []
    for p in sorted(ratings_glob()):
        t = p.read_text(errors="ignore"); new, rep = fill_docs(t, single_only=True)
        if new != t: p.write_text(new)
        filled += sum(1 for v in rep.values() if v == "filled")
        left += [f"{p.parent.name}/{p.name} {fid(n)} ({v})" for n, v in rep.items() if v != "filled"]
    print(f"fill-docs: {filled} facts linked")
    for l in left: print("left alone: " + l)

VERDICT_LABEL = {"5": "Learn from it", "4": "Use it", "3": "Use with a fix", "2": "Rework it", "1": "Jev in name only", "cant-rate": "Can't rate yet"}

def publishable(p):
    """A full read, or a scope the controller approved (depth extract with `skipped: scoped` Coverage lines)."""
    depth = front(p).get("depth", "").split()[:1]
    return depth == ["full"] or (depth == ["extract"] and "skipped: scoped" in section(p.read_text(errors="ignore"), "Coverage"))

def latest_per_project(full_only=False):
    best = {}
    for p in ratings_glob():
        if full_only and not publishable(p): continue
        key = rating_key(p)
        if p.parent.name not in best or key > best[p.parent.name][0]: best[p.parent.name] = (key, p)
    return {k: v[1] for k, v in best.items()}

FACT_LINE = re.compile(r"^\s*[-*]\s*\**([FG])(\d+)\**\s*(.*?)\s*\**\s*(?:—|--)\s*\**(yes|no|n\.a\.|n/a|unknown)\**[.,:]?\s*(.*)$", re.I)
FIX_ONLY = {12, 14, 23}
CODE_EXT = r"py|pyi|ts|tsx|js|jsx|mjs|cjs|rb|go|rs|java|kt|php|swift|ex|sh|md|json|html|css|yml|yaml|toml"
DOC_SLUG = re.compile(r"`((?:concepts|primitives|cookbooks|patterns|model-jaggedness|introduction|sdk)/[\w/.-]+|primitives|models|confidence|patterns|cookbooks)`")

def fact_rows(t):
    """[(n, name, value, finding)] in fact order, from a rating's Facts section."""
    rows = []
    for line in section(t, "Facts").splitlines():
        m = FACT_LINE.match(line)
        if m: rows.append((int(m.group(2)) + (G_BASE if m.group(1).upper() == "G" else 0), m.group(3).strip(" *"), m.group(4).lower().replace("n/a", "n.a."), m.group(5).strip()))
    return rows

ABBREV = re.compile(r"(?:\b(?:e\.g|i\.e|vs|etc|cf|approx|no|fig)\.|\b[A-Z]\.)$", re.I)

def sentences(s):
    """Split prose into sentences, never inside quotes, parentheses or code, nor after e.g./i.e."""
    s = s.replace("\n", " "); out, cur, depth, quote, code = [], "", 0, False, False
    for i, ch in enumerate(s):
        cur += ch
        if ch == "`": code = not code
        elif code: continue
        elif ch in "\u201c\u201d" or ch == '"':
            quote = (not quote) if ch == '"' else (ch == "\u201c")
            if not quote and depth == 0 and len(cur) > 1 and cur[-2] in ".!?" and (i + 1 == len(s) or s[i + 1] == " "):
                out.append(cur.strip()); cur = ""
        elif ch in "([": depth += 1
        elif ch in ")]": depth = max(0, depth - 1)
        elif ch in ".!?" and not quote and depth == 0 and (i + 1 == len(s) or s[i + 1] == " ") and not ABBREV.search(cur.strip()):
            out.append(cur.strip()); cur = ""
    if cur.strip(): out.append(cur.strip())
    return [x for x in out if x]

IMPERATIVE = re.compile(r"^(?:add|ask|average|batch|call|cap|change|check|combine|compare|default|drop|fold|gate|give|include|keep|label|log|make|measure|move|pass|pin|point|put|randomize|record|remove|replace|rewrite|route|run|score|send|set|split|test|treat|use|wrap|write)\b", re.I)

def top_fix(fix):
    """The first instruction in a Core fixes entry, without its bold heading or fact prefix."""
    body = re.sub(r"^\*\*[^*]+\*\*\s*(?:\([^)]*\)\.?\s*)?", "", fix.strip())
    body = re.sub(r"^\**F\d+(?:/F\d+)*\**\s*[:,\u2014-]\s*", "", body)
    ss = [x for x in sentences(body) if not x.startswith(("**(", "Source:", "Sources:"))]
    pick = next((x for x in ss if IMPERATIVE.match(x)), ss[0] if ss else "")
    return pick[:1].upper() + pick[1:] if pick else ""

def linkify(text, d):
    """file:line refs (and ',140' or backticked ':40' follow-ons) link to the project at its rated commit; docs slugs link to TypeSafe."""
    url, commit = d.get("url", "").rstrip("/"), d.get("commit", "").split()[0] if d.get("commit") else ""
    if re.match(r"https://(?:github\.com|huggingface\.co)/[^/]+/[^/]+$", url) and re.fullmatch(r"[0-9a-f]{7,40}", commit):
        def link(path, a, b):
            return f"[`{path}:{a}{'-' + b if b else ''}`]({url}/blob/{commit}/{path}#L{a}" + (f"-L{b}" if b else "") + ")"
        last, end = [None], [-9]
        def ln(m):
            if m.group("n2") and m.start() != end[0] + 2: return m.group(0)  # a bare `N` links only right after a ref
            if m.group("p"): last[0] = m.group("p")
            if not last[0]: return m.group(0)
            end[0] = m.end()
            nums = re.findall(r"(\d+)(?:-(\d+))?", m.group("n") or m.group("n2"))
            return ", ".join(link(last[0], a, b) for a, b in nums)
        text = re.sub(r"(?<!\[)(?:`?(?P<p>[\w./-]+\.(?:" + CODE_EXT + r"))|`(?=:\d))\:(?P<n>\d+(?:-\d+)?(?:,\s*\d+(?:-\d+)?)*)`?|(?<=`, )`(?P<n2>\d+(?:-\d+)?)`", ln, text)
    return DOC_SLUG.sub(lambda m: f"[`{m.group(1)}`](https://docs.typesafe.ai/{m.group(1)})", text)

def cell(x): return x.replace("|", "/").replace("\n", " ")

CODE_LABEL = {"1a": "False marketing: Jev in name only", "1b": "Not a Jev integration", "1c": "Jev answers unused",
              "1g": "Misleading guide", "1r": "Replaces Jev, not yet rated", "1t": "Guide, not yet rated"}

def verdict_label(t, v):
    code = front_text(t).get("verdict_1_code", "").split("#")[0].strip()
    if v == "1" and code in CODE_LABEL: return CODE_LABEL[code]
    if v == "1" and is_guide(front_text(t)): return "Misleading guide"
    if v == "1":
        for lab in ("False marketing: Jev in name only", "Not a Jev integration"):
            if lab.lower() in t.lower(): return lab
    return VERDICT_LABEL.get(v, v)

def minor_fact(n, finding, name):
    """Fix-only facts: never lower a verdict (F12, F14, F23; F20/F22 below very high stakes)."""
    return n in FIX_ONLY or (n in (20, 22) and "very high" not in finding.lower()) or "fix-only" in (name + finding).lower()

def why_line(t, d):
    if d.get("why"): return d["why"].strip()
    s = section(t, "Summary").strip()
    m = re.match(r"(.+?[.!?])(\s|$)", s, re.S)
    return (m.group(1) if m else s).replace("\n", " ").strip()

def dots(x):
    return "●" * int(x) + "○" * (3 - int(x)) if str(x).isdigit() else "n.a."

def export_pages(p):
    """-> (detail page, full page, front matter, rubric, why) for one rating."""
    t = p.read_text(errors="ignore"); d = front_text(t); v = d.get("verdict", "").split()[0] if d.get("verdict") else ""
    r = d.get("rubric", "").split(); r = r[0] if r else ""
    slug = p.parent.name; label = verdict_label(t, v)
    who = f"{d.get('owner', '')}/{d.get('project', slug)}" if "github.com" in d.get("url", "") else d.get("project", slug)
    commit = d.get("commit", "").split()[0] if d.get("commit") else ""
    at = (f"at [`{commit[:7]}`]({d['url'].rstrip('/')}/tree/{commit})" if re.fullmatch(r"[0-9a-f]{7,40}", commit) and re.search(r"github\.com|huggingface\.co", d.get("url", ""))
          else f"[{d.get('url', '')}]({d.get('url', '')}), {d.get('commit', '')}")
    ptype = d.get("project_type", "").split()[0] if d.get("project_type") else ""
    ptype = "" if ptype in ("", "unrecorded") else ptype.replace("-", " ")
    sc = dict(re.findall(r"(\w+):\s*([\w.]+)", d.get("scores", "")))
    scores = " · ".join(f"{k.capitalize()} {dots(sc.get(k, ''))}" for k in ("execution", "fit", "coverage", "evidence"))
    stale = [f"*Rated under an earlier rubric ({r or 'unrecorded'}). A re-rating is queued.*", ""] if r < RUBRIC else []
    rows = fact_rows(t); summ = section(t, "Summary").strip()
    summ_lines = sentences(summ)[:3]
    fixes = [re.sub(r"^\d+\.\s*", "", l).strip() for l in section(t, "Core fixes").splitlines() if re.match(r"^\d+\.", l.strip())]
    top = top_fix(fixes[0]) if fixes else ""
    failing = [x for x in rows if x[2] in ("no", "unknown")]
    major = [x for x in failing if not minor_fact(x[0], x[3], x[1])]
    minor = [x for x in failing if minor_fact(x[0], x[3], x[1])]
    tested = next((section(t, h) for h in ("Tested here", "Does it help") if section(t, h).strip()), "")
    L = lambda x: linkify(x, d)
    detail = ["[← All ratings](README.md)", ""] + stale + [
        f"> **{who}** {at}" + (f" · {ptype}" if ptype else ""), f"> ### Verdict {v}: {label}", f"> {scores}", ">"]
    detail += [f"> - {L(x)}" for x in summ_lines]
    if top: detail += [">", f"> **Top fix:** {L(top)}"]
    detail += ["", "## What holds it back", ""] + ([f"- **{n_}** ({fid(n)}): {L(f)}" for n, n_, _, f in major] or ["Nothing that lowers the verdict."])
    if tested.strip(): detail += ["", "## Tested here", "", L(tested.strip())]
    if fixes:
        detail += ["", "## Fixes (from reading the code; not tested against it)", ""] + [f"{i}. {L(x)}" for i, x in enumerate(fixes[:3], 1)]
    if minor: detail += ["", "**Minor:** " + "; ".join(f"{n_} ({fid(n)})" for n, n_, _, _ in minor) + ". These are listed fixes and don't lower the verdict."]
    detail += ["", f"[Full rating: every fact, its evidence and the files read →](full/{slug}.md)", ""]
    head = f"**Verdict {v}, {label}**" + (f" · {ptype}" if ptype else "") + f" · rated {d.get('rated', '')} {at} · read: {d.get('depth', '').split()[0] if d.get('depth') else ''} · rubric {r or 'unrecorded'}{' (earlier)' if stale else ''} · {d.get('rater', 'rater unrecorded')}" + (f", {d['effort'].split()[0]} effort" if d.get("effort") else "")
    full = [f"[← Summary](../{slug}.md)", "", f"# {d.get('project', slug)}: full rating", "", head, ""] + stale + ["## Summary", "", L(summ), "",
            "## What fails", "", "| Fact | Finding |", "|---|---|"]
    full += [f"| {cell(n_)} ({fid(n)}) | **{val}.** {cell(L(f))} |" for n, n_, val, f in rows if n == 0 or val in ("no", "unknown")]
    passes = [x for x in rows if x[0] != 0 and x[2] not in ("no", "unknown")]
    if passes:
        full += ["", "<details>", f"<summary><b>What passes ({sum(x[2] == 'yes' for x in passes)}) and doesn't apply ({sum(x[2] == 'n.a.' for x in passes)})</b></summary>", "",
                 "| Fact | Finding |", "|---|---|"] + [f"| {cell(n_)} ({fid(n)}) | {val}. {cell(L(f))} |" for n, n_, val, f in passes] + ["", "</details>"]
    for title, name in (("Scores", "Scores"), ("Why this verdict", "Verdict and reasoning")):
        if section(t, name).strip(): full += ["", f"## {title}", "", L(section(t, name).strip())]
    if tested.strip(): full += ["", "## Tested here", "", L(tested.strip())]
    if fixes: full += ["", "## Fixes (from reading the code; not tested against it)", ""] + [f"{i}. {L(x)}" for i, x in enumerate(fixes, 1)]
    cov = section(t, "Coverage").strip()
    if cov: full += ["", "<details>", f"<summary><b>Files read ({len([l for l in cov.splitlines() if l.strip().startswith('-')])})</b></summary>", "", cov, "", "</details>"]
    return "\n".join(detail) + "\n", "\n".join(full) + "\n", d, r, why_line(t, d)

def export(outdir):
    outdir = pathlib.Path(outdir); pages = {}; rows = []; any_stale = False
    # Only full reads and approved scopes are published; quick (extract) ratings stay in the library.
    for slug, p in sorted(latest_per_project(full_only=True).items()):
        detail, full, d, r, why = export_pages(p); pages[slug] = (p, detail, full)
        v = d.get("verdict", "").split()[0] if d.get("verdict") else ""
        stale = r < RUBRIC; any_stale |= stale
        who = f"{d.get('owner', '')}/{d.get('project', slug)}" if "github.com" in d.get("url", "") else d.get("project", slug)
        ptype = (d.get("project_type", "").split() or [""])[0]
        ptype = "" if ptype == "unrecorded" else ptype.replace("-", " ")
        rows.append((-int(v) if v.isdigit() else 0, f"| [{who}]({slug}.md) | {ptype} | **{v} {verdict_label(p.read_text(errors='ignore'), v)}** | {cell(why)} | {d.get('rated', '')}{' †' if stale else ''} |"))
    tpl = SKILL / "ratings-template"
    readme = (tpl / "README.md").read_text().rstrip("\n") + "\n\n## Ratings\n\n| Project | Type | Verdict | Why | Rated |\n|---|---|---|---|---|\n" + "\n".join(r for _, r in sorted(rows)) + "\n"
    if any_stale: readme += "\n† Rated under an earlier rubric; a re-rating is queued.\n"
    pt = LIB / "private-terms.txt"; pats = []
    if pt.exists():
        pats = [re.compile(l.strip(), re.I) for l in pt.read_text().splitlines() if l.strip() and not l.lstrip().startswith("#")]
    else:
        print(f"warning: {pt} not found; no private-term scan", file=sys.stderr)
    hits = []
    for name, text in [(f"{s}.md", x[1]) for s, x in pages.items()] + [(f"full/{s}.md", x[2]) for s, x in pages.items()] + [("README.md", readme)]:
        for i, line in enumerate(text.splitlines(), 1):
            for pat in pats:
                if pat.search(line):
                    src = ""
                    if name != "README.md":
                        sp = pages[name.split("/")[-1][:-3]][0]
                        j = next((k for k, l in enumerate(sp.read_text(errors="ignore").splitlines(), 1) if l.strip() and l.strip() in line), None)
                        src = f" (source {sp}" + (f":{j}" if j else "") + ")"
                    hits.append(f"{name}:{i}: matches private term /{pat.pattern}/{src}")
    for slug, (sp, _, _) in pages.items():
        for i, line in enumerate(sp.read_text(errors="ignore").splitlines(), 1):
            for pat in pats:
                if pat.search(line):
                    hits.append(f"{sp}:{i}: matches private term /{pat.pattern}/ (in the source rating, exported or not; review before publishing)")
    if hits:
        sys.exit("export refused; nothing written:\n- " + "\n- ".join(hits))
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "full").mkdir(exist_ok=True)
    for s, (_, detail, full) in pages.items():
        (outdir / f"{s}.md").write_text(detail); (outdir / "full" / f"{s}.md").write_text(full)
    (outdir / "README.md").write_text(readme)
    shutil.copy(tpl / "LICENSE", outdir / "LICENSE")
    print(f"exported {len(pages)} pages to {outdir}")

def blind(exclude, out):
    out = pathlib.Path(out)
    owner, proj = exclude.lower().split("/", 1)
    hit = re.compile(re.escape(proj) + "|" + re.escape(exclude), re.I); kept = 0
    for p in ratings_glob():
        d = front(p)
        if d.get("owner", "").lower() == owner and d.get("project", "").lower() == proj: continue
        lines = ["[redacted: mentions the project under test]" if hit.search(l) and not l.startswith(("project:", "url:", "owner:")) else l
                 for l in p.read_text(errors="ignore").splitlines()]
        dest_dir = out / "projects" / p.parent.name; dest_dir.mkdir(parents=True, exist_ok=True)
        (dest_dir / p.name).write_text("\n".join(lines) + "\n"); kept += 1
    print(f"{kept} ratings copied to {out}, {exclude} removed and mentions redacted.")
    print(f"Rater runs with: JEVALUATE_LIBRARY={out}")

def cards(d, exclude, limit=5):
    """Past ratings closest to d: same project_type +3, same lineage +2, +1 per shared stage. Closest first."""
    stages = lambda x: {y.strip() for y in x.get("stages", "").strip("[]").split(",") if y.strip()}
    lin = d.get("lineage", "").split(":")[-1]; hits = []
    for p in sorted(ratings_glob(), reverse=True):
        t = p.read_text(errors="ignore"); e = front_text(t); s = 0
        if exclude and f"{e.get('owner','')}/{e.get('project','')}".lower() == exclude.lower(): continue
        if d.get("project_type") and d.get("project_type") == e.get("project_type"): s += 3
        if lin and lin != "new" and lin in e.get("lineage", ""): s += 2
        s += len(stages(d) & stages(e))
        if s:
            failed = [fid(n) for n, _, v, _ in fact_rows(t) if v == "no"]
            hits.append((s, {"path": p, "verdict": e.get("verdict", ""), "code": e.get("verdict_1_code", "").split("#")[0].strip(),
                             "why": why_line(t, e), "failed": failed, "old": e.get("rubric", "") < RUBRIC}))
    hits.sort(key=lambda h: -h[0])
    return [c for _, c in hits[:limit]]

def similar(lineage, stage, limit, exclude=None):
    PROJ.mkdir(parents=True, exist_ok=True)
    found = cards({"lineage": lineage or "", "stages": f"[{stage}]" if stage else ""}, exclude, limit)
    for c in found:
        old = "  [old rubric: context only, not precedent]" if c["old"] else ""
        print(f"{c['path']}  verdict={c['verdict']} {c['code']}  {c['why']}  failed: {', '.join(c['failed']) or 'none'}{old}")
    if not found: print("no similar ratings yet")

def migrate():
    if not RAT.exists() or not any(RAT.glob("*.md")):
        print("ratings/ is empty or missing; nothing to migrate")
        print(f"index: {index()} ratings")
        return
    pat = re.compile(r"^(.*?)(?:-(\d+))?\.md$")
    groups = {}
    for p in RAT.glob("*.md"):
        d = front(p)
        rated = d.get("rated", "")
        if not re.fullmatch(r"\d{4}-\d\d-\d\d", rated): print(f"skipped {p.name}: rated is not a date"); continue
        slug = slug_for(d.get("url", ""))
        m = pat.match(p.name)
        base, num = (m.group(1), int(m.group(2)) if m.group(2) else 1) if m else (p.name, 1)
        groups.setdefault((rated, slug), []).append((base, num, p))
    PROJ.mkdir(parents=True, exist_ok=True)
    moved = 0
    for (rated, slug), items in groups.items():
        items.sort(key=lambda x: (x[0], x[1]))
        pdir = PROJ / slug; pdir.mkdir(parents=True, exist_ok=True)
        for i, (base, num, p) in enumerate(items):
            name = f"{rated}.md" if i == 0 else f"{rated}-{i+1}.md"
            dest = pdir / name
            shutil.move(str(p), str(dest))
            moved += 1
    if RAT.exists() and not any(RAT.iterdir()):
        RAT.rmdir()
    print(f"migrated {moved} ratings")
    print(f"index: {index()} ratings")

def list_add(name, entries):
    entries = pathlib.Path(entries)
    today = datetime.date.today().isoformat()
    ldir = LIB / "lists" / name; ldir.mkdir(parents=True, exist_ok=True)
    dest = ldir / f"entries-{today}.tsv"
    n = 2
    while dest.exists():
        dest = ldir / f"entries-{today}-{n}.tsv"; n += 1
    shutil.copy(entries, dest)
    latest = ldir / "entries.tsv"
    shutil.copy(entries, latest)
    print(dest); print(latest)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["add", "index", "similar", "check", "blind", "migrate", "list-add", "stale", "export", "migrate-fields", "fill-docs"])
    ap.add_argument("file", nargs="?")
    ap.add_argument("list_file", nargs="?")
    ap.add_argument("--lineage"); ap.add_argument("--stage"); ap.add_argument("--limit", type=int, default=3); ap.add_argument("--exclude"); ap.add_argument("--out")
    ap.add_argument("--link-docs", action="store_true"); ap.add_argument("--evidence"); ap.add_argument("--supersedes")
    a = ap.parse_intermixed_args()
    if a.cmd == "add":
        if not a.file: sys.exit("add needs <rating.md>")
        add(a.file, a.link_docs, a.evidence, a.supersedes)
    elif a.cmd == "check":
        problems = check(a.file, evidence=a.evidence)
        for w in WARNINGS: print("warning: " + w, file=sys.stderr)
        print(("ok" + (f"\nderived top_stakes: {DERIVED['top_stakes']}" if DERIVED.get("top_stakes") else "")) if not problems else "- " + "\n- ".join(problems)); sys.exit(1 if problems else 0)
    elif a.cmd == "blind":
        if not (a.exclude and a.out): sys.exit("blind needs --exclude owner/repo and --out DIR")
        blind(a.exclude, a.out)
    elif a.cmd == "index": print(f"index: {index()} ratings")
    elif a.cmd == "migrate": migrate()
    elif a.cmd == "stale": stale()
    elif a.cmd == "export":
        if not a.file: sys.exit("export needs <outdir>")
        export(a.file)
    elif a.cmd == "migrate-fields": migrate_fields()
    elif a.cmd == "fill-docs": fill_docs_existing()
    elif a.cmd == "list-add":
        if not (a.file and a.list_file): sys.exit("list-add needs <list-name> <entries.tsv>")
        list_add(a.file, a.list_file)
    else: similar(a.lineage, a.stage, a.limit, a.exclude)
