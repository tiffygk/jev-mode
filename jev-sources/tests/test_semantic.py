import json, os, sys, importlib
import numpy as np, pytest
CODE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(CODE, "scripts"))

@pytest.fixture
def sem(tmp_path, monkeypatch):
    real = os.path.expanduser(os.environ.get("JEV_SOURCES_DATA") or "~/.claude/jev-sources-data")
    monkeypatch.setenv("HF_HOME", os.environ.get("HF_HOME") or os.path.join(real, "models"))  # the real model cache
    monkeypatch.setenv("JEV_SOURCES_DATA", str(tmp_path))
    import paths, semantic
    importlib.reload(paths); importlib.reload(semantic)
    return semantic, tmp_path

ROWS = [{"id": "docs/a#0", "path": "docs/a.md", "heading": "When one question depends on another"},
        {"id": "docs/b#0", "path": "docs/b.md", "heading": "Rate limits"}]
TEXTS = ["If a later judgment depends on an earlier answer, make a second request in code.",
         "1,200 requests per minute and 250,000 tokens per second."]

def test_build_then_scores_rank_the_paraphrase(sem):
    s, d = sem
    ok, why = s.available()
    if not ok: pytest.skip(why)
    s.build(ROWS, TEXTS)
    sc, why = s.scores("does this step need the answer from the previous step", ROWS)
    assert sc and sc["docs/a#0"] > sc["docs/b#0"]

def test_stale_ids_fall_back(sem):
    s, d = sem
    ok, why = s.available()
    if not ok: pytest.skip(why)
    s.build(ROWS, TEXTS)
    sc, why = s.scores("anything", ROWS + [{"id": "docs/c#0", "path": "docs/c.md", "heading": "x"}])
    assert sc is None and "stale" in why

def test_model_mismatch_falls_back(sem):
    s, d = sem
    ok, why = s.available()
    if not ok: pytest.skip(why)
    s.build(ROWS, TEXTS)
    meta = json.load(open(d / "embeddings.json")); meta["model"] = "other/model"
    json.dump(meta, open(d / "embeddings.json", "w"))
    sc, why = s.scores("anything", ROWS)
    assert sc is None and "model" in why

def test_missing_model_falls_back(sem, monkeypatch):
    s, d = sem
    ok, why = s.available()
    if not ok: pytest.skip(why)
    s.build(ROWS, TEXTS)  # a good index, so only the model is missing
    monkeypatch.setattr(s, "_load_model", lambda: (_ for _ in ()).throw(ImportError("no model2vec")))
    sc, why = s.scores("anything", ROWS)
    assert sc is None and "model unavailable" in why

def test_query_time_stays_offline(sem, monkeypatch):
    s, d = sem
    monkeypatch.delenv("HF_HUB_OFFLINE", raising=False)
    monkeypatch.setattr(s, "_model", None)
    import types
    fake = types.ModuleType("model2vec")
    class StaticModel:
        @staticmethod
        def from_pretrained(mid):
            assert os.environ.get("HF_HUB_OFFLINE") == "1"
            return "m"
    fake.StaticModel = StaticModel
    monkeypatch.setitem(sys.modules, "model2vec", fake)
    assert s._load_model() == "m"

def test_index_time_may_download(sem, monkeypatch):
    s, d = sem
    monkeypatch.delenv("HF_HUB_OFFLINE", raising=False)
    monkeypatch.setattr(s, "_model", None)
    monkeypatch.setattr(s, "ALLOW_DOWNLOAD", True)
    import types
    fake = types.ModuleType("model2vec")
    class StaticModel:
        @staticmethod
        def from_pretrained(mid):
            assert os.environ.get("HF_HUB_OFFLINE") != "1"
            return "m"
    fake.StaticModel = StaticModel
    monkeypatch.setitem(sys.modules, "model2vec", fake)
    assert s._load_model() == "m"

def test_missing_index_falls_back(sem):
    s, d = sem
    sc, why = s.scores("anything", ROWS)
    assert sc is None and "index" in why


MDX = """# Confidence

> How certainty is reported.

export function Explorer() {
  const [p, setP] = useState([90, 6, 4]);
  return <section aria-label="x" className="not-prose">
      <div className="flex">{p}</div>
  </section>;
}

The answer's `confidence` collapses the shape into one number from 0 to 1. See [State](/concepts/state).

```python
client.ask(state, questions)
```

<Warning>
  **Limits can change.** Contact sales.
</Warning>
import { Tabs } from "x";
![diagram](/img/a.png)
| Price | $42 |"""

def test_section_text_keeps_prose_drops_code(sem):
    s, d = sem
    lines = MDX.split("\n")
    t = s.section_text({"heading": "Confidence", "line_start": 1, "line_end": len(lines)}, lines)
    for gone in ("useState", "className", "client.ask", "export", "import", "/concepts/state", "img/a.png", "<Warning>", "**"):
        assert gone not in t, gone
    for kept in ("Confidence", "How certainty is reported", "one number from 0 to 1", "See State", "Limits can change", "Contact sales", "Price", "$42"):
        assert kept in t, kept


def test_long_section_scores_its_late_sentence(sem):
    s, d = sem
    ok, why = s.available()
    if not ok: pytest.skip(why)
    rule = "If a later judgment depends on an earlier answer, make a second request in code."
    lines = ["# Account"] + ["The billing dashboard lists invoices, payment methods and receipts for each month."] * 40 + ["", rule]
    rows = [{"id": "docs/long#0", "path": "docs/long.md", "heading": "Account", "line_start": 1, "line_end": len(lines)},
            {"id": "docs/short#0", "path": "docs/short.md", "heading": "Account", "line_start": 1, "line_end": 3}]
    s.build(rows, [s.section_text(rows[0], lines), s.section_text(rows[1], ["# Account", "", rule])])
    sc, why = s.scores("does this step need the answer from the previous step", rows)
    assert sc and sc["docs/long#0"] >= sc["docs/short#0"] - 0.05, sc


def test_changed_sections_with_same_ids_fall_back(sem):
    s, d = sem
    ok, why = s.available()
    if not ok: pytest.skip(why)
    s.build(ROWS, TEXTS)
    moved = [dict(ROWS[0], heading="Rate limits"), dict(ROWS[1], heading="When one question depends on another")]
    sc, why = s.scores("anything", moved)
    assert sc is None and "stale" in why


def test_rebuild_without_model_removes_old_vectors(tmp_path, monkeypatch):
    real = os.path.expanduser(os.environ.get("JEV_SOURCES_DATA") or "~/.claude/jev-sources-data")
    monkeypatch.setenv("HF_HOME", os.environ.get("HF_HOME") or os.path.join(real, "models"))
    monkeypatch.setenv("JEV_SOURCES_DATA", str(tmp_path))
    import paths, semantic, build_index
    for m in (paths, semantic, build_index): importlib.reload(m)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("# A\n\nSome text.\n")
    (tmp_path / "embeddings.npy").write_bytes(b"old"); (tmp_path / "embeddings.json").write_text("{}")
    monkeypatch.setattr(semantic, "available", lambda: (False, "model unavailable (test)"))
    build_index.main()
    assert not (tmp_path / "embeddings.npy").exists() and not (tmp_path / "embeddings.json").exists()
