# Hardware and environment

Accumulated from 4 transcripts, 15 entries. Built 2026-10-11. Newer chats append here; within a section the entries are grouped by the thing they are about, newest statement first.


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


**--adapt-decay**
- `tools/calibrate.py` now sweeps `--pcie-frac` up to `1.0`, adds adaptive-tier candidates for `--adapt-every`, `--adapt-swaps`, and `--adapt-decay`, uses longer 512-token answers for the adaptive tier, records `report["adapt"]`, and keeps earlier measurements if a later engine restart fails.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-13-20.md</sub>

**catalog**
- A set kept beside the server still wins over the shipped one, and with neither the root path is returned so `catalog` reports it as missing rather than guessing.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-11-46.md</sub>

**hypercore defaults strata**
- HyperCore ran at its defaults, Strata at `pcie-frac 0.00 --spec-min-p 0.70`.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-15-51.md · also in hypercore-chat-2026-10-11-15-51.md</sub>

**pcie frac spec**
- `pcie-frac 0.00` and `spec-min-p 0.70` are real, in `~/Strata/strata-q2_0.json`.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-15-51.md</sub>

**pcie-frac**
- Bottom line: no measured `pcie-frac` or `spec-min-p` exists for the current HyperCore config; the calibration ran and deliberately left the defaults in place.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-15-51.md</sub>

**pcieauto**
- `--pcie-frac 0.00` in the Strata config is a no-op value with a side effect. 0.0 is already Strata's default, so writing it changes nothing about the share, but pinning it disables the `PcieAuto` refinement.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-15-51.md</sub>

**prompts/**
- `serve/test_prompts.py`: the shipped-file test now uses `find_prompt_file(ROOT)`, and a new test covers the search order (root wins over `prompts/`, and neither → the "is not there" error).
  <sub>2026-10-11 · hypercore-chat-2026-10-11-11-46.md</sub>

**prompts/prompt.json**
- Cause. The dropdown is built at run time from `GET /prompts`, and that endpoint reads `ROOT / "prompt.json"` — but this repo ships the profiles in `prompts/prompt.json`.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-11-46.md</sub>

**serve/test_prompts.py**
- (`serve/test_prompts.py` had the same wrong path, which is why `test_the_real_prompt_json_offers_the_shipped_profiles` was failing.) Fix — resolve the file instead of assuming where it is:
  <sub>2026-10-11 · hypercore-chat-2026-10-11-11-46.md</sub>

**settings.json**
- That needs a machine where the CMake configure step is allowed: rebuild, then `./setup.sh --calibrate` to write the pcie-frac and adapt sweep into `settings.json`.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-14-18.md</sub>

**state file next**
- The state file's next step (rebuild, `./setup.sh --calibrate`, record the measured pcie-frac) is still open, and I updated it to note that the attempt needs the GPU free.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-15-51.md</sub>

## Decisions taken

what was chosen, and why, oldest first


**test added serve**
- Test added: `serve/test_server.py AmdTelemetry.test_pcie_link_is_the_narrowest_slowest_hop`.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-14-18.md</sub>

## Measured on this machine

numbers actually measured, not estimated


**defensible statement workspace**
- The defensible statement from this workspace is narrower: on this RTX 4090 the working configuration is `--pcie-frac 0.00 --spec-min-p 0.50 --pool-workers 10` (recorded in `2026-10-03/04/08-community-rtx4090-iq3xxs-200k-{code,ru}/env.json`), with decode in the 135-155 tok/s band, and `STRATA_KV_PREFETCH=1` and `"parallel": 2` both measured as losses here (2-4% and 28% respectively).
  <sub>2026-10-11 · hypercore-chat-2026-10-11-15-51.md</sub>

**verified sweep numbers**
- Verified from the sweep numbers (n=3 per value, paired by round) Overall engine comparison. Across the six pcie values both engines measured (0, 0.2, 0.55, 0.75, 0.9, 1.0), the mean paired difference is +3.04 tok/s with t = 1.19.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-15-51.md</sub>

**wait machine 5090**
- Wait — but this machine is an RTX 5090 with 64GB per the earlier tests.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-13-20.md</sub>
