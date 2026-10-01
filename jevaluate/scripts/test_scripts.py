"""Tests for coverage_manifest.py, screen_list.py and jev_callsites.py.
Network tests are opt-in: JEV_NETWORK=1 pytest test_scripts.py"""
import json, os, pathlib, subprocess, sys
import pytest

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
NET = pytest.mark.skipif(not os.environ.get("JEV_NETWORK"), reason="set JEV_NETWORK=1 for network tests")


# ---------- coverage_manifest ----------
def test_saved_name_never_starts_with_dot(tmp_path):
    import coverage_manifest as cm
    tree = [{"path": ".github/workflows/ci.yml", "type": "blob", "size": 40},
            {"path": "src/client.py", "type": "blob", "size": 40}]
    files = {".github/workflows/ci.yml": "name: ci\nenv: TYPESAFE_API_KEY\n",
             "src/client.py": "import typesafe\n"}
    cm.build_manifest("o/r", tmp_path, {"stargazers_count": 1, "pushed_at": "x"}, "a" * 40, tree, files.get)
    saved = sorted(p.name for p in (tmp_path / "files").iterdir())
    assert saved and not any(n.startswith(".") for n in saved), saved
    assert any("github__workflows__ci.yml" in n for n in saved)
    manifest = (tmp_path / "manifest.md").read_text()
    assert ".github/workflows/ci.yml" in manifest  # manifest still shows the true path


# ---------- screen_list ----------
README = """# Awesome Jev

## Contents
- [Official](#official)

## Official
- [Docs](https://docs.typesafe.ai/introduction) - API docs.

## Applications
- [One](https://github.com/a/one) - first app
- [Two](https://github.com/b/two.git) - second
- [One again](https://github.com/A/One) - duplicate of one
- [Blog](https://example.com/post) - not github

## Agent Tools
- [Three](https://github.com/c/three) - tool

## Contribute
- [Rules](https://github.com/x/y) - ignored
"""


def test_parser_counts_sections_and_dedupes():
    import screen_list as sl
    rows, counts = sl.parse_readme(README)
    assert counts == {"Official": 1, "Applications": 3, "Agent Tools": 1}
    assert [r["repo"] for r in rows if r["section"] == "Applications"] == ["a/one", "b/two", ""]


def test_strict_pattern_ignores_prose_from_typesafe():
    import screen_list as sl
    assert not sl.strict_hit("Built with Jev, a model\nfrom\nTypeSafe that answers questions.\n")
    assert sl.strict_hit("import os\nfrom typesafe import Client\n")
    assert sl.strict_hit("client = Typesafe::Client.new\n")
    assert sl.strict_hit('url = "https://api.typesafe.ai/v1/x"')


def test_classify_uses_tree_and_raw_files_not_code_search():
    import screen_list as sl
    tree = ["README.md", "lib/typesafe/sdk.rb", "notes.txt"]
    raw = {"lib/typesafe/sdk.rb": "module Typesafe\n  Client = Typesafe::Client\nend\n", "README.md": "from\nTypeSafe"}
    cls, ev = sl.classify(tree, raw.get)
    assert cls == "hosted call" and "lib/typesafe/sdk.rb" in ev
    raw["app.py"] = "print('hi')\nfrom\nTypeSafe\n"
    cls, _ = sl.classify(["README.md", "app.py"], raw.get)
    assert cls == "no hosted call found"


def test_known_yes_no_check_aborts_when_pattern_wrong():
    import screen_list as sl
    yes_tree, no_tree = ["a.py"], ["b.py"]
    trees = {"y/y": (yes_tree, {"a.py": "from typesafe import X"}), "n/n": (no_tree, {"b.py": "from\nTypeSafe"})}
    load = lambda repo: (trees[repo][0], trees[repo][1].get)
    sl.check_known("y/y", "n/n", load)  # passes
    trees["n/n"] = (no_tree, {"b.py": "import typesafe"})
    with pytest.raises(SystemExit) as e:
        sl.check_known("y/y", "n/n", load)
    assert "known-no" in str(e.value)
    trees["n/n"] = (no_tree, {"b.py": "x"}); trees["y/y"] = (yes_tree, {"a.py": "x"})
    with pytest.raises(SystemExit) as e:
        sl.check_known("y/y", "n/n", load)
    assert "known-yes" in str(e.value)


