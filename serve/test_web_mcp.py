"""serve/test_web_mcp.py - the Firefox MCP server's address check, packets, and mcp.yaml loading.

    python -m unittest serve.test_web_mcp -v
"""
from __future__ import annotations

import json
import socket
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from serve.mcp import DEFAULTS, hub_from_config, load_mcp_yaml
from serve.mcp.web_mcp import (
    Firefox,
    call,
    encode_packet,
    handle,
    public_http_url,
    read_packet,
    text,
    unwrap_ddg,
    firefox_bin,
)


class Addresses(unittest.TestCase):
    def test_public_https_passes(self):
        self.assertTrue(public_http_url("https://html.duckduckgo.com/html/?q=hypercore").startswith("https://"))

    def test_private_and_local_are_refused(self):
        for url in ("http://127.0.0.1/", "http://10.1.2.3/a", "http://192.168.1.1/", "file:///etc/passwd",
                    "http://localhost/x", "javascript:alert(1)", "http://user:pw@example.com/"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                public_http_url(url)

    def test_duckduckgo_redirect_unwraps(self):
        self.assertEqual(unwrap_ddg("https://duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com%2Fa"),
                         "https://example.com/a")


class Packets(unittest.TestCase):
    def test_round_trip(self):
        left, right = socket.socketpair()
        try:
            left.sendall(encode_packet({"applicationType": "gecko", "marionetteProtocol": 3}))
            self.assertEqual(read_packet(right, 2)["applicationType"], "gecko")
        finally:
            left.close()
            right.close()


class Yaml(unittest.TestCase):
    def test_shipped_file_registers_the_web_server(self):
        # The tuning numbers in mcp.yaml change; what matters is that they are read and applied.
        _, shipped = load_mcp_yaml(str(ROOT / "mcp.yaml"))
        hub = hub_from_config({}, yaml_path=str(ROOT / "mcp.yaml"))
        self.assertIsNotNone(hub)
        self.assertIn("web", hub.servers)
        self.assertTrue(hub.servers["web"].cfg["args"][0].endswith("web_mcp.py"))
        self.assertEqual(hub.settings, {**DEFAULTS, **shipped})
        self.assertGreater(hub.settings["timeout_s"], 0)
        self.assertGreaterEqual(hub.settings["max_result_chars"], 1)
        self.assertGreaterEqual(hub.settings["max_rounds"], 1)
        self.assertTrue(0.0 <= hub.settings["condense_at"] <= 1.0)

    def test_yaml_replaces_a_same_name_in_the_run_config(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "mcp.yaml"
            path.write_text("timeout_s: 12\nservers:\n  web:\n    command: python3\n    args:\n      - other.py\n",
                            encoding="utf-8")
            hub = hub_from_config({"mcp_servers": {"web": {"command": "old"}}}, yaml_path=str(path))
            self.assertEqual(hub.servers["web"].cfg["command"], "python3")
            self.assertEqual(hub.settings["timeout_s"], 12.0)

class ToolDispatch(unittest.TestCase):
    """The tool layer without a browser: every path that can be reached without Firefox."""

    def test_unknown_tool_is_a_tool_error_not_a_crash(self):
        r = call("frobnicate", {})
        self.assertTrue(r["isError"])
        self.assertIn("unknown tool", r["content"][0]["text"])

    def test_a_bad_url_is_reported_rather_than_raised(self):
        r = call("browse", {"url": "file:///etc/passwd"})
        self.assertTrue(r["isError"])
        self.assertIn("http", r["content"][0]["text"].lower())

    def test_an_empty_query_is_refused(self):
        r = call("search", {"query": "   "})
        self.assertTrue(r["isError"])
        self.assertIn("query", r["content"][0]["text"])

    def test_ping_and_an_unknown_method_follow_jsonrpc(self):
        self.assertEqual(handle({"jsonrpc": "2.0", "id": 1, "method": "ping"})["result"], {})
        err = handle({"jsonrpc": "2.0", "id": 2, "method": "does/not/exist"})
        self.assertEqual(err["error"]["code"], -32601)
        self.assertIsNone(handle({"jsonrpc": "2.0", "method": "ping"}))   # a notification gets no reply

    def test_text_builds_a_content_block(self):
        self.assertEqual(text("hi"), {"content": [{"type": "text", "text": "hi"}], "isError": False})
        self.assertTrue(text("hi", error=True)["isError"])


class BrowserLifecycle(unittest.TestCase):
    """The Firefox side, run against the headless Firefox this install has.

    Skipped where there is no Firefox, so the suite still runs on a machine without one.
    """

    def setUp(self):
        if not firefox_bin():
            self.skipTest("no Firefox installed on this machine")
        self.browser = Firefox()

    def tearDown(self):
        self.browser.close()

    def test_status_before_start_says_not_started(self):
        self.assertEqual(self.browser.status()["firefox"], "not started")
        self.assertFalse(self.browser.running())

    def test_open_runs_a_script_and_reports_the_url(self):
        self.browser._open("about:blank")
        self.assertTrue(self.browser.running())
        self.assertEqual(self.browser._script("return 1 + 1;"), 2)
        self.assertEqual(self.browser.status()["firefox"], "running")

    def test_a_private_page_is_refused_and_recorded_as_the_last_error(self):
        with self.assertRaises(ValueError):
            self.browser._open("http://127.0.0.1/x")
        self.assertTrue(self.browser.last_error)

    def test_close_stops_the_process_and_removes_the_profile(self):
        self.browser._open("about:blank")
        profile = self.browser.profile
        self.browser.close()
        self.assertFalse(self.browser.running())
        self.assertIsNone(self.browser.sock)
        self.assertEqual(self.browser.status()["firefox"], "not started")
        self.assertFalse(Path(profile).exists())

    def test_a_second_open_reuses_the_same_browser(self):
        self.browser._open("about:blank")
        first = self.browser.proc.pid
        self.browser._open("about:blank")
        self.assertEqual(self.browser.proc.pid, first)


class Stdio(unittest.TestCase):
    def test_lists_status_search_and_browse(self):
        proc = subprocess.Popen([sys.executable, str(ROOT / "serve" / "mcp" / "web_mcp.py")], stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, text=True)
        try:
            def ask(msg):
                proc.stdin.write(json.dumps(msg) + "\n")
                proc.stdin.flush()
                return json.loads(proc.stdout.readline())
            hello = ask({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
            self.assertEqual(hello["result"]["serverInfo"]["title"], "Firefox and DuckDuckGo")
            listed = ask({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
            self.assertEqual([t["name"] for t in listed["result"]["tools"]], ["status", "search", "browse"])
            status = ask({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                          "params": {"name": "status", "arguments": {}}})
            body = json.loads(status["result"]["content"][0]["text"])
            self.assertEqual(body["firefox"], "not started")
        finally:
            proc.stdin.close()
            proc.stdout.close()
            proc.wait(timeout=5)


if __name__ == "__main__":
    unittest.main()
