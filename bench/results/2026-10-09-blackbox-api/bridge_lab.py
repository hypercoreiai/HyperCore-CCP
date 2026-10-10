#!/usr/bin/env python3
"""bench/results/2026-10-09-blackbox-api/bridge_lab.py

Measures the two dispatch designs against the real engine:

  A  per-token call_soon_threadsafe(queue.put_nowait, payload)   <- the design as written
  B  per-token deque.append, wake the loop every N tokens        <- the batched variant
  C  callback does nothing but count                              <- the engine's own ceiling

Prints tokens/s and the Python-side cost per token for each.
Run: python3 bench/results/2026-10-09-blackbox-api/bridge_lab.py [path-to-.so]
"""
from __future__ import annotations

import asyncio
import collections
import ctypes
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # repo root: .../HyperCore
from tools.calibrate_adapter import (
    CMPFUNC,
    SUCCESS,
    CapsStruct,
    RequestConfig,
)


def make_config(max_new: int) -> RequestConfig:
    return RequestConfig(
        struct_size=ctypes.sizeof(RequestConfig),
        temperature=0.0, top_p=1.0, top_k=1,
        max_new_tokens=max_new, pcie_frac=-1.0, spec_min_p=-1.0,
    )


def run_variant(lib, handle, variant: str, concurrency: int, max_new: int, flush: int) -> dict:
    counters = {"tokens": 0, "wakeups": 0, "payloads": 0, "first": None, "last": None}
    lock = threading.Lock()
    loop = asyncio.new_event_loop()

    async def drain() -> None:
        """Consumes whatever the async side the variant builds. Variant C has none."""

    if variant == "C":
        def cb(chunk_ptr, user_data):
            chunk = chunk_ptr.contents
            if chunk.token_id >= 0:
                now = time.perf_counter()
                with lock:
                    counters["tokens"] += 1
                    if counters["first"] is None:
                        counters["first"] = now
                    counters["last"] = now
    elif variant == "A":
        queues: dict[int, asyncio.Queue] = {i: asyncio.Queue() for i in range(1, concurrency + 1)}

        def cb(chunk_ptr, user_data):
            chunk = chunk_ptr.contents
            if chunk.token_id < 0:
                payload = {"token_id": -1}          # the terminal frame, as the design puts it
            else:
                payload = {"token_id": chunk.token_id, "prompt_reused": chunk.prompt_reused}
                now = time.perf_counter()
                with lock:
                    counters["tokens"] += 1
                    counters["payloads"] += 1
                    if counters["first"] is None:
                        counters["first"] = now
                    counters["last"] = now
            q = queues[int(user_data) if user_data else 1]
            loop.call_soon_threadsafe(q.put_nowait, payload)

        async def drain():
            async def one(i: int) -> None:
                while True:
                    item = await queues[i].get()
                    if item["token_id"] < 0:
                        break
            await asyncio.gather(*(one(i) for i in range(1, concurrency + 1)))

    else:  # B
        buffers = collections.defaultdict(collections.deque)
        pending = collections.defaultdict(int)
        wake = {i: asyncio.Event() for i in range(1, concurrency + 1)}
        done = collections.defaultdict(bool)

        def cb(chunk_ptr, user_data):
            chunk = chunk_ptr.contents
            i = int(user_data) if user_data else 1
            if chunk.token_id < 0:
                done[i] = True
                loop.call_soon_threadsafe(wake[i].set)
                return
            buffers[i].append((chunk.token_id, chunk.prompt_reused))
            now = time.perf_counter()
            with lock:
                counters["tokens"] += 1
                if counters["first"] is None:
                    counters["first"] = now
                counters["last"] = now
            pending[i] += 1
            if pending[i] >= flush:
                pending[i] = 0
                counters["wakeups"] += 1
                loop.call_soon_threadsafe(wake[i].set)

        async def drain():
            async def one(i: int) -> None:
                while not done[i]:
                    await wake[i].wait()
                    wake[i].clear()
                    while buffers[i]:
                        buffers[i].popleft()
            await asyncio.gather(*(one(i) for i in range(1, concurrency + 1)))

    callback = CMPFUNC(cb)
    t0 = time.perf_counter()
    handles = []
    for i in range(concurrency):
        code = lib.hypercore_engine_submit(
            handle, ctypes.byref(make_config(max_new)),
            (ctypes.c_int32 * 4)(1, 2, 3, 4), 4, callback, ctypes.c_void_p(i + 1),
        )
        if code != SUCCESS:
            raise RuntimeError(f"submit failed: {code} (concurrency {concurrency} > slots?)")
        handles.append(i)

    loop.run_until_complete(drain())
    # destroy() joins every request thread, so the elapsed window covers the whole
    # stream - otherwise variant C reports the submit time as the throughput.
    lib.hypercore_engine_destroy(handle)
    elapsed = time.perf_counter() - t0

    loop.close()

    tokens = counters["tokens"]
    emit_window = (counters["last"] - counters["first"]) if counters["first"] else 0.0
    return {
        "variant": variant,
        "concurrency": concurrency,
        "tokens": tokens,
        "elapsed_s": round(elapsed, 3),
        "tokens_per_s": round(tokens / elapsed, 1) if elapsed else 0,
        "emit_window_s": round(emit_window, 4),
        "dispatch_tokens_per_s": round(tokens / emit_window, 1) if emit_window else 0,
        "wakeups": counters["wakeups"],
        "python_cost_per_token_ms": round((elapsed / tokens) * 1000, 4) if tokens else 0,
    }


