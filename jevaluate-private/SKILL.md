---
name: jevaluate-private
description: Use when rating a project with Jevaluate that must stay private -- "/jevaluate-private <link or folder>", "rate this privately", "evaluate my own project", a client's or employer's code, a design doc or a local folder that isn't public, or any rating that must not reach the public ratings or the repo.
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
4. Add `visibility: private` to the rating's front matter, then log it with `library.py add` as usual. `add` refuses a private rating into a public library, and refuses a non-private rating into a private one.
5. Finish with the rating's verdict and its fixes in plain words, for the person who asked. Offer a page if they want one to share. Never run `library.py export`, never copy the rating into a repo, and never push.

Comparisons with past ratings come only from the private library, so a private rating is never shown beside a public one.
