#!/usr/bin/env python3
"""Which pages TypeSafe publishes now, and when each library copy was saved.
live_pages(): the sitemap and llms.txt together, slug -> sitemap date (None when only llms.txt or urls.txt lists it).
Saved pages start with '<!-- saved 2026-10-14T21:07:12Z from <url> -->'; copies saved before 2026-10-14 carry the date only.
Every page is kept twice: raw/<kind>/<file>.md as TypeSafe served it (change detection reads this copy), and the cleaned
copy where pages live (indexed and read). The cleaned header adds '| cleaner <version>' ('| cleaner failed <version>'
when cleaning raised and the cleaned copy holds the raw text)."""
import datetime, hashlib, json, os, re, shutil, sys, time, urllib.error, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import CODE, DATA
import clean

BASE = "https://docs.typesafe.ai/"
UTC = datetime.timezone.utc
HEADER = re.compile(r"^<!-- saved (\d{4}-\d{2}-\d{2})(?:T(\d{2}:\d{2}:\d{2})Z)? from \S+(?: \| cleaner (failed )?(\d+))? -->")
FROM_URL = re.compile(r"^<!-- saved \S+ from (\S+)")
LOCK, NEEDS_RAW = os.path.join(DATA, "check.lock"), os.path.join(DATA, "needs_raw.json")
FAILED_NOW = set()  # slugs whose cleaning raised in this process: the build names them once
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


def _place(slug, top):
    for kind in ("cookbooks", "patterns"):
        if slug.startswith(kind + "/"):
            folder, name = kind, slug[len(kind) + 1:] + ".md"
            break
    else:
        folder, name = "docs", slug.replace("/", "__") + ".md"
    path = os.path.join(top, folder, name)
    real = os.path.realpath(path)
    # a page is never written outside the library, nor outside its own kind folder (raw/ links out of the library count)
    if not (real.startswith(os.path.realpath(DATA) + os.sep) and real.startswith(os.path.realpath(os.path.join(top, folder)) + os.sep)):
        raise ValueError(f"page name {slug!r} points outside the library")
    return path


def dest(slug):
    return _place(slug, DATA)


def raw_dest(slug):
    """Where the page as served is kept: <data>/raw/<kind>/<file>.md, mirroring the cleaned page's path."""
    return _place(slug, os.path.join(DATA, "raw"))


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


def _strip_header(text):
    if HEADER.match(text):
        text = text.split("\n", 1)[1] if "\n" in text else ""
        if text.startswith("\n"):
            text = text[1:]
    return text


def raw_text(path):
    """The text as served for a library page (path is its cleaned copy), or None when it has no raw copy."""
    try:
        with open(raw_dest(slug_of_path(os.path.relpath(path, DATA))), encoding="utf-8", newline="") as f:
            return _strip_header(f.read())
    except OSError:
        return None


def cleaner_of(path):
    """The cleaner version in a page's header: an int, "failed:<n>", or None when the header has no cleaner field."""
    try:
        m = HEADER.match(open(path, encoding="utf-8").readline())
    except OSError:
        return None
    if not m or not m.group(4):
        return None
    return f"failed:{m.group(4)}" if m.group(3) else int(m.group(4))


