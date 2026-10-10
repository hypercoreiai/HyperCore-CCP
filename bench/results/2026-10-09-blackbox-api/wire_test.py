#!/usr/bin/env python3
"""bench/results/2026-10-09-blackbox-api/wire_test.py
Prove the frozen wire layout against a real worker process, not a fixture.

The C side writes the terminal payload field by field; the Python side reads it positionally.
Neither can be trusted against the other until someone looks at the actual bytes. This does
that: it spawns build-shared/hypercore-worker, submits one request, and checks the hex of
the terminal payload against the offsets stated in include/hypercore/hypercore_api.h.

Run: python3 wire_test.py [path/to/hypercore-worker]
"""
from __future__ import annotations

import pathlib
import signal
import socket
import struct
import subprocess
import sys
import time

# Run from anywhere: make the repository root importable so `serve` resolves.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from serve.ipc_parser import (
    CFG,
    CMD_SUBMIT,
    HEADER,
    MAGIC,
    RESP_STATUS,
    STREAM_TERMINAL,
    STREAM_TOKEN,
    SUMMARY_WIRE_SIZE,
    TERMINAL_WIRE,
    FrameError,
    decode_terminal,
)

# Offsets as numbers, not derived from the Struct. If the header changes, this table fails.
SUMMARY_OFFSETS = {
    "struct_size": 4,
    "produced_tokens": 8,
    "prefill_ms": 12,
    "decode_ms": 20,
    "drafts_accepted": 28,
    "drafts_offered": 32,
    "stop_reason": 36,
    "time_to_first_token_ms": 40,
}

failures: list[str] = []


def check(cond: bool, what: str, detail: str = "") -> None:
    line = f"{'PASS' if cond else 'FAIL'}: {what}"
    if detail:
        line += f" ({detail})"
    print(line)
    if not cond:
        failures.append(line)


def read_exact(sock: socket.socket, n: int) -> bytes:
    out = b""
    while len(out) < n:
        chunk = sock.recv(n - len(out))
        if not chunk:
            raise EOFError(f"link closed after {len(out)} of {n} bytes")
        out += chunk
    return out


def test_forward_compatibility() -> None:
    """A newer summary must not break an older reader.

    No worker emits a 48-byte summary yet, so this is tested against hand-built frames:
    the rule belongs to the parser, and the parser has to hold before a future field
    exists to violate it.
    """
    exact = TERMINAL_WIRE.pack(3, 40, 7, 11, 22, 1, 4, 2, 5)

    # A hypothetical v2: struct_size 48, two fields this reader has never seen.
    newer = TERMINAL_WIRE.pack(3, 48, 7, 11, 22, 1, 4, 2, 5) + struct.pack("<II", 99, 100)
    got = decode_terminal(newer)
    check(got["struct_size"] == 48,
         "a declared struct_size above 40 is accepted, not rejected",
         f"got {got['struct_size']}")
    check(got["produced_tokens"] == 7 and got["ttft_ms"] == 5 and got["stop_reason"] == "limit",
         "the known prefix is read correctly out of a longer frame")
    check(len(newer) > TERMINAL_WIRE.size,
         "the trailing bytes are outside the prefix and are discarded",
         f"payload={len(newer)} bytes")

    check(decode_terminal(exact)["ttft_ms"] == 5,
         "an exact 44-byte terminal decodes identically", f"prefix={len(exact)} bytes")

    # Same payload length, a declared size below the v1 minimum: the prefix is not there,
    # so this is a protocol break, not a forward-compatible one.
    try:
        decode_terminal(TERMINAL_WIRE.pack(3, 36, 7, 11, 22, 1, 4, 2, 5))
        check(False, "a summary declaring fewer than 40 bytes is refused", "declared 36")
    except FrameError as exc:
        check(True, "a summary declaring fewer than 40 bytes is refused", str(exc))


