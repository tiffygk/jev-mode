"""Every skill folder in the repo is its own plugin in the marketplace, so each one can be installed by name."""
import json, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_every_skill_folder_is_its_own_plugin():
    market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
    skills = {d.name for d in ROOT.iterdir() if (d / "SKILL.md").is_file()}
    by_plugin = {p["name"]: p.get("skills", []) for p in market["plugins"]}
    assert set(by_plugin) == skills, f"skills with no plugin: {sorted(skills - set(by_plugin))}, plugins with no skill: {sorted(set(by_plugin) - skills)}"
    assert all(by_plugin[s] == [f"./{s}"] for s in skills), by_plugin
