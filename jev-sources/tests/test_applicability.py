"""Which Jev model a section needs, and whether TypeSafe calls it not production-ready (B13)."""
import importlib, json, os, re, subprocess, sys
import pytest
CODE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(CODE, "scripts"))
REAL = os.environ.get("JEV_SOURCES_DATA") or os.path.expanduser("~/.claude/jev-sources-data")  # the library the suite was pointed at

BOX_PAGE = ("# Box\n\nUse a Box to find where something is in an image, like a mug. A mug photo location answer.\n\n"
            "Box questions need Jev 1.14: send `jev-preview` or `jev-1.14.0` as the `model`.\n")
IMG_PAGE = ("# Images\n\nSend a photo of a mug in a request. Where the mug is in a photo depends on the picture.\n\n"
            "Jev 1.13 and Jev 1.14 both accept images.\n")
STATE_PAGE = ("# State\n\nThe state holds the facts a mug question is asked about. A photo can sit in the state.\n")


def _reload():
    pytest.importorskip("numpy")  # semantic.py needs it; the library fixtures reload semantic
    import paths, pages, semantic, route, build_index, route_check, check_new, applicability
    for m in (paths, pages, applicability, semantic, route, build_index, route_check, check_new):
        importlib.reload(m)
    return route, applicability, check_new


@pytest.fixture
def lib(tmp_path, monkeypatch):
    monkeypatch.setenv("JEV_SOURCES_DATA", str(tmp_path))
    monkeypatch.setenv("JEV_SEMANTIC", "off")
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "primitives__box.md").write_text(BOX_PAGE)
    (docs / "images.md").write_text(IMG_PAGE)
    (docs / "concepts__state.md").write_text(STATE_PAGE)
    subprocess.run([sys.executable, os.path.join(CODE, "scripts", "build_index.py")], check=True, capture_output=True)
    yield _reload()
    monkeypatch.undo()
    _reload()


ENTRIES = [
    {"match": "docs/p.md", "needs": "jev-1.13.0", "status": None, "source": "docs/p.md#A", "quote": "q"},
    {"match": "docs/p.md#B", "needs": "jev-1.14.0", "status": "experimental", "source": "docs/p.md#B", "quote": "q"},
]


def test_lookup_gives_page_and_heading_entries_and_a_heading_wins(lib):
    _, A, _ = lib
    assert A.lookup("docs/p.md", "A", ENTRIES)["needs"] == "jev-1.13.0"
    assert A.lookup("docs/p.md", "B", ENTRIES)["needs"] == "jev-1.14.0"
    assert A.lookup("docs/p.md", "B", ENTRIES)["status"] == "experimental"


def test_lookup_of_an_unlisted_page_gives_nones(lib):
    _, A, _ = lib
    assert A.lookup("docs/other.md", "X", ENTRIES) == {"needs": None, "status": None, "source": None, "quote": None, "note": None}


def test_real_box_page_needs_1_14_and_is_experimental(lib):
    _, A, _ = lib
    e = A.lookup("docs/primitives__box.md", "Box")
    assert e["needs"] == "jev-1.14.0" and e["status"] == "experimental"


def test_allowed_compares_versions_and_resolves_aliases(lib):
    _, A, _ = lib
    box, img = A.lookup("docs/primitives__box.md", "Box"), A.lookup("docs/images.md", "Images")
    assert not A.allowed(box, "jev-1.13.0")
    assert A.allowed(box, "jev-preview")
    assert A.allowed(box, "jev-1.14")          # pads to three integers
    assert A.allowed(box, "jev-1.14.0")
    assert A.allowed(img, "jev-1.13.0")        # images need only 1.13
    assert not A.allowed(box, "jev-latest")    # jev-latest points at 1.13.0
    assert A.allowed(box, None)                # no model known: nothing is ruled out
    assert A.allowed({"needs": None}, "jev-1.13.0")


