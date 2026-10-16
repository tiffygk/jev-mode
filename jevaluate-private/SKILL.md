---
name: jevaluate-private
description: Rates a project with Jevaluate and keeps the rating private, with the same rubric and checks, a private library that export refuses, and nothing pushed or published. Use when a rating must stay private, such as "/jevaluate-private" followed by a link or folder, "rate this privately", "evaluate my own project", a client's or employer's code, a design doc or a local folder that isn't public, or any rating that must not reach the public ratings or the repo.
---

# Jevaluate, privately

Rates a project exactly as `jevaluate` does, with the same rubric, steps and checks, and keeps the rating out of everything public. The rating lives in a private library that export refuses, and nothing is pushed, published or added to `ratings/`.

## Setup, once per machine

`python3 <jevaluate>/scripts/library.py init-private ~/.jevaluate-private` creates the private library, marked by a `PRIVATE` file. `<jevaluate>` is the `jevaluate` skill's folder, beside this one.

## How to rate

1. Set `JEVALUATE_LIBRARY=~/.jevaluate-private` for every command in the rating, so `step.py` and `library.py` read and write only the private library. Create the library first if it doesn't exist.
2. Gather the files:
   - a GitHub link: `coverage_manifest.py owner/repo <dir>`, as usual;
   - a folder on disk: `coverage_manifest.py --local <folder> <dir>`. It applies the same skip rules and size cap, reads nothing outside the folder, and records git HEAD as the commit (or a content fingerprint when the folder isn't a clean git checkout).
3. Follow the `jevaluate` skill and its `read.md` unchanged. Two differences only:
   - the project's own files may be private, while the rules still come only from docs.typesafe.ai;
   - a local folder's `url` is `local:<short-name>`.
4. Add `visibility: private` to the rating's front matter, then log it with `../jevaluate/scripts/library.py` add as usual. `add` refuses a private rating into a public library, and refuses a non-private rating into a private one.
5. Finish with the rating's verdict and its fixes in plain words, for the person who asked. Offer a page if they want one to share. Never run `../jevaluate/scripts/library.py` export, never copy the rating into a repo, and never push.

Comparisons with past ratings come only from the private library, so a private rating is never shown beside a public one.

## Enforced by

| Rule | Enforced by |
|---|---|
| A private rating goes only into a private library, and a private library takes only private ratings | `../jevaluate/scripts/library.py` add; `../jevaluate/scripts/test_private.py` |
| A rating of a local folder counts as private | `../jevaluate/scripts/library.py` add; `../jevaluate/scripts/test_private.py` |
| Export refuses a private library and any private rating | `../jevaluate/scripts/library.py` export; `../jevaluate/scripts/test_private.py` |
| A local folder is read with the same skip rules, and nothing outside it | `../jevaluate/scripts/coverage_manifest.py` --local; `../jevaluate/scripts/test_private.py` |
| `JEVALUATE_LIBRARY` set for every command; no rating copied into a repo or pushed | judgment |
