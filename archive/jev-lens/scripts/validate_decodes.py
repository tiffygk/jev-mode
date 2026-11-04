"""Check decodes against the template: every field present, a certainty on each, one way of recording absence.

Usage: python validate_decodes.py <template.json> <decodes folder or file> [...] [--stats]
--stats also prints how often each category and boolean value occurs across the decodes (batch balance check).
Exit code 1 if any decode has errors. Standard library only.
"""
from __future__ import annotations

import sys
from pathlib import Path

from lenslib import CERTAINTIES, LOOSE_ABSENCES, SENTINELS, load_json


def _check_field(where: str, spec: dict, f, errors: list):
    if not isinstance(f, dict) or "value" not in f:
        errors.append(f"{where}: must be an object with value and certainty")
        return
    c = f.get("certainty")
    if c not in CERTAINTIES:
        errors.append(f"{where}: certainty must be one of {'|'.join(CERTAINTIES)} (got {c!r})")
    v = f["value"]
    if v is None or (isinstance(v, str) and v.strip().lower() in LOOSE_ABSENCES):
        errors.append(f"{where}: absence written as {v!r}; use \"not_visible\"")
        return
    if v in SENTINELS:
        return
    t = spec.get("type", "text")
    if t == "category" and v not in spec.get("values", []):
        errors.append(f"{where}: {v!r} is not in the category list (or use not_visible / unclear)")
    elif t == "boolean" and not isinstance(v, bool):
        errors.append(f"{where}: expected true or false (or not_visible / unclear), got {v!r}")


def validate(decode: dict, template: dict):
    """Return (errors, warnings) for one decode."""
    errors, warnings = [], []
    if not str(decode.get("raw", "")).strip():
        errors.append("raw: the first-pass description is missing (two passes are required)")
    sections = decode.get("sections") or {}
    for sec, sspec in template["sections"].items():
        fields = sspec["fields"]
        if sec == "text" and "steering_text" not in fields:
            warnings.append("template: the text section has no steering_text field")
        if sec not in sections:
            errors.append(f"{sec}: missing section (use [] or not_visible fields, never omit)")
            continue
        body = sections[sec]
        if sspec.get("list"):
            if not isinstance(body, list):
                errors.append(f"{sec}: must be a list")
                continue
            prefix, seen = sspec.get("id_prefix", ""), set()
            for i, item in enumerate(body):
                iid = item.get("id")
                if not iid:
                    errors.append(f"{sec}[{i}]: missing id")
                else:
                    if not (str(iid).startswith(prefix) and str(iid)[len(prefix):].isdigit()):
                        errors.append(f"{sec}[{i}]: id {iid!r} should look like {prefix}1, {prefix}2")
                    if iid in seen:
                        errors.append(f"{sec}[{i}]: duplicate id {iid!r}")
                    seen.add(iid)
                for name, spec in fields.items():
                    if name not in item:
                        errors.append(f"{sec}[{i}].{name}: missing")
                    else:
                        _check_field(f"{sec}[{i}].{name}", spec, item[name], errors)
                for extra in set(item) - set(fields) - {"id"}:
                    warnings.append(f"{sec}[{i}].{extra}: not in the template")
        else:
            if not isinstance(body, dict):
                errors.append(f"{sec}: must be an object")
                continue
            for name, spec in fields.items():
                if name not in body:
                    errors.append(f"{sec}.{name}: missing")
                else:
                    _check_field(f"{sec}.{name}", spec, body[name], errors)
            for extra in set(body) - set(fields):
                warnings.append(f"{sec}.{extra}: not in the template")
    for extra in set(sections) - set(template["sections"]):
        warnings.append(f"{extra}: section not in the template")
    return errors, warnings


def value_stats(decodes: list, template: dict) -> dict:
    """{"section.field": {value: count}} for category and boolean fields, including sentinels."""
    from collections import Counter
    out = {}
    for sec, sspec in template["sections"].items():
        for name, spec in sspec["fields"].items():
            if spec.get("type") not in ("category", "boolean"):
                continue
            c = Counter()
            for d in decodes:
                body = (d.get("sections") or {}).get(sec)
                items = body if isinstance(body, list) else [body or {}]
                for it in items:
                    f = it.get(name)
                    if isinstance(f, dict):
                        c[str(f.get("value"))] += 1
            out[f"{sec}{'[]' if sspec.get('list') else ''}.{name}"] = dict(c.most_common())
    return out


def main(argv):
    stats = "--stats" in argv
    argv = [a for a in argv if a != "--stats"]
    if len(argv) < 3:
        print(__doc__)
        return 2
    template = load_json(argv[1])
    files = []
    for a in argv[2:]:
        p = Path(a)
        files += sorted(p.glob("*.json")) if p.is_dir() else [p]
    bad = 0
    for f in files:
        e, w = validate(load_json(f), template)
        bad += bool(e)
        for x in e:
            print(f"ERROR {f.stem}: {x}")
        for x in w:
            print(f"warn  {f.stem}: {x}")
    print(f"{len(files)} decodes checked, {bad} with errors")
    if stats:
        for k, c in value_stats([load_json(f) for f in files], template).items():
            print(f"{k}: " + ", ".join(f"{v} {n}" for v, n in c.items()))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