def test_latest_alias_follows_the_aliases_table(lib):
    _, A, _ = lib
    A.ALIASES["jev-latest"] = "jev-1.14.0"
    assert A.allowed(A.lookup("docs/primitives__box.md", "Box"), "jev-latest")


def test_uncovered_flags_a_page_with_a_limit_and_no_entry(lib):
    _, A, _ = lib
    pages = {"docs/new.md": "Sending video: need Jev 1.15 for this.", "docs/new2.md": "**Dreamer-ready.** try it",
             "docs/plain.md": "Nothing to see.", "docs/primitives__box.md": "Box questions need Jev 1.14"}
    assert A.uncovered(pages) == ["docs/new.md", "docs/new2.md"]


def test_every_seeded_quote_is_in_its_source_section():
    """Reads the real library: a docs change that drops a quote fails here, and applicability.json gets re-read."""
    sections = os.path.join(REAL, "sections.jsonl")
    if not os.path.exists(sections):
        pytest.skip("real library not present")
    import applicability as A
    rows = {(r["path"], r["heading"]): r for r in map(json.loads, open(sections))}
    for e in A.entries():
        for src, quote in A.quotes(e):
            path, head = src.split("#", 1)
            if (path, head) not in rows:
                pytest.fail(f"{e['match']}: source section {src} not in the library")
            r = rows[(path, head)]
            text = " ".join(open(os.path.join(REAL, path), encoding="utf-8").read().split("\n")[r["line_start"] - 1:r["line_end"]])
            assert re.sub(r"\s+", " ", quote) in re.sub(r"\s+", " ", text), (e["match"], quote)


def test_jev_latest_alias_still_points_where_ALIASES_says():
    sections = os.path.join(REAL, "sections.jsonl")
    if not os.path.exists(sections):
        pytest.skip("real library not present")
    import applicability as A
    r = next(x for x in map(json.loads, open(sections)) if x["path"] == "docs/models.md" and x["heading"] == "Aliases")
    text = "\n".join(open(os.path.join(REAL, "docs/models.md"), encoding="utf-8").read().split("\n")[r["line_start"] - 1:r["line_end"]])
    for alias, target in A.ALIASES.items():
        assert re.search(r"`%s`\s*\|\s*`%s`" % (re.escape(alias), re.escape(target)), text), (alias, target)


def _by_path(res):
    return {s["path"]: s for s in res["sections"]}


def test_route_labels_needs_and_experimental(lib):
    R, _, _ = lib
    s = _by_path(R.route("where is the mug in a photo"))["docs/primitives__box.md"]
    assert s["needs"] == "jev-1.14.0" and s["status"] == "experimental"
    assert _by_path(R.route("where is the mug in a photo"))["docs/concepts__state.md"]["needs"] is None


def test_route_with_an_older_model_keeps_the_section_but_lists_it_last(lib):
    R, _, _ = lib
    res = R.route("where is the mug in a photo", model="jev-1.13.0")
    paths = [s["path"] for s in res["sections"]]
    assert "docs/primitives__box.md" in paths and paths[-1] == "docs/primitives__box.md"
    assert res["model"] == "jev-1.13.0"


def test_route_without_a_model_does_not_reorder(lib):
    R, _, _ = lib
    base = [s["path"] for s in R.route("where is the mug in a photo")["sections"]]
    assert base == [s["path"] for s in R.route("where is the mug in a photo")["sections"]]
    assert [s["path"] for s in R.route("where is the mug in a photo", model="jev-1.14.0")["sections"]] == base


def test_a_model_id_in_the_question_sets_the_model(lib):
    R, _, _ = lib
    res = R.route("on jev-1.13.0, where is the mug in a photo")
    assert res["model"] == "jev-1.13.0"
    assert res["sections"][-1]["path"] == "docs/primitives__box.md"
    assert R.route("where is the mug in a photo")["model"] is None


def test_an_explicit_model_beats_one_in_the_question(lib):
    R, _, _ = lib
    assert R.route("on jev-1.13.0, where is the mug", model="jev-preview")["model"] == "jev-preview"


