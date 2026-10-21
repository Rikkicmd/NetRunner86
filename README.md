# NETRUNNER '86

> **The browser version (`web/`, `dist/netrunner86.html`) is the game now.** The
> Python terminal version is frozen and no longer updated; its `netrunner/data`
> files and data constants are still the content source for `build_web.py`.

An 80s-style terminal hacking game. Green-phosphor ASCII graphics, a story to
follow if you want it, and an underground job board if you'd rather freelance.

## Run it

Needs Python 3.8+ and nothing else (no packages to install).

```
cd netrunner86
python3 play.py
```

Use a terminal at least 80 columns wide. Works in macOS Terminal, Linux
terminals, and Windows Terminal / PowerShell (on Windows use `python` or `py`
instead of `python3`). Set `NR_FAST=1` to skip the typewriter effect.

## Play in a browser

`web/index.html` is a browser version of the same game (one self-contained
page, saves kept in the browser). It is published at
https://claude.ai/artifact/UeEe9UxHu8UTVzHPbLmmxZ, and you can also open the
file directly in any browser or put it on any static host (GitHub Pages, itch.io).

The browser version reads the same story chapters, jobs, art and shop data as
the Python version. After changing content, rebuild it with
`python3 build_web.py`. Game logic lives in `web/template.html`; when you add
a feature to the Python game, port it there too.

### Downloadable offline version

`dist/netrunner86.html` is the whole game in one file, with the font built in,
so it runs with no internet connection. Double-click it to play in your
browser, or share the file with anyone. `python3 build_web.py` rebuilds it
along with `web/index.html`. The terminal font is VT323 (SIL Open Font License).

### Side panel

The browser versions have a side panel (a tab strip above the prompt on
phones, with a HIDE button):
* **MAP** - live ASCII diagram of the job's network: hosts appear as you
  scan or connect, with lock/root state and packets crawling along the live link.
* **TRACE** - radar sweep; the blip closing in on the centre is the sysop.
  The tab label shows the live percentage and turns red above 70%.
* **NOTES** - auto-collects scanned hosts, plus likely passwords ('quoted words')
  and IPs from files you `cat`. Add your own with `note <text>`. Saved per handle.

It is the `Panel` block in `web/template.html`; the shell calls
`Panel.begin/update/end`.

### Music and themes

* **Music player** (main menu `M`): four original chiptune tracks synthesised
  live with Web Audio (no audio files): CARRIER DETECT, ICE BREAKER,
  MIDNIGHT BBS, TRACE ALERT. Each is plain data in the `TRACKS` list of the
  `Music` block in `web/template.html` (chords, melody, tempo, drum pattern);
  add one there and it appears in the player. The game opens on a "press any
  key to power on" screen because browsers block sound until the player
  interacts. MUSIC mutes, `>>` skips to the next track; both are remembered.
* **Terminal themes** (main menu `T`): Green phosphor, Amber, IBM PC, Linux TTY,
  Parrot OS, Ubuntu, ZX Spectrum, Windows CMD, PowerShell. Each is a block of CSS tokens (`:root[data-skin=...]`)
  plus an entry in `SKINS`. Fonts live in `web/fonts/` and are inlined into the
  offline download by `build_web.py` (`FONTS`).

### Desktop window mode

By default the game runs in a window on a desktop that matches the theme
(synthwave grid for green/amber, a dithered GEM-style desk for IBM PC, the
rainbow stripes for ZX Spectrum, a teal 95-style desktop for CMD, a blue
light-beam desktop for PowerShell, and so on), with icons, a taskbar and a
1986 clock. **T) Themes & screen -> W** switches back to the full-screen
monitor. Each theme's window style, title and start button are in `CHROME`
in the `Desktop` block of `web/template.html`, with the matching
`:root[data-chrome=...]` CSS.

### News feed window (RSS)

Main menu `N`, or the NEWSFEED desktop icon, opens a window you can drag by
its title bar and resize from the corner. Pick a feed from the list: an
in-game 1986 NEWSWIRE (always works, offline too), Hacker News, Hackaday,
r/retrocomputing, Krebs on Security, The Register security, Ars Technica,
Lobsters, or add your own RSS/Atom URL.

* **Online (claude.ai)** the page can't connect to other sites, so the
  built-in feeds come from the artifact's database (`feeds/<id>` documents).
  An hourly scheduled job runs `tools/fetch_feeds.py` in the "RSS Sites"
  cloud environment and stores the results there. Your own added feeds
  don't work online.
* **Downloaded file** fetches each feed directly from the site every 10
  minutes; if the site doesn't allow that, it goes through the public relay
  api.allorigins.win. The list is `FEEDS` in the
`RSS` block of `web/template.html`.

### CRT effects and cutscenes

* **CRT effects**: the screen powers on (a line opening into the picture) on
  the first key press and powers off on Log off; glitches hit when you get
  traced, fail a crack or a login, or the trace passes 70% and 90%. The curved
  glass, rolling band and phosphor afterglow can be switched off under
  **T) Themes & screen -> C**. All of it is the `CRT` block plus the
  "CRT effects" CSS in `web/template.html`; reduced-motion users get none of
  the motion.
* **Cutscenes**: short animated ASCII scenes (`MODEM`, `RING`, `TOWER`,
  `BASILISK`) in the `Cutscene` block. A story scene plays one first when it
  has `"cutscene": "NAME"` in its chapter JSON. Any key or tap skips. Sound
  effects play only while the music is on.

## How to play

* **Story mode** - Chapter 1 "Carrier Detect": a mysterious contact called
  CASSANDRA pulls you into a conspiracy at Omnidyne Systems.
* **Job board** - open-world contracts. Four hand-written jobs (two locked
  behind reputation) plus endless randomly generated ones. Pay `R` to refresh.
* **Rig upgrades** - spend credits on a faster modem (less trace per command)
  and better cracking software (more attempts per lock).
* **Dossier** - your stats. `T` toggles green/amber monitor colours.

Inside a job you're at a shell. `help` lists commands; the core loop is
`scan` -> `connect <ip>` -> `crack` (or `login <password>` if you found one)
-> `ls` / `cat` / `get` / `put` / `rm` -> `dc`. Every command while connected
raises the TRACE meter in your prompt. Hit 100% and you're caught: you lose a
quarter of your credits and some rep.

Two lock minigames:
* **Keypad** - guess the code. `*` right digit right slot, `+` right digit wrong slot.
* **Memory dump** - pick the password from a hex dump; "likeness" is how many
  letters are in the right position.

## Project layout (where to add things)

| File | What it holds |
| --- | --- |
| `netrunner/data/story/chapterN.json` | Story chapters. Add `chapter2.json` and it's playable. |
| `netrunner/data/jobs.json` | Hand-written job board contracts. |
| `netrunner/board.py` | Job board + random job generator (corp names, loot, etc.). |
| `netrunner/shell.py` | The hacking shell. Mission format is documented at the top. |
| `netrunner/locks.py` | Lock minigames. Add a function to `LOCKS`, then use it as `"lock"` on a host. |
| `netrunner/shop.py` | Rig upgrades. |
| `netrunner/art.py` | ASCII art. Reference by name in story scenes (`"art": "TERMINAL"`). |
| `netrunner/ui.py` | Colours, boxes, typewriter effect, themes. |
| `saves/` | One JSON save per handle. |

Tests: `python3 -m unittest discover tests`
