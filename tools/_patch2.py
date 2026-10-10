#!/usr/bin/env python3
"""Fix the cancel-on-never-accepted case, add config validation to the fixture."""
import pathlib

# --- supervisor: only cancel a request the worker actually accepted ---
p = pathlib.Path("/home/ai-user0/HyperCore/serve/hypercore_supervisor.py")
s = p.read_text()
s = s.replace(
    "        frames = self.open_stream(request_id)\n        terminal_seen = False\n",
    "        frames = self.open_stream(request_id)\n        terminal_seen = False\n        accepted = False\n",
    1,
)
s = s.replace(
    "            if status != 0:\n                raise WorkerRejected(f\"engine rejected the request: status {status}\")\n",
    "            if status != 0:\n                raise WorkerRejected(f\"engine rejected the request: status {status}\")\n            accepted = True\n",
    1,
)
s = s.replace(
    "        finally:\n            if not terminal_seen:\n                self.cancel(request_id)\n            self.close_stream(request_id)",
    "        finally:\n            # A request the worker never accepted has no slot to reclaim;\n            # a stalled or abandoned one does.\n            if accepted and not terminal_seen:\n                self.cancel(request_id)\n            self.close_stream(request_id)",
    1,
)
p.write_text(s)

# --- ipc_parser: a config decoder so the mock can validate like the engine ---
q = pathlib.Path("/home/ai-user0/HyperCore/serve/ipc_parser.py")
t = q.read_text()
anchor = "def build_submit_payload("
addition = '''def decode_config(payload: bytes) -> dict[str, float | int]:
    """Read the request config out of a submit payload.

    Returns {} when the payload is too short to hold one - a caller that wants to
    reject a malformed frame decides that, this function just reports.
    """
    if len(payload) < CFG.size:
        return {}
    struct_size, temperature, top_p, top_k, max_new_tokens, pcie_frac, spec_min_p = CFG.unpack(payload[:CFG.size])
    return {
        "struct_size": struct_size,
        "temperature": temperature,
        "top_p": top_p,
        "top_k": top_k,
        "max_new_tokens": max_new_tokens,
        "pcie_frac": pcie_frac,
        "spec_min_p": spec_min_p,
    }


'''
t = t.replace(anchor, addition + anchor, 1)
q.write_text(t)

# --- fixture: validate the config the way the engine does ---
f = pathlib.Path("/home/ai-user0/HyperCore/serve/frame_fixture.py")
u = f.read_text()
u = u.replace(
    "    RESP_STATUS,\n    decode_header,\n)",
    "    RESP_STATUS,\n    decode_config,\n    decode_header,\n)",
    1,
)
old = '''    def _handle_submit(self, request_id: int, payload: bytes) -> None:'''
i = u.index(old)
snippet = u[i:i + 400]
print(snippet)
