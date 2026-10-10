#!/usr/bin/env python3
"""bench/results/2026-10-09-blackbox-api/scaling_lab.py

Aggregate host-side dispatch throughput as a function of stream count, in-process vs
out-of-process.

The engine in libhypercore_api.so is still the deterministic fixture: it sleeps 40 + max_new/2
ms and then emits tokens as fast as it can. So this measures the *host boundary*, not
inference - which is precisely the thing the two architectures differ on.

Aggregate, not per-stream: a per-stream window over a fixture that sleeps first is dominated
by scheduling jitter. Total tokens delivered divided by the wall-clock window in which any
stream was emitting is stable enough to compare.

Run: python3 bench/results/2026-10-09-blackbox-api/scaling_lab.py
"""
from __future__ import annotations

import ctypes
import json
import pathlib
import statistics
import sys
import threading
import time

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from serve.hypercore_supervisor import HyperCoreProcessSupervisor
from serve.ipc_parser import STREAM_TOKEN
from tools.calibrate_adapter import CMPFUNC, RequestConfig

SOCK = "/tmp/scaling_lab.sock"
WORKER = str(ROOT / "build-shared/hypercore-worker")
TOKENS_PER_STREAM = 4000      # max_context is 4096, so 4000 is the ceiling here
REPEATS = 3


def _emit_window(states: list[dict]) -> tuple[int, float]:
    total = sum(st["n"] for st in states)
    first = min(st["first"] for st in states if st["first"] is not None)
    last = max(st["last"] for st in states if st["last"] is not None)
    return total, last - first


def in_process(streams: int) -> tuple[int, float]:
    lib = ctypes.CDLL(str(ROOT / "build-shared/libhypercore_api.so"))
    lib.hypercore_engine_init.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.c_char_p]
    lib.hypercore_engine_init.restype = ctypes.c_int
    lib.hypercore_engine_submit.argtypes = [
        ctypes.c_void_p, ctypes.c_uint64, ctypes.POINTER(RequestConfig),
        ctypes.POINTER(ctypes.c_int32), ctypes.c_size_t, CMPFUNC, ctypes.c_void_p,
    ]
    lib.hypercore_engine_submit.restype = ctypes.c_int
    lib.hypercore_engine_destroy.argtypes = [ctypes.c_void_p]

    handle = ctypes.c_void_p()
    lib.hypercore_engine_init(ctypes.byref(handle), json.dumps({"batch": streams}).encode())

    states = [{"first": None, "last": None, "n": 0} for _ in range(streams)]
    lock = threading.Lock()

    def cb(chunk_ptr, user_data):
        chunk = chunk_ptr.contents
        if chunk.token_id < 0:
            return
        st = states[int(user_data) - 1]
        now = time.perf_counter()
        with lock:
            st["n"] += 1
            if st["first"] is None:
                st["first"] = now
            st["last"] = now

    hook = CMPFUNC(cb)
    cfg = RequestConfig(struct_size=ctypes.sizeof(RequestConfig), top_k=1,
                       max_new_tokens=TOKENS_PER_STREAM)
    tokens = (ctypes.c_int32 * 4)(1, 2, 3, 4)

    for i in range(streams):
        lib.hypercore_engine_submit(handle, i + 1, ctypes.byref(cfg), tokens, 4, hook,
                                ctypes.c_void_p(i + 1))
    lib.hypercore_engine_destroy(handle)
    return _emit_window(states)


def over_ipc(streams: int) -> tuple[int, float]:
    w = HyperCoreProcessSupervisor(WORKER, SOCK, f'{{"batch":{streams}}}', stderr_log='/tmp/scaling_worker.log')
    w.start()
    states = [{"first": None, "last": None, "n": 0} for _ in range(streams)]
    lock = threading.Lock()

    def run_one(idx: int) -> None:
        st = states[idx]
        for tag, _t, _s in w.stream([1, 2, 3, 4], max_new_tokens=TOKENS_PER_STREAM, timeout_s=120):
            if tag != STREAM_TOKEN:
                continue
            now = time.perf_counter()
            with lock:
                st["n"] += 1
                if st["first"] is None:
                    st["first"] = now
                st["last"] = now

    ts = [threading.Thread(target=run_one, args=(i,)) for i in range(streams)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    w.stop()
    return _emit_window(states)


def main() -> int:
    print(f"aggregate host-side dispatch, {TOKENS_PER_STREAM} tokens per stream, "
          f"median of {REPEATS} runs")
    print(f"{'streams':>7} {'in-process tok/s':>18} {'worker IPC tok/s':>18} {'ratio':>8}")
    rows = []
    for n in (1, 2, 4):
        a = statistics.median(r / w for _ in range(REPEATS) for r, w in [in_process(n)])
        b = statistics.median(r / w for _ in range(REPEATS) for r, w in [over_ipc(n)])
        rows.append((n, a, b))
        print(f"{n:>7} {a:>18,.0f} {b:>18,.0f} {b / a:>8.2f}x")

    print("\nretention relative to one stream (1.00 = no degradation):")
    for name, col in (("in-process", 1), ("worker IPC", 2)):
        base = rows[0][col]
        print(f"  {name:>12}: " + "  ".join(f"{r[col] / base:.2f}" for r in rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
