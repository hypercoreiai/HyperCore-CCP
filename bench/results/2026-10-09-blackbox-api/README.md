# 2026-10-09 — HyperCore black-box API lab (contract drafted, boundary proven, no engine numbers)

## Naming

The engine is HyperCore. `tools/rename_hypercore.sh` is the one-pass mapping; it is idempotent and re-runnable.

| was | now |
|---|---|
| `include/hypercore/hypercore_blackbox.h` | `include/hypercore/hypercore_api.h` |
| `src/interface/hypercore_bridge.cpp` | `src/interface/hypercore_bridge.cpp` |
| `hypercore_shared` / `hypercore_api` | `hypercore_api` (CMake target) |
| `libhypercore_api.so` | `libhypercore_api.so.0.1.40` |
| `hypercore-cli`, `hypercore-worker` | `hypercore-cli`, `hypercore-worker` |
| `HYPERCORE_API`, `HYPERCORE_STATUS_*`, `HYPERCORE_STOP_REASON_*` | `HYPERCORE_API`, `HYPERCORE_STATUS_*`, `HYPERCORE_STOP_REASON_*` |
| `hypercore_engine_*` | `hypercore_engine_*` |
| `HYPERCORE_*` environment variables | `HYPERCORE_*` |
| `HyperCoreWorker`, `HyperCoreCalibrationAdapter` | `HyperCoreWorker`, `HyperCoreCalibrationAdapter` |

Three identifiers were deliberately **not** renamed: `hypercore.ple.format` / `hypercore.ple.scale` (GGUF metadata keys in artifacts already on disk), `~/.cache/hypercore`, and the `hypercore.r1:` reasoning-replay prefix. Renaming those changes what existing files and caches mean, which is a migration, not a rename.

The build directories (`build-shared/`, `build-cuda-check/`) and the repo directory name are still `HyperCore`; renaming them invalidates every absolute path baked into a configured build.


The boundary now lives in the project: `include/hypercore/hypercore_blackbox.h` and
`src/interface/hypercore_bridge.cpp`, built by `hypercore_api` in the root `CMakeLists.txt`. This
directory holds the tests that validate it.

| file | what it is |
|---|---|
| `hypercore/hypercore_blackbox.h` | a copy of the public contract, kept in sync with `include/hypercore/hypercore_blackbox.h` |
| `hypercore_bridge_v2.cpp` | the fixture implementation the tests run against (same source as `src/interface/hypercore_bridge.cpp`) |
| `abi_test.c` | the `struct_size` prefix rule: an older caller reads a newer struct safely |
| `busy_test.c` | `BUSY` at exactly `max_batch_slots` |
| `precedence_test.c` | defaults -> environment -> JSON, on every field the boundary reports |
| `summary_test.c` | terminal chunk, EOS vs LIMIT, prompt ownership, v1 reader against a v2 summary |
| `pool_test.c` | `active_pool_workers` resolves under all three layers; `BUSY` releases nothing; the drafter inside the archive produces real draft counts |
| `adapter_test.py` | the Python mirror matches the C layout; no row is silently dropped |

Against the CMake-built `libhypercore_api.so.0.1.40`:

```
PASS: prefix rule holds
PASS: BUSY exactly when the slots are full
PASS: precedence holds on every reported capability
PASS: terminal summary is readable by an older caller and stop_reason distinguishes EOS from LIMIT
PASS: pool size is observable through every config layer, BUSY releases nothing, and the drafter
      inside the archive produced real draft counts
exported=4  total_exported=4
```

Build and run:

```
cmake -B build-shared -DHYPERCORE_ENABLE_CUDA=OFF
cmake --build build-shared --target hypercore_api -j4
L=/home/ai-user0/HyperCore/build-shared
cd bench/results/2026-10-09-blackbox-api
for t in abi_test busy_test precedence_test summary_test pool_test; do
  gcc -std=c11 -Wall -Wextra -I. $t.c -L$L -lhypercore_api -Wl,-rpath,$L -o $t && ./$t
done
python3 adapter_test.py $L/libhypercore_api.so
$L/hypercore-cli --prompt "5 6 7 5 6 7" --max-new 12
```

The engine is not behind this boundary yet. No model is loaded and no GPU is touched: the `.so`
contains the fixture, not `generate.cpp`. Throughput is still unmeasured here.

## What the contract deliberately does not hide

The engine's existing `--serve` protocol already is a black box, with a line grammar. The API is the same grammar typed:

