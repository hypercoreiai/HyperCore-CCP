"""tools/calibrate_adapter.py
Sequential calibration driver for the hypercore C boundary.

One engine instance, one request at a time, repeated over a parameter grid. The
terminal summary chunk is the only completion signal, so every request is matched
to its own session id carried through the callback's void*.
"""

import ctypes
import os
import threading


class RequestConfig(ctypes.Structure):
    _fields_ = [
        ("struct_size", ctypes.c_uint32),
        ("temperature", ctypes.c_float),
        ("top_p", ctypes.c_float),
        ("top_k", ctypes.c_uint32),
        ("max_new_tokens", ctypes.c_uint32),
        ("pcie_frac", ctypes.c_float),
        ("spec_min_p", ctypes.c_float),
    ]


class CapsStruct(ctypes.Structure):
    _fields_ = [
        ("struct_size", ctypes.c_uint32),
        ("backend_type", ctypes.c_uint32),
        ("max_batch_slots", ctypes.c_uint32),
        ("max_context_len", ctypes.c_uint32),
        ("active_pool_workers", ctypes.c_int32),
    ]


class SummaryStruct(ctypes.Structure):
    _fields_ = [
        ("struct_size", ctypes.c_uint32),
        ("decode_ms", ctypes.c_uint64),
        ("produced_tokens", ctypes.c_uint32),
        ("drafts_accepted", ctypes.c_uint32),
        ("drafts_offered", ctypes.c_uint32),
        ("stop_reason", ctypes.c_int),
    ]


class OutputChunk(ctypes.Structure):
    _fields_ = [
        ("token_id", ctypes.c_int32),
        ("prompt_reused", ctypes.c_uint32),
        ("summary", ctypes.POINTER(SummaryStruct)),
    ]


CMPFUNC = ctypes.CFUNCTYPE(None, ctypes.POINTER(OutputChunk), ctypes.c_void_p)

# Mirrors hypercore_status_t in hypercore/hypercore_blackbox.h.
SUCCESS, INVALID_ARG, BUSY, UNSUPPORTED = 0, -1, -2, -3

# Mirrors hypercore_stop_reason_t.
STOP_UNSPECIFIED, STOP_EOS, STOP_LIMIT, STOP_CANCEL, STOP_ERROR = 0, 1, 2, 3, 4


