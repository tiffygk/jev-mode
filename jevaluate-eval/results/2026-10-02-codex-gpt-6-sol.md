# Codex grader (gpt-6-sol), 2026-10-02

Grader: `gpt-6-sol`, reasoning effort medium, through `run_eval.py --runner codex`: an empty Codex home (login only), no shell, image, web, plugin, skill-search or multi-agent tools, read-only sandbox, empty working folder. What remains is a JavaScript sandbox with no file access; its calls don't appear in Codex's log. Compared with the saved Sonnet baseline run (2026-09-30), whose system prompt, packets and task.md are byte-identical; both runs scored with today's `score.py`. Answer key 35edf8648f34.

## Result: Sol fails one tuning case; Sonnet passes all 19

```
Sonnet: claude-sonnet-5-5 commit d107e63 | Codex: gpt-6-sol effort medium commit a42a256 | key 35edf8648f34
Inputs: identical (system prompt, packets, task.md)

| case | set | Sonnet answered | Sol answered | kind S/Sol | type S/Sol | f0 S/Sol | code S/Sol | stakes S/Sol | Sonnet pass | Sol pass |
|---|---|---|---|---|---|---|---|---|---|---|
| jev-omni | tuning | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | True | True |
| jevmlx | tuning | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | True | True |
| kev | heldout | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | True | True |
| typesafe-sdk-js | tuning | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | True | True |
| askjevs | tuning | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | True | True |
| vibecheck | tuning | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | True | True |
| jev-mcp | tuning | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | True | True |
| building-with-jev-skill | tuning | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | True | True |
| email-tagger | tuning | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | True | True |
| refund-bot | tuning | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | True | True |
| fast-jev-compaction | tuning | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | True | True |
| memsearch | heldout | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | True | True |
| jev-web-analyzer | tuning | 3/3 | 3/3 | 3/3 | 3/2 | 3/3 | 3/3 | 3/3 | True | False |
| jev-agent-harness | heldout | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | True | True |
| jev-gem-scan | heldout | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | True | True |
| soter | heldout | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | True | True |
| tripwire | tuning | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | True | True |
| jev-auto-approve | heldout | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | True | True |
| jev-guard | heldout | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | 3/3 | True | True |

Overall: Sonnet PASS, Sol FAIL (today's score.py for both)
Tokens: Sonnet 382,344; Sol 314,387 (Codex carries built-in tool overhead; not a quality measure)

Sol calls with tool use or no answer:
none
```

`fast-jev-compaction` and `tripwire` were held-out cases Sonnet missed in its first run (2026-09-30), then moved to tuning after a rubric edit; Sol passes both 3/3.

## Comprehension quiz (same scorer for both)

| Run | Sonnet | Sol |
|---|---|---|
| Vocabulary-only control (should stay under 80%) | 8/11 (73%) | 5/11 (45%) |
| Routing instructions, 3 runs | 10/11 | 9/11 |

Both miss q03 on stakes (0/3). The 2026-09-30 Sonnet quiz passed it; `score.py` now derives stakes from the decisions, so this is scorer drift, not either model.

## Sol's misses: one pattern

| Case | Key | Sol | Runs |
|---|---|---|---|
| jev-web-analyzer (eval) | demo | workflow in 1 of 3 | r2 |
| q08 jev-scoreboard (quiz) | demo | workflow in 3 of 3 | all |

Both are a batch or nightly job that sends items to Jev, stores the scores, and a page shows them; nothing else acts on a score. Sol's reason in r2: "Uses Jev's rubric scores to compute a public score; the published score does not trigger a further action." It reads the job's computing as the project's code acting, under rubric section 1's line that a scheduled job applying a rule written in advance is a workflow. Sonnet reads both as demos.

## Isolation findings (fixed before these runs)

- With only `CODEX_HOME` redirected, Codex loaded the user's skills from `~/.agents/skills`. `HOME` now points at the temp home too.
- With a shell, the grader searched the disk for `rubric.md` and read it, even in a read-only sandbox, during the first vocabulary control. That run was discarded; the shell and other tools are now off, and any tool use marks a comparison invalid.

## Not decided here

Whether to add a Codex-only note on the demo/workflow line (`codex-notes.md`, one edit round, then one full re-run reported beside this one), and whether Codex ratings go ahead.
