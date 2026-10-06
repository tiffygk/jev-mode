This is your only task. Return your report as text; never push, commit, or run `library.py add`.

Rate PROJECT with the jevaluate skill: read JEVALUATE/SKILL.md, then read.md, and follow read.md. Don't open `rubric.md` or earlier ratings directly; `step.py` serves them, one section at a time. Work only in ROUND_DIR/SLUG/ (its manifest.md is already there).
- Depth: SCOPE. "full" means every manifest file that could change a fact, read in full. "scoped: <files>" means only those files, with `depth: extract` and every other file `skipped: scoped` in Coverage.
- Mark a file `read` in Coverage only if you read it in full; a file you only grepped or read the head of is not `read`. Read each section `step.py` serves in full, never through `head` or `tail`.
- Read every manifest file in scope before you write the Facts. Once `step.py full` has shown you the previous rating, never change a fact, a score or the verdict; if you find a mistake after that point, say so in your report instead of editing.
- Front matter: rater: RATER, effort: medium, via: VIA, rubric: RUBRIC, and a `why:` line of 20 words at most.
- `step.py full` serves the previous rating PREV after the facts are written; use it only for the "Compared with" sentence.
- Nothing said privately goes in the rating.
- Files made while gathering evidence (captured responses, summaries and timings in ROUND_DIR/SLUG outside `files/`) are evidence about the project, never its own work or measurements.
- Never read `files_full/` in your folder: it holds uncapped copies for the code checks. Read `files/` only.
- Write every path out in full in each command, never as a shell variable: the transcript scan can't follow a variable, and a flagged read sends the rating back.
- Create rating.md from the read.md template before your first `step.py next`.
- Save the rating as ROUND_DIR/SLUG/rating.md and run `python3 JEVALUATE/scripts/library.py check ROUND_DIR/SLUG/rating.md --evidence ROUND_DIR/SLUG` until it passes.
Report: verdict and verdict_1_code, project_type, F0 line, stakes per decision, facts that changed from PREV, and any rubric line you found ambiguous (quote it).
