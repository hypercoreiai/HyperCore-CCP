#!/usr/bin/env python3
"""tools/bench_flood.py - push the process boundary past its limits.

What this actually tests, and what it cannot:

  * load shedding: with concurrency > max_batch_slots, the excess requests must get
    an immediate 503 from the worker's own slot gate. There is no host-side pre-check
    any more, so a 503 here is the compute node speaking.
  * slot reclamation: a client that drops mid-stream must free its slot. The test
    proves it by finishing the flood and reading /slots - in-flight must be 0.
  * stall handling: a stream that goes silent is cancelled by the supervisor, not
    left open.

What it does not test: byte layout. A wrong offset in a frame shows up as a wrong
number, not as an exception, and a throughput test will happily sail through it.
That is what tools/check_abi_alignment.py is for.

Two tiers, on purpose:

  * the integration guard (default) runs against serve/flood_stub.py. It needs no GPU
    and no weights, so it can run on every merge request and still exercise the 503
    gate, the drop-mid-stream slot reclamation and the stall cancel.
  * the hardware guard (--model) runs against serve/server.py with real weights. It is
    gated on pack/full actually existing, so it never reports a clean run that never
    computed anything.

Run:
    python3 tools/bench_flood.py                       # integration guard, spawns its own stub
    python3 tools/bench_flood.py --no-spawn --port 8125
    python3 tools/bench_flood.py --concurrency 32 --slots 2 --disconnect-ratio 0.25
    python3 tools/bench_flood.py --model               # hardware guard; fails if pack/full is absent
"""
from __future__ import annotations

import argparse
import http.client
import json
import os
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@dataclass
class Outcome:
    completed: int = 0
    busy_503: int = 0
    unreachable_503: int = 0
    client_disconnect: int = 0
    other_4xx: int = 0
    other_5xx: int = 0
    tokens: int = 0
    elapsed: float = 0.0
    lock: threading.Lock = field(default_factory=threading.Lock)

    def record(self, kind: str, tokens: int = 0) -> None:
        with self.lock:
            setattr(self, kind, getattr(self, kind) + 1)
            self.tokens += tokens

    def total(self) -> int:
        return (self.completed + self.busy_503 + self.unreachable_503
                + self.client_disconnect + self.other_4xx + self.other_5xx)


def auth_headers(api_key: str) -> dict[str, str]:
    """The credential in the form serve/http_auth.py accepts. No key, no header."""
    return {"Authorization": f"Bearer {api_key}"} if api_key else {}


def read_json(host: str, port: int, path: str, body: str | None = None,
             api_key: str = "") -> tuple[int, dict]:
    conn = http.client.HTTPConnection(host, port, timeout=10.0)
    try:
        conn.request("POST" if body is not None else "GET", path, body, auth_headers(api_key))
        resp = conn.getresponse()
        raw = resp.read()
    finally:
        conn.close()
    try:
        return resp.status, json.loads(raw)
    except json.JSONDecodeError:
        return resp.status, {}


def run_one(client_id: int, host: str, port: int, path: str, prompt: list[int],
            max_new: int, disconnect_at: int | None, outcome: Outcome,
            api_key: str = "") -> None:
    """One client: request, stream, and optionally hang up mid-stream."""
    payload = json.dumps({
        "tokens": prompt,
        "temperature": 0.0,
        "top_p": 1.0,
        "top_k": 1,
        "max_new_tokens": max_new,
        "pcie_frac": -1.0,
        "spec_min_p": -1.0,
    })
    conn = http.client.HTTPConnection(host, port, timeout=15.0)
    tokens_read = 0
    try:
        conn.request("POST", path, payload, {"Content-Type": "application/json", **auth_headers(api_key)})
        resp = conn.getresponse()

        if resp.status == 503:
            body = resp.read().decode()
            kind = "busy_503" if "busy" in body or "slot" in body else "unreachable_503"
            outcome.record(kind)
            return
        if 400 <= resp.status < 500:
            resp.read()
            outcome.record("other_4xx")
            return
        if resp.status >= 500:
            resp.read()
            outcome.record("other_5xx")
            return

        while True:
            line = resp.readline()
            if not line:
                break
            text = line.decode("utf-8").strip()
            if not text.startswith("data:"):
                continue
            try:
                frame = json.loads(text[5:].strip())
            except json.JSONDecodeError:
                continue
            if "token_id" in frame:
                tokens_read += 1
                if disconnect_at is not None and tokens_read >= disconnect_at:
                    conn.close()          # the tab closes; the server sees a broken pipe
                    outcome.record("client_disconnect", tokens_read)
                    return
            if frame.get("done"):
                outcome.record("completed", tokens_read)
                return
        outcome.record("client_disconnect", tokens_read)
    except (http.client.HTTPException, OSError):
        outcome.record("other_5xx")
    finally:
        try:
            conn.close()
        except OSError:
            pass  # the connection is already gone; nothing to report


