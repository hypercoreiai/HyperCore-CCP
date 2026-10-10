"""serve/test_telemetry.py - the /proc readers in serve/telemetry.py close every handle they open.

Python 3.12+ warns on a file object left open, and a sampler that re-reads /proc/stat,
/proc/meminfo and /proc/cpuinfo on every tick leaks a handle per tick until the descriptor
table fills and the background connections lock up. These cases feed fixture text through a
recorded stand-in for open() so an unclosed handle is caught by the test, not by the OS.

    python -m unittest serve.test_telemetry -v
"""
from __future__ import annotations

import ast
import builtins
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from serve import (
    telemetry,  # after the path insert, so the package resolves
)

# /proc/stat fields after the "cpu" label:
#   user nice system idle iowait irq softirq steal guest guest_nice
STAT_BASE = "cpu  100 200 300 4000 500 0 0 100 0 0\n"     # idle+iowait 4500, total 5200
STAT_LATER = "cpu  100 200 300 4500 500 0 0 100 0 500\n"  # idle+iowait 5000, total 6200 -> 50% busy
MEMINFO = "MemTotal: 1000000 kB\nMemFree: 200000 kB\nMemAvailable: 400000 kB\n"
CPUINFO = "model name : Test CPU @ 3.00GHz\nprocessor : 0\n"


class _RecordedOpen:
    """Stands in for builtins.open and tracks whether each handle it handed out was closed."""

    def __init__(self, files: dict[str, str]) -> None:
        self.files = files
        self.handles: list[io.StringIO] = []

    def __call__(self, path: Any, *args: Any, **kwargs: Any) -> io.StringIO:
        if path not in self.files:
            raise FileNotFoundError(path)
        handle = io.StringIO(self.files[path])
        self.handles.append(handle)
        return handle

    @property
    def opened(self) -> int:
        """How many handles the readers asked for."""
        return len(self.handles)

    @property
    def unclosed(self) -> int:
        """How many of them are still open - the leak this suite is about."""
        return sum(1 for handle in self.handles if not handle.closed)


def _callee_name(call: ast.Call) -> str:
    """The plain name a call is made on. ast.Name carries `id`; older builds used `name`.
    Attribute calls like f.open() are not file opens and are left alone."""
    func = call.func
    if isinstance(func, ast.Name):
        return func.id or getattr(func, "name", "")
    return ""


