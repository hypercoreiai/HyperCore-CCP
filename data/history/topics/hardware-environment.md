# Hardware and environment

Accumulated from 37 transcripts, 93 entries. Built 2026-10-13. Newer chats append here; within a section the entries are grouped by the thing they are about, newest statement first.


## Current state

Maintained by hand; the builder keeps it in place.

**GPU.** An NVIDIA RTX 4090 (24 GB) is the working card; the 5090 and 3090 are the other
architectures the ready-made engine builds cover. `nvidia-smi` numbers the cards, and that is the
number `--gpu` and the run config use. AMD is supported through HIP/ROCm (`--backend hip`),
chosen automatically when there is no usable NVIDIA card; the engine refuses a hipBLASLt version
it has no table for and falls back to plain hipBLAS.

**Engine builds are per-architecture.** A ready-made build exists for RTX 20/30/40/50; if none
fits, setup installs the build tools and compiles for the GPU in the box. AVX-512 is detected and
used for the CPU path where available.

**PCIe matters more than people expect.** `--pcie-frac` is tuned by measuring this box, not by a
default; the measured value on this machine is 0.00, and a config that still carries the 0.75
default is running against a baseline it never measured.

**Firefox is needed for the browser tools.** Without it (or `STRATA_FIREFOX` pointing at a
browser) the browser MCP server reports that it cannot search or scrape. `xvfb` is used for the
headless Playwright path.


## What is true now

how the thing works, as the chats established it


**--pcie-frac** · 5 chats
- The differences that change how the model computes: `--pcie-frac` is the one that matters.
  <sub>2026-10-13 · strata-chat-2026-10-13-21-31.md</sub>
- Your log shows it in action: With no `--pcie-frac`, 18,848 experts per request are copied to the GPU and computed there instead of on the CPU pool.
  <sub>2026-10-13 · strata-chat-2026-10-13-21-31.md</sub>
- RAM is MemTotal in GiB (31 here), PCIe is the display device's link (16.0 GT/s = gen 4, x16), not the fastest link on the board, which is what actually decides whether a `--pcie-frac` result transfers.
  <sub>2026-10-12 · hypercore-chat-2026-10-12-17-13.md</sub>
