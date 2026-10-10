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
    encode_packet,
    public_http_url,
    read_packet,
    unwrap_ddg,
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
