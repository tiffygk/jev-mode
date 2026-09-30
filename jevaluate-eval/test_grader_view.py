import html, pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import build_grader_view as gv
import rubric_text as rt
import step

def _view(tmp_path, notes=""):
    out = tmp_path / "view.html"; gv.build(out, notes)
    return html.unescape(out.read_text())

def test_view_has_every_step_heading(tmp_path):
    page = _view(tmp_path)
    for heading in ("## 1. Routing", "## 2. Facts", "## 3. Scores", "## 4. Build stages", "## 5. Verdict"):
        assert heading in page, heading
    assert "Comparison cards" in page

def test_view_has_every_stakes_row_labelled_with_a_level(tmp_path):
    page = _view(tmp_path)
    rows = [l for l in rt.section(2).splitlines() if re.match(r"\| F(11|13|20|22) ", l)]
    assert len(rows) == 9
    for row in rows:
        label = re.match(r"\| F\d+ ([^|]*)\|", row).group(1).strip().rsplit(", ", 1)[-1]
        assert label in step.ROW_LEVELS, label
        assert row.split("|")[1].strip() in page and f"| {label} |" in page

def test_view_shows_brief_skill_read_and_grader_prompt(tmp_path):
    page = _view(tmp_path, "Notes for the owner.")
    root = pathlib.Path(gv.REPO)
    assert "example/ticket-router" in page and "# Jevaluate: rating a project" in page and "name: jevaluate" in page
    assert (root / "jevaluate-eval/task.md").read_text().strip()[:80] in page
    assert "Notes for the owner." in page

def test_view_names_no_home_or_vault_path(tmp_path):
    page = _view(tmp_path)
    assert str(pathlib.Path.home()) not in page and "Obsidian" not in page
    import tempfile
    assert tempfile.gettempdir() not in page and "<library>/projects/example__mail-sorter" in page

def test_builder_finds_the_repo_from_its_own_location():
    assert (pathlib.Path(gv.REPO) / "jevaluate" / "SKILL.md").exists() and pathlib.Path(gv.__file__).resolve().parents[1] == pathlib.Path(gv.REPO)

def test_sample_rating_leaves_kind_to_code():
    assert "kind:" not in gv.SAMPLE


def test_help_prints_usage_and_exits_zero():
    import subprocess
    for flag in ("--help", "-h"):
        r = subprocess.run([sys.executable, gv.__file__, flag], capture_output=True, text=True)
        assert r.returncode == 0 and "Usage: build_grader_view.py" in r.stdout, (flag, r.returncode, r.stderr)