def test_cli_refuses_without_known_flags(tmp_path):
    readme = tmp_path / "r.md"; readme.write_text(README)
    r = subprocess.run([sys.executable, str(HERE / "screen_list.py"), str(readme)], capture_output=True, text=True)
    assert r.returncode != 0 and "--known-yes" in r.stderr and "--known-no" in r.stderr
    r = subprocess.run([sys.executable, str(HERE / "screen_list.py"), str(readme), "--known-yes", "a/b"], capture_output=True, text=True)
    assert r.returncode != 0 and "--known-no" in r.stderr


def test_cli_dry_run_prints_parser_counts(tmp_path):
    readme = tmp_path / "r.md"; readme.write_text(README)
    r = subprocess.run([sys.executable, str(HERE / "screen_list.py"), str(readme), "--known-yes", "a/b", "--known-no", "c/d", "--counts-only"],
                       capture_output=True, text=True)
    assert r.returncode == 0 and "Applications: 3" in r.stdout and "total: 5" in r.stdout, r.stdout + r.stderr


# ---------- jev_callsites ----------
def callsites(path):
    r = subprocess.run([sys.executable, str(HERE / "jev_callsites.py"), str(path)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return json.JSONDecoder().raw_decode(r.stdout)[0]


def make_tree(root, files):
    for rel, text in files.items():
        p = pathlib.Path(root) / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(text)
    return root


def test_imitation_adapter_docs_and_fixtures_are_mentions_not_hosted_calls(tmp_path):
    make_tree(tmp_path, {
        "src/adapter.py": "# serves the System One API locally\ndef system_one(questions):\n    return Noul('x')\n# route: /v1/systemone\n",
        "src/metrics.py": "from jevmlx.evalmetrics import typesafe_agreement\n",
        "tests/test_api.py": "URL = 'https://api.typesafe.ai/v1/systemone'\nsystem_one(1)\n",
        "test_top.py": "URL = 'https://api.typesafe.ai'\n",
        "docs/api.py": "URL = 'https://api.typesafe.ai'\n",
        "fixtures/resp.yaml": "url: https://api.typesafe.ai\n",
        "examples/data.json": '{"url": "https://api.typesafe.ai"}',
        "README.md": "Calls api.typesafe.ai and typesafe/jev-1.13.0\n"})
    out = callsites(tmp_path)
    assert out["hosted_calls"] == 0
    assert out["mentions"] > 0 and "call_sites" not in out


@pytest.mark.parametrize("name,text", [
    ("lib/typesafe/sdk.rb", 'DEFAULT_BASE_URL = "https://api.typesafe.ai"\n'),
    ("src/client.py", 'DEFAULT_MODEL = "~typesafe/jev-latest"\n'),
    ("app/main.py", "import os\nfrom typesafe import Client\n"),
    ("app/main2.py", "import typesafe_ai\n"),
    ("web/index.ts", "import { TypeSafe } from '@typesafe-ai/sdk'\n"),
    ("scripts/run.sh", "curl --model typesafe/jev-1.13 x\n"),
    ("lib/app.rb", "client = Typesafe::SDK::Client.new(api_key: k)\n"),
    ("src/model.ts", 'import { typeSafeAi } from "@ai-sdk/typesafe-ai";\n'),
    ("src/headline.ts", 'import { TypeSafeClient } from "@effect/ai-typesafe";\n'),
    ("CODE.gs", "const MODEL = 'typesafe/jev-latest';\n"),
    ("src/agent.ts", 'const autoModel = "typesafe-ai/jev";\n'),
])
def test_endpoint_sdk_or_gateway_id_counts_as_hosted_call(tmp_path, name, text):
    make_tree(tmp_path, {name: text})
    assert callsites(tmp_path)["hosted_calls"] > 0


@pytest.mark.parametrize("name", ["Sources/JevClient.swift", "include/remote.hpp", "src/remote.cpp", "Client.cs", "lib/client.ex",
                                  "src/Client.scala", "lib/client.dart", "web/app.jsx", "web/app.cjs"])
def test_hosted_calls_found_in_other_languages(tmp_path, name):
    make_tree(tmp_path, {name: 'let endpoint = "https://api.typesafe.ai/v1/systemone"\n'})
    assert callsites(tmp_path)["hosted_calls"] > 0


@pytest.mark.parametrize("name,text", [
    ("scripts/setup.sh", "git clone https://github.com/typesafe-ai/jev-tools\n"),
    ("setup.py", "# pip install git+https://github.com/typesafe-ai/jev-tools\n"),
    ("config.yaml", "workdir: ~/typesafe-ai/jev-lab\n"),
    ("scripts/freeze.py", "# carry the published TypeSafe/Jev answer in _meta\n"),
])
def test_urls_and_paths_naming_the_typesafe_org_are_not_hosted_calls(tmp_path, name, text):
    make_tree(tmp_path, {name: text})
    assert callsites(tmp_path)["hosted_calls"] == 0


def test_json_data_files_do_not_count_as_hosted_calls(tmp_path):
    make_tree(tmp_path, {"analysis/run.json": '{"served_model": "typesafe/jev-1.13-20260917"}'})
    assert callsites(tmp_path)["hosted_calls"] == 0


@NET
@pytest.mark.parametrize("repo,expect_zero", [("bnsd55/jevmlx", True), ("joshmn/typesafe-sdk", False), ("chepyle/jev-test", False)])
def test_real_repos_hosted_calls(tmp_path, repo, expect_zero):
    subprocess.run(["gh", "repo", "clone", repo, str(tmp_path / "r"), "--", "--depth", "1", "-q"], check=True)
    out = callsites(tmp_path / "r")
    assert (out["hosted_calls"] == 0) == expect_zero, out


# Pinned real repos from the 2026-09-30 screen: each was misread by an earlier version of the detector, or tests the docs rule.
@NET
@pytest.mark.parametrize("repo,sha,calls", [
    ("noelzappy/tripwire", "b727e6f928f4675c5171c5d36f4f8040a2f02107", True),         # AI SDK TypeSafe provider
    ("jarrodwatts/jev-trader", "b587759e459ea049590102e54a0b07800864cdc3", True),     # AI SDK TypeSafe provider
    ("tostechbr/partway", "3b57b886abfd9df044ab3143c7884904dc303325", True),          # Swift, posts to api.typesafe.ai
    ("st1ne/jev-gem-scan", "6adc00e8e227c28d065b82f3099273a2b1a83ec1", False),       # a stub named call_jev_api
    ("buildaistack/jev-agent-harness", "e45867439211ce0a9aa93635f8add008a640c0c4", False),  # calls shown only in design docs
])
def test_pinned_real_repos(tmp_path, repo, sha, calls):
    r = tmp_path / "r"
    subprocess.run(["git", "init", "-q", str(r)], check=True)
    subprocess.run(["git", "-C", str(r), "fetch", "-q", "--depth", "1", f"https://github.com/{repo}", sha], check=True)
    subprocess.run(["git", "-C", str(r), "checkout", "-q", "FETCH_HEAD"], check=True)
    out = callsites(r)
    assert (out["hosted_calls"] > 0) == calls, out


@NET
def test_real_known_yes_known_no_screen():
    import screen_list as sl
    sl.check_known("joshmn/typesafe-sdk", "bnsd55/jevmlx", sl.load_repo)


# ---------- data-file cap ----------
import json as _j
from coverage_manifest import cap_data, DATA_CAP


def test_question_catalogue_kept_whole():
    text = _j.dumps([{"question": "Is `x` spam?", "type": "noul", "threshold": 0.8}] * 900)
    out, note = cap_data("checks/catalogue.json", text, {"jev": 900, "decision": 900, "eval": 0}, {})
    assert len(text) > DATA_CAP and out == text and note == ""


def test_results_file_summarized():
    text = _j.dumps({"accuracy": 0.91, "n": 300, "rows": [{"id": i, "ok": True} for i in range(3000)]})
    out, note = cap_data("bench/report.json", text, {"jev": 0, "decision": 0, "eval": 40}, {})
    assert note == "sampled: results summary" and "accuracy" in out and "records" in out and len(out) < 4000


def test_fixture_without_jev_sampled():
    out, note = cap_data("tests/fixtures/files.json", "x" * 60_000, {"jev": 0, "decision": 0, "eval": 0}, {})
    assert note == "sampled: no Jev content" and len(out) <= 1_200


def test_repeat_shape_summarized():
    seen, text = {}, _j.dumps({"accuracy": 0.9, "rows": list(range(9000))})
    cap_data("r/a/report.json", text, {"jev": 0, "decision": 0, "eval": 5}, seen)
    out, note = cap_data("r/b/report.json", text + " " * 100, {"jev": 0, "decision": 0, "eval": 5}, seen)
    assert note == "sampled: repeat of r/a/report.json"


def test_repeat_checked_before_keep_whole():
    seen, text = {}, _j.dumps({"trace": [{"question": "Is x spam?", "confidence": 0.9}] * 900})
    cap_data("golden/a/trace.json", text, {"jev": 900, "decision": 900, "eval": 0}, seen)
    assert cap_data("golden/b/trace.json", text, {"jev": 900, "decision": 900, "eval": 0}, seen)[1] == "sampled: repeat of golden/a/trace.json"


def test_small_data_file_untouched():
    assert cap_data("cfg.json", "{}", {"jev": 0, "decision": 0, "eval": 0}, {}) == ("{}", "")


def test_build_manifest_notes_column_and_files_full(tmp_path):
    import coverage_manifest as cm
    big = _j.dumps({"accuracy": 0.9, "rows": list(range(9000))})
    tree = [{"path": "bench/report.json", "type": "blob", "size": len(big)},
            {"path": "src/c.py", "type": "blob", "size": 20}]
    files = {"bench/report.json": big, "src/c.py": "import typesafe  # accuracy\n"}
    cm.build_manifest("o/r", tmp_path, {}, "a" * 40, tree, files.get)
    man = (tmp_path / "manifest.md").read_text()
    assert "| file | chars | jev | decision | eval | note |" in man and "~" in man and "tokens" in man
    assert (tmp_path / "files_full" / "bench__report.json").read_text() == big
    assert "Never read files_full/" in man


def test_manifest_header_omits_the_files_full_warning_when_nothing_was_sampled(tmp_path):
    import coverage_manifest as cm
    cm.build_manifest("o/r", tmp_path, {}, "a" * 40, [{"path": "src/c.py", "type": "blob", "size": 20}], {"src/c.py": "import typesafe\n"}.get)
    assert "files_full" not in (tmp_path / "manifest.md").read_text() and not (tmp_path / "files_full").exists()


def test_manifest_commit_flag_uses_pinned_sha(monkeypatch, tmp_path):
    import coverage_manifest as cm
    calls = []
    def fake_gh(p):
        calls.append(p)
        if p.startswith("repos/o/r/git/trees/"): return {"tree": []}
        return {"default_branch": "main", "sha": "b" * 40}
    monkeypatch.setattr(cm, "_gh", fake_gh)
    cm.main("o/r", tmp_path, commit="c" * 40)
    assert any("git/trees/" + "c" * 40 in c for c in calls)
    assert not any("commits/main" in c for c in calls)


def test_callsites_json_flag_prints_only_json(tmp_path):
    make_tree(tmp_path, {"a.py": "import x\n# jev typesafe\n"})
    r = subprocess.run([sys.executable, str(HERE / "jev_callsites.py"), str(tmp_path), "--json"], capture_output=True, text=True)
    assert r.returncode == 0 and "hosted_calls" in json.loads(r.stdout)
    assert "NOTE" in r.stderr


def test_same_named_lists_with_different_elements_both_kept():
    seen = {}
    a = _j.dumps([{"question": "Is x spam?", "type": "noul"}] * 900)
    b = _j.dumps([{"prompt": "Pick one", "options": ["a"]}] * 900)
    h = {"jev": 5, "decision": 12, "eval": 0}
    assert cap_data("a/questions.json", a, h, seen) == (a, "")
    assert cap_data("b/questions.json", b, h, seen) == (b, "")


def test_keep_whole_by_decision_hit_threshold():
    big = _j.dumps({"rows": list(range(9000))})
    assert cap_data("checks/catalogue.json", big, {"jev": 343, "decision": 33, "eval": 42}, {}) == (big, "")
    for path, h in (("corpus/scores.json", {"jev": 279, "decision": 1, "eval": 63}),
                    ("checks/fixtures.json", {"jev": 134, "decision": 7, "eval": 27})):
        out, note = cap_data(path, big, h, {})
        assert note == "sampled: results summary" and len(out) < 4000


# ---------- call_lines: client construction ----------
import jev_callsites as jc

@pytest.mark.parametrize("line", ["client = TypeSafe(api_key=k)", "c = TypeSafeClient(api_key=k)", "const t = new TypeSafe({ apiKey })",
                                  "c = typesafe_sdk.TypeSafeClient(k)", "r = typesafe.system_one(state, qs)",
                                  "const provider = createTypeSafeAi({ apiKey })", "client = Typesafe(key)", "let c = TypesafeClient(k)"])
def test_construction_lines_count(line):
    assert jc.lines_with_calls({1: line}) == [1]

@pytest.mark.parametrize("line", ["def _build_typesafe() -> None:", "def typesafe_agreement(records):", "rows = _typesafe_lines(records)",
                                  "x = build_typesafe_report(data)", 'print("Set TYPESAFE_API_KEY (env) first")'])
def test_helper_functions_named_typesafe_are_not_calls(line):
    assert jc.lines_with_calls({1: line}) == []

def test_calls_on_a_constructed_name_count():
    assert jc.lines_with_calls({1: "client = TypeSafe(k)", 2: "x = 1", 3: "r = client.noul(q)"}) == [1, 3]

def test_ai_sdk_evaluate_counts_in_a_file_that_imports_a_typesafe_provider():
    lines = {2: 'import { createTypeSafeAi } from "@ai-sdk/typesafe-ai";', 20: "const provider = createTypeSafeAi({ apiKey });",
             29: "const r = await experimental_evaluate({"}
    assert 29 in jc.lines_with_calls(lines)
    assert jc.lines_with_calls({29: "const r = await experimental_evaluate({"}) == []
    assert 50 not in jc.lines_with_calls({2: 'import { createTypeSafeAi } from "@ai-sdk/typesafe-ai";', 50: "public JevAnswers evaluate(String state) {"})


def test_calls_in_applies_the_broad_rule_to_non_test_files_only(tmp_path):
    assert jc.calls_in([("a/Config.java", {1: "x = new TypeSafeJevClient(k);"}), ("tests/t.py", {1: "c = TypeSafe(k)"})]) == {"a/Config.java": [1]}
    d = tmp_path / "files"; d.mkdir(); (d / "a__Config.java").write_text("x = new TypeSafeJevClient(k);\n")
    assert jc.call_lines(d) == {"a/Config.java": [1]}


@pytest.mark.parametrize("path", ["examples/demo.ts", "example/a.py", "samples/run.py", "sample/run.py", "benchmarks/x.py", "benchmark/x.py",
                                  "bench/x.py", "src/examples/a.go", "scripts/bench.mjs", "scripts/benchmark_jev.py", "Bench_run.py"])
def test_example_and_benchmark_paths_are_not_non_test_code(path):
    assert not jc.counts_as_hosted_path(pathlib.PurePath(path))

@pytest.mark.parametrize("path", ["src/app.py", "demo/app.py", "demos/app.py", "evals/run.py", "eval/run.py", "lib/benchy/x.py", "src/embench.py", "src/sampler.py"])
def test_demo_and_eval_folders_and_lookalike_names_still_count(path):
    assert jc.counts_as_hosted_path(pathlib.PurePath(path))


# ---------- citable lines: what an F0 yes may cite (fix 1, 2026-09-30) ----------
REAL_CALL = "client = TypeSafeClient(api_key=k)"

@pytest.mark.parametrize("line", [
    '    "@typesafe-ai/sdk": "^0.6.0",', "typesafe-ai==1.2.0", "gem 'typesafe'",
    "throw new TypeSafeError('bad key')", "raise TypeSafeError('bad key')", "} catch (TypeSafeError e) {",
    "# POST https://api.typesafe.ai/v1/systemone", "// see https://api.typesafe.ai for docs", " * base url: api.typesafe.ai",
    "class TypeSafeClient {", "class TypeSafeClient(Base):", "  def TypeSafeClient(self):", "  constructor(key) {  ", "public TypeSafeClient(String key) {",
    "function TypeSafeClient(key) {", "func NewTypeSafeClient(key string) *Client {",
    "const HOSTED = /api.typesafe.ai|typesafe-ai\\/jev/i;", "HOSTED = re.compile(r'api.typesafe.ai')",
    '    "https://api.typesafe.ai/v1/systemone",', "from typesafe import TypeSafeClient", "import { TypeSafe } from '@typesafe-ai/sdk';",
    "const { TypeSafe } = require('@typesafe-ai/sdk');"])
def test_non_call_lines_are_not_citable(line):
    assert jc.lines_citable({1: REAL_CALL, 2: line}) == [1]

def test_a_block_comment_and_a_docstring_are_not_citable():
    lines = {1: REAL_CALL, 2: "/*", 3: "  c = new TypeSafeClient(k);", 4: "*/", 5: '"""', 6: "x = TypeSafe(k)", 7: '"""'}
    assert jc.lines_citable(lines) == [1]

@pytest.mark.parametrize("line", [REAL_CALL, "r = client.noul(state, q)", 'BASE = "https://api.typesafe.ai/v1"',
                                  "requests.post('https://api.typesafe.ai/v1/systemone', json=b)", '  model: "typesafe-ai/jev-1.13.0",',
                                  'const r = await evaluate({ model: "typesafe-ai/jev" })', '  "model": "typesafe/jev-1.13.0",',
                                  "c = TypeSafe(k)  # typesafe client"])
def test_real_call_lines_are_citable(line):
    assert jc.lines_citable({1: REAL_CALL, 2: "x = 1", 3: line}) == [1, 3]

def test_citable_in_skips_test_files():
    assert jc.citable_in([("a/bot.py", {1: REAL_CALL}), ("tests/t.py", {1: REAL_CALL})]) == {"a/bot.py": [1]}


# ---------- citable lines, broad form: any call expression in a file that holds a hosted marker (fix 2, 2026-09-30) ----------
def test_async_client_construction_is_citable():
    assert jc.lines_citable({1: "client = AsyncTypeSafeClient(api_key=k)", 2: "r = await client.noul(q)"}) == [1, 2]
    assert jc.lines_citable({1: "const c = new SyncTypeSafeClient({ apiKey })"}) == [1]

def test_a_send_through_a_client_accessor_is_citable_in_a_file_that_builds_the_client():
    lines = {1: "from typesafe import TypeSafeClient", 2: "class Judge:", 3: "    def _sync_client(self): return TypeSafeClient()", 4: "        return self._sync_client().system_one(state, QUESTIONS)"}
    assert 4 in jc.lines_citable(lines)

def test_an_import_alone_does_not_make_other_calls_citable():
    assert jc.lines_citable({1: "from typesafe import TypeSafeClient", 2: "x = self._sync_client().system_one(s)"}) == []

def test_urlopen_of_a_request_built_with_the_api_url_is_citable():
    lines = {1: "import urllib.request", 2: "req = urllib.request.Request('https://api.typesafe.ai/v1/systemone', data=body)", 3: "with urllib.request.urlopen(req) as r:", 4: "    data = r.read()"}
    assert {2, 3} <= set(jc.lines_citable(lines)) and 1 not in jc.lines_citable(lines)

def test_call_expressions_are_not_citable_in_a_file_with_no_hosted_marker():
    assert jc.lines_citable({1: "import urllib.request", 2: "with urllib.request.urlopen(req) as r:", 3: "x = self._sync_client().system_one(s)"}) == []

def test_a_comment_or_regex_or_import_alone_is_not_a_hosted_marker():
    lines = {1: "# talks to https://api.typesafe.ai", 2: "RX = re.compile(r'api.typesafe.ai')", 3: "import typesafe_docs_helper", 4: "x = send(req)"}
    assert jc.lines_citable(lines) == []

def test_control_flow_lines_are_not_call_expressions():
    lines = {1: "client = TypeSafeClient(k)", 2: "if (ready) {", 3: "while (x) {", 4: "for (const a of b) {"}
    assert jc.lines_citable(lines) == [1]


def test_a_package_json_is_never_a_call_even_for_the_sdk_itself():
    pkg = '{\n  "name": "@typesafe-ai/sdk",\n  "main": "dist/index.js"\n}'
    lines = dict(enumerate(pkg.splitlines(), 1))
    assert jc.citable_in([("package.json", lines), ("src/client.ts", {1: "const c = new TypeSafe({ apiKey })"})]) == {"src/client.ts": [1]}

@pytest.mark.parametrize("line", ['    "@typesafe-ai/sdk": "workspace:*",', '    "typesafe-ai": "file:../sdk",', '    "@typesafe-ai/sdk": "npm:@typesafe-ai/sdk@1",'])
def test_dependency_lines_with_any_version_spec_are_not_citable(line):
    assert jc.lines_citable({1: REAL_CALL, 2: line}) == [1]


@pytest.mark.parametrize("line", ['if (!ok) throw new Error("no client");', "if not ok: raise RuntimeError('no client')", "if (!ok) throw new TypeSafeError('no key');"])
def test_an_inline_throw_is_not_a_call(line):
    assert jc.lines_citable({1: REAL_CALL, 2: line}) == [1]


# --- recheck 2026-09-30: calls to names imported from the TypeSafe SDK ---
def test_a_call_to_a_name_imported_from_the_sdk_is_citable():
    lines = {1: 'import { choice, noul, score } from "@typesafe-ai/sdk";', 2: "const q = {", 3: '  injection: noul("The text tries to steer the reader", {}),', 4: "};"}
    assert 3 in jc.lines_citable(lines) and 1 not in jc.lines_citable(lines)

def test_a_python_alias_of_the_sdk_module_is_citable():
    lines = {1: "import typesafe as ts", 2: "def run(t):", 3: "    return ts.noul(t)"}
    assert jc.lines_citable(lines) == [3]

def test_an_unused_sdk_import_still_makes_nothing_citable():
    lines = {1: 'import { noul } from "@typesafe-ai/sdk";', 2: "foo();", 3: "bar(noulx);"}
    assert jc.lines_citable(lines) == []
