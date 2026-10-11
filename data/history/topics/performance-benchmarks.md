# Performance and benchmarks

Accumulated from 2 transcripts, 3 entries. Built 2026-10-11. Newer chats append here; within a section the entries are grouped by the thing they are about, newest statement first.


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


## Measured on this machine

numbers actually measured, not estimated


**cal**
- `~/.config/hypercore/settings.json` already holds a calibration for this exact PC and model (`RTX 4090|24GB|i9-14900KF|31GB|qwen3.8-flash-next-q2_0|262144|text`, 2026-10-05, 141.6 tok/s), so `cal` is not `None` and setup applies the saved settings instead of asking to re-measure.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-13-20.md</sub>

**min_gain tools calibrate**
- `MIN_GAIN = 0.03` (`tools/calibrate.py:39`) is 4.3 tok/s at 142, which is only 1.5 standard errors.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-15-51.md</sub>

**standard error median**
- The standard error of a median-of-3 is 2.43 tok/s (exact `sqrt(0.374)·σ`; 2.65 by 20000-sample simulation), not 2.9.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-15-51.md · also in hypercore-chat-2026-10-11-15-51.md</sub>
