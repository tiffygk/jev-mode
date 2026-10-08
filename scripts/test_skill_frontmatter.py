"""Every SKILL.md opens with frontmatter GitHub and Claude Code can read: a value holding ": " must be quoted, or
GitHub shows "Error in user YAML" on the page (2026-10-08: jevaluate-eval/SKILL.md's description)."""
import pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent


def frontmatter_problems(text):
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        return ["no frontmatter block"]
    out = []
    for n, line in enumerate(m.group(1).splitlines(), 2):
        key, sep, value = line.partition(":")
        value = value.strip()
        if sep and value and value[0] not in "\"'>|[{" and ": " in value:
            out.append(f"line {n}: {key} holds an unquoted ': '")
    return out


def test_every_skill_frontmatter_is_valid():
    bad = {str(p.relative_to(ROOT)): frontmatter_problems(p.read_text()) for p in ROOT.glob("*/SKILL.md")}
    assert not {k: v for k, v in bad.items() if v}


def test_the_check_catches_an_unquoted_colon():
    assert frontmatter_problems("---\nname: x\ndescription: Use when: a thing\n---\n")
    assert not frontmatter_problems('---\nname: x\ndescription: "Use when: a thing"\n---\n')
