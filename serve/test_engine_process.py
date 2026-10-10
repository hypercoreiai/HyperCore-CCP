"""Tests for the real-engine path: the worker drives an engine process and the
numbers on the wire are that engine's, not the fixture's.

    python3 -m unittest serve.test_engine_process

The engine here is serve/fixtures/fake_engine.py, which speaks the same --serve
protocol as src/program/generate.cpp. That is the point: these tests prove the
adapter, the framing and the supervisor agree, without needing weights or a GPU.
When build/hypercore-worker is not present the suite skips, because there is
nothing to drive.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "build" / "hypercore-worker"
FAKE_ENGINE = ROOT / "serve" / "fixtures" / "fake_engine.py"


def worker_config(**over) -> str:
    cfg = {
        "batch": 4,
        "pool_workers": 2,
        "max_context": 8192,
        "engine_exe": str(FAKE_ENGINE),
        "engine_args": ["--max-context", "8192", "--prefill-ms", "137.0", "--decode-ms", "412.0"],
    }
    cfg.update(over)
    return json.dumps(cfg)


class EngineProcess(unittest.TestCase):
    """Drive the built worker with a fake engine and read the frames back."""

    def setUp(self):
        if not WORKER.exists():
            self.skipTest(f"no worker binary at {WORKER}; build it with "
                         "cmake -B build && cmake --build build --target hypercore-worker")
        self.sock = tempfile.mktemp(prefix="hc-engine-test-")
        self.proc = subprocess.Popen(
            [str(WORKER), self.sock, worker_config()],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        self.sys = sys.modules  # keep the import path tidy for the helper below
        sys.path.insert(0, str(ROOT))
        from serve.hypercore_supervisor import HyperCoreProcessSupervisor
        self.sup = HyperCoreProcessSupervisor(worker_binary=str(WORKER),
                                            socket_path=self.sock,
                                            config=worker_config())
        if not self.sup.restart():
            self.fail("the worker did not start")

    def tearDown(self):
        try:
            self.sup.shutdown()
        except Exception:
            pass
        self.proc.terminate()
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.kill()
        if os.path.exists(self.sock):
            os.unlink(self.sock)

    def test_the_engine_is_reached_and_reports_its_own_timings(self):
        list(self.sup.stream([11, 12, 13], max_new_tokens=5))
        s = self.sup.last_summary or {}
        # 137 and 412 are what the fake engine printed. The fixture's numbers are
        # prompt.size() and a 40 ms floor, so matching these proves the engine path ran.
        self.assertEqual(s.get("prefill_ms"), 137)
        self.assertEqual(s.get("decode_ms"), 412)
        self.assertEqual(s.get("drafts_accepted"), 3)
        self.assertEqual(s.get("drafts_offered"), 5)
        self.assertEqual(s.get("produced_tokens"), 5)
        self.assertEqual(s.get("stop_reason"), "limit")

    def test_the_tokens_are_the_engine_s(self):
        # The fake engine emits prompt[i % len(prompt)] + 1: 12, 13, 14, 12, 13.
        # The fixture emits 1000 + i, so a token below 1000 can only have come from the engine.
        got = [tok for tag, tok, _ in self.sup.stream([11, 12, 13], max_new_tokens=5)
               if tag == 4]
        self.assertEqual(got, [12, 13, 14, 12, 13])

    def test_a_bad_engine_is_a_failure_not_a_silent_stub(self):
        sock = tempfile.mktemp(prefix="hc-engine-bad-")
        bad = subprocess.Popen(
            [str(WORKER), sock, worker_config(engine_args=["--fail-start", "no weights on this box"])],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        ok = False
        for _ in range(20):
            if bad.poll() is not None:
                ok = bad.returncode != 0
                break
            import time
            time.sleep(0.2)
        bad.terminate()
        self.assertTrue(ok, "an engine that refuses to start must make the worker exit non-zero")
        if os.path.exists(sock):
            os.unlink(sock)

    def test_the_engine_is_told_to_stop(self):
        # The fake engine honours STOP between tokens; the summary must say cancel, not limit.
        # The request is made long on purpose: a 200-token stream with a pause per token is
        # still running when the cancel arrives, which is the only case worth testing.
        cfg = worker_config(engine_args=["--max-context", "8192", "--token-ms", "20"])
        sock = tempfile.mktemp(prefix="hc-engine-stop-")
        proc = subprocess.Popen([str(WORKER), sock, cfg], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        sys.path.insert(0, str(ROOT))
        from serve.hypercore_supervisor import HyperCoreProcessSupervisor
        sup = HyperCoreProcessSupervisor(worker_binary=str(WORKER), socket_path=sock, config=cfg)
        try:
            self.assertTrue(sup.restart(), "the worker did not start")
            stopper = threading.Timer(0.3, lambda: sup.cancel(1))
            stopper.start()
            got = [tok for tag, tok, _ in sup.stream([11, 12, 13], max_new_tokens=200, request_id=1)]
            stopper.join()
            s = sup.last_summary or {}
            self.assertEqual(s.get("stop_reason"), "cancel",
                            f"a cancelled stream reported {s.get('stop_reason')}; the STOP line never reached the engine")
            self.assertLess(s.get("produced_tokens", 999), 200)
        finally:
            sup.shutdown()
            proc.terminate()
            proc.wait(timeout=5)
            if os.path.exists(sock):
                os.unlink(sock)


class ConfigShape(unittest.TestCase):
    """serve/server.py must hand the worker the model, not just the numeric knobs."""

    def test_worker_config_carries_the_engine(self):
        sys.path.insert(0, str(ROOT))
        from serve.server import hypercore_worker_config
        cfg = {
            "exe": "engine/hypercore",
            "cwd": str(ROOT),
            "args": ["--pack", "pack/full", "--max-context", "4096"],
        }
        out = json.loads(hypercore_worker_config(cfg))
        self.assertEqual(out["engine_exe"], str(ROOT / "engine" / "hypercore"))
        self.assertEqual(out["engine_args"], ["--pack", "pack/full", "--max-context", "4096"])

    def test_no_exe_means_no_model(self):
        sys.path.insert(0, str(ROOT))
        from serve.server import hypercore_worker_config
        out = json.loads(hypercore_worker_config({"args": ["--batch", "4"]}))
        self.assertNotIn("engine_exe", out)
        self.assertEqual(out["batch"], 4)


if __name__ == "__main__":
    unittest.main()
