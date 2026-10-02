"""Tests for library.py: run the script via subprocess against a temp JEVALUATE_LIBRARY."""
import os
import pathlib
import re
import shutil
import subprocess
import sys

import hashlib
import json
import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parent))
SCRIPT = pathlib.Path(__file__).parent / "library.py"
REAL_RATINGS_BACKUP = pathlib.Path(
    os.environ.get("JEVALUATE_REAL_BACKUP", "/nonexistent")
    
)


def run(lib_dir, *args):
    env = dict(os.environ)
    env["JEVALUATE_LIBRARY"] = str(lib_dir)
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True, env=env,
    )


FACTS_BLOCK = "\n".join(f"- F{n} check{n} — yes. evidence:{n}" for n in range(1, 24))


def with_steps(r):
    """Write the step log a rater's step.py calls would leave, matching the rating's routing fields."""
    r = pathlib.Path(r); d = {}
    for line in r.read_text().split("---\n")[1].splitlines():
        if ":" in line:
            k, v = line.split(":", 1); d[k.strip()] = v.split("#")[0].strip()
    import library as _lib
    d["top_stakes"] = _lib.derive_top_stakes(d, r.read_text()) or ""
    d["kind"] = _lib.rubric_text.KIND_OF.get(d.get("project_type"), "")
    fp = hashlib.sha1("|".join(d.get(k, "") for k in ("project_type", "kind", "verdict_1_code", "top_stakes")).encode()).hexdigest()
    steps = ["routing", "compare", "verdict"] if d.get("verdict_1_code") in ("1a", "1b", "1c", "1r", "1t") else ["routing", "facts", "scores", "compare", "verdict"]
    pathlib.Path(str(r) + ".steps.json").write_text(json.dumps([{"step": s, "time": f"2026-09-29T10:0{i}", "routing": fp} for i, s in enumerate(steps)]))
    return r


EV_CALL_SRC = "import os\n\nfrom typesafe import TypeSafeClient\nclient = TypeSafeClient()\nr = client.noul('q')\n\n\n\nx = 1\n"
EV_NO_CALL_SRC = "import os\n\nx = 1\n"
DECISION_LOW = "- flag unclear commit | Noul | low | acts at src/x.py:9 | shows the flag to the author"

def make_rating(path, project, owner, url, rated, commit="abc123def456789", verdict=4, project_type="workflow",
                 scores="execution: 3, fit: 3, coverage: 3, evidence: 2", via="direct",
                 depth="full", rubric="2026-09-29", drop=(), coverage=None, fact_lines=None,
                 core_fixes=None, summary="Test fixture rating for library tests.", decisions=None, auto_evidence=True):
    fm = {"project": project, "url": url, "owner": owner, "rated": rated, "rubric": rubric,
          "commit": commit, "depth": depth, "lineage": "new",
          "stages": "[data-prep, question-state, execution, decision]", "closes_loop": "none",
          "verdict": verdict, "scores": "{" + scores + "}", "via": via, "project_type": project_type,
          "rater": "claude-sonnet-5-5", "effort": "medium", "kind": "uses", "verdict_1_code": "none",
          "citation": "none", "top_stakes": "low"}
    for k in drop:
        fm.pop(k, None)
    fl = {n: f"- F{n} check{n} — yes. evidence:{n}" for n in range(0, 24)}
    fl[0] = "- F0 Calls hosted Jev -- yes. Builds the client and calls it (src/x.py:5)"
    fl[13] = "- F13 check13 -- n.a. No high or very high Choice"
    fl.update(fact_lines or {})
    text = "---\n" + "\n".join(f"{k}: {v}" for k, v in fm.items()) + "\n---\n"
    if decisions is None: decisions = [DECISION_LOW]
    text += f"## Summary\n{summary}\n"
    if decisions: text += "## Decisions\n" + "\n".join(decisions) + "\n"
    text += "## Facts (with evidence)\n" + "\n".join(fl[n] for n in sorted(fl)) + "\n"
    if coverage is not None:
        text += "## Coverage\n" + coverage + "\n"
    text += "## Verdict and reasoning\nTest fixture.\n"
    if core_fixes is not None:
        text += "## Core fixes\n" + core_fixes + "\n"
    path.write_text(text)
    if auto_evidence:  # check refuses an F0 yes or no it cannot check against code, so give the rating the code its F0 line describes
        ed = path.parent / f"{path.stem}-evidence" / "files"; ed.mkdir(parents=True, exist_ok=True)
        (ed / "src__x.py").write_text(EV_CALL_SRC if re.search(r"F0[^\n]*?(--|\u2014|:)\s*yes", fl[0]) else EV_NO_CALL_SRC)
    return with_steps(path)


def make_evidence(tmp_path, files=("a.py", "b.py"), base=True):
    ev = tmp_path / "ev"; ev.mkdir(exist_ok=True)
    if base: (ev / "files").mkdir(exist_ok=True); (ev / "files" / "src__x.py").write_text(EV_CALL_SRC)
    rows = "\n".join(f"| {f} | 10 | 1 | 0 | 0 |" for f in files)
    (ev / "manifest.md").write_text(
        "# Coverage manifest\n\n| file | chars | jev | decision | eval |\n|---|---|---|---|---|\n" + rows + "\n")
    return ev


@pytest.fixture
def lib(tmp_path):
    return tmp_path / "lib"


def test_add_same_day_gives_dash2(lib, tmp_path):
    r1 = make_rating(tmp_path / "r1.md", "Proj", "owner", "https://github.com/owner/proj", "2026-09-28", commit="a" * 12)
    r2 = make_rating(tmp_path / "r2.md", "Proj", "owner", "https://github.com/owner/proj", "2026-09-28", commit="b" * 12)
    p1 = run(lib, "add", str(r1))
    assert p1.returncode == 0, p1.stdout + p1.stderr
    p2 = run(lib, "add", str(r2))
    assert p2.returncode == 0, p2.stdout + p2.stderr
    projdir = lib / "projects" / "owner__proj"
    assert (projdir / "2026-09-28.md").exists()
    assert (projdir / "2026-09-28-2.md").exists()


def test_slug_github_keeps_case(lib, tmp_path):
    r = make_rating(tmp_path / "r.md", "JevTools", "RileyCarney", "https://github.com/RileyCarney/JevTools", "2026-09-28")
    p = run(lib, "add", str(r))
    assert p.returncode == 0, p.stdout + p.stderr
    assert (lib / "projects" / "RileyCarney__JevTools" / "2026-09-28.md").exists()


def test_slug_huggingface(lib, tmp_path):
    r = make_rating(tmp_path / "r.md", "Jev-Omni", "akhilaaa3", "https://huggingface.co/akhilaaa3/Jev-Omni", "2026-09-28")
    p = run(lib, "add", str(r))
    assert p.returncode == 0, p.stdout + p.stderr
    assert (lib / "projects" / "hf__akhilaaa3__Jev-Omni" / "2026-09-28.md").exists()


def test_slug_other_site_with_path(lib, tmp_path):
    r = make_rating(tmp_path / "r.md", "AskJevs", "askjevs", "https://askjevs.site/app/play", "2026-09-28")
    p = run(lib, "add", str(r))
    assert p.returncode == 0, p.stdout + p.stderr
    assert (lib / "projects" / "site__askjevs.site__app__play" / "2026-09-28.md").exists()


def test_slug_other_site_no_path(lib, tmp_path):
    r = make_rating(tmp_path / "r.md", "AskJevs", "askjevs", "https://askjevs.site/", "2026-09-28")
    p = run(lib, "add", str(r))
    assert p.returncode == 0, p.stdout + p.stderr
    assert (lib / "projects" / "site__askjevs.site" / "2026-09-28.md").exists()


@pytest.mark.skipif(not REAL_RATINGS_BACKUP.exists(), reason="real ratings backup not present")
def test_migrate_keeps_all_19_and_orders_jevlint(lib, tmp_path):
    (lib / "ratings").mkdir(parents=True)
    for f in REAL_RATINGS_BACKUP.glob("*.md"):
        shutil.copy(f, lib / "ratings" / f.name)

    p = run(lib, "migrate")
    assert p.returncode == 0, p.stdout + p.stderr

    all_files = list(lib.glob("projects/*/*.md"))
    assert len(all_files) == 19

    index_text = (lib / "index.md").read_text()
    row_count = sum(1 for line in index_text.splitlines() if line.startswith("| 20"))
    assert row_count == 19

    assert not (lib / "ratings").exists()

    jevlint_dir = lib / "projects" / "Fox-Islam__jevlint"
    d1 = (jevlint_dir / "2026-09-27.md").read_text()
    d2 = (jevlint_dir / "2026-09-27-2.md").read_text()
    d3 = (jevlint_dir / "2026-09-27-3.md").read_text()
    orig1 = (REAL_RATINGS_BACKUP / "2026-09-27-fox-islam-jevlint.md").read_text()
    orig2 = (REAL_RATINGS_BACKUP / "2026-09-27-fox-islam-jevlint-2.md").read_text()
    orig3 = (REAL_RATINGS_BACKUP / "2026-09-27-fox-islam-jevlint-3.md").read_text()
    assert d1 == orig1
    assert d2 == orig2
    assert d3 == orig3


@pytest.mark.skipif(not REAL_RATINGS_BACKUP.exists(), reason="real ratings backup not present")
def test_migrate_is_idempotent(lib, tmp_path):
    (lib / "ratings").mkdir(parents=True)
    for f in REAL_RATINGS_BACKUP.glob("*.md"):
        shutil.copy(f, lib / "ratings" / f.name)
    run(lib, "migrate")
    p2 = run(lib, "migrate")
    assert p2.returncode == 0, p2.stdout + p2.stderr
    all_files = list(lib.glob("projects/*/*.md"))
    assert len(all_files) == 19


def test_similar_exclude_still_excludes(lib, tmp_path):
    r1 = make_rating(tmp_path / "r1.md", "ProjA", "ownera", "https://github.com/ownera/proja", "2026-09-28")
    r2 = make_rating(tmp_path / "r2.md", "ProjB", "ownerb", "https://github.com/ownerb/projb", "2026-09-28")
    run(lib, "add", str(r1))
    run(lib, "add", str(r2))
    p = run(lib, "similar", "--stage", "execution", "--exclude", "ownera/ProjA")
    assert p.returncode == 0, p.stdout + p.stderr
    assert "ownera" not in p.stdout
    assert "ProjB" in p.stdout or "ownerb" in p.stdout


def test_blind_uses_projects_layout(lib, tmp_path):
    r1 = make_rating(tmp_path / "r1.md", "ProjA", "ownera", "https://github.com/ownera/proja", "2026-09-28")
    r2 = make_rating(tmp_path / "r2.md", "ProjB", "ownerb", "https://github.com/ownerb/projb", "2026-09-28")
    run(lib, "add", str(r1))
    run(lib, "add", str(r2))
    out = tmp_path / "blind-out"
    p = run(lib, "blind", "--exclude", "ownera/proja", "--out", str(out))
    assert p.returncode == 0, p.stdout + p.stderr
    assert (out / "projects" / "ownerb__projb" / "2026-09-28.md").exists()
    assert not (out / "projects" / "ownera__proja").exists()


def test_index_ignores_evidence_folders(lib, tmp_path):
    r1 = make_rating(tmp_path / "r1.md", "ProjA", "ownera", "https://github.com/ownera/proja", "2026-09-28")
    run(lib, "add", str(r1))
    evdir = lib / "projects" / "ownera__proja" / "2026-09-28-evidence"
    evdir.mkdir(parents=True, exist_ok=True)
    (evdir / "manifest.md").write_text("# not a rating\n")
    p = run(lib, "index")
    assert p.returncode == 0, p.stdout + p.stderr
    assert "index: 1 ratings" in p.stdout


def test_list_add_writes_dated_and_latest(lib, tmp_path):
    tsv = tmp_path / "entries.tsv"
    tsv.write_text("section\turl\nSDKs\thttps://github.com/a/b\n")
    p = run(lib, "list-add", "awesome-jev", str(tsv))
    assert p.returncode == 0, p.stdout + p.stderr
    out_lines = p.stdout.strip().splitlines()
    assert len(out_lines) == 2
    dated, latest = out_lines
    assert pathlib.Path(dated).exists()
    assert pathlib.Path(latest).exists()
    assert pathlib.Path(latest).name == "entries.tsv"
    assert pathlib.Path(dated).read_text() == tsv.read_text()


