"""build_index.health: NOTICE lines for sections that still look like site code, on invented pages in a temp library."""
import os, sys
import pytest

CODE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(CODE, "scripts")
HEAD = "<!-- saved 2026-10-15T09:00:00Z from https://docs.typesafe.ai/x.md | cleaner %s -->\n\n"


@pytest.fixture
def B(tmp_path, monkeypatch):
    monkeypatch.setenv("JEV_SOURCES_DATA", str(tmp_path))
    monkeypatch.setenv("JEV_SEMANTIC", "off")
    monkeypatch.syspath_prepend(SCRIPTS)
    for n in ("paths", "build_index", "jev", "route", "clean", "pages"):
        sys.modules.pop(n, None)
    import build_index
    return build_index


def rows_for(B, tmp_path, name, text, cleaner="1"):
    p = tmp_path / "docs" / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text((HEAD % cleaner if cleaner else "") + text)
    return B.sections("docs/" + name)


CLEAN = "# Models\n\nSome prose about models.\n\n## Limits\n\nMore prose, one short line.\n"


def test_a_cleaned_page_raises_no_notice(B, tmp_path):
    assert B.health(rows_for(B, tmp_path, "m.md", CLEAN)) == []


def test_ten_code_shaped_lines_in_a_section_are_flagged(B, tmp_path):
    text = "# Widget\n\n" + "\n".join("const a%d = () => 1;" % i for i in range(10)) + "\n"
    out = B.health(rows_for(B, tmp_path, "w.md", text))
    assert len(out) == 1 and out[0].startswith("NOTICE: code-shaped lines: docs/w.md#Widget (10")


def test_nine_code_shaped_lines_are_not_flagged(B, tmp_path):
    text = "# Widget\n\n" + "\n".join("const a%d = () => 1;" % i for i in range(9)) + "\n"
    assert B.health(rows_for(B, tmp_path, "w.md", text)) == []


def test_a_line_over_1000_characters_is_flagged(B, tmp_path):
    out = B.health(rows_for(B, tmp_path, "l.md", "# Long\n\n" + "x" * 1001 + "\n"))
    assert len(out) == 1 and out[0].startswith("NOTICE: long line: docs/l.md#Long (1001")


def test_a_line_of_exactly_1000_characters_is_not_flagged(B, tmp_path):
    assert B.health(rows_for(B, tmp_path, "l.md", "# Long\n\n" + "x" * 1000 + "\n")) == []


def test_a_leftover_html_heading_is_flagged(B, tmp_path):
    out = B.health(rows_for(B, tmp_path, "h.md", "# Page\n\n<h2 id=\"a.b\">A</h2>\n\nText.\n"))
    assert len(out) == 1 and out[0].startswith("NOTICE: html heading: docs/h.md#Page")


def test_an_html_heading_inside_a_code_fence_is_not_flagged(B, tmp_path):
    assert B.health(rows_for(B, tmp_path, "h.md", "# Page\n\n```html\n<h2 id=\"a\">A</h2>\n```\n")) == []


def test_a_section_over_the_cap_is_flagged(B, tmp_path):
    body = "\n".join("word " * 15 for _ in range(3200))  # 3200 lines of 75 chars: over 12,000 tokens, no long line
    out = B.health(rows_for(B, tmp_path, "big.md", "# Big\n\n" + body + "\n"))
    assert len(out) == 1 and out[0].startswith("NOTICE: section over the cap: docs/big.md#Big (")


def test_a_failed_clean_is_flagged(B, tmp_path):
    out = B.health(rows_for(B, tmp_path, "f.md", CLEAN, cleaner="failed 1"))
    assert len(out) == 1 and out[0].startswith("NOTICE: cleaner: docs/f.md") and "failed" in out[0]


def test_a_missing_or_older_cleaner_version_is_flagged(B, tmp_path):
    out = B.health(rows_for(B, tmp_path, "o.md", CLEAN, cleaner=""))
    assert len(out) == 1 and out[0].startswith("NOTICE: cleaner: docs/o.md") and "missing" in out[0]
    import clean
    old = str(clean.VERSION - 1)
    out = B.health(rows_for(B, tmp_path, "p.md", CLEAN, cleaner=old))
    assert len(out) == 1 and "older" in out[0]


def test_output_is_capped_at_ten_lines_plus_a_count(B, tmp_path):
    rows = []
    for i in range(14):
        rows += rows_for(B, tmp_path, "p%02d.md" % i, "# P%d\n\n" % i + "x" * 1001 + "\n")
    out = B.health(rows)
    assert len(out) == 11 and out[-1] == "and 4 more"
