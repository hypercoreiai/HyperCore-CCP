"""#Monitor: the Recent requests columns must come from the worker's terminal frame.

The dashboard already had the cells for Reused, Output, Tok/s and VRAM hit rate. The
missing part was the wire: a fixture that sends NOT_MEASURED for every expert-tier field
renders "-", which is correct for an unreported field but useless for proving the path
is wired. This test drives a ScriptedWorker that reports the fields and asserts the
Monitor's history row receives them.
"""
from __future__ import annotations

import contextlib
import io
import sys
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from serve.frame_fixture import ScriptedWorker
from serve.frontend import ChatTemplate
from serve.hypercore_supervisor import HyperCoreProcessSupervisor
from serve.server import ByteTokenizer, HyperCoreRequestHandler, Service


class RecentRequestFields(unittest.TestCase):
    """Prove the Monitor's Recent requests cells are fed by the worker's terminal frame."""

    def test_the_recent_request_row_is_populated_from_the_terminal_frame(self):
        """A worker that reports the expert-tier fields must produce a populated history row."""
        tok = ByteTokenizer()
        worker = ScriptedWorker(
            max_slots=1,
            tokens=5,
            token_start=1,
            prefill_s=0.05,
            prompt_reused=12,
            cache_hits=97,
            cache_lookups=100,
            offloaded=3,
            prompt_read=8,
            ram_blobs=2,
            file_blobs=1,
            file_kb=1234,
            expert_slots=1200,
            expert_slots_full=3700,
            expert_cache_mib=1536,
            expert_cache_full_mib=3700,
            vram_free_mib=2048,
            expert_source=3,
            prompt_chunk=2048,
        )
        sup = HyperCoreProcessSupervisor(transport=worker.connect, max_restarts=0)
        sup.start()
        svc = Service(
            HyperCoreRequestHandler(sup),
            tok,
            ChatTemplate(ROOT / "serve/chat_template.jinja"),
            model_name="test-model",
        )
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                list(svc.run(tok.encode("hi"), False, None, 10, {}, threading.Event()))

            m = svc.metrics()
            row = m["requests"][0]

            self.assertEqual(row["reused"], 12)
            self.assertEqual(row["output_tokens"], 5)
            self.assertGreater(row["duration_s"], 0)
            self.assertGreater(row["decode_tok_s"], 0)
            self.assertEqual(row["hit_rate"], 0.97)
            self.assertEqual(row["pcie_share"], 0.029)
            self.assertEqual(row["prompt_read"], 8)
            self.assertEqual(row["ram_blobs"], 2)
            self.assertEqual(row["file_blobs"], 1)
            self.assertEqual(row["file_mb"], 1.234)

            engine = m["engine"]
            self.assertEqual(engine["expert_slots"], 1200)
            self.assertEqual(engine["expert_slots_full"], 3700)
            self.assertEqual(engine["expert_cache_mib"], 1536)
            self.assertEqual(engine["expert_cache_full_mib"], 3700)
            self.assertEqual(engine["vram_free_mib"], 2048)
            self.assertEqual(engine["expert_source"], 3)
            self.assertEqual(engine["prompt_chunk"], 2048)
        finally:
            sup.stop()

    def test_a_turn_that_ends_on_the_end_of_turn_token_still_reports_its_figures(self):
        """The common case: the answer closes with <|im_end|>.

        Service.run stops reading at that token, so the terminal frame is never reached by
        the caller. If the supervisor does not read it on the way out, Reused, Tok/s and
        the VRAM hit rate are empty for every real request - which is what the Monitor
        showed when this was broken.
        """
        tok = ByteTokenizer()
        worker = ScriptedWorker(
            max_slots=1,
            tokens=5,
            token_start=253,          # 253..257: four words and the end-of-turn token (257)
            prefill_s=0.05,
            prompt_reused=12,
            cache_hits=97,
            cache_lookups=100,
            offloaded=3,
            prompt_read=8,
        )
        sup = HyperCoreProcessSupervisor(transport=worker.connect, max_restarts=0)
        sup.start()
        svc = Service(HyperCoreRequestHandler(sup), tok, ChatTemplate(ROOT / "serve/chat_template.jinja"),
                     model_name="test-model")
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                list(svc.run(tok.encode("hi"), False, None, 10, {}, threading.Event()))
            row = svc.metrics()["requests"][0]
            self.assertEqual(row["finish"], "stop")
            self.assertEqual(row["reused"], 12)
            self.assertEqual(row["hit_rate"], 0.97)
            self.assertGreater(row["decode_tok_s"], 0)
            self.assertEqual(row["prompt_read"], 8)
        finally:
            sup.stop()

    def test_the_prefill_card_gets_a_rate_from_the_terminal_frame(self):
        """Prefill is the tokens read over the time the worker said it took to read them.

        The engine has no prompt-progress line on the wire, so the only honest figure is the
        one the terminal summary makes possible. A worker that reports neither half gets None,
        not 0 - a zero would read as a prompt that took no time to read.
        """
        tok = ByteTokenizer()
        worker = ScriptedWorker(max_slots=1, tokens=3, token_start=1, prefill_s=0.05,
                               prompt_read=8, cache_hits=5, cache_lookups=10)
        sup = HyperCoreProcessSupervisor(transport=worker.connect, max_restarts=0)
        sup.start()
        svc = Service(HyperCoreRequestHandler(sup), tok, ChatTemplate(ROOT / "serve/chat_template.jinja"),
                     model_name="test-model")
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                list(svc.run(tok.encode("hi"), False, None, 10, {}, threading.Event()))
            m = svc.metrics()
            rate = svc.engine.prefill_tok_s_mean
            row = m["requests"][0]
            self.assertIsNotNone(rate)
            self.assertGreater(rate, 0.0)
            # the same division the row's own prompt_ms and prompt_read give
            self.assertEqual(rate, row["prefill_tok_s_mean"])
            self.assertEqual(rate, round(row["prompt_read"] / (row["prompt_ms"] / 1000), 1))
            self.assertEqual(m["live"]["prefill_tok_s_mean"], rate)
            # the telemetry sampler is the same call the history series is built from
            self.assertEqual(svc._prefill_tok_s_mean(), rate)
        finally:
            sup.stop()

    def test_an_unreported_prefill_is_none_and_not_zero(self):
        """A worker whose summary has no prefill window must not put a measurement there."""
        from serve.ipc_parser import (
            SUMMARY_WIRE_SIZE,
            TERMINAL_PREFIX,
            decode_terminal,
            derive_monitor_field,
        )
        # the 40-byte prefix: timings present, expert-tier and prompt-read fields absent
        short = TERMINAL_PREFIX.pack(0, SUMMARY_WIRE_SIZE, 3, 0, 10, 0, 0, 0, 0)
        self.assertIsNone(derive_monitor_field("prefill_tok_s_mean", decode_terminal(short), {}))
        self.assertIsNone(derive_monitor_field("prefill_tok_s_mean", {"prompt_read": 8, "prefill_ms": 0}, {}))
        self.assertEqual(derive_monitor_field("prefill_tok_s_mean", {"prompt_read": 8, "prefill_ms": 100}, {}), 80.0)

    def test_a_stopped_turn_reports_what_it_managed_to_produce(self):
        """A turn the client stopped has a terminal frame too: its tokens and its time."""
        tok = ByteTokenizer()
        worker = ScriptedWorker(max_slots=1, tokens=200, token_start=1, prefill_s=0.0, prompt_reused=4,
                               cache_hits=10, cache_lookups=20)
        sup = HyperCoreProcessSupervisor(transport=worker.connect, max_restarts=0)
        sup.start()
        svc = Service(HyperCoreRequestHandler(sup), tok, ChatTemplate(ROOT / "serve/chat_template.jinja"),
                     model_name="test-model")
        try:
            cancel = threading.Event()
            with contextlib.redirect_stdout(io.StringIO()):
                for kind, _ in svc.run(tok.encode("hi"), False, None, 200, {}, cancel):
                    if kind == "event":
                        cancel.set()
                    if kind == "done":
                        break
            row = svc.metrics()["requests"][-1]
            self.assertEqual(row["finish"], "cancel")
            self.assertEqual(row["reused"], 4)
            self.assertEqual(row["hit_rate"], 0.5)
        finally:
            sup.stop()


if __name__ == "__main__":
    unittest.main()
