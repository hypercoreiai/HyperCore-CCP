# Testing and code quality

Accumulated from 3 transcripts, 9 entries. Built 2026-10-11. Newer chats append here; within a section the entries are grouped by the thing they are about, newest statement first.


## Current state

Maintained by hand; the builder keeps it in place.

**Tests are stdlib unittest, run as modules.** `python3 -m unittest serve.test_server` — there is
no test runner dependency. `serve/test_*.py` covers the server and the engine adapters;
`tools/test_*.py` covers setup, the MCP servers and the harnesses.

**Nothing in a test touches a real GPU.** `serve/frame_fixture.py`'s `ScriptedWorker` is a
in-process stand-in for the worker that speaks the frame protocol: it accepts a submit, emits
token frames after a configurable prefill delay, and sends a terminal summary. `serve/fixtures/
legacy_engine.py` does the same for the older engine interface. A test that needs the real binary
is a contract test (`tools/test_abi_contract.py`), and it is run separately.

**Mocking is by patching the function, not the process.** `tools/test_setup_golden.py`'s `install()`
patches `gpus`, `ram_gb`, `cpu_info`, `is_wsl`, `data_folder`, `load_settings`, `save_settings`
and `subprocess.call`, then calls `setup.main()` and returns the exit code, the printed text, the
config that was written and the questions asked. `quiet()` swallows the output so a test can
assert on it.

**Golden baselines are recorded, not hand-written.** `tools/test_setup_golden.json` holds the
expected config for 25 machine profiles (RAM × GPU count × model). When a change to setup
legitimately changes what a config contains, the baseline is re-recorded with
`python3 tools/test_setup_golden.py --write` and the diff is inspected before accepting it — that
is how the host/api_key/turn_tail_check defaults were verified to be the only change.

**Lint is advisory, not a gate.** `ruff check` is run on changed files and the pre-existing
findings are separated from the new ones; a change is accepted only if it adds no new finding.


## What is true now

how the thing works, as the chats established it


**--turn-tail-check**
- `tools/test_setup_config.py`: new `ServerDefaults` class (new install gets all three; `--host 127.0.0.1 --api-key s3cret --no-turn-tail-check` wins; an existing config keeps its own values; the run script carries `--turn-tail-check` and honours a config that turns it off).
  <sub>2026-10-11 · hypercore-chat-2026-10-11-13-20.md</sub>

**prompts/**
- `serve/test_prompts.py`: the shipped-file test now uses `find_prompt_file(ROOT)`, and a new test covers the search order (root wins over `prompts/`, and neither → the "is not there" error).
  <sub>2026-10-11 · hypercore-chat-2026-10-11-11-46.md</sub>

**serve/test_prompts.py**
- (`serve/test_prompts.py` had the same wrong path, which is why `test_the_real_prompt_json_offers_the_shipped_profiles` was failing.) Fix — resolve the file instead of assuming where it is:
  <sub>2026-10-11 · hypercore-chat-2026-10-11-11-46.md</sub>

**window.hypercore_api_key**
- A server started with a key now injects `window.HYPERCORE_API_KEY` into the page it serves, so the chat UI works without typing the key into Settings (`serve/test_server.py::WebApp` covers it).
  <sub>2026-10-11 · hypercore-chat-2026-10-11-13-20.md</sub>

## Decisions taken

what was chosen, and why, oldest first


**py_compile**
- `node --check serve/web/app.js` ok; `py_compile` clean; ruff reports nothing on any changed line (3 pre-existing findings elsewhere).
  <sub>2026-10-11 · hypercore-chat-2026-10-11-11-46.md</sub>

**serve.test_abi_contract**
- Verification: `serve.test_turn_tail`, `serve.test_monitor_fields`, `serve.test_runconfig`, `serve.test_web_client`, `serve.test_server`, `serve.test_stream_loop`, `serve.test_parallel`, `serve.test_fatal_recovery`, `serve.test_lifecycle`, `serve.test_engine_process`, `serve.test_abi_contract`, `serve.test_slots` — 322 tests, all green; ruff clean on the changed files.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-11-46.md</sub>

**test added serve**
- Test added: `serve/test_server.py AmdTelemetry.test_pcie_link_is_the_narrowest_slowest_hop`.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-14-18.md</sub>

**tools test_setup_golden write**
- `tools/test_setup_golden.py --write` re-recorded: across all 25 PC profiles the only config difference is those three keys, nothing else changed.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-13-20.md</sub>

## Gotchas

things that bit once and will bite again


**exe002**
- A mock-engine server started with the default path now serves all four profiles: `ruff` and `mypy` on the changed files report nothing new (only the pre-existing `EXE002` executable-bit warning).
  <sub>2026-10-11 · hypercore-chat-2026-10-11-11-46.md</sub>
