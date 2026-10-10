#!/usr/bin/env python3
"""tools/frame_probe.py - dump every frame a real worker emits for one request.

Run: python3 tools/frame_probe.py
"""
from __future__ import annotations

import socket
import subprocess
import sys
import time

sys.path.insert(0, "/home/ai-user0/HyperCore")
from serve.ipc_parser import (  # noqa: E402
    HEADER,
    MAGIC,
    RESP_STATUS,
    STREAM_TERMINAL,
    STREAM_TOKEN,
    build_submit_frame,
)

SOCK = "/tmp/hc_frame_probe.sock"


def main() -> int:
    subprocess.run(["rm", "-f", SOCK], check=False)
    cfg = open("/tmp/hc_probe_config.json", encoding="utf-8").read()
    proc = subprocess.Popen(
        ["build-shared/hypercore-worker", SOCK, cfg],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    conn = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    for _ in range(200):
        try:
            conn.connect(SOCK)
            break
        except FileNotFoundError:
            time.sleep(0.02)
    else:
        print("worker never opened the socket:", proc.stderr.read().decode()[:300])
        proc.kill()
        return 1
    conn.settimeout(10)

    conn.sendall(build_submit_frame(1, temperature=0.0, top_p=1.0, top_k=1,
                                    max_new_tokens=25, prompt_tokens=[1, 2, 3, 4]))

    tokens = 0
    seen: list[tuple[int, int, int]] = []
    while True:
        head = conn.recv(24)
        if len(head) < 24:
            print("short header:", len(head))
            break
        magic, msg_type, request_id, payload_len = HEADER.unpack(head)
        body = conn.recv(payload_len) if payload_len else b""
        seen.append((msg_type, payload_len, len(body)))
        if msg_type == STREAM_TOKEN:
            tokens += 1
        elif msg_type == STREAM_TERMINAL:
            print("terminal payload", payload_len, "bytes:", body.hex())
            break
        elif msg_type == RESP_STATUS:
            print("status payload:", body.hex())
        if len(seen) > 80:
            print("too many frames")
            break
    print("tokens:", tokens, "first frames:", seen[:3], "last:", seen[-1:] if seen else None)
    proc.kill()
    proc.wait()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
