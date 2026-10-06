"""Rater agreement: compare two raters' ratings of the same projects, then score both against an owner's answer key.

Agreement shows the rubric reads the same way to two raters; only the answer key shows whether either is right.
Procedure and the checked-risks table: ../rater-agreement.md.

Usage (JEVALUATE_LIBRARY picks the library, as for library.py):
  rater_agreement.py agreement [--a sonnet] [--b codex] [--tuning slug,slug] [--out agreement.md]
  rater_agreement.py facts     [--a sonnet] [--b codex] [--tuning slug,slug] --out facts.json      (held-out projects only)
  rater_agreement.py draw      --facts facts.json --split 3 --agreed 4 --seed N [--skip slug,slug] --out draw.json
  rater_agreement.py score     --key raters.json --owner answers.txt
Rater families come from library.rater_family ("sonnet", "codex", or the model ID for any other rater).
"""
import argparse, json, pathlib, random, re, sys
from collections import Counter

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent / "jevaluate" / "scripts"))

FIELDS = ("type", "f0", "code", "stakes", "verdict")


def kappa(a, b):
    """Cohen's kappa for two raters' labels on the same items; None when chance agreement is 1 (one value everywhere)."""
    n = len(a)
    if n == 0: return None
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return None if pe >= 1 else (po - pe) / (1 - pe)


def agreement(pairs, fields=FIELDS, tuning=()):
    """pairs: {slug: (a_info, b_info)} -> {"held_out": {...}, "tuning": {...}}, each with n and per-field agree/kappa."""
    out = {}
    for name, keep in (("held_out", lambda s: s not in tuning), ("tuning", lambda s: s in tuning)):
        ps = {s: v for s, v in pairs.items() if keep(s)}
        rep = {"n": len(ps)}
        for f in fields:
            a = [v[0].get(f, "") for v in ps.values()]; b = [v[1].get(f, "") for v in ps.values()]
            rep[f] = {"agree": sum(x == y for x, y in zip(a, b)), "kappa": kappa(a, b)}
        if "verdict" in fields:
            rep["within1"] = sum(within1(v[0].get("verdict"), v[1].get("verdict")) for v in ps.values())
        out[name] = rep
    return out


def within1(x, y):
    try: return abs(int(x) - int(y)) <= 1
    except (TypeError, ValueError): return x == y


def draw(facts, n_split, n_agreed, seed, skip=()):
    """A seeded draw for the answer key: split and agreed facts, never a fact both marked n.a., at most one item per
    project across the whole draw and one per fact within each group, so no project or rule dominates."""
    r = random.Random(seed); taken = set(skip); out = {}
    for name, k, pool in (("split", n_split, [f for f in facts if f["split"]]),
                          ("agreed", n_agreed, [f for f in facts if not f["split"] and f["a"] != "n.a."])):
        pool = sorted(pool, key=lambda f: (f["project"], f["fact"])); r.shuffle(pool); got = []
        for f in pool:
            if f["project"] in taken or f["fact"] in {g["fact"] for g in got}: continue
            got.append(f); taken.add(f["project"])
            if len(got) == k: break
        if len(got) < k: print(f"warning: drew {len(got)} {name} facts, not {k}: the pool ran short", file=sys.stderr)
        out[name] = got
    return out


def parse_owner(text):
    """The answer page's copied text ("K1: yes | note: ...") -> {item: answer}."""
    return {m.group(1): m.group(2).strip() for m in re.finditer(r"^(K\d+):\s*([^|\n]+)", text, re.M)}


def score(key, owner):
    """key: {item: {rater: answer}}; owner: {item: answer}. "can't tell" and blanks are counted apart, never as a match."""
    raters = sorted({r for v in key.values() for r in v})
    out = {r: {"right": 0, "wrong": 0, "cant_tell": 0} for r in raters}
    for item, ans in key.items():
        o = owner.get(item, "").strip().lower()
        for r in raters:
            if o in ("", "(blank)", "can't tell", "cant tell"): out[r]["cant_tell"] += 1
            elif ans.get(r, "").strip().lower() == o: out[r]["right"] += 1
            else: out[r]["wrong"] += 1
    return out


# --- reading a library ---
def _lib():
    import library, rubric_text
    return library, rubric_text


def info(p):
    lib, rt = _lib(); t = p.read_text(errors="ignore"); d = lib.front_text(t); f = lambda k: d.get(k, "").split("#")[0].strip()
    f0 = next((v for n, _, v, _ in lib.fact_rows(t) if n == 0), "?")
    return {"type": rt.canon_type(f("project_type")), "f0": f0, "code": f("verdict_1_code"),
            "stakes": lib.derive_top_stakes(d, t) or "n.a.", "verdict": f("verdict"), "path": str(p)}


