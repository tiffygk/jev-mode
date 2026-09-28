# Phase 1: Calibrate

The whole process, end to end, on 1 to 3 images. With 5 images or fewer this is the whole job: run it on every image. ✋ marks a stop where the user rules before you go on. Commands run from the run folder `<name>-jev-lens/` next to the images; `$S` is this skill's `scripts/` folder.

## 1. Intake ✋
Ask, in one message:
- **The goal:** what decision Jev will make, and for whom.
- **Their questions,** if they have any.
- **The images,** and whether they are photos or illustrations.
- **Anything sensitive:** private people, children, documents, locations. Say plainly that the images stay on this machine and with Claude, and that the Jev check sends only the text state to TypeSafe's API.
- **The decoder model:** ask whether to use the strongest vision model for everything, or the strongest for calibration and a cheaper one for the batch, with the cost difference (see `SKILL.md`, Cost).

If they have no questions, offer 2 or 3 framings of the goal, each with its pros and cons, and let them pick.

Then clean the images: `uv run $S/prepare_images.py <images> --out <name>-jev-lens`. Pick the 1 to 3 calibration images: the ones that best cover the variety in the set.

Record the intake answers in `intake-notes.md` at the run folder's root, **never inside `package/`**: everything in `package/` may reach a decoder.

**Keep the user's hypothesis out of everything that follows.** If they said what they think the answer is, it shapes the brief's dimensions only (step 2) and never its wording, and it never reaches a decoder.

## 2. Decode brief ✋
Write `package/brief.md`: the dimensions the decoder must cover, derived from the goal, and nothing else. No goal, no user wording, no notes on why a dimension was chosen (those go in `intake-notes.md`).
- **Name dimensions, never hypotheses.** Word each one so it could support any answer: "describe physical contact between people, including where there is none," not "look for signs of romance."
- If the user drafted a leading brief, rewrite it into neutral dimensions and show both versions side by side, with what changed and why.
- Add goal-specific fields to a copy of `templates/base.json` as `package/template.json` (category fields where the answer depends on a small set of values).
- Offer the choice with pros and cons: **a broad brief** (catches what nobody thought of; longer decodes, more to review) or **a focused one** (shorter, cheaper; can miss the detail that matters).

## 3. Blind decode
Follow `decode-protocol.md`. Heavy: two decoders (A and B) on each calibration image, in parallel. Light: one. Validate with `validate_decodes.py`.

## 4. Review ✋
Show the inventory (the merged decode) and, in Heavy, the agreement table from `agreement.py`. Ask about:
- **Coverage:** what did they notice that's missing?
- **Accuracy:** any misreadings?
- **Bias:** anything leading, or recorded for one side only?
- **Each uncertain label,** one at a time: every field that is unclear or that the decoders disagree on. Example: "A read 'RLHF2', B read 'RLHFZ'. What is it, and is it relevant?" Their options:
  - **say what it is:** recorded with `"certainty": "clear"` and `"source": "user: <what they said>"`;
  - **keep it unclear;**
  - **drop it as irrelevant:** it goes on the left-out list with the reason.

Before showing the inventory, run `python $S/people_words.py inventory` and fix every hit; show the user the count. A pattern that recurs across images becomes a rule in the brief. A fact true of one image stays with that image. Save the result as `inventory/<image>.json`.

## 5. Relevance and balance ✋
- Mark every template field keep or drop in `keep.json`, each drop with a reason (`build_state.py` refuses to run while any field is unassigned; `left-out.md` is written from the reasons).
- **The balance table:** list the likely answers (from their questions, or the goal framing), and count the kept evidence lines that point toward each. Show it.
- If one side has far more lines, offer the fixes with their pros and cons: collapse the absences into one line, list absences for every answer, or drop them.

## 6. The state and the question sketch ✋
- Build the state: `python $S/build_state.py package/template.json keep.json inventory --out state.json --left-out left-out.md` (`--out states` for several images), then `python $S/people_words.py state.json`: it must report no hits, since user-supplied facts in `context` are exempt (add `--context context.json` and `--between between.json` if used). Rules: `state-rules.md`.
- Write `questions.json` and `question-sketch.md`, labeled **"a sketch, not final questions."** 3 to 6 questions, as instruments to check that the state carries what the goal needs; question design is out of scope for this skill.
  - Nouls first.
  - A Choice only when its options don't overlap and cover every case, and each Choice comes with an "is there an answer at all?" Noul.
  - Point at paths in backticks, and don't word an option the way the state is worded.

## 7. The Jev check ✋
Skip this step if `TYPESAFE_API_KEY` is not set, and say so in the report: the state and sketch are still usable. Otherwise:
1. Show the cost first: `uv run $S/jev_check.py fields --state state.json --questions questions.json` prints it and sends nothing (usually under a cent).
2. With the user's go-ahead, add `--yes --out jev-check.md`. This runs the sketch on the pinned model, averaging each Choice over option orders, then the **field-by-field test**: each field removed, plus any counterfactual values in `flips.json`, ranked by how much the answers move. Moves within the run-to-run noise count as no effect.
3. Show the ranking and the options: **accept**; **rebalance** (a field moves the answer more than the goal justifies, or an answer rests on one line); or **revise the brief** (the answer moves on nothing, which means the state is missing what the decision needs).

## 8. Feed back and loop
Carry every fix back into the brief and the template, and re-run from step 3 on the calibration images. Heavy: up to 2 rounds. Light: 1. Stop early when a round changes nothing.

## Phase 1 output: the calibrated package
`package/` holds the frozen package: `brief.md`, `template.json` (fields, order, categories, certainty, how absences are recorded, the rules for `context`), `decoder-prompt.md` (the filled prompt from `decode-protocol.md`, without image paths), and `examples/` with 1 or 2 approved decodes, labeled as format examples. With 5 images or fewer, write `report.md` (see `SKILL.md`) and stop. Otherwise go to `batch.md`.
