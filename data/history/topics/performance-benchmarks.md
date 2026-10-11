# Performance and benchmarks

Accumulated from 13 transcripts, 24 entries. Built 2026-10-11. Newer chats append here; within a section the entries are grouped by the thing they are about, newest statement first.


## Current state

Maintained by hand; the builder keeps it in place.

**Decode.** On the 4090 with the Q2_0 pack, decode runs ~140–150 tok/s on a cold prompt and
higher with the conversation cache warm. Speculative drafts are accepted at 79/82, 9/10 — the
MTP layer is doing real work.

**Prefill.** A 116k-token prompt read from scratch takes ~31 s (≈3.7k tok/s on the first read);
the same window on a subsequent turn reads 29 tokens in 166 ms. Prefill rates reported in the
Monitor range from ~595 to ~905 tok/s depending on how much of the prompt was already cached.

**The worker's own throughput.** Aggregate tokens reaching the host, 4000 tokens per stream,
median of 3: at one stream the worker is slower than the engine — 124k vs 215k tok/s. That gap is
the IPC, not the model.

**Three knobs move tok/s.** `pcie_frac`, `spec_min_p` and `pool_workers` are the ones calibrated;
the other ~357 environment variables are A/B switches used by the parity and bench harness, not
user-facing tuning.

**`STRATA_DEFERRED_REGISTER=1` is opt-in and Windows-only** because it measured about 10% slower
decode.

**A number in a topic file is only as good as the machine it was measured on.** Anything from
another box is marked as such in the entry's provenance.


## What is true now

how the thing works, as the chats established it


**active research frontier** · 2 chats
- Once mlockall is active and memory limits are lifted, execute a fast stress run using your local benchmarking tools: python3 tools/backend_parity.py --repeat 3 1.
  <sub>2026-10-10 · hypercore-chat-2026-10-10-16-40.md</sub>
- The active research frontier is durable memory — hypergraph-based systems such as HGMEM that reason over relationships rather than retrieving passages — and inference-efficient long-context methods such as TTT-E2E, which maintains constant latency at 128k tokens.
  <sub>2026-10-03 · strata-chat-2026-10-03-12-03.md</sub>

**stub ttft_ms prefill_ms** · 2 chats
- In the stub, `ttft_ms == prefill_ms` exactly — 45 and 45 in the wire_test output — and `ttft - prefill` is always 0.
  <sub>2026-10-09 · strata-chat-2026-10-09-22-41.md</sub>
- Because queue_hold_ms = ttft_ms - prefill_ms is a simple subtraction, computing it inside ipc_parser.py is straightforward.
  <sub>2026-10-09 · strata-chat-2026-10-09-22-41.md</sub>

**/home/ai-user0/lm-eval-runs/peer_qwen3_limit10.json**
- To make it an apples-to-apples comparison I then re-ran `Qwen/Qwen3-0.6B` on the peer's 1060 with `--limit 10`, so both of us saw the identical 60 items (100.4 s eval, mirrored to `/home/ai-user0/lm-eval-runs/peer_qwen3_limit10.json`).
  <sub>2026-10-07 · strata-chat-2026-10-07-17-37.md</sub>

**aggregate tokens reaching**
- Aggregate tokens/s reaching the host, 4000 tokens per stream, median of 3: At one stream the worker is slower — 124k vs 215k.
  <sub>2026-10-09 · strata-chat-2026-10-09-18-55.md</sub>

**backend_parity**
- Fix the benchmark, not the engine — `backend_parity` reports total tokens / total time, which is dominated by the ramp.
  <sub>2026-10-10 · hypercore-chat-2026-10-10-18-06.md</sub>

**both symptoms trace**
- Both symptoms trace to the supervisor refactor, not to a missing feature. `grep -cE "calibrat"` → 24 in both `~/Strata/setup.py` and `~/black_box/setup.py`, and the offer block is identical apart from the name: The prompt is emitted after Step 4 (engine + image encoder).
  <sub>2026-10-10 · strata-chat-2026-10-10-20-47.md</sub>

**memory hypergraph based**
- Memory (hypergraph-based systems like HGMEM), long-context efficiency (TTT-E2E, which keeps latency constant at 128k tokens) and self-assessment are the current research frontier.
  <sub>2026-10-03 · strata-chat-2026-10-03-12-03.md</sub>

**pcie_frac**
- The "tune" surface is deliberately tiny. Three knobs (`pcie_frac`, `spec_min_p`, `pool_workers`) are calibrated because they are the three that actually move tok/s; the 357 env vars are mostly A/B switches used by the parity and bench harness, not user-facing tuning.
  <sub>2026-10-09 · strata-chat-2026-10-09-08-03.md</sub>