# ---- check: frontmatter, coverage, docs links ----

@pytest.mark.parametrize("field", ["project_type", "rater", "effort", "via"])
def test_check_refuses_missing_frontmatter_field(tmp_path, lib, field):
    r = make_rating(tmp_path / "r.md", "P", "o", "https://github.com/o/p", "2026-09-28", drop=(field,))
    p = run(lib, "check", str(r))
    assert p.returncode == 1
    assert f"missing front-matter field: {field}" in p.stdout


def test_check_refuses_coverage_omitting_manifest_file(tmp_path, lib):
    ev = make_evidence(tmp_path)
    (tmp_path / "r-evidence").symlink_to(ev)
    r = make_rating(tmp_path / "r.md", "P", "o", "https://github.com/o/p", "2026-09-28",
                    depth="extract", coverage="- a.py: read")
    p = run(lib, "check", str(r))
    assert p.returncode == 1
    assert "b.py" in p.stdout and "Coverage" in p.stdout


def test_check_accepts_coverage_listing_every_manifest_file(tmp_path, lib):
    ev = make_evidence(tmp_path)
    (tmp_path / "r-evidence").symlink_to(ev)
    r = make_rating(tmp_path / "r.md", "P", "o", "https://github.com/o/p", "2026-09-28",
                    coverage="- a.py: read\n- b.py: read")
    p = run(lib, "check", str(r))
    assert p.returncode == 0, p.stdout + p.stderr


def test_check_skipped_line_counts_as_listed_when_not_full(tmp_path, lib):
    ev = make_evidence(tmp_path)
    (tmp_path / "r-evidence").symlink_to(ev)
    r = make_rating(tmp_path / "r.md", "P", "o", "https://github.com/o/p", "2026-09-28",
                    depth="extract", coverage="- a.py: read\nskipped: b.py is a lockfile")
    p = run(lib, "check", str(r))
    assert p.returncode == 0, p.stdout + p.stderr


def test_check_skipped_line_refused_when_depth_full(tmp_path, lib):
    ev = make_evidence(tmp_path)
    (tmp_path / "r-evidence").symlink_to(ev)
    r = make_rating(tmp_path / "r.md", "P", "o", "https://github.com/o/p", "2026-09-28",
                    depth="full", coverage="- a.py: read\nskipped: b.py is a lockfile")
    p = run(lib, "check", str(r))
    assert p.returncode == 1
    assert "full" in p.stdout


def test_check_no_manifest_is_a_warning_not_a_refusal(tmp_path, lib):
    r = make_rating(tmp_path / "r.md", "P", "o", "https://github.com/o/p", "2026-09-28", coverage="- a.py: read")
    p = run(lib, "check", str(r))
    assert p.returncode == 0, p.stdout + p.stderr
    assert "manifest" in p.stderr.lower()


@pytest.mark.parametrize("word", ["read selectively", "skimmed the tests", "partial read of src", "skipped the docs"])
def test_check_refuses_full_depth_with_partial_coverage_words(tmp_path, lib, word):
    r = make_rating(tmp_path / "r.md", "P", "o", "https://github.com/o/p", "2026-09-28",
                    depth="full", coverage=f"Files were {word}.")
    p = run(lib, "check", str(r))
    assert p.returncode == 1
    assert "full" in p.stdout


def test_check_full_depth_allows_none_skipped(tmp_path, lib):
    r = make_rating(tmp_path / "r.md", "P", "o", "https://github.com/o/p", "2026-09-28",
                    depth="full", coverage="All 5 files read; none skipped.")
    p = run(lib, "check", str(r))
    assert p.returncode == 0, p.stdout + p.stderr


NO_F8 = {8: "- F8 options overlap — no. options a and b overlap (x.py:10)"}


def test_check_refuses_no_fact_without_docs_link(tmp_path, lib):
    r = make_rating(tmp_path / "r.md", "P", "o", "https://github.com/o/p", "2026-09-28",
                    verdict=3, fact_lines=NO_F8, core_fixes="1. **F8**, make options exclusive.")
    p = run(lib, "check", str(r))
    assert p.returncode == 1
    assert "F8" in p.stdout and "docs" in p.stdout.lower()


def test_check_accepts_docs_link_on_fact_line(tmp_path, lib):
    r = make_rating(tmp_path / "r.md", "P", "o", "https://github.com/o/p", "2026-09-28", verdict=3,
                    fact_lines={8: NO_F8[8] + " https://docs.typesafe.ai/primitives.md"})
    p = run(lib, "check", str(r))
    assert p.returncode == 0, p.stdout + p.stderr


def test_check_accepts_doc_slug_in_core_fixes_entry(tmp_path, lib):
    r = make_rating(tmp_path / "r.md", "P", "o", "https://github.com/o/p", "2026-09-28", verdict=3,
                    fact_lines=NO_F8, core_fixes="1. **F8**, make options exclusive. `primitives`, `cookbooks/x`.")
    p = run(lib, "check", str(r))
    assert p.returncode == 0, p.stdout + p.stderr


def test_check_core_fixes_link_for_other_fact_does_not_count(tmp_path, lib):
    r = make_rating(tmp_path / "r.md", "P", "o", "https://github.com/o/p", "2026-09-28", verdict=3,
                    fact_lines=NO_F8, core_fixes="1. **F9**, add other. `primitives`.")
    p = run(lib, "check", str(r))
    assert p.returncode == 1


# ---- add flags ----

def test_add_link_docs_fills_missing_link_from_catalog(tmp_path, lib):
    r = make_rating(tmp_path / "r.md", "P", "o", "https://github.com/o/p", "2026-09-28",
                    verdict=3, fact_lines=NO_F8)
    plain = run(lib, "add", str(r))
    assert plain.returncode != 0
    p = run(lib, "add", "--link-docs", str(r))
    assert p.returncode == 0, p.stdout + p.stderr
    saved = (lib / "projects" / "o__p" / "2026-09-28.md").read_text()
    assert "https://docs.typesafe.ai/primitives.md" in saved.split("F8 options overlap")[1].splitlines()[0]


def test_add_evidence_copies_folder_beside_rating(tmp_path, lib):
    ev = make_evidence(tmp_path)
    r = make_rating(tmp_path / "r.md", "P", "o", "https://github.com/o/p", "2026-09-28",
                    coverage="- a.py: read\n- b.py: read")
    p = run(lib, "add", "--evidence", str(ev), str(r))
    assert p.returncode == 0, p.stdout + p.stderr
    assert (lib / "projects" / "o__p" / "2026-09-28-evidence" / "manifest.md").exists()


def test_add_evidence_manifest_is_checked_against_coverage(tmp_path, lib):
    ev = make_evidence(tmp_path)
    r = make_rating(tmp_path / "r.md", "P", "o", "https://github.com/o/p", "2026-09-28", coverage="- a.py: read")
    p = run(lib, "add", "--evidence", str(ev), str(r))
    assert p.returncode != 0
    assert not (lib / "projects" / "o__p" / "2026-09-28.md").exists()


def test_add_supersedes_removes_old_file_after_writing_new(tmp_path, lib):
    r1 = make_rating(tmp_path / "r1.md", "P", "o", "https://github.com/o/p", "2026-09-28", commit="a" * 12)
    run(lib, "add", str(r1))
    old = lib / "projects" / "o__p" / "2026-09-28.md"
    r2 = make_rating(tmp_path / "r2.md", "P", "o", "https://github.com/o/p", "2026-09-28", commit="b" * 12)
    p = run(lib, "add", "--supersedes", str(old), str(r2))
    assert p.returncode == 0, p.stdout + p.stderr
    remaining = list((lib / "projects" / "o__p").glob("*.md"))
    assert len(remaining) == 1
    assert "b" * 12 in remaining[0].read_text()
    assert "index: 1 ratings" in p.stdout


def test_add_supersedes_keeps_old_file_when_new_is_refused(tmp_path, lib):
    r1 = make_rating(tmp_path / "r1.md", "P", "o", "https://github.com/o/p", "2026-09-28")
    run(lib, "add", str(r1))
    old = lib / "projects" / "o__p" / "2026-09-28.md"
    bad = make_rating(tmp_path / "bad.md", "P", "o", "https://github.com/o/p", "2026-09-28", drop=("rater",))
    p = run(lib, "add", "--supersedes", str(old), str(bad))
    assert p.returncode != 0
    assert old.exists()


# ---- stale ----

def test_stale_lists_only_older_rubric(tmp_path, lib):
    r1 = make_rating(tmp_path / "r1.md", "Old", "o", "https://github.com/o/old", "2026-09-20")
    r2 = make_rating(tmp_path / "r2.md", "New", "o", "https://github.com/o/new", "2026-09-28")
    run(lib, "add", str(r2))
    d = lib / "projects" / "o__old"; d.mkdir(parents=True)
    make_rating(d / "2026-09-20.md", "Old", "o", "https://github.com/o/old", "2026-09-20", rubric="2026-09-01")
    p = run(lib, "stale")
    assert p.returncode == 0, p.stdout + p.stderr
    assert "o__old" in p.stdout and "2026-09-01" in p.stdout
    assert "o__new" not in p.stdout


# ---- export ----

def seed_export(tmp_path, lib):
    r = make_rating(tmp_path / "r.md", "Proj", "o", "https://github.com/o/proj", "2026-09-28",
                    commit="c" * 40, verdict=3, summary="Uses Jev for triage; one overlap problem.",
                    fact_lines={8: NO_F8[8] + " https://docs.typesafe.ai/primitives.md"},
                    core_fixes="1. **F8**, make options exclusive. `primitives`.")
    assert run(lib, "add", str(r)).returncode == 0


def test_export_writes_page_readme_license_and_index(tmp_path, lib):
    seed_export(tmp_path, lib)
    out = tmp_path / "out"
    p = run(lib, "export", str(out))
    assert p.returncode == 0, p.stdout + p.stderr
    page = (out / "o__proj.md").read_text()
    assert "Use with a fix" in page and "Uses Jev for triage" in page
    assert "x.py:10" in page and "https://docs.typesafe.ai/primitives.md" in page
    assert "c" * 40 in page
    assert "not tested against it" in page and "make options exclusive" in page
    assert "F1 check1" not in page
    assert "Earlier rubric" not in page
    readme = (out / "README.md").read_text()
    template = (SCRIPT.parent.parent / "ratings-template" / "README.md").read_text()
    assert readme.startswith(template)
    assert "| o/proj" in readme or "o__proj" in readme
    assert (out / "LICENSE").read_text() == (SCRIPT.parent.parent / "ratings-template" / "LICENSE").read_text()


def test_export_takes_latest_rating_per_project(tmp_path, lib):
    seed_export(tmp_path, lib)
    r = make_rating(tmp_path / "r2.md", "Proj", "o", "https://github.com/o/proj", "2026-09-29",
                    summary="Second round summary.")
    run(lib, "add", str(r))
    out = tmp_path / "out"
    assert run(lib, "export", str(out)).returncode == 0
    assert "Second round summary." in (out / "o__proj.md").read_text()
    assert len(list(out.glob("o__proj*.md"))) == 1


def test_export_tags_earlier_rubric(tmp_path, lib):
    d = lib / "projects" / "o__old"; d.mkdir(parents=True)
    make_rating(d / "2026-09-20.md", "Old", "o", "https://github.com/o/old", "2026-09-20", rubric="2026-09-01")
    out = tmp_path / "out"
    assert run(lib, "export", str(out)).returncode == 0
    assert "earlier rubric (2026-09-01)" in (out / "o__old.md").read_text()


def test_export_refuses_private_term(tmp_path, lib):
    r = make_rating(tmp_path / "r.md", "Proj", "o", "https://github.com/o/proj", "2026-09-28",
                    summary="PRIVATEMARKER note that must not ship.")
    run(lib, "add", str(r))
    (lib / "private-terms.txt").write_text("# comment\nPRIVATEMARKER\n")
    out = tmp_path / "out"
    p = run(lib, "export", str(out))
    assert p.returncode != 0
    assert "o__proj" in p.stderr + p.stdout and "PRIVATEMARKER" in p.stderr + p.stdout
    assert not (out / "o__proj.md").exists()


# ---- migrate-fields ----

