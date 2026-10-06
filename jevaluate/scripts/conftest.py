"""Tests never read or write the real GitHub freeze cache (~/.cache/jevaluate): a confirmation stored by one test would let another pass."""
import pathlib, sys
import pytest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import rubric_text


@pytest.fixture(autouse=True)
def private_github_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(rubric_text, "GITHUB_CACHE", tmp_path / "github-freeze-cache.json")
