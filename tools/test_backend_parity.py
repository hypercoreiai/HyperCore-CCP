#!/usr/bin/env python3
"""tools/test_backend_parity.py - the comparison rules, tested against one backend.

The parity harness needs two built artifacts to run. Its rules do not: what must match,
what is allowed to differ, and what counts as a missing backend are all decisions that
can be tested with hand-built snapshots and the socketpair mock worker.

Run: python3 -m unittest tools.test_backend_parity
"""
from __future__ import annotations

import unittest

from serve.frame_fixture import ScriptedWorker
from serve.hypercore_supervisor import HyperCoreProcessSupervisor
from tools.backend_parity import (
    PROBE_CONFIG,
    Snapshot,
    capture,
    compare,
    find_worker,
    report,
)


def snap(backend: str = "cpu", tokens: tuple[int, ...] = (1000, 1001, 1002), **over) -> Snapshot:
    """A snapshot with the fields a real worker sends, plus whatever the test changes."""
    terminal = {
        "struct_size": 40,
        "produced_tokens": len(tokens),
        "drafts_accepted": 0,
        "drafts_offered": 0,
        "prompt_reused": 0,
        "stop_reason": "limit",
        "prefill_ms": 8,
        "decode_ms": 320,
        "ttft_ms": 8,
    }
    terminal.update(over.pop("terminal", {}))
    caps = {"backend_type": 0, "max_batch_slots": 2, "max_context_len": 4096}
    caps.update(over.pop("caps", {}))
    return Snapshot(backend=backend, worker="/dev/null", caps=caps, tokens=list(tokens), terminal=terminal)


class CompareRules(unittest.TestCase):
    def test_identical_snapshots_have_no_problems(self) -> None:
        self.assertEqual(compare(snap("cpu"), snap("cpu")), [])

    def test_a_single_token_difference_is_found_and_located(self) -> None:
        problems = compare(snap("cpu", (1000, 1001, 1002)), snap("cuda", (1000, 1007, 1002)))
        self.assertEqual(len(problems), 1)
        self.assertIn("token stream differs at index 1", problems[0])

    def test_a_different_length_is_a_difference(self) -> None:
        problems = compare(snap("cpu", (1000, 1001, 1002)), snap("cuda", (1000, 1001)))
        self.assertTrue(any("token stream differs" in p for p in problems))

    def test_timing_is_not_compared(self) -> None:
        a = snap("cpu", terminal={"decode_ms": 320, "prefill_ms": 8, "ttft_ms": 8})
        b = snap("cuda", terminal={"decode_ms": 41, "prefill_ms": 3, "ttft_ms": 2})
        self.assertEqual(compare(a, b), [])

    def test_sub_millisecond_decode_is_a_measurement_not_an_absence(self) -> None:
        # decode_ms is an integer in ms: 0 means "under a millisecond", None means "never
        # measured". Treating 0 as missing would fail every fast synthetic run.
        self.assertEqual(compare(snap("cpu", terminal={"decode_ms": 0}), snap("cpu", terminal={"decode_ms": 0})), [])
        problems = compare(snap("cpu", terminal={"decode_ms": None}), snap("cpu", terminal={"decode_ms": 0}))
        self.assertTrue(any("no decode window" in p for p in problems))

    def test_a_counter_that_disagrees_with_the_delivered_tokens_is_caught(self) -> None:
        problems = compare(snap("cpu", (1000, 1001)), snap("cpu", (1000, 1001)))
        self.assertEqual(problems, [])
        lying = snap("cpu", (1000, 1001))
        lying.terminal["produced_tokens"] = 5
        problems = compare(lying, snap("cpu", (1000, 1001)))
        self.assertTrue(any("reported 5 produced tokens but delivered 2" in p for p in problems))

    def test_the_backend_identity_may_differ_and_the_slot_count_may_not(self) -> None:
        a = snap("cpu", caps={"backend_type": 0, "max_batch_slots": 2})
        b = snap("cuda", caps={"backend_type": 1, "max_batch_slots": 2})
        self.assertEqual(compare(a, b), [])
        b = snap("cuda", caps={"backend_type": 1, "max_batch_slots": 4})
        problems = compare(a, b)
        self.assertTrue(any("capability max_batch_slots" in p for p in problems))

    def test_stop_reason_is_part_of_the_result(self) -> None:
        problems = compare(snap("cpu", terminal={"stop_reason": "limit"}), snap("cuda", terminal={"stop_reason": "cancel"}))
        self.assertTrue(any("summary field stop_reason" in p for p in problems))


