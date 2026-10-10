#!/usr/bin/env python3
"""serve/fixtures/fake_engine.py - a stand-in for the real engine, for tests.

It speaks the same --serve protocol as src/program/generate.cpp:

    stdin :  GEN <max_new> <id,id,...>   STOP   QUIT
    stdout:  READY <max_context> <stop_id>
             INFO model=... max_context=...
             PP <pos> <total> <ms> <tok/s>
             T <id>
             DONE <generated> <prompt> <prompt_ms> <decode_ms> <finish>
                  <drafts_accepted> <drafts_offered> <reused>

so the boundary can be tested end to end - spawn, ready handshake, tokens, DONE - without
a model, a GPU, or the 34 GB pack. The tokens it emits are the prompt shifted by one and
the timings are the ones the caller asked for, which is the point: the numbers reaching the
other side must be the ones the engine printed, not the fixture's constants.

STOP is read on its own thread, as the real engine does (generate.cpp reads stdin on a
thread so a cancel reaches a request that is still running). Without that, a cancel would
only be noticed after the request had already finished and the test would prove nothing.

Run it by hand to see the protocol:

    ./serve/fixtures/fake_engine.py --serve
    GEN 5 1,2,3
"""
from __future__ import annotations

import argparse
import queue
import sys
import threading
import time


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--serve", action="store_true", help="read requests from stdin")
    ap.add_argument("--max-context", type=int, default=8192)
    ap.add_argument("--prefill-ms", type=float, default=120.0)
    ap.add_argument("--decode-ms", type=float, default=240.0)
    ap.add_argument("--token-ms", type=float, default=0.0, help="pause between tokens, to make TTFT measurable")
    ap.add_argument("--model", default="fake-model")
    ap.add_argument("--fail-start", help="print ERR <this> and exit, to test the failure path")
    ap.add_argument("--die-after", type=int, default=0, help="exit after this many requests")
    args = ap.parse_args()

    if args.fail_start:
        print(f"ERR {args.fail_start}", flush=True)
        return 1

    def emit(line: str) -> None:
        print(line, flush=True)

    emit(f"READY {args.max_context} 0")
    emit(f"INFO model={args.model} batch_slots=0 max_context={args.max_context}")

    # stdin on its own thread: a STOP has to reach a request that is still running.
    commands: queue.Queue[str] = queue.Queue()

    def reader() -> None:
        for line in sys.stdin:
            line = line.strip()
            if line:
                commands.put(line)
        commands.put("EOF")

    threading.Thread(target=reader, daemon=True).start()

    requests = 0
    stop_requested = False

    while True:
        try:
            line = commands.get(timeout=5)
        except queue.Empty:
            break
        if line == "EOF":
            break
        if line == "QUIT":
            break
        if line == "STOP":
            stop_requested = True
            continue
        if not line.startswith("GEN"):
            continue

        parts = line.split(None, 2)
        max_new = int(parts[1])
        prompt = [int(x) for x in (parts[2].split(",") if len(parts) > 2 and parts[2] else [])]
        requests += 1

        emitted = 0
        for i in range(max_new):
            # check for a cancel between tokens, the way the engine checks it in its loop
            while not commands.empty():
                cmd = commands.get()
                if cmd == "STOP":
                    stop_requested = True
                elif cmd == "QUIT":
                    stop_requested = True
                    break
            if stop_requested:
                break
            if args.token_ms:
                time.sleep(args.token_ms / 1000.0)
            emit(f"T {prompt[i % len(prompt)] + 1 if prompt else 1000 + i}")
            emitted += 1

        finish = "cancel" if stop_requested else "length"
        stop_requested = False
        emit(f"PP {len(prompt)} {len(prompt)} {args.prefill_ms:.1f} "
            f"{len(prompt) * 1000.0 / max(args.prefill_ms, 1.0):.1f}")
        emit(f"REUSED {min(2, len(prompt))}")
        emit(f"DONE {emitted} {len(prompt)} {args.prefill_ms:.1f} {args.decode_ms:.1f} {finish} "
            f"3 5 {min(2, len(prompt))} 1 2 1 1 1")

        if args.die_after and requests >= args.die_after:
            break

    return 0


if __name__ == "__main__":
    sys.exit(main())
