"""Count Jev usage in a folder or file: mentions, hosted calls, question types, thresholds, model pinning, confidence use.

`mentions` counts every textual hit (system_one(, api.typesafe.ai, /v1/systemone), docs and tests included.
`hosted_calls` counts only real reach-outs to hosted Jev: the endpoint (api.typesafe.ai), an SDK client
construction or import, or a gateway model ID (typesafe/jev...), in code or config files outside tests/, test_*,
docs/, fixtures/, example(s)/, sample(s)/, bench(mark)(s)/ folders, files named bench*, and *.md; .json data files (results, analysis) never count. An adapter
that imitates the API, or docs and fixtures, gives mentions but hosted_calls 0.

Usage: python3 jev_callsites.py <path> [--list] [--json]
--json prints only the JSON on stdout; the NOTE lines go to stderr.
Pattern counts are a starting point: confirm them against the code you read.
"""
import re, sys, pathlib, json

EXT = {".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".rb", ".go", ".rs", ".java", ".kt", ".php", ".swift", ".c", ".cc", ".cpp", ".h", ".hpp",
       ".cs", ".scala", ".ex", ".exs", ".dart", ".lua", ".md", ".json", ".yaml", ".yml", ".toml", ".sh", ".gs"}  # .gs: Google Apps Script
PAT = {
    "mentions": r"system_one\s*\(|systemOne\s*\(|api\.typesafe\.ai|/v1/systemone",
    "noul": r"\bNoul\s*\(|[\"']?type[\"']?\s*:\s*[\"']noul[\"']",
    "choice": r"\bChoice\s*\(|[\"']?type[\"']?\s*:\s*[\"']choice[\"']",
    "score": r"\bScore\s*\(|[\"']?type[\"']?\s*:\s*[\"']score[\"']",
    "confidence_used": r"\.confidence\b|\.probabilities\b|\.noul\s*[<>]=?",
    "model_pinned": r"jev-\d+\.\d+\.\d+",
    "model_alias": r"jev-(latest|preview)\b|jev-\d+\.\d+(?![.\d])",
    "threshold_consts": r"^\s*[A-Z][A-Z0-9_]*(THRESH|CUTOFF|FLOOR|MIN|MAX|CONF|_T)\w*\s*[:=]\s*0?\.\d+",
    "threshold_in_prose": r"\b(above|below|over|under|at least|greater than|less than)\s+0?\.\d+\b",
}
HOSTED = re.compile(
    r"api\.typesafe\.ai|@typesafe-ai/sdk|^[ \t]*from[ \t]+typesafe(_ai|_sdk)?[ \t]+import|^[ \t]*import[ \t]+typesafe(_ai|_sdk)?\b"
    r"|require\(?[ \t]*['\"]typesafe|Typesafe::(SDK::)?Client|(?<![/\w.\-])(?-i:typesafe(-ai)?/jev)[\w.\-]*"
    r"|@ai-sdk/typesafe-ai|@effect/ai-typesafe", re.I | re.M)  # AI SDK and Effect providers; typesafe-ai/jev is the Vercel gateway ID, never part of a URL or path
NOT_HOSTED_DIRS = {"tests", "test", "spec", "docs", "fixtures",
                   "examples", "example", "samples", "sample", "benchmarks", "benchmark", "bench"}  # rubric "Non-test code": example folders and benchmark scripts don't count
# not demo/demos (a demo project's app can live there) and not eval/evals (eval scripts are a judgment call)
DATA_EXT = {".json", ".yaml", ".yml", ".toml"}
HOSTED_EXT = EXT - {".md", ".json"}


def counts_as_hosted_path(rel: pathlib.PurePath) -> bool:
    """True when a file at this repo-relative path is non-test code or config that may hold a hosted call."""
    if any(part in NOT_HOSTED_DIRS for part in rel.parts[:-1]): return False
    if rel.name.startswith("test_") or rel.stem.endswith("_test"): return False
    if rel.name.lower().startswith("bench"): return False  # bench_x.py, benchmark.js
    return rel.suffix in HOSTED_EXT or rel.name == "package.json"


def counts_as_hosted_file(f: pathlib.Path, root: pathlib.Path) -> bool:
    return counts_as_hosted_path(f.relative_to(root) if root.is_dir() else pathlib.Path(f.name))


