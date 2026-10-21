"""Retro terminal rendering: green-phosphor colours, typewriter text, boxes.

Everything visual goes through this module so the look can be re-skinned
(amber monitor, CGA, etc.) in one place.
"""
import os
import shutil
import sys
import time

# Enable ANSI escape handling on Windows 10+ consoles.
if os.name == "nt":
    os.system("")

THEMES = {
    "green": {"fg": "\033[32m", "hi": "\033[92m", "dim": "\033[2;32m"},
    "amber": {"fg": "\033[33m", "hi": "\033[93m", "dim": "\033[2;33m"},
}
RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[91m"
CYAN = "\033[96m"

_theme = THEMES["green"]
# NR_FAST=1 skips typewriter delays (handy for testing).
FAST = os.environ.get("NR_FAST") == "1"


def set_theme(name):
    global _theme
    _theme = THEMES.get(name, THEMES["green"])


def fg(text):
    return f"{_theme['fg']}{text}{RESET}"


def hi(text):
    return f"{_theme['hi']}{BOLD}{text}{RESET}"


def dim(text):
    return f"{_theme['dim']}{text}{RESET}"


def alert(text):
    return f"{RED}{BOLD}{text}{RESET}"


def info(text):
    return f"{CYAN}{text}{RESET}"


def width():
    return min(shutil.get_terminal_size((80, 24)).columns, 80)


def clear():
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


def pause(seconds):
    if not FAST:
        time.sleep(seconds)


def type_out(text, delay=0.012, style=fg):
    """Print text one character at a time like an old modem link."""
    for line in text.splitlines() or [""]:
        if FAST:
            print(style(line))
            continue
        for ch in line:
            sys.stdout.write(style(ch))
            sys.stdout.flush()
            time.sleep(delay)
        print()


def say(text="", style=fg):
    for line in text.splitlines() or [""]:
        print(style(line))


def box(lines, title=None, style=fg):
    w = width() - 2
    top = "+" + "-" * w + "+"
    if title:
        label = f"[ {title} ]"
        top = "+--" + label + "-" * (w - 2 - len(label)) + "+"
    print(style(top))
    for line in lines:
        print(style("|") + " " + line + " " * max(0, w - 1 - visible_len(line)) + style("|"))
    print(style("+" + "-" * w + "+"))


def visible_len(s):
    """Length of a string ignoring ANSI escape codes."""
    out, i = 0, 0
    while i < len(s):
        if s[i] == "\033":
            while i < len(s) and s[i] != "m":
                i += 1
        else:
            out += 1
        i += 1
    return out


def progress(label, seconds=1.0, steps=24):
    sys.stdout.write(fg(f"{label} ["))
    for _ in range(steps):
        sys.stdout.write(hi("#"))
        sys.stdout.flush()
        pause(seconds / steps)
    print(fg("] OK"))


def prompt(text="> "):
    try:
        return input(hi(text)).strip()
    except EOFError:
        print()
        return "quit"


def press_enter():
    prompt(dim("[ press ENTER ]"))
