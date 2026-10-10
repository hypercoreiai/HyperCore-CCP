#!/usr/bin/env python3
"""Decision 1 + 2: the HTTP stream loop becomes a thin wrapper over supervisor.stream(),
and the host-side slot pre-check is removed."""
import pathlib
import re

p = pathlib.Path("/home/ai-user0/HyperCore/serve/server.py")
s = p.read_text()

# --- imports ---------------------------------------------------------------
s = s.replace(
    "from serve.hypercore_supervisor import HyperCoreProcessSupervisor\n",
    "from serve.hypercore_supervisor import (\n"
    "    HyperCoreProcessSupervisor,\n"
    "    StreamStalled,\n"
    "    WorkerBusy,\n"
    "    WorkerRejected,\n"
    "    WorkerUnreachable,\n"
    ")\n",
    1,
)

# --- replace the hand-rolled stream loop with the thin wrapper ----------
start = s.index("def process_active_stream_loop(")
section_start = s.index("# ---------------------------------------------------------------- raw inference lane")
nxt = re.search(r"\n(?:class|def) ", s[start:])
end = start + nxt.start()
old = s[section_start:end]

wrapper = '''# ---------------------------------------------------------------- raw inference lane
# POST /infer/stream is the raw-token route: it speaks the frame protocol directly and
# streams the frames out. The API routes build OpenAI/Anthropic-shaped bodies from the
# same generator; this one is the wire, for embedders and for the load tests.
#
# The loop below is deliberately thin. Everything that is stream *state* - the ack,
# the token/terminal transitions, the timeout walls, the CANCEL frame on early exit -
# lives in HyperCoreProcessSupervisor.stream(). This function only serialises what it
# is handed and notices that the client has gone.

STREAM_STALL_S = 30.0


def stream_sse(
    handler,
    supervisor_instance: HyperCoreProcessSupervisor,
    request_id: int,
    prompt_ids: list[int],
    temperature: float,
    top_p: float,
    top_k: int,
    max_new: int,
    pcie_frac: float = -1.0,
    spec_min_p: float = -1.0,
    stall_s: float = STREAM_STALL_S,
    timeout_s: float = 30.0,
) -> str:
    """Drive the supervisor's generator and write SSE. Returns an outcome token.

    "complete", "client_gone", "stalled", "worker_gone", or "busy"/"rejected" when
    the worker refused the request before a single frame was written - those two are
    returned rather than raised so the caller can still choose a status code.
    """
    started = False

    def emit(obj: dict) -> bool:
        nonlocal started
        if not started:
            handler.send_response(200)
            handler.send_header("Content-Type", "text/event-stream")
            handler.send_header("Cache-Control", "no-store")
            handler._cors()
            handler.end_headers()
            started = True
        try:
            handler.wfile.write(f"data: {json.dumps(obj)}\\n\\n".encode())
            handler.wfile.flush()
            return True
        except (BrokenPipeError, ConnectionResetError, OSError):
            return False

    try:
        for msg_type, token_id, metrics in supervisor_instance.stream(
            prompt_ids,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            max_new_tokens=max_new,
            pcie_frac=pcie_frac,
            spec_min_p=spec_min_p,
            timeout_s=timeout_s,
            silence_s=stall_s,
            request_id=request_id,
        ):
            if msg_type == STREAM_TOKEN:
                if not emit({"token_id": token_id,
                            "prompt_reused": int(metrics.get("prompt_reused") or 0)}):
                    return "client_gone"
            elif msg_type == STREAM_TERMINAL:
                logger.info(
                    "[MONITOR] request_id=%d status=success prompt_ms=%s decode_ms=%s "
                    "tokens=%s ttft_ms=%s stop_reason=%s",
                    request_id,
                    metrics.get("prefill_ms", 0),
                    metrics.get("decode_ms", 0),
                    metrics.get("produced_tokens", 0),
                    metrics.get("time_to_first_token_ms", 0),
                    metrics.get("stop_reason", "unknown"),
                )
                if not emit({"done": True,
                             "prompt_reused": int(metrics.get("prompt_reused") or 0),
                             "metrics": metrics}):
                    return "client_gone"
                return "complete"
    except StreamStalled as e:
        logger.error("[MONITOR] request_id=%d status=stall %s", request_id, e)
        emit({"done": True, "error": "stream stalled", "stop_reason": "cancelled"})
        return "stalled"
    except WorkerBusy as e:
        if not started:
            return "busy"
        logger.error("[MONITOR] request_id=%d status=busy %s", request_id, e)
        emit({"done": True, "error": str(e), "stop_reason": "cancelled"})
        return "busy"
    except WorkerRejected as e:
        if not started:
            return "rejected"
        emit({"done": True, "error": str(e), "stop_reason": "cancelled"})
        return "rejected"
    except WorkerUnreachable as e:
        logger.error("[MONITOR] request_id=%d status=worker_gone %s", request_id, e)
        if not started:
            return "worker_gone"
        emit({"done": True, "error": str(e), "stop_reason": "cancelled"})
        return "worker_gone"
    return "complete"

'''
s = s[:section_start] + wrapper + s[end:]

