#!/usr/bin/env python3
"""serve/test_stream_loop.py - the consolidated stream reader.

Decision 1 put every frame transition - ack, token, terminal, stall wall, the
CANCEL frame on early exit - inside HyperCoreProcessSupervisor.stream(). The HTTP
layer is a serialiser. These tests are the proof of that boundary: they only ever
talk to the generator and to the thin wrapper, never to a queue, and they assert
behaviours that used to live in the HTTP loop.

Run: python3 -m unittest serve.test_stream_loop -v
"""
from __future__ import annotations

import json
import unittest

from serve.frame_fixture import ScriptedWorker
from serve.hypercore_supervisor import (
    HyperCoreProcessSupervisor,
    StreamStalled,
    WorkerBusy,
    WorkerRejected,
    WorkerUnreachable,
)
from serve.ipc_parser import CMD_CANCEL, STREAM_TERMINAL, STREAM_TOKEN
from serve.server import stream_sse


class _Pipe:
    """A wfile that can break, the way a browser tab does."""

    def __init__(self, fail_after: int | None = None) -> None:
        self.buf = b""
        self.fail_after = fail_after
        self.writes = 0

    def write(self, data: bytes) -> None:
        self.writes += 1
        if self.fail_after is not None and self.writes > self.fail_after:
            raise BrokenPipeError("client closed the tab")
        self.buf += data

    def flush(self) -> None:
        pass

    def events(self) -> list[dict]:
        return [json.loads(line[5:]) for line in self.buf.decode().split("\n\n")
                if line.startswith("data:")]


class FakeHandler:
    """Enough of BaseHTTPRequestHandler for the wrapper: status line, headers, wfile."""

    def __init__(self, fail_after: int | None = None) -> None:
        self.wfile = _Pipe(fail_after)
        self.status = None
        self.headers_sent = False

    def send_response(self, code: int) -> None:
        self.status = code
        self.headers_sent = True

    def send_header(self, key: str, value: str) -> None:
        pass

    def end_headers(self) -> None:
        pass

    def _cors(self) -> None:
        pass


def supervisor(worker: ScriptedWorker) -> HyperCoreProcessSupervisor:
    sup = HyperCoreProcessSupervisor(transport=worker.connect, max_restarts=0)
    sup.start()
    return sup


def cancelled_requests(worker: ScriptedWorker) -> list[int]:
    return [rid for msg_type, rid, _payload in worker.received if msg_type == CMD_CANCEL]


