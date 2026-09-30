# Changing the rubric

1. **Capture the ruling:** name what is decided, give a plain-words example and your default, and record the ruling in the rulings log (location per your overlay, or the ledger) the same turn.
2. **Write the rule:** a one-sentence meaning and an invented example for every value, sorted correctly. List the gray areas before writing a new definition and get a ruling on each. Examples must not resemble eval cases; `lint_materials.py` refuses eval-case names.
3. **Split by stakes:** a rule whose test or penalty changes with stakes gets one facts-table row per level (`low`, `high`, `very high`, or a pair such as `high or low`), each saying what a no does there. `step.py` serves only the rows for the levels a project's decisions have; a new label must map in `step.ROW_LEVELS`, which a test checks.
4. **Enforce it:** add or update the rule's row in `jevaluate/enforcement.md`: the function that refuses a wrong answer (`library.py check` or `step.py`), with a test, or "judgment" and why no script can check it. Ask raters only for what they observe; if a value follows from other answers, derive it in `library.py add` instead of asking.
5. **Diagrams:** mermaid, short labels, rendered and looked at before review.
6. **Version:** bump the date in `rubric.md`'s title.
7. **Test:** run `jevaluate-eval`: the materials check, then the quiz, then the eval. Fix wording only from tuning misses.
8. **Freeze:** after the owner approves, tag the version (`git tag rubric-<date>-frozen`). This step and step 7's tuning-only rule are judgment, recorded in the ledger.
