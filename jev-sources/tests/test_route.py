import json, os, subprocess, sys
import pytest
CODE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.expanduser(os.environ.get("JEV_SOURCES_DATA") or "~/.claude/jev-sources-data")

def route(q):
    out = subprocess.run([sys.executable, f"{CODE}/scripts/route.py", "--json", q],
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out)

CASES = [
    ("can I put 30 passages in one call", ["docs/concepts__state.md", "docs/primitives.md", "patterns/fan-out.md", "cookbooks/rerank_typesafe.md"]),
    ("how do I pick a threshold", ["docs/confidence.md", "patterns/confidence-routing.md"]),
    ("should Jev count days between dates", ["docs/model-jaggedness__jev-1.13.md", "cookbooks/date_extraction_cookbook.md"]),
    ("does choice option order change the answer", ["cookbooks/consistency_choice_cookbook.md"]),
    ("too many categories for one choice", ["docs/primitives__advanced.md", "cookbooks/hierarchical_classification.md"]),
    ("prompt injection in the state", ["docs/model-jaggedness__jev-1.13.md", "cookbooks/classifying_rag_passages.md"]),
    ("pin the model version", ["docs/models.md"]),
    ("score a dataset of rows", ["patterns/fan-out.md", "cookbooks/parallel_questions.md"]),
]

@pytest.mark.parametrize("q,want", CASES)
def test_known_question_finds_its_sources(q, want):
    paths = {s["path"] for s in route(q)["sections"] + route(q)["definitions"]}
    missing = [w for w in want if w not in paths]
    assert not missing, (q, missing, sorted(paths))

def test_constraint_question_gets_full_reads():
    r = route("must it be one request per candidate?")
    assert r["sections"] and all(s["depth"] == "READ FULL" for s in r["sections"])

def test_definitions_added_for_named_primitive():
    r = route("is a noul right for this check")
    assert any(d["path"] == "docs/primitives__noul.md" for d in r["definitions"])

def test_no_match_says_so():
    out = subprocess.run([sys.executable, f"{CODE}/scripts/route.py", "zzqx flurb"], capture_output=True, text=True).stdout
    assert "no section found" in out

def test_read_prints_header_and_file_caveats():
    sid = next(s["id"] for s in route("re-ranking passages with typesafe")["sections"] if s["path"] == "cookbooks/rerank_typesafe.md")
    out = subprocess.run([sys.executable, f"{CODE}/scripts/read.py", sid], capture_output=True, text=True, check=True).stdout
    assert out.startswith("SOURCE: cookbooks/rerank_typesafe.md#") and "KIND: cookbook example" in out
    assert "for clarity" in out

def test_singular_candidate_routes_to_rerank():
    ids = [s["id"] for s in route("a cookbook does one request per candidate; must we?")["sections"]]
    assert any(i.startswith("cookbooks/rerank_typesafe") for i in ids), ids

def test_topic_words_need_word_start():
    assert route("does Jev handle accounts and updates well")["topics"] == []

def test_incident_questions_list_noul_structured_instructions():
    for q in ["30 passages as 30 Nouls in one request with the query as state",
              "the rerank cookbook does one request per candidate, must we?"]:
        heads = [s["path"] + "#" + s["heading"] for s in route(q)["sections"]]
        assert "docs/primitives__noul.md#Structured instructions" in heads, (q, heads)

def test_paraphrases_route():
    cases = {"send all thirty candidate documents to Jev in a single API hit": "docs/concepts__state.md",
             "can Jev subtract two timestamps to work out someone's age": "cookbooks/date_extraction_cookbook.md",
             "400 labels, will a Choice handle that": "cookbooks/hierarchical_classification.md",
             "does the order I list the answers in bias what Jev picks": "cookbooks/consistency_choice_cookbook.md"}
    for q, p in cases.items():
        r = route(q)
        assert p in [s["path"] for s in r["sections"] + r["definitions"]], q

def test_no_duplicate_ids():
    r = route("what is state in Jev")
    ids = [s["id"] for s in r["sections"] + r["definitions"]]
    assert len(ids) == len(set(ids))

def test_malformed_topics_message(tmp_path):
    import shutil
    lib = tmp_path / "jev-sources"
    shutil.copytree(CODE, lib, ignore=shutil.ignore_patterns("__pycache__"))
    (lib / "topics.json").write_text('{"topics": [')
    r = subprocess.run([sys.executable, str(lib / "scripts/route.py"), "noul"], capture_output=True, text=True, env={**os.environ, "JEV_SOURCES_DATA": DATA})
    assert "topics.json is malformed" in (r.stderr + r.stdout) and "Traceback" not in r.stderr


def test_fresh_install_says_refresh(tmp_path):
    for script, args in (("route.py", ["noul"]), ("read.py", ["docs/concepts__state#0"]), ("build_index.py", [])):
        r = subprocess.run([sys.executable, f"{CODE}/scripts/{script}", *args], capture_output=True, text=True,
                           env={**os.environ, "JEV_SOURCES_DATA": str(tmp_path / "empty")})
        assert "refresh.sh --fetch" in (r.stdout + r.stderr) and "Traceback" not in r.stderr, script

def test_fetch_names_failed_pages(tmp_path, monkeypatch):
    sys.path.insert(0, f"{CODE}/scripts")
    import fetch
    monkeypatch.setattr(fetch, "DATA", str(tmp_path))
    def fake(url, tries=3):
        if url.endswith("llms.txt"):
            return "[a](https://docs.typesafe.ai/concepts/state.md) [b](https://docs.typesafe.ai/cookbooks/gone.md)"
        if "gone" in url or "cookbooks/" in url:
            raise OSError("HTTP Error 404")
        return "# State"
    monkeypatch.setattr(fetch, "get", fake)
    assert fetch.main() == 1
    assert (tmp_path / "docs" / "concepts__state.md").exists()
