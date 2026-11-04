"""Shared helpers for Jev Lens scripts: the template and decode formats.

Template (template.json):
  {"sections": {
     "scene":  {"list": false, "fields": {"setting": {"type": "category", "values": ["outdoor/beach", ...]}}},
     "people": {"list": true,  "id_prefix": "p", "fields": {"posture": {"type": "text"}}}}}
  Field types: "category" (value must be one of "values"), "text", "boolean".

Decode (decodes/<image stem>.json):
  {"image": "image_01.jpg", "raw": "<first-pass description>",
   "sections": {
     "scene":  {"setting": {"value": "outdoor/beach", "certainty": "clear"}},
     "people": [{"id": "p1", "posture": {"value": "sitting", "certainty": "likely"}}]}}
  Every field is {"value": ..., "certainty": "clear" | "likely" | "unclear"}.
  A field with nothing to see has value "not_visible"; one that can't be made out has value "unclear".
"""
from __future__ import annotations

import json
from pathlib import Path

CERTAINTIES = ("clear", "likely", "unclear")
SENTINELS = ("not_visible", "unclear")
# Ways people write "nothing there" that should have been the not_visible sentinel.
LOOSE_ABSENCES = {"", "none", "n/a", "na", "null", "not visible", "not-visible", "nothing",
                  "no", "absent", "unknown", "not shown", "none visible"}


def load_json(path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def iter_fields(decode: dict):
    """Yield (path, section, item_index, field_name, field_obj) for every field in a decode.
    item_index is None for non-list sections."""
    for sec, body in (decode.get("sections") or {}).items():
        if isinstance(body, list):
            for i, item in enumerate(body):
                for name, f in item.items():
                    if name == "id":
                        continue
                    yield f"{sec}[{i}].{name}", sec, i, name, f
        elif isinstance(body, dict):
            for name, f in body.items():
                yield f"{sec}.{name}", sec, None, name, f


def load_decodes(folder) -> dict:
    """{image stem: decode} for every *.json in a folder, sorted by name."""
    return {p.stem: load_json(p) for p in sorted(Path(folder).glob("*.json"))}
