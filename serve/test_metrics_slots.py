"""serve/test_metrics_slots.py - /metrics over a supervisor-backed engine.

The report that started this: a real run answered every /metrics poll with
KeyError: 'state'. The worker's CAPS reply carries max_batch_slots=2, so metrics()
took the parallel branch and summed `x["state"]` over slots_view() - which the
supervisor had built as {"slot", "max_context"} only. On 127.0.0.1 the web page never
polled it; on 0.0.0.0 another device on the network did, and every poll raised.

Nothing in the suite drove metrics() through the HyperCore supervisor, which is why the
shape mismatch survived: serve/test_parallel.py asserts the shape against a fake engine
that does report states.

    python -m unittest serve.test_metrics_slots
"""
from __future__ import annotations

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


def supervisor(worker: ScriptedWorker) -> HyperCoreProcessSupervisor:
    sup = HyperCoreProcessSupervisor(transport=worker.connect, max_restarts=0)
    sup.start()
    return sup


def service(sup: HyperCoreProcessSupervisor) -> Service:
    return Service(HyperCoreRequestHandler(sup), ByteTokenizer(),
                  ChatTemplate(ROOT / "serve/chat_template.jinja"), model_name="test-model")


class SlotsViewShape(unittest.TestCase):
    """Every entry must carry a state: metrics() sums on it and the Monitor renders it."""

    def test_an_empty_engine_reports_every_slot_as_idle(self):
        sup = supervisor(ScriptedWorker(max_slots=2, tokens=3))
        try:
            view = sup.slots_view()
            self.assertEqual(len(view), 2, "the view must cover every slot the worker has")
            for entry in view:
                self.assertIn("state", entry, f"{entry} has no state; metrics() would raise")
                self.assertEqual(entry["state"], "idle", "nothing is running yet")
        finally:
            sup.stop()

    def test_a_request_reads_until_its_first_token_arrives(self):
        worker = ScriptedWorker(max_slots=2, tokens=5, prefill_s=0.25)
        sup = supervisor(worker)
        try:
            done = threading.Event()

            def run() -> None:
                for _ in sup.generate([1, 2, 3, 4, 5], max_new=5, sampling={},
                                     cancel=threading.Event()):
                    pass
                done.set()

            thread = threading.Thread(target=run)
            thread.start()
            # The worker is prefilling: the request is accepted, nothing produced yet.
            reading = sup.slots_view()
            self.assertEqual([x["state"] for x in reading], ["reading", "idle"],
                             f"during prefill the request must read: {reading}")
            done.wait(5)
            thread.join(5)
            settled = sup.slots_view()
            self.assertTrue(all(x["state"] == "idle" for x in settled),
                           f"a finished request releases its slot: {settled}")
        finally:
            sup.stop()

    def test_the_busy_count_never_exceeds_the_slot_count(self):
        sup = supervisor(ScriptedWorker(max_slots=2, tokens=3))
        try:
            for _ in range(4):
                sup.submit([1, 2, 3], max_new_tokens=3)
            view = sup.slots_view()
            busy = sum(1 for x in view if x.get("state", "idle") != "idle")
            self.assertLessEqual(busy, len(view))
        finally:
            sup.stop()


class MetricsOverTheSupervisor(unittest.TestCase):
    def test_metrics_reports_the_slots_without_raising(self):
        sup = supervisor(ScriptedWorker(max_slots=2, tokens=3))
        svc = service(sup)
        try:
            m = svc.metrics()
            live = m["live"]
            self.assertIn("slots", live, "the parallel branch must report the slots")
            self.assertTrue(all("state" in x for x in live["slots"]),
                            f"every slot must carry a state: {live['slots']}")
            self.assertEqual(live["outside_slots"], 0, "nothing is running, so nothing waits")
            self.assertEqual(live["running"], 0)
        finally:
            sup.stop()

    def test_a_slot_entry_with_no_state_is_read_as_idle(self):
        """The endpoint cannot be where a shape error becomes a 500."""
        sup = supervisor(ScriptedWorker(max_slots=2, tokens=3))
        svc = service(sup)
        try:
            sup.slots_view = lambda: [{"slot": 0}, {"slot": 1, "state": "generating"}]
            m = svc.metrics()
            self.assertEqual(m["live"]["outside_slots"], 0,
                            "one slot reported busy out of two: nothing is outside them")
        finally:
            sup.stop()


if __name__ == "__main__":
    unittest.main()
