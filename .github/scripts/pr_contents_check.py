#!/usr/bin/env python3
"""Check what a pull request adds or changes before it can merge. This repo is public, so a file that was never
meant to be part of the PR (a plan, a handoff, a working note, a path from someone's machine) must not slip in.

Fails when an added or changed file:
  - sits under a top-level docs/ folder, or a folder named plans, handoffs or .superpowers;
  - is a document named like a plan, handoff, scratch, todo, draft or brainstorm;
  - reads like a plan or a private note (a dated Status block, a handoff opener, task checkboxes, a home-folder path);
  - is binary or over 1 MB outside ratings/;
  - starts a top-level folder or file the base branch doesn't have, unless the Scope line names it;
  - is outside the Scope line of the PR description.

Scope line: one line in the PR description, such as `Scope: jev-sources/, README.md`. Each item is a folder
(everything under it) or a file. Widen it by editing the description; the check runs again on every edit.

In CI it reads the PR from GITHUB_EVENT_PATH. By hand:
    python3 .github/scripts/pr_contents_check.py --base origin/main --head HEAD --body "Scope: jev-sources/"
"""
import argparse, json, os, re, subprocess, sys

PLAN_DIR = re.compile(r"^docs(/|$)|(^|/)(plans?|handoffs?|\.superpowers)(/|$)", re.I)
PLAN_NAME = re.compile(r"(^|[-_. ])(plans?|handoffs?|scratch|todo|drafts?|brainstorm\w*|working-notes|session-notes)([-_. ]|$)", re.I)
PLAN_EXT = (".md", ".txt", ".html", ".pdf", ".docx")
MARKERS = re.compile(r"\*\*Status \(\d{4}-\d\d-\d\d\)|Read this before[ ]starting|- \[[ x]\] \*\*Step\b|"
                     r"Obsidian[ ]Vaults|\.claude/pla[n]s|/private/tmp/clau[d]e-|<scratch[p]ad>|/Use[r]s/[^/\s]+/(Documents|Desktop)", re.I)
# Brackets such as [r] keep each marker from matching this file itself, and keep the literal paths out of the
# source, where the pre-push personal-path scan would stop them.
MAX_BYTES = 1000000
SCOPE = re.compile(r"^\s*\**Scope\**:\s*(.+)$", re.I | re.M)


def git(*a):
    return subprocess.run(["git", *a], capture_output=True, check=True).stdout


def plan_like(path):
    if PLAN_DIR.search(path):
        return True
    name = path.rsplit("/", 1)[-1]
    return name.lower().endswith(PLAN_EXT) and bool(PLAN_NAME.search(name.rsplit(".", 1)[0]))


def scope_items(body):
    m = SCOPE.search(body or "")
    if not m:
        return None
    items = [i.strip().strip("`'\"") for i in re.split(r"[,\s]+", m.group(1))]
    return [i.lstrip("./") for i in items if i]


def in_scope(path, items):
    for i in items:
        if path == i.rstrip("/") or path.startswith(i.rstrip("/") + "/"):
            return True
    return False


def problems(base, head, body):
    out = []
    files = [f for f in git("diff", "--name-only", "--diff-filter=AMR", "-z", f"{base}...{head}").decode().split("\0") if f]
    top_before = {p.split("/", 1)[0] for p in git("ls-tree", "-r", "--name-only", "-z", base).decode().split("\0") if p}
    items = scope_items(body)
    if items is None:
        out.append(("", "the PR description has no Scope line, such as `Scope: jev-sources/, README.md`"))
        items = []
    for f in files:
        data = git("show", f"{head}:{f}")
        if plan_like(f):
            out.append((f, "looks like a plan or working note"))
        m = MARKERS.search(data.decode("utf-8", "replace"))
        if m:
            out.append((f, f"reads like a plan or private note (has {m.group(0)!r})"))
        if not f.startswith("ratings/"):
            if len(data) > MAX_BYTES:
                out.append((f, f"is {len(data) // 1000} KB, over the 1 MB limit"))
            elif b"\0" in data[:8000]:
                out.append((f, "is a binary file"))
        if f.split("/", 1)[0] not in top_before and not in_scope(f, [i for i in items if "/" not in i.rstrip("/")]):
            out.append((f, "starts a new top-level folder or file; name it in the Scope line if it is meant"))
        elif items and not in_scope(f, items):
            out.append((f, "is outside the Scope line"))
    return files, out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--base")
    ap.add_argument("--head")
    ap.add_argument("--body")
    a = ap.parse_args(argv)
    base, head, body = a.base, a.head, a.body
    if os.environ.get("GITHUB_EVENT_PATH") and not base:
        pr = json.load(open(os.environ["GITHUB_EVENT_PATH"]))["pull_request"]
        base, head, body = pr["base"]["sha"], pr["head"]["sha"], pr.get("body") or ""
    files, found = problems(base or "origin/main", head or "HEAD", body or "")
    print(f"{len(files)} file(s) added or changed.")
    for f, why in found:
        print(f"::error{' file=' + f if f else ''}::{f or 'PR description'} {why}")
    if found:
        print(f"\n{len(found)} problem(s). Remove what wasn't meant to be in this PR, or widen the Scope line on purpose.")
        return 1
    print("Nothing outside the PR's scope, and nothing that reads like a plan or private note.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
