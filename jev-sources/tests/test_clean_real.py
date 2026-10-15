"""Checks the cleaner against the real saved library. Runs only with JEV_CLEAN_REAL=1 and the backup library present."""
import glob, importlib, os, re, shutil, sys
import pytest

SCRIPTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts")
sys.path.insert(0, SCRIPTS)
import clean

BACKUP = os.path.expanduser("~/.claude/backups/jev-sources-data-2026-10-15-pre-clean")
KINDS = ("docs", "cookbooks", "patterns")
pytestmark = pytest.mark.skipif(
    os.environ.get("JEV_CLEAN_REAL") != "1" or not os.path.isdir(os.path.join(BACKUP, "docs")),
    reason="set JEV_CLEAN_REAL=1 with the backup library present")

TAGS = re.compile(r'<[^>\n]+>|\{"|"\}|[*_`#>\[\]]')


def words(s):
    """Words of a line as the prose check sees them. The share payload is dropped (the cleaner cuts it) and a
    tag attribute `alt="` prefix is ignored (the alt text itself still counts)."""
    s = clean.SHARE.sub(r"\1", s)
    s = re.sub(r'^\s*alt="', "", s)
    return re.findall(r"[A-Za-z][A-Za-z'-]+", TAGS.sub(" ", s))


def norm_text(t):
    return " " + " ".join(" ".join(words(ln)) for ln in t.split("\n")).lower() + " "


def page_files():
    out = []
    for kind in KINDS:
        out += sorted(glob.glob(os.path.join(BACKUP, kind, "*.md")))
    return out


@pytest.fixture(scope="module")
def trees(tmp_path_factory):
    base = tmp_path_factory.mktemp("lib")
    raw, cleaned = {}, {}
    for kind in KINDS:
        for d in ("raw", "clean"):
            os.makedirs(os.path.join(str(base), d, kind))
    for p in page_files():
        rel = os.path.relpath(p, BACKUP)
        text = open(p, encoding="utf-8").read()
        raw[rel], cleaned[rel] = text, clean.clean(text)
        shutil.copyfile(p, os.path.join(str(base), "raw", rel))
        with open(os.path.join(str(base), "clean", rel), "w", encoding="utf-8") as f:
            f.write(cleaned[rel])
    return {"base": str(base), "raw": raw, "clean": cleaned}


def sections_of(tree_dir, monkeypatch):
    monkeypatch.setenv("JEV_SOURCES_DATA", tree_dir)
    monkeypatch.setenv("JEV_LOG", "off")
    for name in ("build_index", "paths"):
        sys.modules.pop(name, None)
    bi = importlib.import_module("build_index")
    rows = []
    for rel in sorted(glob.glob(os.path.join(tree_dir, "*", "*.md"))):
        rows += bi.sections(os.path.relpath(rel, tree_dir))
    return rows


def exempt(ln):
    s = ln.lstrip()
    return bool(clean.CODEISH.search(ln)) or s.startswith(("<", "{"))


CODE_PUNCT = re.compile(r"[;{}=()]")


def dropped_lines(raw_lines, kept_lines):
    """Indexes of raw lines the cleaner removed (it only deletes whole lines or rewrites them)."""
    gone, j = set(), 0
    for i, ln in enumerate(raw_lines):
        if j < len(kept_lines) and kept_lines[j] == ln:
            j += 1
        else:
            gone.add(i)
    return gone


def test_no_lost_prose(trees):
    lost = []
    for rel, raw in trees["raw"].items():
        if raw == trees["clean"][rel]:
            continue
        nt = norm_text(trees["clean"][rel])
        raw_lines = raw.split("\n")
        gone = dropped_lines(raw_lines, trees["clean"][rel].split("\n"))
        for i, ln in enumerate(raw_lines):
            w = words(ln)
            if i in gone and (CODE_PUNCT.search(ln) or ln.rstrip().endswith(",")):
                continue  # a removed widget line that reads as code; prose in a mis-ended block ends in a full stop
            if len(w) >= 6 and not exempt(ln) and " " + " ".join(w).lower() + " " not in nt:
                lost.append((rel, i + 1, ln.strip()[:160]))
    assert not lost, "lost prose lines: %d, first: %s" % (len(lost), lost[:10])


def test_flagged_sections_are_gone(trees, monkeypatch):
    def flagged(tree, key):
        n = []
        for row in sections_of(os.path.join(trees["base"], tree), monkeypatch):
            lines = trees[key][row["path"]].split("\n")[row["line_start"] - 1:row["line_end"]]
            if clean.code_shaped(lines) >= 10:
                n.append(row["id"])
        return n
    before, after = flagged("raw", "raw"), flagged("clean", "clean")
    print("flagged sections raw=%d cleaned=%d" % (len(before), len(after)))
    assert len(before) >= 19, len(before)
    assert not after, after


def test_no_long_lines_or_html_headings(trees):
    for rel, text in trees["clean"].items():
        for i, ln in enumerate(text.split("\n")):
            assert len(ln) <= 1000, (rel, i + 1, len(ln))
        outside = [ln for ln, inside in zip(text.split("\n"), clean.fences(text.split("\n"))) if not inside]
        assert not re.search(r"<h[1-6]\b", "\n".join(outside)), rel


def test_sdk_pages_have_unique_headings(trees, monkeypatch):
    seen = {}
    for row in sections_of(os.path.join(trees["base"], "clean"), monkeypatch):
        if os.path.basename(row["path"]).startswith("sdk__"):
            seen.setdefault((row["path"], row["heading"]), []).append(row["id"])
    dup = {k: v for k, v in seen.items() if len(v) > 1}
    assert not dup, dup


def test_llms_full_prose_is_in_the_cleaned_pages(trees):
    full = os.path.join(BACKUP, "llms-full.txt")
    if not os.path.exists(full):
        pytest.skip("no llms-full.txt in the backup")
    by_url = {}
    for rel, text in trees["clean"].items():
        m = re.search(r"<!-- saved \S+ from (\S+?)(?:\.md)? ", text)
        if m:
            by_url[m.group(1)] = norm_text(text)
    pages, cur = {}, None
    for ln in open(full, encoding="utf-8").read().split("\n"):
        m = re.match(r"^Source: (\S+)", ln)
        if m:
            cur = pages.setdefault(m.group(1), [])
        elif cur is not None:
            cur.append(ln)
    raw_by_url = {}
    for rel, text in trees["raw"].items():
        m = re.search(r"<!-- saved \S+ from (\S+?)(?:\.md)? ", text)
        if m:
            raw_by_url[m.group(1)] = norm_text(text)
    missing, drift, checked = [], [], 0
    for url, lines in pages.items():
        if url not in by_url:
            continue
        checked += 1
        for ln in lines:
            w = words(ln)
            needle = " " + " ".join(w).lower() + " "
            if len(w) >= 6 and not exempt(ln) and needle not in by_url[url]:
                # absent from the saved raw page too: the site changed since the page was saved, not the cleaner
                (missing if needle in raw_by_url[url] else drift).append((url, ln.strip()[:160]))
    print("llms-full pages checked=%d missing lines=%d site-drift lines=%d" % (checked, len(missing), len(drift)))
    print("drift:", drift)
    assert checked > 0
    assert not missing, "missing: %d, first: %s" % (len(missing), missing[:10])
