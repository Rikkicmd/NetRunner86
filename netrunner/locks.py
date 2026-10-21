"""Security minigames. Each host names a lock type; add new ones to LOCKS.

A lock function takes (security_level, attempts_bonus, add_trace) and
returns True if the player gets in. add_trace(n) raises the trace meter and
returns False once the player has been traced, which ends the attempt.
"""
import random

from . import art, ui

WORDS = {
    5: ["CRASH", "LOGIN", "VIRUS", "PHONE", "MODEM", "ROGUE", "CRYPT", "PROXY",
        "SHELL", "GHOST", "CABLE", "TOKEN", "SPOOF", "BYTES", "PATCH", "RELAY"],
    6: ["ACCESS", "SYSTEM", "KERNEL", "BUFFER", "CIPHER", "BINARY", "VECTOR", "SOCKET",
        "MATRIX", "PACKET", "LOCKED", "HACKER", "SECURE", "SIGNAL", "STATIC", "REMOTE"],
    7: ["NETWORK", "PAYLOAD", "TROJANS", "HACKERS", "ROUTERS", "COMPILE", "DECRYPT",
        "ENCRYPT", "MONITOR", "PROGRAM", "BITRATE", "CONSOLE", "SPOOFER",
        "SCANNER", "KEYMAPS", "CHANNEL"],
}


def keypad(security, bonus, add_trace):
    """Mastermind-style numeric code. * = right digit right place, + = wrong place."""
    length = 2 + security
    code = "".join(random.choice("0123456789") for _ in range(length))
    tries = 7 + bonus
    ui.say(art.LOCK)
    ui.box([
        f"NUMERIC KEYLOCK  //  {length}-digit access code",
        "Feedback:  " + ui.hi("*") + ui.fg(" right digit, right slot   ")
        + ui.hi("+") + ui.fg(" right digit, wrong slot   ") + ui.dim(".") + ui.fg(" miss"),
        f"Attempts: {tries}   (each failure raises the trace)",
    ], title="CRACK", style=ui.fg)
    for attempt in range(1, tries + 1):
        guess = ui.prompt(f"code {attempt}/{tries}> ")
        if guess.lower() in ("q", "quit", "abort"):
            return False
        if len(guess) != length or not guess.isdigit():
            ui.say(f"  enter exactly {length} digits", ui.dim)
            continue
        if guess == code:
            ui.say("  " + ui.hi("*" * length) + ui.fg("  ACCESS GRANTED"))
            return True
        ui.say("  " + _feedback(guess, code))
        if not add_trace(5):
            return False
    ui.say(ui.alert(f"  LOCKOUT. The code was {code}."))
    return False


def _feedback(guess, code):
    marks = ["."] * len(code)
    remaining = []
    for i, (g, c) in enumerate(zip(guess, code)):
        if g == c:
            marks[i] = "*"
        else:
            remaining.append(c)
    for i, g in enumerate(guess):
        if marks[i] == "." and g in remaining:
            marks[i] = "+"
            remaining.remove(g)
    return "".join(ui.hi(m) if m == "*" else ui.fg(m) if m == "+" else ui.dim(m) for m in marks)


def wordlist(security, bonus, add_trace):
    """Memory-dump password hunt. Likeness = letters matching in the same position."""
    length = min(7, 4 + security)
    pool = random.sample(WORDS[length], min(len(WORDS[length]), 6 + security * 2))
    answer = random.choice(pool)
    tries = 4 + bonus
    junk = "!@#$%^&*()_+-=[]{};:<>,./?|\\"
    rows = []
    words = list(pool)
    random.shuffle(words)
    for i in range(0, len(words), 2):
        cells = []
        for w in words[i:i + 2]:
            pad = "".join(random.choice(junk) for _ in range(14 - len(w)))
            cut = random.randint(0, len(pad))
            cells.append(f"0x{random.randint(0xF000, 0xFFFF):04X} " + ui.dim(pad[:cut]) + ui.hi(w) + ui.dim(pad[cut:]))
        rows.append("   ".join(cells))
    ui.box(rows, title="MEMORY DUMP", style=ui.fg)
    ui.say(f"Password is one of the words above. Likeness = letters in the right position. Attempts: {tries}")
    used = 0
    while used < tries:
        guess = ui.prompt(f"word {used + 1}/{tries}> ").upper()
        if guess.lower() in ("q", "quit", "abort"):
            return False
        if guess not in pool:
            ui.say("  not in memory dump", ui.dim)
            continue
        used += 1
        if guess == answer:
            ui.say(ui.hi("  >ACCESS GRANTED"))
            return True
        likeness = sum(a == b for a, b in zip(guess, answer))
        ui.say(f"  >ENTRY DENIED   >LIKENESS={likeness}")
        if not add_trace(8):
            return False
    ui.say(ui.alert(f"  TERMINAL LOCKED. Password was {answer}."))
    return False


LOCKS = {"keypad": keypad, "wordlist": wordlist}
