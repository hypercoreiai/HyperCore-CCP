"""serve/test_shutdown.py - the banner's Shut Down button (#641).

Two things are tested: the route that asks for a shutdown, and the closing order that
main() then runs. The closing is the same code Ctrl+C and SIGTERM use, and it is plain
Python - no signals, no process scanning - so it behaves the same on Windows and Linux.

    python -m unittest serve.test_shutdown -v
"""
from __future__ import annotations

import json
import sys
import unittest
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from serve.frontend import ChatTemplate
from serve.server import (
    ByteTokenizer,
    MockEngine,
    Service,
    close_everything,
    serve,
)

ROOT = Path(__file__).resolve().parents[1]


class ClosingEngine(MockEngine):
    """A mock engine that records how it was stopped, and has a proc like the real one."""

    def __init__(self, *a, interrupt_on_close: bool = False, **kw):
        super().__init__(*a, **kw)
        self.closed = False
        self.killed = False
        self.interrupt_on_close = interrupt_on_close
        self.proc = self  # close()/kill() are what main() looks for

    def close(self):
        if self.interrupt_on_close:
            raise KeyboardInterrupt
        self.closed = True

    def kill(self):
        self.killed = True


class FakeVision:
    def __init__(self):
        self.shutdown_called = False

    def shutdown(self):
        self.shutdown_called = True


class FakeHub:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


def make_service(engine, vision=None, hub=None, api_key=""):
    tok = ByteTokenizer()
    svc = Service(engine, tok, ChatTemplate(ROOT / "serve/chat_template.jinja"), vision=vision)
    svc.api_key = api_key
    if hub is not None:
        svc.mcp = hub
    return svc


class ShutdownRoute(unittest.TestCase):
    """POST /v1/shutdown asks; main()'s wait loop does the closing."""

    @classmethod
    def setUpClass(cls):
        cls.engine = ClosingEngine(ByteTokenizer(), "ok", max_context=4096)
        cls.svc = make_service(cls.engine)
        cls.httpd = serve(cls.svc, port=0)
        cls.port = cls.httpd.server_address[1]

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def post(self, path, body=None, headers=None):
        h = {"Content-Type": "application/json"}
        h.update(headers or {})
        req = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{path}",
            data=json.dumps(body if body is not None else {}).encode(), headers=h)
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return r.status, json.loads(r.read() or "{}")
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read() or "{}")

    def test_it_asks_and_sets_the_flag(self):
        self.svc.stop_requested.clear()
        code, body = self.post("/v1/shutdown")
        self.assertEqual(code, 200, body)
        self.assertEqual(body["status"], "shutting_down")
        self.assertTrue(self.svc.stop_requested.is_set(), "main() waits on this event")
        self.assertIn("the model engine", body["closing"], "the page says what is being closed")

    def test_a_second_click_is_harmless(self):
        code, _ = self.post("/v1/shutdown")
        self.assertEqual(code, 200)
        self.assertTrue(self.svc.stop_requested.is_set())

    def test_a_foreign_page_cannot_stop_the_server(self):
        self.svc.stop_requested.clear()
        code, body = self.post("/v1/shutdown", headers={"Origin": "https://elsewhere.example"})
        self.assertEqual(code, 403, body)
        self.assertFalse(self.svc.stop_requested.is_set(), "the request was refused, so nothing stops")

    def test_it_needs_json(self):
        self.svc.stop_requested.clear()
        req = urllib.request.Request(f"http://127.0.0.1:{self.port}/v1/shutdown",
                                                   data=b"", headers={"Content-Type": "text/plain"})
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                code = r.status
        except urllib.error.HTTPError as e:
            code = e.code
        self.assertEqual(code, 415)
        self.assertFalse(self.svc.stop_requested.is_set())

    def test_a_key_is_required_when_the_server_has_one(self):
        svc = make_service(ClosingEngine(ByteTokenizer(), "ok", max_context=4096), api_key="secret")
        httpd = serve(svc, port=0)
        port = httpd.server_address[1]
        try:
            req = urllib.request.Request(f"http://127.0.0.1:{port}/v1/shutdown",
                                                      data=b"{}", headers={"Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=10) as r:
                    got = r.status
            except urllib.error.HTTPError as e:
                got = e.code
            self.assertEqual(got, 401, "a server with a key does not let anyone shut it down")
            self.assertFalse(svc.stop_requested.is_set())
            req = urllib.request.Request(f"http://127.0.0.1:{port}/v1/shutdown",
                                                      data=b"{}",
                                                      headers={"Content-Type": "application/json",
                                                             "Authorization": "Bearer secret"})
            with urllib.request.urlopen(req, timeout=10) as r:
                self.assertEqual(r.status, 200)
            self.assertTrue(svc.stop_requested.is_set())
        finally:
            httpd.shutdown()
            httpd.server_close()


class ClosingOrder(unittest.TestCase):
    """What main() closes, and in what order."""

    def test_every_process_this_server_started_is_closed(self):
        engine, vision, hub = ClosingEngine(ByteTokenizer(), "ok", max_context=4096), FakeVision(), FakeHub()
        svc = make_service(engine, vision, hub)
        httpd = serve(svc, port=0)
        closed = close_everything(svc, httpd)
        httpd.server_close()
        self.assertEqual(closed, ["the HTTP server", "the model engine", "the image encoder", "the MCP servers"])
        self.assertTrue(engine.closed and vision.shutdown_called and hub.closed)

    def test_the_http_server_stops_first(self):
        # Nothing new can arrive once the listener is down, so the engine is not asked to
        # free its memory while a request is still running.
        order: list[str] = []
        engine = ClosingEngine(ByteTokenizer(), "ok", max_context=4096)
        engine.close = lambda: order.append("engine")
        hub = FakeHub()
        hub.close = lambda: order.append("hub")
        svc = make_service(engine, None, hub)
        httpd = serve(svc, port=0)
        real = httpd.shutdown
        httpd.shutdown = lambda: (order.append("http"), real())[1]
        close_everything(svc, httpd)
        httpd.server_close()
        self.assertEqual(order, ["http", "engine", "hub"])

    def test_an_engine_that_will_not_free_its_memory_is_killed_not_left_running(self):
        engine = ClosingEngine(ByteTokenizer(), "ok", max_context=4096, interrupt_on_close=True)
        svc = make_service(engine)
        httpd = serve(svc, port=0)
        closed = close_everything(svc, httpd)
        httpd.server_close()
        self.assertTrue(engine.killed, "a second Ctrl+C must not leave the worker running")
        self.assertFalse(engine.closed)
        self.assertIn("the model engine", closed)

    def test_a_server_with_no_engine_or_hub_still_closes_cleanly(self):
        svc = make_service(MockEngine(ByteTokenizer(), "ok", max_context=4096))
        httpd = serve(svc, port=0)
        closed = close_everything(svc, httpd)
        httpd.server_close()
        self.assertEqual(closed, ["the HTTP server"])


if __name__ == "__main__":
    unittest.main()
