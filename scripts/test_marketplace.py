"""Every skill folder in the repo is its own plugin in the marketplace, so each one can be installed by name; the jev-mode plugin holds them all."""
import json, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
BUNDLE = "jev-mode"


def load():
    market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
    skills = {d.name for d in ROOT.iterdir() if (d / "SKILL.md").is_file()}
    return {p["name"]: p for p in market["plugins"]}, skills


def test_every_skill_folder_is_its_own_plugin():
    plugins, skills = load()
    singles = {n: p.get("skills", []) for n, p in plugins.items() if n != BUNDLE}
    assert set(singles) == skills, f"skills with no plugin: {sorted(skills - set(singles))}, plugins with no skill: {sorted(set(singles) - skills)}"
    assert all(singles[s] == [f"./{s}"] for s in skills), singles


def test_the_bundle_holds_every_skill_and_the_jev_sources_hooks():
    plugins, skills = load()
    bundle = plugins[BUNDLE]
    assert sorted(bundle["skills"]) == sorted(f"./{s}" for s in skills)
    assert bundle.get("hooks") == plugins["jev-sources"].get("hooks")


def test_the_jevaluate_plugin_installs_the_publish_command():
    plugins, _ = load()
    assert plugins["jevaluate"]["skills"] == ["./jevaluate"]
    head = (ROOT / "jevaluate" / "SKILL.md").read_text().split("---")[1]
    assert "\nname: jevaluate-publish\n" in head
