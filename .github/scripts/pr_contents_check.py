#!/usr/bin/env python3
"""Check what a pull request adds or changes before it can merge. This repo is public, so a file that was never
meant to be part of the PR (a plan, a handoff, a working note, a path from someone's machine) must not slip in.

Every commit in the PR is checked, not only the final result: with merge commits, a file added in one commit and
deleted in a later one still lands in the public history. Fails when a file added or changed in any commit:
  - sits under a top-level docs/ folder, or a folder named plans, handoffs, audits or .superpowers;
  - is a document named like a plan, handoff, scratch, todo, draft, brainstorm, audit, findings or run log;
  - reads like a plan or a private note (a dated Status block, a handoff opener, task checkboxes, a home-folder path);
  - is over 1 MB outside ratings/, or binary and not an image;
  - starts a top-level folder or file the base branch doesn't have, unless the Scope line names it;
  - is outside the Scope line of the PR description;
  - is a workflow other than pr-contents.yml that uses the name pr-contents: a job by that name could report a
    pass under the required check's name.
Also fails when a commit message, the PR title or the description reads like a plan or private note.

Scope line: one line in the PR description, such as `Scope: jev-sources/, README.md`. Each item is a folder
(everything under it) or a file. Widen it by editing the description; the check runs again on every edit.

In CI it runs main's copy of this file (pull_request_target), so a PR can't switch it off by editing it, and it
reads the PR from GITHUB_EVENT_PATH. By hand:
    python3 .github/scripts/pr_contents_check.py --base origin/main --head HEAD --body "Scope: jev-sources/"
"""
import argparse, json, os, re, subprocess, sys

PLAN_DIR = re.compile(r"^docs(/|$)|(^|/)(plans?|handoffs?|audits|\.superpowers)(/|$)", re.I)
PLAN_NAME = re.compile(r"(^|[-_. ])(plans?|handoffs?|scratch|todo|drafts?|brainstorm\w*|working-notes|session-notes|audits?|findings|run-log)([-_. ]|$)", re.I)
PLAN_EXT = (".md", ".txt", ".html", ".pdf", ".docx")
MARKERS = re.compile(r"\*\*Status \(\d{4}-\d\d-\d\d\)|Read this before[ ]starting|- \[[ x]\] \*\*Step\b|"
                     r"Obsidian[ ]Vaults|\.claude/pla[n]s|/tmp/clau[d]e-|<scratch[p]ad>|/Use[r]s/[^/\s]+/", re.I)
# Brackets such as [r] keep each marker from matching this file itself, and keep the literal paths out of the
# source, where the pre-push personal-path scan would stop them.
MAX_BYTES = 1000000
OWN_WORKFLOW = ".github/workflows/pr-contents.yml"


def borrows_check_name(path, data):
    """True when a workflow other than the check's own spells out pr-contents, even split by an expression
    such as pr-${{ 'contents' }}: a job by that name could report a pass under the required check's name."""
    if not path.startswith(".github/workflows/") or path == OWN_WORKFLOW:
        return False
    flat = re.sub(r"[^a-z0-9]", "", data.decode("utf-8", "replace").lower())
    return "prcontents" in flat


IMAGES = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico")
SCOPE = re.compile(r"^[ \t]*\**Scope\**:[ \t]*(.*)$", re.I | re.M)


def git(*a):
    return subprocess.run(["git", *a], capture_output=True, check=True).stdout


def plan_like(path):
    if PLAN_DIR.search(path):
        return True
    name = path.rsplit("/", 1)[-1]
    return name.lower().endswith(PLAN_EXT) and bool(PLAN_NAME.search(name.rsplit(".", 1)[0]))


def scope_items(body):
    m = SCOPE.search(body or "")
    if not m or not m.group(1).strip():
        return None
    items = [i.strip().strip("`'\"") for i in re.split(r"[,\s]+", m.group(1))]
    return [i[2:] if i.startswith("./") else i for i in items if i]


def in_scope(path, items):
    for i in items:
        if path == i.rstrip("/") or path.startswith(i.rstrip("/") + "/"):
            return True
    return False


MAX_BLOBS = 20000


def raw_entries(*a):
    """(mode, blob sha, path) for each added, modified or type-changed file in a `git ... --raw -z` listing."""
    toks = git(*a).split(b"\0")
    out, i = [], 0
    while i + 1 < len(toks):
        meta, path = toks[i], toks[i + 1]
        i += 2
        if not meta.startswith(b":"):
            continue
        parts = meta[1:].split()
        out.append((parts[1].decode(), parts[3].decode(), path.decode("utf-8", "surrogateescape")))
    return out