def unflatten(name: str) -> str:
    """coverage_manifest.py saves 'src/x.py' as 'src__x.py' (a leading dot gets a '_' prefix): recover the repo path."""
    return name[1:].replace("__", "/") if name.startswith("_.") else name.replace("__", "/")


# A TypeSafe class constructed (case-sensitive, so a helper like typesafe_agreement( is not one), or a call on a typesafe module
CONSTRUCT = re.compile(r"(?<!\w)(?:create|make|new_?|Async|Sync)?Type[Ss]afe\w*\s*\(|(?i:\btypesafe\w*\.\w+\s*\()")
SDK_SEND = re.compile(r"\bexperimental_evaluate\s*\(|\bevaluate\s*\(\s*\{")
ASSIGNED = re.compile(r"(\w+)\s*(?::[^=\n]*)?=[^=]*$")


def calls_in(items):
    """The one call-line rule: {repo path: [line numbers]} of hosted-call lines in the non-test files of `items`, an iterable of
    (repo path, {line number: text}). library.py (F0 yes and no) and jevaluate-eval/check_labels.py both use it, so they cannot drift."""
    out = {}
    for path, lines in items:
        if not counts_as_hosted_path(pathlib.PurePath(path)): continue
        hits = lines_with_calls(lines)
        if hits: out[str(pathlib.PurePath(path))] = hits
    return out


def call_lines(files_dir):
    """{repo path: [line numbers]} of lines that make or start a hosted call: everything hosted_lines finds, a line that
    constructs a TypeSafe client, and a method call on a name the same file assigns from such a construction."""
    return calls_in((str(unflatten(f.name)), dict(enumerate(f.read_text(errors="ignore").splitlines(), 1)))
                    for f in sorted(pathlib.Path(files_dir).iterdir()) if f.is_file())


def lines_with_calls(lines):
    """Sorted line numbers, of a {line number: text} map, that make or start a hosted call (the call_lines rule)."""
    names, hits = set(), set()
    for i, line in sorted(lines.items()):
        m = CONSTRUCT.search(line)
        if m:
            hits.add(i); a = ASSIGNED.search(line[:m.start()])
            if a: names.add(a.group(1))
        elif HOSTED.search(line): hits.add(i)
    if names:
        call = re.compile(r"\b(?:" + "|".join(map(re.escape, names)) + r")\.\w+\s*\(")
        hits |= {i for i, line in lines.items() if call.search(line)}
    if hits:  # the AI SDK's evaluate() sends to whichever provider the file set up; here that is TypeSafe
        hits |= {i for i, line in lines.items() if SDK_SEND.search(line)}
    return sorted(hits)


# --- What an F0 yes may cite: a line that makes the call, not one that mentions or declares it (rubric "Calls Jev (F0)") ---
LINE_COMMENT = re.compile(r"^(?:#(?!\s*include\b)|//|/\*|\*|--\s|<!--|;)")
TRAIL_COMMENT = re.compile(r"(?<=\s)(?:#|//)\s.*$|(?<=\s)(?:#|//)$")
ERROR_NAME = re.compile(r"\w*Type[Ss]afe\w*(?:Error|Exception)\w*|\b\w*(?:Error|Exception)\b(?=\s*\()")
IMPORT = re.compile(r"^(?:import\b|from\s+\S+\s+import\b|export\s+(?:\*|\{[^}]*\})\s+from\b|(?:(?:const|let|var)\s+)?[^=()]*=\s*(?:await\s+)?require\s*\(|require(?:_relative|_once)?\b|"
                    r"#\s*include\b|using\s+[\w.]+\s*;|use\s+[\w:]+|extern\s+crate\b|@import\b|\}?\s*from\s+['\"][^'\"]+['\"]\s*;?$)")
