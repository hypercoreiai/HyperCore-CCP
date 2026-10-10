#!/usr/bin/env python3
"""One-shot rewrite: make supervisor.stream() the single stream reader loop."""
import pathlib

p = pathlib.Path("/home/ai-user0/HyperCore/serve/hypercore_supervisor.py")
s = p.read_text()

old_exc = 'class WorkerUnreachable(RuntimeError):\n    """The worker process is gone or the link is broken."""\n'
new_exc = (
    'class WorkerUnreachable(RuntimeError):\n'
    '    """The worker process is gone or the link is broken."""\n\n\n'
    'class WorkerBusy(WorkerUnreachable):\n'
    '    """The worker\'s own slot gate refused the request (HYPERCORE_STATUS_BUSY).\n\n'
    '    This is the authoritative answer. The host-side count is a snapshot taken at\n'
    '    startup and can disagree with the worker after a config change, so the web\n'
    '    layer never pre-checks it: a 503 here is the worker saying its lanes are full.\n'
    '    """\n\n\n'
    'class WorkerRejected(WorkerUnreachable):\n'
    '    """The worker accepted the frame but rejected the configuration (invalid arg)."""\n\n\n'
    'class StreamStalled(WorkerUnreachable):\n'
    '    """No frame arrived within the silence window; the request was cancelled."""\n'
)
assert s.count(old_exc) == 1, "exception anchor"
s = s.replace(old_exc, new_exc)

start = s.index("    def stream(\n")
end = s.index("    # ---------------------------------------------------------------- the Engine surface")
old_stream = s[start:end]

lines = [
    "    def stream(",
    "        self,",
    "        prompt_tokens: list[int],",
    "        temperature: float = 0.0,",
    "        top_p: float = 1.0,",
    "        top_k: int = 1,",
    "        max_new_tokens: int = 64,",
    "        pcie_frac: float = -1.0,",
    "        spec_min_p: float = -1.0,",
    "        timeout_s: float = 30.0,",
    "        silence_s: float = 0.0,",
    "        request_id: int | None = None,",
    "    ) -> Iterator[tuple[int, int, dict[str, Any]]]:",
    '        """Yield (msg_type, token_id, metrics) for one request, ack to terminal.',
    "",
    "        msg_type is STREAM_TOKEN or STREAM_TERMINAL. A token frame carries the",
    "        prompt-reuse count in metrics; the terminal frame carries the decoded",
    "        summary. This is the only place a frame tuple becomes an application",
    "        message: the HTTP layer, the calibration adapter and generate() all read",
    "        through it, so a wire change lands in one loop instead of three.",
    "",
    "        The timeout walls and the CANCEL frame live here. A caller that stops",
    "        consuming early - a dropped client - does not have to know about",
    "        CMD_CANCEL: the finally block sends it, so slot reclamation is never the",
    "        caller's job.",
    "",
    "        Raises WorkerBusy when the worker's slot gate refuses the request,",
    "        WorkerRejected when the configuration is invalid, StreamStalled when the",
    "        stream goes silent, WorkerUnreachable when the link itself dies.",
    '        """',
    "        request_id = request_id or self.next_request_id()",
    "        listener = self._listener",
    "        if listener is None:",
    '            raise WorkerUnreachable("no link to the worker")',
    "",
    "        frames = self.open_stream(request_id)",
    "        terminal_seen = False",
    "        try:",
    "            payload = build_submit_payload(",
    "                temperature=temperature,",
    "                top_p=top_p,",
    "                top_k=top_k,",
    "                max_new_tokens=max_new_tokens,",
    "                pcie_frac=pcie_frac,",
    "                spec_min_p=spec_min_p,",
    "                prompt_tokens=prompt_tokens,",
    "            )",
    "            if not self.send_ipc_message(CMD_SUBMIT, request_id, payload):",
    '                raise WorkerUnreachable("link closed before the request was sent")',
    "",
    "            item = frames.get(timeout=timeout_s)",
    "            if item[0] is None:",
    '                raise WorkerUnreachable("worker died while scheduling the request")',
    "            if item[0] != expected_reply(CMD_SUBMIT):",
    '                raise WorkerUnreachable(f"expected an ack frame, got {item[0]}")',
    "            status = decode_status(item[2])",
    "            if status == -2:",
    '                raise WorkerBusy("the worker has no free batch slot")',
    "            if status != 0:",
    '                raise WorkerRejected(f"engine rejected the request: status {status}")',
    "            self.last_frame_at = time.monotonic()",
    "",
    "            while True:",
    "                wait = timeout_s",
    "                if silence_s > 0:",
    "                    wait = min(",
    "                        timeout_s, max(0.1, silence_s - (time.monotonic() - self.last_frame_at))",
    "                    )",
    "                try:",
    "                    tag, token_id, frame_payload = frames.get(timeout=wait)",
    "                except queue.Empty:",
    "                    self.cancel(request_id)",
    '                    raise StreamStalled(f"no frame for {wait}s") from None',
    "                if tag is None:",
    '                    raise WorkerUnreachable("worker died mid-stream")',
    "                self.last_frame_at = time.monotonic()",
    "                if tag == STREAM_TOKEN:",
    "                    self.note_frame()",
    "                    if token_id >= 0:",
    "                        reused = frame_payload if isinstance(frame_payload, int) else 0",
    "                        yield (STREAM_TOKEN, token_id, {\"prompt_reused\": reused})",
    "                    continue",
    "                if tag == STREAM_TERMINAL:",
    "                    summary = frame_payload if isinstance(frame_payload, dict) else {}",
    "                    self.note_frame(summary)",
    "                    terminal_seen = True",
    "                    yield (STREAM_TERMINAL, -1, summary)",
    "                    return",
    '                raise WorkerUnreachable(f"unexpected frame type {tag} on a stream queue")',
    "        finally:",
    "            if not terminal_seen:",
    "                self.cancel(request_id)",
    "            self.close_stream(request_id)",
    "",
]
s = s[:start] + "\n".join(lines) + s[end:]

old_gen = "            for token_id, _reused, summary in self.stream("
assert s.count(old_gen) == 1, "generate anchor"
s = s.replace(
    "            for token_id, _reused, summary in self.stream(",
    "            for msg_type, token_id, metrics in self.stream(",
)
s = s.replace(
    "                if token_id < 0:\n                    self.last_summary = summary\n                    return",
    "                if msg_type == STREAM_TERMINAL:\n                    self.last_summary = metrics\n                    return",
)

p.write_text(s)
print("supervisor rewritten")
