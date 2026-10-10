"""Tests for clean.sh: which tiers remove what, against a temporary project.

    python3 -m pytest tools/test_clean_script.py
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "clean.sh"

GENERATED = ("build", "build-shared", "build-cuda")
KEEP = ("engine", "third_party", "data", "bench", "serve", "src", "tools", "docs")


def make_project(root: Path) -> None:
    """A project with build trees, a venv, a staged install, real source and real data."""
    for name in GENERATED:
        (root / name).mkdir(parents=True)
        (root / name / "object.o").write_bytes(b"x" * 100)
    for name in KEEP:
        (root / name).mkdir(parents=True)
        (root / name / "keep.bin").write_bytes(b"k" * 100)
    (root / "serve" / "server.py").write_text("source", encoding="utf-8")
    (root / "__pycache__").mkdir()
    (root / "__pycache__" / "x.pyc").write_bytes(b"y" * 10)
    (root / ".pytest_cache").mkdir()
    (root / ".venv").mkdir()
    (root / ".venv" / "python").write_text("venv", encoding="utf-8")
    (root / "dist").mkdir()
    (root / "dist" / "lib").mkdir()
    (root / "hypercore-q2_0.json").write_text("{}", encoding="utf-8")
    (root / ".blackbox_scan_state.json").write_text("{}", encoding="utf-8")


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(["bash", str(SCRIPT), *args], capture_output=True, text=True, check=False)


class Tiers(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        make_project(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def test_default_is_the_build_tier(self):
        out = run(["--root", str(self.root)])
        self.assertEqual(out.returncode, 0, out.stderr)
        for name in GENERATED:
            self.assertIn(name, out.stdout)
        self.assertFalse((self.root / "build").exists())
        self.assertFalse((self.root / "__pycache__").exists())

    def test_dry_run_lists_without_removing(self):
        out = run(["--builds", "--dry-run", "--root", str(self.root)])
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("dry run", out.stdout)
        for name in GENERATED:
            self.assertTrue((self.root / name).exists(), f"{name} was deleted in a dry run")

    def test_source_and_data_survive_a_build_clean(self):
        run(["--builds", "--root", str(self.root)])
        for name in KEEP:
            self.assertTrue((self.root / name).exists(), f"{name} should never be removed")
        self.assertTrue((self.root / "serve" / "server.py").exists())
        self.assertTrue((self.root / "hypercore-q2_0.json").exists(), "the run config is setup's output, not a build leftover")
        self.assertTrue((self.root / ".blackbox_scan_state.json").exists())

    def test_all_tier_takes_the_environment_and_the_staged_install(self):
        run(["--all", "--root", str(self.root)])
        self.assertFalse((self.root / ".venv").exists())
        self.assertFalse((self.root / "dist").exists())
        self.assertFalse((self.root / "build").exists())

    def test_unknown_flag_is_an_error(self):
        out = run(["--everything", "--root", str(self.root)])
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("unknown flag", out.stderr)

    def test_nothing_to_remove_is_not_a_failure(self):
        with tempfile.TemporaryDirectory() as empty:
            out = run(["--builds", "--root", empty])
            self.assertEqual(out.returncode, 0, out.stderr)
            self.assertIn("nothing to remove", out.stdout)


class Scratch(unittest.TestCase):
    def test_scratch_removes_tracked_logs_and_keeps_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in (".review_build.txt", ".bb_cmake_configure.txt", "mcp.yaml.orig", "config.json.bak", "_kimi_ab.py"):
                (root / name).write_text("scratch", encoding="utf-8")
            (root / "serve").mkdir()
            (root / "serve" / "server.py").write_text("source", encoding="utf-8")
            (root / ".blackbox_scan_state.json").write_text("{}", encoding="utf-8")
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
            subprocess.run(["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@example.com",
                            "commit", "-q", "-m", "seed"], check=True)

            out = run(["--scratch", "--root", str(root)])
            self.assertEqual(out.returncode, 0, out.stderr)
            for name in (".review_build.txt", ".bb_cmake_configure.txt", "mcp.yaml.orig", "config.json.bak", "_kimi_ab.py"):
                self.assertFalse((root / name).exists(), f"{name} should have been removed")
            self.assertTrue((root / "serve" / "server.py").exists())
            self.assertTrue((root / ".blackbox_scan_state.json").exists(), "the tracker is not scratch")
            tracked = subprocess.run(["git", "-C", str(root), "ls-files"], capture_output=True, text=True).stdout.split()
            self.assertIn("serve/server.py", tracked)
            self.assertNotIn(".review_build.txt", tracked)


if __name__ == "__main__":
    unittest.main()