def _open_calls_not_in_a_with(path: Path) -> list[int]:
    """Line numbers of open(...) calls that are not the context expression of a `with`."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    managed: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.With):
            for item in node.items:
                call = item.context_expr
                if isinstance(call, ast.Call) and _callee_name(call) == "open":
                    managed.add(call.lineno)
    bare: list[int] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _callee_name(node) == "open" and node.lineno not in managed:
            bare.append(node.lineno)
    return bare


class TelemetryProc(unittest.TestCase):
    """The three /proc readers the sampler calls on every tick, fed fixture text."""

    def test_cpu_name_reads_the_model_name_and_closes_cpuinfo(self) -> None:
        """_cpu_name returns the model name and closes /proc/cpuinfo on the way out."""
        recorder = _RecordedOpen({"/proc/cpuinfo": CPUINFO})
        with patch.object(os.path, "exists", lambda p: p == "/proc/cpuinfo"), patch.object(builtins, "open", recorder):
            name = telemetry._cpu_name()  # noqa: SL001
        self.assertEqual(name, "Test CPU @ 3.00GHz")
        self.assertEqual(recorder.opened, 1, "cpuinfo was read")
        self.assertEqual(recorder.unclosed, 0, "cpuinfo was left open")

    def test_times_returns_idle_and_total_and_closes_stat(self) -> None:
        """_times returns (idle+iowait, total) and closes /proc/stat."""
        recorder = _RecordedOpen({"/proc/stat": STAT_BASE})
        fallback = telemetry._CpuRamFallback()
        with patch.object(builtins, "open", recorder):
            result = fallback._times()
        self.assertEqual(result, (4500, 5200))
        self.assertEqual(recorder.opened, 1, "stat was read")
        self.assertEqual(recorder.unclosed, 0, "stat was left open")

    def test_ram_returns_used_and_total_and_closes_meminfo(self) -> None:
        """ram returns (used, total) in bytes and closes /proc/meminfo."""
        recorder = _RecordedOpen({"/proc/meminfo": MEMINFO})
        with patch.object(builtins, "open", recorder):
            result = telemetry._CpuRamFallback.ram()
        self.assertEqual(result, (600000 * 1024, 1000000 * 1024))
        self.assertEqual(recorder.opened, 1, "meminfo was read")
        self.assertEqual(recorder.unclosed, 0, "meminfo was left open")

    def test_a_missing_proc_file_gives_none_not_an_exception(self) -> None:
        """A reader that cannot open its file is answered with None, not raised out of the sampler."""
        recorder = _RecordedOpen({})
        fallback = telemetry._CpuRamFallback()
        with patch.object(builtins, "open", recorder):
            times = fallback._times()
            used, total = telemetry._CpuRamFallback.ram()
        self.assertIsNone(times)
        self.assertIsNone(used)
        self.assertIsNone(total)
        self.assertEqual(recorder.unclosed, 0)

    def test_cpu_percent_is_clamped_between_zero_and_one_hundred(self) -> None:
        """Idle growing 500 of 1000 ticks reads as 50% busy, inside the clamp."""
        fallback: telemetry._CpuRamFallback
        with patch.object(builtins, "open", _RecordedOpen({"/proc/stat": STAT_BASE})):
            fallback = telemetry._CpuRamFallback()  # the baseline is taken in __init__
        with patch.object(builtins, "open", _RecordedOpen({"/proc/stat": STAT_LATER})):
            percent = fallback.cpu()
        self.assertAlmostEqual(percent, 50.0, places=4)
        self.assertTrue(0.0 <= percent <= 100.0)

    def test_no_tick_delta_gives_no_reading_instead_of_a_division_by_zero(self) -> None:
        """Two identical ticks return None rather than dividing by zero."""
        with patch.object(builtins, "open", _RecordedOpen({"/proc/stat": STAT_BASE})):
            fallback = telemetry._CpuRamFallback()
            percent = fallback.cpu()
        self.assertIsNone(percent)

    def test_the_guard_itself_catches_a_bare_open(self) -> None:
        """The AST guard must not become a silent no-op on a new Python."""
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as handle:
            handle.write("def leak():\n    for line in open('/proc/stat'):\n        return line\n")
            path = Path(handle.name)
        try:
            self.assertEqual(_open_calls_not_in_a_with(path), [2], "a bare open() was not flagged")
            self.assertEqual(_open_calls_not_in_a_with(ROOT / "serve" / "test_telemetry.py"), [])
        finally:
            path.unlink()

    def test_the_source_has_no_open_call_outside_a_with(self) -> None:
        """Guard against reintroducing a bare open() in the telemetry module."""
        bare = _open_calls_not_in_a_with(ROOT / "serve" / "telemetry.py")
        self.assertEqual(bare, [], f"unmanaged open() at line(s) {bare}")


class TelemetryFdStability(unittest.TestCase):
    """The real /proc files, hammered: the descriptor count must not grow."""

    ITERATIONS = 400

    def _open_fds(self) -> set[str]:
        """Which descriptors this process currently holds open."""
        try:
            return set(os.listdir(f"/proc/{os.getpid()}/fd"))
        except OSError:
            self.skipTest("no /proc/self/fd on this platform")
            return set()

    def test_repeated_sampling_does_not_leak_descriptors(self) -> None:
        """400 sampling ticks must not open a descriptor that stays open.

        The comparison is on the set of descriptors, not the count: another test in the same
        process can close one of its own between the two reads, and a count would then read as
        a leak when nothing here opened anything.
        """
        if not os.path.exists("/proc/stat"):
            self.skipTest("no /proc on this platform")
        fallback = telemetry._CpuRamFallback()
        before = self._open_fds()
        for _ in range(self.ITERATIONS):
            telemetry._cpu_name()
            fallback._times()
            telemetry._CpuRamFallback.ram()
        leaked = sorted(self._open_fds() - before)
        self.assertFalse(
            leaked,
            f"{len(leaked)} descriptor(s) left open after {self.ITERATIONS} ticks: {leaked}",
        )


if __name__ == "__main__":
    unittest.main()
