# Engine internals

Accumulated from 22 transcripts, 67 entries. Built 2026-10-13. Newer chats append here; within a section the entries are grouped by the thing they are about, newest statement first.


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
from `prompt_read` - the tokens actually read - not from the whole prompt, so a cached 88k-token
prefix does not make the rate look wrong.

**Three 0.1.42 features are off by default.** `HYPERCORE_MMVQ_IL` (the interleaved small-batch matvec,
`src/core/verify.cpp:Verifier::mmvq_il_on`), `HYPERCORE_NAN_GUARD` (the per-window head-logits check,
`src/core/verify.cpp:Verifier::nan_guard_on`) and `HYPERCORE_ADAPT_OVERLAP` (the adaptive tier's overlapping
copies, `src/program/generate.cpp:adapt_overlap`) each add work to every decode window. They were on by default in
0.1.42; on 2026-10-13 all three were flipped to opt-in after an install that ran slow and produced broken thinking
blocks. The A/B that proves the link has not been run yet: the card was fully held by the other server, so the
rebuilt engine was never started on a free GPU.


## What is true now

how the thing works, as the chats established it


**prefill_ms** · 5 chats
- For "tracks token latency drops and stalls" to be a real alert, either the summary needs a `prefill_ms` field, or the supervisor computes total from ack→terminal wall clock.
  <sub>2026-10-09 · strata-chat-2026-10-09-22-41.md</sub>
- Your decomposition says `prefill_ms` isolates compute, `ttft_ms` is hold + prefill, and a congested node spikes TTFT while prefill stays normal.
  <sub>2026-10-09 · strata-chat-2026-10-09-22-41.md</sub>
- In the code as it stands, that second half is false: `prefill_ms` is the hold.
  <sub>2026-10-09 · strata-chat-2026-10-09-22-41.md</sub>
- In the stub, `ttft_ms == prefill_ms` exactly — 45 and 45 in the wire_test output — and `ttft - prefill` is always 0.
  <sub>2026-10-09 · strata-chat-2026-10-09-22-41.md</sub>
- That costs a field, and byte 36 is now TTFT, so it means either a 44-byte summary (which the prefix rule already tolerates) or redefining `prefill_ms` to start at the scheduling point.
  <sub>2026-10-09 · strata-chat-2026-10-09-22-41.md</sub>

**--batch-mtp** · 2 chats
- The two paths `include/strata/program/batch_groups.hpp` is the whole decision, and it is pure (no GPU, no env): Why they conflict. With a layer split, `--batch-mtp`'s slot drafters live on the last stage's GPU, and the windows are two rows per slot pushed through every stage.
  <sub>2026-10-13 · hypercore-chat-2026-10-13-03-22.md</sub>
- The 0.1.43 behaviour your changelog describes, where `--batch-mtp` actually runs on a layer split, needs the slot-drafter support from Strata commit `48f2c47d` (`include/strata/core/batch_rows.hpp` plus the `verify.cpp` `stage_batch` layout rules) ported first.
  <sub>2026-10-13 · hypercore-chat-2026-10-13-03-22.md</sub>

**decode_ms** · 2 chats
- After the split, the slot hold is `prefill_ms` and `decode_ms` is only the emit window.
  <sub>2026-10-09 · strata-chat-2026-10-09-22-41.md</sub>
- If suffix-draft verification is charged to `decode_ms`, then `ttft - prefill` is the gate plus the first draft attempt — not purely the gate.
  <sub>2026-10-09 · strata-chat-2026-10-09-22-41.md</sub>

**pcie_frac** · 2 chats
- Does the request config carry `pcie_frac` / `spec_min_p`? Without them the pcie sweep becomes five engine re-inits instead of one — five model loads.
  <sub>2026-10-09 · strata-chat-2026-10-09-18-55.md</sub>
- The "tune" surface is deliberately tiny. Three knobs (`pcie_frac`, `spec_min_p`, `pool_workers`) are calibrated because they are the three that actually move tok/s; the 357 env vars are mostly A/B switches used by the parity and bench harness, not user-facing tuning.
  <sub>2026-10-09 · strata-chat-2026-10-09-08-03.md</sub>

**test hard codes** · 2 chats
- The test intent is excellent: ABI alignment as a build dependency (`add_dependencies(hypercore-worker hypercore_abi_alignment_check)`) is a strong idea — a build that succeeds has already proven the header, the Python mirrors and the frame writer agree.
  <sub>2026-10-10 · strata-chat-2026-10-10-03-30.md</sub>
