#!/usr/bin/env python3
"""tools/context_cliff_probe.py - separate two things that look alike.

"Throughput drops on long runs" can mean either:
  (a) the CONTEXT is large (the KV cache and the attention read more memory per token), or
  (b) the GENERATION is long (something drifts as the run goes on: cache eviction,
      a shrinking working set, thermal or allocator effects).

These are different failures with different fixes. A pin-order change only helps (a)
if the loss is really a host-memory effect; it does nothing for (b).

The probe runs two arms against a live server:

  context arm: fixed generation length, prompt grown over several sizes.
               reports prefill time and steady decode tok/s per size.
  duration arm: fixed small prompt, generation grown; decode tok/s reported in
               windows, so drift inside one run is visible rather than averaged away.

Run:
    python3 tools/context_cliff_probe.py --key 0000
    python3 tools/context_cliff_probe.py --targets 1024,4096,16384,65536 --gen 256
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request

FILLER = ("The maintenance log of the cooling loop reads as follows. Section {i}: the "
          "pump bearing temperature is recorded every four seconds, the differential "
          "pressure across the filter is compared with the previous hour, and any "
          "reading outside the band is written to the operator's queue with the "
          "timestamp and the sensor id. Nothing in this section is used for the "
          "answer; it is here to make the context longer. ")

def make_prompt(tokens: int) -> str:
    # ~60 tokens per repetition; the server reports the real count afterwards
    reps = max(1, tokens // 60 + 1)
    return "".join(FILLER.format(i=i) for i in range(reps))

def stream_run(url: str, key: str, prompt: str, gen: int) -> dict:
    body = json.dumps({
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": gen,
        "stream": True,
        "temperature": 0.0,
    }).encode()
    req = urllib.request.Request(url, data=body,
                                 headers={"Content-Type": "application/json",
                                         "Authorization": "Bearer " + key})
    t0 = time.perf_counter()
    first = None
    stamps = []          # (token_index, arrival)
    got = 0
    usage = {}
    for raw in urllib.request.urlopen(req, timeout=180):
        line = raw.decode(errors="replace").strip()
        if not line.startswith("data:"):
            continue
        if line == "data: [DONE]":
            break
        try:
            obj = json.loads(line[5:])
        except json.JSONDecodeError:
            continue
        usage = obj.get("usage", usage) or usage
        delta = obj.get("choices", [{}])[0].get("delta", {})
        text = (delta.get("content", "") or "") + (delta.get("reasoning_content", "") or "")
        if text:
            n = len(text.split())
            if first is None:
                first = time.perf_counter()
            for _ in range(max(1, n)):
                got += 1
                stamps.append((got, time.perf_counter()))
    end = time.perf_counter()
    return {"first": (first - t0) if first else None, "total": end - t0,
            "tokens": got, "stamps": stamps, "usage": usage}

def window_rate(stamps, total, w):
    """tok/s inside each w-token window, so drift shows up instead of averaging out."""
    out = []
    if not stamps:
        return out
    start = stamps[0][1]
    for k in range(0, total, w):
        seg = [t for i, t in stamps if k < i <= k + w]
        if not seg:
            continue
        a = start if k == 0 else stamps[k - 1][1]
        out.append(w / (seg[-1] - a))
    return out

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8080/v1/chat/completions")
    ap.add_argument("--key", default="0000")
    ap.add_argument("--targets", default="1024,4096,16384,65536")
    ap.add_argument("--gen", type=int, default=256)
    ap.add_argument("--duration", default="256,1024,2048")
    ap.add_argument("--window", type=int, default=256)
    a = ap.parse_args()

    print("=== context arm: fixed generation, growing prompt ===")
    print(f"{'prompt tok':>10} {'gen tok':>7} {'prefill s':>10} {'decode tok/s':>13} {'total s':>8}")
    for tgt in [int(x) for x in a.targets.split(",")]:
        r = stream_run(a.url, a.key, make_prompt(tgt), a.gen)
        dec = r["total"] - (r["first"] or 0.0)
        rate = r["tokens"] / dec if dec > 0.01 else 0.0
        real = r["usage"].get("prompt_tokens", 0)
        wr = window_rate(r["stamps"], r["tokens"], a.window)
        print(f"{real:>10} {r['tokens']:>7} {r['first'] or 0.0:>10.2f} {rate:>13.1f} {r['total']:>8.2f}  "
              f"windows: {' '.join(f'{x:.0f}' for x in wr)}")

    print("\n=== duration arm: fixed prompt, growing generation, tok/s per window ===")
    for gen in [int(x) for x in a.duration.split(",")]:
        r = stream_run(a.url, a.key, "Summarise the state of a cooling loop in one paragraph.", gen)
        rates = window_rate(r["stamps"], r["tokens"], a.window)
        print(f"gen {r['tokens']:>5} tok: prefill {r['first'] or 0.0:.2f} s, "
              f"overall {r['tokens'] / max(0.01, r['total'] - (r['first'] or 0.0)):.1f} tok/s, "
              f"windows: {' '.join(f'{x:.0f}' for x in rates)}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
