# Phase 2: Batch the rest

For more than 5 images, after `calibrate.md` has produced a calibrated package. Commands run from the run folder; `$S` is this skill's `scripts/` folder. This is a separate process: the batch decoders never learn what the calibration was for.

## 1. Freeze and audit the package
- **Batch decoders receive only the frozen package and their images:** never the goal, the questions, the Jev results, or this conversation.
- **Example decodes vary** in content (different settings, numbers of people, amounts of text), so they teach the level of detail, not a particular content. If the calibration images all look alike, use one example, not two.
- **The audit:** `python $S/audit_package.py questions.json package`. It lists the words from the question sketch and searches every package file for them by stem. Reword or remove each hit. A word the package genuinely needs (a field name like `contact` that is also in a question) can be allowed with `--allow word` and a one-line reason in `brief.md`. Dispatch only once the audit is clean.

## 2. Batch decode
Follow `decode-protocol.md` with the batch model, up to 10 images per decoder, writing to `decodes/batch/`. **Every template field is required:** filled, or explicitly `not_visible` or `unclear`. Run `python $S/validate_decodes.py package/template.json decodes/batch` and send failures back once. Then `python $S/people_words.py decodes/batch`, and fix every hit before quality control.

## 3. Agreement on a sample (Heavy)
- A second blind decoder re-decodes about 10% of the batch, at least 3 images, chosen at random, into `decodes/sample/`.
- `python $S/agreement.py package/template.json decodes/batch decodes/sample --out agreement.md`.
- **The batch is accepted if every field's agreement is 90% or more.** For a field below the bar, either tighten its wording in the brief and re-decode that field across the batch, or mark it `unclear` for the whole set and say so in the report.

## 4. The cascade (Heavy)
Fields flagged unclear, or in disagreement in the sample, are re-decoded by the strongest vision model: one decoder, given the image, the field names, and the same decoder prompt, never the first decoder's reading. Its answer replaces the flagged value, keeping its own certainty.

## 5. Quality control ✋
Show the user:
- **Balance across the set:** `python $S/validate_decodes.py package/template.json decodes/batch --stats` counts each category and boolean value. A value that never appears, or a field that is `not_visible` on most images, is worth a question.
- **A spot check:** the most unusual images (the ones that went `not_visible` or `unclear` most, or whose values are rare in the stats) plus 3 at random, each shown next to its decode.
- **The Jev check across the set:** build states (`python $S/build_state.py package/template.json keep.json decodes/batch --out states`), then `uv run $S/jev_check.py inverted --states states --questions questions.json` to see the cost, and `--yes --out jev-check.md` to run it. The inverted request puts each sketch question in the state and sends each image's state as a question. It also runs the standard request on 3 rows and reports the largest difference, since the inverted request needs a check on each new dataset. Skip without a key, and say so.

Then write `report.md` (see `SKILL.md`).
