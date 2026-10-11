"""serve/test_slots.py - batch slot saturation and drain, over binary frames.

The engine's SAVE/RESTORE round trip used to be exercised by feeding text lines into a
mock engine. The text protocol is gone, so the same behaviours are now tested against the
real framing: a ScriptedWorker on the far end of a socketpair, and HyperCoreIPCListener
routing the decoded frames to per-request queues.

What is still covered, unchanged in intent:
  - a saturated slot answers BUSY rather than an empty stream,
  - the slot drains when the holding stream terminates,
  - the capability snapshot reports what the instance resolved, not what was asked for.

    python -m unittest serve.test_slots -v
"""
from __future__ import annotations

import unittest

from serve.frame_fixture import ScriptedWorker
from serve.hypercore_supervisor import HyperCoreProcessSupervisor
from serve.ipc_parser import (
    MONITOR_FIELDS,
    STREAM_TOKEN,
    TERMINAL_PREFIX,
    TERMINAL_V1,
    decode_terminal,
    derive_monitor_field,
)


def supervisor(worker: ScriptedWorker) -> HyperCoreProcessSupervisor:
    sup = HyperCoreProcessSupervisor(transport=worker.connect, max_restarts=0)
    sup.start()
    return sup


class SlotSaturationTest(unittest.TestCase):
    def test_a_saturated_slot_answers_busy_not_empty(self):
        worker = ScriptedWorker(max_slots=1, tokens=4, prefill_s=0.05)
        sup = supervisor(worker)
        try:
            _rid, status = sup.submit([1, 2, 3, 4], max_new_tokens=4)
            self.assertEqual(status, 0, "the first request must be scheduled")
            _rid, second = sup.submit([9, 8, 7], max_new_tokens=4)
            self.assertEqual(second, -2, "a second request against a full slot must be BUSY")
        finally:
            sup.stop()

    def test_the_slot_drains_when_the_holding_stream_ends(self):
        worker = ScriptedWorker(max_slots=1, tokens=3)
        sup = supervisor(worker)
        try:
            tokens = list(sup.stream([1, 2, 3, 4], max_new_tokens=3))
            self.assertEqual(len([t for t in tokens if t[0] == STREAM_TOKEN]), 3)

            # The slot is free again: the same worker accepts a second request.
            _rid, status = sup.submit([5, 6, 7], max_new_tokens=3)
            self.assertEqual(status, 0, "the slot must be reusable after the stream terminated")
        finally:
            sup.stop()

    def test_concurrent_requests_up_to_the_slot_count_all_run(self):
        # prefill_s keeps every request in its slot for 50 ms. Without it a request lasts
        # about two token sleeps (~2 ms), and on a loaded runner the submit round trips
        # take longer than that, so the three requests never overlap and the fourth is
        # accepted. The assertion is about saturation; the fixture has to make saturation
        # possible rather than leave it to luck.
        worker = ScriptedWorker(max_slots=3, tokens=2, prefill_s=0.05)
        sup = supervisor(worker)
        try:
            statuses = [sup.submit([1, 2], max_new_tokens=2)[1] for _ in range(3)]
            self.assertEqual(statuses, [0, 0, 0], "three slots means three concurrent requests")
            _rid, fourth = sup.submit([3, 4], max_new_tokens=2)
            self.assertEqual(fourth, -2, "the fourth request against three slots is BUSY")
        finally:
            sup.stop()

    def test_caps_reports_the_resolved_baseline_not_the_request(self):
        worker = ScriptedWorker(
            max_slots=2,
            tokens=1,
            pool_workers=6,
            instance_pcie_frac=0.25,
            instance_spec_min_p=0.5,
        )
        sup = supervisor(worker)
        try:
            caps = sup.caps
            self.assertEqual(caps["max_batch_slots"], 2)
            self.assertEqual(caps["active_pool_workers"], 6)
            self.assertAlmostEqual(caps["instance_pcie_frac"], 0.25)
            self.assertAlmostEqual(caps["instance_spec_min_p"], 0.5)
            # The supervisor mirrors them so a request handler does not have to re-query.
            self.assertEqual(sup.max_batch_slots, 2)
            self.assertAlmostEqual(sup.instance_pcie_frac, 0.25)

            # A per-request override does not move the instance baseline.
            sup.submit([1, 2], max_new_tokens=1, pcie_frac=0.9, spec_min_p=0.9)
            self.assertAlmostEqual(sup.instance_pcie_frac, 0.25,
                                  msg="a request override must not rewrite the Level-1 baseline")
        finally:
            sup.stop()

    def test_an_unset_baseline_reports_unset(self):
        worker = ScriptedWorker(max_slots=1, tokens=1)
        sup = supervisor(worker)
        try:
            self.assertEqual(sup.instance_pcie_frac, -1.0)
            self.assertEqual(sup.instance_spec_min_p, -1.0)
        finally:
            sup.stop()


