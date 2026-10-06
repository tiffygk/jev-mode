"""Coverage manifest: every text file in a GitHub repo, or a local folder, that could change a Jevaluate verdict.

Usage: python3 coverage_manifest.py owner/repo OUTDIR [--commit SHA]
       python3 coverage_manifest.py --local FOLDER OUTDIR     (a private rating; nothing leaves the machine)
Writes OUTDIR/manifest.md, OUTDIR/meta.json and OUTDIR/files/<path with / -> __>.
Saved names never start with "." (a hidden dotfile is one nobody reads).
"""
import json, re, subprocess, sys, pathlib, urllib.request, urllib.parse

SKIP = re.compile(r"(^|/)(node_modules|vendor|dist|build|\.venv|__pycache__)/|lock|\.min\.|\.(png|jpe?g|gif|ico|webp|mp4|mov|woff2?|ttf|pdf|zip|gz|pt|bin|safetensors|onnx|pkl|npy|parquet)$", re.I)
G = {"jev": r"typesafe|system_one|systemOne|api\.typesafe\.ai|jev-[0-9]|jev-latest|\bNoul|\bChoice\b|\bScore\b",
     "decision": r"threshold|confidence|\bprob|calibrat|>=\s*0\.\d|cutoff",
     "eval": r"\blabel|\bgold\b|\beval|accuracy|brier|\bece\b|precision|recall"}
DATA_CAP = 25_000
KEEP_WHOLE_DECISION_HITS = 10  # real question catalogues (33 hits) clear it; results and fixtures files (1-7) do not
DATA_EXT = re.compile(r"\.(json|jsonl|csv|tsv|ya?ml|txt)$", re.I)
CODE_EXT = re.compile(r"\.(py|ts|tsx|js|mjs|jsx|go|rs|rb|java|kt|php|ipynb|vue|svelte|swift|c|cc|cpp|h|hpp|cs|scala|exs?|dart|lua|gs|cjs|json|ya?ml|toml)$")


def saved_name(path):
    """Flatten a repo path to one file name that is never a dotfile."""
    name = path.replace("/", "__")
    return "_" + name if name.startswith(".") else name


def _summary(text):
    try: obj = json.loads(text)
    except ValueError:
        lines = text.splitlines(); return f"{len(lines)} records (lines); first lines:\n" + "\n".join(lines[:5])
    def walk(o, depth=0):
        if isinstance(o, dict):
            if depth >= 2: return f"object with {len(o)} keys"
            return {k: (v if isinstance(v, (int, float, bool)) or (isinstance(v, str) and len(v) < 80) else walk(v, depth + 1)) for k, v in list(o.items())[:40]}
        if isinstance(o, list): return f"{len(o)} records"
        return o
    return json.dumps(walk(obj), indent=1)[:1800]


