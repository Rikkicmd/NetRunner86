"""Rig upgrades bought with credits. Add entries to UPGRADES to extend."""
from . import ui

UPGRADES = {
    "modem": {"name": "Modem", "desc": "Faster modem: each command adds less trace",
              "levels": ["2400 baud", "9600 baud", "14.4k", "ISDN"], "prices": [400, 900, 2000]},
    "cracker": {"name": "Cracker", "desc": "Better cracking software: +1 attempt per lock",
                "levels": ["CRACK.COM v1", "CRACK.COM v2", "ICEBREAKER", "BLACK ICE"], "prices": [300, 800, 1800]},
}


def open_shop(player):
    while True:
        ui.clear()
        rows = [f"Credits: {player.credits}", ""]
        keys = list(UPGRADES)
        for i, key in enumerate(keys, 1):
            u = UPGRADES[key]
            lvl = getattr(player, key)
            current = u["levels"][lvl - 1]
            if lvl - 1 < len(u["prices"]):
                nxt = f"-> {u['levels'][lvl]} for {u['prices'][lvl - 1]} cr"
            else:
                nxt = "(maxed)"
            rows += [f"{i}) {ui.hi(u['name'])}: {current}  {nxt}", "   " + ui.dim(u["desc"])]
        ui.box(rows, title="CRAZY EDDIE'S ELECTRONICS")
        pick = ui.prompt("shop (number, B=back)> ").lower()
        if pick in ("b", "q", "back"):
            return
        if not pick.isdigit() or not 1 <= int(pick) <= len(keys):
            continue
        key = keys[int(pick) - 1]
        u, lvl = UPGRADES[key], getattr(player, key)
        if lvl - 1 >= len(u["prices"]):
            continue
        price = u["prices"][lvl - 1]
        if player.credits < price:
            ui.say("  Eddie laughs at your wallet.", ui.alert)
            ui.press_enter()
            continue
        player.credits -= price
        setattr(player, key, lvl + 1)
        player.save()
        ui.say(f"  Installed {u['levels'][lvl]}.", ui.hi)
        ui.press_enter()