def test_migrate_fields_fills_only_missing_and_is_idempotent(tmp_path, lib):
    d = lib / "projects" / "o__p"; d.mkdir(parents=True)
    f = make_rating(d / "2026-09-28.md", "P", "o", "https://github.com/o/p", "2026-09-28",
                    drop=("rater", "effort", "project_type", "via"))
    g = make_rating(d / "2026-09-29.md", "P", "o", "https://github.com/o/p", "2026-09-29", via="list:awesome-jev")
    p = run(lib, "migrate-fields")
    assert p.returncode == 0, p.stdout + p.stderr
    t = f.read_text()
    for line in ("rater: unknown", "effort: medium", "project_type: unrecorded", "via: unrecorded"):
        assert line in t
    assert t.startswith("---\n") and "\n---\n## Summary" in t
    assert "via: list:awesome-jev" in g.read_text() and "rater: claude-sonnet-5-5" in g.read_text()
    before = f.read_text(), g.read_text()
    run(lib, "migrate-fields")
    assert (f.read_text(), g.read_text()) == before


def test_fill_docs_existing_only_where_single_page(tmp_path, lib):
    d = lib / "projects" / "o__p"; d.mkdir(parents=True)
    f = make_rating(d / "2026-09-28.md", "P", "o", "https://github.com/o/p", "2026-09-28", verdict=3,
                    fact_lines={1: "- F1 atomic — no. x.py:3",
                                2: "- F2 primitive — no. y.py:4"})
    p = run(lib, "fill-docs")
    assert p.returncode == 0, p.stdout + p.stderr
    t = f.read_text()
    assert "concepts/how-to-build-with-system-one" in t.split("F1 atomic")[1].splitlines()[0]
    assert "docs.typesafe.ai" not in t.split("F2 primitive")[1].splitlines()[0]
    assert "F2" in p.stdout


def test_export_refuses_private_term_anywhere_in_source_rating(tmp_path, lib):
    r = make_rating(tmp_path / "r.md", "Proj", "o", "https://github.com/o/proj", "2026-09-28")
    r.write_text(r.read_text().replace("Test fixture.\n", "PRIVATEMARKER note.\n"))
    run(lib, "add", str(r))
    (lib / "private-terms.txt").write_text("PRIVATEMARKER\n")
    out = tmp_path / "out"
    p = run(lib, "export", str(out))
    assert p.returncode != 0
    assert "2026-09-28.md" in p.stderr and "PRIVATEMARKER" in p.stderr
    assert not out.exists() or not list(out.glob("*.md"))


def test_export_skips_quick_ratings_and_falls_back_to_latest_full(tmp_path, lib):
    d = lib / "projects" / "o__q"; d.mkdir(parents=True)
    make_rating(d / "2026-09-20.md", "Q", "o", "https://github.com/o/q", "2026-09-20", summary="Full read summary.")
    make_rating(d / "2026-09-28.md", "Q", "o", "https://github.com/o/q", "2026-09-28", depth="extract", summary="Quick read summary.")
    e = lib / "projects" / "o__onlyquick"; e.mkdir(parents=True)
    make_rating(e / "2026-09-28.md", "OQ", "o", "https://github.com/o/onlyquick", "2026-09-28", depth="extract")
    out = tmp_path / "out"
    assert run(lib, "export", str(out)).returncode == 0
    assert "Full read summary." in (out / "o__q.md").read_text()
    assert not (out / "o__onlyquick.md").exists()
    assert "o__onlyquick" not in (out / "README.md").read_text()


def test_export_newer_date_beats_numbered_same_day_file(tmp_path, lib):
    d = lib / "projects" / "o__s"; d.mkdir(parents=True)
    make_rating(d / "2026-09-28-3.md", "S", "o", "https://github.com/o/s", "2026-09-28", summary="Old numbered summary.")
    make_rating(d / "2026-09-30.md", "S", "o", "https://github.com/o/s", "2026-09-30", summary="Newer date summary.")
    out = tmp_path / "out"
    assert run(lib, "export", str(out)).returncode == 0
    assert "Newer date summary." in (out / "o__s.md").read_text()


def test_export_publishes_approved_scope_over_older_full(tmp_path, lib):
    d = lib / "projects" / "o__sc"; d.mkdir(parents=True)
    make_rating(d / "2026-09-20.md", "SC", "o", "https://github.com/o/sc", "2026-09-20", summary="Old full summary.")
    make_rating(d / "2026-09-30.md", "SC", "o", "https://github.com/o/sc", "2026-09-30", depth="extract", summary="Scoped summary.",
                coverage="- README.md -- read\n- src/big.py -- skipped: scoped")
    out = tmp_path / "out"
    assert run(lib, "export", str(out)).returncode == 0
    assert "Scoped summary." in (out / "o__sc.md").read_text()


def test_latest_rating_for_prefers_newer_date_over_numbered_file(tmp_path, lib):
    d = lib / "projects" / "o__m"; d.mkdir(parents=True)
    for name, rated in (("2026-09-28-3", "2026-09-28"), ("2026-09-30", "2026-09-30")):
        make_rating(d / f"{name}.md", "M", "o", "https://github.com/o/m", rated)
    sys.path.insert(0, str(pathlib.Path(__file__).parent))
    import importlib, library
    importlib.reload(library); library.PROJ = lib / "projects"
    assert library.latest_rating_for("https://github.com/o/m").name == "2026-09-30.md"


def test_export_resolves_bare_file_names_from_coverage(tmp_path, lib):
    d = lib / "projects" / "o__bare"; d.mkdir(parents=True)
    make_rating(d / "2026-09-30.md", "Bare", "o", "https://github.com/o/bare", "2026-09-30",
                fact_lines={1: "- F1 Atomic questions -- no. Broad check (`deep/dir/core.verification.toml:6`, `core.verification.toml:9`)"},
                coverage="- deep/dir/core.verification.toml -- read\n- jev_x/questions.py -- read (fetched with --also; not in the manifest)\n- big.py -- skipped: scoped")
    out = tmp_path / "out"; assert run(lib, "export", str(out)).returncode == 0
    full = (out / "full" / "o__bare.md").read_text()
    assert "blob/abc123def456789/deep/dir/core.verification.toml#L9" in full
    assert "blob/abc123def456789/core.verification.toml" not in full
    assert "--also" not in full and "fetched separately" in full
    assert "Files read (2; 1 skipped)" in full


def test_export_drops_placeholder_scores(tmp_path, lib):
    d = lib / "projects" / "o__tbd"; d.mkdir(parents=True)
    r = make_rating(d / "2026-09-30.md", "Tbd", "o", "https://github.com/o/tbd", "2026-09-30")
    (d / "2026-09-30.md").write_text((d / "2026-09-30.md").read_text().replace("## Verdict and reasoning", "## Scores\nTBD\n## Verdict and reasoning"))
    out = tmp_path / "out"; assert run(lib, "export", str(out)).returncode == 0
    full = (out / "full" / "o__tbd.md").read_text()
    assert "TBD" not in full and "## Scores" not in full


def test_export_shows_unscored_codes_as_na_and_drops_adjudication_notes(tmp_path, lib):
    d = lib / "projects" / "o__rep"; d.mkdir(parents=True)
    make_rating(d / "2026-09-30.md", "Rep", "o", "https://github.com/o/rep", "2026-09-30", verdict=1, project_type="jev-replacement")
    f = d / "2026-09-30.md"; f.write_text(f.read_text().replace("verdict_1_code: none", "verdict_1_code: 1r"))
    e = lib / "projects" / "o__fm"; e.mkdir(parents=True)
    make_rating(e / "2026-09-30.md", "Fm", "o", "https://github.com/o/fm", "2026-09-30", verdict=1)
    g = e / "2026-09-30.md"; g.write_text(g.read_text().replace("verdict_1_code: none", "verdict_1_code: 1a").replace("Test fixture.", "Test fixture.\nAdjudicated 2026-10-01: internal note."))
    out = tmp_path / "out"; assert run(lib, "export", str(out)).returncode == 0
    readme = (out / "README.md").read_text()
    assert "**n.a. (replaces Jev, not yet rated)**" in readme and "**1 Replaces" not in readme
    assert "**1 False marketing: Jev in name only**" in readme
    assert readme.index("o__fm") < readme.index("o__rep")
    assert "Not rated yet: replaces Jev" in (out / "o__rep.md").read_text()
    assert "Adjudicated" not in (out / "full" / "o__fm.md").read_text()


def test_add_numbers_after_highest_same_day_and_keeps_evidence_separate(tmp_path, lib):
    d = lib / "projects" / "o__n"; d.mkdir(parents=True)
    make_rating(d / "2026-09-28-2.md", "N", "o", "https://github.com/o/n", "2026-09-28")
    old_ev = d / "2026-09-28-evidence"; old_ev.mkdir(); (old_ev / "manifest.md").write_text("OLD\n")
    ev = tmp_path / "ev"; (ev / "files").mkdir(parents=True); (ev / "manifest.md").write_text("# m\n"); (ev / "files" / "src__x.py").write_text(EV_CALL_SRC)
    r = make_rating(tmp_path / "r.md", "N", "o", "https://github.com/o/n", "2026-09-28")
    p = run(lib, "add", "--evidence", str(ev), str(r))
    assert p.returncode == 0, p.stdout + p.stderr
    assert (d / "2026-09-28-3.md").exists() and not (d / "2026-09-28.md").exists()
    assert (d / "2026-09-28-3-evidence" / "manifest.md").read_text() == "# m\n"
    assert (old_ev / "manifest.md").read_text() == "OLD\n"


@pytest.mark.parametrize("f0,verdict,ok", [
    ("no", 3, False), ("unknown", 4, False), ("no", 1, True), ("unknown", "cant-rate", True), ("yes", 4, True)])
def test_check_gates_verdict_on_f0(tmp_path, lib, f0, verdict, ok):
    r = make_rating(tmp_path / "r.md", "P", "o", "https://github.com/o/p", "2026-09-28", verdict=verdict,
                    fact_lines={0: f"- F0 Calls hosted Jev -- {f0}. src/x.py:5; no file would answer it. https://docs.typesafe.ai/introduction/quickstart.md"})
    if verdict == 1:  # under the 2026-09-29 rubric, F0 no with verdict 1 is a mention-only routed to 1b
        _fm(r, project_type="jev-mention-only", kind="mentions", verdict_1_code="1b", top_stakes="n.a.",
            type_best_match="other: imitation", code_functionality="imitates the API", replaces_jev="fixed values", intended_call="none")
    p = run(lib, "check", str(r))
    assert (p.returncode == 0) == ok, p.stdout + p.stderr
    if not ok: assert "F0" in p.stdout + p.stderr and "verdict" in (p.stdout + p.stderr).lower()


def test_check_requires_f0_under_current_rubric(tmp_path, lib):
    r = make_rating(tmp_path / "r.md", "P", "o", "https://github.com/o/p", "2026-09-28")
    text = r.read_text().replace("- F0 Calls hosted Jev -- yes. Builds the client and calls it (src/x.py:5)\n", ""); r.write_text(text)
    p = run(lib, "check", str(r))
    assert p.returncode != 0 and "F0" in p.stdout + p.stderr


def seed_shape(tmp_path, lib, **kw):
    r = make_rating(tmp_path / "s.md", "Proj", "o", "https://github.com/o/proj", "2026-09-28",
                    commit="c" * 40, verdict=3,
                    summary="Sends reviews to Jev. Batches well. Two options overlap.",
                    fact_lines={8: NO_F8[8] + " https://docs.typesafe.ai/primitives.md",
                                12: "- F12 Model pinned (fix-only) — no. Uses jev-latest (x.py:3). `models`"},
                    core_fixes="1. **F8**, make options exclusive. `primitives`.\n2. **F12**, pin the model. `models`.", **kw)
    t = r.read_text().replace("---\n## Summary", "why: One compound option set holds it back.\n---\n## Summary", 1)
    r.write_text(t)
    assert run(lib, "add", str(r)).returncode == 0


def test_export_index_has_type_why_and_stale_mark(tmp_path, lib):
    seed_shape(tmp_path, lib)
    d = lib / "projects" / "o__old"; d.mkdir(parents=True)
    make_rating(d / "2026-09-20.md", "Old", "o", "https://github.com/o/old", "2026-09-20", rubric="2026-09-01",
                summary="First sentence is the fallback. Second one is not.")
    out = tmp_path / "out"; assert run(lib, "export", str(out)).returncode == 0
    readme = (out / "README.md").read_text()
    assert "| Project | Type | Verdict | Why | Rated |" in readme
    assert "One compound option set holds it back." in readme
    assert "First sentence is the fallback." in readme and "Second one is not" not in readme
    assert "2026-09-20 †" in readme and "earlier rubric" in readme.lower()


