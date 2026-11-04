"""Measure field-by-field agreement between two blind decoders of the same images.

Usage: python agreement.py <template.json> <decodes_A folder> <decodes_B folder> [--out agreement.md] [--bar 0.9]
List items are matched by position (decoders number people and objects left to right).
Category and boolean fields must match exactly; text fields match when their words mostly overlap.
A field where either decoder wrote "unclear" is flagged for the user, not counted as a disagreement.
Standard library only.
"""
from __future__ import annotations

import argparse
import re
import sys

from lenslib import load_decodes, load_json


def _norm(v) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s/]", "", str(v).lower())).strip()


def same_value(a, b, ftype: str) -> bool:
    if ftype != "text":
        return a == b
    na, nb = _norm(a), _norm(b)
    if na == nb:
        return True
    wa, wb = set(na.split()), set(nb.split())
    if not wa or not wb:
        return False
    return len(wa & wb) / min(len(wa), len(wb)) >= 0.6  # the shorter reading is mostly inside the longer


def _is_unclear(f) -> bool:
    return isinstance(f, dict) and (f.get("value") == "unclear" or f.get("certainty") == "unclear")


def _val(f):
    return f.get("value") if isinstance(f, dict) else f


def compare(a: dict, b: dict, template: dict) -> dict:
    stats, disagreements, flagged = {}, [], []

    def tally(key, img, fa, fb, ftype):
        s = stats.setdefault(key, {"n": 0, "agree": 0, "unclear": 0})
        s["n"] += 1
        if _is_unclear(fa) or _is_unclear(fb):
            s["unclear"] += 1
            flagged.append((img, key, _val(fa), _val(fb)))
        elif fa is not None and fb is not None and same_value(_val(fa), _val(fb), ftype):
            s["agree"] += 1
        else:
            disagreements.append((img, key, _val(fa), _val(fb)))

    shared = sorted(set(a) & set(b))
    for img in shared:
        sa, sb = a[img].get("sections", {}), b[img].get("sections", {})
        for sec, spec in template["sections"].items():
            fields = spec["fields"]
            if spec.get("list"):
                la, lb = sa.get(sec) or [], sb.get(sec) or []
                tally(f"{sec}.count", img, {"value": len(la)}, {"value": len(lb)}, "category")
                for i in range(max(len(la), len(lb))):
                    ia = la[i] if i < len(la) else {}
                    ib = lb[i] if i < len(lb) else {}
                    for name, fs in fields.items():
                        tally(f"{sec}[].{name}", img, ia.get(name), ib.get(name), fs.get("type", "text"))
            else:
                for name, fs in fields.items():
                    tally(f"{sec}.{name}", img, (sa.get(sec) or {}).get(name), (sb.get(sec) or {}).get(name),
                          fs.get("type", "text"))
    return {"images": shared, "only_one_side": sorted(set(a) ^ set(b)), "fields": stats,
            "disagreements": disagreements, "flagged": flagged}


def to_markdown(r: dict, bar: float) -> str:
    lines = [f"# Agreement\n\n{len(r['images'])} images decoded by both decoders. Bar: {bar:.0%} per field.\n",
             "| Field | Compared | Agree | Unclear | Meets bar |", "|---|---|---|---|---|"]
    below = 0
    for key, s in sorted(r["fields"].items()):
        judged = s["n"] - s["unclear"]
        rate = s["agree"] / judged if judged else 1.0
        ok = rate >= bar
        below += not ok
        lines.append(f"| `{key}` | {s['n']} | {rate:.0%} | {s['unclear']} | {'yes' if ok else '**no**'} |")
    lines.append(f"\n**Fields below the bar: {below}.**\n")
    if r["disagreements"]:
        lines += ["## Disagreements (ask the user)\n", "| Image | Field | Decoder A | Decoder B |", "|---|---|---|---|"]
        lines += [f"| {i} | `{k}` | {x} | {y} |" for i, k, x, y in r["disagreements"]]
    if r["flagged"]:
        lines += ["\n## Unclear (ask the user)\n", "| Image | Field | Decoder A | Decoder B |", "|---|---|---|---|"]
        lines += [f"| {i} | `{k}` | {x} | {y} |" for i, k, x, y in r["flagged"]]
    if r["only_one_side"]:
        lines.append(f"\nDecoded by only one decoder: {', '.join(r['only_one_side'])}")
    return "\n".join(lines) + "\n"


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("template"); ap.add_argument("a"); ap.add_argument("b")
    ap.add_argument("--out"); ap.add_argument("--bar", type=float, default=0.9)
    args = ap.parse_args(argv[1:])
    md = to_markdown(compare(load_decodes(args.a), load_decodes(args.b), load_json(args.template)), args.bar)
    if args.out:
        open(args.out, "w", encoding="utf-8").write(md)
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
