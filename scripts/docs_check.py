"""Doc map check: a change to a source must also change a doc that describes it, or say why not.

Usage: python3 scripts/docs_check.py [--base REF] [--head REF] [--body TEXT]
  --base  what the change is compared with (default origin/main); --head the change (default HEAD)
  --body  the PR description, searched for waivers along with the commit messages in base..head
A waiver line: "Docs checked: <doc> unchanged because <reason>". Also flags counts and rubric versions written into
hand-written README prose (they go stale), and retired names outside the files listed for them (retired-names.json).
Rules: docs-map.json. Why: CONTRIBUTING.md. Exits 1 with one line per problem.
"""
import argparse, fnmatch, json, pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
WAIVER = re.compile(r"Docs checked:\s*`?([\w./-]+)`?\s+unchanged because\s+\S.{3,}", re.I)


def git(*a):
    return subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, text=True, check=True).stdout


def matches(path, globs):
    return any(fnmatch.fnmatch(path, g) for g in globs)


def map_problems(rules, changed, added, waived, ignore=()):
    out = []
    changed = {p for p in changed if not matches(p, ignore)}; added = {p for p in added if not matches(p, ignore)}
    for r in rules:
        pool = added if r.get("added_only") else changed
        hits = sorted(p for p in pool if matches(p, r["sources"]) and p not in r["docs"])
        if not hits or any(d in changed for d in r["docs"]) or any(d in waived for d in r["docs"]): continue
        out.append(f"{r['name']}: {', '.join(hits)} changed, but none of {', '.join(r['docs'])} did ({r['why']}). "
                   f"Update one, or add 'Docs checked: {r['docs'][0]} unchanged because <reason>' to the PR description or a commit message.")
    return out


def count_problems(cfg, root=None):
    root = root or ROOT
    out = []
    pats = [re.compile(p, re.I) for p in cfg["patterns"]]
    files = sorted({p for g in cfg["files"] for p in root.glob(g)})
    for f in files:
        rel = f.relative_to(root).as_posix()
        if rel in cfg["skip"] or "/." in "/" + rel: continue
        fence = False
        for i, line in enumerate(f.read_text(errors="ignore").splitlines(), 1):
            if line.lstrip().startswith("```"): fence = not fence
            if fence or line.lstrip().startswith(("|", ">")): continue  # tables are generated; a quoted block is a dated sample
            for p in pats:
                m = p.search(line)
                if m: out.append(f"{rel}:{i}: '{m.group(0)}' in prose goes stale ({cfg['why']})")
    return out


def retired_problems(cfg, files):
    """files: {path: text}. A retired name may appear only in its allowed files (globs allowed); each allowed entry must
    still match a file that contains it, so the list can't go stale."""
    out = []
    for n in cfg["names"]:
        pat = re.compile(n["pattern"], re.I if "i" in n.get("flags", "") else 0)
        allowed = n.get("allowed", {})
        used = set()
        for path in sorted(files):
            if path == cfg.get("self"): continue
            hit_globs = [g for g in allowed if fnmatch.fnmatch(path, g)]
            for i, line in enumerate(files[path].splitlines(), 1):
                m = pat.search(line)
                if not m: continue
                if hit_globs: used.update(hit_globs); continue
                s, e = m.start(), m.end()
                while s > 0 and (line[s - 1].isalnum() or line[s - 1] == "_"): s -= 1
                while e < len(line) and (line[e].isalnum() or line[e] == "_"): e += 1
                out.append(f"{path}:{i}: '{line[s:e]}' is limited to the files listed in {cfg.get('self')} ({n['why']}). "
                           f"If this file means it that way on purpose, list the file in {cfg.get('self')} with a reason; otherwise use the new name.")
        for g in allowed:
            if g not in used: out.append(f"{cfg.get('self')}: '{g}' is allowed '{n['pattern']}' but no longer contains it; remove the entry")
    return out


def tracked_text(root=None):
    root = root or ROOT
    out = {}
    for rel in git("ls-files").split("\n"):
        f = root / rel
        if not rel or not f.is_file(): continue
        try: out[rel] = f.read_text()
        except (UnicodeDecodeError, OSError): pass
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--base", default="origin/main"); ap.add_argument("--head", default="HEAD"); ap.add_argument("--body", default="")
    a = ap.parse_args(argv)
    cfg = json.loads((ROOT / "docs-map.json").read_text())
    rng = f"{a.base}...{a.head}"
    changed = set(git("diff", "--name-only", rng).split())
    added = set(git("diff", "--name-only", "--diff-filter=A", rng).split())
    text = a.body + "\n" + git("log", "--format=%B", f"{a.base}..{a.head}")
    waived = {m.group(1) for m in WAIVER.finditer(text)}
    problems = map_problems(cfg["rules"], changed, added, waived, cfg.get("ignore", ())) + count_problems(cfg["count_lint"], ROOT)
    retired = ROOT / "retired-names.json"
    if retired.exists(): problems += retired_problems(dict(json.loads(retired.read_text()), self="retired-names.json"), tracked_text(ROOT))
    for p in problems: print("docs check: " + p, file=sys.stderr)
    if not problems: print("docs check: clean")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
