"""Fixed file rule for an eval case's packet, set before any gold answer is re-read (follow-on Task 7).
The root README; every file with a hosted Jev call (jev_callsites.call_lines on the manifest's files/);
then the files with any jev or decision hits until the list holds 4 files: non-test code first, then docs, tests, examples and demos,
then data files (results and records), each group by jev plus decision count, then path.
Each file is excerpted to 3,000 characters. hf, local and fixture cases keep their hand-picked files.

Usage: pick_files.py <manifest dir from coverage_manifest.py>   prints [[path, 3000], ...] as JSON
"""
import json, pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "jevaluate" / "scripts"))
import jev_callsites

CAP, MAX_FILES = 3000, 4
ROW = re.compile(r"^\| (.+?) \| (\d+) \| (\d+) \| (\d+) \| (\d+) \|")
DATA = re.compile(r"\.(json|jsonl|csv|tsv|txt|parquet)$")
TEST = re.compile(r"(^|/)(tests?|spec|__tests__|examples?|demos?|samples?)/|(^|/)test_[^/]*$|\.(test|spec)\.\w+$")
CODE = re.compile(r"\.(py|ts|tsx|js|jsx|mjs|cjs|go|rs|rb|java|kt|php|swift|c|cc|cpp|h|hpp|cs|scala|exs?|dart|lua|gs|sh)$")

def rows(manifest_dir):
    out = []
    for line in (pathlib.Path(manifest_dir) / "manifest.md").read_text().splitlines():
        m = ROW.match(line)
        if m: out.append((m.group(1), int(m.group(3)) + int(m.group(4))))
    return out

def pick(manifest_dir):
    rs = rows(manifest_dir); paths = [p for p, _ in rs]
    chosen = [p for p in paths if p.lower() == "readme.md"]
    chosen += [p for p in sorted(jev_callsites.call_lines(pathlib.Path(manifest_dir) / "files")) if p in paths and p not in chosen]
    group = lambda p: 0 if CODE.search(p) and not TEST.search(p) else 2 if DATA.search(p) else 1
    for p, _ in sorted(((p, s) for p, s in rs if p not in chosen and s > 0), key=lambda r: (group(r[0]), -r[1], r[0])):
        if len(chosen) >= MAX_FILES: break
        chosen.append(p)
    return [[p, CAP] for p in chosen]

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__); sys.exit(0 if len(sys.argv) == 2 else 2)
    print(json.dumps(pick(sys.argv[1])))
