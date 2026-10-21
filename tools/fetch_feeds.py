#!/usr/bin/env python3
"""Fetch the news feeds for the game's NEWSFEED window (stdlib only).

Writes one JSON file per feed to --out (default ./feeds_out), shaped like
the page's database documents: {"name", "fetchedAt", "items": [{"title",
"link", "when"}]}. The scheduled refresh stores them in the artifact's
`feeds` collection, which the online game reads. Keep FEEDS in step with
FEEDS in the RSS block of web/template.html.
"""
import argparse
import email.utils
import json
import os
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

FEEDS = {
    "hn": ("Hacker News: front page", "https://hnrss.org/frontpage"),
    "hackaday": ("Hackaday", "https://hackaday.com/blog/feed/"),
    "retro": ("r/retrocomputing", "https://www.reddit.com/r/retrocomputing/.rss"),
    "krebs": ("Krebs on Security", "https://krebsonsecurity.com/feed/"),
    "reg": ("The Register: security", "https://www.theregister.com/security/headlines.atom"),
    "ars": ("Ars Technica", "https://feeds.arstechnica.com/arstechnica/index"),
    "lobsters": ("Lobsters", "https://lobste.rs/rss"),
}


def local(tag):
    return tag.rsplit("}", 1)[-1]


def when_ms(text):
    if not text:
        return None
    text = text.strip()
    try:
        return int(email.utils.parsedate_to_datetime(text).timestamp() * 1000)
    except (TypeError, ValueError):
        pass
    try:
        return int(datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp() * 1000)
    except ValueError:
        return None


def parse(xml_bytes, limit=30):
    root = ET.fromstring(xml_bytes)
    items = []
    for node in root.iter():
        if local(node.tag) not in ("item", "entry"):
            continue
        title, link, when = "", "", None
        for child in node:
            name = local(child.tag)
            if name == "title":
                title = (child.text or "").strip()
            elif name == "link" and not link:
                link = (child.get("href") or child.text or "").strip()
            elif name in ("pubDate", "published", "updated", "date") and when is None:
                when = when_ms(child.text)
        if not link.startswith(("http://", "https://")):
            link = ""
        items.append({"title": title[:300] or "(untitled)", "link": link, "when": when})
    items.sort(key=lambda i: i["when"] or 0, reverse=True)
    return items[:limit]


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (NETRUNNER86 news relay)"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="feeds_out")
    ap.add_argument("--snapshot", help="also merge the feeds into this JSON file "
                    "(web/feeds_snapshot.json), the saved copy build_web.py puts in the download")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    ok = 0
    fresh = {}
    for fid, (name, url) in FEEDS.items():
        try:
            items = parse(fetch(url))
        except Exception as e:  # one bad feed must not stop the others
            print(f"FAIL {fid}: {e}", file=sys.stderr)
            continue
        if not items:
            print(f"FAIL {fid}: no items", file=sys.stderr)
            continue
        doc = {"name": name, "fetchedAt": int(time.time() * 1000), "items": items}
        with open(os.path.join(args.out, fid + ".json"), "w") as f:
            json.dump(doc, f)
        fresh[fid] = doc
        ok += 1
        print(f"OK   {fid}: {len(items)} items")
    print(f"{ok}/{len(FEEDS)} feeds written to {args.out}")
    if args.snapshot and fresh:
        try:
            with open(args.snapshot) as f:
                snap = json.load(f)
        except (OSError, ValueError):
            snap = {}
        snap.update(fresh)  # a feed that failed this time keeps its last good copy
        with open(args.snapshot, "w") as f:
            json.dump(snap, f)
        print(f"snapshot updated: {args.snapshot}")


if __name__ == "__main__":
    main()
