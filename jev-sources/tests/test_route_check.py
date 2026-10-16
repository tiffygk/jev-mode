import importlib, json, os, subprocess, sys
import pytest
CODE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(CODE, "scripts"))


def _reload():
    pytest.importorskip("numpy")  # semantic.py needs it; the library fixtures reload semantic
    import paths, semantic, route, build_index, route_check, check_new
    for m in (paths, semantic, route, build_index, route_check, check_new):
        importlib.reload(m)
    return route, build_index, route_check, check_new


@pytest.fixture(autouse=True)
def lib(tmp_path, monkeypatch):
    """Every test: a temp library, never ~/.claude/jev-sources-data. Modules reload with it and again at teardown."""
    monkeypatch.setenv("JEV_SOURCES_DATA", str(tmp_path))
    monkeypatch.setenv("JEV_SEMANTIC", "off")
    mods = _reload()
    yield tmp_path, mods
    monkeypatch.undo()
    _reload()


def secs(*rows):
    return {"sections": [{"heading": h, "path": p, "depth": d} for h, p, d in rows]}


def test_hit_matches_by_heading(lib):
    _, (R, B, rc, cn) = lib
    assert rc.hit(secs(("Pin a model", "docs/a.md", "EXTRACT")), {"q": "x", "heading": "Pin a model"})
    assert not rc.hit(secs(("Pin a model", "docs/a.md", "EXTRACT")), {"q": "x", "heading": "Batch limits"})


def test_hit_also_needs_the_path_when_the_question_gives_one(lib):
    _, (R, B, rc, cn) = lib
    res = secs(("Pin a model", "docs/b.md", "EXTRACT"))
    assert not rc.hit(res, {"q": "x", "heading": "Pin a model", "path": "docs/a.md"})
    assert rc.hit(res, {"q": "x", "heading": "Pin a model", "path": "docs/b.md"})


def test_strict_question_needs_read_full(lib):
    _, (R, B, rc, cn) = lib
    q = {"q": "x", "heading": "Pin a model", "strict": True}
    assert not rc.hit(secs(("Pin a model", "docs/a.md", "EXTRACT")), q)
    assert rc.hit(secs(("Pin a model", "docs/a.md", "READ FULL")), q)


def test_loose_question_accepts_extract(lib):
    _, (R, B, rc, cn) = lib
    q = {"q": "x", "heading": "Pin a model", "strict": False}
    assert rc.hit(secs(("Pin a model", "docs/a.md", "EXTRACT")), q)


def test_summary_names_paraphrase_misses_without_a_bar_warning_at_or_above_80(lib):
    _, (R, B, rc, cn) = lib
    rep = {"keywords": {"hits": 8, "total": 10, "strict_misses": [], "misses": []},
           "meaning": {"hits": 8, "total": 10, "strict_misses": [], "misses": ["Pin a model <- how do I pin it"]}}
    s = rc.summary(rep)
    assert "8/10 paraphrase questions" in s
    assert "below the 80% bar" not in s
    assert "release questions missed" not in s
    assert "Paraphrase misses: Pin a model <- how do I pin it" in s


def test_summary_says_below_the_bar_under_80_percent(lib):
    _, (R, B, rc, cn) = lib
    rep = {"keywords": {"hits": 5, "total": 10, "strict_misses": [], "misses": []},
           "meaning": {"hits": 7, "total": 10, "strict_misses": [], "misses": []}}
    assert "below the 80% bar" in rc.summary(rep)


def test_summary_says_release_questions_missed_for_a_strict_miss(lib):
    _, (R, B, rc, cn) = lib
    rep = {"keywords": {"hits": 10, "total": 10, "strict_misses": [], "misses": []},
           "meaning": {"hits": 10, "total": 10, "strict_misses": ["Images <- how are images sent"], "misses": []}}
    s = rc.summary(rep)
    assert "1 release questions missed: Images <- how are images sent" in s


