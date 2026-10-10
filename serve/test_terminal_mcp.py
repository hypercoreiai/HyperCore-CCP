"""The shell jail, the pipeline reporter, and the object-oriented reader.

Run with:  python -m unittest serve.test_terminal_mcp -v
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from serve import terminal_mcp


class Jail(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        terminal_mcp.ROOT = self.root
        terminal_mcp.STATE_DIR = self.root / ".terminal"
        terminal_mcp.ALLOW_ALL = False
        terminal_mcp.MAX_OUT = 20000
        terminal_mcp.MAX_PIPE_BYTES = 2_000_000
        terminal_mcp._jobs.clear()
        terminal_mcp._sessions.clear()

    def tearDown(self):
        terminal_mcp.close_all()
        self.tmp.cleanup()

    def test_paths_outside_the_root_are_refused(self):
        with self.assertRaises(ValueError):
            terminal_mcp.inside("../etc/passwd")
        with self.assertRaises(ValueError):
            terminal_mcp.inside("/etc/passwd")
        escape = self.root / "escape"
        escape.symlink_to("/etc")
        with self.assertRaises(ValueError):
            terminal_mcp.inside("escape")

    def test_the_device_files_are_exempt_from_the_root(self):
        # > /dev/null is a shell idiom; the guard lets the four device entries through
        for device in ("/dev/null", "/dev/stdout", "/dev/stderr", "/dev/stdin"):
            self.assertEqual(str(terminal_mcp.inside(device)), device)
        self.assertEqual(terminal_mcp.run("seq 1 3 > /dev/null", stdin="")["exit_code"], 0)
        self.assertEqual(terminal_mcp.run("wc -l < /dev/null", stdin="")["stdout"], "0\n")
        # ... and nothing else outside the root gets in
        for path in ("/dev/random", "/dev/x", "/dev/null/x", "/etc/hosts"):
            with self.assertRaises(ValueError):
                terminal_mcp.inside(path)
        with self.assertRaises(ValueError):
            terminal_mcp.run("echo hi > /dev/x")

    def test_run_refuses_binaries_not_on_the_allowlist(self):
        with self.assertRaises(ValueError) as got:
            terminal_mcp.run("lmnope --version")
        self.assertIn("allowlist", str(got.exception))
        with self.assertRaises(ValueError):
            terminal_mcp.run("echo one | lmnope")

    def test_a_program_under_the_root_is_allowed_by_absolute_path(self):
        fake = self.root / "myinterp"
        fake.write_text("#!/bin/sh\n", encoding="utf-8")
        fake.chmod(0o755)
        self.assertEqual(terminal_mcp.run(str(fake))["exit_code"], 0)

    def test_an_absolute_program_outside_the_root_is_refused(self):
        with self.assertRaises(ValueError):
            terminal_mcp.run("/usr/bin/echo hi")

    def test_builtins_take_arguments_not_programs(self):
        # cd names a directory, not a command; the target is still jailed
        self.assertEqual(terminal_mcp.run("cd " + str(self.root) + " && echo ok")["stdout"].strip(), "ok")
        with self.assertRaises(ValueError):
            terminal_mcp.run("cd /etc")

    def test_shell_keywords_and_assignments_are_not_programs(self):
        result = terminal_mcp.run("total=3; for n in 1 2; do total=$((total + n)); done; echo $total")
        self.assertEqual(result["exit_code"], 0)
        self.assertEqual(result["stdout"].strip(), "6")
        with self.assertRaises(ValueError):
            terminal_mcp.run("for n in 1 2; do lmnope; done")
        with self.assertRaises(ValueError):
            terminal_mcp.run("if true; then lmnope; fi")

    def test_a_quoted_run_is_not_read_as_several_commands(self):
        out = terminal_mcp.run("printf 'a\nb\nc'")
        self.assertEqual(out["stdout"], "a\nb\nc")

    def test_a_redirect_may_not_write_outside_the_root(self):
        terminal_mcp.run("echo hi > kept.txt")
        self.assertTrue((self.root / "kept.txt").exists())
        with self.assertRaises(ValueError):
            terminal_mcp.run("echo hi > /etc/terminal_test")
        with self.assertRaises(ValueError):
            terminal_mcp.run("echo hi 2> /etc/terminal_stderr")

    def test_command_substitution_is_checked_too(self):
        with self.assertRaises(ValueError):
            terminal_mcp.run("echo $(lmnope)")
        self.assertEqual(terminal_mcp.run("echo $(date)")["stdout"].strip() != "", True)

    def test_unbalanced_quotes_fail_before_a_shell_sees_them(self):
        with self.assertRaises(ValueError):
            terminal_mcp.run("echo 'unclosed")

    def test_run_reports_exit_code(self):
        out = terminal_mcp.run("echo hello")
        self.assertEqual(out["exit_code"], 0)
        self.assertEqual(out["stdout"].strip(), "hello")
        self.assertEqual(terminal_mcp.run("false")["exit_code"], 1)

    def test_truncation_is_counted_not_silently_dropped(self):
        terminal_mcp.MAX_OUT = 10
        big = terminal_mcp.run("printf 'abcdefghijABCDEFGHIJ'")
        self.assertEqual(len(big["stdout"]), 10)
        self.assertEqual(big["truncated"]["stdout_chars"], 10)

    def test_run_can_save_the_whole_output(self):
        result = terminal_mcp.run("echo saved", save_to="out.txt")
        self.assertEqual((self.root / "out.txt").read_text(encoding="utf-8").strip(), "saved")
        self.assertIn("saved_to", result)

    def test_stdin_is_fed_to_the_command(self):
        result = terminal_mcp.run("cat", stdin="from stdin")
        self.assertEqual(result["stdout"], "from stdin")

    def test_timeout_kills_the_command(self):
        result = terminal_mcp.run("printf early; sleep 5", timeout_s=1)
        self.assertTrue(result["timed_out"])
        self.assertIn("early", result["stdout"])

    def test_allow_all_accepts_the_forms_the_jail_refuses(self):
        terminal_mcp.ALLOW_ALL = True
        for command in ("./build.sh", "/usr/bin/git status", "cd /tmp && ls", "echo hi > /tmp/out"):
            terminal_mcp.check_command(command)
        terminal_mcp.ALLOW_ALL = False
        with self.assertRaises(ValueError):
            terminal_mcp.check_command("./build.sh")

    def test_a_full_stdout_keeps_stderr_inside_the_result_cap(self):
        body = terminal_mcp.fit_json(
            {"command": "printf", "cwd": "/home", "exit_code": 0, "elapsed_ms": 1,
             "timed_out": False, "stdout": "x" * 6000, "stderr": "ERROR: linker failed at the end"},
            6000)
        self.assertLessEqual(len(body), 6000)
        parsed = json.loads(body)
        self.assertIn("ERROR: linker failed at the end", parsed["stderr"])
        self.assertLess(len(parsed["stdout"]), 6000)

    def test_pipe_reports_every_stage(self):
        result = terminal_mcp.pipe(["printf 'a\nb\nc'", "grep b", "wc -l"])
        self.assertEqual(result["exit_code"], 0)
        self.assertEqual(len(result["stages"]), 3)
        self.assertEqual(result["output"].strip(), "1")
        broken = terminal_mcp.pipe(["printf 'x'", "grep nope", "wc -l"])
        self.assertEqual(broken["exit_code"], 1)
        self.assertEqual(broken["failed_stage"], "grep nope")
        self.assertEqual(len(broken["stages"]), 2)  # the stage after the failure never ran

    def test_a_cut_between_stages_is_stated(self):
        terminal_mcp.MAX_PIPE_BYTES = 5
        result = terminal_mcp.pipe(["printf 'abcdefghij'", "cat"])
        self.assertEqual(result["output"], "abcde")
        self.assertIn("note", result["stages"][0])


class Processes(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        terminal_mcp.ROOT = self.root
        terminal_mcp.STATE_DIR = self.root / ".terminal"
        terminal_mcp._jobs.clear()

    def tearDown(self):
        terminal_mcp.close_all()
        self.tmp.cleanup()

    def test_start_status_log_and_kill(self):
        started = terminal_mcp.process("start", "demo", "echo one; echo two")
        self.assertTrue(started["pid"] > 0)
        ended = terminal_mcp.process("wait", "demo", timeout_s=5)
        self.assertEqual(ended["exit_code"], 0)
        log = terminal_mcp.process("log", "demo", lines=5)
        self.assertIn("one", log["lines"])
        self.assertIn("two", log["lines"])
        listed = terminal_mcp.process("list")
        self.assertEqual(len(listed["jobs"]), 1)
        terminal_mcp.process("kill", "demo")
        self.assertFalse(terminal_mcp.process("status", "demo")["running"])

    def test_killing_a_finished_job_is_not_an_error(self):
        terminal_mcp.process("start", "done", "true")
        terminal_mcp.process("wait", "done", timeout_s=5)
        again = terminal_mcp.process("kill", "done")
        self.assertTrue(again["already_stopped"])

    def test_unknown_job_is_named_not_crashed(self):
        with self.assertRaises(ValueError):
            terminal_mcp.process("status", "no-such-job")

    def test_signal_reports_the_state_after_the_process_exited(self):
        terminal_mcp.process("start", "sleeper", "sleep 30")
        self.assertTrue(terminal_mcp.process("status", "sleeper")["running"])
        stopped = terminal_mcp.process("signal", "sleeper", sig="TERM")
        self.assertFalse(stopped["running"])
        self.assertEqual(stopped["exit_code"], -15)
        self.assertFalse(terminal_mcp.process("status", "sleeper")["running"])

    def test_a_job_can_be_replaced_by_the_same_name(self):
        terminal_mcp.process("start", "twice", "echo first")
        terminal_mcp.process("wait", "twice", timeout_s=5)
        terminal_mcp.process("start", "twice", "echo second")
        terminal_mcp.process("wait", "twice", timeout_s=5)
        self.assertEqual(len(terminal_mcp.process("list")["jobs"]), 1)
        self.assertIn("second", terminal_mcp.process("log", "twice")["lines"])

    def test_wait_reports_a_job_that_is_still_running(self):
        terminal_mcp.process("start", "slow", "sleep 5")
        result = terminal_mcp.process("wait", "slow", timeout_s=0.5)
        self.assertTrue(result["running"])
        terminal_mcp.process("kill", "slow")


class Sessions(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        terminal_mcp.ROOT = self.root
        terminal_mcp.STATE_DIR = self.root / ".terminal"
        terminal_mcp.close_all()          # close any session a previous test left open
        terminal_mcp._sessions.clear()

    def tearDown(self):
        terminal_mcp.close_all()
        self.tmp.cleanup()

    def test_python_session_keeps_state_between_calls(self):
        terminal_mcp.repl("python", "class Greeter:\n    def __init__(self, name):\n        self.name = name\n"
                         "    def greet(self):\n        return f'hi {self.name}'", action="start")
        out = terminal_mcp.repl("python", "print(Greeter('world').greet())")
        self.assertEqual(out["output"].strip(), "hi world")

    def test_python_session_reports_errors_without_dying(self):
        terminal_mcp.repl("python", "x = 1", action="start")
        bad = terminal_mcp.repl("python", "print(not_defined)")
        self.assertIn("NameError", bad["output"])
        still = terminal_mcp.repl("python", "print(x)")
        self.assertEqual(still["output"].strip(), "1")

    def test_a_compound_statement_is_not_read_as_a_syntax_error(self):
        terminal_mcp.repl("python", "total = 0", action="start")
        out = terminal_mcp.repl("python", "for n in range(4):\n    total += n")
        self.assertNotIn("SyntaxError", out["output"])
        self.assertEqual(terminal_mcp.repl("python", "print(total)")["output"].strip(), "6")

    def test_a_bare_expression_echoes_its_value(self):
        terminal_mcp.repl("python", "answer = 42", action="start")
        out = terminal_mcp.repl("python", "answer")
        self.assertEqual(out["output"].strip(), "42")

    def test_bash_session_keeps_state(self):
        terminal_mcp.repl("bash", "count=3", action="start")
        out = terminal_mcp.repl("bash", "echo $((count * 2))")
        self.assertEqual(out["output"].strip(), "6")

    def test_close_then_status(self):
        terminal_mcp.repl("python", "pass", action="start")
        self.assertTrue(terminal_mcp.repl("python", action="status")["running"])
        terminal_mcp.repl("python", action="close")
        self.assertFalse(terminal_mcp.repl("python", action="status")["running"])

    def test_a_loop_does_not_hang_the_call_and_the_session_is_replaced(self):
        terminal_mcp.repl("python", "value = 7", action="start")
        with self.assertRaises(ValueError):
            terminal_mcp.repl("python", "while True: pass", timeout_s=2)
        self.assertFalse(terminal_mcp.repl("python", action="status")["running"])
        fresh = terminal_mcp.repl("python", "print('restarted')")
        self.assertEqual(fresh["output"].strip(), "restarted")


class CodeTools(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        terminal_mcp.ROOT = self.root
        terminal_mcp.STATE_DIR = self.root / ".terminal"

    def tearDown(self):
        terminal_mcp.close_all()
        self.tmp.cleanup()

    def test_symbols_reads_classes_and_bases(self):
        source = (
            "import json\n"
            "from typing import Any\n"
            "class Base:\n"
            "    def run(self) -> None: ...\n"
            "class Worker(Base):\n"
            "    def __init__(self, cfg: dict) -> None: self.cfg = cfg\n"
            "    def _private(self) -> None: ...\n"
            "    def handle(self, item: Any) -> None: ...\n"
            "def helper() -> None: ...\n"
        )
        (self.root / "worker.py").write_text(source, encoding="utf-8")
        got = terminal_mcp.symbols("worker.py")
        self.assertEqual(got["classes"], 2)
        classes = {s["name"]: s for s in got["detail"][0]["symbols"] if s["kind"] == "class"}
        self.assertEqual(classes["Worker"]["bases"], ["Base"])
        self.assertTrue(any(m["name"] == "_private" and not m["public"] for m in classes["Worker"]["members"]))
        self.assertIn("handle", {m["name"] for m in classes["Worker"]["members"]})
        self.assertIn("json", got["detail"][0]["imports"])
        self.assertEqual([s["name"] for s in got["detail"][0]["symbols"] if s["kind"] == "function"], ["helper"])

    def test_symbols_walks_a_package_and_counts_files(self):
        (self.root / "pkg").mkdir()
        (self.root / "pkg" / "a.py").write_text("class A: pass\n", encoding="utf-8")
        (self.root / "pkg" / "b.py").write_text("class B(A): pass\n", encoding="utf-8")
        got = terminal_mcp.symbols("pkg")
        self.assertEqual(got["files"], 2)
        self.assertEqual(got["classes"], 2)

    def test_a_bad_file_is_reported_not_raised(self):
        (self.root / "broken.py").write_text("def a(:\n", encoding="utf-8")
        got = terminal_mcp.symbols("broken.py")
        self.assertIn("error", got["detail"][0])

    def test_check_reports_each_tool_under_its_own_name(self):
        (self.root / "mod.py").write_text("def a():\n    return 1\n", encoding="utf-8")
        result = terminal_mcp.check("mod.py", tests=False)
        self.assertEqual(set(result["report"]), {"ruff", "mypy", "pylint"})
        for entry in result["report"].values():
            if entry["available"]:
                self.assertIn("exit_code", entry)
            else:
                self.assertIn("install with", entry["note"])
        self.assertIsInstance(result["missing_tools"], list)

    def test_status_lists_interpreters_and_tools(self):
        got = terminal_mcp.status()
        self.assertEqual(got["root"], str(self.root))
        self.assertIn("git", got["tier2"])
        self.assertTrue(any(p.endswith("python3") for p in got["interpreters"]))


class Stdio(unittest.TestCase):
    def test_the_server_lists_eight_tools_over_stdio(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = os.environ.copy()
            env["TERMINAL_ROOT"] = tmp
            env["TERMINAL_STATE_DIR"] = Path(tmp) / ".terminal"
            env["TERMINAL_ALLOW_ALL"] = "0"   # the case below asserts an unknown binary is refused
            entry = Path(__file__).resolve().parents[1] / "serve" / "terminal_mcp.py"
            proc = subprocess.Popen([sys.executable, str(entry)],
                                    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    env=env, text=True)
            try:
                def rpc(msg, expect):
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
                self.assertEqual(init["result"]["serverInfo"]["name"], "terminal")
                proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
                proc.stdin.flush()
                listed = rpc({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}, 2)
                names = {tool["name"] for tool in listed["result"]["tools"]}
                self.assertEqual(names, {"run", "pipe", "process", "repl", "symbols", "check", "install",
                                        "status", "build", "compile", "tidy", "debug", "query", "compare"})

                ran = rpc({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                           "params": {"name": "run", "arguments": {"command": "echo hi"}}}, 3)
                self.assertFalse(ran["result"].get("isError"))
                self.assertIn("hi", ran["result"]["content"][0]["text"])

                bad = rpc({"jsonrpc": "2.0", "id": 4, "method": "tools/call",
                           "params": {"name": "run", "arguments": {"command": "definitelynotatool"}}}, 4)
                self.assertTrue(bad["result"]["isError"])

                streamed = rpc({"jsonrpc": "2.0", "id": 5, "method": "tools/call",
                                "params": {"name": "repl", "arguments": {"session": "python",
                                        "code": "print(1 + 1)"}}}, 5)
                body = json.loads(streamed["result"]["content"][0]["text"])
                self.assertEqual(body["session"], "python")
                self.assertEqual(body["output"].strip(), "2")
            finally:
                for stream in (proc.stdin, proc.stdout, proc.stderr):
                    if stream is not None:
                        try:
                            stream.close()
                        except OSError:
                            pass
                proc.kill()
                proc.wait(timeout=5)


class Native(unittest.TestCase):
    """Tier 3: compiling, static analysis, and looking at a binary."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        terminal_mcp.ROOT = self.root
        terminal_mcp.STATE_DIR = self.root / ".terminal"
        terminal_mcp.ALLOW_ALL = False
        terminal_mcp.MAX_OUT = 20000

    def tearDown(self):
        terminal_mcp.close_all()
        self.tmp.cleanup()

    def test_gplusplus_is_a_program_not_an_argument(self):
        # the name pattern must read "g++" as the command, not skip to the source file
        terminal_mcp.check_command("g++ -O2 a.cpp -o a")
        with self.assertRaises(ValueError):
            terminal_mcp.check_command("g++ -O2 lmnope.cpp | notatool")

    def test_a_source_that_compiles_says_so(self):
        source = self.root / "ok.cpp"
        source.write_text("int main(){return 0;}\n", encoding="utf-8")
        result = terminal_mcp.compile_source(str(source), syntax_only=True)
        self.assertTrue(result["compiled"], result.get("output"))
        self.assertEqual(result["exit_code"], 0)

    def test_a_source_with_an_error_reports_the_exit_code(self):
        source = self.root / "bad.cpp"
        source.write_text("int main(){ return undefined_thing; }\n", encoding="utf-8")
        result = terminal_mcp.compile_source(str(source), syntax_only=True)
        self.assertFalse(result["compiled"])
        self.assertNotEqual(result["exit_code"], 0)
        self.assertIn("undefined_thing", result["output"])

    def test_flags_from_a_compilation_database_are_replayed(self):
        # the recorded paths name a root that no longer exists; the real file is elsewhere
        real = self.root / "src"
        real.mkdir()
        source = real / "t.c"
        source.write_text("int f(void){return 0;}\n", encoding="utf-8")
        recorded = "/oldcheckout/src/t.c"
        commands = self.root / "compile_commands.json"
        commands.write_text(json.dumps([{
            "directory": "/oldcheckout",
            "command": "/usr/bin/cc -DSECRET=1 -I/oldcheckout/include -O2 -c " + recorded + " -o t.o",
            "file": recorded,
        }]), encoding="utf-8")
        result = terminal_mcp.compile_source(str(source), compile_commands=str(commands))
        self.assertTrue(result["compiled"], result.get("output"))
        self.assertIn("-DSECRET=1", result["argv"])
        self.assertIn(str(real), " ".join(result["argv"]))

    def test_missing_entry_is_named_not_guessed(self):
        commands = self.root / "compile_commands.json"
        commands.write_text("[]", encoding="utf-8")
        source = self.root / "x.c"
        source.write_text("int main(){return 0;}", encoding="utf-8")
        with self.assertRaises(ValueError) as got:
            terminal_mcp.compile_source(str(source), compile_commands=str(commands))
        self.assertIn("no entry", str(got.exception))

    def test_symbols_of_a_compiled_binary(self):
        source = self.root / "sym.cpp"
        source.write_text("int visible_marker(){return 1;}\nint main(){return visible_marker();}\n", encoding="utf-8")
        built = terminal_mcp.run("g++ -O0 " + str(source) + " -o " + str(self.root / "sym"), "")
        self.assertEqual(built["exit_code"], 0, built["stderr"])
        listed = terminal_mcp.debug("symbols", path=str(self.root / "sym"))
        self.assertIn("visible_marker", json.dumps(listed))

    def test_trace_reports_the_exit_code_of_the_traced_command(self):
        traced = terminal_mcp.debug("trace", command="exit 3", tracer="time")
        self.assertEqual(traced["tracer"], "time")
        self.assertEqual(traced["stats"]["exit status"], "3")

    def test_valgrind_find_the_leak(self):
        if not terminal_mcp.shutil.which("valgrind"):
            self.skipTest("valgrind is not installed")
        source = self.root / "leak.cpp"
        source.write_text("int main(){ int* p = new int[8]; (void)p; return 0; }\n", encoding="utf-8")
        built = terminal_mcp.run("g++ -O0 " + str(source) + " -o " + str(self.root / "leak"), "")
        self.assertEqual(built["exit_code"], 0, built["stderr"])
        result = terminal_mcp.debug("leak", path=str(self.root / "leak"))
        self.assertIn("definitely lost", result["leaks"])


