"""Path jail and document tools. Uses a temporary root, never the real /home."""
import asyncio
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from serve import docs_mcp


class Docs(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.docs_mcp = docs_mcp
        docs_mcp.guard = docs_mcp.WorkspaceGuard(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def test_rejects_paths_outside_the_workspace(self):
        with self.assertRaises(PermissionError):
            docs_mcp.guard.validate_path("../etc/passwd")
        with self.assertRaises(PermissionError):
            docs_mcp.guard.validate_path("/etc/passwd")
        sibling = Path(str(self.root) + "-not")
        with self.assertRaises(PermissionError):
            docs_mcp.guard.validate_path(str(sibling / "note.md"))
        outside = self.root / "escape.md"
        outside.symlink_to("/etc/passwd")
        with self.assertRaises(PermissionError):
            docs_mcp.guard.validate_path("escape.md")

    def test_create_read_write_and_list(self):
        async def run():
            created = await docs_mcp.create_file("notes/draft.md", "hello")
            self.assertIn("Successfully created", created)
            again = await docs_mcp.create_file("notes/draft.md", "nope")
            self.assertIn("already exists", again)
            self.assertEqual(await docs_mcp.read_file("notes/draft.md"), "hello")
            missing = await docs_mcp.write_file("missing.md", "x")
            self.assertIn("not found", missing)
            saved = await docs_mcp.write_file("notes/draft.md", "changed")
            self.assertIn("Successfully saved", saved)
            self.assertEqual(await docs_mcp.read_file("notes/draft.md"), "changed")
            listing = json.loads(await docs_mcp.list_directory("notes"))
            self.assertEqual(listing["entries"][0]["name"], "draft.md")
            self.assertEqual((self.root / "notes" / "draft.md").read_text(encoding="utf-8"), "changed")

        asyncio.run(run())


    def test_read_file_outlines_a_large_source_without_line_numbers(self):
        async def run():
            body = "# header\n\n" + "x" * 15000 + "\n" + "\n".join(
                f"def f{i}(a):\n    return a + {i}\n" for i in range(120))
            (self.root / "big.py").write_text(body, encoding="utf-8")
            read = await docs_mcp.read_file("big.py")
            self.assertTrue(read.startswith("# File outline for big.py"))
            self.assertIn("Do NOT retry this call", read)
            self.assertIn("120 symbols in", read)
            self.assertIn("more are not shown", read)
        asyncio.run(run())

    def test_a_line_range_is_numbered_and_gives_a_continuation(self):
        async def run():
            lines = [f"line {i}" for i in range(1, 201)]
            (self.root / "many.txt").write_text("\n".join(lines), encoding="utf-8")
            read = await docs_mcp.read_file("many.txt", start_line=5, end_line=8)
            self.assertEqual(read.split("\n\n[")[0],
                             "     5\tline 5\n     6\tline 6\n     7\tline 7\n     8\tline 8")
            self.assertIn("continue with start_line=9", read)
            # the model's habitual mistakes: a 0 start, and end below start
            self.assertTrue((await docs_mcp.read_file("many.txt", start_line=0, end_line=1))
                            .startswith("     1\tline 1"))
            self.assertIn("past the end", await docs_mcp.read_file("many.txt", start_line=201))
        asyncio.run(run())

    def test_edit_file_applies_and_reports(self):
        async def run():
            await docs_mcp.create_file("src/app.py", "def a():\n    return 1\n\ndef b():\n    return 2\n")
            out = await docs_mcp.edit_file("src/app.py", [{"old_text": "return 1", "new_text": "return 2"}])
            self.assertIn("1 edit(s) applied", out)
            self.assertEqual((self.root / "src" / "app.py").read_text(encoding="utf-8"),
                            "def a():\n    return 2\n\ndef b():\n    return 2\n")
            self.assertIn("not found", await docs_mcp.edit_file("src/app.py",
                                                                [{"old_text": "return 9", "new_text": "x"}]))
            self.assertIn("matches 2 places", await docs_mcp.edit_file("src/app.py",
                                                                      [{"old_text": "return", "new_text": "ret"}]))
            out = await docs_mcp.edit_file("src/app.py", [{"old_text": "return", "new_text": "ret", "line": 5}])
            self.assertIn("applied", out)
            self.assertEqual((self.root / "src" / "app.py").read_text(encoding="utf-8"),
                            "def a():\n    return 2\n\ndef b():\n    ret 2\n")
        asyncio.run(run())

    def test_edits_are_all_or_nothing(self):
        async def run():
            await docs_mcp.create_file("src/atomic.py", "one\ntwo\n")
            out = await docs_mcp.edit_file("src/atomic.py", [
                {"old_text": "one", "new_text": "ONE"},
                {"old_text": "nope", "new_text": "NOPE"},
            ])
            self.assertIn("not found", out)
            self.assertEqual((self.root / "src" / "atomic.py").read_text(encoding="utf-8"), "one\ntwo\n")
        asyncio.run(run())

    def test_stringified_and_prefixed_edits_are_accepted(self):
        async def run():
            await docs_mcp.create_file("src/coerce.py", "alpha\nbeta\n")
            out = await docs_mcp.edit_file("src/coerce.py", '[{"old_text": "alpha", "new_text": "ALPHA"}]')
            self.assertIn("applied", out)
            out = await docs_mcp.edit_file("src/coerce.py", [{"old_text": "     2\tbeta", "new_text": "BETA"}])
            self.assertIn("line-number prefix was removed", out)
            self.assertEqual((self.root / "src" / "coerce.py").read_text(encoding="utf-8"), "ALPHA\nBETA\n")
        asyncio.run(run())

    def test_refuses_keys_and_non_text(self):
        async def run():
            secret = await docs_mcp.create_file(".ssh/authorized_keys", "ssh-ed25519 AAAA")
            self.assertIn("Security Error", secret)
            binary = await docs_mcp.create_file("picture.png", "not an image")
            self.assertIn("Error:", binary)
            self.assertFalse((self.root / "picture.png").exists())
            self.assertFalse((self.root / ".ssh").exists())

        asyncio.run(run())

    def test_files_with_no_extension_are_judged_by_content(self):
        """.gitignore has no extension and is a document; the engine binary beside it is not."""
        async def run():
            created = await docs_mcp.create_file(".gitignore", "build/\n*.pyc\n")
            self.assertIn("Successfully created", created)
            self.assertEqual((self.root / ".gitignore").read_text(encoding="utf-8"), "build/\n*.pyc\n")
            self.assertIn("build/", await docs_mcp.read_file(".gitignore"))
            edited = await docs_mcp.edit_file(".gitignore", [{"old_text": "build/", "new_text": "dist/"}])
            self.assertIn("edit(s) applied", edited)
            self.assertEqual((self.root / ".gitignore").read_text(encoding="utf-8"), "dist/\n*.pyc\n")
            written = await docs_mcp.create_file("Makefile", "all:\n\techo hi\n")
            self.assertIn("Successfully created", written)
            self.assertIn("echo hi", await docs_mcp.read_file("Makefile"))
            # A real binary with no extension is still refused, read and write alike.
            (self.root / "engine_binary").write_bytes(b"\x7fELF" + b"\x00" * 40 + bytes(range(256)))
            self.assertIn("only text documents", await docs_mcp.read_file("engine_binary"))
            self.assertIn("only text documents",
                         await docs_mcp.write_file("engine_binary", "overwrite the binary"))
            self.assertEqual((self.root / "engine_binary").read_bytes()[:4], b"\x7fELF")

        asyncio.run(run())

    def test_delete_reports_the_bytes_removed(self):
        async def run():
            await docs_mcp.create_file("scratch/tmp.md", "abcdefghij")
            gone = await docs_mcp.delete_file("scratch/tmp.md")
            self.assertIn("Deleted", gone)
            self.assertIn("10 bytes", gone)
            self.assertFalse((self.root / "scratch" / "tmp.md").exists())
            self.assertIn("not found", await docs_mcp.delete_file("scratch/tmp.md"))
        asyncio.run(run())

    def test_a_long_file_says_how_much_was_left_out(self):
        async def run():
            body = "x" * (docs_mcp.MAX_CHARS + 500)
            (self.root / "long.md").write_text(body, encoding="utf-8")   # written outside the tool
            read = await docs_mcp.read_file("long.md")
            self.assertIn("showing", read)
            self.assertIn(str(len(body)), read)
            self.assertIn("Do NOT repeat this call", read)
            self.assertEqual(len(read.split("\n\n[showing")[0]), docs_mcp.doc_text.MAX_RANGE_CHARS)
        asyncio.run(run())


class Stdio(unittest.TestCase):
    def test_server_lists_the_six_tools(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = os.environ.copy()
            env["HYPERCORE_DOCS_ROOT"] = tmp
            # the repo root is wherever this profile happens to live: derive it from the
            # package we already imported, and use the interpreter running the test
            python = os.environ.get("HYPERCORE_TEST_PYTHON") or sys.executable
            script = str(Path(docs_mcp.__file__).resolve().parent / "mcp" / "docs_mcp.py")
            proc = subprocess.Popen(
                [python, script], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                env=env, text=True)
            try:
                def rpc(msg, expect):
                    assert proc.stdin is not None and proc.stdout is not None
                    proc.stdin.write(json.dumps(msg) + "\n")
                    proc.stdin.flush()
                    for _ in range(8):
                        line = proc.stdout.readline()
                        if not line:
                            break
                        try:
                            got = json.loads(line)
                        except ValueError:
                            continue
                        if got.get("id") == expect:
                            return got
                    raise AssertionError("no reply")

                init = rpc({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                            "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                                       "clientInfo": {"name": "test", "version": "0"}}}, 1)
                self.assertIn("serverInfo", init["result"])
                proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
                proc.stdin.flush()
                listed = rpc({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}, 2)
                names = {tool["name"] for tool in listed["result"]["tools"]}
                self.assertEqual(names, {"create_file", "read_file", "edit_file", "write_file",
                                        "list_directory", "delete_file"})
                made = rpc({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                            "params": {"name": "create_file", "arguments": {"path": "note.txt", "content": "gas"}}}, 3)
                text = made["result"]["content"][0]["text"]
                self.assertIn("Successfully created", text)
                self.assertEqual((Path(tmp) / "note.txt").read_text(encoding="utf-8"), "gas")
            finally:
                if proc.stdin:
                    proc.stdin.close()
                proc.kill()
                proc.wait(timeout=5)
                if proc.stdout:
                    proc.stdout.close()
                if proc.stderr:
                    proc.stderr.close()


class CommandPath(unittest.TestCase):
    def test_absolute_venv_command_is_not_followed(self):
        from serve.mcp import hub_from_config
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            real = root / "real-python"
            real.write_text("#!/bin/sh\n", encoding="utf-8")
            real.chmod(0o755)
            link = root / "venv-python"
            link.symlink_to(real)
            path = root / "mcp.yaml"
            path.write_text("servers:\n  docs:\n    command: " + str(link) + "\n", encoding="utf-8")
            hub = hub_from_config({}, yaml_path=str(path))
            self.assertEqual(hub.servers["docs"].cfg["command"], str(link))


if __name__ == "__main__":
    unittest.main()
