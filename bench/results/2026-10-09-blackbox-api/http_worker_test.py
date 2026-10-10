#!/usr/bin/env python3
"""bench/results/2026-10-09-blackbox-api/http_worker_test.py

Decision 2 and 3 together: the worker client inside a stdlib ThreadingHTTPServer, and
what happens when a client hangs up mid-stream.

ThreadingHTTPServer gives one thread per request, so a request thread can block on the
queue directly - no asyncio. The interesting question is not whether streaming works, it
is whether a dropped connection releases the batch slot. With batch=1, the proof is that
a second request is accepted after the first one is abandoned.

Run: python3 bench/results/2026-10-09-blackbox-api/http_worker_test.py
"""
from __future__ import annotations

import json
import pathlib
import socket
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from serve.hypercore_supervisor import HyperCoreProcessSupervisor, WorkerBusy
from serve.ipc_parser import STREAM_TOKEN, STREAM_TERMINAL

WORKER = str(ROOT / "build-shared/hypercore-worker")
SOCK_PATH = "/tmp/http_worker_test.sock"
PORT = 8091

results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, note: str = "") -> None:
    results.append((name, ok, note))
    print(f"{'PASS' if ok else 'FAIL'}: {name}" + (f" - {note}" if note else ""))


class Handler(BaseHTTPRequestHandler):
    worker: HyperCoreProcessSupervisor

    def do_GET(self) -> None:
        if self.path.startswith("/slots"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(self.worker.caps).encode())
            return

        if not self.path.startswith("/generate"):
            self.send_response(404)
            self.end_headers()
            return

        max_new = int(self.path.split("?max_new=")[1]) if "?max_new=" in self.path else 50
        request_id = self.worker.next_request_id()

        # Decide the status before the headers go out. A BUSY request must be a 503, not a
        # 200 with an empty body - the client cannot tell "no tokens" from "no capacity".
        try:
            stream = self.worker.stream([1, 2, 3, 4], max_new_tokens=max_new,
                                       timeout_s=30, request_id=request_id)
            first = next(stream)
        except WorkerBusy as exc:  # the worker's own slot gate said no
            self._reject(503, str(exc))
            return
        except Exception as exc:  # noqa: BLE001 - the server must not die on an engine fault
            self._reject(500, str(exc))
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()

        delivered = 0
        try:
            tag, token_id, summary = first
            if tag == STREAM_TERMINAL:
                self.wfile.write(f"\nDONE {json.dumps(summary)}\n".encode())
            else:
                self.wfile.write(f"{token_id}\n".encode())
                delivered += 1
                for tag, token_id, summary in stream:
                    if tag == STREAM_TERMINAL:
                        self.wfile.write(f"\nDONE {json.dumps(summary)}\n".encode())
                        break
                    self.wfile.write(f"{token_id}\n".encode())
                    delivered += 1
        except (BrokenPipeError, ConnectionResetError):
            # The client hung up. This is the only place the server learns it.
            self.worker.cancel(request_id)
            print(f"[server] client dropped after {delivered} tokens; cancel issued for {request_id}")
        except Exception as exc:  # noqa: BLE001
            print(f"[server] stream failed: {exc}")

    def _reject(self, status: int, note: str) -> None:
        """Answer before any token is written, so a refusal is never confused with an empty stream."""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"error": note}).encode())

    def log_message(self, format: str, *args) -> None:
        return


def read_until_close(sock: socket.socket) -> bytes:
    out = b""
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            return out
        out += chunk
        if len(out) > 100000:
            return out


def stream_from_client(max_new: int, stop_after: int | None = None) -> list[int]:
    """A raw socket client, so we can close it mid-stream the way a browser tab does."""
    s = socket.create_connection(("127.0.0.1", PORT), timeout=30)
    s.sendall(f"GET /generate?max_new={max_new} HTTP/1.1\r\nHost: x\r\n\r\n".encode())
    tokens: list[int] = []
    buf = b""
    while True:
        chunk = s.recv(4096)
        if not chunk:
            break
        buf += chunk
        for line in buf.split(b"\n"):
            if line.strip().lstrip(b"-").isdigit():
                tokens.append(int(line))
        buf = buf.split(b"\n")[-1]
        if stop_after and len(tokens) >= stop_after:
            break
    s.close()  # the tab closes
    return tokens


def wait_for_slot_free(worker: HyperCoreProcessSupervisor, timeout_s: float = 10.0) -> bool:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        try:
            n = sum(1 for tag, _t, _s in worker.stream([1, 2, 3], max_new_tokens=5, timeout_s=10)
                    if tag == STREAM_TOKEN)
            if n == 5:
                return True
        except Exception:
            time.sleep(0.2)
    return False


def main() -> int:
    worker = HyperCoreProcessSupervisor(WORKER, SOCK_PATH, '{"batch":1}')
    worker.start()

    Handler.worker = worker
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    try:
        # 1. the endpoint streams
        tokens = stream_from_client(30)
        check("a ThreadingHTTPServer request streams all its tokens", len(tokens) == 30,
              f"tokens={len(tokens)}")

        # 2. with batch=1, a second request while the first is running is refused
        s1 = socket.create_connection(("127.0.0.1", PORT), timeout=30)
        s1.sendall(b"GET /generate?max_new=1000 HTTP/1.1\r\nHost: x\r\n\r\n")
        time.sleep(0.3)
        s2 = socket.create_connection(("127.0.0.1", PORT), timeout=30)
        s2.sendall(b"GET /generate?max_new=10 HTTP/1.1\r\nHost: x\r\n\r\n")
        body = read_until_close(s2)
        check("a saturated worker answers with 503, not an empty 200",
              b"503" in body and b"no free batch slot" in body,
              f"first bytes={body[:90]!r}")
        s2.close()

        # 3. the client hangs up; the slot must come back
        s1.close()
        time.sleep(0.3)
        reclaimed = wait_for_slot_free(worker)
        check("closing the client socket releases the batch slot", reclaimed)

        # 4. the /slots endpoint reports real numbers, not sentinels
        s = socket.create_connection(("127.0.0.1", PORT), timeout=10)
        s.sendall(b"GET /slots HTTP/1.1\r\nHost: x\r\n\r\n")
        body = read_until_close(s)
        payload = json.loads(body.split(b"\r\n\r\n", 1)[1])
        s.close()
        check("/slots reports resolved pool size", payload["active_pool_workers"] > 0, str(payload))
    finally:
        server.shutdown()
        worker.stop()

    failed = [n for n, ok, _ in results if not ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed"
          + (f"; failed: {failed}" if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
