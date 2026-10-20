"""jev.py: one call that routes a question in two phrasings and reads every READ FULL section in order, up to a cap.
Order, dedup and cap tests patch route.route and read.render; the rest run on an invented library in tmp_path."""
import json, os, shlex, subprocess, sys
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
def J(monkeypatch, tmp_path):
    import jev
    monkeypatch.setattr(jev.paths, "DATA", str(tmp_path / "plandata"))  # a reading plan is written here, never into the library
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
    assert f"python3 {os.path.join(CODE, 'scripts', 'read.py')} {shlex.quote('b')}  #" in out
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


# ---- the reading plan -------------------------------------------------------------------------------------------

def test_reading_plan_batches_in_order_and_a_big_section_stands_alone(J):
    mk = lambda i, t: {"id": i, "tokens": t}
    plan = J.reading_plan([mk("a", 5000), mk("b", 6000), mk("c", 3000), mk("big", 13000), mk("d", 100)], 12000)
    assert [[s["id"] for s in b] for b in plan] == [["a", "b"], ["c"], ["big"], ["d"]]
    assert J.reading_plan([], 12000) == []


def plan_lib_pages(n, tokens_each=1000):
    body = "\n".join("Sentence number %d about the batch limit goes here." % i for i in range(tokens_each * 4 // 52 + 1))
    pages = {}
    for k in range(n):
        pages["docs/p%d.md" % k] = "# What's the batch limit %d\n\n%s\n" % (k, body)
    return pages


def make_lib(tmp_path, monkeypatch, pages):
    data = tmp_path / "data"
    for p, text in pages.items():
        (data / p).parent.mkdir(parents=True, exist_ok=True)
        (data / p).write_text(text)
    env = {**os.environ, "JEV_SOURCES_DATA": str(data), "JEV_SEMANTIC": "off", "JEV_LOG": "off",
           "JEV_PRIVATE_CONFIG": str(tmp_path / "absent.json")}
    subprocess.run([sys.executable, os.path.join(SCRIPTS, "build_index.py"), "--no-prepare"], check=True, capture_output=True, env=env)
    return env


def run_jev(env, *args):
    return subprocess.run([sys.executable, os.path.join(SCRIPTS, "jev.py"), *args], capture_output=True, text=True, env=env)


def test_over_twice_the_cap_prints_a_plan_with_runnable_numeric_id_commands(tmp_path, monkeypatch):
    pages = plan_lib_pages(4, 1000)
    env = make_lib(tmp_path, monkeypatch, pages)
    r = run_jev(env, "what is the batch limit", "--cap", "1500")
    assert r.returncode == 0, r.stderr
    out = r.stdout
    assert "READING PLAN: " in out and "tokens not yet read, more than the cap (1,500)" in out
    assert "GOAL: what is the batch limit" in out
    assert "BATCH 1 (~" in out and "BATCH 2 (~" in out
    assert "NOT YET READ" not in out
    assert 'FINDING: <one sentence> | CITE AS: <path#heading (label)> | QUOTE: "<exact words>"' in out
    cmds = [l.strip() for l in out.splitlines() if l.strip().startswith("python3 ") and "read.py" in l]
    assert cmds and all("  # docs/" in c and "#" in c.split("  # ", 1)[0] for c in cmds)
    apos = [c for c in cmds if "What's the batch limit" in c]
    assert apos
    cmd = apos[0].split("  # ", 1)[0].replace("python3 ", "", 1)
    import shlex
    res = subprocess.run([sys.executable, *shlex.split(cmd)], capture_output=True, text=True, env=env)
    assert res.returncode == 0 and res.stdout.startswith("SOURCE: docs/p") and "#What's the batch limit" in res.stdout.split("|")[0], res.stderr


def test_at_or_under_the_cap_the_unread_sections_are_listed_not_planned(tmp_path, monkeypatch):
    env = make_lib(tmp_path, monkeypatch, plan_lib_pages(3, 1000))
    over = run_jev(env, "what is the batch limit", "--cap", "1500", "--json")  # 2,000 tokens unread: over the cap
    assert json.loads(over.stdout)["plan"]
    out = run_jev(env, "what is the batch limit", "--cap", "2500").stdout  # 1,000 unread: at or under
    assert "READING PLAN" not in out and "NOT YET READ (over the cap)" in out


def test_a_section_over_the_cap_stands_alone_in_the_cli_plan(J, monkeypatch, capsys):
    routes(J, monkeypatch, {"q": {"sections": [sec("a", tokens=100), sec("b", tokens=13000), sec("c", tokens=200), sec("d", tokens=12500)]}})
    b = J.bundle(["q"])
    assert [[s["id"] for s in x] for x in J.reading_plan(b["not_read"], J.CAP)] == [["b"], ["d"]]
    monkeypatch.setattr(sys, "argv", ["jev.py", "q"])
    J.main()
    out = capsys.readouterr().out
    assert out.count("BATCH ") == 2 and "BATCH 1 (~13,000 tokens)" in out


def test_json_carries_plan_and_read_refs(J, monkeypatch, capsys):
    routes(J, monkeypatch, {"q": {"sections": [sec("a", tokens=100), sec("b", tokens=13000)]}})
    monkeypatch.setattr(sys, "argv", ["jev.py", "q", "--json"])
    J.main()
    d = json.loads(capsys.readouterr().out)
    assert d["plan"] == [["b"]] and d["read_refs"] == ["a.md#Ha"]


def test_a_printed_section_with_ten_code_shaped_lines_gets_a_notice(J, monkeypatch, capsys):
    code = "\n".join("const a%d = () => 1;" % i for i in range(10))
    monkeypatch.setattr(J.RD, "render", lambda sid, extract_terms=None: f"CITE AS: {sid}\nSOURCE: x\n{code}")
    routes(J, monkeypatch, {"q": {"sections": [sec("a")]}})
    monkeypatch.setattr(sys, "argv", ["jev.py", "q"])
    J.main()
    out = capsys.readouterr().out
    assert "NOTICE: a.md#Ha looks like site code (10 code-shaped lines). Run bash " in out
    assert "to re-clean; treat this section as unverified until then." in out


def test_a_clean_section_gets_no_notice(J, monkeypatch, capsys):
    routes(J, monkeypatch, {"q": {"sections": [sec("a")]}})
    monkeypatch.setattr(sys, "argv", ["jev.py", "q"])
    J.main()
    assert "looks like site code" not in capsys.readouterr().out


# ---- map mode, several questions, coverage and the ceilings ------------------------------------------------------

def run_main(J, monkeypatch, *argv):
    monkeypatch.setattr(sys, "argv", ["jev.py", *argv])
    return J.main()


def map_routes(J, monkeypatch, per_q, seen=None):
    def fake(q, model=None, limit=10, per_page=2):
        if seen is not None:
            seen.append((q, limit, per_page))
        return dict(dict(definitions=[], semantic="on"), **per_q[q])
    monkeypatch.setattr(J.R, "route", fake)
    monkeypatch.setattr(J.RD, "render", lambda *a, **k: pytest.fail("map mode must not read a section"))


def big_map(n_pages, heading="A long heading about one topic of the batch limit rules"):
    out = []
    for k in range(n_pages):
        for j in range(2):
            out.append(sec("docs/p%d#%d" % (k, j), path="docs/p%d.md" % k, heading="%s %d.%d" % (heading, k, j), tokens=700 + j * 100))
    return out


def test_map_routes_wide_and_prints_pages_with_sections_and_no_body(J, monkeypatch, capsys):
    seen = []
    secs = [sec("docs/a#0", path="docs/a.md", heading="Alpha", tokens=600), sec("cook/b#0", path="cook/b.md", heading="Beta", kind="example", tokens=1400),
            sec("docs/a#1", path="docs/a.md", heading="Gamma", tokens=900)]
    map_routes(J, monkeypatch, {"goal": {"sections": secs}}, seen)
    assert run_main(J, monkeypatch, "--map", "goal") == 0
    out = capsys.readouterr().out.splitlines()
    assert seen == [("goal", 30, 3)]
    assert out[0] == "MAP: goal"
    assert out[1] == "docs/a.md (reference rule, 2 sections, ~1,500 tokens)"  # grouped, in rank order of each page's best section
    assert out[2:4] == ["  - Alpha (~600)", "  - Gamma (~900)"]
    assert out[4] == "cook/b.md (cookbook example, 1 section, ~1,400 tokens)"
    assert out[-1] == 'Next: run jev.py with one question per topic you need: jev.py "<q1>" --also "<q2>" ...'
    assert not any("body of" in l for l in out)


def test_map_stays_under_the_budget_on_forty_pages_and_says_how_many_more(J, monkeypatch, capsys):
    map_routes(J, monkeypatch, {"goal": {"sections": big_map(40)}})
    assert run_main(J, monkeypatch, "--map", "goal") == 0
    text = capsys.readouterr().out
    assert len(text) / 4 <= J.MAP_TOKENS
    lines = text.rstrip("\n").splitlines()
    assert lines[-2].startswith("... and ") and lines[-2].endswith(" more pages") and lines[-1].startswith("Next: ")
    shown = sum(1 for l in lines if l.startswith("docs/"))
    assert lines[-2] == "... and %d more pages" % (40 - shown) and 0 < shown < 40


def test_map_outline_takes_a_smaller_budget_and_keeps_at_least_one_page(J, monkeypatch):
    map_routes(J, monkeypatch, {"goal": {"sections": big_map(5)}})
    out = J.map_outline("goal", budget=100)
    assert len(out) / 4 <= 100 or out.count("docs/p") == 1
    assert out.count("docs/p0.md (") == 1 and "more pages" in out


def test_map_merges_the_docs_words_routing_without_repeating_a_section(J, monkeypatch, capsys):
    a, b = sec("docs/a#0", path="docs/a.md", heading="Alpha"), sec("docs/b#0", path="docs/b.md", heading="Beta")
    map_routes(J, monkeypatch, {"mine": {"sections": [a]}, "docs": {"sections": [a, b]}})
    run_main(J, monkeypatch, "--map", "mine", "--docs-words", "docs")
    out = capsys.readouterr().out
    assert out.count("Alpha") == 1 and "docs/b.md" in out


def test_map_logs_no_read(tmp_path, monkeypatch):
    monkeypatch.setenv("JEV_SOURCES_DATA", str(tmp_path))
    monkeypatch.setenv("JEV_LOG", "on")
    for name in ("jev", "route", "read", "usage_log", "paths", "applicability", "semantic"):
        sys.modules.pop(name, None)
    import jev
    map_routes(jev, monkeypatch, {"goal": {"sections": [sec("docs/a#0", path="docs/a.md")]}})
    monkeypatch.setattr(sys, "argv", ["jev.py", "--map", "goal"])
    jev.main()
    assert not (tmp_path / "logs" / "read.jsonl").exists()


def three(J, monkeypatch, shared=True):
    routes(J, monkeypatch, {"q1": {"sections": [sec("a"), sec("s")]}, "q2": {"sections": [sec("s"), sec("b")] if shared else [sec("b")]},
                            "q3": {"sections": [sec("x", depth="EXTRACT")]}})


def test_a_section_two_questions_reach_is_printed_once_and_counted_under_both(J, monkeypatch, capsys):
    three(J, monkeypatch)
    assert run_main(J, monkeypatch, "q1", "--also", "q2", "--also", "q3") == 0
    out = capsys.readouterr().out
    assert out.count("body of s") == 1
    cov = out.split("COVERAGE:\n", 1)[1].splitlines()
    assert cov[0] == "  1. q1: read 2, in plan 0" and cov[1] == "  2. q2: read 2, in plan 0"


def test_a_question_with_nothing_to_read_in_full_prints_no_source_found(J, monkeypatch, capsys):
    three(J, monkeypatch)
    run_main(J, monkeypatch, "q1", "--also", "q2", "--also", "q3")
    out = capsys.readouterr().out
    assert "NO SOURCE FOUND: q3" in out
    assert "  3. q3: NO SOURCE FOUND (nothing to read in full; EXTRACT only: 1)" in out
    routes(J, monkeypatch, {"q1": {"sections": [sec("a")]}, "q2": {"sections": []}})
    run_main(J, monkeypatch, "q1", "--also", "q2")
    assert "  2. q2: NO SOURCE FOUND (nothing to read in full; EXTRACT only: 0)" in capsys.readouterr().out


def test_coverage_counts_a_sections_in_the_plan_per_question(J, monkeypatch, capsys):
    routes(J, monkeypatch, {"q1": {"sections": [sec("a", tokens=900)]}, "q2": {"sections": [sec("b", tokens=900), sec("c", tokens=900)]}})
    run_main(J, monkeypatch, "q1", "--also", "q2", "--cap", "1000")
    out = capsys.readouterr().out
    assert "  1. q1: read 1, in plan 0" in out and "  2. q2: read 0, in plan 2" in out


def test_a_single_question_prints_no_coverage_block(J, monkeypatch, capsys):
    routes(J, monkeypatch, {"q": {"sections": [sec("a")]}})
    run_main(J, monkeypatch, "q")
    assert "COVERAGE" not in capsys.readouterr().out


def test_docs_words_belong_to_the_first_question_only(J, monkeypatch, capsys):
    routes(J, monkeypatch, {"q1": {"sections": [sec("a")]}, "words": {"sections": [sec("w")]}, "q2": {"sections": [sec("b")]}})
    run_main(J, monkeypatch, "q1", "--docs-words", "words", "--also", "q2", "--json")
    cov = json.loads(capsys.readouterr().out)["coverage"]
    assert [c["q"] for c in cov] == ["q1", "q2"]
    assert sorted(cov[0]["read"]) == ["a", "w"] and cov[1]["read"] == ["b"]


def test_json_carries_coverage_with_read_planned_and_extract_ids(J, monkeypatch, capsys):
    routes(J, monkeypatch, {"q1": {"sections": [sec("a", tokens=900), sec("e", depth="EXTRACT")]}, "q2": {"sections": [sec("b", tokens=900)]}})
    run_main(J, monkeypatch, "q1", "--also", "q2", "--cap", "1000", "--json")
    cov = json.loads(capsys.readouterr().out)["coverage"]
    assert cov == [{"q": "q1", "read": ["a"], "planned": [], "extract": ["e"]}, {"q": "q2", "read": [], "planned": ["b"], "extract": []}]


def test_a_ninth_question_exits_2_with_the_split_message(J, monkeypatch, capsys):
    routes(J, monkeypatch, {"q%d" % i: {"sections": [sec("a")]} for i in range(9)})
    args = ["q0"] + [x for i in range(1, 9) for x in ("--also", "q%d" % i)]
    assert run_main(J, monkeypatch, *args) == 2
    cap = capsys.readouterr()
    assert "too many sub-questions (9); split the goal into two runs of at most 8" in cap.err and cap.out == ""
    args = ["q0"] + [x for i in range(1, 8) for x in ("--also", "q%d" % i)]
    assert run_main(J, monkeypatch, *args) == 0  # eight is allowed


def test_more_than_six_batches_prints_goal_too_broad_and_no_plan(J, monkeypatch, capsys):
    routes(J, monkeypatch, {"q": {"sections": [sec("s%d" % i, tokens=12000) for i in range(8)]}})
    run_main(J, monkeypatch, "q")
    out = capsys.readouterr().out
    assert "goal too broad: 7 batches (84,000 tokens); narrow the goal or split it into runs" in out
    assert "READING PLAN" not in out and "BATCH" not in out and "NOT YET READ" not in out
    routes(J, monkeypatch, {"q": {"sections": [sec("s%d" % i, tokens=12000) for i in range(7)]}})
    run_main(J, monkeypatch, "q")  # exactly six batches is a plan
    assert "BATCH 6" in capsys.readouterr().out


def test_too_broad_in_json_has_no_plan(J, monkeypatch, capsys):
    routes(J, monkeypatch, {"q": {"sections": [sec("s%d" % i, tokens=12000) for i in range(8)]}})
    run_main(J, monkeypatch, "q", "--json")
    assert json.loads(capsys.readouterr().out)["plan"] == []


def test_the_ceilings_are_constants(J):
    assert (J.MAX_QUESTIONS, J.MAX_BATCHES, J.MAP_TOKENS) == (8, 6, 1500)


def test_a_pages_sections_stay_in_one_batch_when_they_fit(J):
    mk = lambda i, p, t: {"id": i, "path": p, "tokens": t}
    plan = J.reading_plan([mk("x1", "x.md", 5000), mk("y1", "y.md", 6000), mk("x2", "x.md", 5000)], 12000)
    assert [[s["id"] for s in b] for b in plan] == [["x1", "x2"], ["y1"]]


def test_a_page_over_the_cap_is_split_in_reading_order(J):
    mk = lambda i, p, t: {"id": i, "path": p, "tokens": t}
    plan = J.reading_plan([mk("x1", "x.md", 7000), mk("y1", "y.md", 3000), mk("x2", "x.md", 7000)], 12000)
    assert [[s["id"] for s in b] for b in plan] == [["x1", "y1"], ["x2"]]


# ---- the saved plan, the reader blocks and the three T1 review fixes -------------------------------------------------

import re


def two_batches(J, monkeypatch):
    routes(J, monkeypatch, {"q1": {"sections": [sec("docs/a#0", path="docs/a.md", tokens=1900, heading="Alpha"),
                                                 sec("docs/b#1", path="docs/b.md", tokens=900, heading="It's b"),
                                                 sec("docs/c#2", path="docs/c.md", tokens=900, heading="Gamma"),
                                                 sec("docs/d#3", path="docs/d.md", tokens=900, heading="Delta")]},
                            "q2": {"sections": []}})


def plan_files(J):
    d = os.path.join(J.paths.DATA, "plans")
    return sorted(os.listdir(d)) if os.path.isdir(d) else []


def test_a_printed_plan_is_saved_with_exactly_the_interface_fields(J, monkeypatch, capsys):
    two_batches(J, monkeypatch)
    run_main(J, monkeypatch, "q1", "--also", "q2", "--cap", "2000")
    files = plan_files(J)
    assert len(files) == 1 and re.fullmatch(r"p[0-9a-f]{8}\.json", files[0])
    d = os.path.join(J.paths.DATA, "plans")
    plan = json.load(open(os.path.join(d, files[0])))
    assert list(plan) == ["plan_id", "created", "goal", "batches"]
    assert plan["plan_id"] + ".json" == files[0] and re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", plan["created"])
    assert plan["goal"] == ["q1", "q2"]
    assert plan["batches"] == [{"n": 1, "ids": ["docs/b#1", "docs/c#2"], "tokens": 1800}, {"n": 2, "ids": ["docs/d#3"], "tokens": 900}]
    assert oct(os.stat(d).st_mode & 0o777) == "0o700"
    assert oct(os.stat(os.path.join(d, files[0])).st_mode & 0o777) == "0o600"


def test_the_plan_is_written_atomically_leaving_no_temp_file(J, monkeypatch, capsys):
    two_batches(J, monkeypatch)
    run_main(J, monkeypatch, "q1", "--cap", "2000")
    assert all(re.fullmatch(r"p[0-9a-f]{8}\.json", f) for f in plan_files(J))


def test_the_reader_block_is_printed_line_for_line(J, monkeypatch, capsys):
    two_batches(J, monkeypatch)
    run_main(J, monkeypatch, "q1", "--also", "q2", "--cap", "2000")
    out = capsys.readouterr().out
    pid = plan_files(J)[0][:-5]
    skill_line = [l for l in open(os.path.join(CODE, "SKILL.md")).read().split("\n") if l.startswith("JEV-SOURCES:")][0]
    rd = os.path.join(CODE, "scripts", "read.py")
    want = "\n".join([
        f"----- READER BRIEF plan {pid} batch 1 -----",
        f"JEV-READER: plan {pid} batch 1",
        skill_line.replace("<skill>", CODE),
        "GOAL: q1 | q2",
        "Read these sections in full, in order:",
        f"  python3 {rd} {shlex.quote('docs/b#1')}   # docs/b.md#It's b",
        f"  python3 {rd} {shlex.quote('docs/c#2')}   # docs/c.md#Gamma",
        "Return only lines of this form, at most 12, with no page text:",
        'FINDING: <one sentence> | CITE AS: <path#heading (label)> | QUOTE: "<exact words>"',
        "Start your reply with the JEV-READER line above.",
        "----- END READER BRIEF -----"])
    assert want in out
    assert "<skill>" not in out
    assert "Each reader returns only lines of this form" not in out


def test_one_reader_block_per_batch(J, monkeypatch, capsys):
    routes(J, monkeypatch, {"q": {"sections": [sec("s%d" % i, tokens=12000) for i in range(4)]}})
    run_main(J, monkeypatch, "q")
    out = capsys.readouterr().out
    assert out.count("----- READER BRIEF plan ") == 3 and out.count("----- END READER BRIEF -----") == 3
    assert out.count("JEV-READER: plan ") == 3 and "batch 3 -----" in out


def test_json_carries_the_plan_id(J, monkeypatch, capsys):
    two_batches(J, monkeypatch)
    run_main(J, monkeypatch, "q1", "--cap", "2000", "--json")
    d = json.loads(capsys.readouterr().out)
    assert d["plan_id"] + ".json" == plan_files(J)[0]


def test_no_plan_no_file_and_no_plan_id(J, monkeypatch, capsys):
    routes(J, monkeypatch, {"q": {"sections": [sec("a")]}})
    run_main(J, monkeypatch, "q", "--json")
    assert "plan_id" not in json.loads(capsys.readouterr().out) and plan_files(J) == []
    routes(J, monkeypatch, {"q": {"sections": [sec("s%d" % i, tokens=12000) for i in range(8)]}})
    run_main(J, monkeypatch, "q")
    assert plan_files(J) == []


def test_log_off_does_not_stop_the_plan_file(J, monkeypatch, capsys):
    monkeypatch.setenv("JEV_LOG", "off")
    two_batches(J, monkeypatch)
    run_main(J, monkeypatch, "q1", "--cap", "2000")
    assert len(plan_files(J)) == 1


def test_a_too_broad_goal_says_unread_not_in_plan_in_coverage(J, monkeypatch, capsys):
    routes(J, monkeypatch, {"q1": {"sections": [sec("s%d" % i, tokens=12000) for i in range(8)]}, "q2": {"sections": [sec("s7", tokens=12000)]}})
    run_main(J, monkeypatch, "q1", "--also", "q2")
    out = capsys.readouterr().out
    assert "goal too broad" in out
    assert "  1. q1: read 1, unread 7" in out and "  2. q2: read 0, unread 1" in out
    assert "in plan" not in out


def test_map_with_also_exits_2(J, monkeypatch, capsys):
    routes(J, monkeypatch, {"q": {"sections": [sec("a")]}})
    assert run_main(J, monkeypatch, "--map", "q", "--also", "q2") == 2
    cap = capsys.readouterr()
    assert "--map takes one goal; run --also without --map" in cap.err and cap.out == ""
