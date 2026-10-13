"""Model discovery, on-demand loading and safe unloading over the actual HTTP API."""
import json
import io
import os
import subprocess
import threading
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest import mock

from serve.frontend import ChatTemplate
from serve.server import ByteTokenizer, EngineDied, EngineStuck, MockEngine, Service, serve
from serve.fixtures.legacy_engine import HyperCoreEngine  # noqa: E402


class ResidentEngine(HyperCoreEngine):
    def __init__(self, tok):
        self.reply = MockEngine(tok, "Hello.", max_context=4096)
        self.max_context, self.info, self.last = 4096, {}, {}
        self.loaded, self.starts, self.closes = False, 0, 0
        self.unloaded = True
        self.progress = None

    def alive(self):
        return self.loaded

    def exit_code(self):
        return None

    def restart(self):
        self.loaded = True
        self.starts += 1
        self.unloaded = False

    def close(self):
        self.loaded = False
        self.closes += 1

    def unload(self):
        self.close()
        self.unloaded = True

    def generate(self, *args, **kwargs):
        yield from self.reply.generate(*args, **kwargs)


class Lifecycle(unittest.TestCase):
    def test_close_cleans_up_after_a_broken_stdin_pipe(self):
        for running in (False, True):
            with self.subTest(running=running):
                engine = HyperCoreEngine("missing-executable", [], lazy=True)
                read_fd, write_fd = os.pipe()
                stdin = os.fdopen(write_fd, "w")
                self.addCleanup(stdin.close)
                os.close(read_fd)                       # the engine's end of the pipe is already gone
                stdin.write("pending")                  # buffered: flush() and close() will hit the broken pipe
                proc = mock.Mock(stdin=stdin, stdout=io.StringIO())
                self.addCleanup(proc.stdout.close)
                proc.poll.side_effect = [None if running else 0, 0]
                engine.proc, engine.pump, engine.log = proc, mock.Mock(), io.StringIO()
                self.addCleanup(engine.log.close)
                engine.ended, engine.progress, engine.last = False, (1, 2), {"generated": 1}

                engine.close()

                self.assertTrue(stdin.closed)
                self.assertTrue(proc.stdout.closed)
                self.assertTrue(engine.log.closed)
                engine.pump.join.assert_called_once_with(timeout=2)
                self.assertIsNone(engine.proc)
                self.assertTrue(engine.ended)
                self.assertIsNone(engine.progress)
                self.assertEqual(engine.last, {})
                if running:
                    proc.terminate.assert_called_once()
                    proc.wait.assert_called_once_with(timeout=20)
                else:
                    proc.terminate.assert_not_called()
                    proc.wait.assert_not_called()
                proc.kill.assert_not_called()
                engine.close()                          # repeated cleanup is harmless

    def test_close_sends_eof_before_waiting_for_windows_reader(self):
        engine = HyperCoreEngine("missing-executable", [], lazy=True)
        proc = mock.Mock()
        proc.stdin, proc.stdout = io.StringIO(), io.StringIO()
        proc.poll.side_effect = [None, 0]
        proc.wait.side_effect = lambda **kwargs: self.assertTrue(proc.stdin.closed)
        engine.proc = proc
        engine.close()
        self.assertIsNone(engine.proc)
        proc.kill.assert_not_called()

    def test_close_does_not_forget_a_process_still_exiting(self):
        engine = HyperCoreEngine("missing-executable", [], lazy=True)
        proc = mock.Mock()
        proc.stdin, proc.stdout = io.StringIO(), io.StringIO()
        proc.poll.return_value = None
        proc.wait.side_effect = subprocess.TimeoutExpired("engine", 2)
        engine.proc = proc
        with self.assertRaisesRegex(EngineStuck, "still releasing"):
            engine.close()
        self.assertIs(engine.proc, proc)
        proc.terminate.assert_called_once()
        proc.kill.assert_called_once()

    def test_close_terminates_before_it_kills(self):
        # an engine that does not end on QUIT is terminated first (as the unload always did); kill is the last resort
        engine = HyperCoreEngine("missing-executable", [], lazy=True)
        proc = mock.Mock()
        proc.stdin, proc.stdout = io.StringIO(), io.StringIO()
        proc.poll.side_effect = [None, 0]
        proc.wait.side_effect = [subprocess.TimeoutExpired("engine", 20), 0]
        engine.proc = proc
        engine.close()
        proc.terminate.assert_called_once()
        proc.kill.assert_not_called()
        self.assertIsNone(engine.proc)

    def test_native_lazy_constructor_does_not_start_a_process(self):
        engine = HyperCoreEngine("missing-executable", ["--max-context", "16384"], lazy=True)
        self.assertFalse(engine.alive())
        self.assertEqual(engine.max_context, 16384)
        self.assertIsNone(engine.exit_code())
        engine.close()

    def setUp(self):
        tok = ByteTokenizer()
        self.engine = ResidentEngine(tok)
        self.svc = Service(self.engine, tok, ChatTemplate(Path(__file__).parent / "chat_template.jinja"))
        self.httpd = serve(self.svc, port=0)
        self.base = f"http://127.0.0.1:{self.httpd.server_address[1]}"

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()

    def request(self, path, body=None, headers=None):
        req = urllib.request.Request(self.base + path, data=json.dumps(body).encode() if body is not None else None,
                                     headers={"Content-Type": "application/json", **(headers or {})})
        try:
            response = urllib.request.urlopen(req, timeout=10)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            data = response.read().decode()
            return response.status, data if "event-stream" in response.headers.get("Content-Type", "") else json.loads(data)

    def raw(self, path, body=None):
        """The same, but with the response headers: a test of Retry-After needs them."""
        req = urllib.request.Request(self.base + path, data=json.dumps(body).encode() if body is not None else None,
                                    headers={"Content-Type": "application/json"})
        try:
            response = urllib.request.urlopen(req, timeout=10)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            response.read()
            return response.status, response.headers

    def test_unload_wait_reads_the_query(self):
        from serve.server import unload_wait
        self.assertIsNone(unload_wait(None, 300.0))          # no `wait`: unload now, 409 if a request is running
        self.assertEqual(unload_wait("", 300.0), 300.0)     # a bare `wait`: the default
        self.assertEqual(unload_wait("60", 300.0), 60.0)
        self.assertEqual(unload_wait("nonsense", 300.0), 300.0)

    def test_unload_wait_waits_for_a_running_request_to_finish(self):
        # #1997: a peer that wants the GPU back gets the running turn's time instead of a 409 on the first try
        self.request("/v1/load", {"model": self.svc.model})
        self.svc.fifo.acquire()
        waiter = threading.Thread(target=lambda: (time.sleep(0.3), self.svc.fifo.release()))
        waiter.start()
        code, body = self.request("/unload?wait=2", {"model": self.svc.model})
        waiter.join()
        self.assertEqual(code, 200, body)
        self.assertEqual(body["status"], "unloaded")
        self.assertTrue(self.engine.unloaded)

    def test_unload_without_wait_answers_busy_while_a_request_holds_the_slot(self):
        self.request("/v1/load", {"model": self.svc.model})
        self.svc.fifo.acquire()
        try:
            code, body = self.request("/unload", {"model": self.svc.model})
            self.assertEqual(code, 409, body)
            self.assertEqual(body["status"], "busy")
        finally:
            self.svc.fifo.release()

    def test_a_before_load_command_that_fails_is_not_ignored_when_the_card_is_full(self):
        # #1997: the hook's exit code alone does not refuse (a peer that is not running also makes curl fail);
        # the free VRAM decides, and the 503 says both
        self.svc.before_load = "false"
        self.svc.min_free_vram_mib = 1000
        self.svc.vram_free_wait_s = 0.0
        self.svc.free_vram_mib = lambda: 100
        code, body = self.request("/v1/load", {"model": self.svc.model})
        self.assertEqual(code, 503)
        self.assertIn("before_load command failed", body["error"]["message"])
        self.assertIn("min_free_vram_mib", body["error"]["message"])
        self.assertEqual(self.engine.starts, 0, "the engine was not started into 100 MiB")

    def test_a_before_load_command_that_fails_loads_when_the_card_is_free(self):
        self.svc.before_load = "false"
        self.svc.min_free_vram_mib = 1000
        self.svc.free_vram_mib = lambda: 8000
        code, body = self.request("/v1/load", {"model": self.svc.model})
        self.assertEqual(code, 200, body)
        self.assertEqual(self.engine.starts, 1)

    def test_before_load_ignore_failure_skips_the_vram_check(self):
        self.svc.before_load = "false"
        self.svc.min_free_vram_mib = 1000
        self.svc.before_load_ignore_failure = True
        self.svc.free_vram_mib = lambda: 100
        code, body = self.request("/v1/load", {"model": self.svc.model})
        self.assertEqual(code, 200, body)
        self.assertEqual(self.engine.starts, 1)

    def test_before_load_strict_refuses_without_reading_the_card(self):
        self.svc.before_load = "false"
        self.svc.before_load_strict = True
        self.svc.min_free_vram_mib = 0
        code, body = self.request("/v1/load", {"model": self.svc.model})
        self.assertEqual(code, 503)
        self.assertIn("the GPU was not given back", body["error"]["message"])
        self.assertEqual(self.engine.starts, 0)

    def test_a_busy_gpu_503_carries_retry_after(self):
        self.svc.min_free_vram_mib = 1000
        self.svc.free_vram_mib = lambda: 100
        self.svc.vram_free_wait_s = 0.0
        code, headers = self.raw("/v1/load", {"model": self.svc.model})
        self.assertEqual(code, 503)
        self.assertEqual(headers.get("Retry-After"), "15")

    def test_discover_chat_unload_and_stream_reload(self):
        self.assertEqual(self.request("/api/health")[1]["service"], "hypercore")
        self.assertFalse(self.request("/v1/status")[1]["loaded"])
        self.assertEqual(self.request("/v1/models")[1]["data"][0]["status"]["value"], "unloaded")
        self.assertTrue(self.request("/props")[1]["models_autoload"])
        self.assertEqual(self.engine.starts, 0)
        chat = {"messages": [{"role": "user", "content": "Hello"}], "max_tokens": 32, "reasoning_effort": "none"}
        for _ in range(2):
            code, answer = self.request("/v1/chat/completions", chat)
            self.assertEqual(code, 200)
            self.assertEqual(answer["choices"][0]["message"]["content"], "Hello.")
        self.assertEqual(self.engine.starts, 1)
        self.assertFalse(self.request("/v1/unload", {})[1]["loaded"])
        code, stream = self.request("/v1/chat/completions", {**chat, "stream": True})
        self.assertEqual(code, 200)
        self.assertIn("data: [DONE]", stream)
        self.assertEqual(self.engine.starts, 2)

    def test_busy_auth_and_foreign_origin_cannot_unload(self):
        self.engine.loaded = True
        with self.svc.fifo:
            self.assertEqual(self.request("/v1/unload", {})[0], 409)
        self.svc.api_key = "local-secret"
        self.assertEqual(self.request("/v1/unload", {})[0], 401)
        self.assertEqual(self.request("/v1/unload", {}, {"Authorization": "Bearer local-secret",
                                                        "Origin": "https://other.example"})[0], 403)
        self.assertEqual(self.engine.closes, 0)
        self.assertTrue(self.engine.loaded)
        self.assertEqual(self.request("/v1/unload", {}, {"Authorization": "Bearer local-secret"})[0], 200)

    def test_an_engine_that_died_on_load_is_reported_as_such(self):
        # EngineDied is a RuntimeError: it keeps its own answer ("the next request restarts it")
        def died():
            raise EngineDied("the engine ended while it started")
        self.engine.restart = died
        code, body = self.request("/v1/chat/completions", {"messages": [{"role": "user", "content": "Hello"}]})
        self.assertEqual(code, 503)
        self.assertIn("the next request restarts it", body["error"]["message"])

    def test_explicit_load_and_model_matching(self):
        self.assertEqual(self.request("/v1/load", {"model": "other-model"})[0], 404)
        self.assertEqual(self.engine.starts, 0)
        before = time.time()
        code, status = self.request("/v1/load", {"model": self.svc.model})
        self.assertEqual(code, 200)
        self.assertTrue(status["loaded"])
        self.assertEqual(self.engine.starts, 1)
        self.assertGreaterEqual(self.svc.last_request_at, before)
        self.svc.status["queued"] = 1
        self.assertEqual(self.request("/v1/load", {})[0], 409)
        self.assertEqual(self.request("/v1/unload", {})[0], 409)
        self.assertEqual(self.engine.closes, 0)
        self.assertEqual(self.request("/v1/load", {}, {"Content-Type": "text/plain"})[0], 415)


if __name__ == "__main__":
    unittest.main()
