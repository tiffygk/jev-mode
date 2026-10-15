"""jev.py: one call that routes a question in two phrasings and reads every READ FULL section in order, up to a cap.
Order, dedup and cap tests patch route.route and read.render; the rest run on an invented library in tmp_path."""
import json, os, subprocess, sys
import pytest

CODE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(CODE, "scripts")
REAL = os.path.expanduser(os.environ.get("JEV_SOURCES_DATA") or "~/.claude/jev-sources-data")
sys.path.insert(0, SCRIPTS)


def sec(sid, kind="reference", depth="READ FULL", tokens=100, **kw):
    d = dict(id=sid, path=sid.split("#")[0] + ".md", heading="H" + sid, kind=kind, tokens=tokens, depth=depth,
             by="keyword", needs=None, status=None, note=None)
    d.update(kw)
    return d


@pytest.fixture
def J(monkeypatch):
    import jev
    monkeypatch.setattr(jev.RD, "render", lambda sid, extract_terms=None: f"CITE AS: {sid}\nbody of {sid}")
    return jev


def routes(J, monkeypatch, table):
    monkeypatch.setattr(J.R, "route", lambda q, model=None: dict(dict(definitions=[], semantic="on"), **table[q]))


def ids(b):
    return [r.split("\n", 1)[0][len("CITE AS: "):].split(" | ")[0] for r in b["read"]]


def test_definitions_are_read(J, monkeypatch):
    routes(J, monkeypatch, {"q": {"sections": [sec("a")], "definitions": [sec("d", depth="READ FULL")]}})
    assert set(ids(J.bundle(["q"]))) == {"a", "d"}


def test_a_section_one_phrasing_reads_full_is_read_even_if_the_other_says_extract(J, monkeypatch):
    routes(J, monkeypatch, {"mine": {"sections": [sec("a", depth="EXTRACT")]}, "docs": {"sections": [sec("a", depth="READ FULL")]}})
    b = J.bundle(["mine", "docs"])
    assert ids(b) == ["a"] and b["extract"] == []
    routes(J, monkeypatch, {"mine": {"sections": [sec("a", depth="READ FULL")]}, "docs": {"sections": [sec("a", depth="EXTRACT")]}})
    assert ids(J.bundle(["mine", "docs"])) == ["a"]


def test_a_section_both_phrasings_return_appears_once(J, monkeypatch):
    routes(J, monkeypatch, {"x": {"sections": [sec("a"), sec("b")]}, "y": {"sections": [sec("b"), sec("c")]}})
    assert sorted(ids(J.bundle(["x", "y"]))) == ["a", "b", "c"]


def test_reading_order_is_reference_pattern_sdk_example_vendor(J, monkeypatch):
    kinds = ["other", "vendor", "example", "sdk", "pattern", "reference"]
    routes(J, monkeypatch, {"q": {"sections": [sec(k, kind=k) for k in kinds]}})
    assert ids(J.bundle(["q"])) == ["reference", "pattern", "sdk", "example", "vendor", "other"]


def test_a_section_the_model_is_too_old_for_comes_after_every_applicable_one(J, monkeypatch):
    routes(J, monkeypatch, {"q": {"sections": [sec("old", needs_newer=True), sec("ex", kind="example"), sec("vend", kind="vendor")]}})
    assert ids(J.bundle(["q"]))[-1] == "old"
    new = {"q": {"sections": [sec("new", needs="jev-1.14.0"), sec("ex", kind="example"), sec("v", kind="vendor")]}}
    routes(J, monkeypatch, new)
    assert ids(J.bundle(["q"], model="jev-1.13.0")) == ["ex", "v", "new"]


def routes_like_route(J, monkeypatch, sections):
    """A route that behaves like route.route about the model: an explicit model wins, else the question's own."""
    seen = []

    def fake(q, model=None):
        seen.append(model)
        return dict(question=q, model=model or J.applicability.find_model(q), sections=sections, definitions=[], semantic="on")
    monkeypatch.setattr(J.R, "route", fake)
    return seen


def test_a_model_named_only_in_the_first_phrasing_still_orders_both_passes(J, monkeypatch):
    seen = routes_like_route(J, monkeypatch, [sec("new", needs="jev-1.14.0"), sec("ex", kind="example")])
    b = J.bundle(["on jev-1.13.0, where is the mug", "Box question bounding box image"])
    assert ids(b) == ["ex", "new"] and seen == ["jev-1.13.0", "jev-1.13.0"]


