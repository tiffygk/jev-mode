"""Refuse pushing a freeze tag that would freeze the wrong thing (2026-10-06: a tag command was nearly run before its PR merged,
and GitHub forbids moving or deleting a freeze tag, so a wrong one is permanent).

A rubric-<version>-frozen tag passes only when its commit is in GitHub main's history and that commit's rubric.md title carries
<version>. Run from git's pre-push hook: it reads the pushed refs on stdin and exits 1 with one line per problem.
Usage: freeze_tag_check.py <remote name> <remote url>   (stdin: <local ref> <local sha> <remote ref> <remote sha> per line)
"""
import pathlib, re, subprocess, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "jevaluate" / "scripts"))
import rubric_text as rt

TAG = re.compile(r"^rubric-(.+)-frozen$")


def _git(root, *a):
    r = rt._git(root, *a); return r.returncode, r.stdout.decode(errors="replace").strip()


def problems(root, tag, commit, main_sha):
    """[] when tag isn't a freeze tag, or when commit is in main_sha's history and its rubric.md version matches the tag."""
    m = TAG.match(tag)
    if not m: return []
    out = []
    rc, text = _git(root, "show", f"{commit}:jevaluate/rubric.md")
    have = rt.version(text) if rc == 0 else None
    if have != m.group(1):
        out.append(f"{tag}: the rubric at {commit[:7]} is version {have or 'missing'}, not {m.group(1)}; tag the commit that merged that version")
    if not main_sha or _git(root, "cat-file", "-e", f"{main_sha}^{{commit}}")[0] != 0:
        out.append(f"{tag}: GitHub's main isn't here yet; run bash ~/.claude/hooks/jev-mode-sync.sh, then tag the merge commit")
    elif _git(root, "merge-base", "--is-ancestor", commit, main_sha)[0] != 0:
        out.append(f"{tag}: {commit[:7]} isn't in GitHub main's history; merge the PR first, sync, then tag its merge commit")
    return out


def main():
    root = pathlib.Path.cwd(); url = sys.argv[2] if len(sys.argv) > 2 else (sys.argv[1] if len(sys.argv) > 1 else "origin")
    pushed = [l.split() for l in sys.stdin if l.strip()]
    tags = [(ref.rsplit("/", 1)[-1], sha) for ref, sha, *_ in pushed if ref.startswith("refs/tags/") and TAG.match(ref.rsplit("/", 1)[-1]) and set(sha) != {"0"}]
    if not tags: return 0
    rc, ls = _git(root, "ls-remote", url, "refs/heads/main")
    main_sha = ls.split()[0] if rc == 0 and ls else ""
    bad = [p for tag, sha in tags for p in problems(root, tag, _git(root, "rev-parse", f"{sha}^{{commit}}")[1], main_sha)]
    for p in bad: print("freeze tag refused: " + p, file=sys.stderr)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