class Data(unittest.TestCase):
    """Tier 4: structured queries, diffs, and the guardrails that apply to all of them."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        terminal_mcp.ROOT = self.root
        terminal_mcp.STATE_DIR = self.root / ".terminal"
        terminal_mcp.ALLOW_ALL = False
        terminal_mcp.MAX_OUT = 2000

    def tearDown(self):
        terminal_mcp.close_all()
        self.tmp.cleanup()

    def test_json_without_a_filter_gives_the_shape_not_the_bytes(self):
        cfg = self.root / "config.json"
        cfg.write_text(json.dumps({"servers": {"web": {"command": "python3"}}, "timeout_s": 90}), encoding="utf-8")
        result = terminal_mcp.query(str(cfg))
        self.assertEqual(result["shape"]["keys"]["timeout_s"]["value"], 90)
        self.assertIn("servers", result["shape"]["keys"])

    def test_json_with_a_filter_runs_jq(self):
        cfg = self.root / "config.json"
        cfg.write_text(json.dumps({"servers": {"web": {"command": "python3"}}}), encoding="utf-8")
        if not terminal_mcp.shutil.which("jq"):
            self.skipTest("jq is not installed")
        result = terminal_mcp.query(str(cfg), expression=".servers.web.command")
        self.assertEqual(result["result"].strip(), "python3")
        self.assertEqual(result["exit_code"], 0)

    def test_bad_json_is_reported_as_a_failure(self):
        cfg = self.root / "broken.json"
        cfg.write_text("{not json", encoding="utf-8")
        with self.assertRaises(ValueError):
            terminal_mcp.query(str(cfg))

    def test_yaml_lists_the_top_level_keys(self):
        cfg = self.root / "mcp.yaml"
        cfg.write_text("timeout_s: 90\nservers:\n  web:\n    command: python3\n", encoding="utf-8")
        if not terminal_mcp.shutil.which("yq"):
            self.skipTest("yq is not installed")
        result = terminal_mcp.query(str(cfg))
        self.assertEqual(result["exit_code"], 0)
        self.assertIn("servers", result["result"])

    def test_toml_reads_a_key_path(self):
        cfg = self.root / "settings.toml"
        cfg.write_text("[playstation]\nip = " + '"10.0.0.1"\n' + "timeout = 5\n", encoding="utf-8")
        result = terminal_mcp.query(str(cfg), action="toml", expression="playstation.ip")
        self.assertEqual(result["result"]["value"], "10.0.0.1")
        with self.assertRaises(ValueError):
            terminal_mcp.query(str(cfg), action="toml", expression="playstation.missing")

    def test_sqlite_schema_then_a_read_only_query(self):
        if not terminal_mcp.shutil.which("sqlite3"):
            self.skipTest("sqlite3 is not installed")
        db = self.root / "index.db"
        terminal_mcp.run("sqlite3 " + str(db) + " 'CREATE TABLE docs(path TEXT, body TEXT); "
                         "INSERT INTO docs VALUES(\"a\", \"hello world\")'", "")
        schema = terminal_mcp.query(str(db), action="sqlite")
        self.assertEqual(schema["columns"]["docs"], ["path", "body"])
        rows = terminal_mcp.query(str(db), action="sqlite", expression="SELECT path FROM docs")
        self.assertIn("a", rows["rows"])
        with self.assertRaises(ValueError):
            terminal_mcp.query(str(db), action="sqlite", expression="DELETE FROM docs")

    def test_compare_counts_the_lines_that_changed(self):
        left = self.root / "a.txt"
        right = self.root / "b.txt"
        left.write_text("one\ntwo\nthree\n", encoding="utf-8")
        right.write_text("one\ntwo changed\nthree\nfour\n", encoding="utf-8")
        result = terminal_mcp.compare(str(left), other=str(right))
        self.assertFalse(result["identical"])
        self.assertEqual(result["added_lines"], 2)
        self.assertEqual(result["removed_lines"], 1)
        self.assertIn("+two changed", result["diff"])

    def test_identical_files_are_called_identical(self):
        left = self.root / "a.txt"
        right = self.root / "b.txt"
        left.write_text("same\n", encoding="utf-8")
        right.write_text("same\n", encoding="utf-8")
        result = terminal_mcp.compare(str(left), other=str(right))
        self.assertTrue(result["identical"])

    def test_a_large_output_states_what_it_left_out(self):
        big = self.root / "big.txt"
        big.write_text("x" * 5000, encoding="utf-8")
        result = terminal_mcp.run("cat " + str(big), "")
        self.assertIn("truncated", result)
        self.assertEqual(result["truncated"]["stdout_chars"], 3000)


class Timeouts(unittest.TestCase):
    """A tool that hangs is not the same as a tool that failed."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        terminal_mcp.ROOT = self.root
        terminal_mcp.STATE_DIR = self.root / ".terminal"
        terminal_mcp.RUN_TIMEOUT = 30.0
        terminal_mcp.MAX_TIMEOUT = 300.0

    def tearDown(self):
        terminal_mcp.close_all()
        self.tmp.cleanup()

    def test_run_reports_a_timeout_rather_than_an_empty_success(self):
        result = terminal_mcp.run("sleep 20", "", {}, 1.0)
        self.assertTrue(result["timed_out"])
        self.assertNotEqual(result["exit_code"], 0)

    def test_build_names_the_missing_project_before_running_anything(self):
        with self.assertRaises(ValueError) as got:
            terminal_mcp.build(str(self.root), build_dir="build")
        self.assertIn("CMakeLists.txt", str(got.exception))

if __name__ == "__main__":
    unittest.main()
