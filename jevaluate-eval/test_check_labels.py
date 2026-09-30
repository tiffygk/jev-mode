import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import check_labels as cl

PACKET = """# PROJECT: o/r

## FILE: README.md
A harness powered by Jev.

## FILE: AGENT.md
(keyword lines, numbered)
285: String m = typesafe.choose(state, "model");

## FILE: src/app.py
(keyword lines, numbered)
3: from typesafe_sdk import TypeSafeClient
4: client = TypeSafeClient(api_key=k)
9: import bench_helpers
"""

def label(**kw):
    base = {"type": "workflow", "calls_jev": "yes", "call_line": "src/app.py:4", "reason": "r"}
    base.update(kw); return base

def test_yes_citing_a_real_call_line_passes():
    assert cl.problems(label(), PACKET) == []

def test_yes_citing_a_doc_is_refused():
    p = cl.problems(label(call_line="AGENT.md:285 (String m = typesafe.choose(...))"), PACKET)
    assert p and "AGENT.md:285" in p[0] and "not a code file" in p[0]

def test_yes_citing_code_that_is_not_a_call_is_refused():
    p = cl.problems(label(call_line="src/app.py:9"), PACKET)
    assert p and "not a hosted call" in p[0] and "src/app.py:4" in p[0]

def test_yes_with_no_citation_is_refused():
    assert cl.problems(label(call_line="the client file"), PACKET)

def test_no_must_name_each_file_the_packet_shows_calling():
    p = cl.problems(label(calls_jev="no", call_line="none"), PACKET)
    assert p and "src/app.py" in p[0]
    assert cl.problems(label(calls_jev="no", call_line="none", reason="src/app.py only imports the SDK for a benchmark"), PACKET) == []

def test_no_with_no_calls_in_packet_passes():
    assert cl.problems(label(calls_jev="no", call_line="none"), "# PROJECT: o/r\n\n## FILE: README.md\nUses Jev.\n") == []

def test_parse_label_from_headless_output():
    out = {"result": 'Here: {"type": "demo", "calls_jev": "yes", "call_line": "a.py:1"}', "usage": {}}
    assert cl.parse_label(json.dumps(out))["type"] == "demo"


def test_library_and_check_labels_share_one_call_rule(tmp_path):
    import library
    packet = "## FILE: a/Config.java\n(keyword lines, numbered)\n1: x = new TypeSafeJevClient(k);\n"
    assert cl.call_lines(packet) == {"a/Config.java": [1]}
    assert cl.jev_callsites is library.jev_callsites and cl.jev_callsites.calls_in is library.jev_callsites.calls_in
    d = tmp_path / "files"; d.mkdir(); (d / "a__Config.java").write_text("x = new TypeSafeJevClient(k);\n")
    assert cl.jev_callsites.call_lines(d) == cl.call_lines(packet)


def test_yes_citing_an_import_line_is_refused():
    p = cl.problems(label(call_line="src/app.py:3"), PACKET)
    assert p and "not a hosted call" in p[0] and "src/app.py:4" in p[0]


# --- Review fix 7 (2026-09-30): check_labels applies library.py's F0 rules, not its own variants ---
def test_a_cited_path_longer_than_the_packet_path_does_not_match():
    packet = "## FILE: app.py\n(keyword lines, numbered)\n4: client = TypeSafeClient(k)\n"
    assert cl.problems(label(call_line="app.py:4"), packet) == []
    assert cl.problems(label(call_line="pkg/app.py:4"), packet)  # library.same_file matches a bare name to a longer path, never the reverse
    p = cl.problems(label(call_line="pkg/app.py:4"), "## FILE: lib/app.py\n(keyword lines, numbered)\n4: client = TypeSafeClient(k)\n")
    assert p

def test_a_bare_name_matches_a_longer_packet_path():
    packet = "## FILE: src/app.py\n(keyword lines, numbered)\n4: client = TypeSafeClient(k)\n"
    assert cl.problems(label(call_line="app.py:4"), packet) == []

def test_a_scoped_package_path_is_one_citation():
    packet = "## FILE: @acme/client/src/index.ts\n(keyword lines, numbered)\n4: const c = new TypeSafeClient(k);\n"
    assert cl.problems(label(call_line="`@acme/client/src/index.ts:4`"), packet) == []

def test_a_no_needs_three_words_of_reason_per_file():
    bare = label(calls_jev="no", call_line="src/app.py", reason="")
    assert cl.problems(bare, PACKET) and "src/app.py" in cl.problems(bare, PACKET)[0]
    assert cl.problems(label(calls_jev="no", call_line="src/app.py", reason="only used by a benchmark"), PACKET) == []
    assert cl.problems(label(calls_jev="no", call_line="none", reason="mentions src/app.py"), PACKET)

def test_label_checks_use_libraries_helpers():
    import library
    assert cl.library.CITE.pattern == library.CITE.pattern and not hasattr(cl, "CITE")
    for f in ("same_file", "no_reasoned", "cites_a_call", "is_code_cite"):
        assert getattr(cl.library, f).__code__.co_filename == getattr(library, f).__code__.co_filename