# --- _raw_stream: no host-side pre-check, the worker is the gate -------
old_raw = '''            if sup.in_flight() >= sup.max_batch_slots:
                self._json(429, {"error": {"type": "busy",
                                          "message": f"all {sup.max_batch_slots} batch slots are in use"}})
                return

            request_id = sup.next_request_id()
            frames = sup.open_stream(request_id)
            payload = build_submit_payload(
                temperature=float(req.get("temperature", 0.0)),
                top_p=float(req.get("top_p", 1.0)),
                top_k=int(req.get("top_k", 1)),
                max_new_tokens=int(req.get("max_new_tokens", 64)),
                pcie_frac=float(req.get("pcie_frac", -1.0)),
                spec_min_p=float(req.get("spec_min_p", -1.0)),
                prompt_tokens=[int(t) for t in tokens],
            )

            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-store")
            self._cors()
            self.end_headers()
            try:
                outcome = process_active_stream_loop(frames, self, request_id, sup)
            finally:
                sup.close_stream(request_id)
            if outcome != "complete":
                logger.warning("raw stream %d ended: %s", request_id, outcome)'''
new_raw = '''            # No host-side slot pre-check. The snapshot in max_batch_slots is taken at
            # startup and can disagree with the worker after a config change, so the
            # worker's own answer is the only one we act on.
            request_id = sup.next_request_id()
            outcome = stream_sse(
                self,
                sup,
                request_id,
                [int(t) for t in tokens],
                temperature=float(req.get("temperature", 0.0)),
                top_p=float(req.get("top_p", 1.0)),
                top_k=int(req.get("top_k", 1)),
                max_new_tokens=int(req.get("max_new_tokens", 64)),
                pcie_frac=float(req.get("pcie_frac", -1.0)),
                spec_min_p=float(req.get("spec_min_p", -1.0)),
            )
            if outcome == "busy":
                self._json(503, {"error": {"type": "busy",
                                          "message": "the compute node has no free batch slot"}})
            elif outcome == "rejected":
                self._json(400, {"error": {"type": "invalid_request_error",
                                          "message": "the engine rejected this request"}})
            elif outcome == "worker_gone":
                self._json(503, {"error": {"type": "engine_unavailable",
                                          "message": "the compute node is offline"}})
            elif outcome != "complete":
                logger.warning("raw stream %d ended: %s", request_id, outcome)'''
assert s.count(old_raw) == 1, "raw stream anchor"
s = s.replace(old_raw, new_raw)

# --- the API adapter keeps no absolute gate either ---------------------
old_gate = '''        slots = self.batch
        if slots <= 0:
            raise ModelBusy("the HyperCore worker reports no batch slots")
        if self.in_flight() >= slots:
            self.last_err = "all batch slots are full"
            raise ModelBusy("all batch slots are full")'''
new_gate = '''        # The worker is the authoritative gate: it answers the ack frame with
        # HYPERCORE_STATUS_BUSY and the supervisor raises WorkerBusy. A host-side
        # count here would be a snapshot that can drift from the running config.
        pass'''
assert s.count(old_gate) == 1, "generate gate anchor"
s = s.replace(old_gate, new_gate)

# --- status mapping: WorkerBusy is a 503, not the legacy 409 -----------
s = s.replace(
    '''            except ModelBusy as e:
                self._json(409, {"error": {"type": "model_busy", "message": str(e)}})''',
    '''            except WorkerBusy as e:
                self._json(503, {"error": {"type": "busy", "message": str(e)}})
            except ModelBusy as e:
                self._json(409, {"error": {"type": "model_busy", "message": str(e)}})''',
    1,
)
s = s.replace(
    '''            except ModelBusy as e:
                return self._json(409, responses_error_body(str(e), "server_error", code="model_busy"))''',
    '''            except WorkerBusy as e:
                return self._json(503, responses_error_body(str(e), "server_error", code="server_error"))
            except ModelBusy as e:
                return self._json(409, responses_error_body(str(e), "server_error", code="model_busy"))''',
    1,
)

p.write_text(s)
print("server.py rewritten")
