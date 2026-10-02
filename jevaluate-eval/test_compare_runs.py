import json, sys, pathlib, shutil, subprocess
HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE)); import compare_runs

def run(tmp, name, system="S", packets=None):
    d = tmp / name; (d / "packets").mkdir(parents=True)
    (d / "system.md").write_text(system); (d / "task.md").write_text("T")
    for k, v in (packets or {"a.md": "A"}).items(): (d / "packets" / k).write_text(v)
    return d

def test_identical_inputs(tmp_path):
    assert compare_runs.same_inputs(run(tmp_path, "s"), run(tmp_path, "c")) == ([], "")

def test_appended_notes_reported_apart(tmp_path):
    probs, extra = compare_runs.same_inputs(run(tmp_path, "s"), run(tmp_path, "c", system="S\n\nCodex note"))
    assert probs == [] and extra.strip() == "Codex note"

def test_changed_system_and_packet(tmp_path):
    probs, _ = compare_runs.same_inputs(run(tmp_path, "s", packets={"a.md": "A", "b.md": "B"}), run(tmp_path, "c", system="X", packets={"a.md": "A2"}))
    assert any("system.md" in p for p in probs) and any("a.md" in p for p in probs) and any("b.md" in p for p in probs)

def test_report_self_compare(tmp_path):
    src = pathlib.Path.home() / "Documents/jev-mode-finish/jevaluate-eval/.work/run-baseline"
    if not src.exists():
        import pytest; pytest.skip("saved Sonnet run not on this machine")
    r = subprocess.run([sys.executable, str(HERE / "compare_runs.py"), "report", str(src), str(src), "--reps", "3"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert "| jev-omni | tuning | 3/3 | 3/3 |" in r.stdout and "Inputs: identical" in r.stdout

def test_task_md_difference_caught(tmp_path):
    a, b = run(tmp_path, "s"), run(tmp_path, "c"); (b / "task.md").write_text("T2")
    assert "task.md differs" in compare_runs.same_inputs(a, b)[0]

def test_close_home_copies_back_a_refreshed_login(tmp_path, monkeypatch):
    import runners, time
    real = tmp_path / "real.json"; real.write_text("old"); monkeypatch.setenv("JEV_CODEX_AUTH", str(real))
    home = tmp_path / "h"; home.mkdir(); time.sleep(0.01); (home / "auth.json").write_text("new")
    runners.close_home(home)
    assert real.read_text() == "new" and not home.exists()