def _atomic_write(path, data):
    """A temp file in the same folder, then os.replace: a crash leaves the old file or the new one, never half."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = os.path.join(os.path.dirname(path), f".{os.path.basename(path)}.{os.getpid()}.tmp")
    try:
        with open(tmp, "wb") as f:
            f.write(data.encode("utf-8") if isinstance(data, str) else data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise


def _cleaned(text, slug):
    """(cleaned text, header tag). A cleaner that raises leaves the raw text and the tag 'cleaner failed <version>'."""
    try:
        return clean.clean(text), f"cleaner {clean.VERSION}"
    except Exception as e:
        FAILED_NOW.add(slug)
        print(f"NOTICE: could not clean {os.path.relpath(dest(slug), DATA).replace(os.sep, '/')} ({type(e).__name__}: {e})")
        return text, f"cleaner failed {clean.VERSION}"


def _write_cleaned(slug, saved, url, text):
    out, tag = _cleaned(text, slug)
    _atomic_write(dest(slug), f"<!-- saved {saved} from {url} | {tag} -->\n\n{out}")


def write_page(slug, text, now=None):
    """Raw copy first, then the cleaned one, each an atomic replace, both under the same saved time."""
    path, raw_path = dest(slug), raw_dest(slug)  # both guarded before anything is written
    saved, url = stamp(now), f"{BASE}{slug}.md"
    _atomic_write(raw_path, f"<!-- saved {saved} from {url} -->\n\n{text}")
    _write_cleaned(slug, saved, url, text)
    return path


def touch(path, now=None):
    """The text is unchanged: both copies are rewritten from the raw text under the new saved time."""
    slug = slug_of_path(os.path.relpath(path, DATA))
    text = raw_text(path)
    if text is None:
        raise FileNotFoundError(f"no raw copy of {slug}")
    write_page(slug, text, now)


def archive(path, reason, now=None):
    """Moves the page, and its raw copy, to archive/<UTC time of this run>/<reason>/ (raw under raw/<kind>/); one
    folder per run, so a second run the same day never overwrites the first run's copies."""
    rel = os.path.relpath(path, DATA)
    run = os.path.join(DATA, "archive", (now or datetime.datetime.now(UTC)).strftime("%Y-%m-%dT%H%M%SZ"), reason)
    raw = raw_dest(slug_of_path(rel))
    if os.path.exists(raw):
        os.makedirs(os.path.dirname(os.path.join(run, "raw", rel)), exist_ok=True)
        shutil.move(raw, os.path.join(run, "raw", rel))
    to = os.path.join(run, rel)
    os.makedirs(os.path.dirname(to), exist_ok=True)
    shutil.move(path, to)
    return to


def take_lock():
    """True when this run owns the lock: created with O_EXCL, or a stale lock (over an hour old) replaced."""
    os.makedirs(DATA, exist_ok=True)
    for _ in range(2):
        try:
            os.close(os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
            return True
        except FileExistsError:
            try:
                if time.time() - os.path.getmtime(LOCK) < 3600:
                    return False
                os.remove(LOCK)
            except OSError:
                return False
    return False


def drop_lock():
    try:
        os.remove(LOCK)  # only the run that owns the lock gets here
    except OSError:
        pass


def needs_raw():
    """Slugs of cleaned pages with no raw copy, listed by the last prepare(); the next check refetches them."""
    try:
        return list(json.load(open(NEEDS_RAW)))
    except (OSError, ValueError):
        return []


def prepare(locked=False):
    """Brings every library page to the current layout and returns the slugs it rewrote.
    No raw copy, old-style header: the page file is the raw copy, kept byte for byte, then cleaned.
    No raw copy, cleaner header (or no header): never treated as raw; listed in needs_raw.json for a refetch.
    Raw copy and a cleaner version other than clean.VERSION: re-cleaned from raw, saved time kept.
    'cleaner failed <VERSION>': skipped, that version already failed on the page."""
    own = False
    if not locked:
        if not take_lock():
            print("another check is running; pages not re-cleaned")
            return []
        own = True
    try:
        done, needs = [], []
        for slug, path in library().items():
            try:
                raw_path = raw_dest(slug)
                have = os.path.exists(raw_path)
                cl = cleaner_of(path)
                if not have:
                    head = open(path, encoding="utf-8").readline()
                    if not HEADER.match(head) or cl is not None:
                        needs.append(slug)
                        continue
                    _atomic_write(raw_path, open(path, "rb").read())
                elif cl == clean.VERSION or cl == f"failed:{clean.VERSION}":
                    continue
                head = open(raw_path, encoding="utf-8").readline()
                m = HEADER.match(head)
                if not m:
                    needs.append(slug)
                    continue
                saved = m.group(1) + ("T" + m.group(2) + "Z" if m.group(2) else "")
                with open(raw_path, encoding="utf-8", newline="") as f:
                    text = _strip_header(f.read())
                _write_cleaned(slug, saved, FROM_URL.match(head).group(1), text)
                done.append(slug)
            except (OSError, ValueError) as e:  # one unreadable page never stops the others
                print(f"NOTICE: could not prepare {slug} ({e})")
        if needs or os.path.exists(NEEDS_RAW):
            _atomic_write(NEEDS_RAW, json.dumps(sorted(needs)))
        if done:
            print(f"re-cleaned {len(done)} page(s) (cleaner v{clean.VERSION})")
        return done
    finally:
        if own:
            drop_lock()