def test_export_detail_page_is_one_screen_card(tmp_path, lib):
    seed_shape(tmp_path, lib)
    out = tmp_path / "out"; assert run(lib, "export", str(out)).returncode == 0
    page = (out / "o__proj.md").read_text()
    assert "### Verdict 3: Use with a fix" in page
    assert "Execution ●●●" in page and "Evidence ●●○" in page
    assert "- Batches well." in page
    hold = page.split("## What holds it back")[1].split("##")[0]
    assert "options a and b overlap" in hold and "jev-latest" not in hold
    assert "Minor" in page and "Model pinned" in page.split("Minor")[1]
    assert "full/o__proj.md" in page and "F1 check1" not in page


def test_export_full_page_collapses_passes_and_links_lines(tmp_path, lib):
    seed_shape(tmp_path, lib)
    out = tmp_path / "out"; assert run(lib, "export", str(out)).returncode == 0
    full = (out / "full" / "o__proj.md").read_text()
    before, _, after = full.partition("<details>")
    assert "options a and b overlap" in before and "check1" not in before
    assert "check1" in after
    assert "https://github.com/o/proj/blob/" + "c" * 40 + "/x.py#L10" in full
    assert "https://docs.typesafe.ai/primitives" in full


def test_export_verdict_one_uses_the_rating_label(tmp_path, lib):
    r = make_rating(tmp_path / "v1.md", "Imit", "o", "https://github.com/o/imit", "2026-09-28", verdict=1,
                    scores="execution: 0, fit: 0, coverage: 0, evidence: 0",
                    fact_lines={0: "- F0 Calls hosted Jev — no. Only an imitation of the API; no file would answer it. https://docs.typesafe.ai/introduction/quickstart.md"})
    r.write_text(r.read_text().replace("Test fixture.", "Not a Jev integration: it imitates Jev and says so."))
    _fm(r, project_type="jev-mention-only", kind="mentions", verdict_1_code="1b", top_stakes="n.a.",
            type_best_match="other: imitation", code_functionality="imitates the API", replaces_jev="fixed values", intended_call="none")
    assert run(lib, "add", str(r)).returncode == 0, "fixture"
    out = tmp_path / "out"; assert run(lib, "export", str(out)).returncode == 0
    assert "Verdict 1: Not a Jev integration" in (out / "o__imit.md").read_text()


def test_old_rubric_guide_keeps_1g_label_and_g_facts(tmp_path, lib):
    d = lib / "projects" / "o__g"; d.mkdir(parents=True)  # an old rating already in the library
    r = make_rating(d / "2026-09-28.md", "G", "o", "https://github.com/o/g", "2026-09-28", verdict=1, project_type="guide", rubric="2026-09-28b",
                    scores="execution: 1, fit: 1, coverage: 1, evidence: 0",
                    fact_lines={0: "- F0 Calls hosted Jev — n.a. A guide; makes no calls.",
                                24: "- G1 Rules match cited pages — no. Says Scores take bare numbers (SKILL.md:10). https://docs.typesafe.ai/primitives/score.md",
                                25: "- G2 Examples pass F1-F6 — no. Example asks two things (SKILL.md:40). https://docs.typesafe.ai/concepts/how-to-build-with-system-one.md"})
    _fm(r, kind="teaches", verdict_1_code="1g", top_stakes="n.a.")
    out = tmp_path / "out"; assert run(lib, "export", str(out)).returncode == 0
    assert "Verdict 1: Misleading guide" in (out / "o__g.md").read_text()


def test_old_rubric_guide_needs_g_facts_and_skips_f0_gate(tmp_path, lib):
    r = make_rating(tmp_path / "g.md", "G", "o", "https://github.com/o/g", "2026-09-28", verdict=3, project_type="guide", rubric="2026-09-28b",
                    scores="execution: 2, fit: 2, coverage: 1, evidence: 0",
                    fact_lines={0: "- F0 Calls hosted Jev — n.a. A guide; makes no calls."})
    _fm(r, kind="teaches", top_stakes="n.a.")
    out = run(lib, "check", str(r)).stdout + run(lib, "check", str(r)).stderr
    assert "G1 missing" in out and "G2 missing" in out and "F0 is n.a." not in out


# --- Export text quality (2026-09-28, Lane P review) ---

def _export_one(tmp_path, lib, **kw):
    d = lib / "projects" / "o__p"; d.mkdir(parents=True)
    kw.setdefault("url", "https://github.com/o/p")
    make_rating(d / "2026-09-28.md", "P", "o", kw.pop("url"), "2026-09-28", **kw)
    out = tmp_path / "out"
    r = run(lib, "export", str(out)); assert r.returncode == 0, r.stderr
    return (out / "o__p.md").read_text(), (out / "full" / "o__p.md").read_text()


def test_export_summary_does_not_split_inside_quotes_or_eg(tmp_path, lib):
    summ = 'It keeps a ledger. Its rule is "Facts go to code. Judgments go to Jev." It blocks turns (e.g. a Stop hook) when a check fails.'
    page, _ = _export_one(tmp_path, lib, summary=summ)
    assert '> - Its rule is "Facts go to code. Judgments go to Jev."' in page
    assert "> - It blocks turns (e.g. a Stop hook) when a check fails." in page


def test_export_top_fix_is_the_first_instruction(tmp_path, lib):
    fixes = '1. **F22 — untrusted text not treated as data.** The diff text is risky. Add an injection check (e.g. "ignore this") before ranking. **(confirm with data.)** Source: `primitives`.'
    page, _ = _export_one(tmp_path, lib, core_fixes=fixes)
    assert '**Top fix:** Add an injection check (e.g. "ignore this") before ranking.' in page


def test_export_top_fix_drops_fact_prefix(tmp_path, lib):
    page, _ = _export_one(tmp_path, lib, core_fixes="1. F1: split `q` into two questions; combine in code.")
    assert "**Top fix:** Split `q` into two questions; combine in code." in page


def test_export_links_every_line_in_a_list_and_bare_follow_ons(tmp_path, lib):
    fl = {4: "- F4 batching — yes. One request (`src/a.ts:131,140`); again at `src/b.ts:12`, `:40-42`, `50-51`; threshold `3`."}
    _, full = _export_one(tmp_path, lib, fact_lines=fl)
    assert "src/a.ts#L140)" in full and "src/b.ts#L40-L42)" in full and "src/b.ts#L50-L51)" in full and "threshold `3`" in full
    assert ",140`" not in full and "`:40-42`" not in full


def test_export_links_huggingface_refs(tmp_path, lib):
    fl = {6: "- F6 check — yes. Threshold at `jev_omni.py:108`."}
    _, full = _export_one(tmp_path, lib, url="https://huggingface.co/o/p", fact_lines=fl)
    assert "(https://huggingface.co/o/p/blob/abc123def456789/jev_omni.py#L108)" in full
    assert "at [`abc123d`](https://huggingface.co/o/p/tree/abc123def456789)" in full and "[https://" not in full


def test_export_header_marks_earlier_rubric(tmp_path, lib):
    _, full = _export_one(tmp_path, lib, rubric="2026-09-01")
    assert "rubric 2026-09-01 (earlier)" in full


@pytest.mark.parametrize("note", ["second pass closed the gaps", "Raised from 1 in the first version of this rating",
                                  "the strongest evidence file in this rating library", "I kept 2 because the anchors are silent"])
def test_check_refuses_process_notes(tmp_path, lib, note):
    r = make_rating(tmp_path / "r.md", "P", "o", "https://github.com/o/p", "2026-09-28", summary="Fine. " + note + ".")
    res = run(lib, "check", str(r))
    assert res.returncode != 0 and "process note" in (res.stdout + res.stderr)


def test_double_dash_fact_lines_pass(tmp_path, lib):
    r = make_rating(tmp_path / "d.md", "D", "o", "https://github.com/o/d", "2026-09-29")
    r.write_text(r.read_text().replace(" — ", " -- "))
    res = run(lib, "check", str(r))
    assert res.returncode == 0, res.stdout + res.stderr


# --- Rating schema read from the rubric (2026-09-29) ---

def _fm(r, **kv):
    t = r.read_text()
    for k, v in kv.items():
        t = re.sub(rf"^{k}: .*$", f"{k}: {v}", t, flags=re.M) if re.search(rf"^{k}:", t, re.M) else t.replace("---\n", f"---\n{k}: {v}\n", 1)
    lvl = kv.get("top_stakes")
    if lvl in ("very high", "high", "low"):  # keep the fixture's Decisions line and F13 in step with the stakes a test sets
        t = re.sub(r"^- flag unclear commit \|.*$", f"- flag unclear commit | {'Noul' if lvl == 'low' else 'Choice'} | {lvl} | acts at src/x.py:9 | acts on the answer", t, flags=re.M)
        if lvl == "very high": t = t.replace("- F13 check13 -- n.a. No high or very high Choice", "- F13 check13 -- yes. Asked in several orders (src/x.py:9)")
    r.write_text(t); return with_steps(r)

def _chk(lib, r): res = run(lib, "check", str(r)); return res.returncode, res.stdout + res.stderr

def test_kind_derived_from_type(tmp_path, lib):
    # A wrong or missing rater-entered kind is ignored by check; add stores the kind the type gives.
    r = _fm(make_rating(tmp_path / "a.md", "A", "o", "https://github.com/o/a", "2026-09-29"), kind="teaches")
    code, out = _chk(lib, r); assert code == 0, out
    res = run(lib, "add", str(r)); assert res.returncode == 0, res.stdout + res.stderr
    stored = next((lib / "projects" / "o__a").glob("*.md")).read_text()
    assert re.search(r"^kind: uses$", stored, re.M) and "kind: teaches" not in stored
    r2 = make_rating(tmp_path / "b.md", "B", "o", "https://github.com/o/b", "2026-09-29")
    r2.write_text(re.sub(r"^kind: .*\n", "", r2.read_text(), flags=re.M))
    res = run(lib, "add", str(r2)); assert res.returncode == 0, res.stdout + res.stderr
    assert re.search(r"^kind: uses$", next((lib / "projects" / "o__b").glob("*.md")).read_text(), re.M)

def test_kind_stored_for_each_type_and_old_rubric_untouched(tmp_path, lib):
    import library as L
    for typ, kind in L.rubric_text.KIND_OF.items():
        t = f"---\nrubric: 2026-09-29\nproject_type: {typ}\nverdict: 3\n---\nx"
        assert re.search(rf"^kind: {kind}$", L.store_derived(t), re.M), typ
    old = "---\nrubric: 2026-09-28b\nproject_type: guide\nverdict: 3\n---\nx"
    assert L.store_derived(old) == old

def test_mention_only_needs_1a_or_1b_and_fields(tmp_path, lib):
    r = _fm(make_rating(tmp_path / "m.md", "M", "o", "https://github.com/o/m", "2026-09-29", verdict=1),
            project_type="jev-mention-only", kind="mentions", verdict_1_code="1c")
    code, out = _chk(lib, r); assert code != 0 and "1a (False marketing: Jev in name only) or 1b (Not a Jev integration)" in out and "type_best_match" in out

def test_1a_needs_citation(tmp_path, lib):
    r = _fm(make_rating(tmp_path / "m.md", "M", "o", "https://github.com/o/m", "2026-09-29", verdict=1),
            project_type="jev-mention-only", kind="mentions", verdict_1_code="1a", type_best_match="workflow",
            code_functionality="asks a chat model", replaces_jev="another LLM: a chat model", intended_call="none")
    code, out = _chk(lib, r); assert code != 0 and "citation" in out

def test_replacement_is_1r_without_facts(tmp_path, lib):
    r = make_rating(tmp_path / "r.md", "R", "o", "https://github.com/o/r", "2026-09-29", verdict=1,
                    scores="execution: n.a., fit: n.a., coverage: n.a., evidence: n.a.", fact_lines={0: "- F0 Calls hosted Jev -- no. Serves its own model (serve.py:3)"})
    r.write_text(re.sub(r"- F(?!0\b)\d+ .*\n", "", r.read_text()))
    _fm(r, project_type="jev-replacement", kind="replaces", verdict_1_code="1r", top_stakes="n.a.")
    code, out = _chk(lib, r); assert code == 0, out

