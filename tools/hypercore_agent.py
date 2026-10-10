#!/usr/bin/env python3
"""tools/hypercore_agent.py - a client-side wrapper that keeps a task to its end.

HyperCore already gives a client everything it needs to do this; the wrapper just puts
it together:

  GET /health     -> is the server up and is the model loaded (no key needed)
  GET /status     -> busy, queued, phase, tokens generated so far
  GET /metrics    -> live.state: reading | generating | idle | unloaded, tok_s, elapsed_s
  POST /v1/chat/completions (stream=true)
      data: {...} chunks, ": keep-alive" comments while the engine is quiet or a tool
      is running, then a final chunk with finish, then data: [DONE]
      chunks may carry a "hypercore_mcp" field: start / call / result / limit events

A "task" is complete when the stream ends with finish == "stop". Anything else is an
interruption, and each kind has a different recovery:

  length      -> hit max_tokens; continue from where it stopped
  limit       -> the MCP round cap was reached; ask it to finish with what it has
  error       -> the engine died; the server restarts it on the next request, so retry
  disconnect  -> this client closed the socket; retry once
  cancel      -> the user pressed Stop; do not retry

The wrapper heartbeats /health and /status on a timer while a task runs, and watches
the stream for progress. A stall is no token and no tool activity for --stall-s
seconds: the connection is closed (the server sees an OSError and stops the engine),
and the task is retried or reported as stalled rather than left hanging.

    python tools/hypercore_agent.py --task "list the MCP servers and their state"
    python tools/hypercore_agent.py --watch                 # heartbeat only, print each tick
    python tools/hypercore_agent.py --task "..." --mcp --json

Standard library only, like the rest of serve/.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request

DEFAULT_URL = os.environ.get("HYPERCORE_URL", "http://127.0.0.1:8081")
DEFAULT_KEY = os.environ.get("HYPERCORE_API_KEY", os.environ.get("API_KEY", "0000"))
DEFAULT_MODEL = "qwen3.8-flash-next-q2_0"

COMPLETED = "stop"
# A stall closes the stream, which the server sees as a disconnect and answers by
# stopping the engine; retrying is the same recovery as a dropped connection.
RETRYABLE = {"error", "disconnect", "stall"}
CONTINUE = {"length", "limit", "tool_calls"}


class HyperCoreClient:
    """A small, synchronous client for the HyperCore HTTP interface."""

    def __init__(self, url: str = DEFAULT_URL, key: str = DEFAULT_KEY, timeout_s: float = 30.0,
            stream_timeout_s: float = 300.0):
        self.url = url.rstrip("/")
        self.key = key
        self.timeout_s = timeout_s
        # A request can spend minutes reading a large prompt. The socket timeout is per
        # operation, so a stream needs a much longer one than a status call.
        self.stream_timeout_s = stream_timeout_s
        self.serial = threading.Lock()   # the server runs one request at a time; do not fight it

    # ---- liveness ----------------------------------------------------------
    def _get(self, path: str, timeout: float | None = None):
        req = urllib.request.Request(self.url + path)
        if self.key:
            req.add_header("Authorization", "Bearer " + self.key)
        try:
            with urllib.request.urlopen(req, timeout=timeout or self.timeout_s) as r:
                return json.loads(r.read().decode("utf-8", "replace"))
        except (urllib.error.URLError, OSError, ValueError) as e:
            return {"error": str(e)}

    def health(self) -> dict:
        return self._get("/health")

    def status(self) -> dict:
        return self._get("/status")

    def live(self) -> dict:
        m = self._get("/metrics")
        return m.get("live") or {"state": "unknown", "error": m.get("error", "no metrics")}

    def last_finish(self) -> str | None:
        """How the most recent request really ended.

        The OpenAI dialect reports a cancelled request as finish_reason "stop"
        (serve/server.py maps "cancel" to "stop"), so the stream alone cannot tell a
        finished answer from one the user stopped. /metrics keeps the server's own
        record: stop, length, cancel, disconnect or error.
        """
        m = self._get("/metrics")
        rows = m.get("requests") or []
        return rows[0].get("finish") if rows else None

    def heartbeat(self) -> dict:
        """One snapshot: is it up, is it busy, how far along is the work."""
        h = self.health()
        s = self.status()
        l = self.live()
        now = time.time()
        return {
            "at": now,
            "up": bool(h.get("status") == "ok"),
            "loaded": bool(h.get("loaded")),
            "busy": bool(s.get("busy")),
            "queued": int(s.get("queued") or 0),
            "state": l.get("state"),
            "phase": l.get("phase"),
            "generated": l.get("generated"),
            "max_tokens": l.get("max_tokens"),
            "elapsed_s": l.get("elapsed_s"),
            "tok_s": l.get("tok_s"),
        }

    # ---- a task ------------------------------------------------------------
    def run(self, task: str, system: str = "", mcp: bool = True, max_tokens: int = 0,
            stall_s: float = 120.0, max_attempts: int = 3, max_continuations: int = 3,
            heartbeat_s: float = 5.0, on_event=None) -> dict:
        """Run one task and return it only when it is genuinely finished.

        Returns {"completed": bool, "finish": str, "text": str, "attempts": int,
                "continuations": int, "stalls": int, "rounds": int, "log": [...]}
        """
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": task})

        attempts = continuations = stalls = rounds = 0
        text, log = "", []
        while True:
            attempts += 1
            result = self._stream(messages, mcp, max_tokens, stall_s, heartbeat_s, on_event, log)
            # The server's own record beats the dialect's finish_reason: a cancelled
            # request is reported to clients as "stop".
            recorded = self.last_finish()
            if recorded and result["finish"] == "stop" and recorded != "stop":
                result["finish"] = recorded
                log.append(f"stream said stop, the server recorded {recorded}")
            finish = result["finish"]
            text += result["text"]
            rounds += result["rounds"]
            stalls += result["stalls"]

            if finish == COMPLETED:
                return {"completed": True, "finish": finish, "text": text, "attempts": attempts,
                        "continuations": continuations, "stalls": stalls, "rounds": rounds, "log": log}

            if finish in CONTINUE and continuations < max_continuations:
                continuations += 1
                log.append(f"finish={finish}; continuing from where it stopped "
                          f"({continuations}/{max_continuations})")
                if result["text"]:
                    messages.append({"role": "assistant", "content": result["text"]})
                messages.append({"role": "user", "content": "Continue from exactly where you stopped."})
                continue

            if finish in RETRYABLE and attempts < max_attempts:
                log.append(f"finish={finish}; retrying (attempt {attempts + 1}/{max_attempts})")
                time.sleep(min(2.0 * attempts, 10.0))   # the server restarts a dead engine on the next request
                continue

            return {"completed": False, "finish": finish, "text": text, "attempts": attempts,
                    "continuations": continuations, "stalls": stalls, "rounds": rounds, "log": log}

    def _stream(self, messages, mcp, max_tokens, stall_s, heartbeat_s, on_event, log) -> dict:
        body = {"model": DEFAULT_MODEL, "messages": messages, "stream": True}
        if max_tokens:
            body["max_tokens"] = int(max_tokens)
        if mcp:
            body["hypercore_mcp"] = True

        text, finish, rounds, stalls = [], None, 0, 0
        last_progress = time.time()
        stopper = threading.Event()

        seen = {"prompt_read": None, "generated": None}

        def beat():
            """Poll the interface while the task runs.

            Progress is not only tokens: reading a 200k-token prompt takes a minute and
            emits nothing, and a slow tool call emits nothing either. The server reports
            both - prompt_read/prompt_total while prefilling, generated while decoding,
            and a phase while a tool runs - so any of them moving resets the clock.
            """
            nonlocal last_progress
            while not stopper.is_set():
                if stopper.wait(heartbeat_s):
                    return
                hb = self.heartbeat()
                if not hb["up"]:
                    log.append("heartbeat: server not reachable")
                    continue
                live = self.live()
                moved = bool(live.get("phase"))
                if live.get("prompt_total") and live.get("prompt_read") != seen["prompt_read"]:
                    seen["prompt_read"] = live["prompt_read"]
                    moved = True
                if live.get("generated") and live.get("generated") != seen["generated"]:
                    seen["generated"] = live["generated"]
                    moved = True
                if moved:
                    last_progress = time.time()
                quiet = time.time() - last_progress
                if hb["busy"] and quiet > stall_s:
                    log.append(f"heartbeat: busy for {hb['elapsed_s'] or quiet:.0f} s, "
                              f"no output for {quiet:.0f} s")

        ticker = threading.Thread(target=beat, daemon=True)
        ticker.start()
        try:
            with self.serial:
                req = urllib.request.Request(self.url + "/v1/chat/completions",
                                           data=json.dumps(body).encode("utf-8"),
                                           headers={"Content-Type": "application/json",
                                                  "Accept": "text/event-stream",
                                                  "Authorization": "Bearer " + self.key})
                with urllib.request.urlopen(req, timeout=self.stream_timeout_s) as r:
                    for line in r:
                        line = line.decode("utf-8", "replace").strip()
                        if not line or line.startswith(":"):     # the SSE keep-alive comment
                            if time.time() - last_progress > stall_s:
                                finish = "stall"
                                stalls += 1
                                break
                            continue
                        if not line.startswith("data:"):
                            continue
                        payload = line[5:].strip()
                        if payload == "[DONE]":
                            break
                        try:
                            chunk = json.loads(payload)
                        except ValueError:
                            continue
                        if chunk.get("error"):
                            finish = "error"
                            log.append("stream error: " + str(chunk["error"].get("message")))
                            break
                        activity = chunk.get("hypercore_mcp")
                        if activity:
                            if activity.get("event") == "limit":
                                finish = "limit"
                            elif activity.get("event") == "result":
                                rounds += 1
                            last_progress = time.time()          # tool activity is progress
                            if on_event:
                                on_event(activity)
                            continue
                        delta = (chunk.get("choices") or [{}])[0].get("delta") or {}
                        if delta.get("content") or delta.get("reasoning_content") or delta.get("tool_calls"):
                            text.append(delta.get("content") or "")
                            last_progress = time.time()
                        if chunk.get("choices") and chunk["choices"][0].get("finish_reason"):
                            finish = chunk["choices"][0]["finish_reason"]
                        if chunk.get("timings"):
                            last_progress = time.time()
        except (urllib.error.URLError, OSError) as e:
            if finish is None:
                finish = "disconnect"
                log.append("connection closed: " + str(e))
        finally:
            stopper.set()
        return {"text": "".join(text), "finish": finish or "disconnect", "rounds": rounds, "stalls": stalls}


def watch(client: HyperCoreClient, interval: float, until: float | None) -> int:
    """Heartbeat until the server is idle and nothing is queued, or until --until."""
    started = time.time()
    while True:
        hb = client.heartbeat()
        print(f"{time.strftime('%H:%M:%S')}  up={hb['up']} loaded={hb['loaded']} "
              f"state={hb['state']} busy={hb['busy']} queued={hb['queued']} "
              f"generated={hb['generated']}/{hb['max_tokens']} tok/s={hb['tok_s']}", flush=True)
        if not hb["busy"] and not hb["queued"]:
            return 0
        if until and time.time() - started > until:
            return 1
        time.sleep(interval)


def main() -> int:
    ap = argparse.ArgumentParser(description="Heartbeat HyperCore and drive a task to completion.")
    ap.add_argument("--url", default=DEFAULT_URL)
    ap.add_argument("--key", default=DEFAULT_KEY)
    ap.add_argument("--task", help="The task to run to completion.")
    ap.add_argument("--system", default="", help="Optional system prompt.")
    ap.add_argument("--no-mcp", action="store_true", help="Do not offer the MCP tools.")
    ap.add_argument("--max-tokens", type=int, default=0)
    ap.add_argument("--stall-s", type=float, default=120.0,
                        help="Seconds with no token and no tool activity before a stall. A large "
                             "prompt spends minutes reading it, so this must be generous.")
    ap.add_argument("--max-attempts", type=int, default=3)
    ap.add_argument("--max-continuations", type=int, default=3)
    ap.add_argument("--heartbeat-s", type=float, default=5.0)
    ap.add_argument("--watch", action="store_true", help="Heartbeat only; exit when idle.")
    ap.add_argument("--until", type=float, default=0, help="With --watch: give up after this many seconds.")
    ap.add_argument("--json", action="store_true", help="Print the result as JSON.")
    args = ap.parse_args()

    client = HyperCoreClient(args.url, args.key)

    if args.watch:
        return watch(client, args.heartbeat_s, args.until or None)

    if not args.task:
        ap.error("give --task, or --watch")

    hb = client.heartbeat()
    if not hb["up"]:
        print(f"[agent] the server at {client.url} is not reachable: {hb}", file=sys.stderr)
        return 2
    print(f"[agent] target reachable: state={hb['state']}, loaded={hb['loaded']}", flush=True)

    def show(ev):
        if ev.get("event") == "call":
            print(f"[agent] round {ev.get('round')}: {ev.get('name')}({json.dumps(ev.get('arguments'))[:120]})",
                  flush=True)
        elif ev.get("event") == "result":
            print(f"[agent]   -> {ev.get('chars')} chars in {ev.get('ms')} ms"
                  + (" (skipped)" if ev.get("skipped") else ""), flush=True)

    result = client.run(args.task, args.system, not args.no_mcp, args.max_tokens,
                       args.stall_s, args.max_attempts, args.max_continuations,
                       args.heartbeat_s, show if not args.json else None)

    if args.json:
        print(json.dumps(result, indent=1))
    else:
        print("\n" + result["text"])
        print(f"\n[agent] completed={result['completed']} finish={result['finish']} "
              f"attempts={result['attempts']} continuations={result['continuations']} "
              f"tool rounds={result['rounds']}")
        for line in result["log"]:
            print("[agent] " + line)
    return 0 if result["completed"] else 1


if __name__ == "__main__":
    sys.exit(main())
