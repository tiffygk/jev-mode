# jevaluate-eval commands

Run from the repo root. Run output goes to a runs folder: set `RUNS="${JEVALUATE_RUNS:-jevaluate-eval/.work}"` first. Set `JEVALUATE_RUNS` to a folder outside the repo to keep run output after the checkout is gone; `run_eval.py` then refuses any other `--out`.

| Step | Command |
|---|---|
| Lint | `python3 jevaluate-eval/lint_materials.py` |
| Grader view | `python3 jevaluate-eval/build_grader_view.py <out.html> [<notes file>]` |
| Answer form | `python3 jevaluate-eval/quiz/build_answer_form.py --count 12` |
| Packet files for a case | `python3 jevaluate-eval/pick_files.py <manifest dir>` |
| Blind label, checked | `python3 jevaluate-eval/check_labels.py run <labeler prompt> <case packet> <out json>` |
| Evidence cards | `python3 jevaluate-eval/build_cards.py <packets dir> <notes.json> <cards.json>` |
| Answer form, new cases | `python3 jevaluate-eval/quiz/build_answer_form.py --cards <cards.json> --out <form.html>` |
| Key from answers | `python3 jevaluate-eval/quiz/build_answer_form.py --key <answers.json>` |
| Quiz | `python3 jevaluate-eval/quiz/run_quiz.py --system vocab\|routing --reps N --out "$RUNS/<run>"` |
| Quiz score | `python3 jevaluate-eval/quiz/score_quiz.py "$RUNS/<run>"` |
| Eval, before a change | `python3 jevaluate-eval/run_eval.py --phase baseline --out "$RUNS/<run>"` (also `--reps`, `--effort`) |
| Eval, after a change | `python3 jevaluate-eval/run_eval.py --phase after --out "$RUNS/<run>"` |
| Eval score | `python3 jevaluate-eval/score.py "$RUNS/<run>"` |

Headless wording tests: `claude -p --setting-sources "" --strict-mcp-config --tools "" --system-prompt-file <f> --model <m> --effort <e> --output-format json < prompt.md` (`--bare` fails on OAuth logins). Sum each call's `usage`; agent token logs miss these calls.