def test_run_returns_both_modes_and_restores_semantic(lib, monkeypatch):
    tmp, (R, B, rc, cn) = lib
    qdir = tmp / "questions"
    qdir.mkdir()
    (qdir / "paraphrases.json").write_text(json.dumps([{"q": "how do I pin it", "heading": "Pin a model"}]))
    monkeypatch.setattr(rc, "QDIR", str(qdir))
    monkeypatch.setattr(R, "semantic", "SENTINEL")
    seen = []

    def fake_route(q, model=None):
        seen.append(R.semantic)
        return secs(("Pin a model", "docs/a.md", "EXTRACT")) if R.semantic is not None else secs()

    monkeypatch.setattr(R, "route", fake_route)
    rep = rc.run()
    assert set(rep) == {"keywords", "meaning"}
    assert rep["keywords"]["hits"] == 0 and rep["meaning"]["hits"] == 1
    assert seen == [None, "SENTINEL"]
    assert R.semantic == "SENTINEL"


def test_questions_is_empty_when_no_question_file_exists(lib, monkeypatch, tmp_path):
    _, (R, B, rc, cn) = lib
    monkeypatch.setattr(rc, "QDIR", str(tmp_path / "missing"))
    assert rc.questions() == []


def test_deleted_section_is_named_by_after_change(lib, monkeypatch):
    tmp, (R, B, rc, cn) = lib
    docs = tmp / "docs"
    docs.mkdir()
    (docs / "a.md").write_text("# Pin a model\n\nPin the model version in every request.\n")
    (docs / "b.md").write_text("# Batch limits\n\nSend at most 30 passages in one call.\n")
    (docs / "c.md").write_text("# Cookbook notes\n\nSomething else entirely.\n")
    qdir = tmp / "questions"
    qdir.mkdir()
    (qdir / "paraphrases.json").write_text(json.dumps([{"q": "how do I pin the model version", "heading": "Pin a model"}]))
    monkeypatch.setattr(rc, "QDIR", str(qdir))
    build = [sys.executable, os.path.join(CODE, "scripts", "build_index.py")]
    subprocess.run(build, check=True, capture_output=True)
    assert rc.run()["keywords"]["hits"] == 1
    os.remove(docs / "a.md")
    subprocess.run(build, check=True, capture_output=True)
    lines = cn.after_change({})
    assert len(lines) == 1
    assert "Pin a model <- how do I pin the model version" in lines[0]


def labeled(heading, path, needs=None, status=None, depth="READ FULL"):
    return {"sections": [{"heading": heading, "path": path, "depth": depth, "needs": needs, "status": status}]}


def test_needs_newer_passes_only_with_a_needs_label(lib):
    _, (R, B, rc, cn) = lib
    q = {"q": "x", "heading": "Box", "strict": True, "model": "jev-1.13.0", "expect": "needs-newer"}
    assert rc.hit(labeled("Box", "docs/b.md", needs="jev-1.14.0"), q)
    assert not rc.hit(labeled("Box", "docs/b.md"), q)  # a plain READ FULL is a miss


def test_experimental_expectation_needs_the_label_and_no_needs(lib):
    _, (R, B, rc, cn) = lib
    q = {"q": "x", "heading": "Images", "strict": True, "model": "jev-1.13.0", "expect": "experimental"}
    assert rc.hit(labeled("Images", "docs/i.md", status="experimental"), q)
    assert not rc.hit(labeled("Images", "docs/i.md", needs="jev-1.14.0", status="experimental"), q)
    assert not rc.hit(labeled("Images", "docs/i.md"), q)


def test_run_passes_the_question_model_to_route(lib, monkeypatch):
    tmp, (R, B, rc, cn) = lib
    qdir = tmp / "questions"
    qdir.mkdir()
    (qdir / "paraphrases.json").write_text(json.dumps([{"q": "where is it", "heading": "Box", "model": "jev-1.13.0"}, {"q": "plain", "heading": "Box"}]))
    monkeypatch.setattr(rc, "QDIR", str(qdir))
    seen = []
    monkeypatch.setattr(R, "route", lambda q, model=None: seen.append((q, model)) or secs())
    rc.run()
    assert ("where is it", "jev-1.13.0") in seen and ("plain", None) in seen


