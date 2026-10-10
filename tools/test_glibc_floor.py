#!/usr/bin/env python3
"""Tests for tools/glibc_floor.py.

    python3 -m unittest tools.test_glibc_floor

The tool reads a requirement out of a binary that nothing in the source states, so
the tests build the two shapes the tool has to tell apart: an object that carries a
versioned libc reference, and one that carries none. Both are compiled with the
host compiler, which is also how the CI stage uses it.
"""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import glibc_floor as GF

TOOL = ROOT / "tools" / "glibc_floor.py"

# -O0 keeps the call to exp() a real call, so the linker stamps it with the host
# libm's version. At -O2 the compiler inlines it and there is nothing to measure.
CALLS_LIBM = "#include <math.h>\ndouble probe(double x) { return exp(x); }"
CALLS_NOTHING = "int probe(int x) { return x + 1; }"


def build(source: str, out: Path) -> None:
    subprocess.run(
        ["gcc", "-O0", "-fPIC", "-shared", "-x", "c", "-", "-lm", "-o", str(out)],
        input=source, text=True, check=True, cwd=str(ROOT),
    )


def run_tool(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(TOOL)] + args, capture_output=True, text=True, check=False)


class GlibcFloorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp(prefix="glibc_floor_")
        self.tmp_path = Path(self.tmp)

    def test_a_libc_call_is_reported_as_a_floor(self) -> None:
        binary = self.tmp_path / "calls_libm.so"
        build(CALLS_LIBM, binary)
        result = run_tool([str(binary)])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("glibc floor", result.stdout)
        refs = GF.referenced_versions(binary)
        self.assertTrue(any(symbol == "exp" for symbol, _ in refs),
                        "the tool must see the libm call the object actually makes")
        self.assertTrue(GF.parse_version(min(v for _, v in refs)) >= (2, 0))

    def test_require_rejects_an_artifact_over_the_line(self) -> None:
        binary = self.tmp_path / "calls_libm.so"
        build(CALLS_LIBM, binary)
        result = run_tool(["--require", "2.0", str(binary)])
        self.assertEqual(result.returncode, 1)
        self.assertIn("[FAIL]", result.stdout)
        # The message has to name the offender, not just say "too new".
        self.assertIn("@GLIBC_", result.stdout)

    def test_require_accepts_an_artifact_under_the_line(self) -> None:
        binary = self.tmp_path / "calls_libm.so"
        build(CALLS_LIBM, binary)
        result = run_tool(["--require", "99.0", str(binary)])
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertNotIn("[FAIL]", result.stdout)

    def test_an_object_with_no_libc_reference_passes_any_floor(self) -> None:
        binary = self.tmp_path / "clean.so"
        build(CALLS_NOTHING, binary)
        result = run_tool(["--require", "2.0", str(binary)])
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("no versioned glibc references", result.stdout)
        self.assertEqual(GF.referenced_versions(binary), [])

    def test_dotted_glibc_versions_are_parsed_whole(self) -> None:
        # GLIBC_2.2.5 is a real node; reading it as "2.2" would let a 2.2.5
        # requirement pass a 2.2 gate.
        self.assertEqual(GF.parse_version("2.2.5"), (2, 2, 5))
        self.assertGreater(GF.parse_version("2.2.5"), GF.parse_version("2.2"))

    def test_missing_file_is_a_failure_not_a_crash(self) -> None:
        result = run_tool([str(self.tmp_path / "nope.so")])
        self.assertEqual(result.returncode, 1)
        self.assertIn("[FAIL]", result.stdout)

    def test_the_tool_default_is_the_build_contract(self) -> None:
        # Two gates, one number. If the CMake floor moves and the tool's default does
        # not, CI and a standalone run disagree about what is shippable.
        cmake = (ROOT / "CMakeLists.txt").read_text()
        match = re.search(r'set\(HYPERCORE_GLIBC_FLOOR "([\d.]+)"', cmake)
        self.assertIsNotNone(match, "the build must state its libc floor in one place")
        self.assertEqual(GF.CONTRACT_FLOOR, match.group(1))

    def test_a_symbol_above_the_line_produces_a_shim_and_a_flag(self) -> None:
        binary = self.tmp_path / "calls_sqrtf.so"
        build("#include <math.h>\nfloat probe(float x) { return sqrtf(x); }", binary)
        result = run_tool(["--require", "2.0", "--emit-shims", str(binary)])
        self.assertEqual(result.returncode, 1)
        self.assertIn("--wrap=sqrtf", result.stdout)
        self.assertIn("float __wrap_sqrtf(float value)", result.stdout)
        self.assertIn("__builtin_sqrtf", result.stdout)

    def test_the_generated_shim_actually_lowers_the_floor(self) -> None:
        """A shim that leaves the versioned reference in place is not a fix."""
        probe = self.tmp_path / "probe.c"
        probe.write_text("#include <math.h>\nfloat probe(float x) { return sqrtf(x); }")
        source, flags = GF.shim_block([("sqrtf", "2.43")])
        shim = self.tmp_path / "glibc_compat.c"
        shim.write_text(source)
        out = self.tmp_path / "wrapped.so"
        subprocess.run(
            ["gcc", "-O2", "-fPIC", "-shared", str(probe), str(shim)] + flags + ["-lm", "-o", str(out)],
            check=True, cwd=str(ROOT),
        )
        left = [symbol for symbol, _ in GF.referenced_versions(out) if symbol.startswith("sqrtf")]
        self.assertFalse(left, f"the wrapper still carries {left}: wrapping achieved nothing")
        result = run_tool(["--require", "2.39", str(out)])
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_an_unknown_symbol_gets_the_flag_and_a_note_not_a_stub(self) -> None:
        # Guessing a signature would produce a shim that does not compile, which is
        # worse than telling the reader what to write.
        source, flags = GF.shim_block([("exp2f", "2.44")])
        self.assertEqual(flags, ["-Wl,--wrap=exp2f"])
        self.assertIn("no builtin equivalent", source)
        self.assertNotIn("__wrap_exp2f(", source)


if __name__ == "__main__":
    unittest.main()
