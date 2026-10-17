# Community benchmark on NVIDIA GeForce RTX 4090

Measured on 2026-10-17 with `tools/hypercore_bench.py` (suite 1, 3 runs per test, medians with ranges). Speeds are the engine's own timings; first-token times are measured by the client over HTTP. Speed only: no correctness check was run.

## Hardware and software

- GPU and VRAM: NVIDIA GeForce RTX 4090, 24 GiB VRAM
- CPU: Intel(R) Core(TM) i9-14900KF (24 cores, 32 threads); installed RAM: 30.5 GiB; storage: not measured
- OS: Linux 7.0.0-38-generic; GPU driver: 615.71.09; CUDA: not read
- HyperCore: project 0.1.42, commit efae8507; engine hypercore-worker
- Background workloads and power limits: not recorded

## Model and configuration

- Model and quantization: qwen3.8-flash-next-q2_0
- Context: 131072 tokens; parallel slots: 1
- Settings: the install's own configuration, unchanged; thinking off for the suite; temperature 0

```text
hypercore --pack q2_0 --native Qwen3.8-Flash-Next-GSQ-RCO-Q2_0-<key>1-of-<key>2.gguf --ple-gguf Qwen3.8-Flash-Next-GSQ-RCO-Q2_0-<key>2-of-<key>2.gguf --expert-profile expert-profile.bin --expert-cache auto --prefill auto --spec 4 --mtp rt --max-context 131072 --kv int8 --resident-experts --control-vector-scaled Qwen3.8-Flash-Next-experimental-speed-projection.gguf:1.0 --control-vector-layer-range 4 44 --cvec-mode project --cvec-dir per-layer --pcie-frac 0.75 --spec-min-p 0.30
```

## Method

Run by `python tools/hypercore_bench.py` against the HTTP API of a HyperCore server (started by the benchmark from the install configuration); model loading is not timed. One warm-up chat and a 1K prompt are discarded first. Every prompt starts with a unique tag, so the conversation cache cannot help the fresh-prompt tests.

- short chat: the three questions of `tools/ab_engine.py`, up to 100 new tokens, 3 runs
- 4K / 16K prompts: generated word lists sized by a calibration request, 24 new tokens, 3 fresh prompts each
- agent session: system prompt and four tools, then 5 turns that each add about 1500 words of a project file and continue from the model's own earlier answers (the way agent clients resend a conversation), 64 new tokens per turn, 3 sessions; the cache numbers come from the answer's usage (`cached_tokens`) and timings (`prompt_n`)
- concurrency (when run): N requests sent at the same moment, total tokens over the wall time of the burst, latency over all requests

## Results

| Configuration | Actual prompt tokens | Reused tokens | Generated tokens | Runs | Prompt tok/s median and range | Decode tok/s median and range | TTFT seconds median and range |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| short chat | 46 (43-51) | 0 | 100 (100-100) | 9 | not measured | 100.3 (70.8-121.4) | 0.55 (0.43-0.72) |
| 4K prompt, fresh | 4019 (4019-4019) | 0 (0-0) | 24 cap | 3 | 2794.9 (2473.2-2822.3) | not measured | 1.74 (1.65-1.98) |
| 16K prompt, fresh | 16058 (16058-16058) | 0 (0-0) | 24 cap | 3 | 3997.5 (3816.1-4023.6) | not measured | 4.26 (4.22-4.44) |
| agent session, follow-up turns | 13689 (13636-13744) at the last turn | see below | up to 64 | 3 | see below | 132.2 (46.5-176.5) | 1.36 (1.03-2.02) |

Ranges are the lowest and highest of the runs; `Runs` counts requests that returned a token.

### Agent session (conversation cache)

Cache hit over the follow-up turns: 90.0 % (90.0-93.8); earlier-turn tokens read again per session: 90 (19-99) (earlier turns that the cache did not hold; the 4144 (2777-4200) new tokens of the files are read once); first turn (nothing cached) first token: 0.94 s (0.93-1.08).

| Turn (run 1) | Prompt tokens | Reused | Read | Prompt tok/s | First token (s) | Decode tok/s |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 609 | 628 | 62 | 166.7 | 1.081 | 36.4 |
| 1 | 3076 | 602 | 2474 | 1626.6 | 2.017 | 92.5 |
| 2 | 4609 | 3069 | 1540 | 1260.2 | 1.6 | 113.5 |
| 3 | 7983 | 7996 | 63 | 198.7 | 1.8 | 57.1 |
| 4 | 10790 | 10783 | 103 | 408.7 | 1.648 | 132.2 |
| 5 | 13744 | 13737 | 119 | 463.0 | 1.756 | 145.8 |

Per-request data: `results.json`. Engine log lines from the start: `engine-log-excerpt.txt` (when this run started the server).

## Correctness and limitations

Not measured: this is a speed suite. The conversation uses the model's own replies, so token counts differ a little between runs. Machine details come from the server, `nvidia-smi`/`rocm-smi` and the OS; background load and power limits are not recorded. Total time of the suite: 69 s.
