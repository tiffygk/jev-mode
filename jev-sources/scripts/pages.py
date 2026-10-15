#!/usr/bin/env python3
"""Which pages TypeSafe publishes now, and when each library copy was saved.
live_pages(): the sitemap and llms.txt together, slug -> sitemap date (None when only llms.txt or urls.txt lists it).
Saved pages start with '<!-- saved 2026-10-14T21:07:12Z from <url> -->'; copies saved before 2026-10-14 carry the date only."""
import datetime, hashlib, os, re, shutil, sys, time, urllib.error, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import CODE, DATA

BASE = "https://docs.typesafe.ai/"
UTC = datetime.timezone.utc
HEADER = re.compile(r"^<!-- saved (\d{4}-\d{2}-\d{2})(?:T(\d{2}:\d{2}:\d{2})Z)? from \S+ -->")
SKIP = ("docs/cookbooks__", "docs/patterns__")  # old MDX duplicates of cookbooks/ and patterns/


class Gone(Exception):
    """404, or a redirect to a different page (.moved_to is its slug)."""
    def __init__(self, url, moved_to=None):
        super().__init__(url)
        self.moved_to = moved_to


SAFE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*(/[A-Za-z0-9][A-Za-z0-9_.-]*)*$")  # no "..", no empty or hidden parts
MAX_BYTES = 5000000  # a docs page or post is well under 1 MB; anything over this is a broken or hostile server


def safe(slug):
    """A page name from TypeSafe's lists is used as a file path: only plain names pass."""
    return bool(SAFE.match(slug))


def slug_of_url(u):
    s = u.split("#")[0].split("?")[0]
    s = s[len(BASE):] if s.startswith(BASE) else s
    s = s[:-3] if s.endswith(".md") else s
    return s.strip("/")


def get(url, tries=3):
    for n in range(tries):
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "jev-sources"}), timeout=30)
            if slug_of_url(r.geturl()) != slug_of_url(url):
                raise Gone(url, slug_of_url(r.geturl()))
            body = r.read(MAX_BYTES + 1)
            if len(body) > MAX_BYTES:
                raise ValueError(f"{url} is over {MAX_BYTES} bytes")
            return body.decode("utf-8")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise Gone(url)
            if e.code != 429 or n == tries - 1:
                raise
            time.sleep(2 * (n + 1))


def parse_llms(text):
    return {s for s in re.findall(r"https://docs\.typesafe\.ai/([^)\s]+?)\.md", text) if safe(s)}


def parse_time(s):
    s = s.strip()
    try:
        return datetime.datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=UTC)
    except ValueError:
        return datetime.datetime.strptime(s[:10], "%Y-%m-%d").replace(tzinfo=UTC)


def parse_sitemap(xml):
    out = {}
    for block in re.findall(r"<url>(.*?)</url>", xml, re.S):
        loc = re.search(r"<loc>\s*([^<\s]+)\s*</loc>", block)
        slug = slug_of_url(loc.group(1)) if loc else ""
        if slug and safe(slug):
            lm = re.search(r"<lastmod>\s*([^<\s]+)\s*</lastmod>", block)
            out[slug] = parse_time(lm.group(1)) if lm else None
    return out


def extras():
    p = os.path.join(CODE, "scripts", "urls.txt")
    return [s for s in (slug_of_url(u.strip()) for u in open(p) if u.strip().startswith(BASE)) if safe(s)] if os.path.exists(p) else []


def live_pages(fetch=None):
    fetch = fetch or get  # looked up at call time so tests can patch pages.get
    found, errors, read = {}, [], set()
    try:
        xml = fetch(BASE + "sitemap.xml")
        if "<url>" not in xml:  # a sitemap index or an error page served as 200 holds no pages and no dates
            raise ValueError("no <url> entries")
        found.update(parse_sitemap(xml))
        read.add("sitemap")
    except Exception as e:
        errors.append(f"sitemap.xml ({e})")
    try:
        for s in parse_llms(fetch(BASE + "llms.txt")):
            found.setdefault(s, None)
        read.add("llms")
    except Exception as e:
        errors.append(f"llms.txt ({e})")
    if not read:
        raise RuntimeError("could not read " + " or ".join(errors))
    for s in extras():
        found.setdefault(s, None)
    return found, read


def dest(slug):
    for kind in ("cookbooks", "patterns"):
        if slug.startswith(kind + "/"):
            path = os.path.join(DATA, kind, slug[len(kind) + 1:] + ".md")
            break
    else:
        path = os.path.join(DATA, "docs", slug.replace("/", "__") + ".md")
    root = os.path.realpath(DATA)
    if not os.path.realpath(path).startswith(root + os.sep):  # a page is never written outside the library
        raise ValueError(f"page name {slug!r} points outside the library")
    return path


def slug_of_path(rel):
    rel = rel.replace(os.sep, "/")
    kind, name = rel.split("/", 1)
    name = name[:-3] if name.endswith(".md") else name
    return name.replace("__", "/") if kind == "docs" else f"{kind}/{name}"


def library(data=None):
    out = {}
    for kind in ("docs", "cookbooks", "patterns"):
        d = os.path.join(data or DATA, kind)
        for f in sorted(os.listdir(d)) if os.path.isdir(d) else []:
            rel = f"{kind}/{f}"
            if f.endswith(".md") and not rel.startswith(SKIP) and f != "extract.md" and not f.endswith(".raw.md"):
                out[slug_of_path(rel)] = os.path.join(d, f)
    return out


def stamp(now=None):
    return (now or datetime.datetime.now(UTC)).strftime("%Y-%m-%dT%H:%M:%SZ")


def saved_at(path):
    try:
        m = HEADER.match(open(path, encoding="utf-8").readline())
    except OSError:
        return None
    if not m:
        return None
    return datetime.datetime.strptime(m.group(1) + "T" + (m.group(2) or "00:00:00"), "%Y-%m-%dT%H:%M:%S").replace(tzinfo=UTC)


def body(path):
    text = open(path, encoding="utf-8").read()
    if HEADER.match(text):
        text = text.split("\n", 1)[1] if "\n" in text else ""
        if text.startswith("\n"):
            text = text[1:]
    return text


def digest(text):
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()


def write_page(slug, text, now=None):
    path = dest(slug)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"<!-- saved {stamp(now)} from {BASE}{slug}.md -->\n\n{text}")
    return path


def touch(path, now=None):
    slug = slug_of_path(os.path.relpath(path, DATA))
    write_page(slug, body(path), now)


def archive(path, reason, now=None):
    """Moves the page to archive/<UTC time of this run>/<reason>/; one folder per run, so a second run the same day
    never overwrites the first run's copies."""
    rel = os.path.relpath(path, DATA)
    to = os.path.join(DATA, "archive", (now or datetime.datetime.now(UTC)).strftime("%Y-%m-%dT%H%M%SZ"), reason, rel)
    os.makedirs(os.path.dirname(to), exist_ok=True)
    shutil.move(path, to)
    return to
