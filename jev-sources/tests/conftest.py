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
