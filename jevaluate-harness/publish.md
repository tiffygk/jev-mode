# Publishing ratings

Publish only full or agreed-scoped ratings under the current rubric; never evidence folders.

1. Every rating has a `why:` line of 20 words or fewer.
2. `python3 jevaluate/scripts/library.py export <preview dir>`; render it and read the index, a detail page and a full page.
3. A fresh reviewer reads every page for private context (anything from a private conversation; people named other than by their GitHub or Hugging Face handle), rater process notes, and broken or unlinked `file:line` references. Brief it to skip hedging and tone suggestions.
4. Check the README's claims against the skill's current files.
5. Export into `ratings/`, run a GitHub readiness audit, and open one pull request.
