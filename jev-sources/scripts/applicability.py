"""Which Jev model a source section needs, and whether TypeSafe calls it not production-ready.

applicability.json lists entries {match, needs, status, source, quote}: match is a page path or path#heading (a heading
entry wins over its page); needs is the oldest model the section works on; status is "experimental" when TypeSafe says
the feature isn't ready for production; source and quote give the verbatim line (path#heading) that says so. An entry may
carry "also": more {source, quote} pairs. tests/test_applicability.py checks every quote against the library.
"""
import json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import CODE, DATA

# Used only when the library has no usable docs/models.md#Aliases table; aliases() reads that table.
ALIASES = {"jev-preview": "jev-1.14.0", "jev-latest": "jev-1.14.0"}
ALIAS_SECTION = re.compile(r"^#+ Aliases[ \t]*$(.*?)(?=^#|\Z)", re.M | re.S)
ALIAS_ROW = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|", re.M)
VERSION = re.compile(r"^jev-(\d{1,6})(?:\.(\d{1,6}))?(?:\.(\d{1,6}))?$")  # a longer number is not a real ID (and int() refuses thousands of digits)
MODEL = re.compile(r"\bjev-(?:latest|preview|\d+(?:\.\d+){0,2})", re.I)
# A page that states a model or readiness limit: "need(s) Jev 1.15", "Dreamer-ready", "ready for production", a Danger-Zone header
LIMIT = re.compile(r"\bneeds?\s+Jev\s+\d|Dreamer-ready|ready for production|Danger-Zone|\bis experimental\b", re.I)
_entries = None
_aliases = None


def entries():
    global _entries
    if _entries is None:
        try:
            _entries = json.load(open(os.path.join(CODE, "applicability.json")))["entries"]
        except (OSError, ValueError, KeyError):
            _entries = []
    return _entries


def aliases():
    """Alias to versioned ID, from the rows of docs/models.md#Aliases whose target is a version; ALIASES fills in any alias the
    table lacks, and replaces the table when the page, the section or a usable jev-latest row is missing."""
    global _aliases
    if _aliases is None:
        try:
            text = open(os.path.join(DATA, "docs", "models.md"), encoding="utf-8").read()
        except (OSError, ValueError):
            text = ""
        section = ALIAS_SECTION.search(text)
        rows = ALIAS_ROW.findall(section.group(1)) if section else []
        table = {a.lower(): t.lower() for a, t in rows if VERSION.match(t.lower())}
        _aliases = {**ALIASES, **table} if "jev-latest" in table else ALIASES
    return _aliases


MODEL_QUOTE = re.compile(r"\bJev\s+\d")  # a quote that names a model: the section that states what the entry needs


def quotes(entry):
    return [(entry["source"], entry["quote"])] + [(a["source"], a["quote"]) for a in entry.get("also", [])]


def lookup(path, heading, entries_=None):
    es = entries() if entries_ is None else entries_
    for key in (path + "#" + heading, path):
        for e in es:
            if e["match"] == key:
                return {"needs": e.get("needs"), "status": e.get("status"), "source": e["source"], "quote": e["quote"], "note": e.get("note"),
                        "needs_source": next((s for s, q in quotes(e) if MODEL_QUOTE.search(q)), e["source"])}
    return {"needs": None, "status": None, "source": None, "quote": None, "note": None, "needs_source": None}


def version(model):
    """(1, 14, 0) for 'jev-1.14' or 'jev-1.14.0' (aliases resolved); None when it isn't a version."""
    model = aliases().get((model or "").lower(), (model or "").lower())
    m = VERSION.match(model)
    return tuple(int(x or 0) for x in m.groups()) if m else None


def checked(model):
    """The --model value if it is a Jev model, else None with a warning on stderr (routing then names no model)."""
    if model is not None and version(model) is None:
        print(f"warning: --model {model!r} is not a Jev model (jev-1.13.0, jev-latest, jev-preview); ignoring it", file=sys.stderr)
        return None
    return model


def allowed(entry, model):
    """False when the model is older than the entry needs. An unknown model or no requirement rules nothing out."""
    need, have = version(entry.get("needs")), version(model)
    return need is None or have is None or have >= need


def find_model(text):
    """The oldest model named in the text (a question naming several is about the oldest), or None."""
    found = [m.group(0).lower() for m in MODEL.finditer(text or "")]
    return min(found, key=lambda m: version(m) or (9999,)) if found else None


def covered(path, entries_=None):
    return any(e["match"] == path or e["match"].startswith(path + "#") for e in (entries() if entries_ is None else entries_))


def uncovered(pages_text, entries_=None):
    """Paths (from {path: text}) that state a model or readiness limit and have no entry yet."""
    return sorted(p for p, t in pages_text.items() if LIMIT.search(t) and not covered(p, entries_))
