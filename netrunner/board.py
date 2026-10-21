"""The Job Board: hand-written contracts from data/jobs.json plus endless
procedurally generated ones so open-world play never runs dry."""
import json
import os
import random

from . import art, shell, ui

JOBS_PATH = os.path.join(os.path.dirname(__file__), "data", "jobs.json")

CORPS = ["Cyberdyne Logistics", "Tessier Freight", "Hollow Creek Savings", "Ma Bell Exchange 9",
         "Weyland Insurance", "Krupp Chemical", "Metro Transit Auth.", "Delos Leisure",
         "Zenith Satellite", "Gordon Electronics", "St. Jude Hospital", "WOPR Defense Labs"]
HANDLES = ["ZER0_COOL", "PH4NT0M", "ACID_BURN", "LORD_NIKON", "CEREAL", "MR_GREY",
           "NIGHTSHADE", "BYTE_BANDIT", "D3L1R1UM", "CAPTAIN_CRUNCH"]
LOOT = ["payroll.dat", "blueprints.cad", "customer_list.db", "launch_codes.txt",
        "patient_files.db", "routing_table.cfg", "salary_review.txt", "prototype_specs.doc"]
LOGS = ["access.log", "audit.log", "syslog.dat"]
JUNK = {"readme.txt": "Authorized personnel only.", "todo.txt": "- buy floppies\n- fix printer",
        "memo.txt": "Reminder: change your passwords quarterly."}


def generate(seed, rep):
    """Build a random contract. Difficulty scales with the player's rep."""
    rng = random.Random(seed)
    tier = min(3, 1 + rep // 12 + rng.choice([0, 0, 1]))
    corp = rng.choice(CORPS)
    tag = "".join(w[0] for w in corp.split()).upper()
    ip = f"{rng.choice([10, 172, 192])}.{rng.randint(0, 255)}.{rng.randint(0, 255)}.{rng.randint(1, 254)}"
    name = f"{tag}-{rng.choice(['MAIN', 'FILES', 'DB', 'NODE', 'VAX'])}"
    loot = rng.choice(LOOT)
    log = rng.choice(LOGS)
    files = dict(JUNK)
    files[loot] = f"[{rng.randint(10, 900)} KB of {corp} data]"
    files[log] = "CONNECT ... AUTH ... <your fingerprints are here>"
    kind = rng.choice(["steal", "steal_clean", "wipe"])
    if kind == "steal":
        objectives = [{"type": "download", "host": ip, "file": loot}]
        brief = f"I need {loot} from {corp}. Get in, get it, get out."
    elif kind == "steal_clean":
        objectives = [{"type": "download", "host": ip, "file": loot}, {"type": "delete", "host": ip, "file": log}]
        brief = f"Pull {loot} off the {corp} system and wipe {log} so nobody knows it walked."
    else:
        objectives = [{"type": "delete", "host": ip, "file": loot}]
        brief = f"{corp} has something on me in {loot}. Make it disappear."
    reward = 100 * tier + rng.randint(0, 8) * 10 + 40 * (len(objectives) - 1)
    return {
        "id": f"gen_{seed}",
        "title": f"{corp} contract",
        "client": rng.choice(HANDLES),
        "brief": brief,
        "reward": reward,
        "rep": 1 + tier,
        "trace_rate": 2 + tier,
        "objectives": objectives,
        "hosts": {ip: {"name": name, "security": tier, "lock": rng.choice(["keypad", "wordlist"]), "files": files}},
        "generated": True,
    }


def available_jobs(player):
    with open(JOBS_PATH) as f:
        handmade = [j for j in json.load(f) if j["id"] not in player.completed_jobs]
    gen = [generate(player.board_seed * 100 + i, player.rep) for i in range(3)]
    return handmade + gen


def stars(job):
    level = max(h.get("security", 1) for h in job["hosts"].values())
    return "*" * level + " " * (3 - level)


def open_board(player):
    while True:
        ui.clear()
        ui.say(art.BOARD, ui.hi)
        ui.say(f"  {player.handle}  //  {player.rank}  //  {player.credits} cr  //  rep {player.rep}", ui.dim)
        jobs = available_jobs(player)
        rows = []
        for i, j in enumerate(jobs, 1):
            locked = j.get("min_rep", 0) > player.rep
            line = f"{i:>2}) [{stars(j)}] {j['title'][:34]:<34} {j['reward']:>5} cr  {j['client'][:12]}"
            rows.append(ui.dim(line + f"  (rep {j['min_rep']})") if locked else line)
        ui.box(rows, title="CONTRACTS")
        ui.say("  number = view job   R = refresh the board (-20 cr)   B = back", ui.dim)
        pick = ui.prompt("board> ").lower()
        if pick in ("b", "q", "back", "quit"):
            return
        if pick == "r":
            if player.credits >= 20:
                player.credits -= 20
                player.board_seed += 1
                player.save()
            continue
        if not pick.isdigit() or not 1 <= int(pick) <= len(jobs):
            continue
        job = jobs[int(pick) - 1]
        if job.get("min_rep", 0) > player.rep:
            ui.say(f"  {job['client']} doesn't deal with nobodies. Come back with {job['min_rep']} rep.", ui.alert)
            ui.press_enter()
            continue
        ui.clear()
        ui.box([ui.hi(job["title"]), f"Client: {job['client']}", ""] + shell.wrap(job["brief"])
               + ["", f"Pay: {job['reward']} cr   Rep: +{job['rep']}   Security: {stars(job)}"], title="JOB DETAILS")
        if not ui.prompt("Take the job? (y/n) ").lower().startswith("y"):
            continue
        if shell.play(player, job) == "success":
            if job.get("generated"):
                player.board_seed += 1
            else:
                player.completed_jobs.append(job["id"])
            player.save()
