import json, pathlib, subprocess, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import pick_files as pf

def manifest(tmp, rows, files):
    (tmp / "files").mkdir(parents=True)
    head = "# Coverage manifest: o/r @ abc\n\n| file | chars | jev | decision | eval | note |\n|---|---|---|---|---|---|\n"
    (tmp / "manifest.md").write_text(head + "".join(f"| {p} | {c} | {j} | {d} | 0 |  |\n" for p, c, j, d in rows))
    for p, text in files.items(): (tmp / "files" / p.replace("/", "__")).write_text(text)
    return tmp

def test_readme_then_call_files_then_top_by_jev_plus_decision(tmp_path):
    m = manifest(tmp_path, [("README.md", 900, 1, 0), ("src/jev.ts", 800, 9, 2), ("src/a.ts", 500, 0, 5),
                            ("src/b.ts", 500, 1, 1), ("src/c.ts", 500, 0, 0), ("src/d.ts", 500, 0, 1)],
                 {"README.md": "x", "src/jev.ts": "import { TypeSafe } from '@typesafe-ai/sdk'\n", "src/a.ts": "", "src/b.ts": "", "src/c.ts": "", "src/d.ts": ""})
    assert pf.pick(m) == [["README.md", 3000], ["src/jev.ts", 3000], ["src/a.ts", 3000], ["src/b.ts", 3000]]

def test_every_call_file_kept_even_past_four(tmp_path):
    call = "fetch('https://api.typesafe.ai/v1/systemone')\n"
    rows = [("README.md", 1, 0, 0)] + [(f"s{i}.py", 1, 0, 0) for i in range(5)]
    m = manifest(tmp_path, rows, {"README.md": "x", **{f"s{i}.py": call for i in range(5)}})
    assert [p for p, _ in pf.pick(m)] == ["README.md"] + [f"s{i}.py" for i in range(5)]

def test_code_then_docs_and_tests_then_data_and_zero_hits_skipped(tmp_path):
    m = manifest(tmp_path, [("README.md", 1, 0, 0), ("results/r.jsonl", 1, 90, 0), ("docs/z.md", 1, 30, 2), ("tests/test_a.py", 1, 40, 0),
                            ("src/y.py", 1, 1, 1), ("src/b.py", 1, 2, 0), ("src/zero.py", 1, 0, 0)],
                 {"README.md": "x", "results/r.jsonl": "", "docs/z.md": "", "tests/test_a.py": "", "src/y.py": "", "src/b.py": "", "src/zero.py": ""})
    assert [p for p, _ in pf.pick(m)] == ["README.md", "src/b.py", "src/y.py", "tests/test_a.py"]

def test_data_files_only_when_nothing_else(tmp_path):
    m = manifest(tmp_path, [("README.md", 1, 0, 0), ("results/r.jsonl", 1, 90, 0), ("docs/z.md", 1, 3, 0)],
                 {"README.md": "x", "results/r.jsonl": "", "docs/z.md": ""})
    assert [p for p, _ in pf.pick(m)] == ["README.md", "docs/z.md", "results/r.jsonl"]

def test_no_readme_still_picks(tmp_path):
    m = manifest(tmp_path, [("main.go", 1, 3, 0)], {"main.go": ""})
    assert pf.pick(m) == [["main.go", 3000]]

def test_cli_prints_json(tmp_path):
    m = manifest(tmp_path, [("README.md", 1, 0, 0)], {"README.md": "x"})
    r = subprocess.run([sys.executable, str(pathlib.Path(pf.__file__)), str(m)], capture_output=True, text=True)
    assert r.returncode == 0 and json.loads(r.stdout) == [["README.md", 3000]]

def test_demo_and_example_code_rank_after_core_code(tmp_path):
    m = manifest(tmp_path, [("README.md", 1, 0, 0), ("demo/App/main.swift", 1, 11, 2), ("src/compact.ts", 1, 6, 7), ("examples/e.py", 1, 20, 0)],
                 {"README.md": "x", "demo/App/main.swift": "", "src/compact.ts": "", "examples/e.py": ""})
    assert [p for p, _ in pf.pick(m)] == ["README.md", "src/compact.ts", "examples/e.py", "demo/App/main.swift"]
