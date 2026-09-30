# jevaluate-eval commands

Run from the repo root.

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
| Quiz | `python3 jevaluate-eval/quiz/run_quiz.py --system vocab\|routing --reps N --out jevaluate-eval/.work/<run>` |
| Quiz score | `python3 jevaluate-eval/quiz/score_quiz.py jevaluate-eval/.work/<run>` |
| Eval, before a change | `python3 jevaluate-eval/run_eval.py --phase baseline --out jevaluate-eval/.work/<run>` (also `--reps`, `--effort`) |
| Eval, after a change | `python3 jevaluate-eval/run_eval.py --phase after --out jevaluate-eval/.work/<run>` |
| Eval score | `python3 jevaluate-eval/score.py jevaluate-eval/.work/<run>` |

Headless wording tests: `claude -p --setting-sources "" --strict-mcp-config --tools "" --system-prompt-file <f> --model <m> --effort <e> --output-format json < prompt.md` (`--bare` fails on OAuth logins). Sum each call's `usage`; agent token logs miss these calls.
