"""Tests for library.py: run the script via subprocess against a temp JEVALUATE_LIBRARY."""
import os
import pathlib
import shutil
import subprocess
import sys

import pytest

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


def make_rating(path, project, owner, url, rated, commit="abc123def456789", verdict=4,
                 scores="execution: 3, fit: 3, coverage: 3, evidence: 2", via="direct",
                 depth="full", rubric="2026-09-28b", drop=(), coverage=None, fact_lines=None,
                 core_fixes=None, summary="Test fixture rating for library tests."):
    fm = {"project": project, "url": url, "owner": owner, "rated": rated, "rubric": rubric,
          "commit": commit, "depth": depth, "lineage": "new",
          "stages": "[data-prep, question-state, execution, decision]", "closes_loop": "none",
          "verdict": verdict, "scores": "{" + scores + "}", "via": via, "project_type": "sdk",
          "rater": "claude-sonnet-5-5", "effort": "medium"}
    for k in drop:
        fm.pop(k, None)
    fl = {n: f"- F{n} check{n} — yes. evidence:{n}" for n in range(0, 24)}
    fl.update(fact_lines or {})
    text = "---\n" + "\n".join(f"{k}: {v}" for k, v in fm.items()) + "\n---\n"
    text += f"## Summary\n{summary}\n## Facts (with evidence)\n" + "\n".join(fl[n] for n in sorted(fl)) + "\n"
    if coverage is not None:
        text += "## Coverage\n" + coverage + "\n"
    text += "## Verdict and reasoning\nTest fixture.\n"
    if core_fixes is not None:
        text += "## Core fixes\n" + core_fixes + "\n"
    path.write_text(text)
    return path


def make_evidence(tmp_path, files=("a.py", "b.py")):
    ev = tmp_path / "ev"; ev.mkdir(exist_ok=True)
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
    evdir.mkdir(parents=True)
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


def test_add_numbers_after_highest_same_day_and_keeps_evidence_separate(tmp_path, lib):
    d = lib / "projects" / "o__n"; d.mkdir(parents=True)
    make_rating(d / "2026-09-28-2.md", "N", "o", "https://github.com/o/n", "2026-09-28")
    old_ev = d / "2026-09-28-evidence"; old_ev.mkdir(); (old_ev / "manifest.md").write_text("OLD\n")
    ev = tmp_path / "ev"; ev.mkdir(); (ev / "manifest.md").write_text("# m\n")
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
                    fact_lines={0: f"- F0 Calls hosted Jev — {f0}. src/x.py:1; no file would answer it. https://docs.typesafe.ai/introduction/quickstart.md"})
    p = run(lib, "check", str(r))
    assert (p.returncode == 0) == ok, p.stdout + p.stderr
    if not ok: assert "F0" in p.stdout + p.stderr and "verdict" in (p.stdout + p.stderr).lower()


def test_check_requires_f0_under_current_rubric(tmp_path, lib):
    r = make_rating(tmp_path / "r.md", "P", "o", "https://github.com/o/p", "2026-09-28")
    text = r.read_text().replace("- F0 check0 — yes. evidence:0\n", ""); r.write_text(text)
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
    assert run(lib, "add", str(r)).returncode == 0, "fixture"
    out = tmp_path / "out"; assert run(lib, "export", str(out)).returncode == 0
    assert "Verdict 1: Not a Jev integration" in (out / "o__imit.md").read_text()


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


def run_default(home, *args):
    env = dict(os.environ)
    env.pop("JEVALUATE_LIBRARY", None)
    env["HOME"] = str(home)
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, env=env)


def test_default_library_is_harness_neutral(tmp_path):
    r = run_default(tmp_path, "index")
    assert r.returncode == 0, r.stderr
    assert (tmp_path / ".jevaluate-library" / "index.md").exists()
    assert not (tmp_path / ".claude").exists()


def test_default_library_keeps_existing_claude_library(tmp_path):
    old = tmp_path / ".claude" / "jevaluate-library"
    old.mkdir(parents=True)
    r = run_default(tmp_path, "index")
    assert r.returncode == 0, r.stderr
    assert (old / "index.md").exists()
    assert not (tmp_path / ".jevaluate-library").exists()
