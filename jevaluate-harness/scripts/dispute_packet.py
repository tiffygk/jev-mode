"""Blind packet for one disputed fact (round step 6): the rubric row quoted exactly, the code both ratings
cite, and the two answers as "Answer A" and "Answer B" in seeded order. No rater name, model ID or rating path
appears, so whoever answers it can't tell which rater wrote which. The controller, who has read both ratings, never answers it.

Usage: python3 dispute_packet.py <rating A> <rating B> <fact, e.g. F8> <evidence dir> [--seed N] > packet.md
The evidence dir is the rating's evidence folder (its files/ holds the project's files, / flattened to __).
"""
import pathlib, random, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
RUBRIC = ROOT / "jevaluate" / "rubric.md"
CITE = re.compile(r"`?([\w./-]+\.\w+):(\d+)(?:-(\d+))?`?")
RATER_WORDS = re.compile(r"\b(claude[\w.-]*|sonnet[\w.-]*|opus[\w.-]*|haiku[\w.-]*|fable[\w.-]*|gpt[\w.-]*|o[1-9][\w.-]*|sol|codex|openai|anthropic|gemini[\w.-]*|grok[\w.-]*|llama[\w.-]*|mistral[\w.-]*|deepseek[\w.-]*|qwen[\w.-]*)\b", re.I)


def fact_line(rating, fact):
    """(value, finding) of the fact's line in a rating, e.g. ('no', 'A refund is billing (`src/x.py:3`)')."""
    m = re.search(rf"^\s*[-*]\s*\**{re.escape(fact)}\b[^\n]*?(?:--|—)\s*\**(yes|no|n\.a\.|unknown)\**\.?\s*(.*)$",
                  pathlib.Path(rating).read_text(errors="ignore"), re.M | re.I)
    if not m: sys.exit(f"{fact} not found in {rating}")
    return m.group(1).lower(), m.group(2).strip()


def rubric_rows(fact):
    return [l for l in RUBRIC.read_text().splitlines() if re.match(rf"^\|\s*{re.escape(fact)}\b", l)]


def excerpt(evidence, path, a, b, pad=4):
    f = pathlib.Path(evidence) / "files" / path.replace("/", "__")
    if not f.exists(): return f"(`{path}` isn't in the evidence)"
    lines = f.read_text(errors="ignore").splitlines(); lo, hi = max(1, a - pad), min(len(lines), (b or a) + pad)
    return f"`{path}` lines {lo}-{hi}:\n\n```\n" + "\n".join(f"{i:4} {lines[i - 1]}" for i in range(lo, hi + 1)) + "\n```"


def scrub(text, paths, names=True):
    """Rating paths go everywhere; model and company names only where named (the answers), so quoted code stays exact."""
    for p in paths: text = text.replace(str(p), "[a rating]")
    return RATER_WORDS.sub("[a rater]", text) if names else text


def packet(rating_a, rating_b, fact, evidence, seed=0):
    answers = [fact_line(rating_a, fact), fact_line(rating_b, fact)]
    random.Random(seed).shuffle(answers)
    cites = []
    for _, why in answers:
        for m in CITE.finditer(why):
            c = (m.group(1), int(m.group(2)), int(m.group(3)) if m.group(3) else None)
            if c not in cites: cites.append(c)
    out = [f"# Disputed fact: {fact}", "",
           "Two ratings of the same project answer this fact differently. Settle it from the rule and the code below. "
           "Answer with the value, one sentence on why, and the line that decides it. If the code shown can't settle it, say what's missing.", "",
           "## The rule", ""] + (rubric_rows(fact) or [f"(no rubric row starts with {fact})"]) + ["", "## The code the answers cite", ""]
    out += [excerpt(evidence, p, a, b) + "\n" for p, a, b in cites] or ["(neither answer cites a file)", ""]
    tail = ["## The two answers", ""] + [f"- **Answer {k}:** {fact} -- {v}. {why.replace(chr(0x2014), '--')}" for k, (v, why) in zip("AB", answers)]
    return scrub("\n".join(out) + "\n", [rating_a, rating_b], names=False) + scrub("\n".join(tail) + "\n", [rating_a, rating_b])


if __name__ == "__main__":
    a = sys.argv[1:]; seed = 0
    if "--seed" in a:
        i = a.index("--seed"); seed = int(a[i + 1]); a = a[:i] + a[i + 2:]
    if len(a) != 4: sys.exit(__doc__)
    sys.stdout.write(packet(*a, seed=seed))
