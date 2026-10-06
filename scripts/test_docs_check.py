"""docs_check: a source change needs its doc, or a waiver; counts in README prose are flagged."""
import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import docs_check as dc

RULES = [{"name": "harness scripts", "sources": ["jevaluate-harness/scripts/*"], "docs": ["jevaluate-harness/README.md"], "why": "w"},
         {"name": "a new skill", "sources": ["*/SKILL.md"], "added_only": True, "docs": ["README.md"], "why": "w"}]


def test_source_without_doc_fails():
    p = dc.map_problems(RULES, {"jevaluate-harness/scripts/x.py"}, set(), set())
    assert len(p) == 1 and "harness scripts" in p[0] and "Docs checked: jevaluate-harness/README.md" in p[0]


def test_source_with_doc_passes():
    assert dc.map_problems(RULES, {"jevaluate-harness/scripts/x.py", "jevaluate-harness/README.md"}, set(), set()) == []


def test_waiver_passes():
    text = "Docs checked: jevaluate-harness/README.md unchanged because the script's output is the same"
    waived = {m.group(1) for m in dc.WAIVER.finditer(text)}
    assert dc.map_problems(RULES, {"jevaluate-harness/scripts/x.py"}, set(), waived) == []


def test_waiver_needs_a_reason():
    assert not list(dc.WAIVER.finditer("Docs checked: README.md unchanged because"))


def test_added_only_rule_ignores_edits():
    assert dc.map_problems(RULES, {"jev-lens/SKILL.md"}, set(), set()) == []
    assert dc.map_problems(RULES, {"new-skill/SKILL.md"}, {"new-skill/SKILL.md"}, set())


def test_counts_in_prose_flagged_tables_and_quotes_not(tmp_path):
    (tmp_path / "x").mkdir()
    (tmp_path / "x" / "README.md").write_text("We rated 19 projects so far.\n| 19 projects | in a table |\n> 19 cases in a dated sample\n```\n19 cases in code\n```\n")
    cfg = {"files": ["*/README.md"], "skip": [], "patterns": [r"\b\d+ (ratings|projects|cases)\b"], "why": "w"}
    p = dc.count_problems(cfg, root=tmp_path)
    assert len(p) == 1 and p[0].startswith("x/README.md:1:")


def test_repo_map_names_real_docs():
    cfg = json.loads((dc.ROOT / "docs-map.json").read_text())
    missing = [d for r in cfg["rules"] for d in r["docs"] if not (dc.ROOT / d).exists()]
    assert missing == [], missing


# Retired names: an old name may appear only in files listed for it, and each listed file must still contain it.
RETIRED = {"self": "retired-names.json", "names": [
    {"pattern": r"\bcalib\b|test_calibration|calibration\.md|calibration/", "flags": "i", "allowed": {}, "why": "renamed to rater_agreement"},
    {"pattern": r"calibrat", "flags": "i", "allowed": {"jevaluate/rubric.md": "golden: Jev's meaning", "ratings/*.md": "published ratings quote projects"},
     "why": "in jev-mode, calibration means tuning on labeled results, not rater agreement"}]}


def test_retired_name_outside_allowed_fails():
    p = dc.retired_problems(RETIRED, {"README.md": "Run calib.py score\n", "jevaluate/rubric.md": "calibrates", "ratings/a.md": "calibrated"})
    assert len(p) == 1 and p[0].startswith("README.md:1:") and "rater_agreement" in p[0]


def test_word_in_allowed_file_passes():
    assert dc.retired_problems(RETIRED, {"jevaluate/rubric.md": "calibrated probabilities", "ratings/a.md": "calibrated"}) == []


def test_word_in_unlisted_file_fails():
    p = dc.retired_problems(RETIRED, {"jevaluate/rubric.md": "calibrates", "ratings/a.md": "calibrated", "jevaluate-eval/SKILL.md": "Rater calibration"})
    assert len(p) == 1 and p[0].startswith("jevaluate-eval/SKILL.md:1:")


def test_listed_file_that_lost_its_word_is_stale():
    p = dc.retired_problems(RETIRED, {"jevaluate/rubric.md": "no such word", "ratings/a.md": "calibrated"})
    assert len(p) == 1 and "jevaluate/rubric.md" in p[0] and "no longer" in p[0]


def test_allowed_glob_with_no_match_is_stale():
    p = dc.retired_problems(RETIRED, {"jevaluate/rubric.md": "calibrates"})
    assert len(p) == 1 and "ratings/*.md" in p[0]


def test_retired_list_itself_is_skipped():
    assert dc.retired_problems(RETIRED, {"retired-names.json": "calib.py", "jevaluate/rubric.md": "calibrates", "ratings/a.md": "calibrated"}) == []


def test_upper_case_old_name_fails():
    p = dc.retired_problems(RETIRED, {"x.md": "see CALIBRATION.md", "jevaluate/rubric.md": "calibrates", "ratings/a.md": "calibrated"})
    assert any(q.startswith("x.md:1:") for q in p)
