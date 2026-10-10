"""serve/test_fatal_recovery.py - a dead link, and who is allowed to restart it.

The text protocol detected a native fault by reading an ERR line. The boundary has no
lines: the link closes, the listener's reader thread sees EOF, and every attached request
queue receives a death sentinel. Recovery is the supervisor's job - the server only
observes it.

    python -m unittest serve.test_fatal_recovery -v
"""
from __future__ import annotations

import time
import unittest

from serve.frame_fixture import ScriptedWorker
from serve.hypercore_supervisor import HyperCoreProcessSupervisor, WorkerUnreachable


class FatalRecoveryTest(unittest.TestCase):
    def _supervisor(self, worker: ScriptedWorker, max_restarts: int = 2) -> HyperCoreProcessSupervisor:
        sup = HyperCoreProcessSupervisor(
            transport=worker.connect, max_restarts=max_restarts, backoff_s=(0.0, 0.0, 0.0)
        )
        sup.start()
        return sup

    def test_a_dead_link_is_reported_without_waiting_out_the_timeout(self):
        worker = ScriptedWorker(max_slots=1, tokens=5, die_after=3)
        sup = self._supervisor(worker)
        try:
            started = time.monotonic()
            tokens = []
            try:
                for token_id, _reused, _summary in sup.stream([1, 2, 3, 4], max_new_tokens=5, timeout_s=30.0):
                    tokens.append(token_id)
            except WorkerUnreachable:
                pass
            elapsed = time.monotonic() - started
            self.assertLess(elapsed, 5.0,
                            f"the listener's EOF must be reported at once, not after a 30s timeout (took {elapsed:.1f}s)")
            self.assertLess(len(tokens), 5, "the stream must stop at the point the link died")
            self.assertFalse(sup.alive(), "a dead link invalidates health before the next request")
        finally:
            sup.stop()

    def test_recovery_is_the_supervisors_and_is_bounded(self):
        # die_after=2: status + one token are sent, then the link closes before the terminal
        # frame. Every request therefore ends in a dead link, which is the fault the server
        # used to detect from an ERR line.
        worker = ScriptedWorker(max_slots=1, tokens=1, die_after=2)
        sup = self._supervisor(worker, max_restarts=3)
        try:
            for expected_restarts in (1, 2, 3):
                with self.assertRaises(WorkerUnreachable):
                    list(sup.stream([1, 2, 3, 4], max_new_tokens=1, timeout_s=2.0))
                self.assertFalse(sup.alive(), "a dead link must invalidate health first")
                self.assertTrue(sup.start_worker(), "the supervisor restarts within its budget")
                state = sup.watchdog_state()
                self.assertEqual(state["restarts"], expected_restarts)
                self.assertTrue(state["alive"])
                self.assertEqual(state["restart_budget"], 3)

            # Fourth failure: the budget is spent. The observer gets False and decides what
            # to tell the client; nothing here tries again.
            with self.assertRaises(WorkerUnreachable):
                list(sup.stream([1, 2, 3, 4], max_new_tokens=1, timeout_s=2.0))
            self.assertFalse(sup.start_worker())
            state = sup.watchdog_state()
            self.assertTrue(state["budget_exhausted"])
            self.assertFalse(state["alive"])
        finally:
            sup.stop()

    def test_the_observer_sees_when_the_last_frame_arrived(self):
        worker = ScriptedWorker(max_slots=1, tokens=3)
        sup = self._supervisor(worker)
        try:
            list(sup.stream([1, 2, 3, 4], max_new_tokens=3))
            state = sup.watchdog_state()
            self.assertGreater(state["frames_read"], 3)
            self.assertGreater(state["bytes_read"], 24)
            self.assertIsNotNone(state["seconds_since_last_frame"])
        finally:
            sup.stop()

    def test_no_request_is_issued_while_the_link_is_dead(self):
        worker = ScriptedWorker(max_slots=1, tokens=1, die_after=1)
        sup = self._supervisor(worker, max_restarts=0)
        try:
            with self.assertRaises(WorkerUnreachable):
                list(sup.stream([1, 2, 3, 4], max_new_tokens=1, timeout_s=2.0))
            # Health is already false, so a second request never reaches the wire.
            before = len(worker.received)
            with self.assertRaises(WorkerUnreachable):
                list(sup.stream([1, 2, 3, 4], max_new_tokens=1, timeout_s=2.0))
            self.assertEqual(len(worker.received), before, "no request is sent on a dead link")
        finally:
            sup.stop()

    def test_teardown_does_not_wait_out_the_reader_timeout(self):
        """Stopping the supervisor must not block on a blocked recv().

        The reader thread is inside recv() when stop() is called, and the loop only
        checks the dead flag between frames. Setting the flag therefore cannot wake it:
        the join waits out its full timeout and every teardown costs five seconds of
        wall time. A restart budget is counted in attempts, but it is the seconds the
        HTTP server and the watchdog observe.
        """
        worker = ScriptedWorker(max_slots=2, tokens=3)
        sup = self._supervisor(worker, max_restarts=0)
        started = time.monotonic()
        sup.stop()
        elapsed = time.monotonic() - started
        self.assertLess(elapsed, 1.0,
                        f"teardown took {elapsed:.3f} s: the reader was not woken")
        self.assertFalse(sup.alive(), "a stopped supervisor is not alive")


if __name__ == "__main__":
    unittest.main()
