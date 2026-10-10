#!/usr/bin/env python3
"""End-to-end check of the REPL: state across calls, bare expressions, bash, loop recovery.

  python3 tools/test_repl_loop.py

The working directory is a temporary one, not a fixed path: a fixed path is owned by
whoever created it first, and this file used to fail at import with a PermissionError on
a machine where another user had made it.
"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from serve import terminal_mcp as t

COUNTER = (
    "class Counter:\n"
    "    def __init__(self, n=0):\n"
    "        self.n = n\n"
    "    def bump(self):\n"
    "        self.n += 1\n"
    "        return self.n\n"
)


class ReplLoop(unittest.TestCase):
    """Each case gets its own scratch directory and its own sessions."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="repl-"))
        self.old_root, self.old_state = t.ROOT, t.STATE_DIR
        t.ROOT, t.STATE_DIR = self.tmp, self.tmp / ".terminal"
        t._sessions.clear()

    def tearDown(self):
        t.ROOT, t.STATE_DIR = self.old_root, self.old_state
        t._sessions.clear()

    def test_a_class_defined_in_one_call_is_usable_in_the_next(self):
        t.repl("python", COUNTER, action="start")
        got = t.repl("python", "c = Counter(10)\nprint([c.bump() for _ in range(3)])")["output"].strip()
        self.assertEqual(got, "[11, 12, 13]")

    def test_a_bare_expression_echoes_its_value(self):
        t.repl("python", COUNTER, action="start")
        t.repl("python", "c = Counter(7)")
        self.assertEqual(t.repl("python", "c.n")["output"].strip(), "7")

    def test_a_compound_statement_runs(self):
        t.repl("python", "total = 0\nfor n in range(4):\n    total += n", action="start")
        self.assertEqual(t.repl("python", "total = 0\nfor n in range(4):\n    total += n")["output"], "")
        self.assertEqual(t.repl("python", "print(total)")["output"].strip(), "6")

    def test_an_error_does_not_kill_the_session(self):
        t.repl("python", "total = 6", action="start")
        self.assertIn("NameError", t.repl("python", "print(nope)")["output"])
        self.assertEqual(t.repl("python", "print(total)")["output"].strip(), "6")

    def test_a_loop_times_out_and_the_session_is_replaced(self):
        t.repl("python", "x = 1", action="start")
        with self.assertRaises(ValueError):
            t.repl("python", "while True: pass", timeout_s=2)
        self.assertFalse(t.repl("python", action="status")["running"], "the stuck session was left open")
        self.assertEqual(t.repl("python", "print('restarted')")["output"].strip(), "restarted")

    def test_bash_keeps_state_and_closes(self):
        t.repl("bash", "count=3", action="start")
        self.assertEqual(t.repl("bash", "echo $((count * 2))")["output"].strip(), "6")
        t.repl("bash", action="close")
        self.assertFalse(t.repl("bash", action="status")["running"], "the shell was left running")


if __name__ == "__main__":
    unittest.main()
