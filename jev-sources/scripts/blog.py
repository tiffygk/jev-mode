"""TypeSafe's blog posts: listed in typesafe.ai's sitemap, fetched as HTML, saved as plain text with headings in
<data>/blog/<slug>.txt under the same saved-time header the docs pages use. Indexed as vendor claims.
The live pages have no <article> or <nav> tags: the menu is <p> text inside links, the title is the first <h1>,
the date repeats once per screen size, and the footer starts with a symbol-only or copyright <p>."""
import os, re, sys
from html.parser import HTMLParser
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pages

SITE = "https://typesafe.ai/"
POST = re.compile(r"<loc>\s*https://typesafe\.ai/blog/([a-z0-9][a-z0-9-]*)\s*</loc>")
SKIP_TAGS = {"script", "style", "nav", "header", "footer", "noscript", "svg", "form", "button"}
BLOCK = {"h1": "# ", "h2": "## ", "h3": "### ", "h4": "#### ", "p": "", "li": "- ", "blockquote": "> "}
FOOTER = re.compile(r"^(TypeSafe AI )?©")
REPEATS = 5  # the page repeats the date once per screen size, right after the title; later repeats are the author's
EMPTY = "empty page"
MIN_WORDS = 10  # fewer words than this is an error page or a layout change, not a post


def list_posts(fetch=None):
    fetch = fetch or pages.get
    return sorted(set(POST.findall(fetch(SITE + "sitemap.xml"))))


class _Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip = 0
        self.links = []  # per open <a>: whether it raised skip
        self.block = None
        self.buf = []
        self.out = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":  # menu text is a <p> inside a link; a link inside an open block is part of its sentence
            self.links.append(self.block is None)
            self.skip += self.block is None
        elif tag in SKIP_TAGS:
            self.skip += 1
        elif tag in BLOCK and not self.skip:
            self.block, self.buf = tag, []

    def handle_endtag(self, tag):
        if tag == "a":
            if self.links and self.links.pop() and self.skip:
                self.skip -= 1
        elif tag in SKIP_TAGS and self.skip:
            self.skip -= 1
        elif tag == self.block:
            text = " ".join("".join(self.buf).split())
            if text:
                self.out.append(BLOCK[tag] + text)
            self.block = None

    def handle_data(self, data):
        if self.block and not self.skip:
            self.buf.append(data)


def post_text(page_html):
    p = _Text()
    p.feed(page_html)
    lines = p.out
    first_h1 = next((i for i, l in enumerate(lines) if l.startswith("# ")), 0)
    kept = []
    for line in lines[first_h1:]:
        body = line.lstrip("#-> ")
        if FOOTER.match(body):
            break  # the footer follows the article
        if not re.search(r"\w", body) or (0 < len(kept) <= REPEATS and kept[-1] == line):
            continue  # a symbol-only divider, or the same line repeated for another screen size
        kept.append(line)
    return "\n\n".join(kept).strip()


def dest(slug):
    return os.path.join(pages.DATA, "blog", slug + ".txt")


def save(slug, text, now=None):
    path = dest(slug)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"  # write beside it, then swap, so a failed write never truncates the saved copy
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(f"<!-- saved {pages.stamp(now)} from {SITE}blog/{slug} -->\n{text}\n")
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    return path


DATE_LINE = re.compile(r"^[A-Z][a-z]{2,8}\.? \d{1,2}, \d{4}$")


def body_words(text):
    """Words below the title, leaving out date lines: a video post saves only its title and date (2026-10-14)."""
    lines = [l for l in text.splitlines()[1:] if not DATE_LINE.match(l.strip())]
    return len(" ".join(lines).split())


def fetch_posts(slugs, fetch=None, now=None):
    """Returns (saved slugs, failed as (slug, reason) pairs); reason is "gone", "empty page" or "fetch failed (...)"."""
    fetch = fetch or pages.get
    saved, failed = [], []
    for s in slugs:
        try:
            text = post_text(fetch(SITE + "blog/" + s))
            if body_words(text) < MIN_WORDS:
                failed.append((s, EMPTY))
                continue
            save(s, text, now)
        except pages.Gone:
            failed.append((s, "gone"))
            continue
        except Exception as e:
            failed.append((s, f"fetch failed ({type(e).__name__}: {e})"))
            continue
        saved.append(s)
    return saved, failed
