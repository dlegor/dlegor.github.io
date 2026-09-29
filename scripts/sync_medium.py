#!/usr/bin/env python3
"""Sync the latest Medium posts into the Blog section of index.html.

Fetches the public Medium RSS feed and rewrites the HTML between the
<!-- MEDIUM:START --> and <!-- MEDIUM:END --> markers with post cards.
On any network or parse error the page is left untouched, so a Medium
outage never empties the Blog section.

Usage: python3 scripts/sync_medium.py [--feed FILE_OR_URL]
Stdlib only, so it runs in GitHub Actions without installing anything.
"""

import argparse
import html
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from pathlib import Path

FEED_URL = "https://medium.com/feed/@d.legorreta.anguiano"
PAGE = Path(__file__).resolve().parent.parent / "index.html"
MAX_POSTS = 6
EXCERPT_CHARS = 200
START, END = "<!-- MEDIUM:START -->", "<!-- MEDIUM:END -->"
NS = {"content": "http://purl.org/rss/1.0/modules/content/"}
INDENT = "\t\t\t\t\t"


def fetch(source):
    if not source.startswith("http"):
        return Path(source).read_bytes()
    req = urllib.request.Request(source, headers={
        "User-Agent": "Mozilla/5.0 (compatible; dlegor.github.io medium-sync)",
        "Accept": "application/rss+xml, application/xml;q=0.9, */*;q=0.8",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def clean_text(fragment):
    text = re.sub(r"<(figure|figcaption)\b.*?</\1>", " ", fragment, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", html.unescape(text)).strip()
    if len(text) > EXCERPT_CHARS:
        text = text[:EXCERPT_CHARS].rsplit(" ", 1)[0].rstrip(",.;:") + "…"
    return text


def parse(xml_bytes):
    posts = []
    for item in ET.fromstring(xml_bytes).iter("item"):
        body = item.findtext("content:encoded", default="", namespaces=NS) \
            or item.findtext("description", default="")
        img = re.search(r'<img[^>]+src="([^"]+)"', body)
        # Medium adds a 1x1 tracking pixel (…/_/stat?event=…); ignore it.
        thumb = img.group(1) if img and "/_/stat" not in img.group(1) else ""
        pub = item.findtext("pubDate")
        posts.append({
            "title": (item.findtext("title") or "").strip(),
            "link": (item.findtext("link") or "").split("?")[0],
            "date": parsedate_to_datetime(pub) if pub else None,
            "thumb": thumb,
            "excerpt": clean_text(body),
            "tags": [c.text for c in item.findall("category") if c.text][:3],
        })
    return [p for p in posts if p["title"] and p["link"]][:MAX_POSTS]


def render(posts):
    e = lambda s: html.escape(s, quote=True)
    out = [f'{INDENT}<div class="post-grid">']
    for p in posts:
        out.append(f'{INDENT}\t<article class="post-card">')
        if p["thumb"]:
            out.append(f'{INDENT}\t\t<a href="{e(p["link"])}" class="post-thumb" tabindex="-1" aria-hidden="true">'
                       f'<img src="{e(p["thumb"])}" alt="" loading="lazy" referrerpolicy="no-referrer" /></a>')
        meta = []
        if p["date"]:
            meta.append(f'<time datetime="{p["date"]:%Y-%m-%d}">{p["date"]:%b} {p["date"].day}, {p["date"].year}</time>')
        meta += [f'<span class="post-tag">{e(t)}</span>' for t in p["tags"]]
        out.append(f'{INDENT}\t\t<p class="post-meta">{" ".join(meta)}</p>')
        out.append(f'{INDENT}\t\t<h3><a href="{e(p["link"])}">{e(p["title"])}</a></h3>')
        if p["excerpt"]:
            out.append(f'{INDENT}\t\t<p class="post-excerpt">{e(p["excerpt"])}</p>')
        out.append(f'{INDENT}\t</article>')
    out.append(f'{INDENT}</div>')
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--feed", default=FEED_URL, help="feed URL or local XML file")
    args = ap.parse_args()

    try:
        posts = parse(fetch(args.feed))
    except Exception as exc:  # network, HTTP or XML errors: keep the page as is
        print(f"medium-sync: could not read feed ({exc}); leaving page unchanged", file=sys.stderr)
        return 0
    if not posts:
        print("medium-sync: feed has no posts; leaving page unchanged", file=sys.stderr)
        return 0

    page = PAGE.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    if not pattern.search(page):
        print(f"medium-sync: markers not found in {PAGE.name}", file=sys.stderr)
        return 1
    block = f"{START}\n{render(posts)}\n{INDENT}{END}"
    updated = pattern.sub(lambda _: block, page, count=1)
    if updated != page:
        PAGE.write_text(updated, encoding="utf-8")
        print(f"medium-sync: wrote {len(posts)} posts to {PAGE.name}")
    else:
        print("medium-sync: already up to date")
    return 0


if __name__ == "__main__":
    sys.exit(main())