def blobs(shas):
    """{sha: bytes} read through one `git cat-file --batch` process."""
    shas = list(dict.fromkeys(shas))
    r = subprocess.run(["git", "cat-file", "--batch"], input="".join(s + "\n" for s in shas).encode(),
                       capture_output=True, check=True).stdout
    out, pos = {}, 0
    for sha in shas:
        nl = r.index(b"\n", pos)
        head = r[pos:nl].split()
        size = int(head[2])
        out[sha] = r[nl + 1:nl + 1 + size]
        pos = nl + 1 + size + 1
    return out


def text_of(data):
    """The text to search: as UTF-8, and again with NUL bytes dropped, so UTF-16 text can't hide a marker."""
    return data.decode("utf-8", "replace") + "\n" + data.replace(b"\0", b"").decode("utf-8", "replace")


def problems(base, head, body):
    out = []
    diff = ["--raw", "--no-abbrev", "-z", "--no-renames", "--diff-filter=AMT"]
    final = raw_entries("diff", *diff, f"{base}...{head}")
    files = {f for _, _, f in final}
    top_before = {p.split("/", 1)[0] for p in git("ls-tree", "-r", "--name-only", "-z", base).decode("utf-8", "surrogateescape").split("\0") if p}
    commits = [c for c in git("rev-list", f"{base}..{head}").decode().split() if c]
    # Every version of every file any commit added or changed (merge commits too: -m), plus the final one.
    versions = [(head, m, b, f) for m, b, f in final]
    for c in commits:
        versions += [(c, m, b, f) for m, b, f in raw_entries("diff-tree", "-r", "-m", "--no-commit-id", *diff, c)]
    items = scope_items(body)
    if items is None:
        out.append(("", "the PR description has no Scope line, such as `Scope: jev-sources/, README.md`"))
        items = []
    m = MARKERS.search(body or "")
    if m:
        out.append(("", f"title or description reads like a plan or private note (has {m.group(0)!r})"))
    for c in commits:
        m = MARKERS.search(text_of(git("log", "-1", "--format=%B", c)))
        if m:
            out.append(("", f"commit {c[:7]}'s message reads like a plan or private note (has {m.group(0)!r})"))
    content = [b for _, mode, b, _ in versions if mode != "160000"]
    if len(set(content)) > MAX_BLOBS:
        out.append(("", f"has {len(set(content))} file versions, more than the {MAX_BLOBS} this check reads; split the PR"))
        return files, out
    data_of = blobs(content)
    seen_path, seen_blob = set(), set()
    for c, mode, blob, f in versions:
        where = "" if f in files else f" (in commit {c[:7]}, removed later; merged history keeps it)"
        if f not in seen_path:
            seen_path.add(f)
            if plan_like(f):
                out.append((f, "looks like a plan or working note" + where))
            if f.split("/", 1)[0] not in top_before and not in_scope(f, [i for i in items if "/" not in i.rstrip("/")]):
                out.append((f, "starts a new top-level folder or file; name it in the Scope line if it is meant" + where))
            elif items and not in_scope(f, items):
                out.append((f, "is outside the Scope line" + where))
        if mode == "160000":
            out.append((f, "adds a git submodule, which this check can't read" + where))
            continue
        if blob in seen_blob:
            continue
        seen_blob.add(blob)
        data = data_of[blob]
        m = MARKERS.search(text_of(data))
        if m:
            out.append((f, f"reads like a plan or private note (has {m.group(0)!r})" + where))
        if borrows_check_name(f, data):
            out.append((f, "uses the name pr-contents, which only the check's own workflow may use" + where))
        if not f.startswith("ratings/"):
            if len(data) > MAX_BYTES:
                out.append((f, f"is {len(data) // 1000} KB, over the 1 MB limit" + where))
            elif b"\0" in data[:8000] and not f.lower().endswith(IMAGES):
                out.append((f, "is a binary file" + where))
    return files, out


def annotation(text):
    """GitHub's escaping for workflow-command text, so a file name can't start a command of its own."""
    return text.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--base")
    ap.add_argument("--head")
    ap.add_argument("--body")
    a = ap.parse_args(argv)
    base, head, body = a.base, a.head, a.body
    if os.environ.get("GITHUB_EVENT_PATH") and not base:
        pr = json.load(open(os.environ["GITHUB_EVENT_PATH"]))["pull_request"]
        base, head = pr["base"]["sha"], pr["head"]["sha"]
        body = (pr.get("title") or "") + "\n" + (pr.get("body") or "")
    files, found = problems(base or "origin/main", head or "HEAD", body or "")
    print(f"{len(files)} file(s) added or changed.")
    for f, why in found:
        f = annotation(f.encode("utf-8", "surrogateescape").decode("utf-8", "replace"))
        print(f"::error{' file=' + f if f else ''}::{annotation(f or 'PR description')} {annotation(why)}")
    if found:
        print(f"\n{len(found)} problem(s). Remove what wasn't meant to be in this PR, or widen the Scope line on purpose.")
        return 1
    print("Nothing outside the PR's scope, and nothing that reads like a plan or private note.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
