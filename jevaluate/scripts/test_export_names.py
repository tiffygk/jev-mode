"""Export (2026-10-06 retro): one name per project across raters, a reviewable leave-out list, and two locks that keep
private ratings out of the public ratings folder."""
import pathlib
from test_library import make_rating, run


def rater(p, model):
    p = pathlib.Path(p); p.write_text(p.read_text().replace("rater: claude-sonnet-5-5", f"rater: {model}"))
    return p


def two_raters(lib, owner, repo, sonnet_name, sol_name):
    slug = f"{owner}__{repo}"; d = lib / "projects" / slug; d.mkdir(parents=True)
    make_rating(d / "2026-09-30.md", sonnet_name, owner, f"https://github.com/{owner}/{repo}", "2026-09-30")
    rater(make_rating(d / "2026-10-06.md", sol_name, owner, f"https://github.com/{owner}/{repo}", "2026-10-06"), "gpt-6-sol")
    return slug


def test_every_rater_row_uses_the_projects_published_name(tmp_path):
    lib = tmp_path / "lib"; slug = two_raters(lib, "altryne", "jevify", "Jevify", "jevify")
    out = tmp_path / "out"; p = run(lib, "export", str(out))
    assert p.returncode == 0, p.stdout + p.stderr
    rows = [l for l in (out / "README.md").read_text().splitlines() if l.startswith("| [altryne/Jevify](")]
    assert len(rows) == 1 and "Sonnet 5.5:" in rows[0] and "GPT-6 Sol:" in rows[0], rows
    assert "**altryne/Jevify**" in (out / f"{slug}--gpt-6-sol.md").read_text()


def test_left_out_project_drops_every_raters_page(tmp_path):
    lib = tmp_path / "lib"; slug = two_raters(lib, "dbreunig", "building-with-jev-skill", "building-with-jev-skill", "building-with-jev-skill")
    make_rating(tmp_path / "keep.md", "Keep", "o", "https://github.com/o/keep", "2026-09-30")
    assert run(lib, "add", str(tmp_path / "keep.md")).returncode == 0
    out = tmp_path / "out"; p = run(lib, "export", str(out))
    assert p.returncode == 0, p.stdout + p.stderr
    assert not list(out.rglob(f"{slug}*.md")) and slug not in (out / "README.md").read_text()
    assert f"left out: {slug} (" in p.stderr and f"left out: {slug}--gpt-6-sol (" in p.stderr
    assert (out / "o__keep.md").exists()


def test_private_rating_in_public_library_refuses_export(tmp_path):
    lib = tmp_path / "lib"; d = lib / "projects" / "o__secret"; d.mkdir(parents=True)
    r = make_rating(d / "2026-10-06.md", "Secret", "o", "https://github.com/o/secret", "2026-10-06")
    r.write_text(r.read_text().replace("rater: claude-sonnet-5-5", "rater: claude-sonnet-5-5\nvisibility: private"))
    out = tmp_path / "out"; p = run(lib, "export", str(out))
    assert p.returncode != 0 and "private ratings in a public library" in p.stderr and "o__secret" in p.stderr
    assert not out.exists()


def test_private_library_refuses_export(tmp_path):
    lib = tmp_path / "lib"; d = lib / "projects" / "o__x"; d.mkdir(parents=True)
    make_rating(d / "2026-10-06.md", "X", "o", "https://github.com/o/x", "2026-10-06")
    (lib / "PRIVATE").write_text("private library\n")
    out = tmp_path / "out"; p = run(lib, "export", str(out))
    assert p.returncode != 0 and "private library" in p.stderr and not out.exists()