def test_very_high_option_order_caps_at_3(tmp_path, lib):
    r = _fm(make_rating(tmp_path / "v.md", "V", "o", "https://github.com/o/v", "2026-09-29", verdict=4,
                        scores="execution: 3, fit: 2, coverage: 3, evidence: 2",
                        fact_lines={13: "- F13 Choice order handled -- no. Fixed order on the access Choice (app.py:9). https://docs.typesafe.ai/primitives/choice.md"}),
            top_stakes="very high")
    code, out = _chk(lib, r); assert code != 0 and "cap of 3" in out

def test_ignored_confidence_on_high_is_fatal(tmp_path, lib):
    r = _fm(make_rating(tmp_path / "c.md", "C", "o", "https://github.com/o/c", "2026-09-29", verdict=3,
                        scores="execution: 2, fit: 2, coverage: 3, evidence: 2",
                        fact_lines={11: "- F11 Confidence drives action -- no. Acts on the top answer (app.py:20). https://docs.typesafe.ai/confidence.md"}),
            top_stakes="high")
    code, out = _chk(lib, r); assert code != 0 and "cap of 2" in out

def test_old_rubric_rating_not_held_to_new_fields(tmp_path, lib):
    r = make_rating(tmp_path / "o.md", "O", "o", "https://github.com/o/o", "2026-09-28", rubric="2026-09-28b")
    r.write_text(re.sub(r"^(kind|verdict_1_code|citation|top_stakes): .*\n", "", r.read_text(), flags=re.M))
    code, out = _chk(lib, r); assert "kind" not in out and "top_stakes" not in out

def test_export_label_from_code(tmp_path, lib):
    r = _fm(make_rating(tmp_path / "x.md", "X", "o", "https://github.com/o/x", "2026-09-29", verdict=1,
                        scores="execution: n.a., fit: n.a., coverage: n.a., evidence: n.a.", fact_lines={0: "- F0 Calls hosted Jev -- no. Serves its own model (serve.py:3)"}),
            project_type="jev-mention-only", kind="mentions", verdict_1_code="1b", top_stakes="n.a.",
            type_best_match="other: parody", code_functionality="returns a canned line", replaces_jev="fixed values", intended_call="none")
    r.write_text(re.sub(r"- F(?!0\b)\d+ .*\n", "", r.read_text()))
    assert run(lib, "add", str(r)).returncode == 0
    out = tmp_path / "out"; run(lib, "export", str(out))
    assert "Verdict 1: Not a Jev integration" in (out / "o__x.md").read_text()

F20_NO = "- F20 Stakes handled -- no. Nothing gates the action (app.py:30). https://docs.typesafe.ai/concepts/stakes.md"

def test_f20_no_caps_only_on_very_high(tmp_path, lib):
    kw = dict(verdict=4, scores="execution: 3, fit: 3, coverage: 3, evidence: 2", fact_lines={20: F20_NO})
    hi = _fm(make_rating(tmp_path / "h.md", "H", "o", "https://github.com/o/h", "2026-09-29", **kw), top_stakes="high")
    code, out = _chk(lib, hi); assert "cap of 3" not in out, out
    vh = _fm(make_rating(tmp_path / "vh.md", "H", "o", "https://github.com/o/h", "2026-09-29", **kw), top_stakes="very high")
    code, out = _chk(lib, vh); assert code != 0 and "cap of 3" in out

def test_workflow_with_f0_no_is_refused(tmp_path, lib):
    r = make_rating(tmp_path / "w.md", "W", "o", "https://github.com/o/w", "2026-09-29",
                    fact_lines={0: "- F0 Calls hosted Jev -- no. Serves its own model (serve.py:3)"})
    code, out = _chk(lib, r); assert code != 0 and "F0" in out

# --- Step log and comparison cards (2026-09-29) ---

def test_routing_changed_after_facts_refused(tmp_path, lib):
    r = make_rating(tmp_path / "s.md", "S", "o", "https://github.com/o/s", "2026-09-29")
    old = hashlib.sha1(b"workflow|uses|none|high").hexdigest()
    (tmp_path / "s.md.steps.json").write_text(json.dumps([{"step": s, "time": f"2026-09-29T10:0{i}", "routing": old}
                                                          for i, s in enumerate(["routing", "facts", "scores", "compare", "verdict"])]))
    code, out = _chk(lib, r)
    assert code != 0 and "routing changed after the facts were served" in out

def test_routing_change_cleared_by_controller_passes(tmp_path, lib):
    r = make_rating(tmp_path / "s.md", "S", "o", "https://github.com/o/s", "2026-09-29")
    old = hashlib.sha1(b"workflow|uses|none|high").hexdigest()
    (tmp_path / "s.md.steps.json").write_text(json.dumps([{"step": s, "time": f"2026-09-29T10:0{i}", "routing": old}
                                                          for i, s in enumerate(["routing", "facts", "scores", "compare", "verdict"])]))
    (tmp_path / "routing_revised.json").write_text('{"reason": "stakes were low", "time": "2026-09-29T11:00"}')
    code, out = _chk(lib, r); assert code == 0, out

def test_missing_step_log_refused(tmp_path, lib):
    r = make_rating(tmp_path / "n.md", "N", "o", "https://github.com/o/n", "2026-09-29")
    (tmp_path / "n.md.steps.json").unlink()
    code, out = _chk(lib, r); assert code != 0 and "step log" in out

def test_partial_step_log_refused(tmp_path, lib):
    r = make_rating(tmp_path / "p.md", "P", "o", "https://github.com/o/p", "2026-09-29")
    log = json.loads((tmp_path / "p.md.steps.json").read_text())[:1]
    (tmp_path / "p.md.steps.json").write_text(json.dumps(log))
    code, out = _chk(lib, r); assert code != 0 and "expected" in out

def test_old_rubric_needs_no_step_log(tmp_path, lib):
    r = make_rating(tmp_path / "o.md", "O", "o", "https://github.com/o/o", "2026-09-28", rubric="2026-09-28b")
    (tmp_path / "o.md.steps.json").unlink()
    code, out = _chk(lib, r); assert "step log" not in out

def test_add_copies_step_log_into_evidence(tmp_path, lib):
    r = make_rating(tmp_path / "a.md", "A", "o", "https://github.com/o/a", "2026-09-29", coverage="- a.py -- read\n- b.py -- read")
    ev = make_evidence(tmp_path)
    assert run(lib, "add", str(r), "--evidence", str(ev)).returncode == 0
    dest = lib / "projects" / "o__a" / "2026-09-29.md"
    assert (lib / "projects" / "o__a" / "2026-09-29-evidence" / "2026-09-29.md.steps.json").exists()
    code, out = _chk(lib, dest); assert "step log" not in out

def test_cards_rank_type_lineage_stage(tmp_path, lib):
    sys.path.insert(0, str(pathlib.Path(__file__).parent))
    import importlib, library
    importlib.reload(library)
    library.PROJ = lib / "projects"
    for name, typ, verdict in (("Near", "workflow", 4), ("Far", "library", 2)):
        r = make_rating(tmp_path / f"{name}.md", name, "o", f"https://github.com/o/{name.lower()}", "2026-09-29", verdict=verdict, project_type=typ)
        assert run(lib, "add", str(r)).returncode == 0
    d = {"project_type": "workflow", "lineage": "new", "stages": "[data-prep]", "owner": "x", "project": "me"}
    cards = library.cards(d, exclude="x/me")
    assert [c["verdict"] for c in cards][:2] == ["4", "2"] and set(cards[0]) >= {"path", "verdict", "code", "why", "failed"}
    assert library.cards(d, exclude="o/near")[0]["verdict"] == "2"

def test_latest_rating_for_url(tmp_path, lib):
    for rated in ("2026-09-28", "2026-09-29"):
        run(lib, "add", str(make_rating(tmp_path / f"{rated}.md", "A", "o", "https://github.com/o/a", rated)))
    sys.path.insert(0, str(pathlib.Path(__file__).parent))
    import importlib, library
    importlib.reload(library); library.PROJ = lib / "projects"
    assert library.latest_rating_for("https://github.com/o/a").name == "2026-09-29.md"
    assert library.latest_rating_for("https://github.com/o/none") is None

# Mechanical limits, enforced for rubric 2026-09-29 and later (Step 4b(d))

def test_why_over_20_words_refused(tmp_path, lib):
    r = _fm(make_rating(tmp_path / "w.md", "W", "o", "https://github.com/o/w", "2026-09-29"), why=" ".join(["word"] * 21))
    code, out = _chk(lib, r); assert code != 0 and "why" in out and "20 words" in out

def test_fact_finding_over_20_words_refused(tmp_path, lib):
    r = make_rating(tmp_path / "w.md", "W", "o", "https://github.com/o/w", "2026-09-29",
                    fact_lines={3: "- F3 check3 -- yes. " + " ".join(["word"] * 21) + " (a.py:1)"})
    code, out = _chk(lib, r); assert code != 0 and "F3" in out and "20 words" in out

def test_summary_over_three_sentences_refused(tmp_path, lib):
    r = make_rating(tmp_path / "w.md", "W", "o", "https://github.com/o/w", "2026-09-29", summary="One. Two. Three. Four.")
    code, out = _chk(lib, r); assert code != 0 and "Summary" in out

def test_verdict_reasoning_over_five_sentences_refused(tmp_path, lib):
    r = make_rating(tmp_path / "w.md", "W", "o", "https://github.com/o/w", "2026-09-29")
    r.write_text(r.read_text().replace("Test fixture.", "One. Two. Three. Four. Five. Six."))
    code, out = _chk(lib, r); assert code != 0 and "Verdict and reasoning" in out

def test_unknown_stage_label_refused(tmp_path, lib):
    r = _fm(make_rating(tmp_path / "w.md", "W", "o", "https://github.com/o/w", "2026-09-29"), stages="[data-prep, evaluation]")
    code, out = _chk(lib, r); assert code != 0 and "evaluation" in out

def test_commit_must_match_evidence_meta(tmp_path, lib):
    r = make_rating(tmp_path / "w.md", "W", "o", "https://github.com/o/w", "2026-09-29", commit="abc123def456789")
    ev = make_evidence(tmp_path); (ev / "meta.json").write_text(json.dumps({"commit": "fff999fff999fff"}))
    res = run(lib, "check", str(r), "--evidence", str(ev))
    assert res.returncode != 0 and "commit" in res.stdout + res.stderr
    (ev / "meta.json").write_text(json.dumps({"commit": "abc123def456789"}))
    res = run(lib, "check", str(r), "--evidence", str(ev)); assert "commit" not in res.stdout + res.stderr.replace("commit not", "")

def test_mechanical_limits_skipped_for_old_rubric(tmp_path, lib):
    r = make_rating(tmp_path / "w.md", "W", "o", "https://github.com/o/w", "2026-09-28", rubric="2026-09-28b", summary="One. Two. Three. Four.")
    code, out = _chk(lib, r); assert "Summary" not in out


def _cant_rate(tmp_path, name="c"):
    r = make_rating(tmp_path / f"{name}.md", "C", "o", "https://github.com/o/c", "2026-09-29", verdict="cant-rate")
    return r

def test_cant_rate_without_step_log_refused(tmp_path, lib):
    r = _cant_rate(tmp_path); (tmp_path / "c.md.steps.json").unlink()
    code, out = _chk(lib, r); assert code != 0 and "step log" in out

def test_cant_rate_with_routing_only_log_passes(tmp_path, lib):
    r = _cant_rate(tmp_path)
    log = json.loads((tmp_path / "c.md.steps.json").read_text())[:1]
    (tmp_path / "c.md.steps.json").write_text(json.dumps(log))
    code, out = _chk(lib, r); assert "step log" not in out, out

def test_cant_rate_with_out_of_order_log_refused(tmp_path, lib):
    r = _cant_rate(tmp_path)
    log = json.loads((tmp_path / "c.md.steps.json").read_text())
    (tmp_path / "c.md.steps.json").write_text(json.dumps([log[1], log[0]]))
    code, out = _chk(lib, r); assert code != 0 and "step log" in out


# --- Task 4c: F0 points at the call; decisions and stakes; guides get 1t; clients' stakes n.a. (2026-09-29) ---

