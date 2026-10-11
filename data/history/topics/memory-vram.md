# Memory, VRAM and RAM

Accumulated from 2 transcripts, 4 entries. Built 2026-10-11. Newer chats append here; within a section the entries are grouped by the thing they are about, newest statement first.


## Current state

Maintained by hand; the builder keeps it in place.

**Three tiers for experts.** VRAM first, then pinned RAM, then the GGUF file. `--resident-experts`
puts a chosen amount of experts in RAM; `--pcie-frac` is the share of the experts missing from
VRAM that are copied to the GPU rather than computed on the CPU — a fast PCIe link and a slower
CPU want more, a laptop's narrower link less. `--adapt-every` keeps the RAM copy following the
conversation: a swap copies the evicted expert back into the RAM place of the one replacing it.

**Pinned memory is a real mechanism, not a hint.** `PinnedArena` and `HYPERCORE_ARENA_PIN_GIB`
pin a bounded region; the engine manages residency per layer with `MADV_WILLNEED` /
`MADV_DONTNEED`. `STRATA_RESIDENT_PIN=0` (or `--pcie-frac 0`) turns the pinned path off.

**KV is the other half of the budget.** Above 64K context, setup keeps the KV cache in RAM and
only the part attention reads in VRAM (`--kv-resident 32768`), which is what lets a larger model
fit. KV precision is chosen by `--kv` (int8 default, q4_0 half the memory, k8v4 hybrid).

**`--vram-reserve-mib` is an engine argument, not a config key.** The web Settings tab writes it
into the `args` list; there is no top-level `vram_reserve_mib`. It is the only setting in the
editable spec that maps to a flag rather than a key.

**Read the numbers, not the assumption.** A request that reports 88,235 of 88,264 tokens reused is
using the conversation cache; one that reads 116,235 of 116,240 is not. The difference is prompt
time, and it is the first thing to check when a turn is slow.


## What is true now

how the thing works, as the chats established it


**.calibrate_progress.log**
- `.calibrate_progress.log` shows: The calibrator starts its own worker while the live server (pid 998337, started 14:04, `--port 8081 --turn-tail-check`) already holds the model, so the second engine cannot get VRAM.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-14-18.md</sub>

**/home/ai-user0/.config/hypercore/settings.json**
- `/home/ai-user0/.config/hypercore/settings.json` (1498 B, modified 14:17:52) — the actual calibration table, keyed by `GPU|VRAM|CPU|RAM|model|context|mode`: The 2026-10-11 entry is the one that matters for your setup.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-15-51.md</sub>

## Measured on this machine

numbers actually measured, not estimated


**experts real strata**
- 12,630 experts / 16.26 GiB is real: Strata log lines 20-21, `expert cache 12630 slots, 16.26 GiB of VRAM`.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-15-51.md</sub>

**failure vram contention**
- The 13:27 failure is a VRAM contention failure ("cannot pin 260 MiB, nor place it in VRAM"), consistent with the card being held by another instance at that time.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-15-51.md</sub>
