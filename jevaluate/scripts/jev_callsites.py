"""Count Jev usage in a folder or file: call sites, question types, thresholds, model pinning, confidence use.

Usage: python3 jev_callsites.py <path> [--list]
Pattern counts are a starting point: confirm them against the code you read.
"""
import re, sys, pathlib, json

EXT = {".py", ".ts", ".tsx", ".js", ".mjs", ".md", ".json", ".yaml", ".yml", ".toml", ".sh"}
PAT = {
    "call_sites": r"system_one\s*\(|systemOne\s*\(|api\.typesafe\.ai|/v1/systemone",
    "noul": r"\bNoul\s*\(|[\"']?type[\"']?\s*:\s*[\"']noul[\"']",
    "choice": r"\bChoice\s*\(|[\"']?type[\"']?\s*:\s*[\"']choice[\"']",
    "score": r"\bScore\s*\(|[\"']?type[\"']?\s*:\s*[\"']score[\"']",
    "confidence_used": r"\.confidence\b|\.probabilities\b|\.noul\s*[<>]=?",
    "model_pinned": r"jev-\d+\.\d+\.\d+",
    "model_alias": r"jev-(latest|preview)\b|jev-\d+\.\d+(?![.\d])",
    "threshold_consts": r"^\s*[A-Z][A-Z0-9_]*(THRESH|CUTOFF|FLOOR|MIN|MAX|CONF|_T)\w*\s*[:=]\s*0?\.\d+",
    "threshold_in_prose": r"\b(above|below|over|under|at least|greater than|less than)\s+0?\.\d+\b",
}
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
    root = pathlib.Path(sys.argv[1]); show = "--list" in sys.argv
    if not root.exists():
        sys.exit(f"path not found: {root}")
    tot = {k: 0 for k in PAT}; where = {k: [] for k in PAT}; jev_files = []
    for f in files(root):
        try: text = f.read_text(errors="ignore")
        except Exception: continue
        if not any(k in text.lower() for k in KEEP): continue
        jev_files.append(str(f))
        for i, line in enumerate(text.splitlines(), 1):
            for k, rx in PAT.items():
                n = len(re.findall(rx, line, re.I if k != "threshold_consts" else 0))
                if n:
                    tot[k] += n
                    if show and len(where[k]) < 8: where[k].append(f"{f.name}:{i}")
    q = tot["noul"] + tot["choice"] + tot["score"]
    out = {"files_mentioning_jev": len(jev_files), **tot, "questions_total": q,
           "questions_per_call_site": round(q / tot["call_sites"], 1) if tot["call_sites"] else None}
    print(json.dumps(out, indent=2))
    if show:
        print(json.dumps({k: v for k, v in where.items() if v}, indent=2))
    print("NOTE: question counts are static. A question built inside a loop or comprehension counts once; read the code for runtime counts.")
    if tot["call_sites"] == 0:
        print("NOTE: no Jev call sites found. Check for wrappers or MCP tools before rating 'Jev in name only'.")

if __name__ == "__main__":
    main()
