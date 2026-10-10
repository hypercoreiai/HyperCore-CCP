"""Tests for tools/hypercore_agent.py against a stub SSE server.

    python -m unittest tools.test_hypercore_agent

The stub serves /health, /status, /metrics and a scripted stream, so each recovery
path can be exercised without a model: a request that hits max_tokens, one that dies,
one that goes silent, one the user stopped.
"""
import json
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from tools.hypercore_agent import HyperCoreClient


class Stub(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.path == "/health":
            body = {"status": "ok", "loaded": True, "max_context": 1024}
        elif self.path == "/status":
            body = {"busy": False, "queued": 0}
        elif self.path == "/metrics":
            recorded = self.server.recorded.pop(0) if self.server.recorded else "stop"
            body = {"live": {"state": "idle"}, "requests": [{"finish": recorded}]}
        else:
            body = {"error": "not found"}
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())

    def do_POST(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        steps = self.server.script.pop(0) if self.server.script else ["stop"]
        for step in steps:
            if step == "keepalive":
                try:
                    self.wfile.write(b": keep-alive\n\n")
                    self.wfile.flush()
                except BrokenPipeError:
                    return          # the wrapper closed a stalled stream on purpose
                time.sleep(self.server.gap_s)
                continue
            chunk = {"choices": [{"delta": {"content": "part"}, "finish_reason": step}]}
            self.wfile.write(b"data: " + json.dumps(chunk).encode() + b"\n\n")
            self.wfile.flush()
        self.wfile.write(b"data: [DONE]\n\n")


class Agent(unittest.TestCase):
    def stub(self, script, recorded, gap_s=0.0):
        server = ThreadingHTTPServer(("127.0.0.1", 0), Stub)
        server.script = list(script)
        server.recorded = list(recorded)
        server.gap_s = gap_s
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(lambda: (server.shutdown(), server.server_close()))
        return HyperCoreClient(f"http://127.0.0.1:{server.server_port}", "")

    def test_a_clean_answer_is_completed(self):
        result = self.stub([["stop"]], ["stop"]).run("do it")
        self.assertTrue(result["completed"])
        self.assertEqual(result["finish"], "stop")
        self.assertEqual(result["attempts"], 1)

    def test_length_is_continued_until_it_stops(self):
        client = self.stub([["length"], ["length"], ["stop"]], ["length", "length", "stop"])
        result = client.run("do it", max_tokens=10, max_continuations=3)
        self.assertTrue(result["completed"])
        self.assertEqual(result["continuations"], 2)
        self.assertEqual(result["text"], "partpartpart")
        self.assertEqual(result["attempts"], 3)

    def test_continuations_are_bounded(self):
        client = self.stub([["length"]] * 10, ["length"] * 10)
        result = client.run("do it", max_tokens=10, max_continuations=2)
        self.assertFalse(result["completed"])
        self.assertEqual(result["continuations"], 2)
        self.assertEqual(result["finish"], "length")

    def test_tool_calls_is_continued_not_accepted_as_done(self):
        """serve/server.py reports an answer with pending tool calls as finish_reason
        "tool_calls"; that is a mid-turn state, so the wrapper must keep going."""
        client = self.stub([["tool_calls"], ["stop"]], ["tool_calls", "stop"])
        result = client.run("do it", max_continuations=2)
        self.assertTrue(result["completed"])
        self.assertEqual(result["finish"], "stop")
        self.assertEqual(result["continuations"], 1)

    def test_an_engine_death_is_retried(self):
        client = self.stub([["error"], ["stop"]], ["error", "stop"])
        result = client.run("do it", max_attempts=3)
        self.assertTrue(result["completed"])
        self.assertEqual(result["attempts"], 2)
        self.assertTrue(any("retrying" in line for line in result["log"]))

    def test_a_stop_the_user_pressed_is_not_a_completion(self):
        # the dialect says "stop"; the server's own record says the request was cancelled
        client = self.stub([["stop"]], ["cancel"])
        result = client.run("do it", max_attempts=1)
        self.assertFalse(result["completed"])
        self.assertEqual(result["finish"], "cancel")
        self.assertTrue(any("the server recorded" in line for line in result["log"]))

    def test_silence_is_a_stall_not_a_hang(self):
        client = self.stub([["keepalive"] * 6 + ["stop"]], ["disconnect"], gap_s=0.15)
        result = client.run("do it", stall_s=0.3, heartbeat_s=0.1, max_attempts=1)
        self.assertFalse(result["completed"])
        self.assertEqual(result["finish"], "stall")

    def test_tool_activity_counts_as_progress(self):
        """A slow tool call must not be read as a stall."""
        class ToolStub(Stub):
            def do_POST(self):
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.end_headers()
                for _ in range(6):
                    activity = {"hypercore_mcp": {"event": "call", "name": "terminal__run",
                                             "arguments": {}, "round": 1}}
                    self.wfile.write(b"data: " + json.dumps(activity).encode() + b"\n\n")
                    self.wfile.flush()
                    time.sleep(0.15)
                self.wfile.write(b"data: " + json.dumps(
                    {"choices": [{"delta": {}, "finish_reason": "stop"}]}).encode() + b"\n\n")
                self.wfile.write(b"data: [DONE]\n\n")
        server = ThreadingHTTPServer(("127.0.0.1", 0), ToolStub)
        server.script, server.recorded, server.gap_s = [], ["stop"], 0.15
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(lambda: (server.shutdown(), server.server_close()))
        result = HyperCoreClient(f"http://127.0.0.1:{server.server_port}", "").run(
            "do it", stall_s=0.2, heartbeat_s=0.1)
        self.assertTrue(result["completed"], result["log"])

    def test_a_long_prefill_is_not_a_stall(self):
        """Reading a large prompt emits no tokens for minutes. The wrapper must read
        live.prompt_read advancing as progress rather than cutting the request off."""
        class PrefillStub(Stub):
            def do_GET(self):
                if self.path == "/metrics":
                    n = self.server.tick[0]
                    self.server.tick[0] += 1
                    body = {"live": {"state": "reading", "prompt_read": min(n * 4000, 200000),
                                    "prompt_total": 200000, "generated": None},
                            "requests": [{"finish": "stop"}]}
                elif self.path == "/status":
                    body = {"busy": True, "queued": 0}
                elif self.path == "/health":
                    body = {"status": "ok", "loaded": True}
                else:
                    body = {"error": "not found"}
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(body).encode())

            def do_POST(self):
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.end_headers()
                for _ in range(8):
                    self.wfile.write(b": keep-alive\n\n")
                    self.wfile.flush()
                    time.sleep(0.1)
                self.wfile.write(b"data: " + json.dumps(
                    {"choices": [{"delta": {"content": "done"}, "finish_reason": "stop"}]}).encode() + b"\n\n")
                self.wfile.write(b"data: [DONE]\n\n")

        server = ThreadingHTTPServer(("127.0.0.1", 0), PrefillStub)
        server.tick, server.script, server.recorded, server.gap_s = [0], [], ["stop"], 0.0
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(lambda: (server.shutdown(), server.server_close()))
        result = HyperCoreClient(f"http://127.0.0.1:{server.server_port}", "").run(
            "do it", stall_s=0.3, heartbeat_s=0.1)
        self.assertTrue(result["completed"], result["log"])
        self.assertEqual(result["text"], "done")

    def test_unreachable_server_is_reported_not_crashed(self):
        self.assertFalse(HyperCoreClient("http://127.0.0.1:1", "").heartbeat()["up"])


if __name__ == "__main__":
    unittest.main()
