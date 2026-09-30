"""Flag rater tool calls that read rubric.md, past ratings or a files_full/ path directly. Usage: scan_transcripts.py <rating.md> <subagent .jsonl> ..."""
import json, pathlib, re, sys
WATCH = re.compile(r"rubric\.md|jevaluate-library/projects/|\.steps\.json|approved_cost|routing_revised|jev-rules\.md|fix-catalog\.md|/ratings/|jevaluate-round2/[^/ ]+\.md|index\.md|rubric_text|grep\b.*\bjevaluate/|files_full", re.I)
ALLOW = re.compile(r"^\s*(python3\s+)?\S*\b(step|library|coverage_manifest)\.py\b")
SPLIT = re.compile(r";|&&|\|\||\||\n|\$\(|`|\)")
STEP = re.compile(r"\bstep\.py\s+(?:next|full)\s+(\S+)")


def segments(part):
    inp = part.get("input", {})
    if part.get("name") == "Bash": return [x for x in SPLIT.split(inp.get("command", "")) if x.strip()]
    return [(part.get("name") or "").lower() + " " + " ".join(str(inp.get(k, "")) for k in ("file_path", "path", "pattern", "glob"))]


def scan(paths, rating):
    flags = []
    for path in paths:
        for i, line in enumerate(open(path, errors="ignore"), 1):
            try: rec = json.loads(line)
            except ValueError: continue
            content = (rec.get("message") or {}).get("content") or []
            for part in content if isinstance(content, list) else []:
                if not isinstance(part, dict) or part.get("type") != "tool_use": continue
                for seg in segments(part):
                    m = STEP.search(seg)
                    if m and pathlib.Path(m.group(1)).name != pathlib.Path(rating).name: flags.append(f"{path}:{i} step.py on {m.group(1)}, not {rating}")
                    elif WATCH.search(seg) and not (ALLOW.search(seg) and not re.search(r"[<>]", seg)): flags.append(f"{path}:{i} {part.get('name')} {seg[:160]}")
    return flags


if __name__ == "__main__":
    f = scan(sys.argv[2:], sys.argv[1]); print("\n".join(f) or "clean"); sys.exit(1 if f else 0)
