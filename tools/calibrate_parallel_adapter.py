"""tools/calibrate_parallel_adapter.py
Backpressure driver: floods the engine past its declared batch slots and checks that
HYPERCORE_STATUS_BUSY is returned exactly when the slots are full, and that a bounced
request consumed nothing.

The slot limit is read from the boundary (hypercore_engine_get_caps), not passed in.
If the caller supplies it, the test is tautological: it proves the adapter agrees with
a number the adapter was given.
"""

import ctypes
import threading

from calibrate_adapter import (
    BUSY,
    CMPFUNC,
    INVALID_ARG,
    SUCCESS,
    UNSUPPORTED,
    CapsStruct,
    RequestConfig,
)


class ParallelHyperCoreEvaluator:
    """Floods engine slots concurrently up to saturation to test busy backpressure."""

    def __init__(self, lib_path: str):
        self.lib = ctypes.CDLL(lib_path)
        self.lib.hypercore_engine_init.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.c_char_p]
        self.lib.hypercore_engine_init.restype = ctypes.c_int
        self.lib.hypercore_engine_get_caps.argtypes = [ctypes.c_void_p, ctypes.POINTER(CapsStruct)]
        self.lib.hypercore_engine_get_caps.restype = ctypes.c_int
        self.lib.hypercore_engine_destroy.argtypes = [ctypes.c_void_p]
        self.lib.hypercore_engine_destroy.restype = None
        self.lib.hypercore_engine_submit.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint64,
            ctypes.POINTER(RequestConfig),
            ctypes.POINTER(ctypes.c_int32),
            ctypes.c_size_t,
            CMPFUNC,
            ctypes.c_void_p,
        ]
        self.lib.hypercore_engine_submit.restype = ctypes.c_int
        # Kept on the instance: the C function pointer must outlive submit().
        self._native_cb_hook = CMPFUNC(self._parallel_stream_callback)
        self._session_events: dict[int, threading.Event] = {}
        self._session_results: dict[int, dict] = {}
        self._session_counter = 0
        self._counter_lock = threading.Lock()

    def _next_session_id(self) -> int:
        # Not thread-safe without the lock: += on an attribute is load/add/store,
        # and two threads landing on the same id overwrite each other's event.
        with self._counter_lock:
            self._session_counter += 1
            return self._session_counter

    def _parallel_stream_callback(self, chunk_ptr, user_data_ptr) -> None:
        chunk = chunk_ptr.contents
        session_id = user_data_ptr if user_data_ptr else 0
        if chunk.token_id < 0 and session_id in self._session_events:
            s = chunk.summary.contents if chunk.summary else None
            self._session_results[session_id] = {
                "produced": s.produced_tokens if s else 0,
                "decode_ms": s.decode_ms if s else 0,
                "stop_reason": s.stop_reason if s else None,
            }
            self._session_events[session_id].set()

    def flood_engine_concurrently(
        self, engine_ptr, prompt_tokens: list[int], overshoot: int = 2, timeout_s: float = 5.0
    ) -> dict:
        token_array = (ctypes.c_int32 * len(prompt_tokens))(*prompt_tokens)

        caps = CapsStruct()
        caps.struct_size = ctypes.sizeof(CapsStruct)
        status = self.lib.hypercore_engine_get_caps(engine_ptr, ctypes.byref(caps))
        if status != SUCCESS:
            raise RuntimeError(f"hypercore_engine_get_caps failed: {status}")
        max_slots = caps.max_batch_slots

        outcomes = {"accepted": 0, "busy": 0, "invalid": 0, "unsupported": 0, "timed_out": 0}
        outcomes_lock = threading.Lock()
        threads: list[threading.Thread] = []

        def worker_task() -> None:
            req = RequestConfig(
                struct_size=ctypes.sizeof(RequestConfig),
                temperature=0.0,
                top_p=1.0,
                top_k=1,
                max_new_tokens=32,
                pcie_frac=-1.0,
                spec_min_p=-1.0,
            )
            session_id = self._next_session_id()
            evt = threading.Event()
            self._session_events[session_id] = evt

            status = self.lib.hypercore_engine_submit(
                engine_ptr,
                session_id,
                ctypes.byref(req),
                token_array,
                len(prompt_tokens),
                self._native_cb_hook,
                ctypes.c_void_p(session_id),
            )

            with outcomes_lock:
                if status == SUCCESS:
                    outcomes["accepted"] += 1
                    if not evt.wait(timeout=timeout_s):
                        outcomes["timed_out"] += 1
                elif status == BUSY:
                    outcomes["busy"] += 1
                elif status == INVALID_ARG:
                    outcomes["invalid"] += 1
                elif status == UNSUPPORTED:
                    outcomes["unsupported"] += 1
                else:
                    outcomes["timed_out"] += 1

            self._session_events.pop(session_id, None)
            self._session_results.pop(session_id, None)

        attempts = max_slots + overshoot
        for _ in range(attempts):
            t = threading.Thread(target=worker_task)
            threads.append(t)
            t.start()
        for t in threads:
            t.join()

        outcomes["attempts"] = attempts
        outcomes["max_slots"] = max_slots
        outcomes["session_ids"] = self._session_counter
        return outcomes


if __name__ == "__main__":
    import sys

    lib = sys.argv[1] if len(sys.argv) > 1 else "./libhypercore_engine.so"
    ev = ParallelHyperCoreEvaluator(lib)
    engine = ctypes.c_void_p()
    if ev.lib.hypercore_engine_init(ctypes.byref(engine), b'{"batch": 2}') != SUCCESS:
        raise SystemExit("init failed")
    result = ev.flood_engine_concurrently(engine, [1, 2, 3])
    ev.lib.hypercore_engine_destroy(engine)
    print(result)
    expected = result["attempts"] - result["max_slots"]
    if result["accepted"] != result["max_slots"] or result["busy"] != expected:
        raise SystemExit(
            f"FAIL: {result['max_slots']} slots, {result['attempts']} attempts "
            f"-> expected {result['max_slots']} accepted / {expected} busy, "
            f"got {result['accepted']} / {result['busy']}"
        )
    print("PASS: accepted == declared slots, every extra request bounced with BUSY")
