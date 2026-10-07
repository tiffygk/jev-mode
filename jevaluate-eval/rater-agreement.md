# Rater agreement

Instrument 4. It answers two questions about a second rater, such as a different model, on real projects:

1. **Consistency:** do the two raters read the rubric the same way? The measure is agreement.
2. **Accuracy:** is either rater right? The measure is an answer key the owner labels.

Agreement alone never shows accuracy. Two raters reading the same rubric can agree and both be wrong.

Script: `rater_agreement/rater_agreement.py` (its `--help` lists the commands). It reads the library that `JEVALUATE_LIBRARY` points to.

## Steps

1. **Name the tuning sample before any numbers.** Any project whose disagreements fed a rubric or brief change is in it. Agreement there is partly built in, since the wording was changed to settle those projects. Pass the sample as `--tuning`.
2. **Agreement:** `rater_agreement.py agreement --tuning <slugs> --out agreement.md`. Lead every report with the held-out projects. Give raw agreement and Cohen's kappa for each field: raw agreement flatters a field where nearly every project has the same answer, and kappa discounts the agreement chance alone would give. Kappa is n.a. when a field has one value everywhere.
3. **A rerun of the tuning sample is a tuning check, not a result.** If a rater re-rates the sample after a wording change and matches the ruled answer, that shows the wording says what was ruled. Report it that way, or not at all.
4. **Answer key.** Get the facts with `rater_agreement.py facts --tuning <slugs> --out facts.json`, which covers held-out projects only. Then draw with `rater_agreement.py draw --facts facts.json --split 3 --agreed 4 --seed <N> --out draw.json`, and record the seed. Some notes on the draw:
   - Draw agreed facts as well as split ones: they're the only way to catch both raters wrong together.
   - The owner's own open questions (a routing split, say) can join the key; pass their projects as `--skip` so the draw doesn't repeat them.
   - Seal the raters' answers in a private file before the owner sees the key.
5. **Build the owner's page.** Each item is one fact on one project, with:
   - what the program does, in plain words: the behavior, never code, since the owner may not read code;
   - the rubric rule, quoted exactly;
   - the question, with "can't tell" allowed.

   Say once, at the top of the page, how the descriptions were checked. Never add a per-item line saying why to trust a description or which rater said what: per-item notes read as an argument for an answer and hint at which facts the raters agreed on. Order the items so split and agreed facts can't be told apart.
6. **Score:** `rater_agreement.py score --key <sealed raters' answers> --owner <copied answers>`. "Can't tell" is counted apart, never as a match. Only now show the owner the raters' answers, item by item, as the existing eval rules require.
7. **Report what each number can claim.** Agreement claims consistency. "Correct" needs the key, and only on the key's items.

## Checked risks

Each row is a risk to this comparison's fairness: whether it holds, and how that was checked. Check a new risk the same way before raising it.

| Risk | Holds? | How it was checked |
|---|---|---|
| The previous rating anchors a rater's answers | Partly | Each rater writes its facts and scores before it sees the project's previous rating, but picks the verdict after, so the verdict can lean toward the old one. Planned work on this skill aims to remove this bias by keeping the rater model blind to previous ratings until after its overall project verdict is recorded and locked. |
| Tuning-sample agreement reported as evidence | Yes, it happened once (2026-10-06) | Now `agreement` reports the sample apart and second. |
| Whoever settles a dispute has read both ratings | Yes, it happened once (2026-10-06) | Disputes now go to a fresh reviewer as a blind packet (`jevaluate-harness/scripts/dispute_packet.py`, round step 6). |
| A fact parser misses facts, narrowing the draw | Yes, it happened once (2026-10-06) | An ad hoc pattern skipped facts written with a different dash or in bold: it found 182 shared facts where the library's parser finds 267. `rater_agreement.py` now uses the library's own `fact_rows`. A key drawn before this fix is valid item by item, but its pool was narrower. |
| Per-item trust notes on the owner's page lean the answer | Yes, it happened once (2026-10-06) | Step 5: one method note per page, none per item. |