VERSION = r"[\^~<>=*v]*\d[\w.*+\-]*"
DEPENDENCY = re.compile(r"^(?:[\"']?[@\w./-]+[\"']?\s*[:=]\s*[\"']" + VERSION + r"[\"'],?$|[\w.\-\[\]]+\s*(?:==|>=|<=|~=|!=)\s*[\d.]+.*$|"
                        r"(?:gem|implementation|api|compile|testImplementation|runtimeOnly|pod)\s+[\"']|[\"']?@?[a-z0-9./-]*typesafe[a-z0-9./-]*[\"']?\s*[:=]\s*[\"'][^\"']*[\"'],?$|"
                        r"<(?:artifactId|groupId|dependency)>|(?:pip|pip3|npm|yarn|pnpm|uv|cargo|go|gem|brew)\s+(?:install|add|get|i)\b)")
MODS = r"(?:(?:export|default|abstract|public|private|protected|internal|static|final|sealed|async|override|virtual|readonly|pub(?:\([\w:]+\))?|synchronized)\s+)"
DECLARATION = re.compile(r"^" + MODS + r"*(?:class|interface|struct|enum|trait|impl|type|def|fn|func|function|fun|sub)\s+[\w(*\[]|^" + MODS + r"*constructor\s*\(|"
                         r"^" + MODS + r"+[\w<>\[\],.? ]*?\w+\s*\([^)=]*\)\s*(?:throws\s+[\w.,\s]+)?\{?$")
REGEX_USE = re.compile(r"\bre\.(?:compile|match|search|sub|findall|fullmatch|split)\b|\bRegExp\b|Pattern\.compile\b|\bRegex(?:::new)?\s*\(|=~|\.(?:test|match|replace|exec)\(\s*/|"
                       r"^[\w.\[\]$]+\s*[:=]\s*/(?![/*]).*/[a-z]*[;,]?$|[=(:,]\s*/(?![/*])(?:[^/\\\n]|\\.)+/[gimsuyd]*\s*[;,)]")
STRING_ONLY = re.compile(r"^[\[({\s,]*(?:[rbfu]{0,2}(?:\"[^\"]*\"|'[^']*'|`[^`]*`)\s*[,;)\]}]*\s*)+$")


def code_lines(lines):
    """{line number: the line's code}: '' for a blank line, a comment, or the inside of a block comment or docstring."""
    out, block, doc = {}, False, None
    for i, raw in sorted(lines.items()):
        s = raw.strip()
        if block:
            block = "*/" not in s; out[i] = ""; continue
        if doc:
            if doc in s: doc = None
            out[i] = ""; continue
        if s.startswith("/*"): block = "*/" not in s; out[i] = ""; continue
        if s[:3] in ('\"\"\"', "\'\'\'"):
            if s.count(s[:3]) == 1: doc = s[:3]
            out[i] = ""; continue
        out[i] = "" if LINE_COMMENT.match(s) else TRAIL_COMMENT.sub("", s).strip()
    return out


def is_call_code(c):
    """False for a line of code (comments stripped) that only mentions or declares a call: an import, dependency, throw or error class,
    class or constructor declaration, or a regex or bare string."""
    c = ERROR_NAME.sub("", c).strip()
    if not c or re.match(r"(?:except|catch|rescue|\}\s*catch)\b", c) or re.search(r"\b(?:throw|raise)\b", c): return False
    return not (IMPORT.match(c) or DEPENDENCY.match(c) or DECLARATION.match(c) or REGEX_USE.search(c) or STRING_ONLY.match(c))


CALL_EXPR = re.compile(r"([A-Za-z_$][\w$]*)\s*\(")
NOT_CALLS = {"if", "elif", "for", "while", "switch", "catch", "with", "return", "not", "and", "or", "in", "is", "assert", "yield", "await", "lambda", "except", "match", "case"}


MODULE_CALL = re.compile(r"\btypesafe(?:_ai|_sdk)?\.\w+\s*\(", re.I)  # typesafe.noul(...) on the imported module


def is_marker(c):
    """True when a line of code shows the file is set up for hosted Jev: a client construction, a call on the TypeSafe module, api.typesafe.ai URL or gateway model ID
    (not in a comment, a regex, or an error class)."""
    c = ERROR_NAME.sub("", c).strip()
    if not c or REGEX_USE.search(c) or IMPORT.match(c) or DEPENDENCY.match(c): return False  # an unused import is not set-up for a call
    return bool(HOSTED.search(c) or CONSTRUCT.search(c) or MODULE_CALL.search(c))