def _keys(text):
    try: o = json.loads(text)
    except ValueError: return ("lines", len(text) // 20000)
    if isinstance(o, dict): shape = tuple(sorted(o))[:20]
    elif isinstance(o, list) and o and isinstance(o[0], dict): shape = ("list", tuple(sorted(o[0]))[:20])
    else: shape = type(o).__name__
    return (shape, len(text) // 20000)


def cap_data(path, text, hits, seen_shapes):
    """Sample a data file over DATA_CAP by content. Returns (text_out, note)."""
    if not DATA_EXT.search(path) or len(text) <= DATA_CAP: return text, ""
    shape = (pathlib.Path(path).name, _keys(text))
    if shape in seen_shapes: return text[:1000] + "\n...\n" + _summary(text), f"sampled: repeat of {seen_shapes[shape]}"
    seen_shapes[shape] = path
    if hits.get("jev", 0) > 0 and hits.get("decision", 0) >= KEEP_WHOLE_DECISION_HITS: return text, ""
    if hits.get("jev") or hits.get("eval"): return text[:2000] + "\n...\n## Summary (generated)\n" + _summary(text), "sampled: results summary"
    return text[:1000], "sampled: no Jev content"


def build_manifest(repo, out, meta, sha, tree, fetch):
    """tree: list of {'path','size'} blobs. fetch(path) -> text or None."""
    out = pathlib.Path(out); (out / "files").mkdir(parents=True, exist_ok=True)
    text = {}
    for t in tree:
        p = t["path"]
        if SKIP.search(p) or t.get("size", 0) > 200_000: continue
        try: text[p] = fetch(p)
        except Exception: text[p] = None
    hits = {p: {g: len(re.findall(r, s, re.I)) for g, r in G.items()} for p, s in text.items() if s}
    keep = {p for p, h in hits.items() if h["jev"]}
    for _ in range(2):  # follow imports of Jev-call modules
        mods = {pathlib.Path(p).stem for p in keep if pathlib.Path(p).stem not in ("__init__", "index", "README")}
        keep |= {p for p, s in text.items() if s and p not in keep and any(re.search(rf"(import|from|require\().{{0,80}}\b{re.escape(m)}\b", s) for m in mods)}
    keep |= {p for p, h in hits.items() if h["decision"] or h["eval"]} & {p for p in text if CODE_EXT.search(p)}
    keep |= {p for p in text if re.match(r"(?i)readme", pathlib.Path(p).name) and "/" not in p}
    failed = [p for p, s in text.items() if s is None]
    rows, tot, seen, notes = [], 0, {}, []
    for p in sorted(keep):
        h = hits.get(p, {}); out_text, note = cap_data(p, text[p], h, seen)
        (out / "files" / saved_name(p)).write_text(out_text); tot += len(out_text)
        notes.append(note)
        if note:
            (out / "files_full").mkdir(exist_ok=True); (out / "files_full" / saved_name(p)).write_text(text[p])
        rows.append(f"| {p} | {len(out_text)} | {h.get('jev', 0)} | {h.get('decision', 0)} | {h.get('eval', 0)} | {note} |")
    (out / "manifest.md").write_text(
        f"# Coverage manifest: {repo} @ {sha[:10]}\n\nTree: {len(tree)} files; fetched {len(text)} text files; {len(keep)} kept ({tot} chars, ~{tot // 4} tokens). Fetch failed: {failed or 'none'}.\n"
        "Kept = Jev-call files, files importing them (2 passes), code/config with decision or eval terms, root README.\n"
        + ("Never read files_full/: uncapped copies of the sampled files, kept for the code checks.\n" if any(n for n in notes) else "") + "\n"
        "| file | chars | jev | decision | eval | note |\n|---|---|---|---|---|---|\n" + "\n".join(rows) + "\n")
    json.dump({"repo": repo, "commit": sha, "stars": meta.get("stargazers_count"), "pushed": meta.get("pushed_at"),
               "license": (meta.get("license") or {}).get("spdx_id")}, open(out / "meta.json", "w"), indent=1)
    return {"kept": len(keep), "chars": tot}


LOCAL_SKIP_DIRS = {".git", ".hg", ".svn"}


def local_main(folder, outdir):
    """The same manifest from a folder on disk: same skip rules and size cap. Commit: git HEAD when the folder is a clean
    git checkout, else local-<sha256 of the kept paths and contents> so a re-rating can tell whether anything changed."""
    import hashlib, os
    root = pathlib.Path(folder).expanduser().resolve()
    if not root.is_dir(): sys.exit(f"not a folder: {root}")
    tree = []
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in LOCAL_SKIP_DIRS)
        for f in sorted(files):
            full = pathlib.Path(dirpath) / f
            if full.is_symlink() or not full.is_file(): continue
            tree.append({"path": full.relative_to(root).as_posix(), "size": full.stat().st_size, "type": "blob"})
    def fetch(path):
        raw = (root / path).read_bytes()
        if b"\0" in raw[:4096]: raise ValueError("binary")
        return raw.decode("utf-8", "ignore")
    h = hashlib.sha256()
    for t in tree: h.update(t["path"].encode()); h.update(str(t["size"]).encode())
    sha = "local-" + h.hexdigest()[:12]
    g = subprocess.run(["git", "-C", str(root), "status", "--porcelain"], capture_output=True, text=True)
    if g.returncode == 0 and not g.stdout.strip():
        head = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True)
        if head.returncode == 0: sha = head.stdout.strip()
    r = build_manifest(f"local:{root.name}", outdir, {}, sha, tree, fetch)
    print(pathlib.Path(outdir) / "manifest.md", r["kept"], "files", r["chars"], "chars")


def _gh(p): return json.loads(subprocess.run(["gh", "api", p], capture_output=True, text=True, check=True).stdout)


def main(repo, outdir, commit=None):
    meta = _gh(f"repos/{repo}"); sha = commit or _gh(f"repos/{repo}/commits/{meta['default_branch']}")["sha"]
    tree = [t for t in _gh(f"repos/{repo}/git/trees/{sha}?recursive=1")["tree"] if t["type"] == "blob"]
    fetch = lambda p: urllib.request.urlopen(urllib.request.Request(
        f"https://raw.githubusercontent.com/{repo}/{sha}/{urllib.parse.quote(p)}", headers={"User-Agent": "jevaluate"}), timeout=30).read().decode("utf-8", "ignore")
    r = build_manifest(repo, outdir, meta, sha, tree, fetch)
    print(pathlib.Path(outdir) / "manifest.md", r["kept"], "files", r["chars"], "chars")


if __name__ == "__main__":
    a = sys.argv[1:]; commit = None
    if a[:1] == ["--local"]:
        if len(a) != 3: sys.exit(__doc__)
        local_main(a[1], a[2]); sys.exit(0)
    if "--commit" in a:
        i = a.index("--commit"); commit = a[i + 1] if i + 1 < len(a) else None; a = a[:i] + a[i + 2:]
    if len(a) != 2 or (commit is None and "--commit" in sys.argv): sys.exit(__doc__)
    main(a[0], a[1], commit)
