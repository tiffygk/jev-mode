import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import lint_materials as lm

RUB = "- `kind` values: uses, teaches\n- `project_type` values: workflow, guide\n- `verdict_1_code` values: 1a, none\n"
READ = "project_type: workflow | guide   # note\nverdict_1_code: 1a | none\n"
TASK = "project_type, verdict_1_code"

def test_clean_passes():
    assert lm.lint({"rubric.md": RUB}, RUB, READ, TASK, ["kev"]) == []

def test_mismatched_template_fails():
    assert any("read.md template project_type" in p for p in lm.lint({}, RUB, READ.replace("guide", "gide"), TASK, []))

def test_missing_value_line_fails():
    assert any("no '- `kind` values:'" in p for p in lm.lint({}, RUB.split("\n", 1)[1], READ, TASK, []))

def test_task_missing_field_fails():
    assert any("task.md" in p for p in lm.lint({}, RUB, READ, "project_type", []))

def test_asking_the_rater_for_kind_fails():
    # kind is derived from the type by code: neither the template nor the task may ask for it.
    assert any("read.md template" in p and "kind" in p for p in lm.lint({}, RUB, "kind: uses | teaches\n" + READ, TASK, []))
    assert any("task.md" in p and "kind" in p for p in lm.lint({}, RUB, READ, "1. kind and project_type, verdict_1_code", []))

def test_planted_case_name_fails():
    assert any("'kev'" in p for p in lm.lint({"rubric.md": RUB + "Example: kev, a model.\n"}, RUB, READ, TASK, ["kev"]))

def test_name_inside_a_word_passes():
    assert lm.lint({"rubric.md": RUB + "a kevlar vest\n"}, RUB, READ, TASK, ["kev"]) == []

def test_em_dash_fails():
    assert any("em-dash" in p for p in lm.lint({"x.md": "a — b"}, RUB, READ, TASK, []))

def test_case_names_from_gold_and_sources():
    names = lm.case_names({"a": {"match": ["Omni"]}}, {"b": {"repo": "jaredpalmer/kev"}})
    assert names == ["jaredpalmer/kev", "kev", "omni"]


def _skill(tmp_path, text):
    (tmp_path / "scripts").mkdir(exist_ok=True); (tmp_path / "scripts" / "real.py").write_text("")
    (tmp_path / "SKILL.md").write_text(text); return tmp_path

def test_named_missing_script_fails(tmp_path):
    probs = lm.named_files_problems(_skill(tmp_path, "Run `scripts/missing.py` first.\n"))
    assert any("scripts/missing.py" in p for p in probs)

def test_named_existing_and_allowlisted_pass(tmp_path):
    assert lm.named_files_problems(_skill(tmp_path, "Run `scripts/real.py`; it writes manifest.md and `evals/extract.md`.\n")) == []

def test_coming_soon_fails(tmp_path):
    assert any("coming soon" in p for p in lm.named_files_problems(_skill(tmp_path, "The audit mode is coming soon.\n")))

def test_real_repo_named_files_pass():
    assert lm.named_files_problems(pathlib.Path(lm.__file__).resolve().parents[1]) == []
    assert lm.named_files_problems(pathlib.Path(lm.__file__).resolve().parents[2] / "jevaluate-harness") == []


def test_prefixed_missing_path_fails(tmp_path):
    skill = tmp_path / "jevaluate"; skill.mkdir(); (skill / "SKILL.md").write_text("Run `jevaluate/scripts/missing.py`.\n")
    assert any("jevaluate/scripts/missing.py" in p for p in lm.named_files_problems(skill))

def test_prefixed_existing_path_passes(tmp_path):
    skill = tmp_path / "jevaluate"; (skill / "scripts").mkdir(parents=True); (skill / "scripts" / "real.py").write_text("")
    (skill / "SKILL.md").write_text("Run `jevaluate/scripts/real.py`.\n")
    assert lm.named_files_problems(skill) == []


# --- enforcement table ---
RUBRIC_FACTS = "# Jevaluate rubric (2026-09-29)\n## 1. Routing\n- `kind` values: uses\n- `project_type` values: workflow\n- `stakes` values: low\n\n## 2. Facts\n| Fact | Means |\n|---|---|\n| F1 Atomic | x |\n| F2 Primitive | x |\n"
def _table(rows): return "| rule | enforced by | or judgment, because |\n|---|---|---|\n" + "\n".join(rows) + "\n"
GOOD_ROWS = ["| kind | `library.store_derived` | |", "| project_type | `library.check_schema` | |", "| stakes | `library.check_decisions` | |",
             "| F0 calls Jev | `library.check_f0` | |", "| F1 Atomic | | needs reading the question wording |", "| F2 Primitive | `step.missing` | |"]

def test_enforcement_table_covers_every_fact():
    assert lm.enforcement_problems(_table(GOOD_ROWS), RUBRIC_FACTS) == []
    assert any("F2" in p and "no row" in p for p in lm.enforcement_problems(_table(GOOD_ROWS[:-1]), RUBRIC_FACTS))
    assert any("stakes" in p and "no row" in p for p in lm.enforcement_problems(_table(GOOD_ROWS[:2] + GOOD_ROWS[3:]), RUBRIC_FACTS))
    assert any("F0" in p and "no row" in p for p in lm.enforcement_problems(_table(GOOD_ROWS[:3] + GOOD_ROWS[4:]), RUBRIC_FACTS))

def test_enforcement_table_names_only_defined_functions():
    rows = GOOD_ROWS[:5] + ["| F2 Primitive | `library.check_nothing_here` | |"]
    assert any("library.check_nothing_here" in p for p in lm.enforcement_problems(_table(rows), RUBRIC_FACTS))

def test_enforcement_row_needs_a_check_or_a_reason():
    rows = GOOD_ROWS[:5] + ["| F2 Primitive | | |"]
    assert any("F2" in p and "neither" in p for p in lm.enforcement_problems(_table(rows), RUBRIC_FACTS))

def test_real_enforcement_table_is_clean():
    assert lm.enforcement_problems() == []