def test_two_models_across_phrasings_use_the_older_one(J, monkeypatch):
    seen = routes_like_route(J, monkeypatch, [sec("new", needs="jev-1.14.0"), sec("ex", kind="example")])
    b = J.bundle(["on jev-1.13.0, where is the mug", "jev-1.14.0 Box question"])
    assert ids(b) == ["ex", "new"] and seen == ["jev-1.13.0", "jev-1.13.0"]


def test_a_model_flag_that_is_not_a_model_warns_and_routes_with_none(J, monkeypatch, capsys):
    seen = routes_like_route(J, monkeypatch, [sec("a")])
    monkeypatch.setattr(sys, "argv", ["jev.py", "q", "--model", "1.13.0"])
    J.main()
    assert "not a Jev model" in capsys.readouterr().err and seen == [None]


def test_a_needs_1_14_section_is_not_demoted_with_no_model_or_a_new_enough_one(J, monkeypatch):
    routes(J, monkeypatch, {"q": {"sections": [sec("new", needs="jev-1.14.0"), sec("ex", kind="example"), sec("v", kind="vendor")]}})
    assert ids(J.bundle(["q"])) == ["new", "ex", "v"]
    assert ids(J.bundle(["q"], model="jev-1.14.0")) == ["new", "ex", "v"]


def test_sections_past_the_cap_are_listed_not_dropped(J, monkeypatch):
    routes(J, monkeypatch, {"q": {"sections": [sec("a", tokens=700), sec("b", tokens=700), sec("c", tokens=400)]}})
    b = J.bundle(["q"], cap=1000)
    assert ids(b) == ["a"] and [s["id"] for s in b["not_read"]] == ["b", "c"]


def test_the_first_section_is_read_even_when_it_alone_is_over_the_cap(J, monkeypatch):
    routes(J, monkeypatch, {"q": {"sections": [sec("a", tokens=5000)]}})
    assert ids(J.bundle(["q"], cap=1000)) == ["a"]


def test_extract_items_are_listed_not_read(J, monkeypatch):
    routes(J, monkeypatch, {"q": {"sections": [sec("a"), sec("e", depth="EXTRACT")]}})
    b = J.bundle(["q"])
    assert ids(b) == ["a"] and [s["id"] for s in b["extract"]] == ["e"]


def test_cli_prints_a_read_command_for_each_unread_section(J, monkeypatch, capsys):
    routes(J, monkeypatch, {"q": {"sections": [sec("a", tokens=700), sec("b", tokens=700), sec("e", depth="EXTRACT")]}})
    monkeypatch.setattr(sys, "argv", ["jev.py", "q", "--cap", "1000"])
    J.main()
    out = capsys.readouterr().out
    assert f"python3 {os.path.join(CODE, 'scripts', 'read.py')} 'b'" in out
    assert "NOT YET READ" in out and "EXTRACT" in out and "semantic: on" in out


# ---- on an invented library -------------------------------------------------------------------------------------

PAGES = {
    "docs/concepts__state.md": "# State\n\nEach call carries one state. A call must hold every field the question needs.\n",
    "docs/primitives__box.md": "# Box\n\nBox locates the mug in a photo and returns its coordinates in the image.\n",
    "cookbooks/rerank_typesafe.md": "# Rerank\n\nThe build asks one question per passage to rank passages.\n\n## Closing\n\nFor clarity, this walkthrough uses one call per passage.\n",
    "blog/launch.txt": "# Launch\n\nIntro.\n\n## Benchmarks\n\nJev answers 40x faster than a frontier LLM, at a fraction of the cost.\n",
}


@pytest.fixture
def lib(tmp_path, monkeypatch):
    data = tmp_path / "data"
    for p, text in PAGES.items():
        (data / p).parent.mkdir(parents=True, exist_ok=True)
        (data / p).write_text(text)
    monkeypatch.setenv("JEV_SOURCES_DATA", str(data))
    monkeypatch.setenv("JEV_SEMANTIC", "off")
    monkeypatch.setenv("JEV_PRIVATE_CONFIG", str(tmp_path / "absent.json"))
    monkeypatch.syspath_prepend(SCRIPTS)
    for n in ("paths", "build_index", "route", "read", "jev", "usage_log", "applicability"):
        sys.modules.pop(n, None)
    import build_index
    monkeypatch.setattr(build_index, "embed", lambda rows: None)
    build_index.main()
    return data


def rows(data):
    return [json.loads(l) for l in open(data / "sections.jsonl")]