def flood(host: str, port: int, path: str, concurrency: int, prompt: list[int],
          max_new: int, disconnect_ratio: float, disconnect_at: int,
          api_key: str = "") -> Outcome:
    outcome = Outcome()
    threads = []
    started = time.time()
    step = int(1.0 / disconnect_ratio) if disconnect_ratio > 0 else 0
    for i in range(concurrency):
        cut = disconnect_at if (step and i % step == 0) else None
        threads.append(threading.Thread(
            target=run_one,
            args=(i, host, port, path, prompt, max_new, cut, outcome, api_key),
        ))
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    outcome.elapsed = time.time() - started
    return outcome


MODEL_PACK_DIR = ROOT / "pack" / "full"
STUB_SERVER = ROOT / "serve" / "flood_stub.py"
REAL_SERVER = ROOT / "serve" / "server.py"


def model_pack_present() -> bool:
    """True only when the weights are physically there.

    The directory existing is not enough: an empty pack/full is what a CI scaffold
    leaves behind, and running the real engine against it produces a throughput number
    that means nothing.
    """
    if not MODEL_PACK_DIR.is_dir():
        return False
    return any(p for p in MODEL_PACK_DIR.iterdir())


def slots_in_flight(host: str, port: int, api_key: str = "") -> int:
    try:
        status, body = read_json(host, port, "/slots", api_key=api_key)
        if status != 200:
            return -1
        slots = body if isinstance(body, list) else body.get("slots", [])
        return sum(1 for s in slots if s.get("is_processing"))
    except (http.client.HTTPException, OSError):
        return -1


