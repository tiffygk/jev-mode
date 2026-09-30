import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent / "scripts"))
import harness_status as hs

def test_next_step_and_file(tmp_path):
    led = tmp_path / "ledger.md"; led.write_text("done: picked 2026-10-01 5 projects\ndone: sized 2026-10-01 total 610k\n")
    rows = hs.status(led, "round", run_gates=False)
    nxt = [r for r in rows if r["state"] == "next"][0]
    assert nxt["step"] == "costs-approved" and nxt["open"] == "rating-round.md"
    assert [r["state"] for r in rows[:2]] == ["done", "done"] and all(r["state"] == "waiting" for r in rows[3:])

def test_status_runs_the_check(tmp_path, monkeypatch):
    led = tmp_path / "ledger.md"; led.write_text("done: rules-written 2026-10-01 x\ndone: materials-checked 2026-10-01 said so\n")
    monkeypatch.setattr(hs, "GATES", {"materials-checked": lambda: (False, "lint failed")})
    rows = hs.status(led, "rubric", run_gates=True)
    row = [r for r in rows if r["step"] == "materials-checked"][0]
    assert row["state"] == "next" and "lint failed" in row["detail"]

def test_gate_that_passes_is_marked_checked(tmp_path, monkeypatch):
    led = tmp_path / "ledger.md"; led.write_text("done: rules-written 2026-10-01 x\ndone: materials-checked 2026-10-01 ok\n")
    monkeypatch.setattr(hs, "GATES", {"materials-checked": lambda: (True, "lint clean")})
    row = [r for r in hs.status(led, "rubric") if r["step"] == "materials-checked"][0]
    assert row["state"] == "done" and row["checked"] is True

def test_gate_not_run_is_never_reported_checked(tmp_path):
    led = tmp_path / "ledger.md"; led.write_text("done: rules-written 2026-10-01 x\ndone: materials-checked 2026-10-01 ok\n")
    row = [r for r in hs.status(led, "rubric", run_gates=False) if r["step"] == "materials-checked"][0]
    assert row["state"] == "done" and row["checked"] is False

def test_missing_gate_script_is_a_failure_not_a_pass(tmp_path, monkeypatch):
    led = tmp_path / "ledger.md"
    led.write_text("".join(f"done: {s} 2026-10-01 x\n" for s, _ in hs.WORKFLOWS["round"][:7]) + "done: release-check 2026-10-01 said so\n")
    monkeypatch.setattr(hs, "REPO", tmp_path); monkeypatch.setattr(hs, "HERE", tmp_path / "nowhere")
    monkeypatch.setattr(hs, "GATES", hs.make_gates())
    row = [r for r in hs.status(led, "round") if r["step"] == "release-check"][0]
    assert row["state"] == "next" and "not found" in row["detail"]

def test_step_after_a_gap_waits(tmp_path):
    led = tmp_path / "ledger.md"; led.write_text("done: picked 2026-10-01 x\ndone: rated 2026-10-01 x\n")
    states = {r["step"]: r["state"] for r in hs.status(led, "round", run_gates=False)}
    assert states["sized"] == "next" and states["rated"] == "waiting"

def test_no_ledger_starts_at_the_first_step(tmp_path):
    assert hs.status(tmp_path / "none.md", "rubric", run_gates=False)[0]["state"] == "next"
