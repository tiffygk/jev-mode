"""Repo-wide test setup: hide the machine's own git settings, so a test that needs a git identity fails here as it
would on CI (2026-10-06: a test committed without one, passed locally and failed on the runner)."""
import os
import pytest


@pytest.fixture(autouse=True)
def _ci_equal_git(monkeypatch, tmp_path_factory):
    empty = tmp_path_factory.getbasetemp() / "gitconfig-ci"
    # useConfigOnly: no identity invented from the host name, as on a CI runner
    empty.write_text("[user]\n\tuseConfigOnly = true\n")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(empty))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    for k in ("GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL", "EMAIL"):
        monkeypatch.delenv(k, raising=False)
