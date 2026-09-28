# Jev Mode

Claude Code skills for building with Jev, TypeSafe's System One model.

| Skill | What it does | Status |
|---|---|---|
| [Jevaluate](jevaluate/) | Reads a Jev project's code and rates how well it uses Jev, with provenance for every finding | Available |
| [Jev Lens](jev-lens/) | Turns images into a neutral JSON state that Jev can read, one shared schema across the set | Available |

Install a skill by copying its folder into `~/.claude/skills/`:

```
git clone https://github.com/tiffygk/jev-mode
cp -r jev-mode/jevaluate ~/.claude/skills/
cp -r jev-mode/jev-lens ~/.claude/skills/
```

Not affiliated with TypeSafe. Licensed under [PolyForm Noncommercial 1.0.0](LICENSE.md): free for personal and noncommercial use, with credit. Company or paid use needs a commercial license: [open an issue](https://github.com/tiffygk/jev-mode/issues).
