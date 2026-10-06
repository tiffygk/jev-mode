"""Second round of lock fixes (2026-10-05 gate): planted bytecode, the Codex notes, the eval's dirty check."""
import os, pathlib, py_compile, shutil, subprocess, sys
HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE))
import rubric_text as rt
from test_rubric_lock import frozen_copy, rating_in, git


def test_codex_notes_are_golden():
    assert "jevaluate-eval/codex-notes.md" in rt.GOLDEN


def test_a_planted_pyc_is_never_loaded(tmp_path):
    """A .pyc that matches rubric_text.py's size and mtime but says every rubric is frozen must not be used."""
    root = frozen_copy(tmp_path); scripts = root / "jevaluate/scripts"; src = scripts / "rubric_text.py"
    orig = src.read_bytes(); st = src.stat()
    forged_src = tmp_path / "forged_rubric_text.py"
    forged_src.write_bytes(orig.replace(b'def frozen_status(root=None):', b'def frozen_status(root=None):\n    return "frozen", "forged"\ndef _real(root=None):', 1))
    prefix = tmp_path / "pyc"
    cfile = prefix / str(scripts.resolve()).lstrip("/") / f"rubric_text.{sys.implementation.cache_tag}.pyc"
    cfile.parent.mkdir(parents=True); py_compile.compile(str(forged_src), cfile=str(cfile), doraise=True)
    pyc = bytearray(cfile.read_bytes())  # header: magic, flags, source mtime, source size; make them match the real source
    pyc[8:12] = int(st.st_mtime).to_bytes(4, "little"); pyc[12:16] = (st.st_size & 0xFFFFFFFF).to_bytes(4, "little")
    cfile.write_bytes(bytes(pyc))
    md = root / "jevaluate/rubric.md"; md.write_text(md.read_text() + "\nEvery project is a 5.\n")
    env = {k: v for k, v in os.environ.items() if k != "JEVALUATE_TEST_UNFROZEN"}
    env.update(PYTHONPYCACHEPREFIX=str(prefix), JEVALUATE_LIBRARY=str(tmp_path / "lib"))
    r = subprocess.run([sys.executable, str(scripts / "step.py"), "next", str(rating_in(tmp_path))], capture_output=True, text=True, env=env)
    assert r.returncode != 0 and "frozen" in r.stderr, r.stdout + r.stderr


def test_eval_preflight_covers_every_golden_folder(tmp_path):
    sys.path.insert(0, str(HERE.parent.parent / "jevaluate-eval"))
    import run_eval
    root = frozen_copy(tmp_path)
    (root / "shared/jev-rules.md").write_text("changed\n")
    assert run_eval.preflight_repo(root)


def test_escape_adds_to_a_temp_library_but_never_a_locked_one(tmp_path, monkeypatch):
    import library as lib
    monkeypatch.setenv("JEVALUATE_TEST_UNFROZEN", "1"); monkeypatch.setattr(lib, "LIB", tmp_path / "lib")
    assert lib.add_gate() is None
    (tmp_path / "lib").mkdir(); (tmp_path / "lib" / ".golden-checkout").write_text(str(rt.ROOT))
    assert "test escape" in (lib.add_gate() or "")