class HyperCoreCalibrationAdapter:
    def __init__(self, lib_path: str):
        self.lib = ctypes.CDLL(lib_path)
        self._setup_prototypes()
        # Bound method kept on the instance: ctypes does not keep the C function
        # object alive once the temporary argument is gone.
        self._native_cb_hook = CMPFUNC(self._internal_stream_dispatcher)
        self._active_sessions: dict[int, threading.Event] = {}
        self._session_metrics: dict[int, dict] = {}
        self._session_counter = 0
        self._counter_lock = threading.Lock()

    def _setup_prototypes(self) -> None:
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

    def caps(self, engine) -> dict:
        """Read the engine's declared capabilities through the boundary."""
        c = CapsStruct()
        c.struct_size = ctypes.sizeof(CapsStruct)
        status = self.lib.hypercore_engine_get_caps(engine, ctypes.byref(c))
        if status != SUCCESS:
            raise RuntimeError(f"hypercore_engine_get_caps failed: {status}")
        return {
            "backend_type": c.backend_type,
            "max_batch_slots": c.max_batch_slots,
            "max_context_len": c.max_context_len,
            "active_pool_workers": c.active_pool_workers,
        }

    def _next_session_id(self) -> int:
        """A monotonic unsigned id.

        Not a hash: a negative Python int passed as void* arrives on the other side as a large
        unsigned value and never matches the dict key, so the row is dropped silently.
        """
        with self._counter_lock:
            self._session_counter += 1
            return self._session_counter

    def _internal_stream_dispatcher(self, chunk_ptr, user_data_ptr) -> None:
        chunk = chunk_ptr.contents
        # The void* is a monotonic unsigned sequence id, not a pointer to anything.
        session_id = user_data_ptr if user_data_ptr else 0

        if chunk.token_id < 0 and chunk.summary:
            s = chunk.summary.contents
            if session_id in self._active_sessions:
                self._session_metrics[session_id] = {
                    "decode_ms": s.decode_ms,
                    "produced_tokens": s.produced_tokens,
                    "drafts_accepted": s.drafts_accepted,
                    "drafts_offered": s.drafts_offered,
                    "stop_reason": s.stop_reason,
                    "tok_per_sec": (
                        s.produced_tokens / (s.decode_ms / 1000.0) if s.decode_ms > 0 else 0.0
                    ),
                }
                self._active_sessions[session_id].set()

    @staticmethod
    def _validate(name: str, value: float) -> None:
        """Boundary rule: exactly -1.0 is the fallback sentinel, otherwise [0.0, 1.0]."""
        if value == -1.0:
            return
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"{name}={value} is outside the documented range")

    def run_noise_filtered_sweep(
        self,
        base_json_config: str,
        prompt_tokens: list[int],
        pcie_candidates: list[float],
        spec_candidates: list[float],
        repeats: int = 3,
    ) -> list[dict]:
        """Repeated calibration sweep over the parameter grid, interleaved across iterations.

        Returns one row per attempted combination, including the ones the engine refused:
        a dropped row is a result, not a gap in the table.
        """
        # Environmental hygiene: the engine reads HYPERCORE_* before any JSON.
        for key in list(os.environ):
            if key.startswith("HYPERCORE_"):
                del os.environ[key]

        engine_ptr = ctypes.c_void_p()
        res = self.lib.hypercore_engine_init(
            ctypes.byref(engine_ptr), base_json_config.encode("utf-8")
        )
        if res != SUCCESS:
            raise RuntimeError(f"Engine boot sequence aborted: {res}")

        token_array = (ctypes.c_int32 * len(prompt_tokens))(*prompt_tokens)
        matrix_results: list[dict] = []

        parameter_grid: list[tuple[float, float]] = [
            (pcie, spec) for pcie in pcie_candidates for spec in spec_candidates
        ]

        try:
            for iteration in range(repeats):
                for pcie, spec in parameter_grid:
                    self._validate("pcie_frac", pcie)
                    self._validate("spec_min_p", spec)

                    req = RequestConfig(
                        struct_size=ctypes.sizeof(RequestConfig),
                        temperature=0.0,
                        top_p=1.0,
                        top_k=1,
                        max_new_tokens=128,
                        pcie_frac=pcie,
                        spec_min_p=spec,
                    )

                    session_id = self._next_session_id()

                    completion_event = threading.Event()
                    self._active_sessions[session_id] = completion_event

                    status = self.lib.hypercore_engine_submit(
                        engine_ptr,
                        session_id,
                        ctypes.byref(req),
                        token_array,
                        len(prompt_tokens),
                        self._native_cb_hook,
                        ctypes.c_void_p(session_id),
                    )

                    row = {
                        "pcie_frac": pcie,
                        "spec_min_p": spec,
                        "iteration": iteration,
                        "status": status,
                        "stop_reason": None,
                        "metrics": {},
                    }

                    if status == SUCCESS:
                        if not completion_event.wait(timeout=15.0):
                            row["status"] = -100  # timed out; visible, not silent
                        else:
                            row["stop_reason"] = self._session_metrics.get(session_id, {}).get(
                                "stop_reason"
                            )
                            row["metrics"] = self._session_metrics.get(session_id, {})
                    elif status == BUSY:
                        raise RuntimeError(
                            "sequential sweep hit BUSY: the engine's slot accounting is wrong"
                        )

                    matrix_results.append(row)

                    self._active_sessions.pop(session_id, None)
                    self._session_metrics.pop(session_id, None)
        finally:
            self.lib.hypercore_engine_destroy(engine_ptr)

        return matrix_results