def sid_of(data, path, heading):
    return next(r["id"] for r in rows(data) if r["path"] == path and r["heading"] == heading)


def test_blog_text_is_indexed_as_a_vendor_source_with_a_clean_id(lib):
    r = next(r for r in rows(lib) if r["heading"] == "Benchmarks")
    assert r["kind"] == "vendor" and r["id"].startswith("blog/launch#") and ".#" not in r["id"]


def test_route_lists_the_blog_section_labeled_vendor_claim(lib):
    out = subprocess.run([sys.executable, os.path.join(SCRIPTS, "route.py"), "how much faster is it than an LLM"],
                         capture_output=True, text=True, check=True).stdout
    line = next(l for l in out.splitlines() if "blog/launch.txt#Benchmarks" in l)
    assert "vendor claim" in line and line.startswith("READ FULL")


def test_a_blog_capture_with_no_headings_splits_into_parts_that_read_full(tmp_path, lib):
    para = "Jev is fast and cheap. " * 40  # about 920 characters
    (lib / "blog" / "flat.txt").write_text("\n\n".join(f"{para}Paragraph {i} ends here." for i in range(6)) + "\n")
    import build_index
    build_index.main()
    parts = [r for r in rows(lib) if r["path"] == "blog/flat.txt"]
    assert len(parts) >= 3 and all(r["heading"].startswith(f"Part {i + 1}: Jev is fast and cheap") for i, r in enumerate(parts))
    assert all(r["tokens"] < 900 and r["kind"] == "vendor" for r in parts)
    assert len({r["id"] for r in parts}) == len(parts)


def test_render_of_a_reference_section_is_todays_output_after_the_cite_line(lib):
    import read
    sid = sid_of(lib, "docs/concepts__state.md", "State")
    text = read.render(sid)
    first, rest = text.split("\n", 1)
    assert first == "CITE AS: docs/concepts__state.md#State (reference rule)"
    assert rest == ("SOURCE: docs/concepts__state.md#State | KIND: reference rule | READ: full\n"
                    "(lines 1-4, ~21 tokens)\n\n"
                    "# State\n\nEach call carries one state. A call must hold every field the question needs.\n")


def test_render_of_a_cookbook_section_adds_the_example_line_under_source(lib):
    import read
    text = read.render(sid_of(lib, "cookbooks/rerank_typesafe.md", "Rerank"))
    lines = text.split("\n")
    assert lines[0].endswith("(cookbook example)") and lines[1].startswith("SOURCE: ")
    assert lines[2] == ("EXAMPLE: one build TypeSafe published. Its layout, call counts and diagrams are not API limits; "
                        "check the scope notes below and the reference rules.")
    assert "Scope notes elsewhere in this file" in text


def test_read_cli_output_still_starts_with_the_source_line(lib):
    sid = sid_of(lib, "docs/concepts__state.md", "State")
    out = subprocess.run([sys.executable, os.path.join(SCRIPTS, "read.py"), sid], capture_output=True, text=True, check=True).stdout
    assert out.startswith("SOURCE: docs/concepts__state.md#State | KIND: reference rule")


def test_each_read_section_starts_with_its_cite_line_and_label(lib):
    import jev
    b = jev.bundle(["where is the mug in a photo"], model="jev-1.13.0")
    box = next(r for r in b["read"] if "primitives__box" in r.split("\n", 1)[0])
    first = box.split("\n", 1)[0]
    assert first.startswith("CITE AS: docs/primitives__box.md#Box (reference rule)")
    assert "NEEDS jev-1.14.0" in first and "EXPERIMENTAL" in first
    assert all(r.startswith("CITE AS: ") for r in b["read"])


def test_one_call_with_two_phrasings_logs_two_routes_one_read_per_section_and_one_jev_line(lib):
    env = {k: v for k, v in os.environ.items() if k != "JEV_LOG"}
    r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "jev.py"), "does a call hold every field",
                        "--docs-words", "one state per request"], capture_output=True, text=True, env=env)
    assert r.returncode == 0 and "CITE AS: " in r.stdout, r.stderr
    log = lambda n: [json.loads(l) for l in open(lib / "logs" / f"{n}.jsonl")]
    assert len(log("route")) == 2
    printed = r.stdout.count("CITE AS: ")
    assert printed >= 1 and len(log("read")) == printed
    j = log("jev")
    assert len(j) == 1 and j[0]["questions"] == ["does a call hold every field", "one state per request"]
    assert len(j[0]["read"]) == printed


