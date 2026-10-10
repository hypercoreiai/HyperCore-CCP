import ctypes
import itertools
import os
import time
import json
import threading
from typing import Dict, List, Optional, Tuple


class RequestConfig(ctypes.Structure):
    _fields_ = [
        ("struct_size", ctypes.c_uint32),
        ("temperature", ctypes.c_float),
        ("top_p", ctypes.c_float),
        ("top_k", ctypes.c_uint32),
        ("max_new_tokens", ctypes.c_uint32),
        ("pcie_frac", ctypes.c_float),
        ("spec_min_p", ctypes.c_float)
    ]


class SummaryStruct(ctypes.Structure):
    _fields_ = [
        ("struct_size", ctypes.c_uint32),
        ("decode_ms", ctypes.c_uint64),
        ("produced_tokens", ctypes.c_uint32),
        ("drafts_accepted", ctypes.c_uint32),
        ("drafts_offered", ctypes.c_uint32),
        ("stop_reason", ctypes.c_int)
    ]


class OutputChunk(ctypes.Structure):
    _fields_ = [
        ("token_id", ctypes.c_int32),
        ("prompt_reused", ctypes.c_uint32),
        ("summary", ctypes.POINTER(SummaryStruct))
    ]


# Explicitly maintain global callback wrapper reference mapping to prevent garbage collection crashes
CMPFUNC = ctypes.CFUNCTYPE(None, ctypes.POINTER(OutputChunk), ctypes.c_void_p)


class HyperCoreCalibrationAdapter:
    def __init__(self, lib_path: str):
        self.lib = ctypes.CDLL(lib_path)
        self._setup_prototypes()
        # Keep the callback reference bound to the instance life cycle to prevent segmentation faults
        self._native_cb_hook = CMPFUNC(self._internal_stream_dispatcher)
        self._active_sessions: Dict[int, threading.Event] = {}
        self._session_metrics: Dict[int, Dict] = {}
        # A monotonic counter, not hash(): see the note in run_noise_filtered_sweep.
        self._session_counter = itertools.count(1)

    def _setup_prototypes(self):
        self.lib.hypercore_engine_init.argtypes = [ctypes.POINTER(ctypes.c_void_p), ctypes.c_char_p]
        self.lib.hypercore_engine_init.restype = ctypes.c_int
        self.lib.hypercore_engine_destroy.argtypes = [ctypes.c_void_p]
        self.lib.hypercore_engine_destroy.restype = None
        self.lib.hypercore_engine_submit.argtypes = [
            ctypes.c_void_p, ctypes.POINTER(RequestConfig),
            ctypes.POINTER(ctypes.c_int32), ctypes.c_size_t,
            ctypes.c_void_p, ctypes.c_void_p
        ]
        self.lib.hypercore_engine_submit.restype = ctypes.c_int

    def _internal_stream_dispatcher(self, chunk_ptr, user_data_ptr):
        """Asynchronous callback router tracking execution lifespan signals."""
        chunk = chunk_ptr.contents
        session_id = int(user_data_ptr) if user_data_ptr else 0

        # Capture performance profiles directly upon completion signals
        if chunk.token_id < 0 and chunk.summary:
            s = chunk.summary.contents
            if session_id in self._active_sessions:
                self._session_metrics[session_id] = {
                    "decode_ms": s.decode_ms,
                    "produced_tokens": s.produced_tokens,
                    "stop_reason": s.stop_reason,
                    "tok_per_sec": s.produced_tokens / (s.decode_ms / 1000.0) if s.decode_ms > 0 else 0.0
                }
                # Unblock the waiting driver thread
                self._active_sessions[session_id].set()

    def run_noise_filtered_sweep(
        self,
        base_json_config: str,
        prompt_tokens: List[int],
        pcie_candidates: List[float],
        spec_candidates: List[float],
        repeats: int = 3,
        busy_timeout_s: float = 5.0
    ) -> List[Dict]:
        """Executes repeated interleaved calibration matrix steps over a single model instance."""

        # Enforce environmental hygiene state BEFORE initializing the shared engine instance
        for key in list(os.environ.keys()):
            if key.startswith("HYPERCORE_"):
                del os.environ[key]

        engine_ptr = ctypes.c_void_p()
        res = self.lib.hypercore_engine_init(ctypes.byref(engine_ptr), base_json_config.encode('utf-8'))
        if res != 0:
            raise RuntimeError(f"Engine matrix boot sequence aborted: {res}")

        token_array = (ctypes.c_int32 * len(prompt_tokens))(*prompt_tokens)
        matrix_results = []

        # Generate structural grid variants
        parameter_grid = []
        for pcie in pcie_candidates:
            for spec in spec_candidates:
                parameter_grid.append((pcie, spec))

        try:
            # Interleave evaluations to distribute system noise evenly
            for iteration in range(repeats):
                for pcie, spec in parameter_grid:

                    req = RequestConfig(
                        struct_size=ctypes.sizeof(RequestConfig),
                        temperature=0.0,
                        top_p=1.0,
                        top_k=1,
                        max_new_tokens=128,
                        pcie_frac=pcie,
                        spec_min_p=spec
                    )

                    # Defensive Boundary Check: Catch invalid ranges before making boundary calls
                    if not (-1.0 <= req.pcie_frac <= 1.0) or req.pcie_frac < -1.0:
                        raise ValueError(f"Inbound pcie_frac rejected by boundary: {req.pcie_frac}")
                    if not (-1.0 <= req.spec_min_p <= 1.0) or req.spec_min_p < -1.0:
                        raise ValueError(f"Inbound spec_min_p rejected by boundary: {req.spec_min_p}")

                    session_id = next(self._session_counter)
                    completion_event = threading.Event()
                    self._active_sessions[session_id] = completion_event

                    start_backpressure = time.time()
                    status = -2  # Initialize as BUSY

                    # Retry loop handles engine backpressure limits smoothly
                    while status == -2:
                        status = self.lib.hypercore_engine_submit(
                            engine_ptr, ctypes.byref(req), token_array, len(prompt_tokens),
                            self._native_cb_hook, ctypes.c_void_p(session_id)
                        )
                        if status == -2:
                            if time.time() - start_backpressure > busy_timeout_s:
                                break
                            time.sleep(0.01)  # Yield thread briefly

                    if status == 0:
                        # block the host thread until the asynchronous loop signals completion
                        if completion_event.wait(timeout=10.0):
                            metrics = self._session_metrics.get(session_id, {})
                            matrix_results.append({
                                "pcie_frac": pcie,
                                "spec_min_p": spec,
                                "iteration": iteration,
                                "metrics": metrics
                            })

                    # Clean up tracking maps for this session
                    self._active_sessions.pop(session_id, None)
                    self._session_metrics.pop(session_id, None)

        finally:
            self.lib.hypercore_engine_destroy(engine_ptr)

        return matrix_results


if __name__ == "__main__":
    import sys
    lib = sys.argv[1] if len(sys.argv) > 1 else "./libhypercore_engine.so"
    rows = HyperCoreCalibrationAdapter(lib).run_noise_filtered_sweep(
        '{"batch": 2}', [1, 2, 3, 4], [0.0, 0.2, 0.35, 0.55, 0.75], [0.3, 0.5, 0.7]
    )
    print(json.dumps(rows[:2], indent=1))
    print("rows:", len(rows))
