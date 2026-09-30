"""Fetch each eval case's files at its pinned commit and excerpt them into packets (request lines first)."""
import json, os, pathlib, re, sys, urllib.request

HERE = pathlib.Path(__file__).parent
KW = re.compile(r"typesafe|\bjev|api\.|fetch\(|^\s*(import|from)\s|require\(|choice|noul|score|threshold|probab|model|refund|email|review", re.I)
PRI = re.compile(r"fetch\(|post\(|api[./]|typesafe|TypeSafeClient|base_?url|^\s*(import|from)\s|require\(|model", re.I)

def excerpt(text, cap):
    if len(text) <= cap: return text
    if text.count("\n") < 3: return "(head)\n" + text[:cap]
    lines = text.splitlines()
    hits = lambda rx: [i for i, l in enumerate(lines) if rx.search(l)]
    def grow(idx):
        return sorted({k for i in idx for k in (i - 1, i, i + 1) if 0 <= k < len(lines)})
    order, seen = [], set()
    pri_hits = hits(PRI)
    # groups: PRI lines, then their neighbors, then KW lines with neighbors; each in file order, no duplicates
    for group in (pri_hits, grow(pri_hits), grow(hits(KW))):
        for i in group:
            if i not in seen:
                seen.add(i); order.append(i)
    out, n = [], 0
    for i in order:
        s = f"{i + 1}: {lines[i][:200]}"
        if n + len(s) > cap: out.append("[... cut at cap]"); break
        out.append(s); n += len(s) + 1
    return "(keyword lines, numbered)\n" + "\n".join(out)

def fetch(src, path):
    if src["kind"] == "github": url = f"https://raw.githubusercontent.com/{src['repo']}/{src['commit']}/{path}"
    elif src["kind"] == "hf": url = f"https://huggingface.co/{src['repo']}/resolve/{src['commit']}/{path}"
    elif src["kind"] == "local":
        p = pathlib.Path(os.path.expanduser(src["dir"])) / path
        return p.read_text(errors="replace") if p.exists() else None
    else: return None
    try:
        with urllib.request.urlopen(url, timeout=30) as r: return r.read().decode("utf-8", "replace")
    except Exception: return None

def build(sources, outdir):
    outdir = pathlib.Path(outdir); outdir.mkdir(parents=True, exist_ok=True); status = {}
    for slug, src in sources.items():
        if src["kind"] == "fixture":
            (outdir / f"{slug}.md").write_text((HERE / src["path"]).read_text()); status[slug] = "ok"; continue
        if src["kind"] == "local" and not pathlib.Path(os.path.expanduser(src["dir"])).exists():
            status[slug] = "skipped: local missing"; continue
        if not src.get("files"): status[slug] = "skipped: no files"; continue
        body = [f"# PROJECT: {src.get('repo', slug)}"]
        for path, cap in src["files"]:
            text = fetch(src, path)
            if text is None: status[slug] = "fetch failed"; break
            body.append(f"\n## FILE: {path}\n" + excerpt(text, cap))
        else:
            (outdir / f"{slug}.md").write_text("\n".join(body)); status[slug] = "ok"
    return status

if __name__ == "__main__":
    out = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / ".work" / "packets"
    for slug, st in build(json.loads((HERE / "sources.json").read_text()), out).items(): print(f"{slug}: {st}")
