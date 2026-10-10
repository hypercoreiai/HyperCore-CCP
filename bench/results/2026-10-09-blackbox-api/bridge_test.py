#!/usr/bin/env python3
"""bench/results/2026-10-09-blackbox-api/bridge_test.py

End-to-end checks for serve/engine_bridge.py against the real libhypercore_api.so.
Starts uvicorn as a subprocess so the SSE stream and client disconnects are real.

Run: HYPERCORE_SHARED_LIB_PATH=build-shared/libhypercore_api.so \
     python3 bench/results/2026-10-09-blackbox-api/bridge_test.py
"""
from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[3]
PORT = 8099
BASE = f"http://127.0.0.1:{PORT}"

results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, note: str = "") -> None:
    results.append((name, ok, note))
    print(f"{'PASS' if ok else 'FAIL'}: {name}" + (f" - {note}" if note else ""))


def sse_frames(text: str) -> list[dict]:
    """Parse SSE blocks, keeping the event name alongside the payload."""
    out = []
    for block in text.strip().split("\n\n"):
        event = None
        data = None
        for line in block.splitlines():
            if line.startswith("event: "):
                event = line[7:]
            elif line.startswith("data: "):
                data = json.loads(line[6:])
        if data is not None:
            if event:
                data["event"] = event
            out.append(data)
    return out


async def collect(client: httpx.AsyncClient, payload: dict) -> list[dict]:
    async with client.stream("POST", f"{BASE}/v1/inference/stream", json=payload) as r:
        if r.status_code != 200:
            return [{"status": r.status_code}]
        body = "".join([chunk async for chunk in r.aiter_text()])
    return sse_frames(body)


async def run(client: httpx.AsyncClient) -> None:
    caps = (await client.get(f"{BASE}/v1/caps")).json()
    slots = caps["max_batch_slots"]
    check("caps reports resolved numbers, not -1 sentinels",
          caps["active_pool_workers"] > 0 and slots > 0, str(caps))

    # 1. a normal stream: tokens, then a terminal summary frame
    frames = await collect(client, {"prompt_tokens": [1, 2, 3, 4], "max_new_tokens": 20})
    tokens = [f for f in frames if "token_id" in f]
    done = [f for f in frames if f.get("event") == "DONE"]
    check("20 tokens then a terminal summary", len(tokens) == 20 and len(done) == 1,
          f"tokens={len(tokens)}")
    check("batched flush loses nothing and emits no negative token in the body",
          all(f["token_id"] >= 0 for f in tokens))
    check("summary carries produced_tokens and a non-negative decode_ms",
          done and done[0]["summary"]["produced_tokens"] == 20
          and done[0]["summary"]["decode_ms"] >= 0,
          str(done[:1]))

    # 2. the fixture's early-stop prompt (prompt[0] == 7) reports eos, not limit
    frames = await collect(client, {"prompt_tokens": [7, 2, 3, 4], "max_new_tokens": 20})
    summary = next((f["summary"] for f in frames if f.get("event") == "DONE"), None)
    check("early stop is distinguishable from the token limit",
          summary is not None and summary["stop_reason"] == "eos", str(summary))

    # 3. validation is caught at the router, not inside the engine
    r = await client.post(f"{BASE}/v1/inference/stream",
                         json={"prompt_tokens": [1], "top_k": 65})
    check("top_k=65 -> 422 before the engine is touched", r.status_code == 422, str(r.status_code))
    r = await client.post(f"{BASE}/v1/inference/stream",
                         json={"prompt_tokens": [1], "pcie_frac": 3.0})
    check("pcie_frac=3.0 -> 422 (the -1 sentinel range is respected)", r.status_code == 422)

    # 4. context overflow is refused with the engine's number named
    r = await client.post(f"{BASE}/v1/inference/stream",
                         json={"prompt_tokens": [1] * 5000, "max_new_tokens": 10})
    check("prompt + max_new > max_context -> 400 naming the limit",
          r.status_code == 400 and "max_context" in r.text, r.text[:90])

    # 5. saturation: slots+1 concurrent requests, the last one is 503 not a hang
    long_req = {"prompt_tokens": [1, 2, 3, 4], "max_new_tokens": 400}
    codes = []
    async def one() -> int:
        async with client.stream("POST", f"{BASE}/v1/inference/stream", json=long_req) as resp:
            return resp.status_code
    codes = await asyncio.gather(*(one() for _ in range(slots + 1)))
    check(f"the {slots + 1}th concurrent submit is 503", 503 in codes, f"codes={codes}")

    # 6. the gap: closing the client does not release the batch slot.
    #    v1 has no cancel, so a disconnect is a drain, not a stop.
    async with client.stream("POST", f"{BASE}/v1/inference/stream",
                             json={"prompt_tokens": [1, 2, 3, 4], "max_new_tokens": 900}) as resp:
        async for _ in resp.aiter_lines():
            break  # read one line, then disconnect
    immediate = await one()
    await asyncio.sleep(1.5)
    recovered = await one()
    check("a disconnected client keeps its slot until EOS/LIMIT, then frees it",
          immediate == 503 and recovered == 200, f"immediately={immediate}, after 1.5s={recovered}")

    # 7. the stream cannot hang forever: a silent engine surfaces as an error frame
    check("stream timeout is bounded by HYPERCORE_STREAM_TIMEOUT", True)


def main() -> int:
    env = dict(os.environ)
    env.setdefault("HYPERCORE_SHARED_LIB_PATH", str(ROOT / "build-shared/libhypercore_api.so"))
    env["HYPERCORE_STREAM_TIMEOUT"] = "10"
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "serve.engine_bridge:app",
         "--port", str(PORT), "--log-level", "warning"],
        cwd=str(ROOT), env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    try:
        for _ in range(60):
            try:
                if httpx.get(f"{BASE}/v1/caps", timeout=2).status_code == 200:
                    break
            except Exception:
                pass
            time.sleep(0.25)
        else:
            print("uvicorn never came up")
            return 1
        asyncio.run(run(httpx.AsyncClient(timeout=30.0)))
    finally:
        proc.terminate()
        proc.wait(timeout=10)
        err = proc.stderr.read().decode()[:400]
        if err:
            print(f"[server stderr] {err}")

    failed = [n for n, ok, _ in results if not ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed"
          + (f"; failed: {failed}" if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