def _real_blog_indexed():
    idx = os.path.join(REAL, "sections.jsonl")
    return os.path.exists(idx) and any('"vendor"' in l for l in open(idx))


@pytest.mark.skipif(not _real_blog_indexed(), reason="real library with the blog captures indexed is not here")
@pytest.mark.parametrize("quote", ["70ms-500ms for TypeSafe", "two orders of magnitude faster", "193.6x faster, 444.6x cheaper"])
@pytest.mark.parametrize("question", ["how much faster and cheaper is Jev than a frontier LLM", "is Jev faster than an LLM"])
def test_each_launch_post_quote_comes_back_read_full_from_a_speed_or_cost_question(quote, question, monkeypatch):
    monkeypatch.setenv("JEV_SOURCES_DATA", REAL)
    monkeypatch.setenv("JEV_SEMANTIC", "off")
    for n in ("paths", "route", "read"):
        sys.modules.pop(n, None)
    import route, read
    res = route.route(question)
    full = [s for s in res["sections"] + res["definitions"] if s["depth"] == "READ FULL" and s["kind"] == "vendor"]
    assert any(quote in read.render(s["id"]) for s in full), [s["heading"] for s in full]


def test_leading_page_chrome_of_a_blog_capture_is_not_a_part(lib):
    chrome = "Acme AI\n\nManifesto\n\nOur Team\n\nDocs\n\nSign In\n\nSep 15, 2026\n\n"
    body = "\n\n".join(f"Jev answers questions quickly and cheaply in paragraph {i}, which is a full sentence." for i in range(3))
    (lib / "blog" / "chrome.txt").write_text(chrome + body + "\n")
    import build_index
    build_index.main()
    parts = [r for r in rows(lib) if r["path"] == "blog/chrome.txt"]
    assert parts and parts[0]["heading"].startswith("Part 1: Jev answers questions")
    text = "\n".join((lib / "blog" / "chrome.txt").read_text().split("\n")[parts[0]["line_start"] - 1:parts[0]["line_end"]])
    assert "Sign In" not in text and "Manifesto" not in text


def test_no_real_blog_part_is_navigation_only():
    if not _real_blog_indexed():
        pytest.skip("real library with the blog captures indexed is not here")
    for l in open(os.path.join(REAL, "sections.jsonl")):
        r = json.loads(l)
        if r["kind"] == "vendor" and r["heading"].startswith("Part "):
            assert "Sign In" not in r["heading"] and "Manifesto Our Team" not in r["heading"], r["heading"]


def test_a_batch_job_latency_question_routes_no_vendor_section(lib):
    out = subprocess.run([sys.executable, os.path.join(SCRIPTS, "route.py"), "speed up my pipeline latency of the batch job"],
                         capture_output=True, text=True).stdout
    assert "vendor claim" not in out
    out = subprocess.run([sys.executable, os.path.join(SCRIPTS, "route.py"), "is Jev faster than an LLM"],
                         capture_output=True, text=True).stdout
    assert "vendor claim" in out


def test_read_refs_are_the_path_and_heading_of_each_read_id(J, monkeypatch):
    routes(J, monkeypatch, {"q": {"sections": [sec("docs/a#1", kind="pattern"), sec("docs/b#2", kind="reference"), sec("docs/c#0", tokens=900)]}})
    b = J.bundle(["q"], cap=500)
    assert b["read_ids"] == ["docs/b#2", "docs/a#1"]
    assert b["read_refs"] == ["docs/b.md#Hdocs/b#2", "docs/a.md#Hdocs/a#1"]


def test_cap_default_is_12000(J):
    assert J.CAP == 12000


def test_log_false_writes_no_usage_line_even_with_logging_on(tmp_path, monkeypatch):
    monkeypatch.setenv("JEV_SOURCES_DATA", str(tmp_path))
    monkeypatch.setenv("JEV_LOG", "on")
    for name in ("jev", "route", "read", "usage_log", "paths", "applicability", "semantic"):
        sys.modules.pop(name, None)
    import jev
    monkeypatch.setattr(jev.RD, "render", lambda sid, extract_terms=None: f"CITE AS: {sid}\nbody")
    monkeypatch.setattr(jev.R, "route", lambda q, model=None: dict(definitions=[], semantic="on", sections=[sec("docs/a#0")]))
    jev.bundle(["q"], log=False)
    assert not (tmp_path / "logs").exists()
    jev.bundle(["q"])
    assert (tmp_path / "logs" / "route.jsonl").exists() and (tmp_path / "logs" / "read.jsonl").exists()
