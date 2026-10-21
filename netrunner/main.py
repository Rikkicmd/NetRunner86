"""Entry point: boot screen, profile select, and the main menu."""
import sys

from . import art, board, shop, state, story, ui


def boot():
    ui.clear()
    for line in ["ACME BIOS v2.11  (C) 1984", "640K RAM OK", "HAYES COMPATIBLE MODEM ... DETECTED",
                 "LOADING NETRUN.EXE"]:
        ui.say(line, ui.dim)
        ui.pause(0.25)
    ui.progress("", 0.6)
    ui.clear()
    ui.say(art.TITLE, ui.hi)
    ui.type_out("            A HACKING ADVENTURE FOR THE 2400 BAUD GENERATION", delay=0.02, style=ui.dim)
    ui.say()


def pick_profile():
    saves = state.list_saves()
    if saves:
        ui.say("Saved handles: " + ", ".join(saves))
    while True:
        handle = ui.prompt("ENTER HANDLE (or a saved one to resume)> ")
        if handle == "quit":
            sys.exit(0)
        if not handle:
            continue
        key = "".join(c for c in handle if c.isalnum() or c in "-_").lower()
        if key in saves:
            player = state.load(key)
            ui.type_out(f"Welcome back, {player.handle}.", style=ui.hi)
            return player
        player = state.Player(handle=handle.upper()[:16])
        player.save()
        ui.type_out(f"New profile created. Stay paranoid, {player.handle}.", style=ui.hi)
        return player


def status(player):
    ui.clear()
    ui.box([
        f"Handle:    {ui.hi(player.handle)}",
        f"Rank:      {player.rank}",
        f"Credits:   {player.credits}",
        f"Rep:       {player.rep}",
        f"Rig:       {shop.UPGRADES['modem']['levels'][player.modem - 1]} modem, "
        f"{shop.UPGRADES['cracker']['levels'][player.cracker - 1]}",
        f"Story:     Chapter {player.story_chapter}",
        f"Jobs done: {len(player.completed_jobs)} contracts   Times traced: {player.times_traced}",
    ], title="DOSSIER")
    ui.press_enter()


def main_menu(player):
    options = [
        ("S", "Story mode", lambda: story.play(player)),
        ("J", "Job board (open world)", lambda: board.open_board(player)),
        ("R", "Rig upgrades", lambda: shop.open_shop(player)),
        ("D", "Dossier", lambda: status(player)),
        ("T", "Toggle monitor colour (green/amber)", None),
        ("Q", "Save & quit", None),
    ]
    theme = "green"
    while True:
        ui.clear()
        ui.say(art.TITLE, ui.hi)
        ui.say(f"  {player.handle} // {player.rank} // {player.credits} cr // rep {player.rep}", ui.dim)
        ui.box([f"{ui.hi(k)}) {label}" for k, label, _ in options], title="MAIN MENU")
        pick = ui.prompt("> ").upper()
        if pick in ("Q", "QUIT"):
            player.save()
            ui.say("NO CARRIER", ui.dim)
            return
        if pick == "T":
            theme = "amber" if theme == "green" else "green"
            ui.set_theme(theme)
            continue
        for k, _, action in options:
            if pick == k and action:
                action()


def run():
    try:
        boot()
        player = pick_profile()
        ui.pause(0.6)
        main_menu(player)
    except KeyboardInterrupt:
        print(ui.RESET)
        ui.say("\nNO CARRIER", ui.dim)
