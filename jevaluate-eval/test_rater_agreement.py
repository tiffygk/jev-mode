"""Rater agreement (instrument 4): chance-corrected agreement, the tuning sample reported apart, a seeded answer-key
draw, and scoring each rater against the owner's key."""
import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent / "rater_agreement"))
import rater_agreement as ra


def test_kappa_matches_hand_worked_example():
    # observed 3/4; chance (.5 x .25) + (.5 x .75) = .5; kappa = (.75 - .5) / (1 - .5) = .5
    assert abs(ra.kappa(["y", "y", "n", "n"], ["y", "n", "n", "n"]) - 0.5) < 1e-9


def test_kappa_is_none_when_one_value_everywhere():
    assert ra.kappa(["yes"] * 5, ["yes"] * 5) is None


def test_tuning_sample_reported_apart():
    pairs = {"p1": ({"type": "workflow"}, {"type": "workflow"}), "p2": ({"type": "workflow"}, {"type": "display"}),
             "s1": ({"type": "library"}, {"type": "workflow"})}
    rep = ra.agreement(pairs, ["type"], tuning={"s1"})
    assert rep["held_out"]["n"] == 2 and rep["held_out"]["type"]["agree"] == 1
    assert rep["tuning"]["n"] == 1 and rep["tuning"]["type"]["agree"] == 0


def facts(n_projects=6):
    out = []
    for p in range(n_projects):
        for f in range(4):
            split = (p + f) % 3 == 0
            out.append({"project": f"p{p}", "fact": f"F{f}", "a": "yes", "b": "no" if split else "yes", "split": split})
    out.append({"project": "p0", "fact": "F9", "a": "n.a.", "b": "n.a.", "split": False})
    return out


def test_draw_is_seeded_and_keeps_its_limits():
    d1 = ra.draw(facts(), n_split=3, n_agreed=3, seed=7); d2 = ra.draw(facts(), n_split=3, n_agreed=3, seed=7)
    assert d1 == d2
    picked = d1["split"] + d1["agreed"]
    assert len(d1["split"]) == 3 and len(d1["agreed"]) == 3
    assert len({x["project"] for x in picked}) == len(picked)            # one per project
    assert len({x["fact"] for x in d1["split"]}) == 3 and len({x["fact"] for x in d1["agreed"]}) == 3   # one per fact, per group
    assert all(x["a"] != "n.a." for x in d1["agreed"])                    # both-n.a. facts are never drawn


def test_score_counts_cant_tell_apart_never_as_a_match():
    key = {"K1": {"a": "yes", "b": "no"}, "K2": {"a": "workflow", "b": "workflow"}, "K3": {"a": "low", "b": "high"}}
    owner = ra.parse_owner("Answer key 2026-10-06\nK1: yes\nK2: can't tell | note: unsure\nK3: high | note: reaches others\n")
    assert owner == {"K1": "yes", "K2": "can't tell", "K3": "high"}
    s = ra.score(key, owner)
    assert s["a"] == {"right": 1, "wrong": 1, "cant_tell": 1} and s["b"] == {"right": 1, "wrong": 1, "cant_tell": 1}
