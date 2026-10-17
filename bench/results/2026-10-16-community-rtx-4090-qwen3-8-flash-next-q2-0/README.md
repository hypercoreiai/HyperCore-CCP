# Community benchmark on NVIDIA GeForce RTX 4090

Measured on 2026-10-16 with `tools/hypercore_bench.py` (suite 1, 3 runs per test, medians with ranges). Speeds are the engine's own timings; first-token times are measured by the client over HTTP. Speed only: no correctness check was run.

## Hardware and software

- GPU and VRAM: NVIDIA GeForce RTX 4090, 24 GiB VRAM
- CPU: Intel(R) Core(TM) i9-14900KF (24 cores, 32 threads); installed RAM: 30.5 GiB; storage: not measured
- OS: Linux 7.0.0-38-generic; GPU driver: 615.71.09; CUDA: not read
- HyperCore: project 0.1.42, commit 14a43548; engine hypercore-worker
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
| short chat | 46 (43-51) | 0 | 100 (100-100) | 9 | not measured | 96.9 (60.7-106.3) | 0.64 (0.49-1.00) |
| 4K prompt, fresh | 4019 (4019-4019) | 0 (0-0) | 24 cap | 3 | 2804.6 (2461.1-2810.5) | not measured | 1.74 (1.68-2.05) |
| 16K prompt, fresh | 16058 (16058-16058) | 0 (0-0) | 24 cap | 3 | 3871.3 (3695.7-3879.7) | not measured | 4.40 (4.36-4.62) |
| agent session, follow-up turns | 13641 (13627-13646) at the last turn | see below | up to 64 | 3 | see below | 74.1 (30.3-153.1) | 1.40 (1.20-2.08) |

Ranges are the lowest and highest of the runs; `Runs` counts requests that returned a token.

### Agent session (conversation cache)

Cache hit over the follow-up turns: 90.2 % (90.2-90.3); earlier-turn tokens read again per session: 20 (20-27) (earlier turns that the cache did not hold; the 4104 (4104-4104) new tokens of the files are read once); first turn (nothing cached) first token: 0.95 s (0.93-0.99).

| Turn (run 1) | Prompt tokens | Reused | Read | Prompt tok/s | First token (s) | Decode tok/s |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 609 | 626 | 62 | 150.1 | 0.99 | 40.0 |
| 1 | 3074 | 602 | 2472 | 1593.8 | 2.084 | 67.9 |
| 2 | 4607 | 3137 | 1470 | 1196.1 | 1.635 | 88.9 |
| 3 | 7981 | 7994 | 63 | 153.3 | 1.839 | 30.3 |
| 4 | 10788 | 10792 | 63 | 172.6 | 1.704 | 54.1 |
| 5 | 13641 | 13642 | 63 | 200.6 | 1.638 | 66.7 |

Per-request data: `results.json`. Engine log lines from the start: `engine-log-excerpt.txt` (when this run started the server).

## Correctness and limitations

Not measured: this is a speed suite. The conversation uses the model's own replies, so token counts differ a little between runs. Machine details come from the server, `nvidia-smi`/`rocm-smi` and the OS; background load and power limits are not recorded. Total time of the suite: 67 s.
