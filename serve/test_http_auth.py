#!/usr/bin/env python3
"""Tests for the one API-key gate both HTTP fronts use.

Two separate claims are checked, because they fail for different reasons:

  1. the rule (serve/http_auth.py): what counts as a key, and what does not;
  2. that both fronts actually call it, and that the stub's gate bites at the HTTP
     level - a request without a key is refused before the queue is touched.

(2) is the reason the module exists. A stub that passes the flood test while ignoring the
key is not a stand-in for the server, it is a second server, and the CI guard would be
proving nothing about the one that ships.
"""
from __future__ import annotations

import json
import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

import serve.flood_stub
import serve.server
from serve.flood_stub import FloodHandler
from serve.http_auth import auth_error, is_open, key_matches, supplied_key
from serve.ipc_parser import STREAM_TERMINAL, STREAM_TOKEN

KEY = "s3cret-token"


class ScriptedSupervisor:
    """Enough of HyperCoreProcessSupervisor for the stub's routes, with no process.

    The count of requests that reached it is the point: an unauthenticated request must
    never get as far as a slot.
    """

    def __init__(self, slots: int = 2) -> None:
        self.slots = slots
        self.reached_queue = 0
        self.cancelled: list[int] = []

    def alive(self) -> bool:
        return True

    def get_caps(self) -> dict[str, int]:
        return {"max_batch_slots": self.slots, "max_context_len": 4096}

    def in_flight(self) -> int:
        return 0

    def next_request_id(self) -> int:
        self.reached_queue += 1
        return self.reached_queue

    def stream(self, prompt: list[int], **tuning: object):
        for i in range(4):
            yield (STREAM_TOKEN, 100 + i, None)
        yield (STREAM_TERMINAL, 0, {"produced_tokens": 4})

    def cancel(self, request_id: int) -> bool:
        self.cancelled.append(request_id)
        return True


class StubFront:
    """The stub HTTP front, on an ephemeral port, over a scripted supervisor."""

    def __init__(self, api_key: str = "", slots: int = 2) -> None:
        self.supervisor = ScriptedSupervisor(slots)
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), FloodHandler)
        self.server.supervisor = self.supervisor  # type: ignore[attr-defined]
        self.server.api_key = api_key  # type: ignore[attr-defined]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    @property
    def port(self) -> int:
        return self.server.server_port

    def request(self, method: str, path: str, headers: dict[str, str] | None = None) -> tuple[int, dict]:
        conn = HTTPConnection("127.0.0.1", self.port, timeout=5.0)
        try:
            conn.request(method, path, headers=headers or {})
            resp = conn.getresponse()
            raw = resp.read()
        finally:
            conn.close()
        try:
            return resp.status, json.loads(raw)
        except json.JSONDecodeError:
            return resp.status, {}

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()


class TheKeyRule(unittest.TestCase):
    """What the gate accepts, in isolation."""

    def test_no_key_configured_means_no_gate(self):
        self.assertTrue(is_open(""))
        self.assertTrue(key_matches({}, ""))
        self.assertTrue(key_matches({"Authorization": "Bearer anything"}, ""))

    def test_a_configured_key_refuses_a_missing_one(self):
        self.assertFalse(key_matches({}, KEY))
        self.assertFalse(key_matches({"Authorization": ""}, KEY))
        self.assertFalse(key_matches({"Authorization": "Bearer "}, KEY))
        self.assertFalse(key_matches({"x-api-key": ""}, KEY))

    def test_bearer_is_accepted_in_the_form_the_sdk_sends_it(self):
        self.assertTrue(key_matches({"Authorization": f"Bearer {KEY}"}, KEY))
        self.assertTrue(key_matches({"authorization": f"bearer {KEY}"}, KEY))
        self.assertTrue(key_matches({"Authorization": f"Bearer   {KEY}  "}, KEY))

    def test_x_api_key_is_accepted(self):
        self.assertTrue(key_matches({"x-api-key": KEY}, KEY))
        self.assertFalse(key_matches({"x-api-key": "wrong"}, KEY))

    def test_authorization_wins_when_both_headers_are_present(self):
        # A stale x-api-key on a request that also carries a bearer token is a client bug,
        # not a second credential; the gate must not silently accept the wrong one.
        self.assertTrue(key_matches({"Authorization": f"Bearer {KEY}", "x-api-key": "stale"}, KEY))
        self.assertFalse(key_matches({"Authorization": "Bearer wrong", "x-api-key": KEY}, KEY))

    def test_supplied_key_is_what_it_looks_like(self):
        self.assertEqual(supplied_key({"Authorization": f"Bearer {KEY}"}), KEY)
        self.assertEqual(supplied_key({"x-api-key": KEY}), KEY)
        self.assertEqual(supplied_key({}), "")

    def test_a_non_ascii_key_does_not_break_the_comparison(self):
        self.assertTrue(key_matches({"x-api-key": "café"}, "café"))
        self.assertFalse(key_matches({"x-api-key": "cafe"}, "café"))

    def test_the_refusal_has_the_body_clients_already_parse(self):
        body = auth_error()
        self.assertEqual(body["error"]["type"], "authentication_error")
        self.assertTrue(body["error"]["message"])


