"""Skill shape for Claude Code and Codex. Anthropic's limits (skill_check.py encodes them) plus a tighter
description cap: Codex shortens descriptions when many skills are installed, so the trigger words come first."""
import os, re
SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def parts():
    text = open(os.path.join(SKILL_DIR, "SKILL.md"), encoding="utf-8").read()
    m = re.match(r"---\n(.*?)\n---\n(.*)", text, re.S)
    front, body = m.group(1), m.group(2)
    fields = dict(re.findall(r"^(\w+): (.*)$", front, re.M))
    return fields, body


def test_body_under_500_lines():
    assert len(parts()[1].splitlines()) <= 500


def test_name_shape():
    name = parts()[0]["name"]
    assert re.fullmatch(r"[a-z0-9-]{1,64}", name)


def test_description_says_what_then_when():
    d = parts()[0]["description"]
    assert len(d) <= 300
    assert not d.startswith("Use when")
    for word in ("Jev", "Box", "Noul"):
        assert word in d[:100], word
    assert not re.search(r"\b(I|me|my|we|our|you|your)\b", d)


def test_linked_files_exist_one_level_deep():
    body = parts()[1]
    for link in re.findall(r"\]\(([^)#]+\.md)\)", body):
        path = os.path.join(SKILL_DIR, link)
        assert os.path.exists(path), link
        assert not re.search(r"\]\([^)#]+\.md\)", open(path, encoding="utf-8").read()), link


def test_readme_at_most_890_words():
    # The repo's README rule is 750 words; this README may run to 890 (CLAUDE.md, "Writing in this repo").
    text = open(os.path.join(SKILL_DIR, "README.md"), encoding="utf-8").read()
    assert len(re.sub(r"<[^>]*>", "", text).split()) <= 890  # HTML tags don't count, as in the README guide
