"""Versioned cleaner for saved docs pages. Takes a page as served and removes site widget code.

Goes:
  - column-0 `export function/const/let` widget blocks outside code fences (the block ends at its first
    closing line; if a code fence, a Markdown heading or the end of the page comes first, the block is kept);
  - share-link payloads (`#share/...`), cut to the bare playground URL;
  - SDK signature spans, collapsed to a fenced python line;
  - image tags, reduced to one `[image: alt]` line (the dark-theme twin is dropped);
  - HTML headings `<hN ...>`, turned into Markdown headings (a dotted `id` names the heading).

Stays: all prose, Markdown, `<Note>`, `<Tip>`, `<Warning>` and other wrapper tags, and everything inside code
fences, untouched.

Raise VERSION whenever a rule changes, so saved pages are re-cleaned.

Usage: clean.py <page.md> prints the cleaned text."""
import json, re, sys

VERSION = 1

FENCE = re.compile(r"^\s*(```|~~~)")
EXPORT = re.compile(r"^export\s+(?:default\s+)?(?:function|const|let)\s+\w+")
SHARE = re.compile(r"(https://console\.typesafe\.ai/playground)#share/[^\"'\s)>]+")
SIG = re.compile(r"<SdkSignature>(.*?)</SdkSignature>", re.S)
SIGSTR = re.compile(r'\{"((?:[^"\\]|\\.)*)"\}')
IMG = re.compile(r"<img\b[^>]*>")
ALT = re.compile(r'\balt="([^"]*)"')
END = re.compile(r"^[)}\]]+;?\s*$")
HEADING = re.compile(r"^#{1,6}\s")
HTML_HEAD = re.compile(r'<h([1-6])\b([^>]*)>(.*?)</h\1>', re.S)
ID_ATTR = re.compile(r'\bid="([A-Za-z_][\w]*(?:\.[\w]+)+)"')
CODEISH = re.compile(r"^\s*(?:export |import |const |let |function |return\b|[)}\]]+;?\s*$)|=>|className=|style=\{\{|<svg\b")


def fences(lines):
    """True for each line that is a fence line or sits inside a code fence."""
    out, inside = [], False
    for ln in lines:
        if FENCE.match(ln):
            out.append(True)
            inside = not inside
        else:
            out.append(inside)
    return out


def _drop_exports(lines):
    """Drop column-0 export blocks outside fences. A block ends at its first END line; if a fence, a Markdown
    heading or the end of the page comes first, the block is kept whole (the build check will flag it)."""
    f, out, i = fences(lines), [], 0
    while i < len(lines):
        if not f[i] and EXPORT.match(lines[i]):
            if lines[i].rstrip().endswith(";"):
                i += 1
                continue
            j = i + 1
            while j < len(lines) and not f[j] and not HEADING.match(lines[j]) and not END.match(lines[j]):
                j += 1
            if j < len(lines) and not f[j] and END.match(lines[j]):
                i = j + 1
                continue
        out.append(lines[i])
        i += 1
    return out


def _sig(m):
    parts = []
    for s in SIGSTR.findall(m.group(1)):
        try:
            parts.append(json.loads('"' + s + '"'))
        except Exception:
            parts.append(s)
    return "```python\n" + "".join(parts).strip("\n") + "\n```"


def _img(m):
    tag = m.group(0)
    if "dark:block" in tag:  # the dark-theme twin of the image before it
        return ""
    a = ALT.search(tag)
    return "[image: %s]" % a.group(1) if a and a.group(1).strip() else ""


def _head(m):
    ident = ID_ATTR.search(m.group(2))
    text = ident.group(1) if ident else " ".join(re.sub(r"<[^>]+>", "", m.group(3)).split()).replace("\\_", "_")
    return "#" * int(m.group(1)) + " " + text


def _outside_fences(lines, fn):
    """Apply fn to each run of lines outside code fences; fenced lines pass through unchanged."""
    out, buf = [], []
    for ln, inside in zip(lines, fences(lines)):
        if inside:
            if buf:
                out.append(fn("\n".join(buf)))
                buf = []
            out.append(ln)
        else:
            buf.append(ln)
    if buf:
        out.append(fn("\n".join(buf)))
    return "\n".join(out)


def code_shaped(lines):
    """Count lines outside code fences that look like site code."""
    return sum(1 for ln, inside in zip(lines, fences(lines)) if not inside and CODEISH.search(ln))


def clean(text):
    t = "\n".join(_drop_exports(text.split("\n")))
    t = _outside_fences(t.split("\n"), lambda s: SIG.sub(_sig, SHARE.sub(r"\1", s)))
    return _outside_fences(t.split("\n"), lambda s: HTML_HEAD.sub(_head, IMG.sub(_img, s)))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: clean.py <page.md>")
    sys.stdout.write(clean(open(sys.argv[1], encoding="utf-8").read()))