| stdio (`generate.cpp`) | API |
|---|---|
| `GEN <max_new> <ids>` / `GENI <max_new> <embfile> <ids>` | `hypercore_request_set_tokens` + `set_max_new` + `set_embeddings_file` → `submit` |
| `temperature=F top_p=F top_k=N min_p=F penalty_*=F seed=N cvec=0\|1 ckpt=0 pcie_frac=F spec_min_p=F` | `hypercore_sampler_t` — the same keys, as a typed struct |
| `T <id>` | the token sink, or `hypercore_request_next_token` |
| `DONE produced prompt_ms decode_ms stop drafts...` (line 9945) | `hypercore_summary_t` — every field, in the same order |
| `PP <done> <total> <ms> <tok/s>`, `REUSED <n>`, `YIELDED <slot> <n>` | the event sink |
| `STOP`, `BSTOP <slot>` | `hypercore_request_stop` |
| `VRAM <reserve_mib>` (#533) | `hypercore_engine_set_vram_reserve`, returning `HYPERCORE_ERR_BUSY` while batch slots are decoding |
| `ERR <message>` | `hypercore_error_t` + `hypercore_engine_last_error` |
| `--batch N` slots | `caps.batch_slots` + N concurrent requests |

## Two decisions worth arguing about

**1. Engine config is a string; per-request sampling is a struct.** Engine config maps to 164 flags and is set once, so opaque JSON is fine. Per-request keys are on the hot path, must be validated (`top_k` is required in 1..64 by the sampled path), and a caller should not build a JSON document to set a temperature.

**2. `struct_size` is the ABI mechanism, and it has to be got right.** A caller declaring a *smaller* struct is served the prefix it knows; a caller declaring a *larger* one is refused rather than silently truncated. The first version of this lab rejected every mismatch, which would have broken exactly the case the field exists for.

## Prerequisites the repo does not yet have

- `CMakeLists.txt` has no library target at all: `add_executable` for the engine and the tests, `add_library(... INTERFACE)` for warnings and artifact plumbing. A `libhypercore_engine.so` needs a real target, and the engine's error handling is `std::exit()` everywhere — an exit inside a `.so` kills the embedder's process, so every internal exit must become a returned error before the box can be a library.
- Config precedence. There are 75 `getenv` calls in `generate.cpp` alone. A JSON-only API silently changes behaviour unless defaults → env → JSON/argv precedence is written down and tested.
- `sycl/include/hypercore` is 25 headers against CUDA's 108. There is no single public interface today, so the C contract must be defined before the C++ wrapper, or the wrapper will be CUDA-shaped.

## The bridge, compiled

`hypercore_bridge_review.cpp` is the proposed bridge **exactly as written**. It does not compile:

```
error: '::getenv' has not been declared
error: 'strlen' is not a member of 'std'
error: 'nothrow' is not a member of 'std'
error: 'atoi' is not a member of 'std'
```

`hypercore_bridge_fixed.cpp` is the same bridge with the boundary bugs corrected. `abi_test.c` and
`busy_test.c` run against it; both pass.

| what was wrong | what it does now |
|---|---|
| `struct_size > sizeof` accepted a *smaller* caller and then wrote all 148 bytes into it | copies only the declared prefix; the guard test proves an 8-byte caller is untouched beyond 8 bytes |
| `struct_size == 0` (the `memset` default) was accepted | refused: a caller that did not set the field is not an older ABI, it is an unset one |
| `device_name` left as stack garbage | filled |
| allocation failure returned `BUSY` | returns `UNSUPPORTED`; `BUSY` means slots full, and nothing was full |
| `bool slots_available = true` made `BUSY` unreachable | an atomic slot counter; `busy_test.c` sees BUSY at exactly the third submit with `batch: 2` |
| the prompt+max_new bound the engine enforces at `generate.cpp:2164` was not checked | checked at the boundary, which is the only place an embedder can get a status code instead of an exit |
| `C_VISIBILITY_PRESET hidden` | measured: `-fvisibility=hidden` exports **0** symbols; the entry points need an explicit `__attribute__((visibility("default")))` |
| the JSON layer was a stub with no precedence | defaults → env → JSON, verified: `HYPERCORE_POOL_WORKERS=7` with no JSON gives 7, JSON overrides it |

One test bug worth recording, because it is the kind that hides a real failure: reading the caller's
struct in the same `printf` argument list as the call that fills it. C evaluates arguments in an
unspecified order, and gcc evaluated them right-to-left, so the first run reported `batch=0` while the
bridge had correctly parsed `batch=2`. The bridge was right; the test was wrong.

## Cross-machine check (Daytona sandbox)

`tools/daytona_bridge_test.py` uploads the four files to a Daytona sandbox, builds them there, and runs
the same three tests. That is the only honest way to test a `.so` contract: the whole point of a stable
boundary is that a caller on a different machine links against it.

```
$ DAYTONA_API_KEY=... python3 tools/daytona_bridge_test.py
sandbox ba5924b2-... state=STARTED
g++ (Debian 14.2.0-19) 14.2.0          # this machine runs 15.2.0
PASS: prefix rule holds
PASS: BUSY at the slot limit
PASS: precedence holds
exported_symbols=5
```

Two things that only showed up remotely:

- **The header had drifted.** `hypercore_blackbox.h` and `hypercore/hypercore_blackbox.h` existed in parallel and
  diverged - one had the `pool_workers` capability field, the other did not. The sandbox caught it
  because it only ever sees one of them. There is now one header, at `hypercore/hypercore_blackbox.h`.
- **A test that hard-codes a default fails the moment the environment layer is exercised.** The first
  run asserted `workers == -1` for the defaults case; run with `HYPERCORE_POOL_WORKERS=7`, the env layer
  correctly overrode it and the test failed. The bridge was right, the assertion was wrong - same shape
  as the `printf` argument-order bug above.

The sandbox is created and deleted per run; nothing persists. The SDK call is `sandbox.process.exec(...)`
(not `run_command`, which does not exist in this version).

## v2: the summary-in-stream contract, tested

`hypercore/hypercore_blackbox.h` + `hypercore_bridge_v2.cpp` implement the revised contract (per-request
`pcie_frac`/`spec_min_p`, terminal summary chunk). `calibrate_adapter.py` is the ctypes wrapper, run
against it. Four failures, all reproduced:

| what the design said | what happened when it ran |
|---|---|
| `submit()` executes asynchronously, the callback streams tokens | the adapter read the metrics immediately after `submit()` returned. 15 combinations requested, 2 recorded, 1 with no data. The terminal chunk is the only completion signal, so the adapter waits on it. |
| a `CFUNCTYPE` callback per iteration | rebinding it each loop freed the Python object while the request thread still held the raw pointer. Segfault in `destroy()`, not in the engine. |
| `bool slots_available` / BUSY at the slot limit | a stub that *reports* 104 ms and finishes in 10 microseconds makes BUSY a race: 8 consecutive runs, 7 failures. The stub now sleeps for the duration it reports. |
| `pcie_frac` "set negative to skip" | `if (x < 0.0f && x > 1.0f)` is never true; `pcie_frac = 3.0` was accepted. Fixed to `>= 0 && > 1`. |

Layout agreement, measured on both machines:

```
C:  config=28 summary=40 chunk=16 caps=148
py: config=28 summary=40 chunk=16 caps=148
```

## v3: the authorized header, and what broke when the adapter ran against it

`hypercore/hypercore_blackbox.h` is the authorized spec, with one addition: `HYPERCORE_API`. Measured -
compiled with `-fvisibility=hidden` (which `CMakeLists.txt` sets via `C_VISIBILITY_PRESET`), the
`.so` exports **0** symbols. The header as written cannot be linked.

Layout agreement, measured on both machines:

```
C:  config=28 summary=32 chunk=16
py: config=28 summary=32 chunk=16
```

The async model works: `summary_test.c` proves the terminal chunk carries a stop reason that a
24-byte v1 reader can still read, and that `EOS` and `LIMIT` are distinguishable.

Five failures in the adapter, all reproduced:

| what the code does | what happened |
|---|---|
| `session_id = hash((pcie, spec, iteration))` passed as `void*` | Python's `hash()` returns signed values. A negative hash becomes a large unsigned pointer: `-217929430759900949` arrives as `18228814642949650667`. The dict lookup misses, the event never fires, the row is dropped with no error. 6 of 15 combinations lost; the sweep took 61 s because each lost row waited out the 10 s timeout. A monotonic counter fixes it: 45 of 45 rows in 4.9 s. |
| `if not (-1.0 <= req.pcie_frac <= 1.0) or req.pcie_frac < -1.0` | the second clause is subsumed by the first, so the guard is just "reject outside [-1, 1]". The header says **any** negative value is the fallback sentinel; the adapter rejects `-2.0` that the boundary accepts. Two different rules for the same field. |
| `while status == -2: submit(); sleep(0.01)` | unreachable. The sweep submits one request, waits for its terminal chunk, then submits the next. It can never be BUSY. The backpressure handling is dead code. |
| `stop_reason` recorded, never read | the enum exists so calibration can separate a truncated run from a natural one. The adapter stores it and ignores it. |
| `self._session_metrics[session_id] = ...` from the engine thread, `.get()` from the driver | safe only because `Event.set()`/`wait()` orders them. It is not obvious, and the pop happens before a late terminal chunk could arrive. |

Two things the header does not say:

1. **The prompt array's lifetime.** The LIFETIME RULE covers the output frame. `submit()` is
   asynchronous, so `prompt_tokens` must outlive the request - nothing in the contract says the
   engine copies it. `summary_test.c` case D overwrites the caller's array immediately after
   `submit()` and checks that the outcome still reflects the original values; the bridge copies.
2. **`stop_reason` has no value for cancellation.** `generate.cpp` has exactly four terminal states:
   `"length"` (9025), `"stop"` (9521, 9777), `"cancel"` (9047, 9522, 9778). `NONE`/`EOS`/`LIMIT`/
   `ERROR` covers three of them and leaves `cancel` to `ERROR`. Also `NONE = 0` and `EOS = 1` carry
   the same comment, which is what a reader will trust.

And one mismatch with the server layer: `serve/server.py:849` normalises `top_k` - 0 and values
above 64 both become 64. The boundary refuses `top_k = 0` with `INVALID_ARG`. Under decision 3
that is the right behaviour for a library caller, but the server and the boundary currently disagree
about the same input.

Nothing here has been adopted by the engine itself. The boundary compiles, links and passes its
tests on two different toolchains; `src/program/generate.cpp` has not been moved behind it.

## 4. The shared-library build: what the CMake rules actually do

Measured, not assumed:

| claim | result |
|---|---|
| hidden visibility + `HYPERCORE_API` yields exactly 4 entry points | **true.** `nm -D` on the CMake build: 4 `T` symbols, and nothing else. Same on the remote g++ 14.2. |
| `VERSION ${PROJECT_VERSION}` produces `libhypercore_engine.so.0.1.40` | **true.** `project(... VERSION 0.1.40)` at line 11; the build emits `libhypercore_engine.so.0.1.40` with soname `libhypercore_engine.so.1`. |
| "the remaining ~88k lines remain closed within the binary" | **false as written.** The `.so` is 22,936 bytes and contains no symbol from the spine. A static archive linked into a shared library is pulled in only where a referenced symbol exists; the v1 bridge calls none of it, so the linker drops every object. The firewall is currently a link-time fiction. To make it real the bridge has to call the engine, or the spine must be linked with `-Wl,--whole-archive`. |

Three things in the block that did not configure as given:

1. **The spine is conditional.** `hypercore_core` (line 267), `hypercore_kernels` (309), `hypercore_engine` (436) and `hypercore_prefill` (516) are defined only inside `if(HYPERCORE_ENABLE_CUDA OR HYPERCORE_ENABLE_HIP)`. `HYPERCORE_ENABLE_CUDA` defaults to OFF, so the unconditional `target_link_libraries` fails with *"Target 'hypercore_api' links to target 'hypercore_core' but the target was not found."* The appended block builds the link list from what is actually defined: `hypercore_plan hypercore_artifact hypercore_spec` plus `hypercore_kernels_cpu` on CPU, plus the GPU spine when a backend is on.
2. **The nvcc guard was after the point of failure.** `enable_language(CUDA)` runs at line 147, long before any target exists. Discovery placed after the libraries can never fire. It is now immediately before `enable_language(CUDA)`. The `FATAL_ERROR` branch was exercised with a scratch project; on this machine CMake resolves `/usr/local/cuda/bin/nvcc` on its own, so the guard is a fallback, not a routine path.
3. **`install(FILES hypercore/hypercore_blackbox.h ...)`** names a path that does not exist. The header lives at `include/hypercore/hypercore_blackbox.h`, matching the project's `target_include_directories(hypercore_spec PUBLIC include)` convention.

Two smaller notes: `target_compile_features(cxx_std_20)` is redundant (`CMAKE_CXX_STANDARD 20` is set at line 51), and `CUDA_STANDARD 20` on `hypercore_api` is inert because the target has no `.cu` sources.

One naming risk: `OUTPUT_NAME "hypercore_engine"` collides with the existing `hypercore_engine` STATIC target, which produces `libhypercore_engine.a` in the same build directory. Different extensions, so no hard error — but two artifacts named `hypercore_engine` in one build is a packaging ambiguity someone will hit.

## 5. Forcing the spine in: measured

`-Wl,--whole-archive` scoped to the engine targets, plus `-Wl,--exclude-libs,ALL`. Against the CPU build:

| | before | after |
|---|---|---|
| `.so` size | 22,936 B | 2,673,352 B |
| exported `T` symbols | 4 | 4 |
| spine symbols in `.text` | 0 | 75 (`SuffixDrafter`, `detect_cpu_topology`, `ExpertPool`) |
| spine symbols exported | 0 | 0 |

So the claim holds. `nm -D` still shows exactly the four entry points; everything else is local.

Three things that only appear once you force the archive in:

1. **The spine must be PIC.** Forcing a non-PIC static archive into a shared object fails on the first `thread_local`:
   ```
   ld: relocation R_X86_64_TPOFF32 against `hypercore::kernels::cpu::ExpertPool::drain(...)::gbuf'
   can not be used when making a shared object; local-exec is incompatible with -shared
   ```
   (`src/kernels/cpu/pool.cpp:635`.) The reachable-subset link never hit this because that object was never pulled in. `POSITION_INDEPENDENT_CODE ON` is now set on every target inside the whole-archive region.

2. **`--whole-archive` is not scoped to what you list.** `hypercore_kernels_cpu` links ggml `PUBLIC`, so `libggml-base.a` and `libggml-cpu.a` land inside the region too and hit the same PIC problem (`relocation R_X86_64_PC32 against symbol 'stderr@@GLIBC_2.2.5'`). The "unwanted system libraries" you were trying to avoid are pulled in transitively, not by the flag list. If ggml should stay out, it has to be unlinked from the spine, not just left off this list.

3. **The artifact is glibc-2.43-specific.** Exactly one external symbol carries a version tag: `sqrtf@GLIBC_2.43`. The Daytona sandbox (glibc older than 2.43) cannot link it:
   ```
   /usr/bin/ld: ./libhypercore_api.so: undefined reference to `sqrtf@GLIBC_2.43'
   ```
   The bridge alone does not reference `sqrtf`; the spine does. So forcing the archive in trades a 23 KB shell that links anywhere for a self-contained library that requires a very recent glibc. That is the real cost of decision 1, and it is the kind of thing the remote check exists to catch.

## 6. The gateway is linkable

`src/interface/cli_gateway.cpp` + a `hypercore-cli` target that links **only** `hypercore_api`. It reaches the engine through `init`/`get_caps`/`submit`/`destroy` and nothing else:

```
engine: batch_slots=4 max_context=4096 pool_workers=23
5 6 7 5 6 7 5 6 7 5 6 7
[summary] produced=12 decode_ms=46 drafts=12/36 stop=2
```

Two things that follow from it:

- `pool_workers=23` is the pool's own topology probe (`detect_cpu_topology`), not `hardware_concurrency()`. On this i9-14900KF that is 24 logical processors minus the reserved host core. `hardware_concurrency()` would have reported 32 and overstated the pool.
- `drafts=12/36` comes from `hypercore::spec::SuffixDrafter`. A prompt with no repeat produces `drafts=0/0`. The counts are not constants.

What `generate.cpp` still cannot be demoted to a wrapper of: model loading, conversation state, tool calls, and the process-level CUDA/HIP setup it does before its argument loop (`CUDA_MODULE_LOADING=EAGER`, the ROCclr arena sizing). Those are engine responsibilities today and there is no place for them in the boundary yet.

## 7. The out-of-process worker: what the framing actually had to be

`src/interface/worker_main.cpp` + `serve/worker_client.py` put the engine in its own process and talk to it over a UNIX domain socket. `libhypercore_api.so` is unchanged as the contract; the worker is just the only thing that links it.

Three places where the draft spec did not survive contact with the compiler:

1. **The 24-byte header is fine.** `uint32, uint32, uint64, uint64` packs to exactly 24 with no padding on x86-64, and `struct.calcsize("<IIQQ") == 24` agrees. No change needed.

2. **The terminal payload is 32 bytes, not 36.** The listed fields sum to 32. Writing 36 would make the reader read four bytes that were never sent. The `"padded structural copy" note in the spec is the trap: a C struct with a `uint64_t` after two `uint32_t`s does get padding, so the *struct* is 32 and the *field list* is 32 too. There is no 36.

3. **`prompt_len` needs four reserved bytes.** A payload of `config(28) + prompt_len(8)` puts `prompt_len` at byte offset 28, which is not 8-byte aligned. The whole point of the format is alignment, so the payload is `config(28) + reserved(4) + prompt_len(8) + tokens`. The reserved field is explicit in the writer and the reader, not left to compiler padding.

Also worth noting about the writer: `write(fd, header, 24); write(fd, payload, n);` is two syscalls and is not atomic. Two engine threads can interleave a header with someone else's payload. The worker builds the frame in a buffer and issues one `write()`; the test runs four concurrent streams through it and checks every stream gets all its tokens and exactly one terminal frame.

`read()`/`write()` returning short is normal on a socket, not an error. `read_exact`/`write_all` loop. The parent's reader parses frames out of a bulk buffer rather than one `recv()` per frame; measured, that is 0.26 µs/frame versus 0.71 µs/frame for the naive per-frame read.

### Cancellation, now that it has a way to be produced

`hypercore_engine_cancel(engine, request_id)` is in the header and implemented. Semantics, all tested in `cancel_test.c`:

- it is a flag, not a join. It returns immediately; the request thread notices it between tokens.
- a cancelled stream still emits a terminal frame, with `stop_reason == CANCEL` and `produced_tokens` equal to what was actually delivered (403 delivered, 403 reported).
- the slot is released by the request thread, not by `cancel()`. A test with `batch=1` shows the second request is `BUSY` while the first runs, and accepted once the cancelled stream ends.
- `request_id == 0` is rejected, because 0 is the null `user_data` a callback may legitimately receive.
- reusing an in-flight `request_id` is `INVALID_ARG` rather than silently overwriting the registry entry.

One consequence nobody asked for: `submit()` now takes `request_id` as its second argument. That is a signature change, so every caller had to move - the four C tests, `cli_gateway.cpp`, both calibration adapters, and `serve/engine_bridge.py`. The registry is keyed by that id, which is what makes cancel stateless from the caller's side.

### The GIL claim, measured

`scaling_lab.py` measures the host boundary, not inference: the engine in `libhypercore_api.so` is still the deterministic fixture (sleep, then emit as fast as it can). Aggregate tokens/s reaching the host, median of 3 runs, 4000 tokens per stream:

```
streams   in-process tok/s   worker IPC tok/s    ratio
      1            215,352            124,031     0.58x
      2            161,557            180,893     1.12x
      4            154,141            266,965     1.73x

retention relative to one stream (1.00 = no degradation):
    in-process: 1.00  0.75  0.72
    worker IPC: 1.00  1.46  2.15
```

The shapes are the point, not the absolute numbers. In-process, every token crosses the GIL, so adding streams serialises the engine threads and throughput falls. Out-of-process, the engine threads never enter the interpreter; the parent's reader amortises its parse cost over larger reads, so throughput rises as streams are added.

At one stream the worker is *slower* (124k vs 215k). That is the honest reading: the IPC adds a syscall and a parse that the in-process callback does not. The win is not per-token, it is that the cost stops scaling with concurrency. A single-tenant CLI should link the library directly; a multi-tenant server should not.

The micro-costs behind that, measured in isolation:

| path | cost |
|---|---|
| socket recv, bulk | 0.01 µs/frame |
| parse a frame from a buffer | 0.26 µs/frame |
| one `recv()` per frame | 0.71 µs/frame |

The first version of the reader used `del buffer[:n]` per frame, which is O(len(buffer)) and made the reader quadratic in frames per read. Indexing instead of slicing removed it - that change alone is what turned the multi-stream numbers around.

### Crash isolation, actually tested

`crash_isolation()` starts a stream, SIGKILLs the worker mid-flight, and checks what the waiting request thread sees. It sees the death in 0.002 s, not after its 30 s timeout, and a replacement worker boots and serves requests. The engine's own `std::abort()` paths in `pool.cpp` (three of them, all in the topology probe) are not reachable from the fixture, so the signal stands in for them: from the parent's side an abort and a SIGKILL are the same event, an EOF on the socket. That is worth stating plainly - the blast-radius claim is tested against the mechanism, not against the actual abort path.

### Porting to ThreadingHTTPServer

`http_worker_test.py` runs the worker behind a stdlib `ThreadingHTTPServer` and checks the four things that actually break in that shape:

```text
PASS: a ThreadingHTTPServer request streams all its tokens - tokens=30
PASS: a saturated worker answers with 503, not an empty 200
PASS: closing the client socket releases the batch slot
PASS: /slots reports resolved pool size - {'backend_type': 1, 'max_batch_slots': 1,
      'max_context_len': 4096, 'active_pool_workers': 23}
4/4 passed
```

Two things the first version got wrong, and are worth writing down because they are easy to get wrong in the real server too:

- **Status must be decided before the headers.** The handler opened the stream after sending `200`, so a BUSY request became a 200 with an empty body. A client cannot distinguish "no tokens" from "no capacity". Opening the stream and pulling the first frame *before* `send_response` fixes it; the ack frame is produced by the engine before any token, so there is no latency cost.
- **Cancel needs the request id, and a generator does not carry one.** `stream()` now takes an optional `request_id`; the request thread generates it, and the `BrokenPipeError` handler passes it to `worker.cancel()`. Without that handle, a closed tab leaves the slot occupied until the engine finishes the whole `max_new_tokens` run.

The `serve/` tests still exercise the subprocess path. They pass, but they are no longer testing the boundary the server would use - that is the next piece of work.

## 8. The boundary export: five files, and one precedence rule

The engine repository stays where it is. `/home/ai-user0/HyperCore` is still the project home - renaming it breaks the symlinks, the absolute paths inside `.venv-daytona`, and the `build-shared/` / `build-cuda-check/` targets. What is exported as the supported interface is five files:

| file | role |
|---|---|
| `include/hypercore/hypercore_api.h` | the shared header: types, entry points, the ABI size rule |
| `src/interface/hypercore_bridge.cpp` | the bridge: in-process `.so` boundary, six exported symbols |
| `src/interface/worker_main.cpp` | the multiplexer: one engine process, many request streams over one socket |
| `serve/hypercore_supervisor.py` | the supervisor: owns the process, the restart budget, the request lifecycle |
| `serve/ipc_parser.py` | the broker: framing, decoding, and the per-request `queue.Queue` routing |

`serve/engine_bridge.py` is the in-process ASGI variant. It is not part of the export and is kept only so `bridge_test.py` can still compare a threaded worker against a linked library.

The text protocol (`GEN`, `RESUME`, `T`, `PP`, `DONE`, `ERR`) is not translated. It predates the binary contract, and an adapter on top of `HyperCoreProcessSupervisor` would parse a line, re-encode it, and then read the structured fields anyway - two representations of the same event, and the latency of both.

### Precedence, stated once

`hypercore_engine_resolve()` is the only place the two levels meet:

1. **Instance baseline**, fixed at `hypercore_engine_init()`: defaults -> `HYPERCORE_*` environment -> the JSON string.
2. **Request frame**: `pcie_frac` / `spec_min_p` set to exactly `-1.0f` means "take level 1". Any value in `[0.0, 1.0]` overrides it for that execution only. Anything else is `INVALID_ARG` - never clamped.

`-0.0f` is not a sentinel; it compares equal to `0.0`, which is a real value. An instance with no configured baseline resolves the sentinel to `-1`, meaning "the engine decides", not "zero".

The rule is observable, not just stated: in the fixture `spec_min_p` raises the draft acceptance floor and `pcie_frac` shortens the slot hold. `resolve_test` proves both reach the thread that is running the request:

```
PASS: sentinels fall back to the instance baseline
PASS: an in-domain request value overrides the baseline
PASS: the two fields resolve independently
PASS: pcie_frac 1.5 is rejected, not clamped
PASS: -0.5 is not the sentinel and is not a probability
PASS: the domain endpoints 0.0 and 1.0 are valid values, not sentinels
PASS: raising spec_min_p in the request lowers drafts_accepted
      drafts_offered=60 accepted: baseline=20 strict=0
PASS: pcie_frac in the request changes the slot hold the engine reports
      decode_ms: pcie_frac=0.0 -> 60, pcie_frac=1.0 -> 10
```

Run: `gcc -std=c11 -Wall -Wextra -I. resolve_test.c -L../../build-shared -lhypercore_api -Wl,-rpath,../../build-shared -o resolve_test && ./resolve_test`

The worker test suite against `serve/hypercore_supervisor.py` + `serve/ipc_parser.py`: 23/23, and the HTTP harness 4/4.

## 9. The capability snapshot, and the tests that replaced the text pipe

`hypercore_caps_t` grew two fields. A calibration runner needs the starting point of a sweep before it runs one, and inferring it by submitting an all-sentinel probe request makes a capability read a side effect - it occupies a batch slot and it can be BUSY.

```c
typedef struct hypercore_caps_t {
    uint32_t struct_size;
    uint32_t backend_type;
    uint32_t max_batch_slots;
    uint32_t max_context_len;
    int32_t  active_pool_workers;
    float    instance_pcie_frac;     /* resolved Level-1 baseline, or -1.0f if unset */
    float    instance_spec_min_p;    /* resolved Level-1 baseline, or -1.0f if unset */
} hypercore_caps_t;
```

28 bytes now. `pool_test` keeps a hand-written `caps_v1` (16-byte declared prefix, guard bytes after it) rather than deriving the old layout from the current struct, so growing the struct cannot move the goalposts of the test that checks the prefix rule. The worker's `RESP_CAPS` payload is 28 bytes: backend, slots, max_ctx, pool_workers, status, pcie, spec.

The three text-protocol integration tests were rewritten, not retired:

| test | what it now proves |
|---|---|
| `serve/test_slots.py` | a saturated slot answers BUSY, the slot drains when the holding stream ends, four requests against three slots means the fourth is BUSY, and a request override does not rewrite the instance baseline |
| `serve/test_control_cancel.py` | a cancel during prefill reaches the wire exactly once, a cancelled stream terminates with `cancel` and a produced count that matches what was delivered, an unknown id is a no-op |
| `serve/test_fatal_recovery.py` | a dead link is reported at once rather than after the timeout, recovery is bounded by the supervisor's budget, and the observer can see when the last frame arrived |

They run against `serve/frame_fixture.py`: a `ScriptedWorker` on the far end of a `socketpair`, feeding real frames into the real `HyperCoreIPCListener`. The mock handles each request on its own thread, because a single-threaded mock finishes the first request before the second frame is even read and "saturated slot" becomes unobservable.

One thing the mock taught us about the real boundary: `attach()` before `send()`. A frame routed to a queue that does not exist yet is dropped, and a worker that answers immediately will always beat a caller that attaches after sending.

**Not yet done:** `serve/server.py` still runs `HyperCoreEngine` over the text pipe. The supervisor is built and tested, but the HTTP handlers are not wired to it. That is the migration, and it is the reason `test_server.py` and `test_lifecycle.py` are unaffected by this change.






## 5. The message map, and where the Monitor gets its numbers

`serve/ipc_parser.py` states request→reply as data:

```python
MSG_TYPE_MAP = {CMD_SUBMIT: RESP_STATUS, CMD_CANCEL: RESP_STATUS,
                CMD_GET_CAPS: RESP_CAPS, CMD_PING: RESP_PONG}
```

`expected_reply()` is the only way the supervisor decides what a worker should answer.
`msg_type + 1` is gone, and with it a latent collision: the listener used to put the
token id in slot 0 and the message type in slot 0 for an ack, so a token id of 3 was
indistinguishable from `RESP_STATUS = 3`. Every frame now arrives as
`(msg_type, token_id, payload)`.

`HyperCoreProcessSupervisor.monitor_snapshot()` returns the legacy scrape names —
`decode_ms`, `tokens_produced`, `drafts_accepted`, `drafts_offered`, `decode_tok_s`,
`exit_code`, `panic`, `status` — so the dashboard code does not change. Two things that
showed up while wiring it:

- `restarts` counts every bring-up, including the first. It is a lifecycle signal, not a
  fault signal, so `panic` is derived from the process actually being gone with a
  nonzero exit, not from the counter.
- A caller that builds its own frames must call `note_frame()`; otherwise the Monitor
  panel stays empty while requests run and the watchdog thinks the link is quiet.

`serve/hypercore_server.py` is the migration: `ThreadingHTTPServer` over the supervisor,
`/health`, `/slots`, `/v1/chat/completions`, `/v1/completions`, host-side shedding,
stall → `CMD_CANCEL`, client disconnect → `CMD_CANCEL`, one `[MONITOR]` line per
request. It does not re-encode the request struct — `build_submit_payload` is the only
place the layout is written. That rule caught a real bug in the draft:
`struct.pack("<IfffIff", 28, …)` puts `top_k` in the float slot while the header
declares `uint32_t top_k`. The worker would read garbage and say nothing.

## 10. The wire layout is now explicit, not implied

`hypercore_request_summary_t` is `#pragma pack(push, 1)` and 40 bytes on every target. The
worker writes it field by field into a 44-byte buffer (`prompt_reused` + 40), and
`serve/ipc_parser.py` reads the same offsets positionally. `struct_size` is a protocol tag,
not a field count.

| byte (payload) | field | note |
|---|---|---|
| 0 | prompt_reused | header field, outside the summary |
| 4 | struct_size | always 40 |
| 8 | produced_tokens | |
| 12 | prefill_ms | slot hold; maps to the legacy `prompt_ms` |
| 20 | decode_ms | emit window + draft verification |
| 28 | drafts_accepted | |
| 32 | drafts_offered | |
| 36 | stop_reason | |
| 40 | time_to_first_token_ms | was reserved padding; now the TTFT slot, same 40-byte footprint |

`wire_test.py` proves it against the real worker rather than a fixture. Actual terminal
payload from `build-shared/hypercore-worker`:

```
00000000 28000000 0a000000 2d000000 00000000 00000000 00000000 00000000 02000000 2d000000
```

10 tokens delivered, prefill 45 ms, decode 0 ms, stop = LIMIT, TTFT 45 ms. Every offset
check passes.

Two things this exposed:

- **`decode_ms` is legitimately 0 in the fixture.** The stub emits 10 tokens with no
  simulated work, so the emit window is under a millisecond. Assertions that said
  `decode_ms > 0` were testing the fixture, not the boundary. They now assert
  `decode_ms >= 0`. On real hardware the field is the number that shows batching
  degradation, so it stays on the wire.
- **`prefill_ms` is the only field a per-request `pcie_frac` can move.** `resolve_test`
  originally asserted `decode_ms` would change; it cannot, because the hold happens before
  the first token. The test now asserts `prefill_ms` moves (50 ms at `pcie_frac=0.0`,
  0 ms at `1.0`) and leaves `decode_ms` alone.

## 11. Byte 36 is a field now, and the parser reads a prefix

Two changes to the same 40 bytes:

**Reserved padding became `time_to_first_token_ms`.** The footprint is unchanged; the tag
is still 40. `hypercore_bridge.cpp` measures it from the moment the request is accepted to
the moment the first token reaches the callback, so it includes the scheduling hold that
`prefill_ms` already describes. That is deliberate: a stream with a large TTFT and a clean
`decode_ms` is a stall before generation, not a slow decode, and without TTFT the two look
identical in the Monitor. A stream that produced nothing reports 0, meaning "no first token
delivered", not "instant".

**`decode_terminal` accepts `struct_size >= 40`.** Strict equality was the opposite of the
forward-compatibility promise in the header: a worker that appends a field would have
broken every older caller. The rule is one-directional and is now tested with hand-built
frames, since no worker emits a longer summary yet:

| declared struct_size | payload | outcome |
|---|---|---|
| 40 | 44 bytes | read, normal path |
| 48 | 52 bytes | prefix read, 8 trailing bytes discarded |
| 36 | 44 bytes | `FrameError` - the prefix itself is not there |

`static_assert(offsetof(..., time_to_first_token_ms) == 36)` in `worker_main.cpp` is what
makes a header edit fail at compile time rather than at the first request.

One thing this surfaced: `MONITOR_FIELDS` in `serve/ipc_parser.py` is defined and never
read. The supervisor builds `monitor_snapshot()` by hand, so the legacy-key map is dead
code. Either wire it up or delete it; keeping it is how the two lists drift apart.

Verified: 7/7 C ABI tests, 24/24 `worker_test.py`, 4/4 `http_worker_test.py`, 13/13 serve
unit tests, `wire_test.py` OK, and the same header decodes against the 51 MB CUDA build.

## 12. Telemetry policy: three answers, one of them a correction

**TTFT includes the queue hold.** It is measured from request acceptance to the first
delivered token, so it fully overlaps `prefill_ms`. That is the point: `ttft_ms` is what a
client waited, `prefill_ms` is what the engine computed, and `ttft_ms - prefill_ms` is the
gate delay a developer can read off the two. `test_ttft_includes_the_hold_and_is_never_less_than_prefill`
pins that invariant.

**Absent is `None`, never 0.** `decode_terminal` returns `None` for fields the worker that
built the frame did not have. A v1 summary has no prefill window and no TTFT; reporting 0
for those makes an old worker look instantaneous, which is a false alert, not a missing one.

**`MONITOR_FIELDS` is now the table, not a comment.** `monitor_snapshot()` iterates it. Each
row carries its source: `summary` (the wire), `process` (the worker's exit status),
`watchdog` (restart counter), or `derived`. That split matters: lifecycle keys are not on
the wire, so a purely wire-driven table cannot produce `status`, `exit_code` or `panic`.
Adding a metric is one row; the function does not change.

```
$ python3 -m unittest serve.test_slots   # 11 tests, including TelemetryContractTest
```

## 13. The server.py blueprint, tested against the real worker

The proposed handler does not run as written. Three defects, each verified against
`build-shared/hypercore-worker`:

| # | line in the blueprint | what the worker actually does |
|---|---|---|
| 1 | `struct.pack("<IfffIff", 28, ...)` | `hypercore_request_config_t` is `<IffIIff`. Packing `top_k` as a float writes `0x3F800000` into the uint32 slot: the engine reads `top_k = 1065353216`. |
| 2 | config + prompt_len, no reserved field | the submit payload is `SUBMIT_HEAD` = config(28) + reserved(4) + prompt_len(8) = 40 bytes before the tokens. Without the reserved 4, `declared_len` and the token count disagree and the worker answers `ack status=-1` (INVALID_ARG). |
| 3 | `msg_tag == "ACK"` / `"TOKEN"` / `"TERMINAL"` | the listener routes `(msg_type, token_id, payload)` with integer tags: `RESP_STATUS=3`, `STREAM_TOKEN=4`, `STREAM_TERMINAL=5`. No string tag ever appears, so the loop runs to the 30 s timeout and cancels a finished request. |

Verified directly:

```
blueprint submit : 52B -> ack status=-1
correct submit   : 56B -> ack status=0
```

`build_submit_payload` and `build_frame` in `serve/ipc_parser.py` already get this right,
and `serve/hypercore_server.py` already implements the same handler against the real
supervisor signature (`worker_binary`, `socket_path`, `config`) and passes 4/4.

The migration the blueprint describes is in fact already installed: `serve/server.py:2150`
defines `HyperCoreRequestHandler`, an adapter over `HyperCoreProcessSupervisor`, and
`main()` at line 5317 wires it into `Service`. No stdout lines are parsed on the live
path. What is left is the orphan: `serve/server.py:539` still defines the text-pipe
`HyperCoreEngine`, and nothing in `main()` constructs it - only `test_lifecycle.py` and
`test_parallel.py` do, by importing it directly. Deleting the class without porting those
two suites would break them; keeping it means two engines in one file with one of them
never running.

## 13. prefill_ms now starts at the scheduling point

`run_request` takes three timestamps instead of two:

```
request_start  -> scheduled_at  = queue hold   (not reported directly)
scheduled_at   -> prefill_end   = prefill_ms
request_start  -> first_token   = ttft_ms
```

The fixture sleeps `prompt.size()` ms for prompt evaluation, so the two windows are
independent and the subtraction is testable rather than asserted.

Before, a `pcie_frac` change moved `prefill_ms` (58 vs 8) and nothing else, which meant
the Monitor could not tell a slow bus from a slow prompt. Now:

```
PASS: the same prompt reports the same prefill regardless of bus pressure
      ttft_ms: pcie_frac=0.0 -> 58, pcie_frac=1.0 -> 8 (prefill_ms 8 both)
```

`serve/ipc_parser.py` derives `queue_hold_ms = ttft_ms - prefill_ms` and puts it in the
Monitor snapshot. It is `None` when either side was never measured, not 0.

## 14. The text-pipe engine is a fixture now

`HyperCoreEngine` moved out of `serve/server.py` (1,052 lines) into
`serve/fixtures/legacy_engine.py`. `serve/server.py` is 4,453 lines and no longer
defines or constructs it.

The path differs from the one proposed: `tests/` is the C++ suite tree (core, cuda, hip,
prefill), and the Python suites live next to the code they test. Putting a Python
fixture under `tests/` would split the test convention in two. `serve/fixtures/`
already exists and already holds test data.

Five suites import it, not two: `test_lifecycle`, `test_parallel`, `test_vram`,
`test_server`, `test_restart_waiters`. All import from the fixture now.

## 15. The routing patch, run verbatim

`build_submit_payload` in the patch is byte-identical to
`serve/ipc_parser.build_submit_payload` - verified, not assumed. The stream loop is not:

```
--- valid request ---
TypeError: cannot unpack non-iterable int object
```

The listener routes `(msg_type, token_id, reused)` for a token and
`(STREAM_TERMINAL, -1, summary_dict)` for the terminal. So:

| the patch reads | actual content | effect |
|---|---|---|
| `data_block` as `(token_id, prompt_reused)` on msg 4 | an `int` token id | TypeError on the first token |
| `data_block` as the status code on msg 3 | always `0`; the status is in the payload bytes | a rejected request is never reported; the handler waits for the 30 s timeout and then cancels a request that already ended |
| `data_block` as `prompt_reused` on msg 5 | the `-1` sentinel | every SSE `done` frame reports `prompt_reused: -1` |

The loop also never calls `note_frame(summary)`, so `/metrics` stays empty even though
the telemetry arrived.

## 16. Draft cycles are decode work; the wire stays 40 bytes; server.py is the entry point

Three decisions, and what each one changed in the code.

**1. The first speculative cycle is charged to `decode_ms`.** The header already claimed
`decode_ms` includes draft verification, but the bridge measured it from the first token
callback. The drafter is built and the first candidate is verified *before* anything is
emitted, so that work sat in neither window: `prefill_ms` ended before it, `decode_ms`
started after it. `run_request` now opens the decode window at `prefill_end`:

```
prefill_ms = scheduled_at -> prefill_end          # prompt evaluation only
decode_ms  = prefill_end  -> last token           # drafts, verification, sampler
ttft_ms    = scheduled_at -> first token
```

The invariant worth a test, not a comment: changing the lookahead length moves
`decode_ms` and `ttft_ms` and leaves `prefill_ms` where it was. `test_prompt_timing_does_not_move_with_the_draft_cycle`
runs the same request twice with and without a 150 ms draft cycle and asserts exactly that.
Without it, prompt telemetry is a sampling artefact and an embedder cannot read it as a
prompt cost.

**2. `queue_hold_ms` stays derived.** No field at byte 40. `MONITOR_FIELDS` maps it to
`ttft_ms - prefill_ms` in `serve/ipc_parser.py`, so the wire layout is untouched and the
dashboards get a flat metric. One consequence worth naming: with decision 1, the derived
hold contains the first draft cycle as well as the queue gate. It is still the right
number for "time between being scheduled and seeing the first token", but it is not a
pure queue measurement, and the name should not imply that it is.

**3. `serve/hypercore_server.py` is gone.** The raw stream loop now lives in
`serve/server.py` as `process_active_stream_loop`, reachable at `POST /infer/stream`.
The corrected consumer reads the tuple the listener actually sends:

| frame | slot 1 | slot 2 | read as |
|---|---|---|---|
| `RESP_STATUS` | request id | status code bytes | `decode_status(payload)` |
| `STREAM_TOKEN` | token id | prompt-reuse count | `token_id`, `reused` |
| `STREAM_TERMINAL` | `-1` | decoded summary | metrics, `prompt_reused` |

It also handles the case the patch did not: the listener puts `(None, 0, {"error": ...})`
on a request queue when the link dies. Without that branch the loop reads nothing, falls
through, and waits out the 30 s stall before cancelling a request whose worker is gone.
`serve/test_stream_loop.py` covers the ack, the busy path, the closed link, the stall,
and the reuse count.

## 17. One reader, and the build verifies the wire

HyperCoreProcessSupervisor.stream() is the only place a frame is consumed. It owns the ack,
the token/terminal transitions, both timeout walls, and the CMD_CANCEL that a dropped client
triggers in its finally block. stream_sse() in serve/server.py is a serializer: it writes the
data: lines and notices BrokenPipeError. _raw_stream() is a route, not a second loop.

serve/test_stream_loop.py drives that serializer against ScriptedWorker: token order, terminal
payload, client-gone mid-stream, stall-then-cancel, and busy-before-first-frame returning a
status code rather than raising.

The CI answer is the layout check, not the flood test. tools/check_abi_alignment.py reads the
static_assert(sizeof(...) == N) lines out of the header and compares them, field by field, with
the struct.Struct mirrors in serve/ipc_parser.py. It runs as
add_custom_target(hypercore_abi_alignment_check ALL ...) at CMakeLists.txt:1492, so every build
fails on a drift. A flood test measures throughput; it cannot see a byte move.

The Monitor's legacy names are still in use: drafts_offered, drafts_accepted, decode_tok_s and
panic are read at serve/server.py:2421-2514. MONITOR_FIELDS in serve/ipc_parser.py is the single
mapping from those names to wire fields or derived values; nothing else derives them.

Unverified: tools/bench_flood.py needs serve/server.py to start, and main() exits before serving
because pack/full/tokenizer/vocab.json is not present in this environment. The HTTP path is
tested against the fixture, not against the real entry point.

## 18. The config argument takes inline JSON or a file path

`hypercore_engine_init(engine, config)` now accepts either form. The decision is made on the
first non-whitespace character, so there is no heuristic to get wrong:

| argument | what happens |
|---|---|
| starts with `{` | inline JSON, used verbatim |
| anything else | a path, read once at init |
| `NULL` or blank | no configuration |
| missing file, unreadable, non-object JSON, >1 MB | `HYPERCORE_STATUS_INVALID_ARG` |
| empty file | no configuration |

Two deliberate choices:

- **A bad path is an error, not "no config."** A typo in `--config` must not start the engine on
  defaults and quietly produce the wrong numbers. That is the same reasoning as decision 1
  (crash-on-error retained).
- **The worker never sees the path.** `start_worker` is handed the resolved text, so the file is
  read exactly once. A restart after the file changes cannot produce an engine that disagrees with
  the caps already reported to the web runtime.

Precedence is unchanged: system defaults, then `HYPERCORE_*` environment, then this config - inline
or file, whichever was supplied. `config_test.c` covers all eleven cases, including a file config
driving the out-of-process worker.

## 19. Two entry points are shipped, and the load test uses the one that needs no model

`libhypercore_api.so` is not the only artifact an embedder is expected to use.

| entry point | how you reach it | what it is for |
|---|---|---|
| `build-shared/libhypercore_api.so` | link it, include `hypercore/hypercore_api.h` | an embedder that wants the engine inside its own process |
| `build-shared/hypercore-worker` | spawn it with a socket path, speak the frames in `src/interface/ipc_frame.h` | the same engine where an abort must not take the host down with it |

The worker is not a debug tool. It is the reason `HYPERCORE_STATUS_ENGINE_DEAD` exists as a
distinct value from `HYPERCORE_STATUS_BUSY`: BUSY means retry, ENGINE_DEAD means re-init. The
supervisor in `serve/hypercore_supervisor.py` is a reference client for that boundary, not the
only one - the frame layout is asserted in the header, in the worker, and in
`tools/check_abi_alignment.py`, so any client that reads the same 24-byte header and 40-byte
terminal payload is conformant.

`tools/bench_flood.py` measures that boundary: shedding when the slots are full, slot
reclamation when a client hangs up mid-stream. Those properties belong to the worker, not to a
model, so the test spawns `serve/flood_stub.py` - a stdlib ThreadingHTTPServer in front of the
real supervisor, with no tokenizer and no pack. Point `--server` at `serve/server.py` once a
pack is installed; the assertions are identical because the shedding is done by the worker's own
slot gate, and the stub never decides anything.

Run: `python3 tools/bench_flood.py --concurrency 12 --slots 4`
Result on this machine: 12 dispatched, 2-3 completed, 8 shed with 503, 2 client disconnects,
in-flight after settle 0.

## 20. There is no heartbeat frame, and the stall path proves it is not needed

The binary contract has no keepalive frame, and adding one would not buy anything:
liveness is already answered out-of-band by `CMD_PING`/`RESP_PONG`, and stream death is
already distinguishable - the listener sets `dead` on EOF and the stream loop raises
`WorkerUnreachable`, while a live link that simply stops emitting raises `StreamStalled`.

What was missing was the *reason*. A silent stream used to be reported as stalled whether
the engine was slow or the worker had stopped serving, and those need different actions.
`stream()` now tests the link before it names the failure:

```python
except queue.Empty:
    if not self.ping():
        raise WorkerUnreachable("worker stopped answering") from None
    raise StreamStalled(f"no frame for {wait}s") from None
```

`serve/frame_fixture.py` gains `mute_ping`, a fixture that answers no ping - a link that is
up but not serving, which is the only state a heartbeat would have distinguished. The test
`test_a_silent_link_is_called_unreachable_not_stalled` asserts that state reaches the HTTP
layer as 503-unreachable rather than 504, and that the host still reaps its own slot
(`sup.in_flight() == 0`) either way.

One consequence worth naming: a ping during a long generation is handled by the worker's
command loop, not by the request thread, so a slow engine still answers it. Slow and gone
are not the same thing, and now they are not reported as the same thing.

## 21. Two fixtures, deliberately: the wire and the HTTP surface

`HyperCoreEngine` is no longer in `serve/server.py`. It lives in `serve/fixtures/legacy_engine.py`
and is instantiated only by `test_lifecycle.py`, `test_parallel.py`, `test_server.py` and
`test_vram.py`; production reaches the engine through `HyperCoreProcessSupervisor` and the
binary IPC. That is the intended end state, not a leftover.

The two fixtures test different contracts and should not be merged. `ScriptedWorker` speaks
the packed wire and is the right stand-in for slot accounting, terminal summaries, stop
reasons and cancel. The legacy text engine speaks HTTP - auth, routing, structured output,
image admission, restart waiters - and those 204 tests do not need a tokenizer, a pack, or
a real worker. Moving them to `ScriptedWorker` would make the HTTP tests depend on frame
parsing they do not exercise.

## 22. The remote harness is the CI job, not a demo

`tools/daytona_bridge_test.py` was pointing at a header name and a library name that no
longer exist. It now uploads the current boundary - `include/hypercore/hypercore_api.h`,
`serve/ipc_parser.py`, `tools/check_abi_alignment.py`, the eight C tests and the artifact
built here - and runs three things in a sandbox that shares no toolchain with this machine:

1. a header-only compile under `-std=c11 -pedantic`, with no HyperCore source in sight;
2. the mirror drift check, on the sandbox's own CPython;
3. the ABI tests, linked against `libhypercore_api.so.0.1.40` built here.

Result on this run: header-only compile ok, mirror drift check ok, `remote_c_fail=0`, exit 0.

The division of labour is deliberate. `hypercore_abi_alignment_check` is a build target, so
drift is caught when someone builds. The sandbox is the only place that catches a host that
is not this one - a different libc, a different gcc, a different CPython. A boundary nobody
re-tests on someone else's machine is a boundary nobody owns, so this belongs in CI.

## 23. The load test has two tiers, and the tier is decided by what is on disk

`tools/bench_flood.py` now picks its target from the environment, not from a flag someone
has to remember:

- **Integration guard (default).** Spawns `serve/flood_stub.py` - stdlib HTTP in front of
  the real `HyperCoreProcessSupervisor` and the real `hypercore-worker`. No GPU, no
  weights. It exercises the 503 slot gate, the drop-mid-stream slot reclamation and the
  stall cancel, and it runs on every merge.
- **Hardware guard (`--model`).** Runs against `serve/server.py` with real weights. It
  refuses to run unless `pack/full` exists and is non-empty: an empty pack directory is
  what a CI scaffold leaves behind, and a throughput number from it means nothing. With no
  pack it prints `[SKIP]` and exits 2, so CI can gate the stage on file presence rather
  than on a hope.

The split is deliberate. The guard proves the supervisor reclaims slots and the worker
refuses what it cannot serve; only a real engine can show that the CUDA scheduling loop
has not slowed down. A flood test cannot see byte layout - a wrong offset produces a
plausible number in the wrong slot, not an exception - so it is paired with the contract
lock, not a substitute for it.

## 24. The request config is pinned by absolute offsets, not by a size

`hypercore_request_config_t` is the struct every inference call crosses. Size alone is a
weak guard: inserting `uint32_t reserved` before `top_k` keeps every field 4 bytes wide,
so a length check would still pass while `pcie_frac` landed in `max_new_tokens`'s slot.

`tools/check_abi_alignment.py` now asserts the offsets themselves:

```
struct_size@0  temperature@4  top_p@8  top_k@12
max_new_tokens@16  pcie_frac@20  spec_min_p@24      total 28 bytes
```

and rejects a hot-path field that is not 4 bytes. Offsets come from the parsed header
(comments stripped, widths taken from the type names), not from a hand-split of the
struct text - every field carries an inline `/* >= 0 */` comment, and splitting on `;`
turns those into phantom fields.

`serve/test_abi_contract.py` proves the lock is not vacuous: it edits the real header
(insert a field above `top_k`, delete `top_p`, widen `top_k` to `uint64_t`) and asserts
the checker fails. 8 tests, all passing.

## 25. Both artifacts are gated, in both build trees

`hypercore_abi_alignment_check` is now a dependency of `hypercore_api` **and**
`hypercore-worker`. Verified in the CPU tree and the CUDA tree:

```
[  9%] Verifying the C/Python wire-layout contract
[100%] Built target hypercore_api
[100%] Built target hypercore-worker
```

Deliberately not `ALL`. An `ALL` custom target re-runs the Python parser on every
`make`, on every target - including a one-file edit to a kernel. As a dependency of the
two artifacts that carry the contract, it runs exactly when a build produces them.

`.github/workflows/boundary.yml` wires the stages in order: contract lock → supervisor
tests + integration guard → hardware guard (conditional on `pack/full`) → cross-toolchain
sandbox. The Daytona stage is required, not advisory: it is the only check that runs the
shipped `.so` against a foreign gcc and CPython.

One thing I did **not** change: the target still carries `ALL`, so the lock also runs on a
bare `make` with no target named. That is the right default for a contract check - a
build that never produces the artifacts can still be handed a drifted header - but it
means the Python parser runs on every invocation of the build, including a one-line edit
to a kernel. If that ever shows up in build times, drop `ALL` and keep the two
`add_dependencies` lines; the gate stays, the cost goes away.

## 26. The libc the artifact is allowed to call is also a contract, and it was failing

The first real run of the cross-toolchain stage said the boundary was fine and the
artifact was not: the header compiled, the mirror check passed, and then all eight C
tests died at link time on the sandbox -

```
/usr/bin/ld: ./libhypercore_api.so: undefined reference to `sqrtf@GLIBC_2.43'
```

Nothing in the source says "needs glibc 2.43". The build host has glibc 2.43, the linker
resolves `sqrtf` against that host's libm, and the version stamp is written into the
`.so`. The reference is not even ours - it comes from the statically linked ggml
archives (`ggml-quants.c.o`, `unary-ops.cpp.o`, `ops.cpp.o`). The sandbox is Debian with
glibc 2.41, where that version does not exist, so the requirement surfaces as a link
error with no cause a reviewer can read.

The requirement is readable, so it is now a gate:

- **`tools/glibc_floor.py`** parses `objdump -T` and reports the highest glibc version any
  undefined reference is stamped with. `--require <ver>` fails the build when the artifact
  asks for more than we promise, and names the offending symbols rather than just saying
  "too new". `GLIBC_2.2.5` is parsed whole, not as "2.2".
- **`HYPERCORE_GLIBC_FLOOR`** (default `2.39`) states the oldest libc we ship to. That is
  not an arbitrary number: `Dockerfile:41` is `nvidia/cuda:13.0.0-devel-ubuntu24.04`, and
  Ubuntu 24.04 is glibc 2.39.
- **`hypercore_glibc_floor_check`** runs the tool on `$<TARGET_FILE:hypercore_api>` and is a
  dependency of `hypercore-worker`. It has to be an explicit edge: CI builds named targets
  (`--target hypercore_api hypercore-worker`), and an `ALL` target is skipped by exactly
  that kind of build, so the gate would have been in the Makefile and absent from every
  merge request.
- **`src/interface/glibc_compat.c`** + `-Wl,--wrap=sqrtf` is the fix. Every internal
  `sqrtf` is redirected to a local `__wrap_sqrtf` that calls `__builtin_sqrtf`, which the
  compiler lowers to one SSE instruction. No libm symbol is pulled in, so no version stamp
  is written. The wrapper is hidden (`C_VISIBILITY_PRESET hidden`) and is not part of the
  ABI surface.

Measured, after the change:

| artifact | glibc floor | gate |
|---|---|---|
| `build-shared/libhypercore_api.so.0.1.40` (CPU) | 2.38 | pass (2.39) |
| `build-cuda-check/libhypercore_api.so.0.1.40` (CUDA) | 2.38 | pass (2.39) |
| `hypercore-worker` (both trees) | 2.34 | pass |

Before the wrap the same artifacts reported 2.43 and the stage failed.

`tools/test_glibc_floor.py` (6 tests) compiles two objects with the host compiler - one
that calls libm, one that does not - and asserts the tool sees the floor, rejects a
2.0 gate, accepts a 99.0 gate, names the offender in the failure message, and does not
crash on a missing file. That suite runs in the `contract-lock` job.

Re-running the sandbox end to end:

```
sandbox: 05e368ce-...  artifact: 2703528 bytes
header-only compile: ok
mirror drift check: ok
sandbox_libc: ldd (Debian GLIBC 2.41-12+deb13u4) 2.41
[INFO] libhypercore_api.so.0.1.40: glibc floor 2.38; versions referenced: 2.2.5, ..., 2.38
remote_c_fail=0
```

The floor check is deliberately measured **on the sandbox**, not asserted from the build
host: the deployment machine is what decides what can be linked.

## 27. The floor gate writes its own fix

"The fix is one more `__wrap_` in `glibc_compat.c" is true, and useless at 2 a.m. in a
failed build: the reader still has to work out the signature, the builtin, and where the
link flag goes. The gate now emits the patch.

- **`CONTRACT_FLOOR = "2.39"`** in `tools/glibc_floor.py` is the default for `--require`,
  so a standalone run gates exactly the way the build does. A test reads
  `set(HYPERCORE_GLIBC_FLOOR "...")` out of `CMakeLists.txt` and asserts the two numbers
  are the same; the contract cannot drift into two places.
- **`--emit-shims`** prints, for every reference above the line, the shim source to add
  to `src/interface/glibc_compat.c` and the `-Wl,--wrap=<symbol>` flag to add to the
  target. Symbols with a compiler builtin (`sqrtf`, `sqrt`, `sqrtl`, `fabsf`, `fabs`) get
  a real body; anything else gets a note, not a guessed stub - a wrapper that calls
  `__real_<symbol>` keeps the very stamp wrapping was meant to remove, and a wrong
  signature fails to compile, which is worse than no shim.
- **`tools/test_glibc_floor.py` (10 tests)** compiles the emitted shim with the host
  compiler and asserts the reference is gone, not just that the text looks right:

```python
source, flags = GF.shim_block([("sqrtf", "2.43")])   # the tool's own output
# gcc -O2 -fPIC -shared probe.c glibc_compat.c -Wl,--wrap=sqrtf -lm -o wrapped.so
["sqrtf" for name, _ in GF.referenced_versions(wrapped_so)]  # -> []
```

The failure path, on the real artifact, against a gate one version lower than the contract:

```
$ python3 tools/glibc_floor.py --require 2.37 --emit-shims build/libhypercore_api.so
[FAIL] libhypercore_api.so requires glibc 2.38, the contract allows 2.37
  __isoc23_fscanf@GLIBC_2.38
  __isoc23_strtol@GLIBC_2.38
  __isoc23_strtoll@GLIBC_2.38
  fix: add to src/interface/glibc_compat.c
    /* __isoc23_fscanf@GLIBC_2.38: no builtin equivalent. ... */
  fix: add to the target's link options
    -Wl,--wrap=__isoc23_fscanf
```

`hypercore_glibc_floor_check` passes `--emit-shims` unconditionally, so a build that fails
this gate fails with the patch in its own output.

## 28. The four CI stages, replayed

The workflow cannot be run from here, so every command in `boundary.yml` was executed in
order on the build host. Stage 4 is the one that is not reproducible locally, and it ran
against the live sandbox:

| stage | what ran | result |
|---|---|---|
| `contract-lock` | CPU configure + `hypercore_api`/`hypercore-worker`, `check_abi_alignment.py --json`, `test_glibc_floor`, floor gate at 2.39 | 49 steps, contract PASS, 10 tests OK, floor 2.38 |
| `supervisor-tests` | `test_slots`, `test_control_cancel`, `test_fatal_recovery`, `test_config_forms`, `test_stream_loop`, then the stub flood | 42 tests OK; 12 dispatched / 2 completed / 8 shed / 0 in-flight |
| `model-guard` | `bench_flood.py --model` | exit 2, `[SKIP] no model pack at pack/full` - the stage is entered only when `pack/full` exists |
| `cross-toolchain` | `daytona_bridge_test.py` on Debian/gcc 14.2, glibc 2.41 | header-only ok, mirror drift ok, floor 2.38, `remote_c_fail=0` |

Nothing in the pipeline needs a GPU, a weight file, or this machine's toolchain.


## 29. The byte offsets matched; nobody had checked that the backends behave the same

`check_abi_alignment.py` proves two artifacts agree about where the fields are. It says
nothing about what they put in them. A CPU build and a CUDA build can share a header, share
the wire, and still answer the same request differently - and no test in the tree would
notice, because every test up to this point ran against one artifact.

`tools/backend_parity.py` sends one fixed request to every backend that has been built and
compares what came back. The probe is deliberately boring: `top_k=1`, `temperature=0.0`,
no overrides (`pcie_frac`/`spec_min_p` stay at the `-1.0` sentinel). Those are the settings
that make a differing stream a backend difference rather than sampling noise.

Two claims are checked, because they fail for different reasons:

| claim | how it is checked | what a failure means |
|---|---|---|
| determinism | the same backend, twice, byte for byte | the backend cannot be benchmarked; any regression test against it is a coin flip |
| cross-backend parity | token ids, `produced_tokens`, draft counters, `prompt_reused`, stop reason, `max_batch_slots`, `max_context_len` | the boundary behaves differently depending on which kernel answered |

`prefill_ms`, `decode_ms` and `ttft_ms` are deliberately not compared. They are
measurements of different hardware; a test that compared them would fail every day for
reasons nobody broke. `backend_type` is likewise excluded - it is the one field that is
supposed to differ.

One detail that took a correction: `decode_ms = 0` is a measurement, not an absence. An
integer milliseconds field reports 0 for a sub-millisecond window; `None` is what the
decoder produces when a worker never sent the field. Treating 0 as "missing" failed every
fast synthetic run.

### What the first run found

```
cpu:  64 tokens, stop=limit, produced=64, backend_type=0, slots=2
[PASS] cpu: run 2 byte-identical to run 1
cuda: 64 tokens, stop=limit, produced=64, backend_type=1, slots=2
[PASS] cuda: run 2 byte-identical to run 1
[PASS] cpu vs cuda: identical token stream and counters (timing differs, as it should)
[PASS] 2 backends agree on the probe; the boundary behaves the same whichever kernel answered.
```

The token stream matched, and `backend_type` was wrong. `hypercore_engine_get_caps()` had
`full.backend_type = 1;` hard-coded, so every artifact - including a CPU-only one - told
its client it was running on a CUDA card. The header defines the field as
`0 = cpu, 1 = cuda, 2 = hip`, and it is the one capability field a client reads without
cross-checking anything else.

The fix states the backend where it is actually known. `CMakeLists.txt` now emits a
definition for the tree it is configuring:

```cmake
if(HYPERCORE_HIP_GFX906 OR HYPERCORE_ENABLE_HIP)
  add_compile_definitions(HYPERCORE_BACKEND_HIP=1)
elseif(HYPERCORE_ENABLE_CUDA)
  add_compile_definitions(HYPERCORE_BACKEND_CUDA=1)
endif()
```

and the bridge reads it. No flag means CPU. Rebuilding both trees gives `0` from the CPU
artifact and `1` from the CUDA one, which is the first time the two are distinguishable
from the wire.

### The comparison rules are tested without a second backend

`tools/test_backend_parity.py` (18 tests, all passing) covers the rules themselves: a
one-token drift is found and located, a length mismatch is a difference, timing is not,
`decode_ms=None` is flagged and `decode_ms=0` is not, a `produced_tokens` that disagrees
with the number of tokens actually delivered is caught, `backend_type` may differ and
`max_batch_slots` may not, a required-but-unbuilt backend exits 2 while an optional one is
skipped, and `capture()` is exercised end to end against `serve/frame_fixture.ScriptedWorker`
so the collection path is proven without a subprocess or a GPU.

### What this does not prove

There are no weights in this checkout (`pack/` is gitignored and absent), so the engine
spine that answers the probe is the deterministic one. This is parity of the boundary and
the spine, not of GGML kernel numerics against real tensors. The kernel-level comparison
still belongs to the pack-gated hardware guard in stage 4; the harness is the stage that
runs on a runner with no GPU at all.

```
$ python3 tools/backend_parity.py --backend cpu --require cpu --repeat 2
cpu: 64 tokens, stop=limit, produced=64, backend_type=0, slots=2
[PASS] cpu: run 2 byte-identical to run 1
[SKIP] only one backend was available; nothing to compare.
```

A single backend reports `[SKIP]`, not `[PASS]`: nothing was compared, and the harness says
so rather than implying a cross-backend result it did not measure. The CI stage adds
`backend-parity` between the supervisor tests and the model guard: the rules, then the
CPU determinism gate, then the cross-backend comparison only if a CUDA artifact was built
on that runner.


## 30. The load test now runs behind the key the server requires

The integration guard proved the slot gate and nothing else about the HTTP surface:
`serve/flood_stub.py` answered `/health`, `/v1/slots` and `/infer/stream` with no credential
check, while `serve/server.py` required one whenever `api_key` was set. A green stub run
therefore said nothing about the auth path a customer's request actually takes. Two copies
of the same rule also drift in the way rules do: one front accepts `Bearer`, the other only
`bearer`; one compares in constant time, the other does not.

The rule is now one function, `serve/http_auth.py`, and both fronts call it:

| request | key configured | result |
|---|---|---|
| no key configured at all | no | open - this is a machine-local server first |
| `Authorization: Bearer <key>`, any case, any spacing | yes | 200 |
| `x-api-key: <key>` | yes | 200 |
| both headers present | yes | `Authorization` wins; a stale `x-api-key` is not a second credential |
| nothing, empty, or wrong | yes | 401 `{"error": {"type": "authentication_error", ...}}` |
| `GET /health` | yes or no | 200 - a monitoring probe has no key, so health is never gated and says whether one is required |

`key_matches` is `hmac.compare_digest`, and the header lookup is case-insensitive whether it
is handed `http.client.HTTPHeaders` or a plain dict, because the gate is called from a
request handler, from the stub, and from tests.

The wiring is asserted, not assumed. `serve/test_http_auth.py` (14 tests, all passing) checks
that `serve.server.key_matches` and `serve.flood_stub.key_matches` are the *same function
object* as `serve.http_auth.key_matches`, then drives the stub over real HTTP with a scripted
supervisor: an unauthenticated `/infer/stream` returns 401 and `supervisor.reached_queue` is
still 0, so a refused request never occupies a slot and never appears in the in-flight count.

The same gate, on the real server with the mock engine and `--api-key live-gate-key`:

```text
GET /v1/models                        -> 401 {"error": {"type": "authentication_error", ...}}
GET /v1/models  Authorization: Bearer live-gate-key -> 200
GET /v1/models  x-api-key: live-gate-key            -> 200
GET /health                           -> 200 {"status": "ok", ..., "api_key": true}
```

`tools/bench_flood.py` gained `--api-key`, which is passed to the front it spawns and used
for every client. When a key is set, the guard asserts the gate before it floods, so the CI
stage proves two things in one run:

```text
$ python3 tools/bench_flood.py --concurrency 12 --slots 4 --api-key ci-boundary-key
 FLOOD: 12 clients against a 4-slot worker
 auth: key required (11 chars)
[PASS] auth gate: no key 401, key 200 - the same rule the server uses
 dispatched              : 12
 completed streams       : 2
 503 from the slot gate : 8
 client hung up         : 2
 in-flight after settle  : 0
[TEST PASSED] load shedding and slot reclamation behaved.
```

### One red test on the way, and what it was actually about

`serve.test_frontend` was failing before this change: the HyperCore rename moved
`HYPERCORE_KEEP_EMPTY_TURNS` to `HYPERCORE_KEEP_EMPTY_TURNS` in `serve/frontend.py` but left the
test patching the old name, so the assertion that the flag restores the old prompt could not
be true. The fix is not just the test. A machine that still exports the old name should not
silently change its prompt, so `serve/frontend.py` reads both spellings
(`KEEP_EMPTY_TURNS_FLAGS`), and the test now covers: no flag, `=0`, the new name, and the
old one. 10 tests pass.

## 31. `install.sh`: the pipeline is a script, not only a workflow

A CI job that nobody can reproduce locally is a claim, not a gate. `install.sh` runs the same
five stages as `.github/workflows/boundary.yml`, in the same order, on the build host:

| stage | what it runs | needs |
|---|---|---|
| `contract-lock` | configure + build `hypercore_api` and `hypercore-worker`, `check_abi_alignment.py --json`, `test_glibc_floor`, `glibc_floor.py --require 2.39` on the artifact | compiler, cmake, python |
| `supervisor-tests` | the seven supervisor suites, then the stub flood behind an API key | nothing else |
| `backend-parity` | the parity rules, the determinism gate, and cross-backend parity only if a CUDA tree exists | a second tree for the second half |
| `model-guard` | `bench_flood.py --model`, only when `pack/full` is present and non-empty | the weights |
| `cross-toolchain` | `daytona_bridge_test.py`, only when `DAYTONA_API_KEY` is set | the sandbox |

Two properties matter more than the flags:

* **A stage cannot pass on its last command.** Each stage is a list of `step` calls, and the
  first failing step returns from the stage. Before this, a stage ended with `return 0` and
  reported PASS even when a test in the middle of it had failed - the exact shape of the bug
  the ABI work exists to prevent.
* **A skip is reported as a skip.** The model guard and the cross-toolchain stage print why
  they did not run. `--model-guard` and `--cross-toolchain` turn those skips into failures, so
  a run that claims to have tested the pack or the foreign toolchain cannot quietly not do it.

The script ends by installing the boundary: `cmake --install` puts the library and the public
header under `dist/`, and `hypercore-worker` (which CMake has no install rule for) is placed
next to the library it links against.

```text
$ ./install.sh --jobs 4
...
  stage_contract_lock PASS
  stage_supervisor_tests PASS
  stage_backend_parity PASS
  stage_model_guard  PASS          # skipped: no pack/full on this checkout
  stage_cross_toolchain PASS       # skipped: DAYTONA_API_KEY not set
  stage_install      PASS
all stages passed: the boundary is built, byte-locked, and load-gated.
```

With the key present, stage 5 ran against the live sandbox through the same script:

```text
sandbox: 395543fc-...  artifact: 2703528 bytes
header-only compile: ok
mirror drift check: ok
sandbox_libc: ldd (Debian GLIBC 2.41-12+deb13u4) 2.41
[INFO] libhypercore_api.so.0.1.40: glibc floor 2.38
remote_c_fail=0
```

One thing this exposed rather than solved: `serve.test_slots.TelemetryContractTest.test_prompt_timing_does_not_move_with_the_draft_cycle` asserts a 150 ms difference between two scripted timings and failed once at 156 vs 157. The gate is sound, the test's margin is not - section 32 fixes it.

## 32. A test that measures a wall clock is flaky by construction; the margin was the bug

The comparison in that test was written as a difference between two measured windows:

```python
self.assertGreaterEqual(drafted["decode_ms"], plain["decode_ms"] + 150)
```

`time.sleep()` is a lower bound, every window is an `int()` floor of a wall clock, and the
fixture's emit loop sleeps 1 ms per token - six sleeps the scheduler handles differently in
each run. Two such runs have no stable difference to assert on, which is why 156 against 157
was not a boundary failure but a measurement artefact.

The assertion now bounds each window against the schedule the fixture was told to run, which
is what the test is actually about:

```python
PREFILL_MS, DRAFT_MS = 50, 150
FLOOR_MS = 2                       # int() truncation, one per window compared
assert drafted["prefill_ms"] >= PREFILL_MS - FLOOR_MS
assert drafted["prefill_ms"] <  PREFILL_MS + DRAFT_MS   # prompt did not absorb the lookahead
assert drafted["decode_ms"]    >= DRAFT_MS - FLOOR_MS   # the draft is charged to decode
assert plain["decode_ms"]      <  DRAFT_MS              # and is absent when it never ran
assert drafted["ttft_ms"]      >= PREFILL_MS + DRAFT_MS - FLOOR_MS
```

A window can only be longer than the sleep that produced it, so a lower bound derived from the
schedule is not a guess. It is also a stronger test: the old form could not distinguish "the
draft is in decode_ms" from "both runs were slow".

```text
$ for i in 1 2 3 4 5; do python3 -m unittest serve.test_slots.TelemetryContractTest.test_prompt_timing_does_not_move_with_the_draft_cycle; done
OK OK OK OK OK
```

## 33. `listener.stop()` could not wake its own reader, so every teardown cost 5 seconds

Timing the suites showed `supervisor.stop()` taking 5.209 s for a request that ran in 0.209 s.
`HyperCoreIPCListener.stop()` set `dead` and then joined the reader thread, but that thread is
inside `recv()` and the loop only checks `dead` between frames, so the join always ran out its
timeout:

```text
start 0.001
stream 0.209
stop  5.209        # before
stop  0.000        # after
```

The reader is woken by closing its own read side before the join:

```python
def stop(self) -> None:
    self.dead.set()
    if self._thread is None:
        return
    try:
        self._sock.shutdown(socket.SHUT_RD)
    except OSError:
        pass  # the worker may already have closed the link; the join still works
    self._thread.join(timeout=5.0)
    self._thread = None
```

The 5 s join stays as a safety net for a socket that will not answer; it is no longer the
normal path. This is not only a test-runtime matter: the restart budget counts attempts, and
what the HTTP server and the watchdog observe is seconds. `serve/test_fatal_recovery.py` now
asserts the bound:

```text
$ python3 -m unittest serve.test_fatal_recovery
Ran 5 tests in 0.008s
OK
```

The supervisor suites run the same 57 tests in about 10 s instead of 35.5 s, and the
integration guard settles in 0.7 s.