class TheStubAndTheServerShareOneGate(unittest.TestCase):
    """Not two implementations of the rule - the same function object."""

    def test_both_fronts_import_the_same_function(self):
        self.assertIs(serve.flood_stub.key_matches, key_matches)
        self.assertIs(serve.server.key_matches, key_matches)
        self.assertIs(serve.flood_stub.auth_error, auth_error)
        self.assertIs(serve.server.auth_error, auth_error)

    def test_an_open_front_answers_every_route(self):
        front = StubFront(api_key="", slots=2)
        try:
            status, body = front.request("GET", "/health")
            self.assertEqual(status, 200)
            self.assertTrue(body["ok"])
            self.assertFalse(body["api_key"])

            status, body = front.request("GET", "/v1/slots")
            self.assertEqual(status, 200)
            self.assertEqual(body["max_batch_slots"], 2)
        finally:
            front.close()

    def test_a_key_required_refuses_before_the_queue_is_touched(self):
        front = StubFront(api_key=KEY, slots=2)
        try:
            status, body = front.request("GET", "/v1/slots")
            self.assertEqual(status, 401)
            self.assertEqual(body["error"]["type"], "authentication_error")

            status, _ = front.request("POST", "/infer/stream")
            self.assertEqual(status, 401)
            self.assertEqual(front.supervisor.reached_queue, 0,
                             "an unauthenticated request reached the worker queue")
        finally:
            front.close()

    def test_health_is_never_gated_and_says_whether_a_key_is_needed(self):
        front = StubFront(api_key=KEY, slots=2)
        try:
            status, body = front.request("GET", "/health")
            self.assertEqual(status, 200)
            self.assertTrue(body["api_key"], "health must tell a probe a key is required")
        finally:
            front.close()

    def test_the_key_is_accepted_through_both_headers_and_the_stream_runs(self):
        front = StubFront(api_key=KEY, slots=2)
        try:
            for headers in ({"Authorization": f"Bearer {KEY}"}, {"x-api-key": KEY}):
                conn = HTTPConnection("127.0.0.1", front.port, timeout=5.0)
                try:
                    conn.request("POST", "/infer/stream",
                                 json.dumps({"tokens": [101, 2043], "max_new_tokens": 4}),
                                 {"Content-Type": "application/json", **headers})
                    resp = conn.getresponse()
                    # The stream has no Content-Length: the terminal frame is the end of
                    # the body, so read frame by frame rather than to EOF.
                    frames = []
                    while True:
                        line = resp.readline()
                        if not line:
                            break
                        if line.startswith(b"data: "):
                            frame = json.loads(line[6:])
                            frames.append(frame)
                            if frame.get("done"):
                                break
                finally:
                    conn.close()
                self.assertEqual(resp.status, 200, f"key via {list(headers)} was refused")
                self.assertTrue(frames[-1]["done"], "the stream never reached its terminal frame")
            self.assertEqual(front.supervisor.reached_queue, 2)
        finally:
            front.close()

    def test_a_wrong_key_is_a_401_not_a_500(self):
        front = StubFront(api_key=KEY, slots=2)
        try:
            status, body = front.request("POST", "/infer/stream", {"Authorization": "Bearer nope"})
            self.assertEqual(status, 401)
            self.assertEqual(body["error"]["type"], "authentication_error")
        finally:
            front.close()


if __name__ == "__main__":
    unittest.main()