def _uses(tmp_path, name="u.md", **kw):
    return make_rating(tmp_path / name, "U", "o", "https://github.com/o/u", "2026-09-29", **kw)

def _ev_with(tmp_path, files):
    """An evidence folder whose files/ holds {repo path: text} under the saved names coverage_manifest.py uses."""
    ev = make_evidence(tmp_path, files=list(files), base=False); (ev / "files").mkdir(exist_ok=True)
    for path, text in files.items(): (ev / "files" / path.replace("/", "__")).write_text(text)
    return ev

def _chk_ev(lib, r, ev):
    res = run(lib, "check", "--evidence", str(ev), str(r)); return res.returncode, res.stdout + res.stderr

CALL_SRC = "import os\n\nfrom typesafe import TypeSafeClient\nclient = TypeSafeClient()\n\nx = 1\n"
F0_YES = "- F0 Calls hosted Jev -- yes. Imports the client and calls it ({}). https://docs.typesafe.ai/introduction/quickstart.md"

def test_f0_yes_citing_only_a_readme_is_refused(tmp_path, lib):
    r = _uses(tmp_path, fact_lines={0: F0_YES.format("README.md:3")})
    code, out = _chk(lib, r); assert code != 0 and "F0" in out and "code file" in out

def test_f0_yes_citing_tests_or_docs_is_refused(tmp_path, lib):
    for cite in ("tests/test_app.py:4", "docs/guide.py:2", "notes.txt:1"):
        r = _uses(tmp_path, fact_lines={0: F0_YES.format(cite)})
        code, out = _chk(lib, r); assert code != 0 and "code file" in out, cite

def test_f0_yes_without_any_line_number_is_refused(tmp_path, lib):
    r = _uses(tmp_path, fact_lines={0: "- F0 Calls hosted Jev -- yes. It calls Jev somewhere in app.py."})
    code, out = _chk(lib, r); assert code != 0 and "path:line" in out

def test_f0_yes_cited_file_must_be_in_evidence_files(tmp_path, lib):
    ev = _ev_with(tmp_path, {"other.py": CALL_SRC})
    r = _uses(tmp_path, fact_lines={0: F0_YES.format("src/x.py:3")})
    code, out = _chk_ev(lib, r, ev); assert code != 0 and "src/x.py" in out and "files/" in out

def test_f0_yes_cited_line_must_hold_a_hosted_call(tmp_path, lib):
    ev = _ev_with(tmp_path, {"src/x.py": CALL_SRC})
    r = _uses(tmp_path, fact_lines={0: F0_YES.format("src/x.py:6")})
    code, out = _chk_ev(lib, r, ev); assert code != 0 and "src/x.py:6" in out and "hosted" in out

def test_f0_refusal_names_client_construction_and_client_calls(tmp_path, lib):
    ev = _ev_with(tmp_path, {"src/x.py": CALL_SRC})
    r = _uses(tmp_path, fact_lines={0: F0_YES.format("src/x.py:6")})
    code, out = _chk_ev(lib, r, ev)
    assert code != 0 and "creates the client" in out and "calls it (client.noul(...))" in out

def test_f0_yes_citing_the_call_line_passes_and_the_import_line_does_not(tmp_path, lib):
    ev = _ev_with(tmp_path, {"src/x.py": CALL_SRC})
    r = _uses(tmp_path, fact_lines={0: F0_YES.format("src/x.py:3")})
    code, out = _chk_ev(lib, r, ev); assert code != 0 and "F0 cites src/x.py:3" in out, out
    r = _uses(tmp_path, fact_lines={0: F0_YES.format("src/x.py:4")})
    code, out = _chk_ev(lib, r, ev); assert "F0" not in out, out

def test_f0_no_with_a_hosted_call_in_app_py_is_refused(tmp_path, lib):
    ev = _ev_with(tmp_path, {"app.py": CALL_SRC})
    r = _fm(_uses(tmp_path, verdict=1, scores="execution: n.a., fit: n.a., coverage: n.a., evidence: n.a.",
                  fact_lines={0: "- F0 Calls hosted Jev -- no. The code calls a chat model (chat.py:2)"}),
            project_type="jev-mention-only", kind="mentions", verdict_1_code="1b", top_stakes="n.a.",
            type_best_match="other: parody", code_functionality="canned", replaces_jev="fixed values", intended_call="none")
    code, out = _chk_ev(lib, r, ev); assert code != 0 and "app.py" in out and "F0 is no" in out

def test_f0_no_naming_the_file_and_why_passes(tmp_path, lib):
    ev = _ev_with(tmp_path, {"app.py": CALL_SRC})
    r = _fm(_uses(tmp_path, verdict=1, scores="execution: n.a., fit: n.a., coverage: n.a., evidence: n.a.",
                  fact_lines={0: "- F0 Calls hosted Jev -- no. app.py:3 imports the client but the branch never runs (app.py:9)"}),
            project_type="jev-mention-only", kind="mentions", verdict_1_code="1b", top_stakes="n.a.",
            type_best_match="other: parody", code_functionality="canned", replaces_jev="fixed values", intended_call="none")
    code, out = _chk_ev(lib, r, ev); assert "F0 is no" not in out, out

def test_1a_citation_needs_file_and_line(tmp_path, lib):
    kw = dict(project_type="jev-mention-only", kind="mentions", verdict_1_code="1a", top_stakes="n.a.",
              type_best_match="other: parody", code_functionality="canned", replaces_jev="fixed values", intended_call="none")
    base = dict(verdict=1, scores="execution: n.a., fit: n.a., coverage: n.a., evidence: n.a.",
                fact_lines={0: "- F0 Calls hosted Jev -- no. Canned answers (app.py:2)"})
    r = _fm(_uses(tmp_path, "a.md", **base), citation='"powered by Jev"', **kw)
    code, out = _chk(lib, r); assert code != 0 and "file:line" in out
    r = _fm(_uses(tmp_path, "b.md", **base), citation='"powered by Jev" (README.md:3)', **kw)
    code, out = _chk(lib, r); assert code == 0, out

def test_workflow_without_decisions_is_refused(tmp_path, lib):
    r = _uses(tmp_path, decisions=[])
    code, out = _chk(lib, r); assert code != 0 and "## Decisions" in out and "acts at" in out

def test_decision_line_needs_five_parts_primitive_and_level(tmp_path, lib):
    for bad in ("- sort the ticket | Noul | low | shows it",
                "- sort the ticket | Vote | low | acts at src/x.py:9 | shows it",
                "- sort the ticket | Noul | medium | acts at src/x.py:9 | shows it",
                "- sort the ticket | Noul | low | src/x.py | shows it"):
        r = _uses(tmp_path, decisions=[bad])
        code, out = _chk(lib, r); assert code != 0 and "Decisions" in out, bad

def test_decision_file_must_be_in_evidence_files(tmp_path, lib):
    ev = _ev_with(tmp_path, {"src/x.py": CALL_SRC})
    r = _uses(tmp_path, decisions=["- flag it | Noul | low | acts at src/y.py:9 | shows it"])
    code, out = _chk_ev(lib, r, ev); assert code != 0 and "src/y.py" in out and "Decisions" in out

def test_very_high_choice_with_f13_na_is_refused(tmp_path, lib):
    r = _fm(_uses(tmp_path), top_stakes="very high")
    t = r.read_text().replace("- F13 check13 -- yes. Asked in several orders (src/x.py:9)", "- F13 check13 -- n.a. one order is fine")
    r.write_text(t)
    code, out = _chk(lib, r); assert code != 0 and "F13" in out and "very high" in out

def test_no_high_choice_means_f13_is_na(tmp_path, lib):
    r = _uses(tmp_path, fact_lines={13: "- F13 check13 -- yes. Asked in two orders (src/x.py:9)"})
    code, out = _chk(lib, r); assert code != 0 and "F13" in out and "n.a." in out

def test_high_choice_allows_f13_na_only_when_f11_yes(tmp_path, lib):
    r = _fm(_uses(tmp_path), top_stakes="high")
    code, out = _chk(lib, r); assert "F13" not in out, out
    r = _fm(_uses(tmp_path, "h2.md", fact_lines={11: "- F11 check11 -- no. Acts on the top answer (src/x.py:9). https://docs.typesafe.ai/confidence.md"}), top_stakes="high")
    code, out = _chk(lib, r); assert code != 0 and "F13" in out and "F11" in out

def test_f11_na_only_when_every_decision_is_low(tmp_path, lib):
    r = _uses(tmp_path, fact_lines={11: "- F11 check11 -- n.a. Only shown to the author"})
    code, out = _chk(lib, r); assert "F11" not in out, out
    r = _fm(_uses(tmp_path, "h.md", fact_lines={11: "- F11 check11 -- n.a. Only shown"}), top_stakes="high")
    code, out = _chk(lib, r); assert code != 0 and "F11" in out and "low" in out

def test_guide_gets_1t_and_no_facts(tmp_path, lib):
    r = _fm(_uses(tmp_path, verdict=1, project_type="guide", decisions=[], scores="execution: n.a., fit: n.a., coverage: n.a., evidence: n.a.",
                  fact_lines={0: "- F0 Calls hosted Jev -- n.a. A guide; makes no calls."}),
            kind="teaches", verdict_1_code="1t", top_stakes="n.a.")
    r.write_text(re.sub(r"- F(?!0\b)\d+ .*\n", "", r.read_text()))
    code, out = _chk(lib, r); assert code == 0, out

def test_guide_with_1g_or_none_is_refused(tmp_path, lib):
    for c in ("1g", "none"):
        r = _fm(_uses(tmp_path, decisions=[], project_type="guide", fact_lines={0: "- F0 Calls hosted Jev -- n.a. A guide; makes no calls."}),
                kind="teaches", verdict_1_code=c, top_stakes="n.a.")
        code, out = _chk(lib, r); assert code != 0 and "1t" in out, c

def test_1t_only_for_a_guide(tmp_path, lib):
    r = _fm(_uses(tmp_path), verdict_1_code="1t")
    code, out = _chk(lib, r); assert code != 0 and "1t" in out

def test_export_label_for_1t(tmp_path, lib):
    r = _fm(_uses(tmp_path, verdict=1, project_type="guide", decisions=[], scores="execution: n.a., fit: n.a., coverage: n.a., evidence: n.a.",
                  fact_lines={0: "- F0 Calls hosted Jev -- n.a. A guide; makes no calls."}),
            kind="teaches", verdict_1_code="1t", top_stakes="n.a.")
    r.write_text(re.sub(r"- F(?!0\b)\d+ .*\n", "", r.read_text()))
    assert run(lib, "add", str(r)).returncode == 0
    out = tmp_path / "out"; assert run(lib, "export", str(out)).returncode == 0
    assert "Not rated yet: guide" in (out / "o__u.md").read_text()
    assert "**n.a. (guide, not yet rated)**" in (out / "README.md").read_text()


# --- Task 4c fix round 1 ---
BOT_SRC = "\n".join(["import os", "from typesafe import TypeSafeClient", "", "# setup", "client = TypeSafeClient(api_key=KEY)", "",
                     "def run(x):", "    state = {'x': x}", "    q = build(state)", "    # send", "    log(x)", "", "    # ask", "    r = client.ask(state, q)", "    return r"]) + "\n"
CHAT_SRC = "\n".join(["from typesafe import TypeSafeClient  # unused", "import openai", "c = openai.OpenAI()", "", "r = c.chat.completions.create(model='x')"]) + "\n"

def test_f0_yes_accepts_the_rubrics_client_and_call_example(tmp_path, lib):
    ev = _ev_with(tmp_path, {"bot.py": BOT_SRC.replace("from typesafe import TypeSafeClient\n", "import typesafe_sdk_alias\n")})
    for cite in ("bot.py:5", "bot.py:14"):
        r = _uses(tmp_path, fact_lines={0: F0_YES.format(cite)})
        code, out = _chk_ev(lib, r, ev); assert "F0" not in out, (cite, out)

def test_f0_yes_citing_a_chat_completions_call_is_refused(tmp_path, lib):
    ev = _ev_with(tmp_path, {"bot.py": CHAT_SRC.replace("from typesafe import TypeSafeClient  # unused\n", "")})
    r = _uses(tmp_path, fact_lines={0: F0_YES.format("bot.py:4")})
    code, out = _chk_ev(lib, r, ev); assert code != 0 and "bot.py:4" in out and "hosted" in out

