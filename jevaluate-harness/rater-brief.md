This is your only task. Return your report as text; never push, commit, or run `library.py add`.

Rate PROJECT with the jevaluate skill: read ~/.claude/skills/jevaluate/SKILL.md, then read.md, and follow read.md. Don't open `rubric.md` or earlier ratings directly; `step.py` serves them, one section at a time. Work only in ROUND_DIR/SLUG/ (its manifest.md is already there).
- Depth: SCOPE. "full" means every manifest file that could change a fact, read in full. "scoped: <files>" means only those files, with `depth: extract` and every other file `skipped: scoped` in Coverage.
- Front matter: rater: claude-sonnet-5-5, effort: medium, via: VIA, rubric: <the date in jevaluate/rubric.md's title>, and a `why:` line of 20 words at most.
- `step.py full` serves the previous rating PREV after the facts are written; use it only for the "Compared with" sentence.
- Nothing said privately goes in the rating.
- Never read `files_full/` in your folder: it holds uncapped copies for the code checks. Read `files/` only.
- Write every path out in full in each command, never as a shell variable: the transcript scan can't follow a variable, and a flagged read sends the rating back.
- Save the rating as ROUND_DIR/SLUG/rating.md and run `python3 ~/.claude/skills/jevaluate/scripts/library.py check ROUND_DIR/SLUG/rating.md --evidence ROUND_DIR/SLUG` until it passes.
Report: verdict and verdict_1_code, project_type, F0 line, stakes per decision, facts that changed from PREV, and any rubric line you found ambiguous (quote it).
