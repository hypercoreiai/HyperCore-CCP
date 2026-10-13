# Community benchmark on NVIDIA GeForce RTX 4090

Measured on 2026-10-13 with `tools/hypercore_bench.py` (suite 1, 3 runs per test, medians with ranges). Speeds are the engine's own timings; first-token times are measured by the client over HTTP. Speed only: no correctness check was run.

## Hardware and software

- GPU and VRAM: NVIDIA GeForce RTX 4090, 24 GiB VRAM
- CPU: Intel(R) Core(TM) i9-14900KF (24 cores, 32 threads); installed RAM: 30.5 GiB; storage: not measured
- OS: Linux 7.0.0-38-generic; GPU driver: 615.71.09; CUDA: not read
- HyperCore: project 0.1.42, commit da4ecd10; engine hypercore-worker
- Background workloads and power limits: not recorded

## Model and configuration

- Model and quantization: qwen3.8-flash-next-q2_0
- Context: 262144 tokens; parallel slots: 1
- Settings: the install's own configuration, unchanged; thinking off for the suite; temperature 0

```text
hypercore --pack q2_0 --native Qwen3.8-Flash-Next-GSQ-RCO-Q2_0-<key>1-of-<key>2.gguf --ple-gguf Qwen3.8-Flash-Next-GSQ-RCO-Q2_0-<key>2-of-<key>2.gguf --expert-profile expert-profile.bin --expert-cache auto --prefill auto --spec 4 --mtp rt --max-context 262144 --kv q4_0 --resident-experts --control-vector-scaled Qwen3.8-Flash-Next-experimental-speed-projection.gguf:1.0 --control-vector-layer-range 4 44 --cvec-mode project --cvec-dir per-layer --spec-min-p 0.5
```

Environment of the config: `HYPERCORE_ROUTE_TAIL_SKIP=0`

## Method

Run by `python tools/hypercore_bench.py` against the HTTP API of a HyperCore server (started by the benchmark from the install configuration); model loading is not timed. One warm-up chat and a 1K prompt are discarded first. Every prompt starts with a unique tag, so the conversation cache cannot help the fresh-prompt tests.

- short chat: the three questions of `tools/ab_engine.py`, up to 100 new tokens, 3 runs
- 4K / 16K prompts: generated word lists sized by a calibration request, 24 new tokens, 3 fresh prompts each
- agent session: system prompt and four tools, then 5 turns that each add about 1500 words of a project file and continue from the model's own earlier answers (the way agent clients resend a conversation), 64 new tokens per turn, 3 sessions; the cache numbers come from the answer's usage (`cached_tokens`) and timings (`prompt_n`)
- concurrency (when run): N requests sent at the same moment, total tokens over the wall time of the burst, latency over all requests

## Results

| Configuration | Actual prompt tokens | Reused tokens | Generated tokens | Runs | Prompt tok/s median and range | Decode tok/s median and range | TTFT seconds median and range |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| short chat | 46 (43-51) | 0 | 100 (9-242) | 9 | not measured | 69.5 (61.5-90.5) | 0.56 (0.27-0.95) |
| 4K prompt, fresh | 4019 (4019-4019) | 0 (0-0) | 24 cap | 3 | 2828.3 (2415.3-2830.3) | not measured | 1.84 (1.75-1.99) |
| 16K prompt, fresh | 16058 (16058-16058) | 0 (0-16051) | 24 cap | 3 | 3897.6 (321.4-3919.5) | not measured | 4.43 (4.42-4.49) |
| agent session, follow-up turns | 13906 (13798-13945) at the last turn | see below | up to 64 | 3 | see below | 97.7 (70.4-116.4) | 1.59 (1.11-2.11) |

Ranges are the lowest and highest of the runs; `Runs` counts requests that returned a token.

### Agent session (conversation cache)

Cache hit over the follow-up turns: 86.7 % (80.4-92.7); earlier-turn tokens read again per session: 250 (130-288) (earlier turns that the cache did not hold; the 5461 (3225-7775) new tokens of the files are read once); first turn (nothing cached) first token: 1.00 s (0.95-1.12).

| Turn (run 1) | Prompt tokens | Reused | Read | Prompt tok/s | First token (s) | Decode tok/s |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 609 | 602 | 86 | 339.9 | 1.118 | 111.1 |
| 1 | 3055 | 3048 | 92 | 394.8 | 1.836 | 90.9 |
| 2 | 4638 | 3048 | 1590 | 1214.7 | 1.705 | 88.3 |
| 3 | 8011 | 4631 | 3380 | 1928.1 | 2.11 | 82.2 |
| 4 | 10867 | 10885 | 63 | 295.8 | 1.928 | 93.3 |
| 5 | 13798 | 10860 | 2938 | 1888.2 | 1.942 | 102.1 |

Per-request data: `results.json`. Engine log lines from the start: `engine-log-excerpt.txt` (when this run started the server).

## Correctness and limitations

Not measured: this is a speed suite. The conversation uses the model's own replies, so token counts differ a little between runs. Machine details come from the server, `nvidia-smi`/`rocm-smi` and the OS; background load and power limits are not recorded. Total time of the suite: 83 s.
