import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import jev_check as jc  # noqa: E402

QUESTIONS = {
    "near": {"type": "noul", "instructions": "Are `people[0]` and `people[1]` touching?"},
    "where": {"type": "choice", "instructions": "Where was this taken?",
              "options": {"beach": "At a beach", "office": "In an office", "park": "In a park"}},
}
STATE = {"scene": {"setting": "beach", "weather": {"value": "sunny", "certainty": "likely"}},
         "people": [{"id": "p1", "contact": "arm around p2"}, {"id": "p2", "contact": "none"}]}


def fake_ask(state, qspecs):
    """Deterministic stand-in for Jev: 'touching' follows people[0].contact; 'where' follows the setting.
    The first-listed option gets a small bonus, so averaging over orders matters."""
    out = {}
    for k, q in qspecs.items():
        if q["type"] == "noul":
            c = ((state.get("people") or [{}])[0]).get("contact", "")
            out[k] = 0.9 if "arm" in str(c) else 0.2
        else:
            setting = (state.get("scene") or {}).get("setting", "")
            opts = list(q["criteria"])
            raw = {o: (0.7 if o == setting else 0.15) + (0.06 if i == 0 else 0) for i, o in enumerate(opts)}
            t = sum(raw.values())
            out[k] = {o: v / t for o, v in raw.items()}
    return out


def test_expand_rotates_choice_options():
    specs = jc.expand(QUESTIONS)
    rot = [k for k in specs if k.startswith("where")]
    assert len(rot) == 3
    assert {list(specs[k]["criteria"])[0] for k in rot} == {"beach", "office", "park"}


def test_summarize_averages_rotations():
    specs = jc.expand(QUESTIONS)
    s = jc.summarize(fake_ask(STATE, specs), QUESTIONS)
    assert abs(s["near"]["yes"] - 0.9) < 1e-9
    assert abs(sum(s["where"].values()) - 1) < 1e-9
    assert s["where"]["office"] == s["where"]["park"]  # order bonus averaged away


def test_leaves_skip_ids_and_treat_certainty_pairs_as_one_field():
    paths = [jc.path_str(p) for p in jc.leaves(STATE)]
    assert "scene.weather" in paths and "scene.weather.value" not in paths
    assert "people[0].contact" in paths and "people[0].id" not in paths


def test_field_test_ranks_and_applies_noise_band():
    rows = jc.field_test(fake_ask, STATE, QUESTIONS, flips={"scene.setting": "office"}, repeats=2)
    assert (rows[0]["change"], rows[0]["field"]) == ("remove", "people[0].contact")  # 0.9 -> 0.2
    assert {(r["change"], r["field"]) for r in rows[1:3]} == {("flip", "scene.setting"), ("remove", "scene.setting")}
    by = {(r["change"], r["field"]): r for r in rows}
    assert by[("remove", "people[0].contact")]["effect"]
    assert not by[("remove", "people[1].contact")]["effect"]  # no answer reads it: within noise


def test_estimate_counts_requests_and_prices_input_only():
    e = jc.estimate([STATE], QUESTIONS, requests=10)
    assert e["requests"] == 10 and e["tokens"] > 0
    assert e["dollars"] == e["tokens"] * jc.PRICE_PER_MTOK / 1e6


def test_size_warning():
    big = {"text": "word " * 140000}
    assert jc.size_problems(big, QUESTIONS)
    assert jc.size_problems(STATE, QUESTIONS) == []


def test_inverted_puts_question_in_state_and_rows_in_questions():
    calls = []

    def ask(state, qspecs):
        calls.append((state, qspecs))
        return fake_ask({}, {k: v for k, v in qspecs.items()})

    rows = {"image_01": STATE, "image_02": {"scene": {"setting": "office"}}}
    jc.inverted(ask, rows, {"near": QUESTIONS["near"]})
    state, qspecs = calls[0]
    assert state["question"] == QUESTIONS["near"]["instructions"]
    assert set(qspecs) == {"image_01", "image_02"}
    assert qspecs["image_01"]["instructions"] == STATE


def test_missing_key_skips(monkeypatch, capsys):
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    code = jc.main(["x", "run", "--state", "s.json", "--questions", "q.json", "--yes"])
    assert code == 3 and "skipping the Jev check" in capsys.readouterr().out
