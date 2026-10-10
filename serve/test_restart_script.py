"""The restart script: stop the running server, start the variant you asked for.

    python3 -m unittest serve.test_restart_script

Runs against a mock run script in a temporary directory and the mock engine on a spare
port, so it never touches the server the chat is using.
"""
from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = str(REPO / "restart.sh")
PORT = 8099


def run(args: list[str], root: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "HYPERCORE_ROOT": root, "READY_S": "30", "GRACE_S": "8"}
    return subprocess.run(["sh", SCRIPT, *args], capture_output=True, text=True, env=env, timeout=60, check=False)


class Restart(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        (root / "run-q2_0.sh").write_text(
            f'#!/bin/sh\ncd "{REPO}"\nexec python3 "serve/server.py" --engine mock --port {PORT} --host 127.0.0.1\n',
            encoding="utf-8",
        )

    def tearDown(self):
        run(["stop", "--port", str(PORT)], self.tmp.name)
        self.tmp.cleanup()

    def test_status_reports_nothing_when_nothing_is_running(self):
        out = run(["status", "--port", str(PORT)], self.tmp.name)
        self.assertEqual(out.returncode, 0)
        self.assertIn("no HyperCore server running", out.stdout)

    def test_start_then_status_then_stop(self):
        out = run(["start", "q2_0", "--port", str(PORT)], self.tmp.name)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertIn("listening after", out.stdout)

        out = run(["status", "--port", str(PORT)], self.tmp.name)
        self.assertIn("port 8099", out.stdout)

        out = run(["stop", "--port", str(PORT)], self.tmp.name)
        self.assertIn("stopping pid", out.stdout)
        self.assertIn("stopped", out.stdout)
        out = run(["status", "--port", str(PORT)], self.tmp.name)
        self.assertIn("no HyperCore server running", out.stdout)

    def test_a_missing_variant_says_so_and_starts_nothing(self):
        out = run(["start", "missing", "--port", str(PORT)], self.tmp.name)
        self.assertEqual(out.returncode, 1)
        self.assertIn("run-missing.sh does not exist yet", out.stdout)
        self.assertEqual(run(["status", "--port", str(PORT)], self.tmp.name).stdout.strip(),
                         "no HyperCore server running")

    def test_dry_run_changes_nothing(self):
        run(["start", "q2_0", "--port", str(PORT)], self.tmp.name)
        out = run(["stop", "--port", str(PORT), "--dry-run"], self.tmp.name)
        self.assertIn("would stop", out.stdout)
        still = run(["status", "--port", str(PORT)], self.tmp.name)
        self.assertIn("port 8099", still.stdout)

    def test_an_unknown_argument_exits_2(self):
        out = run(["bogus"], self.tmp.name)
        self.assertEqual(out.returncode, 2)
        self.assertIn("usage:", out.stdout)


if __name__ == "__main__":
    unittest.main()
