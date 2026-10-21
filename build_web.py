#!/usr/bin/env python3
"""Build the browser version: web/template.html + game data -> web/index.html.

The browser game reads the same story chapters, jobs, art, shop and word
lists as the Python game, so content only has to be written once.
Run this after changing anything in netrunner/data or the data modules.
"""
import base64
import glob
import json
import os
import re

from netrunner import art, board, locks, shop

ROOT = os.path.dirname(os.path.abspath(__file__))


def main():
    story = {}
    for path in glob.glob(os.path.join(ROOT, "netrunner", "data", "story", "chapter*.json")):
        n = int(re.search(r"chapter(\d+)", path).group(1))
        with open(path) as f:
            story[n] = json.load(f)
    with open(board.JOBS_PATH) as f:
        jobs = json.load(f)
    data = {
        "art": {k: v for k, v in vars(art).items() if k.isupper()},
        "story": story,
        "jobs": jobs,
        "upgrades": shop.UPGRADES,
        "corps": board.CORPS, "handles": board.HANDLES, "loot": board.LOOT,
        "logs": board.LOGS, "junk": board.JUNK,
        "words": locks.WORDS,
    }
    with open(os.path.join(ROOT, "web", "template.html")) as f:
        page = f.read()
    blob = json.dumps(data).replace("</", "<\\/")
    page = page.replace("/*__DATA__*/null", blob)
    snap_path = os.path.join(ROOT, "web", "feeds_snapshot.json")
    snap = "null"
    if os.path.exists(snap_path):
        with open(snap_path) as f:
            snap = json.dumps(json.load(f)).replace("</", "<\\/")
    page = page.replace("/*__FEEDS__*/null", snap)
    with open(os.path.join(ROOT, "web", "index.html"), "w") as f:
        f.write(page)
    write_standalone(page)
    print(f"wrote web/index.html ({len(page) // 1024} KB, {len(story)} chapter(s), {len(jobs)} jobs)")


STANDALONE_HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#0b0f0a">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3E%3Crect width='16' height='16' rx='3' fill='%23031006'/%3E%3Ctext x='2' y='12' font-family='monospace' font-size='11' fill='%2333ff66'%3E%3E_%3C/text%3E%3C/svg%3E">
<style>
FONTFACES
html, body { margin: 0; }
</style>
"""


# Terminal-theme fonts, inlined so the download works offline (all SIL OFL,
# except Ubuntu Mono: Ubuntu Font Licence; both allow redistribution).
FONTS = {
    "VT323": "VT323-latin.woff2",
    "IBM Plex Mono": "IBMPlexMono-latin.woff2",
    "Source Code Pro": "SourceCodePro-latin.woff2",
    "Fira Code": "FiraCode-latin.woff2",
    "Ubuntu Mono": "UbuntuMono-latin.woff2",
    "Press Start 2P": "PressStart2P-latin.woff2",
    "Cascadia Mono": "CascadiaMono-latin.woff2",
}


def write_standalone(page):
    """dist/netrunner86.html: one file that runs offline when double-clicked."""
    faces = []
    for family, filename in FONTS.items():
        with open(os.path.join(ROOT, "web", "fonts", filename), "rb") as f:
            data = base64.b64encode(f.read()).decode()
        faces.append(f'@font-face {{ font-family: "{family}"; font-style: normal; font-weight: 400; font-display: swap;\n'
                     f'  src: url(data:font/woff2;base64,{data}) format("woff2"); }}')
    page = re.sub(r'<link rel="(preconnect|stylesheet)" href="https://fonts[^>]*>\n', "", page)
    head, sep, body = page.partition("</style>")
    out = STANDALONE_HEAD.replace("FONTFACES", "\n".join(faces)) + head + sep + "\n</head>\n<body>" + body + "</body>\n</html>\n"
    os.makedirs(os.path.join(ROOT, "dist"), exist_ok=True)
    with open(os.path.join(ROOT, "dist", "netrunner86.html"), "w") as f:
        f.write(out)


if __name__ == "__main__":
    main()