- A test that hard-codes a default fails the moment the environment layer is exercised. The first run asserted `workers == -1` for the defaults case; run with `STRATA_POOL_WORKERS=7`, the env layer correctly overrode it and the test failed.
  <sub>2026-10-09 · strata-chat-2026-10-09-18-55.md</sub>

**--context**
- If you genuinely need a bigger window, re-run setup with a larger `--context`; 262,144 is the model's trained ceiling, so anything above it needs rope scaling, which setup derives for you (`START-HERE.bat --setup --context 393216` picks yarn and the factor).
  <sub>2026-10-04 · strata-chat-2026-10-04-03-57.md</sub>

**--gen**
- What is in place Usage `--gen` maximises generation tok/s, `--prefill` maximises prompt tok/s, `--latency` minimises `prompt_ms + decode_ms`; all three are mapped to one maximisation score so a failed boot lands at the bottom of the range.
  <sub>2026-10-12 · hypercore-chat-2026-10-12-14-31.md</sub>

**/health**
- Live: `python3 -m serve.hypercore_server --port 8125 --worker build-shared/hypercore-worker --socket /tmp/hc3.sock --config '{"batch":2}'` → `/health` 200, a 20-token completion streams and logs `[MONITOR] … decode_ms=39 tokens=20 drafts=20/100`, `/slots` returns the populated monitor, a dropped client issues `CMD_CANCEL` and `in_flight` returns to 0.
  <sub>2026-10-09 · strata-chat-2026-10-09-22-41.md</sub>

**/home/ai-user0/black_box/tune/**
- `/home/ai-user0/black_box/tune/` holds `lib.sh` (the shared FIFO + DONE-parsing plumbing), three single-dimension sweeps (`tune_affinity.sh`, `tune_host_core.sh`, `tune_pool_workers.sh`), two production launchers, and `results/` with four CSVs and 20 engine logs.
  <sub>2026-10-12 · hypercore-chat-2026-10-12-11-07.md</sub>

**/metrics**
- Also, while checking I noticed the config passes `--spec 4` but `/metrics` reports `"spec": 6`; the engine is apparently deriving the verify window from the MTP draft head rather than the flag.
  <sub>unknown · context.txt</sub>

**_request_last**
- `prompt_read` / `prefill_ms` are parsed from the terminal summary in `serve/ipc_parser.py` (`derive_monitor_field`), carried through `_request_last` into the request record, and rendered in `serve/web/app.js`.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-11-46.md</sub>

**active_pool_workers**
- What does `active_pool_workers` actually mean? Right now it reports the pool's configured topology count, not the number of requests in flight.
  <sub>2026-10-09 · strata-chat-2026-10-09-18-55.md</sub>

**batch**
- Where does instance-level config live? `batch`, `max_context`, `pool_workers` are set at `init` via argv; there is no frame to change them at runtime.
  <sub>2026-10-09 · strata-chat-2026-10-09-18-55.md</sub>

**because queue_hold_ms ttft_ms**
- Because queue_hold_ms = ttft_ms - prefill_ms is a simple subtraction, computing it inside ipc_parser.py is straightforward.
  <sub>2026-10-09 · strata-chat-2026-10-09-22-41.md</sub>

