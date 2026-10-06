"""Lint the grader's instructions before any eval run: the allowed-value lines in rubric.md match
read.md's template and task.md names every field; no eval case is named in any instruction file;
no em-dashes. Exit 1 with a list of problems."""
import json, pathlib, re, sys

HERE = pathlib.Path(__file__).parent
SKILL = HERE.parent / "jevaluate"
sys.path.insert(0, str(SKILL / "scripts"))
from rubric_text import allowed_values
import rubric_text
INSTRUCTIONS = [SKILL / "SKILL.md", SKILL / "read.md", SKILL / "rubric.md", HERE / "task.md", SKILL / "enforcement.md"]
FIELDS = ("project_type", "verdict_1_code")  # asked of the rater and the eval grader; kind is derived from the type by code
ENFORCEMENT = SKILL / "enforcement.md"
ASKS_KIND = re.compile(r"\bkind\b(?!\s+of\b)")

def template_values(read_text):
    """{field: [values]} from read.md template lines like 'kind: uses | teaches   # comment'."""
    out = {}
    for f in FIELDS:
        m = re.search(rf"^{f}: (.+?)(?:\s+#.*)?$", read_text, re.M)
        if m: out[f] = [v.strip() for v in m.group(1).split("|")]
    return out

def case_names(gold, sources):
    names = {k.lower() for g in gold.values() for k in g.get("match", [])}
    for s in sources.values():
        if s.get("repo"): names |= {s["repo"].lower(), s["repo"].split("/")[-1].lower()}
    return sorted(n for n in names if len(n) >= 3)

def lint(files, rubric_text, read_text, task_text, names):
    problems, allowed, tmpl = [], allowed_values(rubric_text), template_values(read_text)
    if "kind" not in allowed: problems.append("rubric.md has no '- `kind` values:' line")
    if re.search(r"^kind:", read_text, re.M): problems.append("read.md template asks for kind; code derives it from project_type")
    if ASKS_KIND.search(task_text): problems.append("task.md asks for kind; code derives it from project_type")
    for f in FIELDS:
        if f not in allowed: problems.append(f"rubric.md has no '- `{f}` values:' line"); continue
        if tmpl.get(f) != allowed[f]: problems.append(f"read.md template {f} {tmpl.get(f)} != rubric.md {allowed[f]}")
        if f not in task_text: problems.append(f"task.md never names the field {f}")
    for path, text in files.items():
        low = text.lower()
        for n in names:
            if re.search(r"(?<![\w-])" + re.escape(n) + r"(?![\w-])", low): problems.append(f"{path}: names eval case {n!r}")
        if "—" in text: problems.append(f"{path}: em-dash")
    return problems

ROW_ID = re.compile(r"^\|\s*(F\d+|[a-z][a-z0-9_]*)\b")
FUNC_REF = re.compile(r"`?\b(library|step)\.(\w+)")

def enforcement_problems(text=None, rubric=None):
    """enforcement.md: a row for every routing call and every fact, each naming a defined function or giving a reason it stays judgment."""
    import library, step
    mods = {"library": library, "step": step}
    text = text if text is not None else ENFORCEMENT.read_text() if ENFORCEMENT.exists() else ""
    rubric = rubric if rubric is not None else rubric_text._text(None)
    want = list(allowed_values(rubric)) + ["F0"] + [f"F{n}" for n in sorted({int(m.group(1)) for m in re.finditer(r"^\| F(\d+) ", rubric_text.section(2, rubric), re.M)})]
    rows = {}
    for line in text.splitlines():
        m = ROW_ID.match(line)
        if m and not line.startswith(("| rule", "|--")):
            rows.setdefault(m.group(1), []).append([c.strip() for c in line.strip().strip("|").split("|")])
    problems = []
    for w in want:
        if w not in rows: problems.append(f"enforcement.md has no row for {w}; add '| {w} | <function> | <or judgment, because> |'")
    for w, rs in rows.items():
        for cells in rs:
            by, why = (cells + ["", ""])[1], (cells + ["", ""])[2]
            refs = FUNC_REF.findall(by)
            for mod, fn in refs:
                if not hasattr(mods[mod], fn): problems.append(f"enforcement.md row {w} names {mod}.{fn}, which is not defined")
            if by and not refs: problems.append(f"enforcement.md row {w}: 'enforced by' names no library.<function> or step.<function>")
            if not refs and not why: problems.append(f"enforcement.md row {w} has neither a function that enforces it nor a reason it stays judgment")
    return problems