def test_each_section_records_how_it_was_found(lib):
    R, _, _ = lib
    assert {s["by"] for s in R.route("where is the mug in a photo")["sections"]} == {"keyword"}


def test_route_lines_carry_the_labels(lib):
    out = subprocess.run([sys.executable, os.path.join(CODE, "scripts", "route.py"), "--model", "jev-1.13.0",
                          "where is the mug in a photo"], capture_output=True, text=True, check=True,
                         env=dict(os.environ, JEV_SOURCES_DATA=os.environ["JEV_SOURCES_DATA"], JEV_LOG="off", JEV_SEMANTIC="off")).stdout
    box = [l for l in out.splitlines() if "primitives__box.md" in l and "|" in l][0]
    assert "NEEDS jev-1.14.0" in box
    assert "EXPERIMENTAL: TypeSafe says not production-ready" in box
    img = [l for l in out.splitlines() if "images.md" in l and "|" in l][0]
    assert "NEEDS" not in img and "EXPERIMENTAL" in img
    assert out.index("concepts__state.md") < out.index("primitives__box.md")


def test_read_prints_an_applies_line_under_the_source_line(lib, tmp_path):
    sid = next(json.loads(l)["id"] for l in open(tmp_path / "sections.jsonl") if "primitives__box" in l)
    out = subprocess.run([sys.executable, os.path.join(CODE, "scripts", "read.py"), sid], capture_output=True, text=True, check=True,
                         env=dict(os.environ, JEV_LOG="off", JEV_SOURCES_DATA=str(tmp_path))).stdout.splitlines()
    assert out[0].startswith("SOURCE: docs/primitives__box.md#Box")
    assert out[1] == "APPLIES: needs jev-1.14.0 or newer | experimental (docs/primitives__box.md#Box)"


def test_read_of_an_unlabeled_section_has_no_applies_line(lib, tmp_path):
    sid = next(json.loads(l)["id"] for l in open(tmp_path / "sections.jsonl") if "concepts__state" in l)
    out = subprocess.run([sys.executable, os.path.join(CODE, "scripts", "read.py"), sid], capture_output=True, text=True, check=True,
                         env=dict(os.environ, JEV_LOG="off", JEV_SOURCES_DATA=str(tmp_path))).stdout
    assert "APPLIES:" not in out


def test_after_change_names_a_new_page_with_a_limit_and_no_entry(lib, tmp_path):
    _, _, CN = lib
    (tmp_path / "docs" / "video.md").write_text("# Video\n\nVideo questions need Jev 1.15.\n")
    lines = CN.after_change({"added": ["video"], "changed": ["primitives/box"]})
    assert any("1 new page(s) state a model or readiness limit not yet in applicability.json: docs/video.md" in l for l in lines)


def test_after_change_is_quiet_when_every_limit_has_an_entry(lib):
    _, _, CN = lib
    out = CN.after_change({"changed": ["primitives/box"]})
    assert not any("applicability.json" in l for l in out), out


# --- fix round 1 ---
def test_python_assets_page_is_experimental_and_needs_1_13(lib):
    _, A, _ = lib
    e = A.lookup("docs/sdk__python__api__types__assets.md", "Assets")
    assert e["needs"] == "jev-1.13.0" and e["status"] == "experimental" and e["source"].startswith("docs/images.md#")


def test_python_basic_usage_is_part_experimental_with_its_own_quote(lib):
    _, A, _ = lib
    e = A.lookup("docs/sdk__python__usage__basic.md", "Basic usage")
    assert e["status"] == "part-experimental" and e["quote"] == "image support is only dreamer-ready"
    assert A.allowed(e, "jev-1.13.0")


def test_js_box_function_page_is_experimental(lib):
    _, A, _ = lib
    assert A.lookup("docs/sdk__javascript__api__functions__box.md", "Function: box()")["status"] == "experimental"