def pairs_from_library(fa, fb):
    """{project slug: (newest rating by family fa, newest by fb)} for projects both families rated."""
    lib, _ = _lib(); best = {}
    for p in lib.ratings_glob():
        r = (lib.front(p).get("rater") or "unknown").split()[0]
        fam = lib.rater_family(r)
        if fam not in (fa, fb): continue
        k = (p.parent.name, fam)
        if k not in best or lib.rating_key(p) > lib.rating_key(best[k]): best[k] = p
    slugs = {s for s, _ in best}
    return {s: (best[(s, fa)], best[(s, fb)]) for s in sorted(slugs) if (s, fa) in best and (s, fb) in best}


def fact_pairs(pairs, tuning=()):
    out = []
    for s, (pa, pb) in pairs.items():
        if s in tuning: continue
        lib, _ = _lib()  # the library's own fact parser, the one export uses
        a = {n: (nm, v.lower(), w) for n, nm, v, w in lib.fact_rows(pa.read_text(errors="ignore"))}
        b = {n: (nm, v.lower(), w) for n, nm, v, w in lib.fact_rows(pb.read_text(errors="ignore"))}
        for n in sorted(set(a) & set(b)):
            out.append({"project": s, "fact": f"F{n}", "name": a[n][0].strip(), "a": a[n][1], "b": b[n][1],
                        "a_why": a[n][2], "b_why": b[n][2], "split": a[n][1] != b[n][1]})
    return out


def report(rep, fa, fb, pairs, tuning):
    pct = lambda k: "n.a." if k is None else f"{k:.2f}"
    lines = [f"# Rater agreement: {fa} vs {fb}", "",
             "Agreement shows the two raters read the rubric the same way. It does not show either is right; that takes an answer key (rater-agreement.md).", ""]
    for name, title in (("held_out", "Projects outside the tuning sample (lead with these)"), ("tuning", "Tuning sample (agreement here is partly built in)")):
        r = rep[name]
        if not r["n"]: continue
        lines += [f"## {title}: {r['n']} projects", "", "| Field | Agree | Kappa |", "|---|---|---|"]
        lines += [f"| {f} | {r[f]['agree']}/{r['n']} | {pct(r[f]['kappa'])} |" for f in FIELDS]
        lines += [f"| verdict within one point | {r['within1']}/{r['n']} | |", ""]
    lines += ["## Per project", "", "Cells show one value when both agree, **a / b** when they differ.", "",
              "| Project | Type | Calls Jev | Verdict-1 code | Top stakes | Verdict |", "|---|---|---|---|---|---|"]
    for s, (pa, pb) in pairs.items():
        a, b = info(pa), info(pb); m = lambda k: a[k] if a[k] == b[k] else f"**{a[k]} / {b[k]}**"
        lines.append(f"| {s}{' (tuning)' if s in tuning else ''} | {m('type')} | {m('f0')} | {m('code')} | {m('stakes')} | {m('verdict')} |")
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["agreement", "facts", "draw", "score"])
    ap.add_argument("--a", default="sonnet"); ap.add_argument("--b", default="codex"); ap.add_argument("--tuning", default="")
    ap.add_argument("--out"); ap.add_argument("--facts"); ap.add_argument("--split", type=int, default=3); ap.add_argument("--agreed", type=int, default=4)
    ap.add_argument("--seed", type=int); ap.add_argument("--skip", default=""); ap.add_argument("--key"); ap.add_argument("--owner")
    a = ap.parse_args(argv); tuning = {s for s in a.tuning.split(",") if s}
    if a.cmd in ("agreement", "facts"):
        pairs = pairs_from_library(a.a, a.b)
        if a.cmd == "agreement":
            rep = agreement({s: (info(x), info(y)) for s, (x, y) in pairs.items()}, tuning=tuning)
            text = report(rep, a.a, a.b, pairs, tuning)
            if a.out: pathlib.Path(a.out).write_text(text)
            print(text.split("## Per project")[0])
        else:
            fp = fact_pairs(pairs, tuning); pathlib.Path(a.out).write_text(json.dumps(fp, indent=1))
            print(f"{len(fp)} shared facts on held-out projects, {sum(f['split'] for f in fp)} split")
    elif a.cmd == "draw":
        if a.seed is None: sys.exit("draw needs --seed (record it with the results)")
        d = draw(json.loads(pathlib.Path(a.facts).read_text()), a.split, a.agreed, a.seed, [s for s in a.skip.split(",") if s])
        d["seed"] = a.seed; pathlib.Path(a.out).write_text(json.dumps(d, indent=1))
        for g in ("split", "agreed"): print(g, [f"{x['project']} {x['fact']}" for x in d[g]])
    else:
        key = json.loads(pathlib.Path(a.key).read_text()); key = key.get("items", key)
        key = {k: {r: v[r] for r in v if r not in ("project", "fact")} for k, v in key.items()}
        print(json.dumps(score(key, parse_owner(pathlib.Path(a.owner).read_text())), indent=1))


if __name__ == "__main__":
    main()