class TelemetryContractTest(unittest.TestCase):
    """The Monitor table is the only place these keys are defined, and an unmeasured
    field is None rather than 0.
    """

    def test_monitor_snapshot_is_exactly_the_declared_table(self):
        worker = ScriptedWorker(max_slots=1, tokens=3)
        sup = supervisor(worker)
        try:
            list(sup.stream([1, 2], max_new_tokens=3))
            snapshot = sup.monitor_snapshot()
            declared = set(MONITOR_FIELDS)
            emitted = set(snapshot) - {"in_flight", "max_batch_slots"}
            self.assertEqual(emitted, declared,
                             "monitor_snapshot keys must equal MONITOR_FIELDS keys")
        finally:
            sup.stop()

    def test_ttft_decomposes_into_hold_plus_prefill(self):
        # A 120 ms queue hold and a 30 ms prompt evaluation. The two must not be conflated:
        # prefill_ms is what the engine computed, ttft_ms is what the client waited, and the
        # difference is the gate. This is the assertion that makes "prefill starts at the
        # scheduling point" a contract rather than a comment.
        worker = ScriptedWorker(max_slots=1, tokens=3, hold_s=0.12, prefill_s=0.03)
        sup = supervisor(worker)
        try:
            list(sup.stream([1, 2], max_new_tokens=3))
            summary = sup.last_summary
            hold = summary["ttft_ms"] - summary["prefill_ms"]
            self.assertGreaterEqual(summary["prefill_ms"], 30,
                                    "prefill_ms measures prompt evaluation only")
            self.assertGreaterEqual(summary["ttft_ms"], 150,
                                   "ttft_ms is acceptance to first token, hold included")
            self.assertGreaterEqual(hold, 120,
                                    "ttft_ms - prefill_ms is the queue hold, and it is measurable")
            self.assertLess(hold, 200, "the hold is not double-counted anywhere else")
        finally:
            sup.stop()

    def test_a_field_the_worker_never_sent_is_none_not_zero(self):
        # No request has run, so there is nothing to measure. Reporting 0 here would read
        # as "instantaneous", which is a different claim than "unknown".
        worker = ScriptedWorker(max_slots=1, tokens=3)
        sup = supervisor(worker)
        try:
            snapshot = sup.monitor_snapshot()
            for key in ("ttft_ms", "prefill_ms", "decode_ms", "prompt_ms",
                        "queue_hold_ms", "decode_tok_s", "stop_reason"):
                self.assertIsNone(snapshot[key], f"{key} has no data and must read as None")
            self.assertEqual(snapshot["status"], "up", "lifecycle is known even with no traffic")
        finally:
            sup.stop()

    def test_a_v1_summary_reports_its_missing_fields_as_none(self):
        # A worker built against the first, unpacked draft: 32 bytes, no prefill, no TTFT.
        payload = TERMINAL_V1.pack(0, 32, 12, 5, 1, 4, 2)
        summary = decode_terminal(payload)
        self.assertEqual(summary["decode_ms"], 12, "the fields a v1 worker has are still read")
        self.assertIsNone(summary["prefill_ms"], "v1 has no prefill window")
        self.assertIsNone(summary["ttft_ms"], "v1 has no TTFT; 0 would read as instantaneous")

    def test_ttft_includes_the_hold_and_is_never_less_than_prefill(self):
        worker = ScriptedWorker(max_slots=1, tokens=3, prefill_s=0.05)
        sup = supervisor(worker)
        try:
            list(sup.stream([1, 2], max_new_tokens=3))
            summary = sup.last_summary
            self.assertIsNotNone(summary["ttft_ms"])
            self.assertGreaterEqual(
                summary["ttft_ms"], summary["prefill_ms"],
                "TTFT starts at request acceptance, so it cannot be shorter than prefill",
            )
            self.assertGreaterEqual(summary["ttft_ms"], 50,
                                   "the 50 ms hold must show up in the user-visible wait")
        finally:
            sup.stop()

    def test_prompt_timing_does_not_move_with_the_draft_cycle(self):
        """Decision 1: the first speculative draft cycle is decode work.

        Two identical requests, one with a draft cycle and one without. prefill_ms is
        the same in both; decode_ms and ttft_ms carry the difference. If prompt timing
        ever moved with lookahead length, prompt telemetry would be a sampling artefact
        and an embedder could not read it as a prompt cost.

        Every bound here is derived from the schedule the fixture is told to run, never
        from the difference between two wall clocks. time.sleep() is a lower bound, so a
        window can only be longer than scheduled; int() drops at most 1 ms from each one.
        A window that comes back *shorter* than its own schedule is the attribution bug.
        Comparing two runs instead - the old `drafted >= plain + 150` - made the result
        depend on how the scheduler handled six 1 ms sleeps on that machine, and it
        failed at 156 against 157 on a quiet runner.
        """
        PREFILL_MS, DRAFT_MS = 50, 150
        FLOOR_MS = 2  # int() truncation, one per window being compared

        def run(draft_s: float) -> dict:
            worker = ScriptedWorker(max_slots=1, tokens=6, prefill_s=PREFILL_MS / 1000,
                                   draft_s=draft_s)
            sup = supervisor(worker)
            try:
                list(sup.stream([1, 2], max_new_tokens=6))
                return sup.last_summary
            finally:
                sup.stop()

        plain = run(0.0)
        drafted = run(DRAFT_MS / 1000)

        # The prompt window is measured against its own schedule and must not grow
        # into the lookahead: prefill_ms is bounded by the sleep the fixture ran.
        self.assertGreaterEqual(plain["prefill_ms"], PREFILL_MS - FLOOR_MS,
                                "prefill_ms is shorter than the prompt it was given")
        self.assertGreaterEqual(drafted["prefill_ms"], PREFILL_MS - FLOOR_MS,
                                "prefill_ms is shorter than the prompt it was given")
        self.assertLess(drafted["prefill_ms"], PREFILL_MS + DRAFT_MS,
                        "prefill_ms moved with the speculative lookahead")

        # The draft cycle is charged to decode_ms and nowhere else.
        self.assertGreaterEqual(drafted["decode_ms"], DRAFT_MS - FLOOR_MS,
                               "the draft cycle is not charged to decode_ms")
        self.assertLess(plain["decode_ms"], DRAFT_MS,
                        "decode_ms carries a draft cycle that was never scheduled")

        # ttft is stamped from the request start, so it contains prompt plus draft.
        self.assertGreaterEqual(drafted["ttft_ms"], PREFILL_MS + DRAFT_MS - FLOOR_MS,
                               "ttft_ms must include the first draft cycle")

        # queue_hold_ms is ttft - prefill: the part of first-token latency that is
        # neither prompt evaluation nor generation.
        plain_hold = derive_monitor_field("queue_hold_ms", plain, {})
        drafted_hold = derive_monitor_field("queue_hold_ms", drafted, {})
        self.assertGreaterEqual(drafted_hold, DRAFT_MS - FLOOR_MS,
                                "the derived hold does not absorb the draft cycle")
        self.assertLess(plain_hold, DRAFT_MS,
                        "the derived hold reports a draft cycle the worker never ran")

    def test_a_longer_summary_is_read_as_a_prefix(self):
        payload = TERMINAL_PREFIX.pack(1, 48, 6, 10, 20, 2, 3, 2, 15) + b"\x01\x02\x03\x04\x05\x06\x07\x08"
        summary = decode_terminal(payload)
        self.assertEqual(summary["struct_size"], 48)
        self.assertEqual(summary["produced_tokens"], 6)
        self.assertEqual(summary["ttft_ms"], 15)
        self.assertEqual(summary["stop_reason"], "limit")

    def test_a_summary_below_the_v1_minimum_is_refused(self):
        from serve.ipc_parser import FrameError
        with self.assertRaises(FrameError):
            decode_terminal(TERMINAL_PREFIX.pack(0, 36, 1, 1, 1, 0, 0, 1, 0))


if __name__ == "__main__":
    unittest.main()