**src/interface/worker_main.cpp**
- `src/interface/worker_main.cpp` — the failure is now self-diagnosing: `tools/backend_parity.py` / `tools/bench_flood.py` — pid-namespaced paths, matching the pattern `tools/calibrate.py` already used.
  <sub>2026-10-10 · hypercore-chat-2026-10-10-16-40.md</sub>

**warm engine before**
- Warm the engine before the benchmark gate. `backend_parity.py --repeat 3` measures run 1 as a real datapoint; it should discard or pre-warm it, otherwise every CI number is a cold-start number.
  <sub>2026-10-10 · hypercore-chat-2026-10-10-16-40.md</sub>

**what does branch**
- What does the V1 branch report for TTFT? It sets `ttft_ms = 0`, which for a v1 worker that did emit tokens reads as "instantaneous" rather than "not measured".
  <sub>2026-10-09 · strata-chat-2026-10-09-22-41.md</sub>

## Decisions taken

what was chosen, and why, oldest first


**--builds**
- `--builds` would delete `build-shared/hypercore-worker` and `build/libhypercore_api.so`, which `tools/bench_flood.py`, `tools/backend_parity.py`, `tools/native_probe.py` and the calibration I just fixed all read by default.
  <sub>2026-10-10 · strata-chat-2026-10-10-12-04.md</sub>

## Measured on this machine

numbers actually measured, not estimated


**derived figures median** · 2 chats
- The standard error of a median-of-3 is 2.43 tok/s (exact `sqrt(0.374)·σ`; 2.65 by 20000-sample simulation), not 2.9.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-15-51.md · also in hypercore-chat-2026-10-11-15-51.md</sub>
- My log-derived figures (median 155 tok/s decode across 5,773 requests, 142 tok/s on a live 645-token generation) are steady-state numbers from a warmed expert cache and heavy prefix reuse.
  <sub>2026-10-07 · strata-chat-2026-10-07-09-31.md</sub>

**setup calibrate works** · 2 chats
- `MIN_GAIN = 0.03` (`tools/calibrate.py:39`) is 4.3 tok/s at 142, which is only 1.5 standard errors.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-15-51.md</sub>
- `./setup.sh --calibrate` works — the repo's own state record shows a real run on this box (`--pcie-frac 0.75, --spec-min-p 0.30, --pool-workers 12, 2362 tok/s`).
  <sub>2026-10-10 · strata-chat-2026-10-10-20-47.md</sub>

**--resident-experts**
- Right as they are: `--pcie-frac 0.00` (correct — zero file reads), `--expert-cache auto` (15.05 GiB free → 11,022 slots), `--resident-experts`, `--spec-min-p 0.70` (calibrated at 141.6 tok/s).
  <sub>2026-10-07 · strata-chat-2026-10-07-09-31.md</sub>

**cal**
- `~/.config/hypercore/settings.json` already holds a calibration for this exact PC and model (`RTX 4090|24GB|i9-14900KF|31GB|qwen3.8-flash-next-q2_0|262144|text`, 2026-10-05, 141.6 tok/s), so `cal` is not `None` and setup applies the saved settings instead of asking to re-measure.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-13-20.md</sub>

**caveat these production**
- One caveat: these are production numbers from a server that is in active use — another client was running 130k-token prompts while I measured, so treat 142 tok/s as "in real use with contention" and the 155 median as the steady-state figure.
  <sub>2026-10-07 · strata-chat-2026-10-07-09-31.md</sub>

**decode_ms**
- Now: Tested, not asserted: `test_prompt_timing_does_not_move_with_the_draft_cycle` runs the same request with and without a 150 ms draft cycle and requires `prefill_ms` to stay put while `decode_ms` and `ttft_ms` move.
  <sub>2026-10-09 · strata-chat-2026-10-09-22-41.md</sub>

**edge device inference**
- Edge/on-device inference is now production-viable — 7B–8B models run on consumer hardware with sub-50 ms latency and zero per-inference cost, which matters for privacy, latency and sovereignty.
  <sub>2026-10-03 · strata-chat-2026-10-03-12-03.md</sub>

**ranking puts fully**
- Ranking puts a fully resident pack above one that streams its experts from the SSD, which is the distinction setup.py itself documents (UD-Q4_K_XL measures 7–8.5 tokens/s on a 64 GB PC).
  <sub>2026-10-10 · strata-chat-2026-10-10-08-05.md</sub>