def lines_citable(lines):
    """Sorted line numbers of a {line number: text} map that an F0 yes may cite: in a file that holds a hosted marker, every line that is a call
    expression or names the endpoint or a model ID, except imports, dependencies, comments, throws, declarations, regexes and bare strings."""
    code = code_lines(lines)
    if not any(is_marker(c) for c in code.values()): return []
    return [i for i, c in sorted(code.items()) if is_call_code(c) and (HOSTED.search(c) or any(m.group(1) not in NOT_CALLS for m in CALL_EXPR.finditer(c)))]


def citable_in(items):
    """{repo path: [line numbers]} an F0 yes may cite, in the non-test files of `items`, an iterable of (repo path, {line number: text})."""
    out = {}
    for path, lines in items:
        if not counts_as_hosted_path(pathlib.PurePath(path)) or pathlib.PurePath(path).name == "package.json": continue  # a manifest lists dependencies, it never calls
        hits = lines_citable(lines)
        if hits: out[str(pathlib.PurePath(path))] = hits
    return out


def citable_lines(files_dir):
    """citable_in over an evidence files/ folder."""
    return citable_in((str(unflatten(f.name)), dict(enumerate(f.read_text(errors="ignore").splitlines(), 1)))
                      for f in sorted(pathlib.Path(files_dir).iterdir()) if f.is_file())


def hosted_lines(files_dir):
    """{repo path: [line numbers]} of hosted-call lines in the non-test files of an evidence files/ folder."""
    out = {}
    for f in sorted(pathlib.Path(files_dir).iterdir()):
        rel = pathlib.PurePath(unflatten(f.name))
        if not f.is_file() or not counts_as_hosted_path(rel): continue
        hits = [i for i, line in enumerate(f.read_text(errors="ignore").splitlines(), 1) if HOSTED.search(line)]
        if hits: out[str(rel)] = hits
    return out


KEEP = ("typesafe", "system_one", "systemone", "noul", "jev")

def files(root: pathlib.Path):
    if root.is_file():
        yield root; return
    for p in root.rglob("*"):
        if p.is_file() and p.suffix in EXT and not any(x in p.parts for x in (".git", "node_modules", ".venv", "venv", "dist")):
            yield p

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__); sys.exit(0 if len(sys.argv) > 1 else 2)
    root = pathlib.Path(sys.argv[1]); show = "--list" in sys.argv; note = sys.stderr if "--json" in sys.argv else sys.stdout
    if not root.exists():
        sys.exit(f"path not found: {root}")
    tot = {k: 0 for k in PAT}; where = {k: [] for k in PAT}; jev_files = []; hosted = 0; hosted_where = []
    for f in files(root):
        try: text = f.read_text(errors="ignore")
        except Exception: continue
        if not any(k in text.lower() for k in KEEP): continue
        jev_files.append(str(f))
        if counts_as_hosted_file(f, root):
            n = len(HOSTED.findall(text))
            hosted += n
            if n and len(hosted_where) < 8: hosted_where.append(f.name)
        for i, line in enumerate(text.splitlines(), 1):
            for k, rx in PAT.items():
                n = len(re.findall(rx, line, re.I if k != "threshold_consts" else 0))
                if n:
                    tot[k] += n
                    if show and len(where[k]) < 8: where[k].append(f"{f.name}:{i}")
    q = tot["noul"] + tot["choice"] + tot["score"]
    out = {"files_mentioning_jev": len(jev_files), "mentions": tot["mentions"], "hosted_calls": hosted,
           **{k: v for k, v in tot.items() if k != "mentions"}, "questions_total": q,
           "questions_per_hosted_call": round(q / hosted, 1) if hosted else None}
    print(json.dumps(out, indent=2))
    if show:
        print(json.dumps({k: v for k, v in where.items() if v} | ({"hosted_calls": hosted_where} if hosted_where else {}), indent=2))
    print("NOTE: question counts are static. A question built inside a loop or comprehension counts once; read the code for runtime counts.", file=note)
    if hosted == 0:
        print("NOTE: hosted_calls is 0" + (f" ({tot['mentions']} mentions are docs, tests, fixtures or an imitation of the API)" if tot["mentions"] else "") + ". Check for wrappers or MCP tools before rating 'Jev in name only'.", file=note)

if __name__ == "__main__":
    main()
