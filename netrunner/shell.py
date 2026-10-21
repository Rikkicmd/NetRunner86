"""The hacking shell: one mission = one Session.

A mission is a plain dict (loaded from JSON or built by the job generator):

    {
      "id": "...", "title": "...", "client": "...", "brief": "...",
      "reward": 300, "rep": 3, "trace_rate": 4,
      "payload": ["worm.exe"],                   # files the player starts with
      "objectives": [
        {"type": "download", "host": "10.0.0.5", "file": "plans.txt"},
        {"type": "delete",   "host": "10.0.0.5", "file": "access.log"},
        {"type": "read",     "host": "10.0.0.5", "file": "memo.txt"},
        {"type": "upload",   "host": "10.0.0.5", "file": "worm.exe"}
      ],
      "hosts": {
        "10.0.0.5": {"name": "ACME-MAIN", "security": 1, "lock": "keypad",
                     "password": "optional login password",
                     "banner": "optional welcome text",
                     "files": {"plans.txt": "file contents"}}
      }
    }
"""
import copy

from . import art, locks, ui

HELP = [
    ("scan", "list reachable hosts"),
    ("connect <ip>", "dial into a host"),
    ("crack", "break the host's security lock"),
    ("login <password>", "log in with a known password (no trace from cracking)"),
    ("ls", "list files on the host"),
    ("cat <file>", "read a file"),
    ("get <file>", "download a file to your rig"),
    ("put <file>", "upload a file from your rig"),
    ("rm <file>", "delete a file"),
    ("dc", "disconnect from the host"),
    ("brief", "show the job brief and objectives"),
    ("rig", "show files on your own machine"),
    ("abort", "walk away from the job"),
]


