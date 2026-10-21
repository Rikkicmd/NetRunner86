"""Scripted playthroughs. Run with:  python3 -m unittest discover tests"""
import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest import mock

os.environ["NR_FAST"] = "1"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from netrunner import board, locks, shell, state, story, ui  # noqa: E402


def scripted(inputs):
    it = iter(inputs)
    return mock.patch.object(ui, "prompt", lambda *_: next(it, "quit"))


class Smoke(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        state.SAVE_DIR = self.tmp.name
        self.p = state.Player(handle="TEST")

    def tearDown(self):
        self.tmp.cleanup()

    def test_feedback(self):
        strip = lambda s: "".join(c for c in ui_strip(s))
        self.assertEqual(strip(locks._feedback("1234", "1243")), "**++")
        self.assertEqual(strip(locks._feedback("1111", "1200")), "*...")

    def test_story_chapter1(self):
        inputs = ["", "",                                      # intro scenes
                  "scan", "connect 10.0.1.20", "crack", "ls", "cat sysop_note.txt",
                  "get staff_dir.txt", "dc", "",               # mission 1 (+ enter)
                  "", "2",                                     # text, choice
                  "",                                          # choice enter
                  "connect 192.168.7.1", "login nightowl", "cat ops_memo.txt", "rm access.log",
                  "connect 192.168.7.2", "login tiresias", "get project_basilisk.txt", "dc", "",
                  "", ""]
        with scripted(inputs), mock.patch.dict(locks.LOCKS, {"keypad": lambda *a: True}), redirect_stdout(io.StringIO()):
            story.play(self.p)
        self.assertEqual(self.p.story_chapter, 2)
        self.assertEqual(self.p.credits, 200 + 150 + 600)
        self.assertTrue(self.p.flags.get("asked_money"))

    def test_trace_busts(self):
        job = board.generate(7, 0)
        ip = next(iter(job["hosts"]))
        with scripted([f"connect {ip}"] + ["ls"] * 60 + [""]), redirect_stdout(io.StringIO()):
            self.assertEqual(shell.play(self.p, job), "traced")
        self.assertEqual(self.p.times_traced, 1)

    def test_generated_jobs_are_winnable(self):
        for seed in range(50):
            job = board.generate(seed, rep=seed)
            ip = next(iter(job["hosts"]))
            cmds = [f"connect {ip}", "crack"]
            for o in job["objectives"]:
                cmds.append({"download": "get", "delete": "rm"}[o["type"]] + " " + o["file"])
            cmds += ["dc", ""]
            with scripted(cmds), mock.patch.dict(locks.LOCKS, {k: (lambda *a: True) for k in locks.LOCKS}), \
                    redirect_stdout(io.StringIO()):
                self.assertEqual(shell.play(self.p, job), "success", job)


def ui_strip(s):
    import re
    return re.sub(r"\x1b\[[0-9;]*m", "", s)


if __name__ == "__main__":
    unittest.main()
