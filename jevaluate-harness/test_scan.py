import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from scan_transcripts import scan


def run(tmp_path, name, inp):
    p = tmp_path / "t.jsonl"
    p.write_text(json.dumps({"message": {"content": [{"type": "tool_use", "name": name, "input": inp}]}}) + "\n")
    return scan([str(p)], "r.md")


def bash(tmp_path, cmd): return run(tmp_path, "Bash", {"command": cmd})


def test_flags_rubric_read(tmp_path): assert run(tmp_path, "Read", {"file_path": "/x/jevaluate/rubric.md"})
def test_flags_library_cat(tmp_path): assert bash(tmp_path, "cat ~/.claude/jevaluate-library/projects/o__p/2026-09-28.md")
def test_flags_second_segment_only(tmp_path):
    f = bash(tmp_path, "python3 scripts/step.py next r.md; cat ../rubric.md")
    assert len(f) == 1 and "rubric.md" in f[0]
def test_flags_other_rating(tmp_path): assert bash(tmp_path, "python3 scripts/step.py next scratch.md")
def test_flags_steps_write(tmp_path): assert run(tmp_path, "Write", {"file_path": "/a/r.md.steps.json"})
def test_flags_approval_writes(tmp_path):
    assert run(tmp_path, "Write", {"file_path": "/a/approved_cost.json"})
    assert run(tmp_path, "Write", {"file_path": "/a/routing_revised.json"})
def test_flags_published_ratings(tmp_path): assert bash(tmp_path, "cat ~/Documents/jev-mode/ratings/x.md")
def test_flags_round_pre(tmp_path): assert bash(tmp_path, "cat ~/jevaluate-round2/x.pre-2.md")
def test_flags_rubric_text_import(tmp_path): assert bash(tmp_path, 'python3 -c "import rubric_text"')
def test_flags_grep_f13(tmp_path): assert bash(tmp_path, "grep -r F13 jevaluate/")
def test_flags_redirect_in(tmp_path): assert bash(tmp_path, "python3 scripts/step.py next r.md < ../rubric.md")
def test_flags_redirect_out(tmp_path): assert bash(tmp_path, "python3 scripts/step.py next r.md > r.md.steps.json")
def test_plain_step_not_flagged(tmp_path): assert bash(tmp_path, "python3 scripts/step.py next r.md") == []
def test_write_rating_mentioning_catalog_not_flagged(tmp_path):
    assert run(tmp_path, "Write", {"file_path": "/a/r.md", "content": "see fix-catalog.md"}) == []


def test_flags_command_substitution(tmp_path): assert bash(tmp_path, "python3 scripts/step.py next r.md $(cat ../rubric.md)")
def test_flags_backticks(tmp_path): assert bash(tmp_path, "python3 scripts/step.py next r.md `cat ../rubric.md`")
def test_flags_grep_tool(tmp_path): assert run(tmp_path, "Grep", {"pattern": "F13", "path": "jevaluate/"})
def test_flags_uppercase_rubric(tmp_path): assert run(tmp_path, "Read", {"file_path": "/x/RUBRIC.md"})


# --- Review fix 6 (2026-09-30): files_full/ holds uncapped copies for the code checks; raters never read it ---
def test_flags_files_full_reads(tmp_path):
    assert run(tmp_path, "Read", {"file_path": "/r/SLUG/files_full/bench__report.json"})
    assert bash(tmp_path, "cat /r/SLUG/files_full/bench__report.json")
    assert bash(tmp_path, "grep accuracy /r/SLUG/files_full/bench__report.json")
    assert run(tmp_path, "Grep", {"pattern": "accuracy", "path": "/r/SLUG/files_full"})

def test_reading_the_capped_files_folder_is_not_flagged(tmp_path):
    assert run(tmp_path, "Read", {"file_path": "/r/SLUG/files/bench__report.json"}) == []

def test_rater_brief_says_never_read_files_full():
    brief = (pathlib.Path(__file__).parent / "rater-brief.md").read_text()
    assert "files_full" in brief and "never read" in brief.lower()


# Codex raters: `codex exec --json` logs, one event per line
def codex(tmp_path, item):
    p = tmp_path / "c.jsonl"
    p.write_text(json.dumps({"type": "item.started", "item": item}) + "\n" + json.dumps({"type": "item.completed", "item": item}) + "\n")
    return scan([str(p)], "r.md")

def test_codex_shell_read_flagged_once(tmp_path):
    f = codex(tmp_path, {"type": "command_execution", "command": "/bin/zsh -lc 'cat jevaluate/rubric.md'"})
    assert len(f) == 1 and "rubric.md" in f[0]
def test_codex_double_quoted_wrapper(tmp_path):
    assert codex(tmp_path, {"type": "command_execution", "command": '/bin/zsh -lc "sed -n 1,9p ../ratings/x.md"'})
def test_codex_allowed_step_full_not_flagged(tmp_path):
    assert not codex(tmp_path, {"type": "command_execution", "command": "/bin/zsh -lc 'python3 jevaluate/scripts/step.py full r.md ~/.claude/jevaluate-library/projects/x/y.md'"})
def test_codex_file_change_flagged(tmp_path):
    assert codex(tmp_path, {"type": "file_change", "changes": [{"path": "/a/routing_revised.json", "kind": "add"}]})
def test_codex_mcp_and_web_calls_flagged(tmp_path):
    assert codex(tmp_path, {"type": "mcp_tool_call", "server": "fs", "tool": "read_file", "arguments": {"path": "/x/rubric.md"}})
    assert codex(tmp_path, {"type": "web_search", "query": "jevaluate rubric.md"})

def test_flags_the_unfrozen_test_escape(tmp_path):
    import json
    t = tmp_path / "t.jsonl"
    t.write_text(json.dumps({"type": "item.completed", "item": {"type": "command_execution", "command": "/bin/zsh -lc 'JEVALUATE_TEST_UNFROZEN=1 python3 /x/jevaluate/scripts/step.py next /r/rating.md'"}}) + "\n")
    assert scan([str(t)], "/r/rating.md")
