#!/usr/bin/env python3
"""bench/results/2026-10-09-blackbox-api/adapter_test.py

Tests the calibration adapter against the fixture engine. Three things the C tests cannot check:
the Python struct mirrors match the C layout, every session id round-trips through a void*, and
no row is silently dropped.

Build the library first:
    g++ -std=c++17 -Wall -Wextra -I. -shared -fPIC -fvisibility=hidden \
        hypercore_bridge_v2.cpp -o libhypercore_engine.so
    python3 adapter_test.py ./libhypercore_engine.so
"""
import ctypes
import statistics
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]   # .../HyperCore
sys.path.insert(0, str(REPO_ROOT / "tools"))
from calibrate_adapter import (
    OutputChunk,
    RequestConfig,
    HyperCoreCalibrationAdapter,
    SummaryStruct,
)
from calibrate_parallel_adapter import ParallelHyperCoreEvaluator

# Measured from hypercore/hypercore_blackbox.h with a C program. If these differ, the Python mirror has
# drifted and every measurement the adapter reports is wrong.
C_SIZES = {"config": 28, "summary": 32, "chunk": 16}

PCIE = (0.0, 0.2, 0.35, 0.55, 0.75)
SPEC = (0.3, 0.5, 0.7)
GRID = [(p, s) for p in PCIE for s in SPEC]
REPEATS = 3


def check_layout() -> bool:
    """The adapter is a third copy of the ABI. Check it against the header."""
    got = {
        "config": ctypes.sizeof(RequestConfig),
        "summary": ctypes.sizeof(SummaryStruct),
        "chunk": ctypes.sizeof(OutputChunk),
    }
    for name, want in C_SIZES.items():
        if got[name] != want:
            print(f"FAIL: {name} is {got[name]} bytes in Python, {want} in C")
            return False
    print(f"PASS: Python mirrors match the C layout {got}")
    return True


def check_session_ids(lib_path: str) -> bool:
    """A session id travels through the boundary as a void*.

    Python's hash() returns signed values. A negative hash becomes a large unsigned pointer:
    -217929430759900949 arrives on the other side as 18228814642949650667. The dict lookup misses,
    the completion event never fires, and the row is dropped with no error and no warning. Measured
    with hash() as the id: 6 of 15 combinations lost, and the sweep took 61 s instead of 5 s
    because each lost row waited out its 10 s timeout.

    A monotonic counter cannot produce that failure, so the test asserts the ids the adapter
    actually generates are non-negative and unique.
    """
    adapter = HyperCoreCalibrationAdapter(lib_path)
    generated = [adapter._next_session_id() for _ in range(len(GRID) * REPEATS)]
    if any(v < 0 for v in generated):
        print(f"FAIL: {sum(v < 0 for v in generated)} session ids are negative")
        return False
    if len(set(generated)) != len(generated):
        print("FAIL: session ids are not unique")
        return False
    print(f"PASS: {len(generated)} session ids, all non-negative and unique")
    return True


def check_no_rows_lost(lib_path: str) -> bool:
    """Every submitted combination must produce a row. Silent loss is the failure mode."""
    adapter = HyperCoreCalibrationAdapter(lib_path)
    rows = adapter.run_noise_filtered_sweep('{"batch": 2}', [1, 2, 3, 4],
                                           list(PCIE), list(SPEC), repeats=REPEATS)
    want = len(GRID) * REPEATS
    empty = sum(1 for r in rows if not r["metrics"])
    print(f"sweep: {want} requested, {len(rows)} returned, {empty} with no metrics")
    if len(rows) != want or empty:
        print("FAIL: rows were dropped")
        return False

    # The fixture always runs to max_new_tokens, so every run must report LIMIT (2).
    reasons = {r["stop_reason"] for r in rows}
    if reasons != {2}:
        print(f"FAIL: stop_reason values {reasons}; the fixture always hits the limit")
        return False

    # The fixture is deterministic by design, so a zero spread is expected here. Against a real
    # engine a zero spread would mean the sweep is measuring nothing.
    rates = [r["metrics"]["tok_per_sec"] for r in rows]
    print(f"PASS: all {want} rows measured; median {statistics.median(rates):.1f} tok/s, "
          f"spread {(max(rates) - min(rates)) / max(rates):.1%} (fixture is deterministic)")
    return True


def check_backpressure(lib_path: str) -> bool:
    """The async claim, tested: N declared slots means exactly N accepted requests and every
    extra one bounces with BUSY. A bounced request must consume nothing.
    """
    ev = ParallelHyperCoreEvaluator(lib_path)
    handle = ctypes.c_void_p()
    if ev.lib.hypercore_engine_init(ctypes.byref(handle), b'{"batch": 3}') != 0:
        print("FAIL: could not open an engine for the backpressure test")
        return False
    out = ev.flood_engine_concurrently(handle, [1, 2, 3], overshoot=3)
    ev.lib.hypercore_engine_destroy(handle)
    slots, attempts = out["max_slots"], out["attempts"]
    print(f"flood: {attempts} requests against {slots} slots -> "
          f"accepted={out['accepted']} busy={out['busy']} timed_out={out['timed_out']}")
    if out["accepted"] != slots or out["busy"] != attempts - slots or out["timed_out"]:
        print("FAIL: slot accounting is wrong")
        return False
    print("PASS: BUSY is returned exactly at the declared limit and releases nothing")
    return True


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "./libhypercore_engine.so"
    passed = (check_layout() and check_session_ids(path)
              and check_no_rows_lost(path) and check_backpressure(path))
    print("adapter_test:", "PASS" if passed else "FAIL")
    sys.exit(0 if passed else 1)
