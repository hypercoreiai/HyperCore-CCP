# Memory, VRAM and RAM

Accumulated from 29 transcripts, 80 entries. Built 2026-10-13. Newer chats append here; within a section the entries are grouped by the thing they are about, newest statement first.


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


**--pcie-frac** · 3 chats
- RAM is MemTotal in GiB (31 here), PCIe is the display device's link (16.0 GT/s = gen 4, x16), not the fastest link on the board, which is what actually decides whether a `--pcie-frac` result transfers.
  <sub>2026-10-12 · hypercore-chat-2026-10-12-17-13.md</sub>
- With a page-locked copy the GPU also takes its usual share of the misses over PCIe (`--pcie-frac`), as with enough RAM; `--pcie-frac 0` (or `STRATA_RESIDENT_PIN=0`) gives the mapp [showing 8000 of 8001 characters read; the rest is not included.
  <sub>2026-10-04 · strata-chat-2026-10-04-03-57.md · also in strata-chat-2026-10-03-14-03.md</sub>
- the share of the experts missing from VRAM that are copied to the GPU instead of computed by the CPU (`--pcie-frac`: a fast PCIe link and a slower CPU want more, a laptop's narrower link less);
  <sub>2026-10-03 · strata-chat-2026-10-03-14-03.md</sub>

**--adapt-swaps** · 2 chats
- `--pcie-frac 0.00` + `--resident-experts` + `--adapt-swaps` — docs DETAILS.md line ~95-100 explicitly: "Through the server, two more things carry over from one request to the next (#410): the adaptive tier moves experts between RAM and VRAM (the GPU and the CPU round an expert differently), and the prompt cache resumes a repeated prompt and reads only its tail through the decode path.
  <sub>2026-10-13 · strata-chat-2026-10-13-21-31.md</sub>
- For the requests that produced token soup: `--prompt-cache` is at its default 6 (`src/program/generate.cpp:592`) and `--adapt-swaps` at 96 (`:588`).
  <sub>2026-10-13 · strata-chat-2026-10-13-21-31.md</sub>

**--vram-reserve-mib** · 2 chats
- `svc.config_path` and the engine `args` are read at startup, and `ensure_loaded()` reuses that args list — so a `/v1/unload` + `/v1/load` cycle will not pick up `--vram-reserve-mib`.
  <sub>unknown · context.txt</sub>
- The only bridge is `("arg", "--flag")` in the `EDITABLE` spec — currently just `--vram-reserve-mib`.
  <sub>2026-10-09 · strata-chat-2026-10-09-08-03.md</sub>

**break** · 2 chats
- If capped (`STRATA_ARENA_PIN_GIB=N`, multi-GPU under WDDM, remote experts) or refused: `for (i = 0; i + 1 < bounds.size(); ++i)` — arena order, `break` at the first refusal.
  <sub>2026-10-10 · hypercore-chat-2026-10-10-18-06.md</sub>
- `src/core/pinned.cu:356–483` — registration loop walks the explicit heat order first, then the remaining slices in arena order; cap overflow `continue`s, driver refusal `break`s; tail lock is per-slice when an order is supplied.
  <sub>2026-10-10 · hypercore-chat-2026-10-10-17-15.md</sub>

**hypercore_arena_pin_gib** · 2 chats
- This is a deliberate design decision, stated in the source: The engine manages residency per layer with `MADV_WILLNEED` / `MADV_DONTNEED`, and there is already a selective pinning mechanism (`PinnedArena`, `HYPERCORE_ARENA_PIN_GIB`).
  <sub>2026-10-10 · hypercore-chat-2026-10-10-16-40.md</sub>
- Pin the hot slices, not the address space. Use the existing `PinnedArena` / `HYPERCORE_ARENA_PIN_GIB` path, sized to the working set, rather than `mlockall`.
  <sub>2026-10-10 · hypercore-chat-2026-10-10-16-40.md</sub>

**streaming engine more** · 2 chats
- When the engine exited at boot (your trial 1: `vram=512, kv=fp16, pcie=0.33` at 131072 context is a plausible MTP/VRAM boot failure), Python flushed that buffer during GC and printed `Exception ignored while finalizing file <_io.TextIOWrapper name=5>`.
  <sub>2026-10-12 · hypercore-chat-2026-10-12-14-31.md</sub>
- KV streaming (engine 0.1.5): at 64K and more, setup keeps the context's KV cache in RAM and only the part the attention reads in VRAM (`--kv-resident 32768`), so more experts fit on the GPU.
  <sub>2026-10-03 · strata-chat-2026-10-03-14-03.md</sub>

**--adapt-every**
- The cache still follows the conversation (`--adapt-every`): a swap copies the evicted expert back from VRAM into the RAM place of the one that replaces it, so the RAM copy keeps holding exactly what the GPU does not.
  <sub>2026-10-03 · strata-chat-2026-10-03-14-03.md</sub>

**--kv-resident**
- KV streaming is not active here (`--kv-resident` is absent; `kv_resident` defaults to 0, all KV in VRAM), and at these sizes it wouldn't matter.
  <sub>2026-10-10 · hypercore-chat-2026-10-10-18-06.md</sub>

**--min-save**
- For every file it copies a keyframe-exact segment (`-c copy`, so the original bits are preserved), then re-encodes that segment with libx265 — the same encoder HandBrake uses — starting at RF 26 and stepping up to RF 30 until the measured byte saving reaches `--min-save`.
  <sub>2026-10-04 · strata-chat-2026-10-04-07-56.md</sub>

**--mmap-experts**
- Then a parity run on the arena path (no `--mmap-experts`) — the `FileExpertSource` path on this node is already fully page-locked, so it won't show a delta; the gain is only measurable in the default arena configuration.
  <sub>2026-10-10 · hypercore-chat-2026-10-10-17-15.md</sub>

**--tail-role-token**
- Compared with Strata's running args, `_hypercore-q2_0.json` is missing `--vram-reserve-mib 512`, has `--pcie-frac 0.75` (the default) instead of the measured `0.00`, `--spec-min-p 0.80` instead of `0.90`, and no `--tail-role-token`.
  <sub>2026-10-10 · strata-chat-2026-10-10-20-47.md</sub>

**.calibrate_progress.log**
- `.calibrate_progress.log` shows: The calibrator starts its own worker while the live server (pid 998337, started 14:04, `--port 8081 --turn-tail-check`) already holds the model, so the second engine cannot get VRAM.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-14-18.md</sub>

**/home/ai-user0/.config/hypercore/settings.json**
- `/home/ai-user0/.config/hypercore/settings.json` (1498 B, modified 14:17:52) — the actual calibration table, keyed by `GPU|VRAM|CPU|RAM|model|context|mode`: The 2026-10-11 entry is the one that matters for your setup.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-15-51.md</sub>

**_hypercore_run-q2_0.sh**
- Next step needs your go-ahead: stop the Strata instance (pid 178995) so the 4090 is free, then re-run `_hypercore_run-q2_0.sh` to see the full READY handshake — or, if you'd rather keep Strata up, I can run the calibration path first so the config gets a VRAM reserve.
  <sub>2026-10-10 · strata-chat-2026-10-10-20-47.md</sub>

**args**
- The server reads the config at start, so the tab's own note says it plainly: "Saved to the run config; used from the next start of the model." Some keys have guards — `lazy_load` is refused if the config has a `vision` block — and `vram_reserve_mib` is written into the `args` list as `--vram-reserve-mib <n>`, not as a top-level key.
  <sub>2026-10-07 · strata-chat-2026-10-07-09-31.md</sub>

**docs/details.md**
- Check the RAM headroom first — at 262K the context is already the memory limit for the larger quants (`docs/DETAILS.md`, speed tables).
  <sub>2026-10-04 · strata-chat-2026-10-04-03-57.md</sub>

**home_of**
- sycl #2014 `resident_stage_swaps`' `home_of` argument (`sycl/src/program/generate.cpp:255` has no such parameter) - needs an Arc build.
  <sub>2026-10-13 · hypercore-chat-2026-10-13-08-16.md</sub>

**hot_layer_order**
- Need maybe maybe include "The C++ test covers `hot_layer_order` and, when a CUDA device is present, `PinnedArena` honors order." Good.
  <sub>2026-10-10 · hypercore-chat-2026-10-10-18-54.md</sub>

**hypercore_bridge.cpp**
- So the correct place to act is not `hypercore_bridge.cpp` with `mlockall`, but the arena registration path in `PinnedArena`.
  <sub>2026-10-10 · hypercore-chat-2026-10-10-18-54.md</sub>

**hypercorerequesthandler**
- Which HTTP entry is production? `serve/server.py` (5,479 lines, `Service`, `HyperCoreRequestHandler` adapter, MCP, VRAM admission) and `serve/hypercore_server.py` (316 lines, clean, 4/4 passing) both exist and both speak the same wire.
  <sub>2026-10-09 · strata-chat-2026-10-09-22-41.md</sub>

**pin_order**
- Potential issue: `PinnedArena` constructor with `register_order` may be called with `pin_order` from profile but if profile is flat, empty.
  <sub>2026-10-10 · hypercore-chat-2026-10-10-18-54.md</sub>

**pinnedarena**
- The `PinnedArena` side of #1 is already in place — I just re-confirmed it:
  <sub>2026-10-10 · hypercore-chat-2026-10-10-17-15.md</sub>

**prompt_read**
- The worker's terminal frame now carries the expert-tier accounting it already computed (`prompt_read`, cache hits/lookups, PCIe offloads, RAM blobs, file blobs) and the caps reply carries the VRAM tier (slots, slots full, cache MiB, cache full MiB, free VRAM, how the host experts are held, prompt chunk).
  <sub>2026-10-11 · hypercore-chat-2026-10-11-08-01.md</sub>

**rank_learned_profile**
- Heat is used only on the GPU side: `read_expert_profile` / `rank_learned_profile` fill the VRAM cache tiers.
  <sub>2026-10-10 · hypercore-chat-2026-10-10-18-06.md</sub>

**reused**
- The request table's `Reused`, `Tok/s` and `VRAM hit rate` columns are populated.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-08-01.md</sub>

**serve/server.py**
- `serve/server.py` — wire the narrator into the one lifecycle entry the server uses: The trigger strings are still valid for this engine: `src/program/generate.cpp:3777` prints `expert arena:`, `:3778` prints `loaded %.2f GiB at %.2f GiB/s`, `:4073` prints `expert cache N slots,`.
  <sub>2026-10-10 · strata-chat-2026-10-10-20-47.md</sub>

**vram**
- `VRAM` is not optional sugar — the server uses it live, so an API that can't express it can't host the server.
  <sub>2026-10-09 · strata-chat-2026-10-09-16-17.md</sub>

## Decisions taken

what was chosen, and why, oldest first


**--batch**
- It is not applied, and no line is printed, when every expert is already in VRAM, with `--batch` slots, or with a peer/helper GPU.
  <sub>2026-10-13 · hypercore-chat-2026-10-13-03-22.md</sub>

**src/core/pinned.cu**
- I widened the magic field and the struct member to 20 bytes in both `src/core/pinned.cu` and `sycl/src/core/pinned.dp.cpp`, keeping the header 4-byte aligned inside the fixed 4096-byte arena header.
  <sub>2026-10-10 · strata-chat-2026-10-10-07-17.md</sub>

## Measured on this machine

numbers actually measured, not estimated


**vram model runtime** · 5 chats
- The 13:27 failure is a VRAM contention failure ("cannot pin 260 MiB, nor place it in VRAM"), consistent with the card being held by another instance at that time.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-15-51.md</sub>
- 3 GB VRAM is tight. `--batch_size 16` OOMs ("tried to allocate 1.15 GiB").
  <sub>2026-10-07 · strata-chat-2026-10-07-17-37.md</sub>
- Its head takes ~180 MiB of VRAM, which the expert cache leaves free for it (0.1.28).
  <sub>2026-10-03 · strata-chat-2026-10-03-14-03.md</sub>
- Your GPU has 24 GB of VRAM, and the model/runtime is using: > 23.8 GB That means the model is using almost all available GPU memory.
  <sub>2026-10-02 · strata-chat-2026-10-02-22-43.md</sub>
- Combined with other model/cache requirements, it explains why VRAM is near 24 GB.
  <sub>2026-10-02 · strata-chat-2026-10-02-22-43.md</sub>

**cudamalloc** · 3 chats
- No model was loaded, no GPU was touched — the 4090 is holding 24,074 of 24,564 MiB and a 4 KB `cudaMalloc` from a second process returns `out of memory`, so throughput is still unmeasured here.
  <sub>2026-10-09 · strata-chat-2026-10-09-18-55.md</sub>
- It produced no numbers: the engine is resident on the 4090 (24,074 of 24,564 MiB, 93% utilisation), and a 4 KB `cudaMalloc` from a second process returned `out of memory`.
  <sub>2026-10-09 · strata-chat-2026-10-09-16-17.md</sub>
- A refactor of an 11k-line driver is exactly the kind of change that would need that same paired-measurement discipline before it's adopted — and I can't run it here: the 4090 is holding 24,074 of 24,564 MiB and a 4 KB `cudaMalloc` from a second process returns `out of memory`.
  <sub>2026-10-09 · strata-chat-2026-10-09-16-17.md</sub>

**mode engine chosen** · 3 chats
- The engine pins 19.34 GiB of experts page-locked in host RAM on a 30 GB box, and takes a 15.57 GiB expert cache on a 24 GB card.
  <sub>2026-10-13 · strata-chat-2026-10-13-21-31.md</sub>
- But the resident mode's own headroom is 4 GiB, and there is essentially none left for the web server, the six MCP processes, and the patched Firefox.
  <sub>2026-10-07 · strata-chat-2026-10-07-09-31.md</sub>
- Low-RAM mode (engine 0.1.26, chosen by setup): normally all of a model's experts are copied into RAM (23-50 GB, pinned) and the GPU holds a copy of the most-used ones.
  <sub>2026-10-03 · strata-chat-2026-10-03-14-03.md</sub>

**--resident-experts** · 2 chats
- And on this node it is moot twice over: the running config uses `--resident-experts` → `FileExpertSource`, whose 19.15 GiB is already fully page-locked and registered (96–98% hit, 1–5% PCIe); and I checked the profile itself — `data/expert-profile.bin` (48×512, all 24,576 pairs ranked) has a layer-heat spread of only 32.5%, and the best heat-ordered prefix beats the arena prefix by 1.99% at k=18.
  <sub>2026-10-10 · hypercore-chat-2026-10-10-18-06.md</sub>
- The Q2_0 arena is 34.0 GB on a 32 GB PC, so setup chose `--resident-experts` — and it's working: the log reports "0 blob reads from the file" and an 87–92% expert hit rate.
  <sub>2026-10-07 · strata-chat-2026-10-07-09-31.md</sub>

**experts real strata** · 2 chats
- So the real mechanism: the config sets `--vram-reserve-mib 512` but the engine warns it needs 831/1024 MiB.
  <sub>2026-10-13 · strata-chat-2026-10-13-21-31.md</sub>
- 12,630 experts / 16.26 GiB is real: Strata log lines 20-21, `expert cache 12630 slots, 16.26 GiB of VRAM`.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-15-51.md</sub>

**hybrid k8v4 cache** · 2 chats
- With `--expert-cache auto` filling 15.94 GiB and resident RAM mode, the VRAM is nearly full → the driver pages GPU memory to system RAM → decode degrades → the model emits garbage/CJK spam/empty.
  <sub>2026-10-13 · strata-chat-2026-10-13-21-31.md</sub>
- Hybrid K8V4 KV cache (engine 0.1.25, optional, PR #120): `--kv k8v4` (`START-HERE.bat --setup --kv k8v4`) keeps the keys at 8 bits and stores the values as rotated 4-bit: 23% less KV memory than 8-bit, so more experts fit in VRAM.
  <sub>2026-10-03 · strata-chat-2026-10-03-14-03.md</sub>

**measured estimated runs** · 2 chats
- Peak measured 2784 / 2998 MiB — it runs, but there is no headroom.
  <sub>2026-10-07 · strata-chat-2026-10-07-17-37.md</sub>
- Not measured - estimated from the runs above (same CPU and 64 GB RAM): the GPU part scaled by memory bandwidth, the CPU part by how many more experts the card's VRAM holds.
  <sub>2026-10-03 · strata-chat-2026-10-03-14-03.md</sub>

**--selftest**
- The full `--selftest` could not be run here: serve (pid 1321629) holds 24,068 MiB and the test aborts at `history regression allocation: out of memory`.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-22-55.md</sub>

**--vram-elastic**
- `--vram-elastic` exists for the GPU side; there are only 377 MiB free on the 4090.
  <sub>2026-10-07 · strata-chat-2026-10-07-09-31.md</sub>

**--vram-reserve-mib**
- Set `--vram-reserve-mib`. It's unset, so the engine default of 700 MiB applies, and only 377 MiB is actually free.
  <sub>2026-10-07 · strata-chat-2026-10-07-09-31.md</sub>

**adaptive swap tier**
- The adaptive swap tier moved ~320 MiB of experts into RAM to compensate, so nothing is being read from the SSD.
  <sub>unknown · context.txt</sub>

**also tuning failed**
- This is also why `Tuning: FAILED` said "the draft head does not fit: needs 178 MiB of VRAM and 170 MiB is free" — the MTP head competes for the same held-back pool.
  <sub>2026-10-10 · strata-chat-2026-10-10-20-47.md</sub>

**cudahostalloc**
- `src/core/native_head.cpp:150` fails when both `cudaHostAlloc` (mapped pinned — which also needs device mapping) and the `cudaMalloc` fallback cannot get 260 MiB, and that error is fatal to init (`worker_main.cpp:277` → `-5`).
  <sub>2026-10-10 · strata-chat-2026-10-10-20-47.md</sub>

**cudahostregister**
- The test asserts the real profile is rejected: The registration half of the test exits 77 (skipped) because the live server holds 23.9 GiB of the 24.5 GiB GPU — `cudaHostRegister` of even 1 MiB is refused.
  <sub>2026-10-10 · hypercore-chat-2026-10-10-18-06.md</sub>

**hypercore-q2_0.json**
- `hypercore-q2_0.json` was written with `--vram-reserve-mib 700`, from: The BF16 mmproj alone is 907,524,736 B = 865 MiB of tensors, plus the encoder's own CUDA context and its work buffers.
  <sub>2026-10-10 · strata-chat-2026-10-10-20-47.md</sub>

**hypercore-q2_0.log**
- So the engine is doing the work — `hypercore-q2_0.log` has `FileExpertSource: allocating 19.15 GiB page-locked cache complement … 12241 in the GPU cache` — the window just says nothing for those minutes.
  <sub>2026-10-10 · strata-chat-2026-10-10-20-47.md</sub>

**mlock**
- `src/platform/memory_test.cpp` failed because `RLIMIT_MEMLOCK` here is 8 MiB and the test demanded a 256 MiB `mlock`.
  <sub>2026-10-13 · hypercore-chat-2026-10-13-00-06.md</sub>

**page locked expert**
- RAM, not GPU. 20.7 GiB is page-locked for the expert arena and the process RSS is 24.5 GB of 32 GB.
  <sub>2026-10-07 · strata-chat-2026-10-07-09-31.md</sub>

**py_compile**
- `py_compile` clean on all seven edited files, `sh -n` clean on both scripts To see it live, the process needs to reload the source: I didn't do that myself — it stops the running chat and reloads the model (minutes of weight loading, ~24 GB of VRAM).
  <sub>2026-10-10 · strata-chat-2026-10-10-19-47.md</sub>

**qwen/qwen2.5-1.5b-instruct**
- Constraint found: the GPU is fully held by the Strata engine (PID 71501, 23.5 / 24.5 GiB), so `Qwen/Qwen2.5-1.5B-Instruct` OOM'd on CUDA → the benchmark ran on CPU.
  <sub>2026-10-07 · strata-chat-2026-10-07-17-37.md</sub>

**same headroom failure**
- That is the same headroom failure that killed the calibration worker ("cannot pin 260 MiB, nor place it in VRAM").
  <sub>2026-10-13 · strata-chat-2026-10-13-21-31.md</sub>

**serve**
- It compiled (`cmake --build build --target ple_parity`, exit 0), but running it directly hits `history regression allocation: out of memory` at `src/kernels/ple_parity.cpp:195` while `serve` holds 24084 of 24564 MiB.
  <sub>2026-10-12 · hypercore-chat-2026-10-12-07-50.md</sub>

**start here setup**
- `START-HERE.bat --setup --draft-vocab en` keeps the English/code subset from before (40,525 ids, ~110 MiB less VRAM, English answers 1-2% faster; CJK answers get almost no drafts).
  <sub>2026-10-03 · strata-chat-2026-10-03-14-03.md</sub>

**strata_models**
- Consider the model setup.py recommends. `strata_models` says Coder IQ1_M at 128K is the fastest that fits here (23.4 GB arena → fully resident), while Q2_0 "fits in the low-RAM mode (slower: the GPU holds part of the experts)".
  <sub>2026-10-07 · strata-chat-2026-10-07-09-31.md</sub>

**what ramp made**
- What the ramp is made of, from the log: the VRAM expert tier fills across the session (38,435 → 51,309 exchanges with the tier), and draft acceptance rises from 86–94% on short requests to 97% on long ones.
  <sub>2026-10-10 · hypercore-chat-2026-10-10-18-06.md</sub>

## Gotchas

things that bit once and will bite again


**vram 1024 point** · 2 chats
- And "193 MiB of VRAM free with everything loaded - LOW: requests may stall" and "WARNING: only 51 MiB of VRAM free at the start of this request (below 512 MiB): when the card is this full the driver can page GPU memory to system RAM, decode falls to a few tok/s and a window may never finish (#2065)".
  <sub>2026-10-13 · strata-chat-2026-10-13-21-31.md</sub>
- a `vram=1024` point when you run `--vram-max 512`) is skipped and counted, never clamped.
  <sub>2026-10-12 · hypercore-chat-2026-10-12-17-13.md</sub>

**--conversation-cache-mib**
- Don't add `--conversation-cache-mib` yet. It defaults to 0, and `--conversation-cache-min-free-mib` (default 2560) would refuse to park anything with 4.4 GiB available.
  <sub>2026-10-07 · strata-chat-2026-10-07-09-31.md</sub>

**docs details already**
- docs/DETAILS.md already says "~1.4 GB of VRAM is kept free for it" — setup just never reserved that much.
  <sub>2026-10-10 · strata-chat-2026-10-10-20-47.md</sub>

**expert cache rate**
- Expert cache hit rate 87–92% on a 512-expert MoE: 11,022 slots (14.5 GiB) in VRAM plus 20.72 GiB of experts page-locked in RAM, and the log says "0 blob reads from the file" — the SSD is never touched during decode.
  <sub>2026-10-07 · strata-chat-2026-10-07-09-31.md</sub>

**rank_learned_profile**
- The one missing link is the call site. `src/core/expert_source.cpp:3287-3288` still constructs `PinnedArena(want + blob, bounds, max_pinned_bytes, ...)` with no order argument, so the heat ranking from `read_expert_profile` / `rank_learned_profile` in `src/core/expert_cache.cpp` never reaches the arena.
  <sub>2026-10-10 · hypercore-chat-2026-10-10-17-15.md</sub>

**strata_resident_headroom_gib**
- The engine leaves 4 GB of the RAM it finds free (`STRATA_RESIDENT_HEADROOM_GIB`); when even the experts the GPU does not hold do not fit, it says so and runs the plain mapped mode.
  <sub>2026-10-03 · strata-chat-2026-10-03-14-03.md</sub>
