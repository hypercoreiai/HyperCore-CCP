# Setup, run configs and defaults

Accumulated from 4 transcripts, 11 entries. Built 2026-10-11. Newer chats append here; within a section the entries are grouped by the thing they are about, newest statement first.


## Current state

Maintained by hand; the builder keeps it in place.

**Entry point.** `./setup.sh` (Linux) or `START-HERE.bat` (Windows) is the only thing a user
needs to run. It finds or creates `.venv`, installs the packages, gets or builds the engine,
writes `hypercore-<model>.json` and `run-<model>.sh`/`.bat`, and starts the server. A second
run does not reinstall; it just starts.

**Defaults written by setup (since 2026-10-11).** Every run config setup writes now carries:

- `"host": "0.0.0.0"` — the server answers to the other devices on the network
- `"api_key": "0000"` — a placeholder key, so a default install is not wide open
- `"turn_tail_check": true` — the end-of-turn completion check is on

`run-<model>.sh`/`.bat` passes `--turn-tail-check` accordingly. `--host`, `--api-key` and
`--no-turn-tail-check` override them; a model whose config already sets one keeps it. The
defaults are filled in only where the key is absent (`apply_server_defaults` in `setup.py`),
and a config written by an older setup gets them on its next start.

**Run configs are the source of truth for a model.** `hypercore-<model>.json` holds the engine
path, the engine args, the tokenizer, the log path, the port, the GPU selection, and the
server-side settings (`api_key`, `host`, `cors_origins`, `open_browser`, `reasoning_effort`,
`turn_tail_check`, `sampling.*`). Keys setup does not write are carried over when setup runs
again (`carry_over`), and the previous file is kept as `.bak`.

**Two config paths are checked before anything else:** `--config` on the command line, then
`hypercore-<model>.json` beside the server. `find_prompt_file` follows the same rule for the
agent profiles.


## What is true now

how the thing works, as the chats established it


**--turn-tail-check** · 2 chats
- Opt-in via `--turn-tail-check` or `"turn_tail_check": true`; the question text is overridable with `--turn-tail-prompt` / `turn_tail_prompt`.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-11-46.md</sub>
- One caveat: the turn-tail check is off by default — the running server was started without `--turn-tail-check`, so it won't fire until you add the flag or set `"turn_tail_check": true` in the profile.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-11-46.md</sub>

**./setup.sh**
- `./setup.sh` (which execs `setup.py`) now writes those three defaults into every run config and run script it generates.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-13-20.md</sub>

**/health**
- Live state: pid 793996 on port 8081, started from `run-q2_0.sh` with `--host 0.0.0.0 --turn-tail-check`; `/health` reports `api_key: true`, and a streamed request emitted `tail_check {"result":"continue","checks":1,"max_checks":3}`, so the turn-tail check is active.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-13-20.md</sub>

**build/hypercore-worker**
- `tools/calibrate.py hypercore-q2_0.json` exits with `WorkerUnreachable: worker exited during startup (1)`, and running `build/hypercore-worker` standalone gives `engine init failed (-5)` because the live server (pid 834276, port 8081) holds the GPU.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-13-20.md</sub>

**calls means round1**
- Hmm, calls==3 means: round1 (WORK) → not done → check round 2 (IGNORED) → text empty → `tail_is_done("")` False → then the guard `not (svc.turn_tail_check and checks < ...
  <sub>2026-10-11 · hypercore-chat-2026-10-11-11-46.md</sub>

**settings.json**
- That needs a machine where the CMake configure step is allowed: rebuild, then `./setup.sh --calibrate` to write the pcie-frac and adapt sweep into `settings.json`.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-14-18.md</sub>

**turn_tail_checks**
- A yes/confirmation ends the turn; a no, an unanswered question, or more work keeps it open and the model continues — up to `turn_tail_checks` (default 3, capped 10) per turn.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-11-46.md</sub>

**window.hypercore_api_key**
- A server started with a key now injects `window.HYPERCORE_API_KEY` into the page it serves, so the chat UI works without typing the key into Settings (`serve/test_server.py::WebApp` covers it).
  <sub>2026-10-11 · hypercore-chat-2026-10-11-13-20.md</sub>

## Decisions taken

what was chosen, and why, oldest first


**hypercore-q2_0.json**
- What survives unchanged: the gate behaviour, the per-engine decisions, the stale `HYPERCORE_ROUTE_TAIL_SKIP=0` in `hypercore-q2_0.json` (confirmed present, and `grep -c "tail skip is on"` on the current log returns 0, so it is still in effect despite the 15:38 run preferring the default), and the recommendation to raise `SWEEP_ROUNDS` or `MIN_GAIN` in `tools/calibrate.py`.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-15-51.md</sub>

**setup.py**
- What changed in `setup.py` `SETUP_KEYS` now includes `turn_tail_check`, so a setup rerun does not drop it.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-13-20.md</sub>