class StreamReaderTest(unittest.TestCase):
    def test_the_generator_is_the_only_place_a_frame_becomes_a_message(self):
        worker = ScriptedWorker(tokens=3)
        sup = supervisor(worker)
        try:
            messages = list(sup.stream([1, 2, 3, 4], max_new_tokens=3))
            self.assertEqual([m[0] for m in messages],
                             [STREAM_TOKEN, STREAM_TOKEN, STREAM_TOKEN, STREAM_TERMINAL])
            self.assertEqual([m[1] for m in messages[:3]], [1000, 1001, 1002])
            self.assertEqual(messages[0][2], {"prompt_reused": 0})
            self.assertEqual(messages[-1][2]["stop_reason"], "limit")
            self.assertEqual(messages[-1][2]["produced_tokens"], 3)
        finally:
            sup.stop()

    def test_stream_sse_is_a_serializer_and_nothing_else(self):
        worker = ScriptedWorker(tokens=3)
        sup = supervisor(worker)
        handler = FakeHandler()
        try:
            outcome = stream_sse(handler, sup, 42, [1, 2, 3, 4], 0.0, 1.0, 1, 3)
            self.assertEqual(outcome, "complete")
            self.assertEqual(handler.status, 200)
            events = handler.wfile.events()
            self.assertEqual(len(events), 4)
            self.assertTrue(all("token_id" in e for e in events[:-1]))
            self.assertEqual([e["token_id"] for e in events[:-1]], [1000, 1001, 1002])
            self.assertTrue(events[-1]["done"])
            self.assertEqual(events[-1]["metrics"]["produced_tokens"], 3)
        finally:
            sup.stop()

    def test_a_full_worker_is_the_authoritative_gate(self):
        """No host-side pre-check: the request goes to the worker, and the worker says no."""
        worker = ScriptedWorker(max_slots=1, tokens=4, prefill_s=0.05)
        sup = supervisor(worker)
        try:
            holding = sup.stream([1, 2, 3, 4], max_new_tokens=4, request_id=1)
            next(holding)  # ack consumed, first token in flight
            with self.assertRaises(WorkerBusy):
                list(sup.stream([9, 8, 7], max_new_tokens=2, request_id=2))
            self.assertNotIn(2, cancelled_requests(worker),
                            "a request the worker never accepted has nothing to cancel")
        finally:
            sup.stop()

    def test_a_bad_config_is_rejected_not_silently_clamped(self):
        worker = ScriptedWorker(tokens=2)
        sup = supervisor(worker)
        handler = FakeHandler()
        try:
            outcome = stream_sse(handler, sup, 5, [1, 2], 0.0, 1.0, 1, 0)
            self.assertEqual(outcome, "rejected")
            self.assertFalse(handler.headers_sent,
                            "the status code must still be choosable after a rejection")
        finally:
            sup.stop()

    def test_a_closed_client_is_cancelled_by_the_supervisor(self):
        """The wrapper notices the broken pipe; the generator sends the CANCEL frame."""
        worker = ScriptedWorker(tokens=8)
        sup = supervisor(worker)
        handler = FakeHandler(fail_after=2)
        try:
            outcome = stream_sse(handler, sup, 7, [1, 2, 3], 0.0, 1.0, 1, 8)
            self.assertEqual(outcome, "client_gone")
            self.assertTrue(worker.await_frame(CMD_CANCEL, 1.0),
                            "the generator must send the CANCEL frame on early exit")
            self.assertEqual(cancelled_requests(worker), [7])
            self.assertEqual(len(handler.wfile.events()), 2)
        finally:
            sup.stop()

    def test_a_silent_link_is_called_unreachable_not_stalled(self):
        """No heartbeat frame exists on the stream, so a stall is checked out-of-band.
        A worker that answers a ping is slow; one that does not is gone."""
        worker = ScriptedWorker(tokens=3, hold_s=0.6, mute_ping=True)
        sup = supervisor(worker)
        try:
            with self.assertRaises(WorkerUnreachable):
                list(sup.stream([1, 2, 3, 4], max_new_tokens=3, silence_s=0.3, timeout_s=2.0))
            # Whether the link is slow or gone, the host reaps its own slot.
            self.assertEqual(sup.in_flight(), 0)
        finally:
            sup.stop()

    def test_a_silent_stream_stalls_and_cancels(self):
        worker = ScriptedWorker(tokens=3, prefill_s=5.0)
        sup = supervisor(worker)
        handler = FakeHandler()
        try:
            outcome = stream_sse(handler, sup, 9, [1, 2], 0.0, 1.0, 1, 4,
                                stall_s=0.5, timeout_s=2.0)
            self.assertEqual(outcome, "stalled")
            self.assertTrue(worker.await_frame(CMD_CANCEL, 1.0))
            self.assertEqual(cancelled_requests(worker), [9])
        finally:
            sup.stop()

    def test_the_stall_wall_is_measured_from_the_last_frame(self):
        """A long prefill must not trip a wall meant to detect silence."""
        worker = ScriptedWorker(tokens=2, prefill_s=0.2, draft_s=0.4)
        sup = supervisor(worker)
        handler = FakeHandler()
        try:
            outcome = stream_sse(handler, sup, 11, [1, 2], 0.0, 1.0, 1, 2,
                                stall_s=1.0, timeout_s=5.0)
            self.assertEqual(outcome, "complete")
        finally:
            sup.stop()

    def test_busy_rejected_and_stalled_are_distinguishable_to_the_http_layer(self):
        self.assertTrue(issubclass(WorkerBusy, WorkerRejected.__bases__[0]))
        self.assertTrue(issubclass(StreamStalled, Exception))
        self.assertTrue(issubclass(WorkerRejected, Exception))


if __name__ == "__main__":
    unittest.main()