def test_long_context_note_keeps_to_its_pages_words(lib):
    _, A, _ = lib
    e = A.lookup("docs/models.md", "Long context")
    assert "not production-ready" not in e["note"] and "slower and less accurate" in e["note"]


def test_lookup_note_is_none_without_one(lib):
    _, A, _ = lib
    assert A.lookup("docs/primitives__box.md", "Box")["note"] is None


def _run_route(args, tmp_path):
    return subprocess.run([sys.executable, os.path.join(CODE, "scripts", "route.py")] + args, capture_output=True, text=True,
                          env=dict(os.environ, JEV_LOG="off", JEV_SEMANTIC="off", JEV_SOURCES_DATA=str(tmp_path)))


def test_long_context_line_does_not_say_not_production_ready(lib, tmp_path):
    (tmp_path / "docs" / "models.md").write_text("# Models\n\n## Long context\n\nLong context is off by default. Send the `TypeSafe-Danger-Zone-Long-Context: true` header. It is slower and less accurate.\n")
    subprocess.run([sys.executable, os.path.join(CODE, "scripts", "build_index.py")], check=True, capture_output=True,
                   env=dict(os.environ, JEV_SOURCES_DATA=str(tmp_path)))
    out = _run_route(["long context header"], tmp_path).stdout
    line = [l for l in out.splitlines() if "models.md#Long context" in l][0]
    assert "EXPERIMENTAL" in line and "not production-ready" not in line and "slower and less accurate" in line


def test_part_experimental_line_and_applies_line(lib, tmp_path):
    (tmp_path / "docs" / "sdk__python__usage__basic.md").write_text("# Basic usage\n\nSend a python client request with an image.\n\nimage support is only dreamer-ready.\n")
    subprocess.run([sys.executable, os.path.join(CODE, "scripts", "build_index.py")], check=True, capture_output=True,
                   env=dict(os.environ, JEV_SOURCES_DATA=str(tmp_path)))
    out = _run_route(["--model", "jev-1.13.0", "python client basic usage"], tmp_path).stdout
    line = [l for l in out.splitlines() if "sdk__python__usage__basic.md" in l and "|" in l][0]
    assert "PART EXPERIMENTAL: TypeSafe says image support is not production-ready" in line and "NEEDS" not in line
    sid = next(json.loads(l)["id"] for l in open(tmp_path / "sections.jsonl") if "usage__basic" in l)
    read = subprocess.run([sys.executable, os.path.join(CODE, "scripts", "read.py"), sid], capture_output=True, text=True,
                          env=dict(os.environ, JEV_LOG="off", JEV_SOURCES_DATA=str(tmp_path))).stdout.splitlines()
    assert read[1] == "APPLIES: part experimental (docs/sdk__python__usage__basic.md#Attaching Media Assets)"


def test_part_experimental_section_is_never_reordered(lib):
    R, _, _ = lib
    base = [s["path"] for s in R.route("where is the mug in a photo")["sections"]]
    res = R.route("where is the mug in a photo", model="jev-1.13.0")
    assert all(s["status"] != "part-experimental" or s["path"] in base for s in res["sections"])


def test_unparseable_model_warns_and_is_ignored(lib, tmp_path):
    r = _run_route(["--model", "gpt-4", "where is the mug in a photo"], tmp_path)
    assert r.returncode == 0 and "warning" in r.stderr and "gpt-4" in r.stderr and "Model:" not in r.stdout


def test_model_flag_without_a_value_warns(lib, tmp_path):
    r = _run_route(["where is the mug in a photo", "--model"], tmp_path)
    assert r.returncode == 0 and "--model" in r.stderr and "warning" in r.stderr and "Question:" in r.stdout


def test_several_models_in_a_question_use_the_oldest(lib):
    _, A, _ = lib
    assert A.find_model("what does jev-1.14.0 add over jev-1.13.0") == "jev-1.13.0"
    assert A.find_model("jev-preview versus jev-latest") == "jev-latest"
    assert A.find_model("no model here") is None
