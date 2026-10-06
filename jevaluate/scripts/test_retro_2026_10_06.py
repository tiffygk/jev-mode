"""Retro fixes (2026-10-06): a cached GitHub freeze confirmation, an F0 refusal that explains itself, and a freeze-tag push check."""
import json, pathlib, subprocess, sys, time
import pytest
HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent.parent / "jevaluate-harness")); sys.path.insert(0, str(HERE.parent.parent / "jevaluate-eval"))
import rubric_text as rt
from test_rubric_lock import frozen_copy, git


# --- the GitHub freeze confirmation is cached on disk for a few minutes; a failure never is ---
def counting(monkeypatch, tags, ok=True):
    calls = []
    def get(path):
        calls.append(path)
        if not ok: raise OSError("offline")
        if path.startswith("git/matching-refs/"): return [{"ref": f"refs/tags/{t}", "object": {"type": "commit", "sha": s}} for t, s in tags.items()]
        if path.startswith("compare/"): return {"status": "ahead", "behind_by": 0}
        raise AssertionError(path)
    monkeypatch.setattr(rt, "_github_get", get); rt.github_check.cache_clear(); return calls

def test_confirmed_freeze_is_reused_from_disk(tmp_path, monkeypatch):
    root = frozen_copy(tmp_path / "r"); tag = rt.newest_tag(root); sha = git(root, "rev-parse", f"{tag}^{{commit}}").stdout.strip()
    monkeypatch.setattr(rt, "GITHUB_CACHE", tmp_path / "cache.json")
    calls = counting(monkeypatch, {tag: sha}); assert rt.github_check(tag, root) == (True, "") and calls
    calls = counting(monkeypatch, {tag: sha}); assert rt.github_check(tag, root) == (True, "") and calls == []   # a new process: no API calls

def test_cache_expires_and_is_keyed_by_commit(tmp_path, monkeypatch):
    root = frozen_copy(tmp_path / "r"); tag = rt.newest_tag(root); sha = git(root, "rev-parse", f"{tag}^{{commit}}").stdout.strip()
    cache = tmp_path / "cache.json"; monkeypatch.setattr(rt, "GITHUB_CACHE", cache)
    cache.write_text(json.dumps({tag: {"sha": sha, "at": time.time() - rt.GITHUB_CACHE_SECONDS - 5}}))
    calls = counting(monkeypatch, {tag: sha}); rt.github_check(tag, root); assert calls                     # expired: asks GitHub
    cache.write_text(json.dumps({tag: {"sha": "0" * 40, "at": time.time()}}))
    calls = counting(monkeypatch, {tag: sha}); rt.github_check(tag, root); assert calls                     # another commit: asks GitHub

def test_failure_is_never_cached(tmp_path, monkeypatch):
    root = frozen_copy(tmp_path / "r"); tag = rt.newest_tag(root)
    cache = tmp_path / "cache.json"; monkeypatch.setattr(rt, "GITHUB_CACHE", cache)
    counting(monkeypatch, {}, ok=False); assert not rt.github_check(tag, root)[0]
    assert not cache.exists() or tag not in json.loads(cache.read_text())


# --- an F0 refusal names why the cited file can't show a hosted call, and suggests lines that use the SDK ---
def test_f0_refusal_names_the_wrapper_package(tmp_path):
    import library
    ev = tmp_path / "ev"; (ev / "files").mkdir(parents=True)
    (ev / "files" / "src__provider.ts").write_text('import { ask } from "@acme/jev-wrapper";\n\nexport async function run(state) {\n  return await ask({ state }, { transport });\n}\n')
    (ev / "files" / "src__server.ts").write_text('import { noul } from "@typesafe-ai/sdk";\nconst { version } = createRequire(import.meta.url)("../package.json");\nconst q = noul("Is it urgent?");\n')
    err = []
    library.check_f0("- F0 Calls hosted Jev -- yes. Sends state (`src/provider.ts:4`).", "yes", ev, err)
    msg = " ".join(err)
    assert "@acme/jev-wrapper" in msg and "no TypeSafe" in msg
    assert "src/server.ts:3" in msg and "src/server.ts:2" not in msg


# --- a freeze tag is pushed only for a commit on GitHub's main whose rubric version matches the tag ---
def test_freeze_tag_push_check(tmp_path):
    import freeze_tag_check as ftc
    root = frozen_copy(tmp_path / "r"); head = git(root, "rev-parse", "HEAD").stdout.strip()
    v = rt.version((root / "jevaluate/rubric.md").read_text())
    assert ftc.problems(root, f"rubric-{v}-frozen", head, head) == []
    assert any("version" in p for p in ftc.problems(root, "rubric-2099-01-01-frozen", head, head))
    md = root / "jevaluate/rubric.md"; md.write_text(md.read_text() + "\nmore\n"); git(root, "-c", "user.email=a@b", "-c", "user.name=t", "commit", "-qam", "later")
    later = git(root, "rev-parse", "HEAD").stdout.strip()
    assert any("main" in p for p in ftc.problems(root, f"rubric-{v}-frozen", later, head))       # not in main's history yet
    assert ftc.problems(root, "v1.0", later, head) == []                                         # other tags are not this check's business


# --- the lint flags a long sentence added since the newest freeze, not ones already frozen ---
def test_long_new_sentences():
    import lint_materials as lm
    old = "Short rule. " + " ".join(["word"] * 40) + "."
    new = old + " Another short one. " + " ".join(["fresh"] * 36) + "."
    hits = lm.long_new_sentences(new, old)
    assert len(hits) == 1 and hits[0].startswith("fresh")