- With a page-locked copy the GPU also takes its usual share of the misses over PCIe (`--pcie-frac`), as with enough RAM; `--pcie-frac 0` (or `STRATA_RESIDENT_PIN=0`) gives the mapp [showing 8000 of 8001 characters read; the rest is not included.
  <sub>2026-10-04 · strata-chat-2026-10-04-03-57.md · also in strata-chat-2026-10-03-14-03.md</sub>
- the share of the experts missing from VRAM that are copied to the GPU instead of computed by the CPU (`--pcie-frac`: a fast PCIe link and a slower CPU want more, a laptop's narrower link less);
  <sub>2026-10-03 · strata-chat-2026-10-03-14-03.md</sub>

**--adapt-swaps** · 2 chats
- `--pcie-frac 0.00` + `--resident-experts` + `--adapt-swaps` — docs DETAILS.md line ~95-100 explicitly: "Through the server, two more things carry over from one request to the next (#410): the adaptive tier moves experts between RAM and VRAM (the GPU and the CPU round an expert differently), and the prompt cache resumes a repeated prompt and reads only its tail through the decode path.
  <sub>2026-10-13 · strata-chat-2026-10-13-21-31.md</sub>
- So the config's `--pcie-frac 0.00` is already the deterministic arm, but `--prompt-cache` is left at its default 6 and `--adapt-swaps` at 96 — the two switches the docs say you must also set for identical repeats.
  <sub>2026-10-13 · strata-chat-2026-10-13-21-31.md</sub>

**installed engine install** · 2 chats
- When the engine exited at boot (your trial 1: `vram=512, kv=fp16, pcie=0.33` at 131072 context is a plausible MTP/VRAM boot failure), Python flushed that buffer during GC and printed `Exception ignored while finalizing file <_io.TextIOWrapper name=5>`.
  <sub>2026-10-12 · hypercore-chat-2026-10-12-14-31.md</sub>
- I installed the engine on this box — `pip install --break-system-packages invisible-playwright` → wrapper 0.27.0, engine fetched — and the server reached the launch step, which reports: `apt-get install xvfb` timed out against the tool's 90 s cap, so the real-engine path is not yet exercised — the live case skips with that sentence rather than failing.
  <sub>2026-10-07 · strata-chat-2026-10-07-07-26.md</sub>

**session_id hash pcie** · 2 chats
- `pcie-frac 0.00` and `spec-min-p 0.70` are real, in `~/Strata/strata-q2_0.json`.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-15-51.md</sub>
- `session_id = hash((pcie, spec, iteration))` silently loses rows. Python's `hash()` is signed.
  <sub>2026-10-09 · strata-chat-2026-10-09-18-55.md</sub>

**strata** · 2 chats
- HyperCore ran at its defaults, Strata at `pcie-frac 0.00 --spec-min-p 0.70`.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-15-51.md · also in hypercore-chat-2026-10-11-15-51.md</sub>
- What is `strata_shared`'s relationship to the existing `strata` executable? Right now both link the same spine.
  <sub>2026-10-09 · strata-chat-2026-10-09-18-55.md</sub>

**--adapt-decay**
- `tools/calibrate.py` now sweeps `--pcie-frac` up to `1.0`, adds adaptive-tier candidates for `--adapt-every`, `--adapt-swaps`, and `--adapt-decay`, uses longer 512-token answers for the adaptive tier, records `report["adapt"]`, and keeps earlier measurements if a later engine restart fails.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-13-20.md</sub>

**.so**
- Is the SYCL/HIP side expected to implement this contract, or is the `.so` CUDA-only for v1? If the 25-header `sycl/` tree is meant to implement it, the contract needs a capability-negotiation step now — otherwise you ship a C API that is a CUDA wrapper with a neutral name, which is the failure mode your third decision was specifically trying to avoid.
  <sub>2026-10-09 · strata-chat-2026-10-09-18-55.md · also in 2026-10-09-strata-chat-2026-10-09-18-55.md</sub>

**/home/ai-agent/strata**
- `git status` in `/home/ai-agent/Strata` works — no "dubious ownership"
  <sub>2026-10-03 · strata-chat-2026-10-03-18-59.md</sub>

**/home/ai-user0/strata**
- 6 failures are identical in the untouched archive `/home/ai-user0/Strata` (verified side-by-side): `test_download_auth` ×5 (no network/HF token here) and `test_amd_is_not_asked` (`/usr` not writable).
  <sub>2026-10-10 · strata-chat-2026-10-10-05-20.md</sub>

**410**
- Tier 1 as a set-membership check (free, instant), Tier 2 to drop 404/410, Tier 3 with a 15 s timeout, one retry at 60 s — treat `429` as "available, rate-limited" (keep it), `410` as permanently dead, and cold-start timeouts as "unverified" rather than dead.
  <sub>2026-10-09 · strata-chat-2026-10-09-09-50.md</sub>

**active research frontier**
- The active research frontier is durable memory — hypergraph-based systems such as HGMEM that reason over relationships rather than retrieving passages — and inference-efficient long-context methods such as TTT-E2E, which maintains constant latency at 128k tokens.
  <sub>2026-10-03 · strata-chat-2026-10-03-12-03.md</sub>

**ai-user0**
- One ownership note: `README.md` and `docs/media/header_readme.jpg` are owned by `user0`, not `ai-user0`, and `sudo chown` is refused by the sandbox.
  <sub>2026-10-10 · strata-chat-2026-10-10-19-47.md</sub>

**app.js**
- New `serve/test_web_client.py` (8 cases) asserts the shipped `app.js`/`index.html` actually do these things.
  <sub>2026-10-06 · strata-chat-2026-10-06-18-57.md</sub>

**artifact**
- `artifact` and `plan` are leaf modules with no GPU dependency, which is deliberate: `strata_artifact` and `strata_plan` are `INTERFACE` libraries with no CUDA link (`CMakeLists.txt:227, 258`).
  <sub>2026-10-09 · strata-chat-2026-10-09-08-03.md</sub>

**boundary.yml**
- In CI the second half is still correctly gated on `build-cuda/hypercore-worker` existing — a GPU-less runner can't claim it, and `boundary.yml` says so rather than faking it.
  <sub>2026-10-10 · strata-chat-2026-10-10-07-17.md</sub>

**build**
- Build-directory consistency: OK. `build-hip`, `build-sycl`, `build-halo`, `build-cuda12` each have a matching configure line in their own page; the main path uses `build`, as `install.sh` and CI do.
  <sub>2026-10-10 · strata-chat-2026-10-10-19-47.md</sub>

**build-cuda/hypercore-worker**
- This box has an RTX 4090 and `build-cuda/hypercore-worker` is built, so I ran the cross-backend half directly: That is the determinism half and the cross-backend half, both green.
  <sub>2026-10-10 · strata-chat-2026-10-10-07-17.md</sub>

**catalog**
- A set kept beside the server still wins over the shipped one, and with neither the root path is returned so `catalog` reports it as missing rather than guessing.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-11-46.md</sub>

**checkpoint_restore**
- On step 1 specifically: generate.cpp is not one monolith, it's four — CLI parsing (310–860), residency policy (`under_wddm`, `pin_blobs`, `on_rotational_disk`, `probe_pcie_h2d_gbps`, `JobThread`), checkpointing (`checkpoint_save`/`checkpoint_restore`, `load_control_vectors`), and the serve/batch loop.
  <sub>2026-10-09 · strata-chat-2026-10-09-16-17.md</sub>

**core**
- `tests/` is the C++ suite tree (`core`, `cuda`, `hip`, `prefill`); `serve/fixtures/` already exists and already holds test data.
  <sub>2026-10-09 · strata-chat-2026-10-09-22-41.md</sub>

**cublas_v2.h**
- One source tree, three GPU backends. CUDA is the native dialect; AMD is reached by a header shim (`include/strata/hip_compat/`, `include/strata/platform/hip_compat/`) that redefines `cuda_runtime.h`/`cublas_v2.h` onto HIP so "the engine's sources stay one tree" (`include/strata/platform/hip_compat/strata_hip.h:2-6`).
  <sub>2026-10-09 · strata-chat-2026-10-09-08-03.md · also in 2026-10-09-strata-chat-2026-10-09-08-03.md</sub>

**cudahostregister**
- Potential issue: If `cudaHostRegister` fails for a slice due driver refusal, break.
  <sub>2026-10-10 · hypercore-chat-2026-10-10-18-54.md</sub>

**docs/amd_hip_performance.md**
- The `Niko1221/HyperCore` links in `README.md`, `docs/INSTALL.md`, `docs/MCP_SERVER.md`, `docs/STRIX_HALO.md`, and the PR/issue references in `docs/AMD_HIP_PERFORMANCE.md` and `docs/INTEL_ARC.md` are the upstream source of the code, not your project.
  <sub>2026-10-10 · strata-chat-2026-10-10-07-17.md</sub>

**docs/details.md**
- `docs/DETAILS.md` says of this exact path: "the PCIe share of the missed experts (computed on the GPU instead of the CPU) still made the first answer after a start differ from the next ones." And issue #31 is a documented bug in precisely this expert-copy path for the IQ packs ("the experts are now copied by a GPU kernel, `--pcie-mode dma` restores the old way").
  <sub>2026-10-13 · strata-chat-2026-10-13-21-31.md</sub>

**downloads/**
- Permission layer separate from execution — new `serve/tool_permissions.py` Ownership rule, not a path rule: a file this process created, or anything under `scratch/`, `tmp/`, `downloads/`, is free; anything else is refused with a reason and a `force=true` escape hatch.
  <sub>2026-10-05 · strata-chat-2026-10-05-23-07.md</sub>

**expert_multi_test**
- The failure is `expert_multi_test`, which exits with "this CPU cannot run the expert kernel: missing AVX512F/BW/VL/VNNI/VBMI" — a hardware guard on this box, not the rename.
  <sub>2026-10-10 · strata-chat-2026-10-10-07-17.md · also in strata-chat-2026-10-10-07-17.md</sub>

**find_history globs model**
- `find_history()` globs `_<model>_<objective>_<cntx>.json` and keeps only files whose CPU, GPU, RAM and PCIe generation match.
  <sub>2026-10-12 · hypercore-chat-2026-10-12-17-13.md</sub>

**get_caps**
- Does `get_caps` need to report the instance baseline? The supervisor can read `max_batch_slots` and `max_context_len`, but it cannot ask "what pcie_frac is this instance running with".
  <sub>2026-10-09 · strata-chat-2026-10-09-22-41.md</sub>

**ggml-common.h**
- Actual ggml surface used is tiny and specific: 16 source/header files include `ggml.h`, `ggml-cpu.h`, or `ggml-common.h`, concentrated in `src/kernels/cpu/{iq_avx2,iq_avx512,kq_avx2,native_expert}.cpp`, `src/kernels/cuda/iq_kernels.cu`, `src/prefill/moe_fused_iq.cu`, and `src/core/mtp.cpp`.
  <sub>2026-10-09 · strata-chat-2026-10-09-08-03.md</sub>

**hub.collisions**
- A partial read now says what it is a piece of: Registry uniqueness. `McpHub` records namespaced collisions in `hub.collisions`, reported by `status()`; a contracts test asserts the shipped config produces none (36 distinct names).
  <sub>2026-10-05 · strata-chat-2026-10-05-23-07.md</sub>

**hypercore-worker**
- Is `hypercore-worker` part of the shipped artifact? Right now the documented entry point is `libhypercore_api.so`, but the out-of-process worker is the one that survives an engine crash.
  <sub>2026-10-09 · strata-chat-2026-10-09-22-41.md</sub>

**hypercore_caps_t**
- `hypercore_caps_t` is now 28 bytes with `instance_pcie_frac` / `instance_spec_min_p`.
  <sub>2026-10-09 · strata-chat-2026-10-09-22-41.md</sub>

**hypercore_engine_init**
- Should the worker's config be per-instance or per-request? `hypercore_engine_init` takes the JSON config; per-request `pcie_frac`/`spec_min_p` already travel in the request struct.
  <sub>2026-10-09 · strata-chat-2026-10-09-18-55.md</sub>

**hypercorerequesthandler.info**
- `serve/server.py`'s `HyperCoreRequestHandler.info` now reports the instance's `pcie_frac` / `spec_min_p` / `pool_workers` from the worker's CAPS reply, so the sweep tunes against the baseline it is really running rather than the product defaults.
  <sub>2026-10-10 · strata-chat-2026-10-10-12-04.md</sub>

**next_step**
- `next_step` is now "build `pack/full` locally, run CUDA-vs-CPU parity on the 4090" — no Daytona GPU credits required.
  <sub>2026-10-10 · hypercore-chat-2026-10-10-11-52.md · also in hypercore-chat-2026-10-10-11-52.md</sub>

**pcie-frac**
- Bottom line: no measured `pcie-frac` or `spec-min-p` exists for the current HyperCore config; the calibration ran and deliberately left the defaults in place.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-15-51.md</sub>

**pcie_frac**
- Does the request config carry `pcie_frac` / `spec_min_p`? Without them the pcie sweep becomes five engine re-inits instead of one — five model loads.
  <sub>2026-10-09 · strata-chat-2026-10-09-18-55.md</sub>

**pcieauto**
- `--pcie-frac 0.00` in the Strata config is a no-op value with a side effect. 0.0 is already Strata's default, so writing it changes nothing about the share, but pinning it disables the `PcieAuto` refinement.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-15-51.md</sub>

**permissionerror**
- Also, `rocm_root()` wrote its marker into `sys.prefix`, which is read-only for a system interpreter — that was the `PermissionError` in `test_setup_unsloth`.
  <sub>2026-10-10 · strata-chat-2026-10-10-08-05.md</sub>

**prompt.json**
- The profiles are read from `prompt.json` beside the server or `prompts/prompt.json` (the one this repo ships): adding a profile to that file adds a menu entry with nothing to change in the page or the code.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-08-01.md</sub>

**prompts/**
- `serve/test_prompts.py`: the shipped-file test now uses `find_prompt_file(ROOT)`, and a new test covers the search order (root wins over `prompts/`, and neither → the "is not there" error).
  <sub>2026-10-11 · hypercore-chat-2026-10-11-11-46.md</sub>

**prompts/prompt.json**
- Cause. The dropdown is built at run time from `GET /prompts`, and that endpoint reads `ROOT / "prompt.json"` — but this repo ships the profiles in `prompts/prompt.json`.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-11-46.md · also in 2026-10-11-hypercore-chat-2026-10-11-06-34.md</sub>

**rules same field**
- Two rules for the same field, and the second clause (`or req.pcie_frac < -1.0`) is subsumed by the first, so the guard is just "reject outside [-1, 1]".
  <sub>2026-10-09 · strata-chat-2026-10-09-18-55.md</sub>

**s2_gemv_fast.cu**
- Both levers in `s2_gemv_fast.cu` are ones I would have shipped as wins, because absent the paired runs their sign is not knowable from first principles.
  <sub>2026-10-09 · strata-chat-2026-10-09-16-17.md</sub>

**serve/test_abi_contract.py**
- Test culture is genuinely strong: 94 Python test files, 37 C++/CUDA/HIP test files, ABI alignment checks (`tools/check_abi_alignment.py`, `serve/test_abi_contract.py`), a glibc-floor gate, cross-toolchain test (Daytona), backend-parity tests.
  <sub>2026-10-10 · strata-chat-2026-10-10-03-30.md</sub>

**serve/test_prompts.py**
- (`serve/test_prompts.py` had the same wrong path, which is why `test_the_real_prompt_json_offers_the_shipped_profiles` was failing.) Fix — resolve the file instead of assuming where it is:
  <sub>2026-10-11 · hypercore-chat-2026-10-11-11-46.md</sub>

**settings.json**
- That needs a machine where the CMake configure step is allowed: rebuild, then `./setup.sh --calibrate` to write the pcie-frac and adapt sweep into `settings.json`.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-14-18.md</sub>

**src/kernels/**
- The pattern is systematic: every GPU kernel in `src/kernels/cuda/` has a CPU or reference counterpart driven from `src/kernels/` — e.g.
  <sub>2026-10-09 · strata-chat-2026-10-09-08-03.md</sub>

**src/kernels/_parity.cpp**
- Parity/bench/test files are colocated with the kernels they check (`src/kernels/_parity.cpp`), plus a separate `tests/` tree: `tests/core` 12 files, `tests/hip` 16, `tests/cuda` 3, `tests/prefill` 1, `tests/platform` 1, `tests/data/native_experts` 6 fixtures.
  <sub>2026-10-09 · strata-chat-2026-10-09-08-03.md</sub>

**state file next**
- The state file's next step (rebuild, `./setup.sh --calibrate`, record the measured pcie-frac) is still open, and I updated it to note that the attempt needs the GPU free.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-15-51.md</sub>

**strata_build_conversation_tests**
- They cluster by module exactly as the code does: Note the collision: `STRATA_BUILD_CONVERSATION_TESTS` and `STRATA_ENABLE_HIP` are both CMake options and identifiers in the source — the build-time and runtime namespaces overlap, which is a real footgun when mapping this surface.
  <sub>2026-10-09 · strata-chat-2026-10-09-08-03.md</sub>

**test_web_client.py**
- The test style is contract-based rather than smoke-based: `test_web_client.py` asserts on the shipped JS and HTML, so a UI change that breaks behaviour fails a test.
  <sub>2026-10-13 · hypercore-chat-2026-10-13-00-06.md</sub>

**timeout_s hard ceiling**
- `timeout_s: 90` is a hard ceiling on every tool call. I hit it twice this session: `sudo apt-get install -y xvfb` with `timeout_s: 300` returned `error: tools/call timed out after 90 s`.
  <sub>2026-10-07 · strata-chat-2026-10-07-09-31.md</sub>

**tools/hip**
- One note: while confirming that pre-existing failure I used `git stash`, which briefly reverted the repo's uncommitted tracked changes; I restored them and the working tree is back to its original state (`git stash list` is empty, the `tools/hip` and `tools/vision` edits intact).
  <sub>2026-10-06 · strata-chat-2026-10-06-00-55.md</sub>

**universal home user0**
- The … [universal] /home/ai-user0/_Strata/docs/AMD_HIP.md … Since 0.1.39 a tuning run by hand (`./setup.sh --calibrate`) is saved for the AMD card it ran on and reused when setup runs again.
  <sub>2026-10-13 · hypercore-chat-2026-10-13-08-16.md · also in hypercore-chat-2026-10-13-08-16.md</sub>

**wait actually ni_hypercore**
- Wait — actually in ni_hypercore-q2_0.json, `--pcie-frac 0.00` IS set.
  <sub>2026-10-13 · strata-chat-2026-10-13-21-31.md</sub>

**xvfb**
- Run `STRATA_TEST_LIVE=1 python3 serve/mcp/tests/run_all.py --server browser` once `xvfb` is present to close that gap.
  <sub>2026-10-07 · strata-chat-2026-10-07-07-26.md</sub>

## Decisions taken

what was chosen, and why, oldest first


**.mcp_test_state.json**
- README coverage table (17 cases, 221 total) and `.mcp_test_state.json` (loop 5, the thread-affinity fix recorded, the Xvfb error marked resolved) are updated.
  <sub>2026-10-07 · strata-chat-2026-10-07-09-31.md</sub>

**add_test**
- Do you want the C++ test suite wired into CI? It requires `tests/CMakeLists.txt` (or enabling the inline `add_test` blocks) and a CUDA/HIP-free path on `ubuntu-latest`; right now it can't run there at all.
  <sub>2026-10-10 · strata-chat-2026-10-10-03-30.md</sub>

**applied core expert_source**
- applied at `src/core/expert_source.cpp:3692-3712`, zeroed rows counted at `:3865-3868` When it is on. On by default (rank 7) on CUDA builds since 0.1.42, and on HIP gfx1200/gfx1201 since 0.1.43.
  <sub>2026-10-13 · hypercore-chat-2026-10-13-03-22.md</sub>

**test added serve**
- Test added: `serve/test_server.py AmdTelemetry.test_pcie_link_is_the_narrowest_slowest_hop`.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-14-18.md</sub>

## Measured on this machine

numbers actually measured, not estimated


**--resident-experts** · 3 chats
- And on this node it is moot twice over: the running config uses `--resident-experts` → `FileExpertSource`, whose 19.15 GiB is already fully page-locked and registered (96–98% hit, 1–5% PCIe); and I checked the profile itself — `data/expert-profile.bin` (48×512, all 24,576 pairs ranked) has a layer-heat spread of only 32.5%, and the best heat-ordered prefix beats the arena prefix by 1.99% at k=18.
  <sub>2026-10-10 · hypercore-chat-2026-10-10-18-06.md</sub>
- The tool's fit assessment says Q2_0 "fits in the low-RAM mode (slower: the GPU holds part of the experts)" — consistent with the `--resident-experts` and `--pcie-frac 0.00` flags in `ni_strata-q2_0.json`, and with the 4.4 GB of RAM I found available while the engine was resident.
  <sub>2026-10-07 · strata-chat-2026-10-07-09-31.md</sub>
- Right as they are: `--pcie-frac 0.00` (correct — zero file reads), `--expert-cache auto` (15.05 GiB free → 11,022 slots), `--resident-experts`, `--spec-min-p 0.70` (calibrated at 141.6 tok/s).
  <sub>2026-10-07 · strata-chat-2026-10-07-09-31.md</sub>

**cudamalloc** · 2 chats
- No model was loaded, no GPU was touched — the 4090 is holding 24,074 of 24,564 MiB and a 4 KB `cudaMalloc` from a second process returns `out of memory`, so throughput is still unmeasured here.
  <sub>2026-10-09 · strata-chat-2026-10-09-18-55.md</sub>
- A refactor of an 11k-line driver is exactly the kind of change that would need that same paired-measurement discipline before it's adopted — and I can't run it here: the 4090 is holding 24,074 of 24,564 MiB and a 4 KB `cudaMalloc` from a second process returns `out of memory`.
  <sub>2026-10-09 · strata-chat-2026-10-09-16-17.md</sub>

**nvidia-smi** · 2 chats
- `nvidia-smi` reports 834 MiB free on the RTX 4090, and pid 2247278 (`/home/ai-user0/black_box/serve/server.py --engine hypercore --config /home/ai-user0/black_box/max_run_q2_0.json --port 8081`) has been up 55 minutes and is still serving requests.
  <sub>2026-10-13 · hypercore-chat-2026-10-13-03-22.md</sub>
- Status: code done and building; the four measurements are blocked on the GPU, which your own serve instance is holding. Done, verified in this session Blocked `nvidia-smi` shows 26 MiB free of 24564, held by pid 1246988 (`engine/hypercore --serve`), child of pid 1246985, whose parent is your shell (bash 21365), not a job I started.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-22-55.md</sub>

**--selftest**
- `nvidia-smi` reports 38 MiB free right now: serve holds the GPU, so the `--selftest` run and the two A/Bs (`HYPERCORE_ADAPT_OVERLAP`, `HYPERCORE_MMVQ_IL`) cannot run.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-22-55.md</sub>

**3090 takes most**
- A 3090's 24 GB takes most of the CPU work away.
  <sub>2026-10-03 · strata-chat-2026-10-03-14-03.md</sub>

**build-shared/hypercore-worker**
- Also, `--short --dry-run` no longer runs a real calibration; it says so and falls back to the staged sweep: The next blocker you will hit `nvidia-smi` reports 28 MiB free right now: `serve/server.py` (pid 1646195) is running with `build-shared/hypercore-worker` holding the card.
  <sub>2026-10-12 · hypercore-chat-2026-10-12-13-18.md</sub>

**cudaerrornokernelimagefordevice**
- The GPU is dead for this build. `torch 2.10.0+cu128` reports `cuda.is_available() == True` but every kernel call fails: "GTX 1060 3GB with CUDA capability sm_61 is not compatible with the current PyTorch install" → `cudaErrorNoKernelImageForDevice`.
  <sub>2026-10-07 · strata-chat-2026-10-07-17-37.md</sub>

**cudahostregister**
- The test asserts the real profile is rejected: The registration half of the test exits 77 (skipped) because the live server holds 23.9 GiB of the 24.5 GiB GPU — `cudaHostRegister` of even 1 MiB is refused.
  <sub>2026-10-10 · hypercore-chat-2026-10-10-18-06.md</sub>

**data/expert-profile-coder.bin**
- Strata ships its expert profile (`data/expert-profile-coder.bin`, the shipped ranking mapped onto the kept experts through the release's `rco-allocation.txt`: 72% of the expert reads hit the GPU on a 12 GB card).
  <sub>2026-10-03 · strata-chat-2026-10-03-14-03.md</sub>

**decode_ms**
- That confirms both of your decisions empirically: `prefill_ms` is the slot hold (45 ms = `40 + max_new/2`, and `resolve_test` shows it collapsing to 0 at `pcie_frac=1.0`), and `decode_ms` really is 0 in the stub.
  <sub>2026-10-09 · strata-chat-2026-10-09-22-41.md</sub>

**defensible statement workspace**
- The defensible statement from this workspace is narrower: on this RTX 4090 the working configuration is `--pcie-frac 0.00 --spec-min-p 0.50 --pool-workers 10` (recorded in `2026-10-03/04/08-community-rtx4090-iq3xxs-200k-{code,ru}/env.json`), with decode in the 135-155 tok/s band, and `STRATA_KV_PREFETCH=1` and `"parallel": 2` both measured as losses here (2-4% and 28% respectively).
  <sub>2026-10-11 · hypercore-chat-2026-10-11-15-51.md</sub>

**expert cache auto**
- With `--expert-cache auto` filling 15.94 GiB and resident RAM mode, the VRAM is nearly full → the driver pages GPU memory to system RAM → decode degrades → the model emits garbage/CJK spam/empty.
  <sub>2026-10-13 · strata-chat-2026-10-13-21-31.md</sub>

**guard more experts**
- The guard. If 90% or more of the experts are already in the GPU cache (60% on a HIP layer split), the default is not set and you get the opposite message: `STRATA_ROUTE_TAIL_SKIP is off by default: X% of the experts are in the GPU cache, so few are missed and skipping costs more draft acceptance than it saves`.
  <sub>2026-10-13 · hypercore-chat-2026-10-13-03-22.md</sub>

**live decode throughput**
- From the live log, decode throughput against prompt length: Expert cache hit rate is 97.5–98.3% across that range, with only 1.3–2.7% of routed experts read over PCIe — at ~785 KB per blob that is well under 1 GB/s, nowhere near the PCIe limit.
  <sub>2026-10-10 · hypercore-chat-2026-10-10-18-06.md</sub>

**max_run_q2_0.json**
- Next step, when you are willing to stop the live server: It will warm-start from `optuna_tune/history/Intel-Core-i9-14900KF_NVIDIA-GeForce-RTX-4090_31GB_PCIe4x16_q2_0_gen_131072.json` (5 configurations already measured there) and rewrite `max_run_q2_0.sh` / `max_run_q2_0.json`.
  <sub>2026-10-12 · hypercore-chat-2026-10-12-17-13.md</sub>

**qwen/qwen2.5-1.5b-instruct**
- Constraint found: the GPU is fully held by the Strata engine (PID 71501, 23.5 / 24.5 GiB), so `Qwen/Qwen2.5-1.5B-Instruct` OOM'd on CUDA → the benchmark ran on CPU.
  <sub>2026-10-07 · strata-chat-2026-10-07-17-37.md</sub>

**summary says real**
- The summary says real cliff is context length: 67-token prompt 190 tok/s, 68k prompt 102.6 tok/s, 94.1% hit, 7.4% PCIe reads.
  <sub>2026-10-10 · hypercore-chat-2026-10-10-18-54.md</sub>

**verified sweep numbers**
- Verified from the sweep numbers (n=3 per value, paired by round) Overall engine comparison. Across the six pcie values both engines measured (0, 0.2, 0.55, 0.75, 0.9, 1.0), the mean paired difference is +3.04 tok/s with t = 1.19.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-15-51.md</sub>

**wait machine 5090**
- Wait — but this machine is an RTX 5090 with 64GB per the earlier tests.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-13-20.md</sub>

## Still open

not done, deferred, or waiting on a decision


**nvidia-smi**
- Not yet done: no real engine measurement, because `nvidia-smi` reported 28 MiB free (a server is running).
  <sub>2026-10-12 · hypercore-chat-2026-10-12-14-31.md</sub>
