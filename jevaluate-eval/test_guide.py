import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import guide_test as gt

GOLD = json.loads((pathlib.Path(__file__).parent / "guide_gold.json").read_text())["building-with-jev-skill"]["misses"]

def test_recall_scores_nine_of_twelve():
    nine = ["existence check", "uncertain band", "deriving thresholds", "composite confidence", "ids on items",
            "shortlist then recheck", "cascade", "beam search", "function calling"]
    reply = {"result": json.dumps({"misses": [GOLD[g][0] for g in nine]})}
    found, which = gt.recall(reply, GOLD)
    assert found == 9 and sorted(which) == sorted(nine)

def test_recall_unparsable_json_is_zero():
    assert gt.recall({"result": "not json {"}, GOLD) == (0, [])
    assert gt.recall({}, GOLD) == (0, [])
    assert gt.recall({"result": '{"misses": "oops"}'}, GOLD) == (0, [])

def test_guide_sources_raise_every_cap():
    src = gt.wide_source({"k": {"files": [["a", 5], ["b", 9]], "kind": "github"}}["k"])
    assert all(c == 20000 for _, c in src["files"])

def test_ids_matches_word_start_only():
    assert gt.recall({"result": json.dumps({"misses": ["it avoids kids"]})}, GOLD) == (0, [])
    assert gt.recall({"result": json.dumps({"misses": ["IDs on items"]})}, GOLD) == (1, ["ids on items"])
    assert gt.recall({"result": json.dumps({"misses": ["no rate limiting or caching"]})}, GOLD)[0] == 1

def test_summary_reports_miss_count_and_failed_call():
    md = gt.render([(1, 9, ["cascade"], 2, 14, ""), (2, 0, [], "?", 0, "call failed: exit 1, see guide_r2.json")], [], 5, GOLD, False)
    assert "9/12 found, from 14 misses listed" in md and "call failed: exit 1, see guide_r2.json" in md
