"""Every SKILL.md opens with frontmatter that parses as YAML, with a name and a description; otherwise GitHub shows
"Error in user YAML" on the page (2026-10-08: jevaluate-eval/SKILL.md's unquoted ": ")."""
import pathlib, re
import pytest

yaml = pytest.importorskip("yaml")
ROOT = pathlib.Path(__file__).resolve().parent.parent


def frontmatter_problem(text):
    m = re.match(r"---\n(.*?)\n---\n", text.replace("\r\n", "\n"), re.S)
    if not m:
        return "no frontmatter block"
    try:
        data = yaml.safe_load(m.group(1))
    except yaml.YAMLError as e:
        return f"not valid YAML: {str(e).splitlines()[0]}"
    if not isinstance(data, dict) or not data.get("name") or not data.get("description"):
        return "needs a name and a description"
    return None


def test_every_skill_frontmatter_is_valid():
    bad = {str(p.relative_to(ROOT)): frontmatter_problem(p.read_text()) for p in ROOT.rglob("SKILL.md")
           if ".git" not in p.parts}
    assert not {k: v for k, v in bad.items() if v}


def test_the_check_catches_what_github_rejects():
    assert frontmatter_problem("---\nname: x\ndescription: Use when: a thing\n---\n")
    assert frontmatter_problem("---\nname: x\ndescription: `code` first\n---\n")
    assert not frontmatter_problem('---\nname: x\ndescription: "Use when: a thing"\n---\n')
    assert not frontmatter_problem("---\r\nname: x\r\ndescription: >\r\n  folded: text\r\n---\r\n")
