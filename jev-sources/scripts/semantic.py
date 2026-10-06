"""Local semantic scores for route.py: a static embedding model (model2vec) over each section.
Vectors live beside sections.jsonl in $JEV_SOURCES_DATA; nothing here touches the network at
query time. Any problem returns (None, reason) and route.py falls back to BM25 alone."""
import json, os, re
import numpy as np
from paths import DATA

MODEL_ID = "minishlab/potion-base-8M"   # measured in Task 1: 256-d, ~0.26 s cold load plus one embed
VEC, META = os.path.join(DATA, "embeddings.npy"), os.path.join(DATA, "embeddings.json")
os.environ.setdefault("HF_HOME", os.path.join(DATA, "models"))
ALLOW_DOWNLOAD = False  # build_index.py sets True: index time may download the model once
_model = None


def _load_model():
    global _model
    if _model is None:
        if not ALLOW_DOWNLOAD:
            os.environ["HF_HUB_OFFLINE"] = "1"  # query time never touches the network
        from model2vec import StaticModel
        _model = StaticModel.from_pretrained(MODEL_ID)
    return _model


def available():
    try:
        _load_model()
        return True, "ok"
    except Exception as e:  # missing package, missing download
        return False, f"model unavailable ({type(e).__name__})"


CODE_END = re.compile(r"^[}\])]+;?\s*$")


def prose(lines):
    """Drop what isn't prose: fenced code, MDX export/import blocks, tags, link targets, emphasis."""
    out, fence, block = [], False, False
    for ln in lines:
        if ln.lstrip().startswith(("```", "~~~")):
            fence = not fence; continue
        if fence:
            continue
        if block:
            block = not CODE_END.match(ln); continue
        if ln.startswith(("export ", "import ")):
            block = not ln.rstrip().endswith((";", "}")) and not ln.startswith("import "); continue
        ln = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", ln)
        ln = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", ln)
        ln = re.sub(r"<[^>]*>", "", ln)
        ln = re.sub(r"[*_`#>|]+", " ", ln)
        if ln.strip():
            out.append(" ".join(ln.split()))
    return "\n".join(out)


def section_text(row, lines):
    body = prose(lines[row["line_start"] - 1:row["line_end"]])
    return row["heading"] + "\n" + body[:20000]


def chunks(text, size=80):
    """The whole section, then each paragraph led by its heading (long ones in word windows),
    so a long section is scored by its best part."""
    head, _, body = text.partition("\n")
    out = [text[:2000]]
    for para in body.split("\n"):
        words = para.split()
        if len(words) < 5:
            continue
        for k in range(0, max(1, len(words) - size // 2), size // 2):
            out.append(head + "\n" + " ".join(words[k:k + size]))
    return out


def _embed(texts):
    v = np.asarray(_load_model().encode(texts), dtype=np.float32)
    n = np.linalg.norm(v, axis=1, keepdims=True)
    return v / np.where(n == 0, 1, n)


def _key(r):
    """What a section's vector was built from; a change means the vector is stale even if the id isn't."""
    return [r.get("path"), r.get("heading"), r.get("line_start"), r.get("line_end")]


def clear():
    for f in (VEC, META):
        if os.path.exists(f):
            os.remove(f)


def build(rows, texts):
    parts, owners = [], []
    for k, t in enumerate(texts):
        for c in chunks(t):
            parts.append(c); owners.append(k)
    v = _embed(parts)
    np.save(VEC, v)
    with open(META, "w") as fh:
        json.dump({"model": MODEL_ID, "dim": int(v.shape[1]), "ids": [r["id"] for r in rows], "owners": owners,
                   "keys": {r["id"]: _key(r) for r in rows}}, fh)


def scores(q, rows):
    try:
        with open(META) as fh:
            meta = json.load(fh)
        v = np.load(VEC)
    except (FileNotFoundError, ValueError, OSError):
        return None, "no semantic index; run refresh.sh"
    if meta.get("model") != MODEL_ID:
        return None, f"index built with model {meta.get('model')}; run refresh.sh"
    ids, owners = meta.get("ids", []), meta.get("owners", [])
    pos = {i: k for k, i in enumerate(ids)}
    keys = meta.get("keys", {})
    if len(owners) != len(v) or any(r["id"] not in pos or keys.get(r["id"]) != _key(r) for r in rows):
        return None, "stale semantic index; run refresh.sh"
    try:
        qv = _embed([q])[0]
    except Exception as e:
        return None, f"model unavailable ({type(e).__name__})"
    best = np.full(len(ids), -1.0, dtype=np.float32)
    with np.errstate(all="ignore"):  # numpy 2 + Accelerate warns spuriously on float32 matmul
        sims = v @ qv
    np.maximum.at(best, np.asarray(owners), sims)  # a section scores as its best chunk
    return {r["id"]: float(best[pos[r["id"]]]) for r in rows}, "ok"