def test_experimental_expectation_rejects_part_experimental(lib):
    _, (R, B, rc, cn) = lib
    q = {"q": "x", "heading": "Basic usage", "strict": True, "expect": "experimental"}
    assert not rc.hit(labeled("Basic usage", "docs/u.md", status="part-experimental"), q)


# ---- strict release questions count only when delivered --------------------------------------------------------

def with_id(res, sid="docs/a#0"):
    for s in res["sections"]:
        s["id"] = sid
    return res


def test_a_strict_question_whose_section_falls_past_the_cap_is_a_miss(lib):
    _, (R, B, rc, cn) = lib
    q = {"q": "x", "heading": "Box", "strict": True}
    res = with_id(labeled("Box", "docs/b.md"))
    assert rc.hit(res, q)  # no delivery information: the old rule
    assert not rc.hit(res, q, delivered=set())
    assert not rc.hit(res, q, delivered={"docs/other#1"})
    assert rc.hit(res, q, delivered={"docs/a#0"})


def test_a_loose_question_ignores_delivery(lib):
    _, (R, B, rc, cn) = lib
    q = {"q": "x", "heading": "Box", "strict": False}
    assert rc.hit(with_id(labeled("Box", "docs/b.md", depth="EXTRACT")), q, delivered=set())


def test_a_delivered_section_must_still_pass_the_expected_labels(lib):
    _, (R, B, rc, cn) = lib
    q = {"q": "x", "heading": "Box", "strict": True, "model": "jev-1.13.0", "expect": "needs-newer"}
    assert not rc.hit(with_id(labeled("Box", "docs/b.md")), q, delivered={"docs/a#0"})
    assert rc.hit(with_id(labeled("Box", "docs/b.md", needs="jev-1.14.0")), q, delivered={"docs/a#0"})


def test_run_asks_bundle_once_per_strict_question_without_logging(lib, monkeypatch):
    tmp, (R, B, rc, cn) = lib
    qdir = tmp / "questions"
    qdir.mkdir()
    (qdir / "release_questions.json").write_text(json.dumps([{"q": "where is it", "heading": "Box", "model": "jev-1.13.0"}]))
    (qdir / "paraphrases.json").write_text(json.dumps([{"q": "loose", "heading": "Box"}]))
    monkeypatch.setattr(rc, "QDIR", str(qdir))
    monkeypatch.setattr(R, "route", lambda q, model=None: with_id(labeled("Box", "docs/b.md")))
    calls = []

    def fake_bundle(qs, model=None, cap=None, log=True):
        calls.append((qs, model, log))
        return {"read_ids": []}

    monkeypatch.setattr(rc, "bundle", fake_bundle)
    rep = rc.run()
    assert rep["keywords"]["strict_misses"] == ["Box <- where is it"]
    assert all(c == (["where is it"], "jev-1.13.0", False) for c in calls) and len(calls) == 2  # one per mode


def test_run_with_logging_on_writes_no_usage_line(lib, monkeypatch):
    tmp, (R, B, rc, cn) = lib
    docs = tmp / "docs"
    docs.mkdir()
    (docs / "a.md").write_text("# Pin a model\n\nPin the model version in every request.\n")
    subprocess.run([sys.executable, os.path.join(CODE, "scripts", "build_index.py"), "--no-prepare"], check=True, capture_output=True)
    qdir = tmp / "questions"
    qdir.mkdir()
    (qdir / "release_questions.json").write_text(json.dumps([{"q": "how do I pin the model version", "heading": "Pin a model"}]))
    monkeypatch.setattr(rc, "QDIR", str(qdir))
    monkeypatch.setenv("JEV_LOG", "on")
    rep = rc.run()
    assert rep["keywords"]["strict_misses"] == []
    assert not (tmp / "logs").exists()