def test_f0_no_needs_three_words_of_reason_per_file(tmp_path, lib):
    ev = _ev_with(tmp_path, {"app.py": CALL_SRC})
    kw = dict(project_type="jev-mention-only", kind="mentions", verdict_1_code="1b", top_stakes="n.a.",
              type_best_match="other: parody", code_functionality="canned", replaces_jev="fixed values", intended_call="none")
    base = dict(verdict=1, scores="execution: n.a., fit: n.a., coverage: n.a., evidence: n.a.")
    r = _fm(_uses(tmp_path, "a.md", fact_lines={0: "- F0 Calls hosted Jev -- no. Only app.py (chat.py:2)"}, **base), **kw)
    code, out = _chk_ev(lib, r, ev); assert code != 0 and "app.py" in out and "three words of reason" in out
    r = _fm(_uses(tmp_path, "b.md", fact_lines={0: "- F0 Calls hosted Jev -- no. app.py imports the client but never calls it (chat.py:2)"}, **base), **kw)
    code, out = _chk_ev(lib, r, ev); assert "F0 is no" not in out, out


# --- Task 4d: code works out top_stakes; replacements that claim Jev get 1a ---
import library as L

def _drop_top(r):
    r.write_text(re.sub(r"^top_stakes: .*\n", "", r.read_text(), flags=re.M)); return with_steps(r)

def _stored(lib, slug="o__u"):
    return sorted((lib / "projects" / slug).glob("*.md"), key=lambda p: (len(p.name), p.name))[-1].read_text()

VH = "- grant access | Choice | very high | acts at src/x.py:20 | grants it"
F13_YES = "- F13 check13 -- yes. Asked in three orders (src/x.py:20)"

def test_derive_top_stakes_is_na_for_guide_client_and_every_routed_code():
    for typ, code in (("guide", "1t"), ("client", "none"), ("jev-replacement", "1r"), ("jev-replacement", "1a"),
                      ("jev-mention-only", "1b"), ("workflow", "1c")):
        assert L.derive_top_stakes({"project_type": typ, "verdict_1_code": code}, "## Decisions\n" + DECISION_LOW + "\n") == "n.a.", (typ, code)

def test_derive_top_stakes_is_the_highest_listed():
    d = {"project_type": "workflow", "verdict_1_code": "none"}
    t = lambda *ls: "## Decisions\n" + "\n".join(ls) + "\n"
    assert L.derive_top_stakes(d, t(DECISION_LOW)) == "low"
    assert L.derive_top_stakes(d, t(DECISION_LOW, "- route | Choice | high | acts at src/x.py:12 | routes")) == "high"
    assert L.derive_top_stakes(d, t(DECISION_LOW, "- route | Choice | high | acts at src/x.py:12 | routes", VH)) == "very high"

def test_rater_does_not_enter_top_stakes(tmp_path, lib):
    r = _drop_top(_uses(tmp_path))
    code, out = _chk(lib, r); assert code == 0, out

def test_a_rater_entered_top_stakes_is_ignored_and_the_derived_one_reported(tmp_path, lib):
    r = _uses(tmp_path, decisions=[DECISION_LOW, VH], fact_lines={13: F13_YES})
    r.write_text(re.sub(r"^top_stakes: .*$", "top_stakes: low", r.read_text(), flags=re.M)); with_steps(r)
    code, out = _chk(lib, r); assert code == 0 and "top_stakes: very high" in out, out

def test_client_and_guide_need_no_top_stakes_and_a_wrong_one_is_not_refused(tmp_path, lib):
    r = _drop_top(_fm(_uses(tmp_path, decisions=[]), project_type="client"))
    code, out = _chk(lib, r); assert code == 0 and "top_stakes: n.a." in out, out
    r = _fm(_uses(tmp_path, "c2.md", decisions=[]), project_type="client", top_stakes="high")
    code, out = _chk(lib, r); assert code == 0, out
    r = _fm(_uses(tmp_path, "g.md", verdict=1, project_type="guide", decisions=[], scores="execution: n.a., fit: n.a., coverage: n.a., evidence: n.a.",
                  fact_lines={0: "- F0 Calls hosted Jev -- n.a. A guide; makes no calls."}), kind="teaches", verdict_1_code="1t", top_stakes="low")
    r.write_text(re.sub(r"- F(?!0\b)\d+ .*\n", "", r.read_text()))
    code, out = _chk(lib, r); assert code == 0 and "top_stakes: n.a." in out, out

def test_add_stores_the_derived_top_stakes(tmp_path, lib):
    r = _drop_top(_uses(tmp_path, decisions=[DECISION_LOW, VH], fact_lines={13: F13_YES}))
    assert run(lib, "add", str(r)).returncode == 0
    assert re.search(r"^top_stakes: very high$", _stored(lib), re.M)
    r = _uses(tmp_path, "b.md", decisions=[DECISION_LOW])
    r.write_text(re.sub(r"^top_stakes: .*$", "top_stakes: very high", r.read_text(), flags=re.M)); with_steps(r)
    assert run(lib, "add", str(r)).returncode == 0
    assert len(re.findall(r"^top_stakes: .*$", _stored(lib), re.M)) == 1 and re.search(r"^top_stakes: low$", _stored(lib), re.M)

def test_add_stores_na_for_a_routed_code_and_a_guide(tmp_path, lib):
    r = _drop_top(make_rating(tmp_path / "r.md", "R", "o", "https://github.com/o/r", "2026-09-29", verdict=1,
                    scores="execution: n.a., fit: n.a., coverage: n.a., evidence: n.a.", fact_lines={0: "- F0 Calls hosted Jev -- no. Serves its own model (serve.py:3)"}))
    _fm(r, project_type="jev-replacement", kind="replaces", verdict_1_code="1r")
    r.write_text(re.sub(r"- F(?!0\b)\d+ .*\n", "", r.read_text()))
    assert run(lib, "add", str(r)).returncode == 0, run(lib, "check", str(r)).stdout
    assert re.search(r"^top_stakes: n\.a\.$", _stored(lib, "o__r"), re.M)

def test_caps_use_the_derived_stakes_not_the_front_matter(tmp_path, lib):
    r = _drop_top(_uses(tmp_path, verdict=4, scores="execution: 3, fit: 3, coverage: 3, evidence: 2",
                        decisions=[VH], fact_lines={13: F13_YES, 20: "- F20 Stakes handled -- no. Nothing gates the action (app.py:30). https://docs.typesafe.ai/concepts/stakes.md"}))
    code, out = _chk(lib, r); assert code != 0 and "cap of 3" in out, out

def test_a_stakes_change_after_the_facts_were_served_is_flagged(tmp_path, lib):
    r = _drop_top(_uses(tmp_path))
    r.write_text(r.read_text().replace(DECISION_LOW, "- flag unclear commit | Choice | high | acts at src/x.py:9 | blocks it"))
    code, out = _chk(lib, r); assert code != 0 and "routing changed" in out, out

def test_a_guide_f0_line_may_say_no_and_add_stores_na(tmp_path, lib):
    r = _fm(_uses(tmp_path, verdict=1, project_type="guide", decisions=[], scores="execution: n.a., fit: n.a., coverage: n.a., evidence: n.a.",
                  fact_lines={0: "- F0 Calls hosted Jev -- no. A guide; sample requests only."}), kind="teaches", verdict_1_code="1t")
    r.write_text(re.sub(r"- F(?!0\b)\d+ .*\n", "", r.read_text()))
    code, out = _chk(lib, r); assert code == 0, out
    assert run(lib, "add", str(r)).returncode == 0
    st = _stored(lib)
    assert "- F0 Calls hosted Jev -- n.a. A guide; sample requests only." in st and "F0 Calls hosted Jev -- no" not in st

def _repl(tmp_path, code, citation="none", name="p.md"):
    r = make_rating(tmp_path / name, "P", "o", "https://github.com/o/p", "2026-09-29", verdict=1,
                    scores="execution: n.a., fit: n.a., coverage: n.a., evidence: n.a.", fact_lines={0: "- F0 Calls hosted Jev -- no. Serves its own model (serve.py:3)"})
    r.write_text(re.sub(r"- F(?!0\b)\d+ .*\n", "", r.read_text()))
    return _fm(r, project_type="jev-replacement", kind="replaces", verdict_1_code=code, citation=citation, top_stakes="n.a.")

CLAIM = '"powered by Jev" (README.md:3)'

def test_a_replacement_with_a_claim_gets_1a(tmp_path, lib):
    code, out = _chk(lib, _repl(tmp_path, "1a", CLAIM)); assert code == 0, out
    code, out = _chk(lib, _repl(tmp_path, "1r", CLAIM, "q.md"))
    assert code != 0 and "1a" in out and "claim" in out and "citation" in out

def test_a_replacement_without_a_claim_gets_1r(tmp_path, lib):
    code, out = _chk(lib, _repl(tmp_path, "1r")); assert code == 0, out
    code, out = _chk(lib, _repl(tmp_path, "1a", "none", "q.md"))
    assert code != 0 and "1r" in out and "1a" in out

def test_a_replacement_1a_citation_needs_file_and_line(tmp_path, lib):
    code, out = _chk(lib, _repl(tmp_path, "1a", '"powered by Jev"')); assert code != 0 and "file:line" in out

def test_a_replacement_only_gets_1a_or_1r(tmp_path, lib):
    code, out = _chk(lib, _repl(tmp_path, "1b")); assert code != 0 and "1r" in out


# --- Review fix 1 (2026-09-30): call-line checks never skip silently ---

def _beside(tmp_path, files, name="rating.md", **kw):
    """A rater's folder: rating.md beside manifest.md and files/ (jevaluate-harness/rater-brief.md)."""
    d = tmp_path / "slug"; d.mkdir(exist_ok=True)
    ev = make_evidence(d, files=list(files), base=False); (ev / "manifest.md").rename(d / "manifest.md"); ev.rmdir()
    (d / "files").mkdir(exist_ok=True)
    for path, text in files.items(): (d / "files" / path.replace("/", "__")).write_text(text)
    r = make_rating(d / name, "U", "o", "https://github.com/o/u", "2026-09-29", auto_evidence=False, **kw)
    return d, r

def test_evidence_is_found_when_manifest_sits_beside_the_rating(tmp_path, lib):
    d, r = _beside(tmp_path, {"src/x.py": CALL_SRC}, fact_lines={0: F0_YES.format("src/x.py:6")})
    code, out = _chk(lib, r)
    assert code != 0 and "not a hosted Jev call" in out and "src/x.py:6" in out, out

def test_f0_yes_with_no_evidence_is_refused_not_skipped(tmp_path, lib):
    r = _uses(tmp_path, auto_evidence=False)
    code, out = _chk(lib, r)
    assert code != 0 and "F0 was not checked" in out and "--evidence" in out, out

def test_f0_no_with_no_evidence_is_refused_not_skipped(tmp_path, lib):
    r = _fm(_uses(tmp_path, auto_evidence=False, verdict=1, scores="execution: n.a., fit: n.a., coverage: n.a., evidence: n.a.",
                  fact_lines={0: "- F0 Calls hosted Jev -- no. Canned answers only (app.py:2)"}),
            project_type="jev-mention-only", kind="mentions", verdict_1_code="1b", top_stakes="n.a.",
            type_best_match="other: parody", code_functionality="canned", replaces_jev="fixed values", intended_call="none")
    code, out = _chk(lib, r)
    assert code != 0 and "F0 was not checked" in out and "--evidence" in out, out

def test_add_refuses_f0_yes_with_no_evidence(tmp_path, lib):
    r = _uses(tmp_path, auto_evidence=False)
    p = run(lib, "add", str(r))
    assert p.returncode != 0 and "F0 was not checked" in p.stdout + p.stderr
    assert not (lib / "projects").exists()


# --- Review fix 2 (2026-09-30): a guide does not skip the calls-Jev check ---

def _guide(tmp_path, f0_line, name="g.md", coverage=None):
    r = _fm(_uses(tmp_path, name, verdict=1, project_type="guide", decisions=[], scores="execution: n.a., fit: n.a., coverage: n.a., evidence: n.a.",
                  fact_lines={0: f0_line}, coverage=coverage), kind="teaches", verdict_1_code="1t", top_stakes="n.a.")
    r.write_text(re.sub(r"- F(?!0\b)\d+ .*\n", "", r.read_text())); return r

