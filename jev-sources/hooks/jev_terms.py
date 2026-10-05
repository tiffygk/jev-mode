"""Shared patterns for the jev-sources hooks. The claim patterns (CLAIM, DESIGN, RELAY, WEAK, source_read)
serve an optional reply checker that is not shipped here."""
import re
from datetime import datetime
import os

ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))  # this install's jev-sources folder; realpath, since hooks are often symlinked into ~/.claude/hooks

# A Jev term. "choice", "score" and "state" alone are common words, so they count only in compounds.
_JEV_CI = re.compile(r"\b(jevs?|jevaluate[\w-]*|nouls?)\b|\b(choice|score)s? (primitive|question)s?\b", re.I)
# "typesafe" (TypeScript) and "system one" (Kahneman) are common in other senses: match the product names by case.
_JEV_CS = re.compile(r"\b(TypeSafe|System One)\b")


class _Jev:
    def search(self, s):
        return _JEV_CI.search(s) or _JEV_CS.search(s)

    def finditer(self, s):
        return sorted(list(_JEV_CI.finditer(s)) + list(_JEV_CS.finditer(s)), key=lambda m: m.start())


JEV = _Jev()
# Words that turn a mention into a design claim.
CLAIM = re.compile(r"\b(must|requires?|required|incorrect|not supported|unsupported|one (call|request)|(its|their) own (call|request)|in (one|a single) (call|request)|batch(ed)? (all|every)|per (request|call|candidate|passage|pair)|can'?t|cannot|not allowed|only works|has to|needs? to)\b", re.I)
# How Jev works, as opposed to a project or a rating: a claim needs one of these too.
DESIGN = re.compile(r"\b(nouls?|state|requests?|calls? per|per call|questions?|options?|levels?|criteria|instructions|thresholds?|confidence|primitives?|batch\w*|tokens?|passages?|candidates?|fan.?out|pinned model|model (version|id)s?|jev-\d+\.\d+)\b", re.I)
# A relayed subagent finding.
RELAY = re.compile(r"\b(reviewer|gate|subagent|agent|panel)s?\b\W+(?:\w+\W+){0,3}(says|said|found|flags?|flagged|claims?|reports?|calls? it|blocked)\b", re.I)
# Weaker Jev context, counted only beside a relayed finding ("the gate says one call per passage is wrong").
WEAK = re.compile(r"\b(cookbooks?|primitives?|state|passages?|candidates?|one call)\b", re.I)
# Evidence that a source was opened, checked per tool call (see source_read).
READ_PY = re.compile(r"jev-sources/scripts/read\.py")
SRC_PATH = re.compile(r"jev-sources(-data)?/(docs|cookbooks|patterns)/|_plans/(docs|cookbooks|patterns)/")
WEB = re.compile(r"docs\.typesafe\.ai")


def source_read(name, inp):
    """True when this tool call opened a TypeSafe source: read.py, a Read of a source file, or a web read of the docs."""
    inp = inp or {}
    if name == "Bash":
        c = inp.get("command") or ""
        return bool(READ_PY.search(c) or (WEB.search(c) and re.search(r"agent-browser|curl|defuddle", c)))
    if name == "Read":
        return bool(SRC_PATH.search(inp.get("file_path") or ""))
    if name == "WebFetch":
        return bool(WEB.search(inp.get("url") or ""))
    return False


def strip_code(text):
    return re.sub(r"```.*?```|`[^`\n]*`", " ", text, flags=re.S)
MARKER = "JEV-SOURCES:"
BRIEF = ("JEV-SOURCES: before any finding, run route.py on the question and read every READ FULL item with "
         f"read.py ({ROOT}/scripts); quote verbatim, give path#heading, label reference rule or "
         "cookbook example; findings without this are unverified.")


def sentences(text):
    return [x for x in re.split(r"(?<=[.!?])\s+|\n+", text) if x.strip()]


def same_sentence(text, a, b):
    return any(a.search(x) and b.search(x) for x in sentences(text))


def near(text, a, b, window=80):
    for m in a.finditer(text):
        lo, hi = max(0, m.start() - window), m.end() + window
        if b.search(text[lo:hi]):
            return True
    return False


def log(name, line):
    if "session=None" in line and not os.environ.get("JEV_HOOK_LOG_TESTS"):
        return  # test runs and hand-piped JSON carry no session id; keep them out of the retire count
    try:
        with open(os.path.join(os.path.expanduser(os.environ.get("JEV_HOOK_LOG_DIR") or "~/.claude/hooks"), f"{name}.log"), "a", encoding="utf-8") as f:
            f.write(f"{datetime.now().isoformat(timespec='seconds')} {line}\n")
    except OSError:
        pass


# Talk about this skill's own tooling (route.py, the hooks, topics.json), not about how Jev works.
TOOLING = re.compile(r"route\.py|read\.py|refresh\.sh|build_index|topics\.json|sections\.jsonl|SKILL\.md|jev-sources|"
                     r"\b(stop|dispatch|reminder|claim)[- ]hook|\bhooks?\b.{0,40}\b(fired|held|false alarm)", re.I)
