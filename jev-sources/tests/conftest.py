import os
import shutil
import sys
import pytest


@pytest.fixture(autouse=True)
def no_side_effects(monkeypatch):
    """Every test: no usage log, no background docs check. Subprocess hooks inherit this environment."""
    monkeypatch.setenv("JEV_LOG", "off")
    monkeypatch.setenv("JEV_CHECK", "off")


@pytest.fixture(autouse=True)
def fresh_route_modules():
    """route and its helpers read the library path at import time; drop them after each test so the next import
    sees that test's library, not a temp one that is already gone."""
    yield
    for name in ("route", "route_check", "semantic", "build_index", "citations", "usage_log", "applicability", "jev", "read", "paths", "pages", "check_new", "fetch", "blog", "sources"):
        sys.modules.pop(name, None)


# --- the configured library is read only -------------------------------------------------------------------
LIB_PAGE_DIRS = ("docs", "cookbooks", "patterns", "blog", "raw")


def configured_library():
    return os.path.expanduser(os.environ.get("JEV_SOURCES_DATA") or "~/.claude/jev-sources-data")


def library_state(lib):
    """mtime of the index and of every page folder (a folder's mtime moves when a file in it is added or replaced);
    None for a missing item, so a new raw/ folder shows up as a change."""
    state = {}
    for name in ("sections.jsonl",) + LIB_PAGE_DIRS:
        try:
            state[name] = os.stat(os.path.join(lib, name)).st_mtime_ns
        except OSError:
            state[name] = None
    return state


def copy_library(src, dst):
    """Copy what the index and the routers read (pages, index, embeddings) from src into dst, without the source's
    permissions (the source may be read only on purpose). models/ is linked, not copied."""
    for dirpath, dirnames, filenames in os.walk(src):
        rel = os.path.relpath(dirpath, src)
        if rel == ".":
            dirnames[:] = [d for d in dirnames if d not in ("models", "logs", "archive", "notices")]
        os.makedirs(os.path.join(dst, rel), exist_ok=True)
        for f in filenames:
            shutil.copyfile(os.path.join(dirpath, f), os.path.join(dst, rel, f))
    if os.path.isdir(os.path.join(src, "models")) and not os.path.exists(os.path.join(dst, "models")):
        os.symlink(os.path.join(src, "models"), os.path.join(dst, "models"))
    return dst


# taken when this file is loaded, before any test runs (a conftest below the root misses pytest_sessionstart)
_START = {"lib": configured_library()}
_START["state"] = library_state(_START["lib"])


def pytest_sessionfinish(session, exitstatus):
    """A test that writes into the library it is pointed at fails the session, whatever else passed."""
    now = library_state(_START["lib"])
    if now != _START["state"]:
        changed = sorted(k for k in now if now[k] != _START["state"][k])
        sys.stderr.write("\nLIBRARY WRITTEN BY THE SUITE: %s changed under %s\n" % (", ".join(changed), _START["lib"]))
        session.exitstatus = 1


@pytest.fixture(scope="session")
def lib_copy(tmp_path_factory):
    """A private copy of the configured library; tests that build an index or write pages use this, never the original."""
    return copy_library(configured_library(), str(tmp_path_factory.mktemp("libcopy")))
