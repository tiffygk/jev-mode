# /// script
# requires-python = ">=3.9"
# dependencies = ["typesafe-sdk"]
# ///
"""The Jev check: run the question sketch on a state, and find which fields drive the answers.

Usage (TYPESAFE_API_KEY in the environment; without --yes, prints the cost and stops):
  uv run jev_check.py run      --state state.json  --questions questions.json [--yes]
  uv run jev_check.py fields   --state state.json  --questions questions.json [--flips flips.json] [--repeats 3] [--yes]
  uv run jev_check.py inverted --states states/    --questions questions.json [--standard 3] [--yes]
Common: --model jev-1.13.0 (take the ID from docs.typesafe.ai/models), --out jev-check.md

questions.json: {"id": {"type": "noul", "instructions": "..."},
                 "id2": {"type": "choice", "instructions": "...", "options": {"key": "description"}}}
flips.json: {"people[0].posture": "standing"}   (counterfactual values for the field-by-field test)
Choices are always asked once per rotation of their options and averaged (Choice is the least stable type).
Exit codes: 0 done or cost shown; 3 skipped on purpose because TYPESAFE_API_KEY is not set (not an error).
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import re
import sys
from pathlib import Path

MODEL = "jev-1.13.0"
PRICE_PER_MTOK = 0.042  # dollars per million input tokens; output is free (docs.typesafe.ai/models, 2026-09)
NOISE_FLOOR = 0.02      # a change smaller than this never counts as an effect
MAX_STATE_PLUS_Q = 32000
MAX_REQUEST = 64000


def tokens(obj) -> int:
    # Jev bills about 1.65x the usual characters/4 (measured 2026-09-28: 8,160 estimated vs 13,356 billed)
    return len(json.dumps(obj, ensure_ascii=False)) * 10 // 24 + 1


# ---- questions ----
def expand(questions: dict) -> dict:
    """Plain-dict question specs, with each Choice asked once per rotation of its options."""
    out = {}
    for qid, q in questions.items():
        if q["type"] == "noul":
            out[qid] = {"type": "noul", "instructions": q["instructions"]}
        elif q["type"] == "choice":
            keys = list(q["options"])
            for i in range(len(keys)):
                order = keys[i:] + keys[:i]
                out[f"{qid}__r{i}"] = {"type": "choice", "instructions": q["instructions"],
                                       "criteria": {k: q["options"][k] for k in order}}
        else:
            raise ValueError(f"{qid}: type must be noul or choice")
    return out


def summarize(raw: dict, questions: dict) -> dict:
    """{qid: {"yes": p}} for Nouls, {qid: {option: mean p}} for Choices."""
    out = {}
    for qid, q in questions.items():
        if q["type"] == "noul":
            out[qid] = {"yes": raw[qid]}
        else:
            rots = [raw[k] for k in raw if k.startswith(f"{qid}__r")]
            out[qid] = {o: sum(r[o] for r in rots) / len(rots) for o in q["options"]}
    return out


# ---- state paths ----
def leaves(d, path=()):
    """Every field path, skipping ids; a {"value", "certainty"} pair counts as one field."""
    if isinstance(d, dict) and not (set(d) <= {"value", "certainty", "source"} and "value" in d):
        for k, v in d.items():
            if k != "id":
                yield from leaves(v, path + (k,))
    elif isinstance(d, list) and d and all(isinstance(x, (dict, list)) for x in d):
        for i, v in enumerate(d):
            yield from leaves(v, path + (i,))
    else:
        yield path


def path_str(p) -> str:
    return "".join(f"[{x}]" if isinstance(x, int) else (f".{x}" if i else x) for i, x in enumerate(p))


def parse_path(s: str) -> tuple:
    return tuple(int(t[1:-1]) if t.startswith("[") else t for t in re.findall(r"\[\d+\]|[^.\[\]]+", s))


def _edit(state, path, value=None, remove=False):
    s = copy.deepcopy(state); cur = s
    for p in path[:-1]:
        cur = cur[p]
    if remove:
        del cur[path[-1]]
    else:
        cur[path[-1]] = value
    return s


def _move(a: dict, b: dict) -> float:
    return max(abs(a[q][k] - b[q][k]) for q in a for k in a[q])


def _mean(runs: list) -> dict:
    return {q: {k: sum(r[q][k] for r in runs) / len(runs) for k in runs[0][q]} for q in runs[0]}


def field_test(ask, state: dict, questions: dict, flips: dict | None = None, repeats: int = 3) -> list:
    """Remove each field (and apply each flip), rank by how far the answers move.
    The noise band is the largest spread seen across repeated runs of the unchanged state."""
    specs = expand(questions)
    base_runs = [summarize(ask(state, specs), questions) for _ in range(max(1, repeats))]
    base = _mean(base_runs)
    noise = max([NOISE_FLOOR] + [_move(r, base) * 2 for r in base_runs])
    rows = []
    for p in leaves(state):
        rows.append(("remove", p, summarize(ask(_edit(state, p, remove=True), specs), questions)))
    for ps, v in (flips or {}).items():
        rows.append(("flip", parse_path(ps), summarize(ask(_edit(state, parse_path(ps), v), specs), questions)))
    out = []
    for kind, p, res in rows:
        m = _move(res, base)
        out.append({"change": kind, "field": path_str(p), "move": m, "effect": m > noise, "noise": noise,
                    "detail": {q: {k: res[q][k] - base[q][k] for k in res[q]} for q in res}})
    return sorted(out, key=lambda r: -r["move"])


# ---- inverted request (batch quality control) ----
def inverted(ask, rows: dict, questions: dict) -> dict:
    """One request per sketch question: the question goes in the state, each decode becomes a question."""
    out = {}
    for qid, q in questions.items():
        state = {"question": q["instructions"]}
        if q["type"] == "noul":
            specs = {rid: {"type": "noul", "instructions": row} for rid, row in rows.items()}
            raw = ask(state, specs)
            out[qid] = {rid: {"yes": raw[rid]} for rid in rows}
        else:
            state["options"] = q["options"]
            keys = list(q["options"]); specs = {}
            for i in range(len(keys)):
                order = keys[i:] + keys[:i]
                for rid, row in rows.items():
                    specs[f"{rid}__r{i}"] = {"type": "choice", "instructions": row,
                                             "criteria": {k: q["options"][k] for k in order}}
            raw = ask(state, specs)
            out[qid] = {rid: {o: sum(raw[f"{rid}__r{i}"][o] for i in range(len(keys))) / len(keys)
                              for o in keys} for rid in rows}
    return out


# ---- cost and size ----
def estimate(states: list, questions: dict, requests: int) -> dict:
    per = max(tokens(s) for s in states) + tokens(expand(questions))
    t = per * requests
    return {"requests": requests, "tokens": t, "dollars": t * PRICE_PER_MTOK / 1e6}


def size_problems(state, questions: dict) -> list:
    longest = max(tokens(q) for q in expand(questions).values())
    probs = []
    if tokens(state) + longest > MAX_STATE_PLUS_Q:
        probs.append(f"state plus the longest question is about {tokens(state) + longest:,} tokens (limit 32k)")
    if tokens(state) + tokens(expand(questions)) > MAX_REQUEST:
        probs.append("state plus all questions is over 64k tokens")
    return probs


# ---- the live client ----
def make_ask(model: str):
    from typesafe_sdk import Choice, Noul, TypeSafeClient
    client = TypeSafeClient(api_key=os.environ["TYPESAFE_API_KEY"], timeout=120.0)
    seen = {"model": None, "input_tokens": 0}

    def ask(state, specs):
        qs = {k: (Noul(instructions=v["instructions"]) if v["type"] == "noul"
                  else Choice(instructions=v["instructions"], criteria=v["criteria"])) for k, v in specs.items()}
        r = client.system_one(state=state, questions=qs, model=model)
        seen["model"] = r.model
        seen["input_tokens"] += r.usage.input_tokens
        return {k: (a.noul if a.type == "noul" else dict(a.probabilities)) for k, a in r.answers.items()}
    return ask, seen


def _fmt(summary: dict) -> list:
    lines = ["| Question | Answer |", "|---|---|"]
    for q, v in summary.items():
        lines.append(f"| `{q}` | " + ", ".join(f"{k} {p:.2f}" for k, p in sorted(v.items(), key=lambda x: -x[1])) + " |")
    return lines


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("mode", choices=["run", "fields", "inverted"])
    ap.add_argument("--state"); ap.add_argument("--states"); ap.add_argument("--questions", required=True)
    ap.add_argument("--flips"); ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--standard", type=int, default=3, help="inverted: also run the standard request on this many rows")
    ap.add_argument("--model", default=MODEL); ap.add_argument("--out"); ap.add_argument("--yes", action="store_true")
    a = ap.parse_args(argv[1:])
    if not os.environ.get("TYPESAFE_API_KEY"):
        print("TYPESAFE_API_KEY is not set: skipping the Jev check. The state and sketch are still usable; "
              "set the key (from your TypeSafe account) and rerun this command to check them.")
        return 3
    questions = json.loads(Path(a.questions).read_text(encoding="utf-8"))
    flips = json.loads(Path(a.flips).read_text(encoding="utf-8")) if a.flips else {}
    if a.mode == "inverted":
        rows = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in sorted(Path(a.states).glob("*.json"))}
        states = list(rows.values())
        n_std = min(a.standard, len(rows))
        est = estimate(states, questions, requests=len(questions) + n_std)
        est["tokens"] = sum(tokens(r) for r in states) * sum(len(q.get("options", [1])) for q in questions.values()) \
            + n_std * (max(tokens(s) for s in states) + tokens(expand(questions)))
        est["dollars"] = est["tokens"] * PRICE_PER_MTOK / 1e6
    else:
        state = json.loads(Path(a.state).read_text(encoding="utf-8"))
        states = [state]
        n = 1 if a.mode == "run" else a.repeats + len(list(leaves(state))) + len(flips)
        est = estimate(states, questions, requests=n)
    for s in states:
        for p in size_problems(s, questions):
            print("SIZE:", p)
    dollars = f"${est['dollars']:.4f}" if est["dollars"] >= 0.0001 else "under $0.0001"
    print(f"Cost: {est['requests']} request{'s' if est['requests'] != 1 else ''}, about {est['tokens']:,} input tokens, "
          f"about {dollars} on {a.model}.")
    if not a.yes:
        print("Nothing sent. Rerun with --yes to run it.")
        return 0
    ask, seen = make_ask(a.model)
    lines = [f"# Jev check ({a.mode})\n"]
    if a.mode == "run":
        lines += _fmt(summarize(ask(state, expand(questions)), questions))
    elif a.mode == "fields":
        rows = field_test(ask, state, questions, flips, a.repeats)
        lines += [f"Noise band (run-to-run): {rows[0]['noise']:.3f}. Changes inside it count as no effect.\n",
                  "| Change | Field | Largest move | Effect |", "|---|---|---|---|"]
        lines += [f"| {r['change']} | `{r['field']}` | {r['move']:.3f} | {'yes' if r['effect'] else 'no'} |" for r in rows]
    else:
        res = inverted(ask, rows, questions)
        lines += ["| Row | " + " | ".join(questions) + " |", "|---" * (len(questions) + 1) + "|"]
        for rid in rows:
            cells = [", ".join(f"{k} {p:.2f}" for k, p in sorted(res[q][rid].items(), key=lambda x: -x[1])[:2])
                     for q in questions]
            lines.append(f"| {rid} | " + " | ".join(cells) + " |")
        if n_std:
            diffs = []
            for rid in list(rows)[:n_std]:
                std = summarize(ask(rows[rid], expand(questions)), questions)
                diffs.append(max(abs(std[q][k] - res[q][rid][k]) for q in questions for k in std[q]))
            lines.append(f"\nInverted vs standard on {n_std} rows: largest difference {max(diffs):.3f} "
                         f"({'fine' if max(diffs) <= 0.10 else 'check this dataset with the standard request'}).")
    lines.append(f"\nModel: {seen['model']}. Input tokens billed: {seen['input_tokens']:,} "
                 f"(about ${seen['input_tokens'] * PRICE_PER_MTOK / 1e6:.4f}).")
    md = "\n".join(lines) + "\n"
    if a.out:
        Path(a.out).write_text(md, encoding="utf-8")
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