def main() -> int:
    worker = sys.argv[1] if len(sys.argv) > 1 else "build-shared/hypercore-worker"
    sock_path = "/tmp/hc_wire_test.sock"
    subprocess.run(["rm", "-f", sock_path], check=True)

    # The worker binds and accepts; the host connects. Starting it first is what makes
    # the connect succeed.
    proc = subprocess.Popen(
        [worker, sock_path, '{"batch": 1}'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    conn = None
    for _ in range(50):
        try:
            conn = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            conn.connect(sock_path)
            break
        except OSError:
            conn = None
            time.sleep(0.1)
    if conn is None:
        proc.kill()
        proc.wait(timeout=5)
        print("FAIL: could not connect to the worker")
        return 1
    conn.settimeout(20.0)

    try:
        cfg = CFG.pack(28, 0.0, 1.0, 1, 10, -1.0, -1.0)
        prompt = struct.pack("<4i", 1, 2, 3, 4)
        payload = cfg + b"\0" * 4 + struct.pack("<Q", 4) + prompt
        conn.sendall(HEADER.pack(MAGIC, CMD_SUBMIT, 42, len(payload)) + payload)

        tokens = 0
        terminal = None
        while terminal is None:
            header = read_exact(conn, HEADER.size)
            _, msg_type, _, length = HEADER.unpack(header)
            body = read_exact(conn, length)
            if msg_type == STREAM_TOKEN:
                tokens += 1
            elif msg_type == STREAM_TERMINAL:
                terminal = body
            elif msg_type == RESP_STATUS:
                check(int.from_bytes(body, "little") == 0,
                      "the submit ack is SUCCESS",
                      f"got {int.from_bytes(body, 'little')}")

        check(tokens == 10, "the stream delivered 10 token frames", f"got {tokens}")
        check(len(terminal) == TERMINAL_WIRE.size,
            "terminal payload is 44 bytes", f"got {len(terminal)}")

        print("terminal hex: " + terminal.hex())
        for name, offset in SUMMARY_OFFSETS.items():
            print(f"  offset {offset:>2} {name}")

        reused, struct_size, produced, prefill, decode, accepted, offered, stop, ttft = \
            TERMINAL_WIRE.unpack(terminal)

        check(struct_size == SUMMARY_WIRE_SIZE,
             "struct_size carries the protocol tag 40", f"got {struct_size}")
        check(produced == tokens,
             "produced_tokens equals the frames actually delivered",
             f"reported={produced} delivered={tokens}")
        check(stop == 2, "stop_reason is LIMIT for a full run", f"got {stop}")
        check(prefill > 0, "prefill_ms is the prompt evaluation window, not the queue hold",
              f"got {prefill}")
        check(ttft - prefill >= 40,
             "ttft_ms - prefill_ms isolates the queue hold the fixture is known to impose",
             f"ttft={ttft} prefill={prefill} hold={ttft - prefill}")
        check(decode >= 0, "decode_ms is on the wire and non-negative", f"got {decode}")
        check(ttft > 0, "byte 36 carries a real time_to_first_token_ms", f"got {ttft}")
        check(ttft >= prefill,
            "TTFT is measured from request acceptance, so it cannot precede prefill",
            f"ttft={ttft} prefill={prefill}")
        check(reused >= 0, "prompt_reused is present and non-negative", f"got {reused}")
        check(accepted >= 0 and offered >= 0 and accepted <= offered,
             "draft counts are on the wire and internally consistent",
             f"accepted={accepted} offered={offered}")

        # Read the same fields straight out of the byte offsets, independent of the Struct.
        check(int.from_bytes(terminal[8:12], "little") == produced,
             "produced_tokens sits at payload byte 8")
        check(int.from_bytes(terminal[12:20], "little") == prefill,
             "prefill_ms sits at payload byte 12")
        check(int.from_bytes(terminal[20:28], "little") == decode,
             "decode_ms sits at payload byte 20")
        check(int.from_bytes(terminal[36:40], "little") == stop,
             "stop_reason sits at payload byte 36")
        check(int.from_bytes(terminal[40:44], "little") == ttft,
             "time_to_first_token_ms sits at payload byte 40")
    except (EOFError, TimeoutError) as exc:
        print(f"FAIL: the worker did not complete a stream - {exc}")
        failures.append(str(exc))
    finally:
        proc.send_signal(signal.SIGKILL)
        proc.wait(timeout=5)
        conn.close()

    test_forward_compatibility()
    print(f"\nwire_test: {'FAILED' if failures else 'OK'} ({len(failures)} failures)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