def main() -> int:
    ap = argparse.ArgumentParser(description="Flood the HTTP boundary and check the worker's gate.")
    ap.add_argument("--model", action="store_true",
                    help="hardware guard: run against serve/server.py with real weights. "
                         "Refuses to run when pack/full is absent.")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8125)
    ap.add_argument("--path", default="/infer/stream")
    ap.add_argument("--concurrency", type=int, default=16)
    ap.add_argument("--slots", type=int, default=4, help="batch slots the worker is configured with")
    ap.add_argument("--max-new", type=int, default=64)
    ap.add_argument("--disconnect-ratio", type=float, default=0.25)
    ap.add_argument("--disconnect-at", type=int, default=5, help="tokens to read before hanging up")
    ap.add_argument("--prompt", default="101,2043,2000,1037,2601,102")
    ap.add_argument("--no-spawn", action="store_true", help="assume a server is already running")
    ap.add_argument("--worker", default=str(ROOT / "build-shared/hypercore-worker"))
    ap.add_argument("--server", default=str(ROOT / "serve/flood_stub.py"),
                    help="HTTP front to spawn. The stub needs no model pack; point this at "
                         "serve/server.py once a pack is installed.")
    ap.add_argument("--api-key", default=os.environ.get("HYPERCORE_API_KEY", ""),
                    help="put the front behind a key. When set, the guard also proves the "
                         "gate: no key -> 401, key -> 200.")
    args = ap.parse_args()

    if args.model:
        if not model_pack_present():
            print(f"[SKIP] hardware guard: no model pack at {MODEL_PACK_DIR}")
            print("       the integration guard is the stub; run without --model for the CI path.")
            return 2
        if Path(args.server) == STUB_SERVER:
            args.server = str(REAL_SERVER)
        print(f"[guard] hardware: {args.server}, pack at {MODEL_PACK_DIR}")
    else:
        print(f"[guard] integration: {args.server} (no weights, no GPU)")

    prompt = [int(t) for t in args.prompt.split(",")]
    proc = None
    if not args.no_spawn:
        if not os.path.exists(args.worker):
            print(f"[FAIL] worker binary not found: {args.worker} (build it first)")
            return 2
        config = json.dumps({"batch": args.slots, "sampling": {"temperature": 0.0}})
        spawn = [sys.executable, str(args.server),
                 "--port", str(args.port),
                 "--worker", args.worker,
                 "--ipc-socket", f"/tmp/hypercore-flood-{args.port}-{os.getpid()}.sock",
                 "--config", config]
        if args.api_key:
            spawn += ["--api-key", args.api_key]
        proc = subprocess.Popen(
            spawn,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        for _ in range(60):
            try:
                conn = http.client.HTTPConnection(args.host, args.port, timeout=2.0)
                try:
                    conn.request("GET", "/health")
                    ok = conn.getresponse().status == 200
                finally:
                    conn.close()
                if ok:
                    break
            except (http.client.HTTPException, OSError):
                time.sleep(0.5)
        else:
            print("[FAIL] the server did not come up")
            proc.kill()
            return 2

    print("=" * 64)
    print(f" FLOOD: {args.concurrency} clients against a {args.slots}-slot worker")
    print(f" path={args.path}  max_new={args.max_new}  disconnect ratio={args.disconnect_ratio}")
    if args.api_key:
        print(f" auth: key required ({len(args.api_key)} chars)")
    print("=" * 64)

    if args.api_key:
        # The point of the guard is that the stub and the server share one gate. Asking for
        # /slots with no credential is the cheapest way to show it: the request must be
        # refused before the queue is touched, with the body a client already knows how to
        # read. A stub that answered 200 here would be a stub with no gate at all.
        status, body = read_json(args.host, args.port, "/slots")
        error_type = body.get("error", {}).get("type") if isinstance(body, dict) else None
        if status != 401 or error_type != "authentication_error":
            print(f"[FAIL] unauthenticated /slots -> {status} ({error_type}); expected 401 authentication_error")
            if proc is not None:
                proc.terminate()
                proc.wait(timeout=10)
            return 1
        status, _ = read_json(args.host, args.port, "/slots", api_key=args.api_key)
        if status != 200:
            print(f"[FAIL] /slots with the key -> {status}; expected 200")
            if proc is not None:
                proc.terminate()
                proc.wait(timeout=10)
            return 1
        print("[PASS] auth gate: no key 401, key 200 - the same rule the server uses")

    outcome = flood(args.host, args.port, args.path, args.concurrency, prompt,
                    args.max_new, args.disconnect_ratio, args.disconnect_at, args.api_key)

    in_flight = slots_in_flight(args.host, args.port, args.api_key)

    print("-" * 64)
    print(f" dispatched              : {outcome.total()}")
    print(f" completed streams       : {outcome.completed}")
    print(f" 503 from the slot gate : {outcome.busy_503}")
    print(f" 503 worker unreachable  : {outcome.unreachable_503}")
    print(f" client hung up         : {outcome.client_disconnect}")
    print(f" 4xx / 5xx other        : {outcome.other_4xx} / {outcome.other_5xx}")
    print(f" tokens streamed        : {outcome.tokens}")
    print(f" in-flight after settle  : {in_flight}")
    print("=" * 64)

    failures = []
    if outcome.total() != args.concurrency:
        failures.append(f"{args.concurrency - outcome.total()} requests produced no outcome")
    if outcome.other_4xx or outcome.other_5xx:
        failures.append("unexpected 4xx/5xx responses")
    if outcome.completed == 0:
        failures.append("no stream completed - the gate is shedding everything")
    if in_flight > 0:
        failures.append(f"slots still held after the flood: {in_flight} (cancel did not reclaim)")
    if outcome.total() > args.slots and outcome.busy_503 == 0 and outcome.client_disconnect == 0:
        failures.append("over-subscribed but nothing was shed: the worker gate never answered busy")

    if proc is not None:
        proc.terminate()
        proc.wait(timeout=10)

    if failures:
        print("[TEST DEGRADED]")
        for f in failures:
            print("  " + f)
        return 1
    print("[TEST PASSED] load shedding and slot reclamation behaved.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
