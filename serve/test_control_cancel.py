"""serve/test_control_cancel.py - a Stop that arrives before the first token.

The behaviour this test has always cared about: a request cancelled while the engine is
still reading the prompt must be sent at once, not after the first token, and it must be
sent exactly once. Under the text protocol that was a control line into a pipe; here it is
a CANCEL frame on the same socket as the stream.

    python -m unittest serve.test_control_cancel -v
"""
from __future__ import annotations

import threading
import unittest

from serve.frame_fixture import STOP_CANCEL, ScriptedWorker
from serve.hypercore_supervisor import HyperCoreProcessSupervisor
from serve.ipc_parser import CMD_CANCEL, STREAM_TERMINAL


class ControlCancelTest(unittest.TestCase):
    def _supervisor(self, worker: ScriptedWorker) -> HyperCoreProcessSupervisor:
        sup = HyperCoreProcessSupervisor(transport=worker.connect, max_restarts=0)
        sup.start()
        return sup

    def test_cancel_during_prefill_is_sent_at_once(self):
        # prefill_s is the window in which the engine has accepted the request but emitted
        # nothing. A cancel issued in that window has to reach the wire before any token.
        worker = ScriptedWorker(max_slots=2, tokens=50, prefill_s=0.2)
        sup = self._supervisor(worker)
        try:
            rid, status = sup.submit([1, 2, 3, 4], max_new_tokens=50)
            self.assertEqual(status, 0)

            sup.cancel(rid)
            self.assertTrue(worker.await_frame(CMD_CANCEL), "the cancel frame must reach the worker")
            cancel_frames = [r for r in worker.received if r[0] == CMD_CANCEL]
            self.assertEqual(len(cancel_frames), 1, "the cancel must be written exactly once")
            self.assertEqual(cancel_frames[0][1], rid, "the cancel carries the request id")
        finally:
            sup.stop()

    def test_a_cancelled_stream_terminates_with_cancel(self):
        worker = ScriptedWorker(max_slots=1, tokens=200, prefill_s=0.15)
        sup = self._supervisor(worker)
        try:
            rid = sup.next_request_id()
            delivered = 0
            terminal = None
            for msg_type, _token_id, summary in sup.stream(
                [1, 2, 3, 4], max_new_tokens=200, request_id=rid
            ):
                if msg_type == STREAM_TERMINAL:
                    terminal = summary
                    break
                delivered += 1
                if delivered == 1:
                    sup.cancel(rid)

            self.assertIsNotNone(terminal, "the stream must end with a terminal frame")
            self.assertEqual(terminal["stop_reason"], "cancel")
            self.assertEqual(terminal["stop_reason_code"], STOP_CANCEL)
            self.assertLess(delivered, 200, "cancel must stop the stream before max_new_tokens")
        finally:
            sup.stop()

    def test_cancel_of_an_unknown_id_is_a_no_op_on_the_wire(self):
        worker = ScriptedWorker(max_slots=1, tokens=1)
        sup = self._supervisor(worker)
        try:
            self.assertTrue(sup.cancel(999999))
            self.assertTrue(worker.await_frame(CMD_CANCEL))
            self.assertEqual(len([r for r in worker.received if r[0] == CMD_CANCEL]), 1)
            # The worker still answers normally: the spurious cancel changed nothing.
            self.assertEqual(next(sup.stream([1, 2], max_new_tokens=1))[1], 1000)
        finally:
            sup.stop()

    def test_a_dropped_client_is_cancelled_by_the_request_thread(self):
        """The server's BrokenPipeError path: the handler holds the request id and issues
        the cancel itself. Nothing in the boundary can know a client hung up."""
        worker = ScriptedWorker(max_slots=1, tokens=100, prefill_s=0.1)
        sup = self._supervisor(worker)
        try:
            rid = sup.next_request_id()
            cancel = threading.Event()
            stream = sup.stream([1, 2, 3, 4], max_new_tokens=100, request_id=rid)
            for _ in range(3):
                next(stream)
            cancel.set()
            sup.cancel(rid)
            for _msg_type, _token_id, summary in stream:
                if _msg_type == STREAM_TERMINAL:
                    self.assertEqual(summary["stop_reason"], "cancel")
                    break
        finally:
            sup.stop()


if __name__ == "__main__":
    unittest.main()
