"""Metadata plus a capped extract of a public GitHub repo, focused on Jev code. No auth needed.

Usage: python3 fetch_repo.py <owner/repo> [--out DIR] [--files N] [--cap 4000] [--also path1,path2]
--also adds named files the ranking missed (a JSON check catalogue, a second source file): matching lines go in the extract, full text in files/.
Writes DIR/meta.json and DIR/extract.md; prints their paths. Raw file fetches don't use the API rate limit.
"""
import json, sys, urllib.request, urllib.parse, argparse, pathlib, re, tempfile

def get(url, raw=False):
    req = urllib.request.Request(url, headers={"User-Agent": "jevaluate"})
    data = urllib.request.urlopen(req, timeout=30).read()
    return data.decode("utf-8", "ignore") if raw else json.loads(data)

ap = argparse.ArgumentParser()
ap.add_argument("repo"); ap.add_argument("--out", default=None, help="output folder (default: a new temp folder)")
ap.add_argument("--files", type=int, default=4); ap.add_argument("--cap", type=int, default=4000)
ap.add_argument("--also", default="", help="comma-separated repo paths to add")
a = ap.parse_args()
out = pathlib.Path(a.out or tempfile.mkdtemp(prefix="jevaluate-")); out.mkdir(parents=True, exist_ok=True)
try:
    meta = get(f"https://api.github.com/repos/{a.repo}")
except Exception as e:
    sys.exit(f"could not fetch {a.repo}: {e}. Check the owner/repo spelling, that it is public, and the GitHub rate limit (60 calls an hour without auth).")
sha = get(f"https://api.github.com/repos/{a.repo}/commits/{meta['default_branch']}")["sha"]
m = {k: meta.get(k) for k in ("full_name", "description", "stargazers_count", "created_at", "pushed_at", "default_branch")}
m["license"] = (meta.get("license") or {}).get("spdx_id"); m["commit"] = sha; m["owner"] = meta["owner"]["login"]
(out / "meta.json").write_text(json.dumps(m, indent=2))
tree = [t["path"] for t in get(f"https://api.github.com/repos/{a.repo}/git/trees/{sha}?recursive=1")["tree"] if t["type"] == "blob"]
raw = lambda p: get(f"https://raw.githubusercontent.com/{a.repo}/{sha}/{urllib.parse.quote(p)}", raw=True)
KW = re.compile(r"system_one|systemOne|typesafe|Noul|Choice\(|Score\(|jev-|[\"']?type[\"']?\s*:\s*[\"'](noul|choice|score)[\"']", re.I)
code = [p for p in tree if re.search(r"\.(py|ts|tsx|js|mjs|php|go|rb|rs|java|kt|md|json|toml|ya?ml)$", p) and not re.search(r"(^|/)(tests?|node_modules|dist|\.github)/|lock", p)]
def prio(p):  # likeliest Jev source first: source dirs and Jev-ish names; corpora, examples and docs last
    s = 0
    if re.search(r"(^|/)(src|lib|php|js|python|py|skills|hooks|app|agent|server)/", p): s -= 2
    if re.search(r"jev|typesafe|system.?one|client|question|check|query|judge|gate", p, re.I): s -= 2
    if re.search(r"(^|/)(corpus|examples?|docs?|fixtures?|samples?|data)/", p): s += 3
    return (s, len(p))
code.sort(key=prio)
scored = []
for p in code[:80]:  # sample files; rank by Jev-keyword density
    try: t = raw(p)
    except Exception: continue
    n = len(KW.findall(t))
    if n and not p.lower().startswith("readme"):
        is_code = not re.search(r"\.(json|md|toml|ya?ml)$", p)
        scored.append((is_code, n, p, t))  # code files rank above data and docs
scored.sort(reverse=True)
scored = scored[: a.files]
for p in [x.strip() for x in a.also.split(",") if x.strip()]:
    if any(p == s[2] for s in scored): continue
    try: t = raw(p)
    except Exception as e: print(f"NOTE: --also {p}: fetch failed ({e})"); continue
    scored.append((True, len(KW.findall(t)), p, t))
parts = [f"# {a.repo} @ {sha[:10]}\n\n## Files ({len(tree)}, first 150)\n" + "\n".join(tree[:150])]
for p in [p for p in tree if p.lower() in ("readme.md", "readme")][:1]:
    parts.append("\n## README\n" + re.sub(r"(?m)^#", "###", raw(p)[:a.cap]))
for is_code, n, p, t in scored:
    lines = [l for l in t.splitlines() if KW.search(l) or re.search(r"(THRESH|CONF|instructions|criteria|state\s*=)", l)]
    parts.append(f"\n## {p} ({n} Jev keywords)\n" + "\n".join(lines)[: a.cap])
(out / "extract.md").write_text("\n".join(parts))
full = out / "files"; full.mkdir(exist_ok=True)
for is_code, n, p, t in scored:  # full text, for jev_callsites.py
    (full / p.replace("/", "__")).write_text(t)
print(out / "meta.json"); print(out / "extract.md")
if len(tree) > 150: print(f"NOTE: the file list in extract.md shows the first 150 of {len(tree)} files.")
if len(code) > 80: print(f"NOTE: sampled 80 of {len(code)} code files; fetch others by name if the file list shows Jev code elsewhere.")
