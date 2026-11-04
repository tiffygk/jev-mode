# Lessons from past reports

Each lesson is general; the example shows where it came from. The first report was written for an outside project, skimmer, a Go tool that asks Jev a keep-or-drop question per chunk of a page (October 2026). Its maintainer adopted 14 of 16 fixes and tested the other two on held-out goals before declining them.

## What the reader acted on

- **Line-cited, checkable defects.** The maintainer wrote that the code citations held up and named three findings that "found real problems": an id-matching bug in the eval, a model alias mismatch, and the push for held-out goals, baselines and intervals. A fix the maintainer can check against one line of their own code gets acted on first.
- **Fixes phrased as a test.** Each adopted fix came with a "How to check it" the maintainer could run. They ran several and reported the numbers back.

## What the first draft got wrong

- **The opening hid the result.** It opened with thanks and praise and never gave the verdict. The template now opens with what the report is and that each fix is a test, then the verdict and its one cause, then the top fixes as bullets.
- **The rating was left out,** so it wouldn't read as a grade. Readers wanted the verdict and each score with what it means. Include the Rating section; the advice framing does the softening.
- **No summary table, and bare fix numbers.** "See S9" sends the reader back to the table. Put the table right after the opening and refer to fixes by section name.
- **A claim added late was wrong.** A sentence added in chat, after review, described how the project's eval questions were written, and the code showed otherwise. Check every claim added after the draft against the code before it goes in.
- **No room for disagreement.** The final version added a line asking for pushback and a line pointing the reader's agents at the index. The template's agent paragraph keeps both: ask before changing what the team already tested, and work down the table.

## What the maintainer's tests taught

- **The verdict-moving fix lost.** Splitting the broad question was the top fix. On the maintainer's held-out goals it "raised near-miss leak from 2 to 8 of 18 (p = 0.03)", so they kept their design. Docs practice is a hypothesis about the product; frame every fix as advice to try against a bar, and keep the current design as the control.
- **The maintainer had already tested a version of it.** Their variants run had tried a two-question design combined with AND and rejected it. Read the project's own experiments before proposing a fix, and when one was tried, propose a different version.
- **Defaults the maintainer declined.** Two changes showed "no measurable difference" and a stricter cutoff lost 8 of 42 holdout goals. They shipped some as opt-in features instead. Offer a change as an option when the evidence for it is docs practice alone.

## What broke after the review

- **A quote checker found four slips in the posted file.** Two docs quotes had no link to their page, one quoted a filled-in example as the template text, and one named a table column with an extra word. `trace_check.py` now checks every docs and code quote before the file is handed back.
- **A label broke in the last edit.** A sentence pasted into the last fix replaced its "How to check it" label after the review panel had passed the file. Rerun both checks on the file exactly as the agents will read it.