class Session:
    def __init__(self, player, mission):
        self.player = player
        self.m = copy.deepcopy(mission)
        self.hosts = self.m["hosts"]
        self.host = None          # ip we are connected to
        self.unlocked = set()
        self.scanned = False
        self.trace = 0
        self.rig = {f: "<payload>" for f in self.m.get("payload", [])}
        self.done = [False] * len(self.m["objectives"])
        # Better modems leave fewer footprints.
        self.trace_rate = max(1, self.m.get("trace_rate", 4) - (player.modem - 1))

    # -- trace ----------------------------------------------------------
    def add_trace(self, n):
        self.trace = min(100, self.trace + n)
        return self.trace < 100

    def trace_bar(self):
        filled = self.trace // 10
        bar = "#" * filled + "." * (10 - filled)
        text = f"TRACE[{bar}]{self.trace:3d}%"
        return ui.alert(text) if self.trace >= 70 else ui.fg(text)

    # -- objectives -----------------------------------------------------
    def check(self, kind, filename):
        for i, o in enumerate(self.m["objectives"]):
            if not self.done[i] and o["type"] == kind and o["host"] == self.host and o["file"] == filename:
                self.done[i] = True
                ui.say(ui.hi(f"  [OBJECTIVE COMPLETE] {describe(o, self.hosts)}"))
                if all(self.done):
                    ui.say(ui.hi("  >> All objectives done. Disconnect (dc) to cover your tracks and get paid."))

    def show_brief(self):
        lines = [ui.hi(self.m["title"]), f"Client: {self.m.get('client', 'anonymous')}", ""]
        lines += wrap(self.m["brief"])
        lines += ["", "Objectives:"]
        for o, d in zip(self.m["objectives"], self.done):
            mark = ui.hi("[x]") if d else ui.fg("[ ]")
            lines.append(f"  {mark} {describe(o, self.hosts)}")
        lines += ["", f"Pay: {self.m.get('reward', 0)} cr   Rep: +{self.m.get('rep', 0)}"]
        ui.box(lines, title="JOB", style=ui.fg)

    # -- main loop ------------------------------------------------------
    def run(self):
        """Returns 'success', 'traced' or 'aborted'."""
        ui.clear()
        self.show_brief()
        ui.say("Type 'help' for commands.", ui.dim)
        while True:
            where = self.hosts[self.host]["name"] if self.host else "localhost"
            line = ui.prompt(f"{self.trace_bar()} {ui.hi(self.player.handle)}@{where}$ ")
            if not line:
                continue
            cmd, _, arg = line.partition(" ")
            cmd, arg = cmd.lower(), arg.strip()
            handler = getattr(self, f"do_{cmd}", None)
            if handler is None:
                ui.say(f"{cmd}: command not found", ui.dim)
                continue
            if self.host and cmd not in ("help", "brief", "rig"):
                if not self.add_trace(self.trace_rate):
                    return self.busted()
            result = handler(arg)
            if result:
                return result
            if self.trace >= 100:
                return self.busted()

    def busted(self):
        ui.say(art.SKULL, ui.alert)
        ui.type_out("Your line has been traced. The feds know where you live.", style=ui.alert)
        return "traced"

    # -- commands -------------------------------------------------------
    def do_help(self, _):
        for c, d in HELP:
            ui.say(f"  {ui.hi(c.ljust(18))}{ui.fg(d)}")

    def do_brief(self, _):
        self.show_brief()

    def do_rig(self, _):
        ui.say("  " + ("  ".join(self.rig) if self.rig else ui.dim("(empty)")))

    def do_abort(self, _):
        if ui.prompt("Abort the job? (y/n) ").lower().startswith("y"):
            return "aborted"

    def do_scan(self, _):
        ui.progress("Scanning subnet", 0.8)
        for ip, h in self.hosts.items():
            sec = "#" * h.get("security", 1)
            ui.say(f"  {ui.hi(ip.ljust(16))}{h['name'].ljust(22)}security {sec}")
        self.scanned = True

    def do_connect(self, ip):
        if not ip:
            return ui.say("usage: connect <ip>", ui.dim)
        if ip not in self.hosts:
            return ui.say(f"connect: no carrier at {ip}", ui.dim)
        if self.host:
            self.do_dc("")
        ui.say(f"ATDT {ip} ...", ui.dim)
        ui.progress("Handshake", 0.6)
        self.host = ip
        h = self.hosts[ip]
        ui.say(ui.hi(f"CONNECTED to {h['name']}"))
        if h.get("banner"):
            ui.say(h["banner"])
        if ip not in self.unlocked:
            ui.say(ui.alert("ACCESS RESTRICTED.") + ui.fg(" Use 'crack' or 'login <password>'."))

    def do_dc(self, _):
        if not self.host:
            return ui.say("not connected", ui.dim)
        ui.say(f"NO CARRIER ({self.hosts[self.host]['name']})", ui.dim)
        self.host = None
        if all(self.done):
            return "success"

    do_disconnect = do_dc
    do_exit = do_dc

    def do_crack(self, _):
        if not self._connected():
            return
        if self.host in self.unlocked:
            return ui.say("already in", ui.dim)
        h = self.hosts[self.host]
        lock = locks.LOCKS[h.get("lock", "keypad")]
        if lock(h.get("security", 1), self.player.cracker - 1, self.add_trace):
            self.unlocked.add(self.host)
            ui.say(ui.hi(f"ROOT ACCESS ON {h['name']}"))
        elif self.trace < 100:
            ui.say("Crack failed. Try again or find a password.", ui.dim)

    def do_login(self, pw):
        if not self._connected():
            return
        if pw and pw == self.hosts[self.host].get("password"):
            self.unlocked.add(self.host)
            ui.say(ui.hi("LOGIN OK. Welcome back, operator."))
        else:
            ui.say(ui.alert("LOGIN INCORRECT"))
            self.add_trace(5)

    def do_ls(self, _):
        if self._inside():
            files = self.hosts[self.host]["files"]
            for name, body in files.items():
                ui.say(f"  {name.ljust(24)}{len(body):6d} bytes")
            if not files:
                ui.say("  (no files)", ui.dim)

    def do_cat(self, name):
        if self._inside() and self._exists(name):
            ui.box(wrap(self.hosts[self.host]["files"][name]), title=name, style=ui.fg)
            self.check("read", name)

    def do_get(self, name):
        if self._inside() and self._exists(name):
            ui.progress(f"Downloading {name}", 0.8)
            self.rig[name] = self.hosts[self.host]["files"][name]
            self.check("download", name)

    def do_put(self, name):
        if not self._inside():
            return
        if name not in self.rig:
            return ui.say(f"put: {name} is not on your rig", ui.dim)
        ui.progress(f"Uploading {name}", 0.8)
        self.hosts[self.host]["files"][name] = self.rig[name]
        self.check("upload", name)

    def do_rm(self, name):
        if self._inside() and self._exists(name):
            del self.hosts[self.host]["files"][name]
            ui.say(f"  {name} deleted")
            self.check("delete", name)

    # -- guards ---------------------------------------------------------
    def _connected(self):
        if not self.host:
            ui.say("not connected. scan, then connect <ip>", ui.dim)
        return bool(self.host)

    def _inside(self):
        if not self._connected():
            return False
        if self.host not in self.unlocked:
            ui.say(ui.alert("ACCESS DENIED") + ui.fg(" - crack the lock first"))
            return False
        return True

    def _exists(self, name):
        if name in self.hosts[self.host]["files"]:
            return True
        ui.say(f"no such file: {name}", ui.dim)
        return False


def describe(o, hosts):
    verb = {"download": "Download", "delete": "Delete", "read": "Read", "upload": "Upload"}[o["type"]]
    where = "to" if o["type"] == "upload" else "from" if o["type"] != "read" else "on"
    return f"{verb} {o['file']} {where} {hosts[o['host']]['name']} ({o['host']})"


def wrap(text, w=None):
    import textwrap
    w = w or ui.width() - 6
    out = []
    for para in text.split("\n"):
        out += textwrap.wrap(para, w) or [""]
    return out


def play(player, mission):
    """Run a mission and apply rewards/penalties. Returns the outcome string."""
    outcome = Session(player, mission).run()
    if outcome == "success":
        player.credits += mission.get("reward", 0)
        player.rep += mission.get("rep", 0)
        ui.type_out(f"\nTransfer received: {mission.get('reward', 0)} credits. Rep +{mission.get('rep', 0)}.", style=ui.hi)
    elif outcome == "traced":
        fine = player.credits // 4
        player.credits -= fine
        player.rep = max(0, player.rep - 2)
        player.times_traced += 1
        ui.say(f"You burn {fine} credits on lawyers and a new phone line. Rep -2.", ui.alert)
    else:
        ui.say("You hang up and walk away. No pay.", ui.dim)
    player.save()
    ui.press_enter()
    return outcome
