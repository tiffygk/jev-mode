"""Eval tests never call GitHub: 60 unauthenticated calls an hour are shared with real scoring, and a few test runs
used them up (2026-10-05). GitHub's side of the freeze check has its own tests in jevaluate/scripts/test_lock_round3.py."""
import pathlib, sys
import pytest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "jevaluate" / "scripts"))
import rubric_text


@pytest.fixture(autouse=True)
def github_confirms(monkeypatch):
    monkeypatch.setattr(rubric_text, "github_check", lambda tag, root=None: (True, ""))
