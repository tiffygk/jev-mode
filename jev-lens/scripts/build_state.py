"""Build Jev states from decodes, keeping only the fields marked keep.

Usage: python build_state.py <template.json> <keep.json> <decode.json or decodes folder> --out <state.json or states folder>
         [--context context.json] [--between between.json] [--left-out left-out.md]
keep.json: {"keep": ["scene.setting", "people[].posture"], "drop": {"people[].shirt": "reason"}}
Clear values go in as plain values; likely or unclear ones keep their certainty: {"value": ..., "certainty": ...};
a value the user supplied keeps its "source".
Every template field must be kept or dropped with a reason; the script stops if one is unassigned.
Standard library only.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from lenslib import load_decodes, load_json


def _out(f):
    """Clear values go in plain; likely/unclear keep their certainty; user-supplied facts keep their source."""
    if not (isinstance(f, dict) and "value" in f):
        return f
    extra = {}
    if f.get("certainty") != "clear":
        extra["certainty"] = f.get("certainty")
    if f.get("source"):
        extra["source"] = f["source"]
    return dict(value=f["value"], **extra) if extra else f["value"]


def build_state(decode: dict, keep: list, context: dict | None = None, between: dict | None = None) -> dict:
    """Sections and fields come out in keep-list order, so every image's state has the same layout."""
    sections = decode.get("sections") or {}
    state = {}
    for path in keep:
        sec, name = path.split(".", 1)
        if sec.endswith("[]"):
            sec = sec[:-2]
            body = sections.get(sec)
            if not isinstance(body, list):
                continue
            items = state.setdefault(sec, [{"id": it.get("id")} for it in body])
            for out, it in zip(items, body):
                if name in it:
                    out[name] = _out(it[name])
        else:
            body = sections.get(sec)
            if isinstance(body, dict) and name in body:
                state.setdefault(sec, {})[name] = _out(body[name])
    if between:
        state["between"] = between
    if context:
        state["context"] = context
    return state


def all_paths(template: dict) -> list:
    return sorted(f"{sec}[].{n}" if s.get("list") else f"{sec}.{n}"
                  for sec, s in template["sections"].items() for n in s["fields"])


def unassigned(template: dict, keep: dict) -> list:
    done = set(keep.get("keep", [])) | set(keep.get("drop", {}))
    return [p for p in all_paths(template) if p not in done]


def left_out_md(keep: dict) -> str:
    lines = ["# Left out\n", "Fields in the inventory that are not in the state, and why.\n",
             "| Field | Reason |", "|---|---|"]
    lines += [f"| `{p}` | {r} |" for p, r in sorted(keep.get("drop", {}).items())]
    return "\n".join(lines) + "\n"


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("template"); ap.add_argument("keep"); ap.add_argument("decodes")
    ap.add_argument("--out", required=True); ap.add_argument("--context"); ap.add_argument("--between")
    ap.add_argument("--left-out")
    a = ap.parse_args(argv[1:])
    template, keep = load_json(a.template), load_json(a.keep)
    missing = unassigned(template, keep)
    if missing:
        print("Mark each of these keep or drop (with a reason) in keep.json first:\n  " + "\n  ".join(missing))
        return 1
    ctx = load_json(a.context) if a.context else None
    btw = load_json(a.between) if a.between else None
    src = Path(a.decodes)
    decodes = load_decodes(src) if src.is_dir() else {src.stem: load_json(src)}
    out = Path(a.out)
    if len(decodes) == 1 and out.suffix == ".json":
        targets = {next(iter(decodes)): out}
    else:
        out.mkdir(parents=True, exist_ok=True)
        targets = {k: out / f"{k}.json" for k in decodes}
    for k, d in decodes.items():
        s = build_state(d, keep["keep"], ctx, btw)
        targets[k].write_text(json.dumps(s, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"{targets[k]}  (~{len(json.dumps(s)) // 4} tokens)")
    if a.left_out:
        Path(a.left_out).write_text(left_out_md(keep), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
