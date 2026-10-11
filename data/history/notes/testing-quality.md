# How the code is tested

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
