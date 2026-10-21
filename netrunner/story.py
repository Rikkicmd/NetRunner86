"""Story mode. Chapters live in data/story/chapterN.json as a list of scenes.

Scene types:
  text     {"text", "speaker"?, "art"?}          art = name of a constant in art.py
  choice   {"prompt", "options": [{"label", "text", "flag"?}]}
  mission  {"mission": {...}}                    see shell.py for the mission format
Any scene may have "requires": {"flag_name": true} to only play when flags match.
Text can use {handle}. Progress is saved after every scene.
"""
import json
import os

from . import art, shell, ui

STORY_DIR = os.path.join(os.path.dirname(__file__), "data", "story")


def load_chapter(n):
    path = os.path.join(STORY_DIR, f"chapter{n}.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def fmt(text, player):
    return text.replace("{handle}", player.handle)


def play(player):
    chapter = load_chapter(player.story_chapter)
    if chapter is None:
        ui.clear()
        ui.box(["Chapter %d is still being written." % player.story_chapter,
                "Hit the Job Board and upgrade your rig in the meantime."], title="STORY")
        ui.press_enter()
        return
    scenes = chapter["scenes"]
    if player.story_scene == 0:
        ui.clear()
        ui.say(art.TITLE, ui.dim)
        ui.type_out(f"CHAPTER {chapter['number']}: {chapter['title']}", delay=0.05, style=ui.hi)
        ui.pause(0.8)
    while player.story_scene < len(scenes):
        scene = scenes[player.story_scene]
        if not all(player.flags.get(k) == v for k, v in scene.get("requires", {}).items()):
            player.story_scene += 1
            continue
        result = run_scene(scene, player)
        if result == "quit":
            player.save()
            return
        player.story_scene += 1
        player.save()
    player.story_chapter += 1
    player.story_scene = 0
    player.save()


def run_scene(scene, player):
    kind = scene["type"]
    if kind == "text":
        ui.clear()
        if scene.get("art"):
            ui.say(getattr(art, scene["art"]), ui.dim)
        if scene.get("speaker"):
            ui.say(f"<< {scene['speaker']} >>", ui.hi)
            ui.say()
        ui.type_out(fmt(scene["text"], player))
        ui.say()
        return "quit" if ui.prompt(ui.dim("[ ENTER to continue, Q to save & quit ] ")).lower() == "q" else None
    if kind == "choice":
        ui.say()
        ui.say(scene["prompt"], ui.hi)
        opts = scene["options"]
        for i, o in enumerate(opts, 1):
            ui.say(f"  {i}) {o['label']}")
        while True:
            pick = ui.prompt("choice> ")
            if pick.isdigit() and 1 <= int(pick) <= len(opts):
                break
            if pick.lower() in ("q", "quit"):
                return "quit"
        o = opts[int(pick) - 1]
        if o.get("flag"):
            player.flags[o["flag"]] = True
        ui.say()
        ui.type_out(fmt(o["text"], player))
        ui.press_enter()
        return None
    if kind == "mission":
        m = dict(scene["mission"])
        m["brief"] = fmt(m["brief"], player)
        while True:
            outcome = shell.play(player, m)
            if outcome == "success":
                return None
            if not ui.prompt("Retry the job? (y/n) ").lower().startswith("y"):
                return "quit"
    raise ValueError(f"unknown scene type {kind}")