NAMED = re.compile(r"(?<![\w./-])((?:scripts|evals)/[\w./-]+\.\w+|[\w-]+\.(?:md|py|json))(?![\w/-])")
PREFIXED = re.compile(r"(?<![\w./-])((?:jevaluate|jevaluate-harness|jevaluate-eval)/[\w./-]+\.\w+)(?![\w/-])")
ALLOW_NAMED = {"rating.md", "prompt.md", "manifest.md", "meta.json", "extract.md", "agreement.md", "rubric-tuning-log.md", "EVAL-RESULTS.md"}
UNBUILT = re.compile(r"coming soon|not yet built|\bTODO mode\b", re.I)


def named_files_problems(skill_dir):
    """Every scripts/, evals/ path and skill-root .md/.py/.json name a skill's markdown gives must exist;
    no 'coming soon'. Outputs and create-if-missing files are allowed."""
    skill_dir = pathlib.Path(skill_dir); problems = []
    for md in sorted(skill_dir.glob("*.md")):
        text = md.read_text()
        if UNBUILT.search(text): problems.append(f"{md.name}: names an unbuilt mode ({UNBUILT.search(text).group(0)!r})")
        for name in sorted(set(PREFIXED.findall(text))):
            if name.rsplit("/", 1)[-1] in ALLOW_NAMED: continue
            if not ((skill_dir.parent / name).exists() or (skill_dir / name).exists()):  # a skill folder, or the repo root
                problems.append(f"{md.name}: names {name}, which does not exist")
        for name in sorted(set(NAMED.findall(text))):
            if name in ALLOW_NAMED or name.rsplit("/", 1)[-1] in ALLOW_NAMED: continue
            if "/" in name:
                if not (skill_dir / name).exists(): problems.append(f"{md.name}: names {name}, which does not exist")
            elif name.endswith(".md") and not any((d / name).exists() for d in (skill_dir, skill_dir / "evals", skill_dir / "scripts", *(skill_dir.parent / n for n in ("jevaluate", "jevaluate-harness", "jevaluate-eval", "shared")))):
                problems.append(f"{md.name}: names {name}, which does not exist")
    return problems


LONG_SENTENCE = 35  # words; a rater reads these mid-rating (2026-10-06: a 49-word rule sentence came back as a run-on)


def _sentences(text):
    text = re.sub(r"`[^`]*`|https?://\S+", "x", text)
    for line in text.splitlines():
        if line.startswith(("|", "```")): continue
        for s in re.split(r"(?<=[.!?])\s+", line.strip(" -*")):
            if s.strip(): yield s.strip()


def long_new_sentences(now, frozen, limit=LONG_SENTENCE):
    """Sentences over `limit` words in `now` that aren't in `frozen`: only wording added since the freeze is flagged."""
    old = set(_sentences(frozen))
    return [s for s in _sentences(now) if len(s.split()) > limit and s not in old]


def long_sentence_problems(skill_dir=SKILL):
    tag = rubric_text.newest_tag()
    if not tag: return []
    out = []
    for name in ("rubric.md", "read.md"):
        r = rubric_text._git(rubric_text.ROOT, "show", f"{tag}:jevaluate/{name}")
        frozen = r.stdout.decode(errors="replace") if r.returncode == 0 else ""
        for s in long_new_sentences((skill_dir / name).read_text(), frozen):
            out.append(f"{name}: a new sentence of {len(s.split())} words (limit {LONG_SENTENCE}); split it: {s[:80]}...")
    return out


if __name__ == "__main__":
    files = {p.name: p.read_text() for p in INSTRUCTIONS}
    names = case_names(json.loads((HERE / "gold.json").read_text()), json.loads((HERE / "sources.json").read_text()))
    probs = lint(files, files["rubric.md"], files["read.md"], files["task.md"], names)
    probs += named_files_problems(SKILL) + named_files_problems(SKILL.parent / "jevaluate-harness") + named_files_problems(SKILL.parent / "jevaluate-eval") + enforcement_problems() + long_sentence_problems()
    print("\n".join(probs) or "lint clean"); sys.exit(1 if probs else 0)
