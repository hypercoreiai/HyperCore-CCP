![HyperCore — a large GGUF model running on low-spec consumer hardware](docs/media/header_readme.jpg)

# HyperCore-CCP

**Cuda, CPP, Python.** Big GGUF models on low-spec consumer hardware.

HyperCore runs a 30 B-class MoE model on a single 12–24 GB consumer GPU by keeping the
hot path on the card and the cold path in system RAM, and serving it as an OpenAI- and
Anthropic-compatible API on `http://127.0.0.1:8080`.

Engine version **0.1.40** · CUDA, HIP (AMD), SYCL (Intel Arc) and CPU backends · MIT licensed.

---

## Install

```sh
./install.sh                 # detect the GPU, pick a model size, build, run
```

Step by step, on Windows and Linux, for NVIDIA, AMD and Intel cards:
[docs/INSTALL.md](docs/INSTALL.md). If an AI coding assistant is doing the install for
you, hand it [docs/AI_SETUP.md](docs/AI_SETUP.md).

## How it works

| Technique | What it buys you | Detail |
|---|---|---|
| Expert cache on the GPU | MoE experts stay resident, so decode rarely leaves the card | [HOW_IT_WORKS.md](docs/HOW_IT_WORKS.md) |
| Layer split across GPUs | Two or three cards run contiguous layer ranges, each with its own expert cache | [MULTI_GPU.md](docs/MULTI_GPU.md) |
| MTP / speculative decode | A draft layer proposes, the model verifies | [DETAILS.md](docs/DETAILS.md#speed-measured) |
| KV prefetch and batching | Overlaps the CPU pool with the GPU launch | [KV_PREFETCH.md](docs/KV_PREFETCH.md), [BATCHING.md](docs/BATCHING.md) |
| Prompt- and message-boundary caching | Repeated turns reuse prefill instead of recomputing it | [PROMPT_CACHE_TAIL.md](docs/PROMPT_CACHE_TAIL.md), [MESSAGE_BOUNDARY_CACHE.md](docs/MESSAGE_BOUNDARY_CACHE.md) |
| Disjoint expert cache, exchange rotation | Secondary GPUs and the CPU pool share expert work without contending | [DISJOINT_EXPERT_CACHE.md](docs/DISJOINT_EXPERT_CACHE.md), [EXCHANGE_ROTATION.md](docs/EXCHANGE_ROTATION.md) |

Measured numbers for your card: [docs/DETAILS.md](docs/DETAILS.md#speed-measured). Older
and experimental hardware: [docs/OLDER_GPUS.md](docs/OLDER_GPUS.md).

## The black-box boundary

Everything outside the engine talks through one C header,
`include/hypercore/hypercore_api.h`. The engine is a separate worker process; the
Python side frames messages over IPC.

```
serve/  ── C API ──>  libhypercore_api.so  ──>  hypercore-worker
```

Two gates are **blocking build targets** — the build fails if either is violated:

```sh
python3 tools/check_abi_alignment.py     # header, worker and Python mirrors agree
python3 tools/glibc_floor.py build/libhypercore_api.so
```

The ABI is pinned: `hypercore_caps_t` 28 bytes, `hypercore_request_summary_t` 40 bytes,
`hypercore_request_config_t` 28 bytes (`struct_size@0, temperature@4, top_p@8, top_k@12,
max_new_tokens@16, pcie_frac@20, spec_min_p@24`). Every struct carries `struct_size` at
offset 0 for forward compatibility.

## Technical accomplishments

**Engine**
- 248 C/C++/header files across `src/` and `include/`, with CUDA, HIP and SYCL backends
  chosen at configure time (`-DHYPERCORE_ENABLE_CUDA|HIP|SYCL`).
- Backend-neutral public API: no CUDA, HIP or SYCL type crosses the boundary.
- 47 C/C++/CUDA test files in `tests/` and `bench/`, including the boundary tests that
  link against the built library.

**Interface**
- OpenAI- and Anthropic-compatible HTTP API with streaming, cancellation, and a worker
  supervisor with slot admission and shed-at-gate backpressure.
- 8 MCP servers exposing 50 tools (browser, contracts, docs, home, hub, scrape,
  terminal, web), each contract-checked against the handler that implements it.

**Testing**
- 98 Python test modules and 47 C/C++/CUDA test files.
- One command exercises the whole tool surface and reports coverage:

```sh
python3 serve/mcp/tests/run_all.py
# TOTAL  50 tools  235 cases  235 pass  0 fail  0 error  0 skip   OK
# every advertised tool has at least one case
```

**Reproducibility**
- CI (`.github/workflows/boundary.yml`) runs contract-lock → supervisor tests →
  integration guard → model guard (conditional on `pack/full`) → cross-toolchain.
- The glibc floor of the shipped artifact is 2.38, under the 2.39 contract line, so the
  binary runs on older distributions without a rebuild.

**Documentation**
- 28 pages in `docs/`, every internal link verified, plus the design paper
  ([docs/paper/HyperCore-Paper.pdf](docs/paper/HyperCore-Paper.pdf)) and raw benchmark
  data ([docs/benchmarks/](docs/benchmarks/)).

## Repository layout

| Path | Contents |
|---|---|
| `include/hypercore/` | The public C contract |
| `src/` | artifact, core, kernels, ngram, plan, platform, prefill, program, spec |
| `sycl/` | SYCL kernels and includes for Intel Arc |
| `serve/` | HTTP server, supervisor, MCP servers, web front end |
| `tools/` | Validation gates: ABI alignment, glibc floor, benchmarks |
| `tests/`, `bench/` | Engine tests and frozen benchmark evidence |
| `docs/` | User and technical documentation |
| `cmake/`, `CMakeLists.txt` | Build, including the HIP backend |
| `data/` | Draft vocabularies and expert profiles the engine needs |

Generated output is not in the repository: `build*/`, `engine/`, `dist/`, `.venv/`,
model packs, logs, and agent session state. Rebuild with:

```sh
cmake -B build -DHYPERCORE_ENABLE_CUDA=OFF && cmake --build build -j4
```

## History

This repository's history begins here. The prior history of the project (1,182 commits,
42 release tags) is archived in the working tree as `project_history_2026-10-10.txt` and
`project_history_2026-10-10.git.bundle`, both gitignored.

Something went wrong? [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).
