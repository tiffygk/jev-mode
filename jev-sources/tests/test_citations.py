import importlib, json, os, sys
import pytest
CODE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(CODE, "scripts"))


def _reload():
    import paths, pages, citations, check_new
    for m in (paths, pages, citations, check_new):
        importlib.reload(m)
    return citations, check_new


@pytest.fixture(autouse=True)
def lib(tmp_path, monkeypatch):
    """Every test: a temp library and a temp repo, never the real ones. Modules reload with them and again at teardown."""
    data = tmp_path / "data"
    data.mkdir()
    monkeypatch.setenv("JEV_SOURCES_DATA", str(data))
    mods = _reload()
    yield tmp_path, data, mods
    monkeypatch.undo()
    _reload()


def put(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(text)


def library(data, changes, sections):
    put(str(data / "section_changes.json"), json.dumps(changes))
    put(str(data / "sections.jsonl"),
        "".join(json.dumps({"id": i, "path": p, "heading": h}) + "\n" for i, (p, h) in enumerate(sections)))


def fake_near(table):
    """near(query, only_slug, only_added) -> the target of the first table key found in the query."""
    def near(query, only_slug=None, only_added=False):
        for key, (target, needs_added) in table.items():
            if key in query and (only_added or not needs_added):
                return target
        return None
    return near


def by_file(rows):
    return {(r["file"], r["cites"]): r for r in rows}


def test_fake_repo_rows_are_classed(lib):
    tmp, data, (C, _) = lib
    repo = tmp / "repo"
    os.makedirs(str(repo / "jevaluate"))  # a full checkout, not a plugin install
    put(str(repo / "jev-sources" / "SKILL.md"), "See `docs/models.md#Rate limits` for caps.\nUse `models` and `confidence-level`.\n")
    put(str(repo / "README.md"), "Docs: https://docs.typesafe.ai/sdk/python/usage\n")
    put(str(repo / "jev-sources" / "q.json"), '{"cite": "docs/primitives.md#When one question depends on another"}\n')
    put(str(repo / "ratings" / "2026-10-01.md"), "Cited docs/sdk__javascript__api__functions__noul.md in the review.\n")
    library(data, {"date": "2026-10-14", "changed": ["models"], "added": [], "removed": ["sdk/javascript/api/functions/noul"],
                   "moved": {"sdk/python/usage": "sdk/python/usage/basic"},
                   "removed_sections": [["docs/models.md", "Rate limits"]], "added_sections": [["docs/models.md", "Request limits"]]},
            [("docs/models.md", "Request limits"), ("docs/primitives.md", "When one question depends on another")])
    rows, path = C.report(str(repo), near=fake_near({"Rate limits": ("models#Request limits", False)}))
    got = by_file(rows)
    skill = got[(os.path.join("jev-sources", "SKILL.md"), "models#Rate limits")]
    assert (skill["class"], skill["replacement"]) == ("superseded", "models#Request limits")
    readme = got[("README.md", "sdk/python/usage")]
    assert (readme["class"], readme["replacement"]) == ("superseded", "sdk/python/usage/basic")
    rating = got[(os.path.join("ratings", "2026-10-01.md"), "sdk/javascript/api/functions/noul")]
    assert rating["class"] == "obsolete" and rating["note"] == "dated record: flag only"
    assert got[(os.path.join("jev-sources", "SKILL.md"), "models")]["class"] == "changed"
    assert not any("primitives" in r["cites"] for r in rows)
    assert not any("confidence-level" in r["cites"] for r in rows)
    assert os.path.basename(path) == "STALE_CITATIONS.md" and os.path.dirname(path) == str(data)
    assert "sdk/python/usage/basic" in open(path).read()


def real_shape(data, added):
    library(data, {"date": "2026-10-14", "changed": ["models"], "added": [], "removed": [], "moved": {}, "removed_sections": [],
                   "added_sections": [["docs/models.md", "Rate limits"]] if added else []},
            [("docs/models.md", "Current models")] + ([("docs/models.md", "Rate limits")] if added else []))


def kept_section_repo(tmp):
    repo = tmp / "repo"
    put(str(repo / "jev-sources" / "SKILL.md"), "Price and rate limits are in `docs/models.md#Current models`\n")
    return repo


def test_kept_section_is_superseded_by_a_section_the_refresh_added(lib):
    tmp, data, (C, _) = lib
    real_shape(data, True)
    rows, _ = C.report(str(kept_section_repo(tmp)), near=fake_near({"rate limits": ("models#Rate limits", True)}))
    assert [(r["class"], r["replacement"]) for r in rows] == [("superseded", "models#Rate limits")]


def test_kept_section_on_a_changed_page_is_only_changed_when_nothing_was_added(lib):
    tmp, data, (C, _) = lib
    real_shape(data, False)
    rows, _ = C.report(str(kept_section_repo(tmp)), near=fake_near({"rate limits": ("models#Rate limits", True)}))
    assert [(r["class"], r["replacement"]) for r in rows] == [("changed", "models#Current models")]


def test_heading_captured_past_its_end_is_cut_back_to_the_known_heading(lib):
    tmp, data, (C, _) = lib
    real_shape(data, False)
    repo = tmp / "repo"
    put(str(repo / "jev-sources" / "SKILL.md"), "Read `docs/models.md#Current models (reference rule)` first.\n")
    rows, _ = C.report(str(repo), near=fake_near({}))
    assert [(r["cites"], r["class"]) for r in rows] == [("models#Current models", "changed")]


def test_heading_cut_back_also_finds_a_removed_heading(lib):
    tmp, data, (C, _) = lib
    library(data, {"date": "d", "changed": ["models"], "removed": [], "moved": {}, "added_sections": [],
                   "removed_sections": [["docs/models.md", "Rate limits"]]}, [("docs/models.md", "Current models")])
    repo = tmp / "repo"
    put(str(repo / "jev-sources" / "SKILL.md"), "Read `docs/models.md#Rate limits and quotas` first.\n")
    rows, _ = C.report(str(repo), near=fake_near({}))
    assert [(r["cites"], r["class"]) for r in rows] == [("models#Rate limits", "obsolete")]


def test_plugin_install_scans_only_the_skill_folder(lib):
    tmp, data, (C, _) = lib
    real_shape(data, False)
    repo = tmp / "repo"  # no jevaluate/ folder: a plugin install
    put(str(repo / "jev-sources" / "SKILL.md"), "Use `models`.\n")
    put(str(repo / "README.md"), "Use `models`.\n")
    rows, _ = C.report(str(repo), near=fake_near({}))
    assert [r["file"] for r in rows] == [os.path.join("jev-sources", "SKILL.md")]
    os.makedirs(str(repo / "jevaluate"))
    rows, _ = C.report(str(repo), near=fake_near({}))
    assert sorted(r["file"] for r in rows) == ["README.md", os.path.join("jev-sources", "SKILL.md")]


def test_plugin_install_in_a_versioned_folder_still_scans_the_skill_itself(lib, monkeypatch):
    tmp, data, (C, _) = lib
    real_shape(data, False)
    skill = tmp / "cache" / "1.14.0"  # not named jev-sources, no repo around it
    put(str(skill / "SKILL.md"), "Use `models`.\n")
    monkeypatch.setattr(C, "CODE", str(skill))
    rows, _ = C.report(near=fake_near({}))
    assert [r["file"] for r in rows] == ["SKILL.md"]


def test_nearest_names_the_best_row_above_the_floor_and_none_below(lib, monkeypatch):
    import types
    _, _, (C, _) = lib
    rows = [{"id": 0, "path": "docs/a.md", "heading": "A"}, {"id": 1, "path": "docs/b.md", "heading": "B"}]
    fake = types.ModuleType("semantic")
    fake.scores = lambda q, r: ({0: 0.1, 1: 0.8}, None)
    monkeypatch.setitem(sys.modules, "semantic", fake)
    assert C.nearest("q", rows) == "b#B"
    fake.scores = lambda q, r: ({0: 0.1, 1: 0.2}, None)
    assert C.nearest("q", rows) is None
    def boom(q, r):
        raise RuntimeError("no index")
    fake.scores = boom
    assert C.nearest("q", rows) is None


def test_after_change_points_to_the_report(lib, monkeypatch):
    _, data, (C, CN) = lib
    monkeypatch.setattr(C, "report", lambda root=None, near=None: ([{"x": 1}], str(data / "STALE_CITATIONS.md")))
    assert f"1 citation(s) to check: {data / 'STALE_CITATIONS.md'}." in CN.after_change({})


def test_after_change_survives_a_failing_report(lib, monkeypatch):
    _, _, (C, CN) = lib
    def boom(*a, **k):
        raise RuntimeError("x")
    monkeypatch.setattr(C, "report", boom)
    assert isinstance(CN.after_change({}), list)


def test_after_change_is_quiet_without_a_changes_file(lib):
    _, data, (_, CN) = lib
    assert not os.path.exists(str(data / "section_changes.json"))
    assert not any("itation" in l for l in CN.after_change({}))
    assert not os.path.exists(str(data / "STALE_CITATIONS.md"))


def test_an_explicit_root_with_neither_skill_is_refused(lib):
    tmp, data, (C, _) = lib
    real_shape(data, False)
    with pytest.raises(SystemExit):
        C.report(str(tmp / "typo"), near=fake_near({}))