**build-cuda/libhypercore_api.so.0.1.40**
- truncated: the page has more text; the first 12,000 characters are shown] abi busy precedence summary pool cancel resolve worker_mode → 8/8 PASS ``` `build-cuda/libhypercore_api.so.0.1.40` links `libcublas.so.13`, `libcudart.so.13`, `libcublasLt.so.13`; glibc floor still 2.38.
  <sub>2026-10-10 · hypercore-chat-2026-10-10-11-52.md</sub>

**caps_size.c**
- The 12 C boundary tests compiled and ran from the copy: abi, busy, cancel, caps_size, config, pool, precedence, resolve, summary, worker_mode green (`caps_size.c` prints sizes only — it reports 28/28/40 and is not a pass/fail test; `probe.c` and `dbg_mode.c` are helpers).
  <sub>2026-10-10 · strata-chat-2026-10-10-03-30.md</sub>

**computed exactly place**
- It is computed in exactly one place (`serve/ipc_parser.py::derive_monitor_field`); emitting it from the worker would grow the frozen 40-byte summary and add a third number that has to agree with two measured ones.
  <sub>2026-10-10 · strata-chat-2026-10-10-00-02.md</sub>

**decode_tok_s**
- Monitor fields. `drafts_offered`, `drafts_accepted`, `decode_tok_s`, `panic` are read at `serve/server.py:2421-2514` and by `serve/engine_bridge.py` — load-bearing, so `MONITOR_FIELDS` in `serve/ipc_parser.py` stays as the single mapping.
  <sub>2026-10-09 · strata-chat-2026-10-09-22-41.md</sub>

**done**
- Where is the summary? `DONE` at `generate.cpp:9945` carries produced count, decode ms, stop reason, drafts accepted/offered, RAM reads, offloaded, window count.
  <sub>2026-10-09 · strata-chat-2026-10-09-18-55.md</sub>

**draft layer accepted**
- MTP draft layer accepted 298/332 drafts in my request; `--spec 6` with suffix drafts is doing real work.
  <sub>2026-10-07 · strata-chat-2026-10-07-09-31.md</sub>

**example consumer sends**
- For example, if a consumer sends top_k = 128, it returns STRATA_STATUS_INVALID_ARG immediately rather than bubbling down to src/kernels/sampler.cu and causing an abrupt std::exit().
  <sub>2026-10-09 · strata-chat-2026-10-09-18-55.md</sub>

**ggml-common.h**
- Actual ggml surface used is tiny and specific: 16 source/header files include `ggml.h`, `ggml-cpu.h`, or `ggml-common.h`, concentrated in `src/kernels/cpu/{iq_avx2,iq_avx512,kq_avx2,native_expert}.cpp`, `src/kernels/cuda/iq_kernels.cu`, `src/prefill/moe_fused_iq.cu`, and `src/core/mtp.cpp`.
  <sub>2026-10-09 · strata-chat-2026-10-09-08-03.md</sub>

**hypercore-worker**
- CMake gating — `hypercore_abi_alignment_check` is now a dependency of `hypercore-worker` as well as `hypercore_api`.
  <sub>2026-10-10 · strata-chat-2026-10-10-00-02.md</sub>

**hypercore_caps_t**
- `hypercore_caps_t` is now 28 bytes with `instance_pcie_frac` / `instance_spec_min_p`.
  <sub>2026-10-09 · strata-chat-2026-10-09-22-41.md</sub>

**hypercore_engine_init**
- Should the worker's config be per-instance or per-request? `hypercore_engine_init` takes the JSON config; per-request `pcie_frac`/`spec_min_p` already travel in the request struct.
  <sub>2026-10-09 · strata-chat-2026-10-09-18-55.md</sub>

**hypercorerequesthandler**
- `tools/calibrate.py` now builds the engine the server actually runs — the IPC worker — via a new `worker_engine()` that mirrors `serve/server.py`'s construction (supervisor + `HyperCoreRequestHandler`), with `transport=` injectable so the tests need no GPU or model pack.
  <sub>2026-10-10 · strata-chat-2026-10-10-12-04.md</sub>

**hypercorerequesthandler.info**
- `serve/server.py`'s `HyperCoreRequestHandler.info` now reports the instance's `pcie_frac` / `spec_min_p` / `pool_workers` from the worker's CAPS reply, so the sweep tunes against the baseline it is really running rather than the product defaults.
  <sub>2026-10-10 · strata-chat-2026-10-10-12-04.md</sub>

**ipc_parser**
- Is `queue_hold_ms` derived in Python or emitted by the worker? Derived keeps the wire at 40 bytes but puts the arithmetic in the dashboard layer, where a reader that doesn't use `ipc_parser` can't see it.
  <sub>2026-10-09 · strata-chat-2026-10-09-22-41.md</sub>

**max_batch_slots**
- Does the boundary report pool size, or does `STRATA_POOL_WORKERS` go away? I'd rather report it than drop it — the adapter needs `max_batch_slots` to size its concurrency, and right now it can't ask.
  <sub>2026-10-09 · strata-chat-2026-10-09-18-55.md</sub>

**monitor_fields**
- Is `prefill_ms` the Monitor's `prompt_ms`? `MONITOR_FIELDS` currently maps `engine.prompt_ms → prompt_ms`.
  <sub>2026-10-09 · strata-chat-2026-10-09-22-41.md</sub>

**pool_workers**
- Also: `strata_caps_t` no longer reports `pool_workers`, so `STRATA_POOL_WORKERS` is parsed by the bridge and then unobservable — a setting you can set but not read.
  <sub>2026-10-09 · strata-chat-2026-10-09-18-55.md</sub>

**prompt_read**
- The worker's terminal frame now carries the expert-tier accounting it already computed (`prompt_read`, cache hits/lookups, PCIe offloads, RAM blobs, file blobs) and the caps reply carries the VRAM tier (slots, slots full, cache MiB, cache full MiB, free VRAM, how the host experts are held, prompt chunk).
  <sub>2026-10-11 · hypercore-chat-2026-10-11-08-01.md</sub>

**reused**
- Native build check: Result: passed, including the ABI alignment check: So the Monitor tab’s `Reused`, `Tok/s`, and `VRAM Hit Rate` columns are no longer empty placeholders; they are fed from the worker terminal frame and rendered by the web app.
  <sub>2026-10-10 · hypercore-chat-2026-10-10-19-47.md</sub>

**serve/test_abi_contract.py**
- `serve/test_abi_contract.py` proves the lock isn't vacuous — it edits the real header (insert above `top_k`, delete `top_p`, widen `top_k` to `uint64_t`) and asserts the checker fails.
  <sub>2026-10-10 · strata-chat-2026-10-10-00-02.md</sub>

**silence wall supervisor**
- The silence wall is the supervisor's own (`"engine_silence_s"`, 300 s by default; `0` waits as long as the request needs), measured from the last frame, so a six-figure prompt that takes 31 s to read is not cut off mid-prefill.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-08-01.md</sub>

**spec spec speculative**
- The `--spec 4` / `--spec-min-p 0.90` speculative decoding: the log shows "drafts accepted 0 of 0" on the degenerate turns and the MTP draft vocab includes all CJK tokens (106,299 ids) — the garbling into CJK characters ("该该该", "亚马逊pyramid", " scopes.otify") is exactly the kind of thing the draft layer proposes when the verified model's logits collapse.
  <sub>2026-10-13 · strata-chat-2026-10-13-21-31.md</sub>

**strata**
- Upstream `third_party/llama.cpp/models/ggml-vocab-.gguf` — `strata` there is a vocabulary token inside llama.cpp's own model files, not our naming.
  <sub>2026-10-10 · strata-chat-2026-10-10-07-17.md</sub>

**streaming engine more**
- KV streaming (engine 0.1.5): at 64K and more, setup keeps the context's KV cache in RAM and only the part the attention reads in VRAM (`--kv-resident 32768`), so more experts fit on the GPU.
  <sub>2026-10-03 · strata-chat-2026-10-03-14-03.md</sub>

**text protocol integration**
- The text-protocol integration tests (test_slots.py, test_control_cancel.py, test_fatal_recovery.py) must be rewritten using ipc_parser and binary frame fixtures rather than retired.
  <sub>2026-10-09 · strata-chat-2026-10-09-22-41.md</sub>

**tools/daytona_bridge_test.py**
- Cross-toolchain stage: now green. `tools/daytona_bridge_test.py` ran end-to-end: 8/8 C tests (abi, busy, precedence, summary, pool, cancel, resolve, worker_mode) compiled and ran on a foreign glibc 2.41 host against the artifact built here.
  <sub>2026-10-10 · hypercore-chat-2026-10-10-11-52.md · also in 2026-10-10-hypercore-chat-2026-10-10-11-52.md</sub>

**vision_start_reason**
- `log.tell()` on a handle opened in append mode is 0 until it is written to, so `vision_start_reason` read the whole log and returned its last line — the engine's `hypercore serve: mtp: the draft head does not fit` from setup's tuning run.
  <sub>2026-10-10 · strata-chat-2026-10-10-20-47.md</sub>

**worker builds frame**
- The worker builds the frame in a buffer and issues one `write()`; the test runs four concurrent streams and checks every stream gets all its tokens and exactly one terminal frame.
  <sub>2026-10-09 · strata-chat-2026-10-09-18-55.md</sub>

## Decisions taken

what was chosen, and why, oldest first


**--batch-mtp**
- What was added Verified in this session One thing you should know before using it `black_box` at 0.1.42 still refuses `--batch-mtp` on any layer split (`generate.cpp:3601`, "it is for one GPU (no layer split or helper) for now").
  <sub>2026-10-13 · hypercore-chat-2026-10-13-03-22.md</sub>

**decode_ms**
- Decision 1 — the premise was already violated in code, so I fixed the code, not the doc. `include/hypercore/hypercore_api.h` claimed `decode_ms` "includes draft verification latency", but `src/interface/hypercore_bridge.cpp` measured it from the first token callback.
  <sub>2026-10-09 · strata-chat-2026-10-09-22-41.md</sub>

**ipc_parser.py**
- Is the terminal frame a memcpy of the C struct, or a separately declared packed layout? I'd make it explicit and keep `struct_size` as the version tag — but that means `worker_main.cpp` and `ipc_parser.py` share one table that must be edited together.
  <sub>2026-10-09 · strata-chat-2026-10-09-22-41.md</sub>

**niko1221/strata**
- It is not a toy project — it's a full handoff mirror of "HyperCore" (the renamed Strata engine, GitHub `Niko1221/Strata`), rsync'd on 2026‑10‑10 to freeze the boundary surface (public C API + worker + IPC framing + supervisor) for review.
  <sub>2026-10-10 · strata-chat-2026-10-10-07-17.md</sub>

**prefill_ms**
- Is TTFT meant to include the hold? As implemented it starts at request acceptance, so it overlaps `prefill_ms` completely.
  <sub>2026-10-09 · strata-chat-2026-10-09-22-41.md</sub>

**prompt_reused**
- The Monitor path is now connected end to end: The populated fields include: I also found and fixed a real bridge bug: the terminal frame was discarding `prompt_reused`.
  <sub>2026-10-10 · hypercore-chat-2026-10-10-19-47.md</sub>

**resp_caps**
- The bridge fills them from the already-resolved Level-1 options; the worker's `RESP_CAPS` payload is 28 bytes; `ipc_parser.decode_caps()` returns them; the supervisor mirrors them on the instance so a handler doesn't re-query.
  <sub>2026-10-09 · strata-chat-2026-10-09-22-41.md</sub>

## Measured on this machine

numbers actually measured, not estimated


**decode_ms** · 2 chats
- That confirms both of your decisions empirically: `prefill_ms` is the slot hold (45 ms = `40 + max_new/2`, and `resolve_test` shows it collapsing to 0 at `pcie_frac=1.0`), and `decode_ms` really is 0 in the stub.
  <sub>2026-10-09 · strata-chat-2026-10-09-22-41.md</sub>
- Now: Tested, not asserted: `test_prompt_timing_does_not_move_with_the_draft_cycle` runs the same request with and without a 150 ms draft cycle and requires `prefill_ms` to stay put while `decode_ms` and `ttft_ms` move.
  <sub>2026-10-09 · strata-chat-2026-10-09-22-41.md</sub>

**empirical test results** · 2 chats
- Engine + boundary + test harness: ~90–95% complete and green — it builds, the ABI contract locks, the supervisor and IPC framing suites pass, and the docs are thorough.
  <sub>2026-10-10 · strata-chat-2026-10-10-07-17.md</sub>
- Your empirical test results (45 ms == 45 ms) expose a serious design flaw: as long as prefill_ms captures the queue sleep, it is tracking gate delays, not core hardware computation.
  <sub>2026-10-09 · strata-chat-2026-10-09-22-41.md</sub>

**/metrics**
- `--expert-cache auto` became 11,015 slots / 14,521 MiB; the About tab's "Speculation" line is computed from the engine's reported `mtp_max`/`spec` (`MTP drafts up to max(mtp_max, spec) - 1`), which reads 6 in `/metrics` even though the flag says `--spec 4`.
  <sub>2026-10-07 · strata-chat-2026-10-07-09-31.md</sub>

**also tuning failed**
- This is also why `Tuning: FAILED` said "the draft head does not fit: needs 178 MiB of VRAM and 170 MiB is free" — the MTP head competes for the same held-back pool.
  <sub>2026-10-10 · strata-chat-2026-10-10-20-47.md</sub>

**guard more experts**
- The guard. If 90% or more of the experts are already in the GPU cache (60% on a HIP layer split), the default is not set and you get the opposite message: `STRATA_ROUTE_TAIL_SKIP is off by default: X% of the experts are in the GPU cache, so few are missed and skipping costs more draft acceptance than it saves`.
  <sub>2026-10-13 · hypercore-chat-2026-10-13-03-22.md</sub>

**verdict give defensible**
- Verdict: I can give a defensible probabilistic forecast, but the honest headline is that the dominant uncertainty is observational, not mechanistic. Forecast under stated pathways. IPCC AR6 gives a likely decline of ~34% (10–43%) by 2100 under high emissions, and explicitly states low confidence in collapse.
  <sub>2026-10-07 · strata-chat-2026-10-07-18-16.md</sub>

**what ramp made**
- What the ramp is made of, from the log: the VRAM expert tier fills across the session (38,435 → 51,309 exchanges with the tier), and draft acceptance rises from 86–94% on short requests to 97% on long ones.
  <sub>2026-10-10 · hypercore-chat-2026-10-10-18-06.md</sub>

## Gotchas

things that bit once and will bite again


**decode_ms**
- Those were empty for every real request, and the cause was in the engine adapter, not the dashboard: Closing the generator at the end-of-turn token means the worker's terminal frame is never read, so `HyperCoreRequestHandler.last` stayed `None` and every column fed from it (`reused`, `prompt_read`, `decode_ms`, `decode_tok_s`, `hit_rate`) rendered as "–".
  <sub>2026-10-11 · hypercore-chat-2026-10-11-11-46.md</sub>
