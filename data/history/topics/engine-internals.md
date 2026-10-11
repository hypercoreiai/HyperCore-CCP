# Engine internals

Accumulated from 1 transcripts, 2 entries. Built 2026-10-11. Newer chats append here; within a section the entries are grouped by the thing they are about, newest statement first.


## Current state

Maintained by hand; the builder keeps it in place.

**The engine is HyperCore, not llama.cpp.** `engine/hypercore` is built from this repo's `src/`
with CMake; llama.cpp is only a reference for quant formats and rope types. The server talks to a
`hypercore-worker` process over a Unix socket using a small frame protocol (`CMD_SUBMIT`,
`CMD_CANCEL`, token frames, one terminal frame per request), and the worker in turn drives the
engine process. `serve/hypercore_supervisor.py` owns that lifecycle; `serve/ipc_parser.py` decodes
the wire; `serve/server.py`'s `HyperCoreRequestHandler` is the adapter the `Service` uses.

**The ABI contract is a build step, not a hope.** `include/hypercore/hypercore_api.h` defines the
request and summary structs; `serve/ipc_parser.py` mirrors their sizes and field offsets, and
`tools/test_abi_contract.py` checks the two agree. The worker's summary carries `prompt_reused`,
`produced_tokens`, `prefill_ms`, `decode_ms`, `ttft_ms`, drafts accepted/offered and the stop
reason. When the worker does not report a counter, the Python side derives it rather than leaving
the Monitor blank (`derive_monitor_field`).

**Expert residency is the main memory mechanism.** Experts live in three tiers — VRAM, pinned RAM,
and the GGUF file — with `--resident-experts`, `--pcie-frac` and `--adapt-every` controlling what
stays on the GPU and how the cache follows the conversation. Hit rates are reported per request
("expert cache 90.0% hit"). KV streaming at 64K+ keeps most of the context's KV in RAM and only
the part attention reads in VRAM.

**Speculative decoding is on by default.** `--spec 4` plus the MTP draft layer (`--mtp <path>`)
accepts a large share of drafts; the terminal frame reports `drafts accepted/offered`, which is
what the Monitor's "Reused" and draft columns show.

**Prefill and decode are measured separately.** `prefill_ms` is the engine's own time to read the
prompt; `decode_ms` is the emit window. The Monitor's prefill card is computed from those two and
from `prompt_read` — the tokens actually read — not from the whole prompt, so a cached 88k-token
prefix does not make the rate look wrong.


## What is true now

how the thing works, as the chats established it


**_request_last**
- `prompt_read` / `prefill_ms` are parsed from the terminal summary in `serve/ipc_parser.py` (`derive_monitor_field`), carried through `_request_last` into the request record, and rendered in `serve/web/app.js`.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-11-46.md</sub>

## Gotchas

things that bit once and will bite again


**decode_ms**
- Those were empty for every real request, and the cause was in the engine adapter, not the dashboard: Closing the generator at the end-of-turn token means the worker's terminal frame is never read, so `HyperCoreRequestHandler.last` stayed `None` and every column fed from it (`reused`, `prompt_read`, `decode_ms`, `decode_tok_s`, `hit_rate`) rendered as "–".
  <sub>2026-10-11 · hypercore-chat-2026-10-11-11-46.md</sub>
