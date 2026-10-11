"""serve/test_vision_start.py - what the server says when the image encoder does not start.

    python -m unittest serve.test_vision_start

The encoder prints "READY <n_embd>" and then answers `ENC <image> <out>` lines.  When it cannot get its
VRAM, llama.cpp's crash reporter forks gdb and writes the stack trace on stdout - the pipe the server reads -
so the first line is "[New LWP 12345]" and the reason (a GGML assert, a cudaMalloc that did not fit) is on
stderr, in the model's log, where nobody was looking at it.  These tests drive Vision with a stand-in
encoder: no GPU, no weights.
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from serve.server import Vision, vision_env, vision_start_reason

OOM = "ggml_backend_cuda_buffer_type_alloc_buffer: allocating 865.48 MiB on device 0: cudaMalloc failed: out of memory"
BAD_MMPROJ = "hypercore-vision: the mmproj is not a clip model"

STAND_IN = """import sys

GPU_FAIL = {gpu_fail!r}
CPU_FAIL = {cpu_fail!r}


def say(msg):
    print(msg, file=sys.stderr)


if "--gpu" in sys.argv and GPU_FAIL:
    say(GPU_FAIL)
    sys.exit(134)
if CPU_FAIL:
    say(CPU_FAIL)
    sys.exit(134)
print("READY 1024")
"""


class VisionStart(unittest.TestCase):
    def start(self, gpu_fail: str = "", cpu_fail: str = "", gpu: bool = False, noise: str = ""):
        """Vision() over a stand-in encoder: it fails with gpu_fail when asked for the GPU, with cpu_fail otherwise.

        Returns (the Vision, log) when it starts, (the RuntimeError, log) when it does not.
        """
        if os.name == "nt":
            self.skipTest("the stand-in encoder is a shell script")
        d = Path(tempfile.mkdtemp())
        script = d / "fake-vision.py"
        script.write_text("#!/usr/bin/env python3" + chr(10) + (f"print({noise!r})" + chr(10) if noise else "") +
                         STAND_IN.format(gpu_fail=gpu_fail, cpu_fail=cpu_fail), encoding="utf-8")
        script.chmod(0o755)
        log = d / "vision.log"
        log.write_text("", encoding="utf-8")
        handle = open(log, "a", encoding="utf-8")  # noqa: SIM115 - it is the encoder's stderr for its whole life
        self.addCleanup(handle.close)
        cfg = {"exe": str(script), "mmproj": "mmproj.gguf", "model": "model.gguf"}
        if gpu:
            cfg["gpu"] = True
        try:
            return Vision(cfg, log=handle), log
        except RuntimeError as e:
            return e, log

    def test_a_ready_encoder_is_ready(self):
        """A loader warning on stdout before READY is not a failed start."""
        got, _ = self.start(noise="[New LWP 12345]")
        self.assertIsInstance(got, Vision)
        self.assertTrue(got.alive())
        got.close()

    def test_a_crash_names_the_reason_and_the_fix(self):
        got, _ = self.start(gpu_fail=OOM, gpu=True, cpu_fail=OOM)   # the CPU retry is disabled below
        # (with a CPU failure too the fallback cannot help: the message still says what and what to do)
        self.assertIsInstance(got, RuntimeError)
        text = str(got)
        self.assertIn("out of memory", text)
        self.assertIn("--vision cpu", text)
        self.assertNotIn("[New LWP", text)

    def test_a_failure_without_an_allocation_says_only_its_own_line(self):
        got, _ = self.start(cpu_fail=BAD_MMPROJ)
        self.assertIsInstance(got, RuntimeError)
        self.assertIn("the mmproj is not a clip model", str(got))
        self.assertNotIn("--vision cpu", str(got))

    def test_the_encoder_says_what_it_cannot_open(self):
        got, _ = self.start(noise="ERR cannot load the vision encoder missing.gguf")
        self.assertIsInstance(got, RuntimeError)
        self.assertIn("cannot load the vision encoder missing.gguf", str(got))

    def test_no_room_on_the_card_falls_back_to_the_cpu(self):
        """The card is full: the encoder starts on the CPU instead of taking the server down with it."""
        got, log = self.start(gpu_fail=OOM, gpu=True)
        self.assertIsInstance(got, Vision)
        self.assertTrue(got.alive())
        self.assertTrue(got.cpu_only)
        self.assertNotIn("--gpu", got.spawn[0])
        self.assertIn("out of memory", log.read_text())     # what it said is still in the model's log
        got.close()

    def test_a_cpu_only_config_that_fails_is_not_retried(self):
        got, _ = self.start(cpu_fail=OOM)
        self.assertIsInstance(got, RuntimeError)
        self.assertIn("out of memory", str(got))

    def test_the_engine_lines_are_not_read_as_the_encoder_s(self):
        """The model's log is shared with the engine: only this start's encoder lines can be the reason."""
        log = Path(tempfile.mkdtemp()) / "vision.log"
        log.write_text("hypercore serve: mtp: the draft head does not fit" + chr(10) +
                       "hypercore_worker: engine init failed (-5)" + chr(10), encoding="utf-8")
        with open(log, "a", encoding="utf-8") as f:
            f.write(OOM + chr(10) + "hypercore serve: prompt chunk auto: 8192 tokens" + chr(10))
        self.assertIn("cudaMalloc", vision_start_reason(str(log), 0))
        self.assertEqual(vision_start_reason(str(log), os.path.getsize(str(log))), "")

    def test_no_log_says_nothing(self):
        self.assertEqual(vision_start_reason(None, 0), "")

    def test_the_encoder_gets_no_gdb_backtrace(self):
        """The crash reporter's gdb output is what made the failure unreadable; it is switched off."""
        env = vision_env({}, {"PATH": "/bin"})
        self.assertEqual(env["GGML_NO_BACKTRACE"], "1")
        self.assertEqual(env["PATH"], "/bin")
        on_card = vision_env({"vision": {"cuda_device": 1}}, {})
        self.assertEqual(on_card["CUDA_VISIBLE_DEVICES"], "1")
        self.assertEqual(on_card["GGML_NO_BACKTRACE"], "1")

    def test_the_reserve_the_encoder_is_given_covers_its_own_weights(self):
        """setup keeps at least the encoder's tensors plus its context free on the card (docs: ~1.4 GB)."""
        import setup
        mmproj_bytes = 907_524_736                       # the BF16 mmproj this model ships with
        self.assertGreaterEqual(setup.VISION["gpu"]["reserve_mib"] * 1048576, mmproj_bytes)


if __name__ == "__main__":
    unittest.main()
