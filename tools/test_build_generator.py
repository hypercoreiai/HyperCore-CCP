"""setup must configure a build directory with the generator that directory already uses.

CMake refuses to reconfigure a directory with a different generator - it stops with
"Error: generator : Ninja / Does not match the generator used previously: Unix Makefiles"
and setup stops with it. install.sh and a plain `cmake -B build` both use Unix Makefiles,
so a build/ left by either of them has to be built the way it was configured.

    python -m unittest tools.test_build_generator
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
import setup


def write_cache(bdir: Path, generator: str) -> None:
    bdir.mkdir(parents=True, exist_ok=True)
    (bdir / "CMakeCache.txt").write_text(
        "CMAKE_GENERATOR:INTERNAL=" + generator + "\n"
        "CMAKE_GENERATOR_INSTANCE:INTERNAL=\n",
        encoding="utf-8",
    )


class GeneratorChoice(unittest.TestCase):
    def test_a_directory_configured_with_makefiles_is_kept_on_makefiles(self):
        with tempfile.TemporaryDirectory() as d:
            bdir = Path(d) / "build"
            write_cache(bdir, "Unix Makefiles")
            self.assertEqual(setup.build_generator(bdir), "Unix Makefiles")

    def test_a_directory_configured_with_ninja_stays_on_ninja(self):
        with tempfile.TemporaryDirectory() as d:
            bdir = Path(d) / "build"
            write_cache(bdir, "Ninja")
            self.assertEqual(setup.build_generator(bdir), "Ninja")

    def test_a_new_directory_gets_ninja(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(setup.build_generator(Path(d) / "build-cuda12"), "Ninja")

    def test_a_cache_without_a_generator_falls_back_to_ninja(self):
        with tempfile.TemporaryDirectory() as d:
            bdir = Path(d) / "build"
            bdir.mkdir()
            (bdir / "CMakeCache.txt").write_text("CMAKE_GENERATOR:INTERNAL=\n", encoding="utf-8")
            self.assertEqual(setup.build_generator(bdir), "Ninja")

    def test_the_configure_line_only_names_ninja_when_ninja_is_the_generator(self):
        """CMAKE_MAKE_PROGRAM is a Ninja variable; passing it to another generator is noise,
        and passing ninja as the generator to a Makefiles directory is the error itself."""
        with tempfile.TemporaryDirectory() as d:
            bdir = Path(d) / "build"
            write_cache(bdir, "Unix Makefiles")
            cmds = []

            def fake_run(cmd, check=True):
                cmds.append(list(cmd))
                return type("R", (), {"returncode": 0})()

            with mock.patch.object(setup, "find_tool", lambda name: "/usr/bin/" + name), \
                 mock.patch.object(setup, "run", fake_run):
                setup.cmake_build(ROOT, bdir, "hypercore", ["-DHYPERCORE_ENABLE_CUDA=ON"], None, "build-hypercore.bat")

            conf = cmds[0]
            self.assertEqual(conf[1:3], ["-G", "Unix Makefiles"])
            self.assertNotIn("-DCMAKE_MAKE_PROGRAM=/usr/bin/ninja", conf)
            self.assertTrue(any(a.startswith("-DHYPERCORE_ENABLE_CUDA=ON") for a in conf))

    def test_a_fresh_directory_is_configured_with_ninja_and_its_make_program(self):
        with tempfile.TemporaryDirectory() as d:
            bdir = Path(d) / "build-cuda12"
            cmds = []

            def fake_run(cmd, check=True):
                cmds.append(list(cmd))
                return type("R", (), {"returncode": 0})()

            with mock.patch.object(setup, "find_tool", lambda name: "/usr/bin/" + name), \
                 mock.patch.object(setup, "run", fake_run):
                setup.cmake_build(ROOT, bdir, "hypercore", [], None, "build-hypercore-cuda12.bat")

            self.assertEqual(cmds[0][1:3], ["-G", "Ninja"])
            self.assertIn("-DCMAKE_MAKE_PROGRAM=/usr/bin/ninja", cmds[0])


if __name__ == "__main__":
    unittest.main()