def main() -> int:
    lib_path = sys.argv[1] if len(sys.argv) > 1 else "build-shared/libhypercore_api.so"
    lib = ctypes.CDLL(lib_path)
    lib.hypercore_engine_init.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.c_char_p]
    lib.hypercore_engine_init.restype = ctypes.c_int
    lib.hypercore_engine_get_caps.argtypes = [ctypes.c_void_p, ctypes.POINTER(CapsStruct)]
    lib.hypercore_engine_get_caps.restype = ctypes.c_int
    lib.hypercore_engine_submit.argtypes = [
        ctypes.c_void_p, ctypes.c_uint64, ctypes.POINTER(RequestConfig),
        ctypes.POINTER(ctypes.c_int32), ctypes.c_size_t, CMPFUNC, ctypes.c_void_p,
    ]
    lib.hypercore_engine_submit.restype = ctypes.c_int

    handle = ctypes.c_void_p()
    if lib.hypercore_engine_init(ctypes.byref(handle), b"{}") != SUCCESS:
        print("init failed")
        return 1
    caps = CapsStruct(struct_size=ctypes.sizeof(CapsStruct))
    lib.hypercore_engine_get_caps(handle, ctypes.byref(caps))
    print(f"engine: slots={caps.max_batch_slots} workers={caps.active_pool_workers} ctx={caps.max_context_len}")

    # Fresh handle per run: destroy() joins the threads, so each variant starts clean.
    def fresh_handle():
        h = ctypes.c_void_p()
        if lib.hypercore_engine_init(ctypes.byref(h), b"{}") != SUCCESS:
            raise RuntimeError("init failed")
        return h

    print(f"{'variant':>8} {'conc':>5} {'tokens':>8} {'elapsed':>9} {'emit_win':>9} "
          f"{'dispatch tok/s':>15} {'wakeups':>8} {'ms/token':>9}")
    for concurrency in (1, min(4, caps.max_batch_slots)):
        for variant, flush in (("C", 0), ("A", 0), ("B", 1), ("B", 16), ("B", 64)):
            r = run_variant(lib, fresh_handle(), variant, concurrency, 4000, flush)
            print(f"{r['variant']:>8} {r['concurrency']:>5} {r['tokens']:>8} "
                  f"{r['elapsed_s']:>9} {r['emit_window_s']:>9} "
                  f"{r['dispatch_tokens_per_s']:>15} {r['wakeups']:>8} "
                  f"{r['python_cost_per_token_ms']:>9}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