class ReportVerdict(unittest.TestCase):
    def test_clean_backends_report_zero(self) -> None:
        code, lines = report({"cpu": [snap("cpu")], "cuda": [snap("cuda")]}, [])
        self.assertEqual(code, 0)
        self.assertTrue(any(l.startswith("[PASS] cpu vs cuda") for l in lines))

    def test_drift_reports_one(self) -> None:
        code, lines = report(
            {"cpu": [snap("cpu")], "cuda": [snap("cuda", tokens=(1000, 1001, 1003))]},
            [],
        )
        self.assertEqual(code, 1)
        self.assertTrue(any(l.startswith("[FAIL] cpu vs cuda") for l in lines))

    def test_a_required_backend_that_was_not_built_reports_two(self) -> None:
        code, lines = report({"cpu": [snap("cpu")], "cuda": []}, ["cuda"])
        self.assertEqual(code, 2)
        self.assertTrue(any("required by --require but not built" in l for l in lines))

    def test_an_optional_missing_backend_is_skipped_not_failed(self) -> None:
        code, lines = report({"cpu": [snap("cpu")], "hip": []}, [])
        self.assertEqual(code, 0)
        self.assertTrue(any("hip: no worker built - skipped" in l for l in lines))

    def test_a_single_backend_reports_no_comparison_rather_than_a_pass(self) -> None:
        code, lines = report({"cpu": [snap("cpu")]}, [])
        self.assertEqual(code, 0)
        self.assertTrue(any(l.startswith("[SKIP]") for l in lines))

    def test_a_non_deterministic_backend_is_drift(self) -> None:
        code, lines = report({"cpu": [snap("cpu"), snap("cpu", tokens=(1000, 1001, 1003))]}, [])
        self.assertEqual(code, 1)
        self.assertTrue(any("not deterministic across runs" in l for l in lines))


class Discovery(unittest.TestCase):
    def test_a_backend_that_was_never_built_is_reported_as_none(self) -> None:
        self.assertIsNone(find_worker("no-such-backend"))
        self.assertIsNone(find_worker("hip"))

    def test_the_probe_is_deterministic_by_construction(self) -> None:
        # top_k=1 and temperature=0 are what make a differing stream a backend difference
        # rather than sampling noise.
        self.assertEqual(PROBE_CONFIG["top_k"], 1)
        self.assertEqual(PROBE_CONFIG["temperature"], 0.0)
        self.assertEqual(PROBE_CONFIG["pcie_frac"], -1.0)  # the sentinel, not a configured value


class CaptureAgainstTheMockWorker(unittest.TestCase):
    """capture() is the part that touches the wire, so it is tested with the fixture."""

    def test_tokens_and_terminal_are_collected_from_a_mock_worker(self) -> None:
        worker = ScriptedWorker(max_slots=2, tokens=5, backend=0)
        sup = HyperCoreProcessSupervisor(transport=worker.connect)
        sup.start()
        try:
            snap_ = capture(sup, "cpu", "mock")
        finally:
            sup.stop()
            worker.close()

        self.assertIsNone(snap_.error)
        self.assertEqual(len(snap_.tokens), 5)
        self.assertTrue(snap_.ok())
        self.assertEqual(snap_.terminal["produced_tokens"], 5)
        self.assertEqual(snap_.terminal["stop_reason"], "limit")
        self.assertEqual(snap_.caps["max_batch_slots"], 2)
        # A mock that reports a different backend must not be compared as if it were the
        # same one: the harness only compares counters, and backend_type is excluded on purpose.
        self.assertEqual(snap_.caps["backend_type"], 0)

    def test_a_stream_that_never_starts_is_recorded_as_an_error_not_an_empty_result(self) -> None:
        """A backend that cannot take the request must fail loudly, not return nothing.

        An empty snapshot and an errored one look the same to a caller that only checks
        `tokens`; only the second one can be reported as a failure.
        """
        from serve.ipc_parser import CMD_SUBMIT, build_submit_payload

        worker = ScriptedWorker(max_slots=1, tokens=2, prefill_s=0.3)
        sup = HyperCoreProcessSupervisor(transport=worker.connect)
        sup.start()
        held = sup.next_request_id()
        sup.open_stream(held)
        sup.send_ipc_message(CMD_SUBMIT, held, build_submit_payload(prompt_tokens=[1, 2]))
        second = capture(sup, "cpu", "mock")  # the only slot is still in use
        sup.stop()
        worker.close()
        self.assertIsNotNone(second.error)
        self.assertFalse(second.ok())
        self.assertIn("Busy", second.error)


if __name__ == "__main__":
    unittest.main()
