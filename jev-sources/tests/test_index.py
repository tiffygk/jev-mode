import json, os, subprocess, sys
CODE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.expanduser(os.environ.get("JEV_SOURCES_DATA") or "~/.claude/jev-sources-data")
ROOT = DATA
IDX = os.path.join(ROOT, "sections.jsonl")

def rows():
    subprocess.run([sys.executable, os.path.join(CODE, "scripts/build_index.py")], check=True)
    return [json.loads(l) for l in open(IDX)]

def test_rerank_closing_caveat_is_attached_to_every_section_of_its_file():
    rs = [r for r in rows() if r["path"] == "cookbooks/rerank_typesafe.md"]
    assert rs and all(any("for clarity" in c for c in r["file_caveats"]) for r in rs)

def test_kinds():
    rs = rows()
    kind = {r["path"]: r["kind"] for r in rs}
    assert kind["docs/concepts__state.md"] == "reference"
    assert kind["cookbooks/rerank_typesafe.md"] == "example"
    assert kind["patterns/fan-out.md"] == "pattern"
    assert any(k == "sdk" for p, k in kind.items() if p.startswith("docs/sdk"))

def test_no_duplicate_cookbook_copies_from_docs_folder():
    assert not any(r["path"].startswith(("docs/cookbooks__", "docs/patterns__")) for r in rows())

def test_line_range_reads_back_heading_and_skips_code_fences():
    for r in rows():
        lines = open(os.path.join(ROOT, r["path"])).read().split("\n")
        assert lines[r["line_start"] - 1].lstrip("#").strip() == r["heading"]
    rr = [r["heading"] for r in rows() if r["path"] == "cookbooks/rerank_typesafe.md"]
    assert not any(h.startswith("calls") for h in rr)  # '# calls ...' inside a code block is not a heading
