"""Player profile and save/load. Saves are plain JSON in ./saves/."""
import json
import os
from dataclasses import asdict, dataclass, field

SAVE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "saves")


@dataclass
class Player:
    handle: str
    credits: int = 200
    rep: int = 0
    # Hardware levels; see shop.UPGRADES for what each one does.
    modem: int = 1
    cracker: int = 1
    completed_jobs: list = field(default_factory=list)
    story_chapter: int = 1
    story_scene: int = 0
    flags: dict = field(default_factory=dict)
    board_seed: int = 1
    times_traced: int = 0

    @property
    def path(self):
        safe = "".join(c for c in self.handle if c.isalnum() or c in "-_").lower() or "player"
        return os.path.join(SAVE_DIR, f"{safe}.json")

    def save(self):
        os.makedirs(SAVE_DIR, exist_ok=True)
        with open(self.path, "w") as f:
            json.dump(asdict(self), f, indent=2)

    @property
    def rank(self):
        for threshold, title in ((60, "ELITE"), (30, "CRACKER"), (10, "PHREAK"), (0, "SCRIPT KIDDIE")):
            if self.rep >= threshold:
                return title
        return "LAMER"


def list_saves():
    if not os.path.isdir(SAVE_DIR):
        return []
    return sorted(f[:-5] for f in os.listdir(SAVE_DIR) if f.endswith(".json"))


def load(name):
    with open(os.path.join(SAVE_DIR, f"{name}.json")) as f:
        data = json.load(f)
    known = Player.__dataclass_fields__
    return Player(**{k: v for k, v in data.items() if k in known})
