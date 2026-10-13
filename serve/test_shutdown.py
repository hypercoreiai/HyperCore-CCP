"""serve/test_shutdown.py - the banner's Shut Down button (#641) and its Stop/Start pair.

Three things are tested: the route that asks for a shutdown, the closing order main()
then runs, and the /v1/stop - /v1/start pair that stops the engine and brings it back
without ending the process.

    python -m unittest serve.test_shutdown -v
"""
from __future__ import annotations

import json
import sys
import tempfile
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


class LifecycleEngine(MockEngine):
    """An engine that can be stopped and started, which is what the Stop/Start pair needs.

    It replays a scripted answer while it is up, and yields nothing while it is stopped - the shape of the
    empty reply the Monitor used to record as "Max tokens".
    """

    def __init__(self):
        super().__init__(ByteTokenizer(), "the engine is running", max_context=4096)
        self.running = True
        self.unloads = 0
        self.restarts = 0

    def generate(self, ids, max_new, sampling, cancel, embeddings=None):
        if not self.running:
            return
        yield from super().generate(ids, max_new, sampling, cancel, embeddings)

    def alive(self) -> bool:
        return self.running

    def unload(self) -> None:
        self.running = False
        self.unloads += 1

    def restart(self) -> bool:
        self.running = True
        self.restarts += 1
        return True


def turn_tokens(body) -> int:
    """How many tokens the turn produced. A stopped engine used to answer 200 with nothing in it; that
    is what the Monitor's Recent requests table then showed as "Max tokens". The fixture engine emits
    its own tokens rather than words, so the count - not the text - is what proves the engine ran."""
    return int((body.get("usage") or {}).get("completion_tokens") or 0)


class StopStartRoute(unittest.TestCase):
    """POST /v1/stop and POST /v1/start: the engine-only pair, for the API and the Monitor.

    Unlike /v1/shutdown these do not end the process: the HTTP server stays up, so the
    engine can be stopped and started without closing the page. The banner's Shut Down
    button is a different thing - it closes the server - and the composer's Start button
    sends a prompt, not this call.
    """

    def setUp(self):
        self.engine = LifecycleEngine()
        self.vision = FakeVision()
        self.hub = FakeHub()
        self.svc = make_service(self.engine, vision=self.vision, hub=self.hub)
        self.httpd = serve(self.svc, port=0)
        self.port = self.httpd.server_address[1]

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()

    def post(self, path, headers=None):
        h = {"Content-Type": "application/json"}
        h.update(headers or {})
        req = urllib.request.Request(f"http://127.0.0.1:{self.port}{path}", data=b"{}", method="POST", headers=h)
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return r.status, json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode())

    def test_stop_freezes_the_engine_and_keeps_the_server(self):
        code, body = self.post("/v1/stop")
        self.assertEqual(code, 200)
        self.assertEqual(body["status"], "stopped")
        self.assertIn("the model engine", body["stopped"])
        self.assertEqual(self.engine.unloads, 1)
        self.assertFalse(self.engine.running)
        self.assertTrue(self.svc.engine_stopped)
        self.assertFalse(self.svc.stop_requested.is_set())   # the process stays up
        self.assertFalse(self.httpd.server_address is None)

    def test_start_brings_the_engine_back(self):
        self.post("/v1/stop")
        code, body = self.post("/v1/start")
        self.assertEqual(code, 200)
        self.assertEqual(body["status"], "running")
        self.assertEqual(self.engine.restarts, 1)
        self.assertTrue(self.engine.running)
        self.assertFalse(self.svc.engine_stopped)

    def test_load_on_a_stopped_engine_is_the_start_and_not_a_refusal(self):
        """The Monitor's Load button posts /load. After /v1/stop that is the same request as
        /v1/start, so it must not be answered 409 the way a chat request is.
        """
        self.post("/v1/stop")
        code, body = self.post("/load")
        self.assertEqual(code, 200, body)
        self.assertEqual(body["status"], "loaded")
        self.assertFalse(self.svc.engine_stopped)
        self.assertTrue(self.engine.running)
        code, body = self.chat("say something")
        self.assertEqual(code, 200, body)
        self.assertTrue(turn_tokens(body), "the Load button brought the engine back and it answered")

    def test_a_start_that_does_not_come_back_is_a_503(self):
        class DeadEngine(LifecycleEngine):
            def restart(self):
                self.running = False
                return False
        self.post("/v1/stop")
        self.svc.engine = DeadEngine()
        code, body = self.post("/v1/start")
        self.assertEqual(code, 503)
        self.assertTrue(self.svc.engine_stopped)            # the button stays Start
        self.assertIn("message", body["error"])

    def test_a_request_while_stopped_is_refused_and_not_answered_with_nothing(self):
        """Stop -> chat -> Start -> chat.

        The bug this guards: a request that reaches a stopped engine used to come back as a 200 with an empty
        reply, which the Monitor's Recent requests table records as "Max tokens" (Service.run's default finish
        is "length") and the chat shows as a blank bubble.
        """
        code, body = self.chat("say something")
        self.assertEqual(code, 200, body)
        self.post("/v1/stop")
        code, body = self.chat("say something")
        self.assertEqual(code, 409, body)
        self.assertEqual(body["error"]["type"], "engine_stopped")
        self.assertIn("start", body["error"]["message"].lower())
        code, body = self.chat("say something")           # still stopped: it did not quietly reload
        self.assertEqual(code, 409, body)
        code, body = self.post("/v1/start")
        self.assertEqual(code, 200, body)
        code, body = self.chat("say something")
        self.assertEqual(code, 200, body)
        self.assertTrue(turn_tokens(body), "the engine came back and answered")

    def test_stop_start_does_not_use_up_the_crash_budget(self):
        """Deliberate Starts are not crashes: ten of them must not exhaust max_restarts."""
        class BudgetEngine:
            """An engine whose restart goes through a supervisor with a restart budget."""
            def __init__(self):
                self.supervisor = SupervisorStub(max_restarts=3)
            def alive(self):
                return self.supervisor.alive()
            def unload(self):
                self.supervisor.stop()
            def restart(self):
                return self.supervisor.start_worker()

        from serve.hypercore_supervisor import HyperCoreProcessSupervisor

        class SupervisorStub(HyperCoreProcessSupervisor):
            def __init__(self, max_restarts):
                super().__init__(worker_binary="missing-worker", socket_path="/tmp/hc-stop-start-test.sock",
                                max_restarts=max_restarts)
                self._started = 0
            def start(self, timeout_s=None):
                self._started += 1
            def alive(self):
                return self._started > 0 and self._proc is None
            def stop(self):
                self._started = 0

        engine = BudgetEngine()
        svc = make_service(engine)
        for _ in range(5):
            svc.engine_stopped = True
            self.assertTrue(svc.start_engine(), "a deliberate Start is refused by the crash budget")
            svc.engine_stopped = False
            svc.engine.unload()

    def chat(self, text):
        body = {"model": "mock", "messages": [{"role": "user", "content": text}]}
        req = urllib.request.Request(f"http://127.0.0.1:{self.port}/v1/chat/completions",
                                     data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return r.status, json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode() or "{}")

    def test_the_status_says_the_engine_is_stopped(self):
        """A client polling /v1/status can tell "stopped by the user" from "not loaded yet"."""
        with urllib.request.urlopen(f"http://127.0.0.1:{self.port}/v1/status", timeout=10) as r:
            body = json.loads(r.read().decode())
        self.assertFalse(body["engine_stopped"])
        self.post("/v1/stop")
        with urllib.request.urlopen(f"http://127.0.0.1:{self.port}/v1/status", timeout=10) as r:
            body = json.loads(r.read().decode())
        self.assertTrue(body["engine_stopped"], "the status reports the deliberate stop")
        self.assertFalse(body["loaded"])
        self.post("/v1/start")
        with urllib.request.urlopen(f"http://127.0.0.1:{self.port}/v1/status", timeout=10) as r:
            self.assertFalse(json.loads(r.read().decode())["engine_stopped"])

    def test_the_pair_is_not_open_to_a_foreign_origin(self):
        code, _ = self.post("/v1/stop", headers={"Origin": "https://elsewhere.example"})
        self.assertEqual(code, 403)
        self.assertTrue(self.engine.running)


