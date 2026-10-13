"""A CMake option has to be defined before the section that reads it.

#2027: `HYPERCORE_NATIVE_EXPERTS` was declared far below the GPU section, and the GPU section
uses it to register the native-expert tests. On a first configure the variable does not exist
yet, so those tests are not registered; a second configure, with the value sitting in the cache,
registers them. A fresh clone therefore ran four fewer tests than the same folder configured twice.

    python -m unittest tools.test_cmake_option_order
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

OPTION_LINE = "option(HYPERCORE_NATIVE_EXPERTS \"Native (IQ) expert support through ggml-cpu\" ON)"
READER = "if(HYPERCORE_BUILD_TESTS AND HYPERCORE_NATIVE_EXPERTS)"


def configure_and_count(src: Path, build: Path) -> int:
    """Configure src into build and return how many tests CMake registered in that pass."""
    r = subprocess.run(["cmake", "-B", str(build), "-S", str(src)],
                      capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise RuntimeError(f"cmake failed: {r.stderr[-400:]}")
    tests = build / "CTestTestfile.cmake"
    if not tests.is_file():
        return 0
    return tests.read_text(encoding="utf-8", errors="replace").count("add_test(")


class OptionIsDefinedBeforeItIsRead(unittest.TestCase):
    def test_the_declaration_precedes_the_first_use(self):
        src = (ROOT / "CMakeLists.txt").read_text(encoding="utf-8-sig").splitlines()
        declared = [i for i, line in enumerate(src, 1) if line.startswith("option(HYPERCORE_NATIVE_EXPERTS")]
        read = [i for i, line in enumerate(src, 1) if READER in line]
        self.assertEqual(len(declared), 1, "the option is declared more than once")
        self.assertTrue(read, "no section reads HYPERCORE_NATIVE_EXPERTS to register tests")
        self.assertLess(declared[0], read[0],
                        f"declared at line {declared[0]}, first read at line {read[0]}: "
                        "a first configure cannot see it")

    def test_the_declaration_keeps_its_default_on(self):
        src = (ROOT / "CMakeLists.txt").read_text(encoding="utf-8-sig")
        self.assertIn(OPTION_LINE, src, "the default stays ON: a native IQ pack needs it")

    def test_the_comment_says_why_it_is_there(self):
        src = (ROOT / "CMakeLists.txt").read_text(encoding="utf-8-sig")
        self.assertIn("#2027", src, "the placement is a fix; without the note the next reader moves it back")


class CMakeSemantics(unittest.TestCase):
    """The same shape, in a project small enough to configure in a second: the bug and the fix."""

    def project(self, build_dir: Path, declare_first: bool) -> Path:
        src = build_dir / "src"
        src.mkdir(parents=True, exist_ok=True)
        body = (
            "cmake_minimum_required(VERSION 3.24)\nproject(order_demo)\nenable_testing()\n"
            "add_executable(d demo.c)\n"
            + ("option(DEMO_NATIVE \"native experts\" ON)\n" if declare_first else "")
            + "if(DEMO_NATIVE)\n  add_test(NAME native_test COMMAND demo)\nendif()\n"
            + ("option(DEMO_NATIVE \"native experts\" ON)\n" if not declare_first else "")
        )
        (src / "CMakeLists.txt").write_text(body, encoding="utf-8")
        (src / "demo.c").write_text("int main(){return 0;}\n", encoding="utf-8")
        return src

    def setUp(self):
        if not shutil.which("cmake"):
            self.skipTest("cmake is not installed")
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_declaring_after_use_registers_nothing_on_the_first_configure(self):
        src = self.project(self.root / "late", declare_first=False)
        first = configure_and_count(src, self.root / "late-build")
        second = configure_and_count(src, self.root / "late-build")
        self.assertEqual(first, 0, "the first configure saw no value for the option")
        self.assertEqual(second, 1, "the second configure found it in the cache")

    def test_declaring_before_use_registers_the_test_on_the_first_configure(self):
        src = self.project(self.root / "early", declare_first=True)
        first = configure_and_count(src, self.root / "early-build")
        second = configure_and_count(src, self.root / "early-build")
        self.assertEqual(first, 1, "the first configure must register the native-expert tests")
        self.assertEqual(second, first, "configuring twice must not change the test list")


if __name__ == "__main__":
    unittest.main()
