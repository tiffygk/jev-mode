#!/usr/bin/env python3
"""Download every page TypeSafe lists in llms.txt into the data folder: docs/, cookbooks/, patterns/.
A page that fails (404, rate limit) is named and skipped; the run carries on. Exit 1 if any failed."""
import datetime, os, re, sys, time, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import CODE, DATA

BASE = "https://docs.typesafe.ai/"


def get(url, tries=3):
    for n in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "jev-sources"})
            return urllib.request.urlopen(req, timeout=30).read().decode("utf-8")
        except urllib.error.HTTPError as e:
            if e.code != 429 or n == tries - 1:
                raise
            time.sleep(2 * (n + 1))


def dest(slug):
    for kind in ("cookbooks", "patterns"):
        if slug.startswith(kind + "/"):
            return os.path.join(DATA, kind, slug[len(kind) + 1:] + ".md")
    return os.path.join(DATA, "docs", slug.replace("/", "__") + ".md")


def main():
    try:
        slugs = sorted(set(re.findall(r"https://docs\.typesafe\.ai/([^)\s]+?)\.md", get(BASE + "llms.txt"))))
    except Exception as e:
        sys.exit(f"fetch: could not read llms.txt ({e})")
    extra = [u.strip()[len(BASE):-3] for u in open(os.path.join(CODE, "scripts", "urls.txt")) if u.strip().startswith(BASE)]
    slugs += [s for s in extra if s not in slugs]
    stamp = datetime.date.today().isoformat()
    failed = []
    for slug in slugs:
        try:
            text = get(BASE + slug + ".md")
        except Exception as e:
            failed.append(f"{slug} ({e})")
            continue
        path = dest(slug)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"<!-- saved {stamp} from {BASE}{slug}.md -->\n\n{text}")
    print(f"fetched {len(slugs) - len(failed)} of {len(slugs)} pages into {DATA}")
    for x in failed:
        print(f"fetch failed: {x}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