def test_guide_with_f0_yes_is_refused(tmp_path, lib):
    r = _guide(tmp_path, F0_YES.format("src/x.py:5"))
    code, out = _chk(lib, r)
    assert code != 0 and "guide" in out and "n.a." in out and "uses type" in out, out

def test_guide_whose_code_holds_a_hosted_call_is_refused_naming_the_file(tmp_path, lib):
    ev = _ev_with(tmp_path, {"tutorial/run.py": CALL_SRC, "README.md": "# hi\n"})
    r = _guide(tmp_path, "- F0 Calls hosted Jev -- n.a. A guide; sample requests only.")
    code, out = _chk_ev(lib, r, ev)
    assert code != 0 and "tutorial/run.py" in out and "typed by what its code does" in out, out

def test_guide_with_no_hosted_call_in_its_code_passes(tmp_path, lib):
    ev = _ev_with(tmp_path, {"tutorial/run.py": "print('hi')\n", "README.md": "uses api.typesafe.ai in prose\n"})
    r = _guide(tmp_path, "- F0 Calls hosted Jev -- n.a. A guide; sample requests only.", coverage="- tutorial/run.py -- read\n- README.md -- read")
    code, out = _chk_ev(lib, r, ev); assert code == 0, out


# --- Review fix 3 (2026-09-30): F0 no is checked against the broad call-line rule ---

NO_MENTION = dict(project_type="jev-mention-only", kind="mentions", verdict_1_code="1b", top_stakes="n.a.",
                  type_best_match="other: parody", code_functionality="canned", replaces_jev="fixed values", intended_call="none")

def _no_rating(tmp_path, f0_line, coverage=None):
    return _fm(_uses(tmp_path, verdict=1, scores="execution: n.a., fit: n.a., coverage: n.a., evidence: n.a.", fact_lines={0: f0_line}, coverage=coverage), **NO_MENTION)

def test_f0_no_is_refused_for_a_client_construction_in_an_unnamed_file(tmp_path, lib):
    ev = _ev_with(tmp_path, {"Config.java": "class Config {\n  Object c = new TypeSafeJevClient(key);\n}\n",
                             "Other.java": "import com.typesafe.config.Config;\n"})
    r = _no_rating(tmp_path, "- F0 Calls hosted Jev -- no. Other.java only reads a config library and never calls out")
    code, out = _chk_ev(lib, r, ev)
    assert code != 0 and "Config.java" in out and "F0 is no" in out, out

def test_f0_no_naming_the_constructing_file_with_a_reason_passes(tmp_path, lib):
    ev = _ev_with(tmp_path, {"Config.java": "class Config {\n  Object c = new TypeSafeJevClient(key);\n}\n"})
    r = _no_rating(tmp_path, "- F0 Calls hosted Jev -- no. Config.java:2 builds a client that nothing ever calls")
    code, out = _chk_ev(lib, r, ev); assert "F0 is no" not in out, out


# --- Review fix 4 (2026-09-30): example folders and benchmark scripts are not the project calling Jev ---

BENCH_SRC = "const a = 1\n\n\n\nconst r = await evaluate({ model: \"typesafe-ai/jev\" })\n"

def test_f0_yes_citing_only_an_example_call_is_refused(tmp_path, lib):
    ev = _ev_with(tmp_path, {"src/x.py": "print('local model')\n", "examples/demo.ts": "import x\n\n\nconst client = new TypeSafeClient({});\nawait client.systemOne({})\n"})
    r = _uses(tmp_path, fact_lines={0: F0_YES.format("examples/demo.ts:5")})
    code, out = _chk_ev(lib, r, ev); assert code != 0 and "F0 cites examples/demo.ts:5" in out, out

def test_f0_yes_citing_only_a_benchmark_script_is_refused(tmp_path, lib):
    ev = _ev_with(tmp_path, {"src/x.py": "print('local model')\n", "scripts/bench.mjs": BENCH_SRC})
    r = _uses(tmp_path, fact_lines={0: F0_YES.format("scripts/bench.mjs:5")})
    code, out = _chk_ev(lib, r, ev); assert code != 0 and "F0 cites scripts/bench.mjs:5" in out, out

def test_f0_no_need_not_name_example_or_benchmark_files(tmp_path, lib):
    ev = _ev_with(tmp_path, {"src/x.py": "print('local model')\n", "examples/demo.ts": CALL_SRC, "benchmarks/cmp.py": CALL_SRC, "scripts/bench_jev.py": CALL_SRC})
    r = _no_rating(tmp_path, "- F0 Calls hosted Jev -- no. The app serves its own model and never sends a request out")
    code, out = _chk_ev(lib, r, ev); assert "F0 is no" not in out, out

def test_f0_yes_citing_a_call_in_a_demo_app_still_passes(tmp_path, lib):
    ev = _ev_with(tmp_path, {"demo/app.py": CALL_SRC, "src/x.py": "x = 1\n"})
    r = _uses(tmp_path, fact_lines={0: F0_YES.format("demo/app.py:4")})
    code, out = _chk_ev(lib, r, ev); assert "F0" not in out, out


# --- Review fix 1 (2026-09-30): an F0 yes cites a call, not an import, dependency, comment, throw or declaration ---

def _yes_ev(src_line, name="src/x.py"):
    return {name: "x = 1\n\n\n\n" + src_line + "\n", "src/client.py": "from typesafe import TypeSafeClient\nclient = TypeSafeClient(k)\n"}

@pytest.mark.parametrize("name,line", [("package.json", '  "@typesafe-ai/sdk": "^0.6.0"'), ("src/x.js", "throw new TypeSafeError('bad key')"),
                                       ("src/x.py", "# POST to https://api.typesafe.ai/v1/systemone"), ("src/x.ts", "  constructor(key: string) {  // TypeSafeClient"),
                                       ("src/X.java", "public TypeSafeClient(String key) {"), ("src/x.js", "const RX = /api.typesafe.ai/i;"),
                                       ("src/x.py", "from typesafe import TypeSafeClient")])
def test_f0_yes_citing_a_line_that_is_not_a_call_is_refused(tmp_path, lib, name, line):
    files = _yes_ev(line, name); ev = _ev_with(tmp_path, files)
    r = _uses(tmp_path, fact_lines={0: F0_YES.format(f"{name}:5")}, coverage="\n".join(f"- {p} -- read" for p in files))
    code, out = _chk_ev(lib, r, ev); assert code != 0 and f"F0 cites {name}:5" in out, out

def test_f0_refusal_does_not_tell_raters_an_import_is_the_call(tmp_path, lib):
    ev = _ev_with(tmp_path, {"src/x.py": CALL_SRC})
    r = _uses(tmp_path, fact_lines={0: F0_YES.format("src/x.py:3")})
    code, out = _chk_ev(lib, r, ev)
    assert code != 0 and "an import of" not in out and "imports a TypeSafe" not in out, out
    assert "creates the client" in out and "posts to api.typesafe.ai" in out and "names the" in out and "calls it" in out, out


# --- Review fix 2 (2026-09-30): a yes may cite any call expression in a file that holds a hosted marker ---

SEND_SHAPES = {
    "async": ("src/a.py", "import os\n\nfrom typesafe import AsyncTypeSafeClient\n\nclient = AsyncTypeSafeClient(api_key=KEY)\n", 5),
    "accessor": ("src/b.py", "from typesafe import TypeSafeClient\n\nclass Judge:\n    def _sync_client(self): return TypeSafeClient()\n        return self._sync_client().system_one(s, QS)\n", 5),
    "urlopen": ("src/c.py", "import urllib.request\nURL = 'https://api.typesafe.ai/v1/systemone'\nreq = urllib.request.Request(URL, data=b)\nwith urllib.request.urlopen(req) as r:\n    out = r.read()\n", 4)}

@pytest.mark.parametrize("shape", sorted(SEND_SHAPES))
def test_f0_yes_citing_a_send_line_passes(tmp_path, lib, shape):
    name, src, n = SEND_SHAPES[shape]
    ev = _ev_with(tmp_path, {name: src})
    r = _uses(tmp_path, fact_lines={0: F0_YES.format(f"{name}:{n}")}, coverage=f"- {name} -- read")
    code, out = _chk_ev(lib, r, ev); assert "F0" not in out, out

def test_f0_yes_citing_a_call_in_a_file_with_no_hosted_marker_is_refused(tmp_path, lib):
    ev = _ev_with(tmp_path, {"src/c.py": "import urllib.request\nreq = urllib.request.Request('https://example.com/x')\nwith urllib.request.urlopen(req) as r:\n    pass\n"})
    r = _uses(tmp_path, fact_lines={0: F0_YES.format("src/c.py:3")}, coverage="- src/c.py -- read")
    code, out = _chk_ev(lib, r, ev); assert code != 0 and "F0 cites src/c.py:3" in out, out


# --- F0 yes cited to a saved capture (2026-09-30) ---
CAPTURE = '{"model": "jev-1.13.0", "state": {"q": "x"}, "questions": [{"id": "a", "type": "noul"}], "answers": {"a": {"p_true": 0.8}}}'

@pytest.mark.parametrize("folder", ["captures", "responses"])
def test_f0_yes_accepts_a_saved_capture_beside_files(tmp_path, folder):
    import library
    ev = tmp_path / "ev"; (ev / "files").mkdir(parents=True); (ev / folder).mkdir()
    (ev / "files" / "app.js").write_text("fetch('/api/ask')\n")
    (ev / folder / "01.json").write_text(CAPTURE)
    err = []
    library.check_f0(f"- F0 Calls hosted Jev: yes. The saved response holds the request and typed answers ({folder}/01.json:1).", "yes", ev, err)
    assert err == []

def test_f0_yes_refuses_a_capture_without_questions(tmp_path):
    import library
    ev = tmp_path / "ev"; (ev / "files").mkdir(parents=True); (ev / "captures").mkdir()
    (ev / "files" / "app.js").write_text("fetch('/api/ask')\n")
    (ev / "captures" / "01.json").write_text('{"reply": "hello"}')
    err = []
    library.check_f0("- F0 Calls hosted Jev: yes (captures/01.json:1).", "yes", ev, err)
    assert err

def test_f0_yes_refuses_a_missing_capture(tmp_path):
    import library
    ev = tmp_path / "ev"; (ev / "files").mkdir(parents=True)
    (ev / "files" / "app.js").write_text("fetch('/api/ask')\n")
    err = []
    library.check_f0("- F0 Calls hosted Jev: yes (captures/09.json:1).", "yes", ev, err)
    assert err


# --- scoped review, 2026-09-30 ---
def test_f0_yes_refuses_any_call_in_a_file_that_only_imports_the_sdk(tmp_path):
    import library
    ev = tmp_path / "ev"; (ev / "files").mkdir(parents=True)
    (ev / "files" / "app.py").write_text("from typesafe import Client\n\n\ndef main():\n    foo()\n")
    err = []
    library.check_f0("- F0 Calls hosted Jev: yes (app.py:5).", "yes", ev, err)
    assert err

def test_f0_yes_accepts_a_module_call(tmp_path):
    import library
    ev = tmp_path / "ev"; (ev / "files").mkdir(parents=True)
    (ev / "files" / "app.py").write_text("import typesafe\n\n\ndef main(t):\n    return typesafe.noul(t)\n")
    err = []
    library.check_f0("- F0 Calls hosted Jev: yes (app.py:5).", "yes", ev, err)
    assert err == []

@pytest.mark.parametrize("name,text", [("snippet.py", "from typesafe import Client\n"), ("package.json", '{"dependencies": {"@typesafe-ai/sdk": "^1.0.0"}}\n')])
def test_a_guide_with_only_an_import_or_dependency_passes(tmp_path, name, text):
    import library
    ev = tmp_path / "ev"; (ev / "files").mkdir(parents=True)
    (ev / "files" / name).write_text(text)
    err = []
    library.check_guide_code("n.a.", ev, err)
    assert err == []


# --- audit, 2026-09-30: rated must be a date, never a path ---
@pytest.mark.parametrize("bad", ["../../../x", "2026-09-30/../../y", "latest"])
def test_add_refuses_a_rated_value_that_is_not_a_date(tmp_path, bad):
    import library
    d = {"project": "P", "owner": "o", "rated": bad, "verdict": "3"}
    with pytest.raises(SystemExit) as e:
        library.require_date(d)
    assert "rated" in str(e.value)

def test_add_accepts_a_date():
    import library
    library.require_date({"rated": "2026-09-30"})
