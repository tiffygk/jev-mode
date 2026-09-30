# What code enforces and what stays judgment

Every routing call and every fact in `rubric.md` has one row. A row names the function that enforces it, or says why the rule stays judgment, or both when code checks the format and a person still decides the value. `jevaluate-eval/lint_materials.py` fails when a routing call or fact has no row, or when a named function does not exist. Nothing here applies to a rating on a rubric older than 2026-09-29.

Routing calls (the rater and the owner answer only what they observe; code derives the rest):

| rule | enforced by | or judgment, because |
|---|---|---|
| kind | `library.store_derived` writes it from the type; `library.check_schema` ignores a rater-entered kind | |
| project_type | `library.check_schema` (an allowed value, and consistent with F0, the code and the citation; a guide with F0 yes, or whose non-test code holds a hosted call, is refused: a project that calls Jev is typed by what its code does); `step.missing` withholds the facts until it is written (template text from read.md counts as unwritten, for F0 too) | Which type fits depends on what the project's code does with Jev's answers. Reading that needs a person; the eval grader tests it. |
| verdict_1_code | `library.check_schema` (1t only for a guide, 1c only for a uses type, 1a or 1b for a jev-mention-only, 1a or 1r for a jev-replacement by whether it quotes a claim, and a code only with verdict 1) | Whether a claim to be Jev exists, and whether the answers are unused, are read from the project. |
| citation | `library.check_schema` (1a needs the claim quoted with its file:line) | Whether the quoted text is a claim to be or call Jev is read from the project. |
| stakes | `library.check_decisions` (each line has five parts, a primitive, an allowed level, and an `acts at` file that is in the evidence folder) | The level follows the rubric's stakes definitions applied to what the action changes, which needs a person's reading. |
| top_stakes | `library.derive_top_stakes` works it out and `library.store_derived` writes it: n.a. for a guide, a client or any verdict-1 code, else the highest listed level (`library.highest_stakes`; `jevaluate-eval/score.py` scores the grader's decisions list with the same function, not its stated top_stakes) | |

Facts:

| rule | enforced by | or judgment, because |
|---|---|---|
| F0 Calls hosted Jev | `library.check_f0` (yes cites a line `jev_callsites.citable_in` accepts: any call expression, endpoint or model ID in a non-test file that holds a hosted marker (a TypeSafe import, client construction, api.typesafe.ai URL or model ID), never a package.json, comment, import, dependency, throw, class or constructor declaration, regex or bare string; no names every file `jev_callsites.calls_in` flags (imports, client constructions, calls on the client, endpoint and model IDs: the rule `jevaluate-eval/check_labels.py` shares, along with `library.CITE`, `same_file`, `cites_a_call` and `no_reasoned`), with a reason; with yes or no and no evidence `files/` folder found, beside the rating or by `--evidence`, `check` and `add` refuse with "F0 was not checked"); `library.check_schema` (a uses type is yes, a jev-replacement or jev-mention-only is no); `library.store_derived` (a guide records n.a.) | |
| F1 Atomic questions | `library.check` (the line exists, its value is allowed, a no carries a docs link and the verdict cap); `library.check_mechanical` (finding at most 20 words) | Whether a question asks one property needs reading the question text against the standard it names. |
| F2 Right primitive | `library.check_decisions` (each decision names Noul, Choice or Score); `library.check` (line, value and cap) | Whether the primitive fits the answer's shape needs reading the question. |
| F3 Structured state | `library.check` (line, value and cap) | Whether the state is named fields or one joined string needs reading the code that builds it. |
| F4 Batching | `library.check` (line, value and cap) | Whether independent questions share one request needs reading the call sites. |
| F5 Thresholds in code | `library.check` (line, value and cap) | Whether a cut-off is a named constant or a phrase in the question needs reading both. |
| F6 No invented values | `library.check` (a no caps the verdict at 2) | Whether Jev is asked to count or calculate needs reading the question text. |
| F7 Measured in the workflow | `library.check` (line and value) | Whether a reported number comes from the project's own task needs reading its results. |
| F8 Options cover every case | `library.check` (line, value and cap) | Whether options overlap or leave cases out needs reading them against realistic inputs. |
| F9 An "other" option | `library.check` (line, value and cap) | Whether a case falls outside the options needs reading them against realistic inputs. |
| F10 Evidence recorded evenly | `library.check` (line, value and cap) | Whether the state favors one answer needs reading the state's fields. |
| F11 Confidence drives action | `library.check_decisions` (n.a. is refused when any decision is above low); `library.check` (a no on a high or very high decision caps the verdict at 2); `step.stakes_rows` serves only the rows for the levels listed | Whether the probability gates the action needs reading the code path that acts. |
| F12 Pinned model version | `library.check` (line and value; a no moves nothing) | Whether a tuned threshold exists and the model ID is versioned needs reading the config. |
| F13 Choice order handled | `library.check_decisions` (n.a. when no Choice is high or very high; refused as n.a. for a very high Choice, or a high Choice whose F11 is not yes); `library.check` (a no on very high caps the verdict at 3) | Whether option orders are varied or a gate stands in needs reading the calls. |
| F14 Size limits respected | `library.check` (line and value; a no moves nothing) | Whether a guard or a reported maximum exists needs reading the code and the docs. |
| F15 Sample size adequate | `library.check` (line and value) | Whether a sample supports its claim is arithmetic on a number the project reports, read from its results. |
| F16 Independent labels | `library.check` (line and value) | Who labeled the data is read from the project's own description. |
| F17 Held-out result | `library.check` (line and value) | Whether a threshold was tuned on the reported data is read from the project's method. |
| F18 Fair baseline | `library.check` (line and value) | Whether a baseline is reasonable is read from the project's comparison. |
| F19 Typed answers read directly | `library.check` (line, value and cap) | Whether the decision reads the typed field or greps text needs reading the code. |
| F20 Data as fields, not templates | `library.check` (very high: a no caps the verdict at 3; else listed as a fix) | Whether values are spliced into question text needs reading the question construction. |
| F21 No instructions in the state | `library.check` (a no caps the verdict at 3) | Whether a state field holds directions needs reading the state. |
| F22 Untrusted text treated as data | `library.check` (very high: a no caps the verdict at 3; else listed as a fix) | Whether user text is flagged or tested needs reading the state and the tests. |
| F23 Non-English handled | `library.check` (line and value; a no moves nothing) | Whether inputs in other languages matter is a judgment about the project's users. |

Rules on the rating as a whole are also code: `library.check_steps` (the step log shows each section was served in order and the routing calls did not change afterward), `library.check_mechanical` (word and sentence limits, stage labels, commit against the evidence), and `library.check` (evidence coverage, no process notes, verdict caps and the verdict-5 requirements).