class StopStartWithARealEngine(unittest.TestCase):
    """Stop -> chat -> Start -> chat against an engine process, not a mock.

    serve/fixtures/fake_engine.py speaks the same --serve protocol as src/program/generate.cpp, so the
    stop really ends a process and the start really spawns one again - without a model or a GPU.
    """

    FAKE_ENGINE = ROOT / "serve" / "fixtures" / "fake_engine.py"

    def setUp(self):
        from serve.fixtures.legacy_engine import HyperCoreEngine
        self.tmp = tempfile.TemporaryDirectory()
        self.engine = HyperCoreEngine(str(self.FAKE_ENGINE), ["--max-context", "4096"],
                                     log=str(Path(self.tmp.name) / "engine.log"))
        self.svc = make_service(self.engine)
        self.httpd = serve(self.svc, port=0)
        self.port = self.httpd.server_address[1]

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        try:
            self.engine.close()
        except Exception:  # noqa: BLE001, S110 - the process is already gone in most runs
            pass
        self.tmp.cleanup()

    def post(self, path):
        req = urllib.request.Request(f"http://127.0.0.1:{self.port}{path}", data=b"{}",
                                     method="POST", headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status, json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode() or "{}")

    def chat(self, text):
        body = {"model": "fake", "messages": [{"role": "user", "content": text}], "max_tokens": 12}
        req = urllib.request.Request(f"http://127.0.0.1:{self.port}/v1/chat/completions",
                                     data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status, json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode() or "{}")

    def test_the_engine_answers_before_the_stop(self):
        code, body = self.chat("hello")
        self.assertEqual(code, 200, body)
        self.assertTrue(self.engine.alive())

    def test_a_request_after_the_stop_is_refused(self):
        self.chat("hello")
        code, body = self.post("/v1/stop")
        self.assertEqual(code, 200, body)
        self.assertFalse(self.engine.alive())
        code, body = self.chat("hello")
        self.assertEqual(code, 409, body)
        self.assertEqual(body["error"]["type"], "engine_stopped")

    def test_start_answers_again(self):
        self.chat("hello")
        self.post("/v1/stop")
        code, body = self.post("/v1/start")
        self.assertEqual(code, 200, body)
        self.assertTrue(self.engine.alive(), "the engine process is back")
        code, body = self.chat("hello")
        self.assertEqual(code, 200, body)
        self.assertTrue(turn_tokens(body))

    def test_stop_start_stop_start_keeps_working(self):
        """The pair is idempotent: repeating it does not run the engine down."""
        for i in range(3):
            self.post("/v1/stop")
            code, body = self.post("/v1/start")
            if code != 200:
                self.fail(f"cycle {i}: start returned {code} {body}")
            code, body = self.chat("hello")
            if code != 200:
                self.fail(f"cycle {i}: chat returned {code} {body}")
            if not turn_tokens(body):
                self.fail(f"cycle {i}: the engine answered with nothing")


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
