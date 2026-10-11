# Deployment, paths and permissions

Accumulated from 42 transcripts, 147 entries. Built 2026-10-11. Newer chats append here; within a section the entries are grouped by the thing they are about, newest statement first.


## Current state

Maintained by hand; the builder keeps it in place.

**Two users.** `ai-user0` owns the work; `ai-agent` is the account the MCP servers run as. The
sudoers grant for `ai-agent` was a no-op (`ai-agent ALL=(ai-agent) NOPASSWD: ALL`) until real
entries were added. Groups now include `dev`, `docker`, `user0`, `systemd-journal`.

**`/home` itself is not writable.** Only `/home/<user>/…` is. Anything that defaults to a cache
or output path under `/home` fails: ruff wanted `/home/.ruff_cache`, pytest wanted a basetemp,
`docs__create_file` with a relative path resolved to `/home`. The fix is always to default to a
per-user directory, not to grant write on `/home`.

**The GPU box is `192.168.74.2`; the client is on the same LAN.** MCP servers that need to be
reachable from a container run as streamable HTTP on their own port (the scrape server on 8766)
over the `ai-bridge` Docker network. There is no nginx on this host, so nginx rules in config
files are inert.

**The server is started by the run script, not by a service manager.** `restart.sh status|stop|start
<model>` is the operational entry point; it finds the pid by matching `serve/server.py` and the
port. A config change takes effect only after that restart — this is the single most common cause
of "I changed it and nothing happened".

**Git ownership.** Repos owned by `ai-user0` but accessed by `ai-agent` produce "dubious
ownership"; the fix is `git config --global --add safe.directory <path>`, not chown.


## What is true now

how the thing works, as the chats established it


**/home** · 4 chats
- `/home` root is not writable, so it lives under `ai-user0`.
  <sub>2026-10-07 · strata-chat-2026-10-07-17-37.md</sub>
- The default cache/target paths point at a non-writable root. `/home` itself is not writable, only `/home/user0/…`.
  <sub>2026-10-03 · strata-chat-2026-10-03-18-25.md</sub>
- `docs__create_file` path default is the main bug. Relative paths resolve against `/home`, which is not writable, so the most natural call (`path: "notes.md"`) fails with `[Errno 13] Permission denied`.
  <sub>2026-10-03 · strata-chat-2026-10-03-15-05.md</sub>
- directly under `/home`, which is not writable — the same permission wall that made `docs__create_file` fail on `tool_test/notes.md`.
  <sub>2026-10-03 · strata-chat-2026-10-03-15-05.md</sub>

**/home/.ruff_cache** · 2 chats
- Workaround: run it directly — `RUFF_CACHE_DIR=/home/user0/.ruff_cache /home/user0/.pyenv/versions/3.12.9/bin/python3 -m ruff check …` (the default `/home/.ruff_cache` is not writable).
  <sub>2026-10-03 · strata-chat-2026-10-03-18-25.md</sub>
- As ai-agent: writes to `/home/user0/.terminal/`, `/home/projects/`, and `/home/.ruff_cache` all succeed; `sudo -n apt-get update` succeeds.
  <sub>2026-10-03 · strata-chat-2026-10-03-18-25.md</sub>

**/home/ai-agent/strata** · 2 chats
- One correction to the target path: there is no `/home/ai-agent/Strata` — the framework lives at `/home/ai-user0/Strata` (that's the path `mcp.yaml` resolves `serve/mcp/.py` against, and `ai-agent` already has write access there — `serve/assist_fast_models.json` and `serve/assist_latency_report.txt` are owned by `ai-agent`).
  <sub>2026-10-09 · strata-chat-2026-10-09-11-32.md</sub>
- `git status` in `/home/ai-agent/Strata` works — no "dubious ownership"
  <sub>2026-10-03 · strata-chat-2026-10-03-18-59.md</sub>

**/home/ai-user0/strata** · 2 chats
- And confirm the live `/home/ai-user0/Strata` keeps its old names so PID 1552343 keeps running.
  <sub>2026-10-10 · strata-chat-2026-10-10-05-20.md</sub>
- 6 failures are identical in the untouched archive `/home/ai-user0/Strata` (verified side-by-side): `test_download_auth` ×5 (no network/HF token here) and `test_amd_is_not_asked` (`/usr` not writable).
  <sub>2026-10-10 · strata-chat-2026-10-10-05-20.md</sub>

**/home/user0/.terminal/cache** · 2 chats
- `RUFF_CACHE_DIR` fixes the "Failed to initialize cache at /home/.ruff_cache: Permission denied" failure — `/home/user0/.terminal/cache` is writable by both user0 and ai-agent.
  <sub>2026-10-03 · strata-chat-2026-10-03-18-25.md</sub>
- `RUFF_CACHE_DIR` points at `/home/user0/.terminal/cache`, which is writable by both users — the ruff cache failure is gone.
  <sub>2026-10-03 · strata-chat-2026-10-03-18-25.md</sub>

**/usr/bin/docker** · 2 chats
- `docker` is granted nowhere. Docker is installed and the daemon is running, but `ai-user0` is not in the `docker` group (`id -Gn` → `adm redis postgres systemd-journal dev-sandbox`) and `/usr/bin/docker` isn't in sudoers — so `docker ps` fails with "permission denied ...
  <sub>2026-10-05 · strata-chat-2026-10-05-20-19.md</sub>
- Either add `/usr/bin/docker` to the grants or `usermod -aG docker ai-user0` (needs real root).
  <sub>2026-10-05 · strata-chat-2026-10-05-20-19.md</sub>

**192.168.74.2** · 2 chats
- The server runs on the GPU box (`192.168.74.2`) so it can bind UDP `33740`, heartbeat the console on `33739`, and call Ollama at `127.0.0.1:11434`.
  <sub>2026-10-04 · strata-chat-2026-10-04-06-37.md</sub>
- It runs as streamable HTTP on port 8766 on the GPU box (`192.168.74.2`) so the AnythingLLM container can reach it over the `ai-bridge` Docker network.
  <sub>2026-10-03 · strata-chat-2026-10-03-14-03.md · also in strata-chat-2026-10-03-14-03.md</sub>

**_read_path** · 2 chats
- `_writable` now returns a writable sibling with the content copied, so a read-only file can't empty the dropdown, and `_read_path` picks the newest existing copy for reading.
  <sub>2026-10-10 · strata-chat-2026-10-10-07-17.md</sub>
- `serve/assist.py` now resolves one path per process (`_writable` → `_read_path`), prefers a file every account can write, and `chmod`s the file it picks to 666 so the next account converges on it instead of creating a second list.
  <sub>2026-10-09 · strata-chat-2026-10-09-15-05.md</sub>

**ai-agent** · 2 chats
- (b) Two allowlist files, owned by two accounts, drifting apart. `serve/assist_fast_models.json` is `ai-agent`-owned 0644 (10 pinned, 12:23); `Strata/assist_fast_models.json` is `ai-user0`-owned (13 pinned, 14:42).
  <sub>2026-10-09 · strata-chat-2026-10-09-15-05.md</sub>
- `ai-user0` cannot write the `ai-agent` file, so the divergence is a filesystem-permission fact, not a code bug.
  <sub>2026-10-09 · strata-chat-2026-10-09-15-05.md</sub>

**ai-user0** · 2 chats
- One ownership note: `README.md` and `docs/media/header_readme.jpg` are owned by `user0`, not `ai-user0`, and `sudo chown` is refused by the sandbox.
  <sub>2026-10-10 · strata-chat-2026-10-10-19-47.md</sub>
- That's fine for a report, but if you want the agent to revise it in place, it needs to be writable by `ai-user0` (it already is, as owner).
  <sub>2026-10-06 · strata-chat-2026-10-06-18-22.md</sub>

**boundary.yml** · 2 chats
- What's left is external, not code: a workflow-scoped token so `boundary.yml` can land, and published releases so the README asset links resolve.
  <sub>2026-10-10 · strata-chat-2026-10-10-08-05.md</sub>
- `boundary.yml` stays in the working tree and is gitignored with the reason written in the file, so the gate isn't lost — it just can't land until a token with the `workflow` scope exists.
  <sub>2026-10-10 · strata-chat-2026-10-10-07-17.md</sub>

**docker** · 2 chats
- `serve/mcp/web-scrape-mcp/tests` fails collection with `ModuleNotFoundError: No module named 'webscrape'` — that's the containerised HTTP scraper, not installed (and `docker` is still absent).
  <sub>2026-10-05 · strata-chat-2026-10-05-20-19.md</sub>
- Similarly, Tier 3 (`jq`, `sqlite3`, `docker`, `gdb`) is on the allowlist but has no dedicated tool — `run` is enough for them, since they are single-purpose binaries rather than things needing a custom report.
  <sub>2026-10-03 · strata-chat-2026-10-03-15-05.md</sub>

**--flag**
- I verified your numbers before answering, because the plan's credibility depends on them: `src/program/generate.cpp` is exactly 11,102 lines, `struct Options` spans 310–642 with 164 `--flag` handlers, `include/strata/` is 108 headers / 12,141 lines, and the core→kernels fan-out is real (22 `kernels/native`, 10 `kernels/s`, 9 `kernels/qsa`, 9 `kernels/kv`, 7 each quantize/elementwise/cpu-pool).
  <sub>2026-10-09 · strata-chat-2026-10-09-16-17.md</sub>

**.dockerignore**
- `.gitignore`, `.dockerignore`, `Makefile`, `LICENSE` write through the document tools; an extensionless ELF is still refused read and write.
  <sub>2026-10-10 · strata-chat-2026-10-10-07-17.md</sub>

**.pyenv**
- As ai-agent, `HOME=/home/ai-agent`, which has no `.pyenv`, so `terminal__status` reported only: With `PYENV_ROOT=/home/user0/.pyenv` set, it correctly returns 3.12.2, 3.12.9 and 3.13.13.
  <sub>2026-10-03 · strata-chat-2026-10-03-18-25.md</sub>

**.ssh/id_rsa**
- `serve/mcp/tests/test_docs.py::test_docs__create_secret` asserted `.ssh/id_rsa` can be created, while `serve/test_docs_mcp.py` asserts a credential is not a document.
  <sub>2026-10-10 · strata-chat-2026-10-10-07-17.md</sub>

**/assist/log**
- Assist calls in the Monitor — live and confirmed against the running server (pid 1087489, port 8081): `/assist/log` returns the endpoint, the pinned list, the 67 over-limit models with reasons, and 36 recorded calls.
  <sub>2026-10-09 · strata-chat-2026-10-09-15-05.md</sub>

**/etc/sudoers.d/ai-agent**
- For reference, `/etc/sudoers.d/ai-agent` only allows NOPASSWD for `apt-get`, `pip3 install`, nginx `systemctl`, the ruff_cache mkdir/chmod, and `visudo -c` — `sudo` with that password refuses anything else ("I'm sorry ai-agent.
  <sub>2026-10-03 · strata-chat-2026-10-03-18-59.md</sub>

**/etc/sudoers.d/ai-user0**
- The generated non-comment rule lines are byte-identical to the live `/etc/sudoers.d/ai-user0` (17 lines, `identical: True`).
  <sub>2026-10-05 · strata-chat-2026-10-05-23-31.md</sub>

**/health**
- Live: `python3 -m serve.hypercore_server --port 8125 --worker build-shared/hypercore-worker --socket /tmp/hc3.sock --config '{"batch":2}'` → `/health` 200, a 20-token completion streams and logs `[MONITOR] … decode_ms=39 tokens=20 drafts=20/100`, `/slots` returns the populated monitor, a dropped client issues `CMD_CANCEL` and `in_flight` returns to 0.
  <sub>2026-10-09 · strata-chat-2026-10-09-22-41.md</sub>

**/home/ai-agent**
- All non-Docker files that referenced `/home/user0` are now pointed at `/home/ai-agent`.
  <sub>2026-10-03 · strata-chat-2026-10-03-18-59.md</sub>

**/home/ai-agent/...**
- Read all five (`serve/mcp/web_mcp.py`, `serve/mcp/rag_mcp.py`, `serve/mcp/web_scrape_mcp.py`, `serve/terminal_mcp.py`, `serve/docs_mcp.py`) — the code is already `$HOME`-universal; every user-specific path is derived from `Path.home()` when the env var is unset: The non-universal part was `mcp.yaml`, which hard-coded `/home/ai-agent/...` and then `/home/ai-user0/...`.
  <sub>2026-10-05 · strata-chat-2026-10-05-20-19.md</sub>

**/home/ai-agent/.terminal/retest_report.json**
- The default report is `/home/ai-agent/.terminal/retest_report.json`.
  <sub>2026-10-04 · strata-chat-2026-10-04-06-01.md</sub>

**/home/ai-agent/strata/serve/test_docs_mcp.py**
- `/home/ai-agent/Strata/serve/test_docs_mcp.py` hardcoded `/home/user0/Strata/.venv/bin/python3` and the script path About the sudo password: it wasn't needed — everything was writable as `ai-agent` (the MCP files are owned by `ai-agent`, and `/home/user0/downloads` has an ACL granting `ai-agent` rwx).
  <sub>2026-10-03 · strata-chat-2026-10-03-18-59.md</sub>

**/home/ai-user0/.ssh/authorized_keys**
- (Correction to my earlier sweep: port 22 is open on `.9`; my `nc -z` check gave a false negative.) The likely source of the confusion: `/home/ai-user0/.ssh/authorized_keys` on this box contains a key for `[email]`.
  <sub>2026-10-07 · strata-chat-2026-10-07-17-37.md</sub>

**/home/ai-user0/.ssh/config**
- And `/home/ai-user0/.ssh/config` exists but is `root:root 600`, so ssh can't read it; harmless, but worth `chown` if you intended to use it.
  <sub>2026-10-07 · strata-chat-2026-10-07-17-37.md</sub>

**/home/ai-user0/lm-eval-bench/state.json**
- State is updated in `/home/ai-user0/lm-eval-bench/state.json` (loop 4, JSON verified, queue: install key → run suite → report).
  <sub>2026-10-07 · strata-chat-2026-10-07-17-37.md</sub>

**/home/ai-user0/lm-eval-bench/summarise_results.py**
- Artifact `/home/ai-user0/lm-eval-bench/summarise_results.py` (runs, prints the table above; ruff flags only a shebang-not-executable and import-order nit).
  <sub>2026-10-07 · strata-chat-2026-10-07-17-37.md</sub>

**/home/ai-user0/lm-eval-runs**
- Peer serves the model, harness runs here (preferred — I drive it, results land in `/home/ai-user0/lm-eval-runs`).
  <sub>2026-10-07 · strata-chat-2026-10-07-17-37.md</sub>

**/home/ai-user0/strata/ni_strata-q2_0.json**
- The text-only config exists here: `/home/ai-user0/Strata/ni_strata-q2_0.json` has no `"vision"` section, and `ni_run-q2_0.sh` starts it on the same port 8081.
  <sub>2026-10-05 · strata-chat-2026-10-05-23-36.md</sub>

**/home/ai-user0/strata_chats**
- One note: `/home/ai-user0/Strata_chats` is owned by `user0` with mode 755, so the agent user (`ai-user0`) cannot create files there directly — I wrote the document via `sudo cp`, so it is `root:root 644`.
  <sub>2026-10-06 · strata-chat-2026-10-06-18-22.md</sub>

**/opt/ai-workspace/.tmp/pytest-of-ai-user0**
- The 16 errors are an environment artifact — pytest's temp root `/opt/ai-workspace/.tmp/pytest-of-ai-user0` is owned by `ai-agent` and I can't remove it; with `TMPDIR=/tmp` those 18 web-scrape tests pass.
  <sub>2026-10-09 · strata-chat-2026-10-09-15-05.md · also in strata-chat-2026-10-06-23-05.md</sub>

**/tmp**
- Writes: `/tmp` inside WSL is writable but is cleared between `terminal` calls{{#if worktrees}}.
  <sub>2026-10-06 · strata-chat-2026-10-06-01-06.md · also in strata-chat-2026-10-06-01-06.md</sub>

**/tmp/repltest/.terminal/repl_driver.py**
- `tools/test_repl_loop.py` hard-codes `sys.path.insert(0, "/home/ai-agent/HyperCore")` and writes `/tmp/repltest/.terminal/repl_driver.py` at import — that directory belongs to another user, so it raises `PermissionError` during collection.
  <sub>2026-10-10 · strata-chat-2026-10-10-07-17.md</sub>

**/usr/bin/**
- `visudo` is at `/usr/sbin/`, not `/usr/bin/` — my sudoers rule used the wrong path.
  <sub>2026-10-03 · strata-chat-2026-10-03-18-25.md</sub>

**172.17.0.1**
- In the AnythingLLM storage `plugins/anythingllm_mcp_servers.json`: `172.17.0.1` is the Docker bridge to the host on Linux.
  <sub>2026-10-04 · strata-chat-2026-10-04-06-37.md</sub>

**192.168.74.3**
- Verified against `mcp.yaml` (lists its five top-level keys), `strata-q2_0.json`, `ps5-control/config.toml` (read `playstation.ip` = `192.168.74.3`), and the RAG index directly: Non-SELECT statements are refused (`DELETE` raises).
  <sub>2026-10-03 · strata-chat-2026-10-03-19-51.md</sub>

**192.168.74.9**
- `serve/web/app.js:161` polls it continuously; your dashboard at `192.168.74.9` was polling it every few seconds, which is why the identical traceback appears ~20 times.
  <sub>2026-10-10 · strata-chat-2026-10-10-12-04.md</sub>

**_cpuramfallback.__init__**
- The leak was genuine in the running server — `Telemetry.__init__` starts a daemon `_loop` thread and `_CpuRamFallback.__init__` calls `_times()` immediately, so every tick was leaking a handle.
  <sub>2026-10-06 · strata-chat-2026-10-06-23-05.md</sub>

**_strata_/engine/strata**
- Nothing else in the live system was touched: the server in `~/Strata` (PID 1552343, port 8081, HTTP 200) is still running, and I left `_Strata_/engine/strata` alone.
  <sub>2026-10-10 · strata-chat-2026-10-10-03-30.md</sub>

**_wait**
- HTTP-transport calls cannot be interrupted `serve/mcp/__init__.py:345-360`: the POST runs on a daemon thread and `_wait` raises `McpTimeout`/`McpCancelled` while that thread keeps running (with a hardcoded `timeout + 5` socket timeout).
  <sub>2026-10-06 · strata-chat-2026-10-06-14-10.md</sub>

**_writable assist falls**
- `_writable()` (assist.py:44) falls back to the copy this process can write, `_read_path()` (assist.py:80) reads whichever was written last, and `_write_shared()` (assist.py:87) mirrors the write — but only to copies it can write.
  <sub>2026-10-09 · strata-chat-2026-10-09-15-05.md</sub>

**allow_hosts**
- `allow_all_hosts: true` — lift the network restriction entirely: outbound access to any host over any protocol, so SSH, FTP, and raw sockets work too (unlike `allow_hosts`, which is HTTP/HTTPS-only).
  <sub>2026-10-06 · strata-chat-2026-10-06-01-06.md</sub>

**android-d7o4t9**
- What works is `ssh [email]`, and it is now passwordless: publickey auth succeeds, `BatchMode=yes` returns `OK` from host `android-d7o4t9`.
  <sub>2026-10-07 · strata-chat-2026-10-07-17-37.md</sub>

**artifact**
- `artifact` and `plan` are leaf modules with no GPU dependency, which is deliberate: `strata_artifact` and `strata_plan` are `INTERFACE` libraries with no CUDA link (`CMakeLists.txt:227, 258`).
  <sub>2026-10-09 · strata-chat-2026-10-09-08-03.md</sub>

**assist.py**
- The live server (pid 1071617, port 8081, started 14:38) still has the pre-convergence `assist.py` loaded; it needs a restart for the new bridge code to take effect.
  <sub>2026-10-09 · strata-chat-2026-10-09-15-05.md</sub>

**auth works shortcut**
- Key auth now works — the shortcut resolves differently, but `ssh [email]` is passwordless now.
  <sub>2026-10-07 · strata-chat-2026-10-07-17-37.md</sub>

**body-pose**
- Blank fields are real gaps, not parse failures for `body-pose`, `cosmos3-nano`, `cosmos3-nano-reasoner` — those three cards render only via JavaScript, so no parameter/context data is server-side.
  <sub>2026-10-09 · strata-chat-2026-10-09-08-40.md</sub>

**build/hypercore-worker**
- `tools/calibrate.py hypercore-q2_0.json` exits with `WorkerUnreachable: worker exited during startup (1)`, and running `build/hypercore-worker` standalone gives `engine init failed (-5)` because the live server (pid 834276, port 8081) holds the GPU.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-13-20.md</sub>

**cargo_home**
- It works here because the hub was launched interactively, but if `server.py` is ever started by systemd or `sh -c`, `PATH`, `UV_`, `PIP_`, `CARGO_HOME` and `TMPDIR` are all lost — and the script's own comment warns about exactly this for `TMPDIR`/`nvcc`.
  <sub>2026-10-05 · strata-chat-2026-10-05-20-19.md</sub>

**cat**
- Logs land in `/home/user0/.terminal/jobs/<name>` — note they are plain files, so `docs__read_file` refuses them ("not a document type"); use `process` action=log or a shell `cat`.
  <sub>2026-10-03 · strata-chat-2026-10-03-18-25.md</sub>

**chmod**
- `chown`/`chmod` are not permitted by the sandbox's sudo policy.
  <sub>2026-10-10 · strata-chat-2026-10-10-03-30.md</sub>

**code live strata**
- The new code is live. Strata restarted at 03:44 (PID 2512290) and `GET /mcp` now reports `condense_at: 0.55, condense_after: 2, condense_chars: 1200`.
  <sub>2026-10-04 · strata-chat-2026-10-04-03-57.md</sub>

**curl**
- `rg`, `diff`/`patch`, `docker`, `curl`/`wget`, `strace`/`time` were already allowed and are now exercised through `run`/`debug`.
  <sub>2026-10-03 · strata-chat-2026-10-03-19-51.md</sub>

**docs__read_file**
- Logs land in `/home/user0/.terminal/jobs/<name>`, which is under the docs root, so `docs__read_file` can read a server's log.
  <sub>2026-10-03 · strata-chat-2026-10-03-15-05.md</sub>

**downloads/**
- Permission layer separate from execution — new `serve/tool_permissions.py` Ownership rule, not a path rule: a file this process created, or anything under `scratch/`, `tmp/`, `downloads/`, is free; anything else is refused with a reason and a `force=true` escape hatch.
  <sub>2026-10-05 · strata-chat-2026-10-05-23-07.md</sub>

**fails http 8765**
- If that fails, use `http://192.168.74.2:8765/mcp`.
  <sub>2026-10-04 · strata-chat-2026-10-04-06-37.md</sub>

**filter.file**
- The Monitor card does surface this (`filter.file` + the "not writable by this user" note), and `_shared_lines()` (assist.py:311) unions the two call logs so the history is one history.
  <sub>2026-10-09 · strata-chat-2026-10-09-15-05.md</sub>

**groups agent data**
- Groups are now `ai-agent bin adm www-data systemd-journal docker dev user0`.
  <sub>2026-10-03 · strata-chat-2026-10-03-18-25.md</sub>

**harness runs peer**
- Harness runs on the peer, I drive it over SSH — works if you open :22 on `.9`.
  <sub>2026-10-07 · strata-chat-2026-10-07-17-37.md</sub>

**hypercore_engine_init**
- `src/interface/hypercore_bridge.cpp` — `load_config_text()`, `is_blank()`, `trimmed()`, `looks_like_json_object()`, placed next to the existing JSON helpers; `hypercore_engine_init` resolves the source before allocating the engine, so a bad path unwinds nothing.
  <sub>2026-10-09 · strata-chat-2026-10-09-22-41.md</sub>

**integrating tools daytona_bridge_test**
- Integrating the tools/daytona_bridge_test.py verification pass as a blocking stage in your CI pipeline ensures that the hidden visibility boundaries (STRATA_API/HYPERCORE_API), calling conventions, and cross-language compatibility guarantees are proven on a clean, isolated, foreign toolchain before code can be merged.
  <sub>2026-10-10 · strata-chat-2026-10-10-00-02.md</sub>

**interpreter**
- sudoers/mcp.yaml: open items are the operator-rule fallback and the `INTERPRETER` grant.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-13-20.md</sub>

**mcp.py**
- One thing to know before it takes effect: the running server (PID 2491454) still reports the old settings — `GET /mcp` returns `{'max_result_chars': 6000, 'max_rounds': 20}` with no condense keys, because it loaded `mcp.py` before the patch.
  <sub>2026-10-04 · strata-chat-2026-10-04-03-57.md</sub>

**mcp.yaml**
- To make them apply you'd need to start Strata (or just that server) as ai-agent; `mcp.yaml` has no `user:` key, so `command: sudo` is the only in-file option and it conflicts with stdin being the JSON-RPC channel.
  <sub>2026-10-03 · strata-chat-2026-10-03-18-25.md</sub>

**nginx.service**
- The nginx rule is inert — there is no `nginx.service` on this host (docker and containerd are running).
  <sub>2026-10-03 · strata-chat-2026-10-03-18-25.md</sub>

**ngram**
- It is organised as eleven modules that mirror eleven CMake libraries, and the dependency graph is acyclic and layered: `artifact → plan → core → kernels → engine → prefill → program`, with `spec` and `ngram` as side branches consumed only by the driver.
  <sub>2026-10-09 · strata-chat-2026-10-09-08-03.md</sub>

**niko1221/strata**
- Is the HyperCore rename intended to land, or is it abandoned? The GitHub repo is still `Niko1221/Strata` and HEAD is self-consistently "strata" — the rename is only in the uncommitted working tree.
  <sub>2026-10-10 · strata-chat-2026-10-10-03-30.md</sub>

**ping**
- `ssh`, `scp`, `nc`, `ping` are available, so either topology is workable once a port is open.
  <sub>2026-10-07 · strata-chat-2026-10-07-17-37.md</sub>

**portainer**
- For reference, the API key in `strata-q2_0.json` is `api_key: "0000"`, and AnythingLLM is not running (`docker ps` shows only `portainer`), so the only web UI on this box is Strata on `:8081`.
  <sub>2026-10-04 · strata-chat-2026-10-04-06-37.md</sub>

**readme.md**
- I worked around it by deleting and recreating `README.md` (the directory is world-writable).
  <sub>2026-10-10 · strata-chat-2026-10-10-19-47.md</sub>

**ready_s**
- Starts detached with `setsid nohup sh <variant>_run-q2_0.sh &`, writes the PID to `~/.cache/strata/server.pid`, then polls `http://127.0.0.1:<port>/` until it answers, reporting progress every 10 s (a cold model load takes a minute or two, so `READY_S` defaults to 120).
  <sub>2026-10-05 · strata-chat-2026-10-05-23-07.md</sub>

**reconstructed_installed.sudoers**
- Strictly, only two files match `sudoers.ai-user0`; the third sudoers file is `reconstructed_installed.sudoers`.
  <sub>2026-10-05 · strata-chat-2026-10-05-20-19.md</sub>

**scp**
- Next step: once `ssh -o BatchMode=yes [email] 'echo ok'` works, I'll drive the benchmark over SSH (topology B) — clone, install, run, and `scp` the results JSON back.
  <sub>2026-10-07 · strata-chat-2026-10-07-17-37.md</sub>

**scrape__file_info**
- When the chat is … [universal] /home/ai-user0/_Notes/strata-chat-2026-10-03-15-09.md … Install it — `scrape__file_info` cannot report duration or codec for the audio/video it downloads.
  <sub>2026-10-05 · strata-chat-2026-10-05-20-19.md</sub>

**serve/**
- Fixing that means editing `serve/mcp/__init__.py`, and `serve/` is `root:root 644` (`stat -c '%a %U:%G' serve/mcp/__init__.py` → `644 root:root`), while the sudoers rules here allow only `sudo apt-get install -y nodejs npm git ripgrep jq`.
  <sub>2026-10-05 · strata-chat-2026-10-05-20-19.md · also in strata-chat-2026-10-05-20-19.md</sub>

**serve/mcp.py**
- The Docker version is untouched. If you'd rather keep the container running, the alternative is a `url:` entry — `url: http://web-scrape-mcp:8766/mcp` — which `serve/mcp.py` already supports.
  <sub>2026-10-03 · strata-chat-2026-10-03-14-03.md</sub>

**serve/test_assist.py**
- `serve/test_assist.py`, `serve/test_monitor.py`, `serve/test_frontend.py`: 44 passed (18 subtests), including four new `SharedPaths` tests covering the "file owned by the other account" case, the chmod-to-666 convergence, and "Check lag writes to the file the dropdown reads".
  <sub>2026-10-09 · strata-chat-2026-10-09-15-05.md</sub>

**sntrup761x25519**
- I confirmed it non-interactively: Everything else is healthy. Key exchange succeeded (`sntrup761x25519` / chacha20), and `Host '192.168.74.9' is known and matches the ED25519 host key` — so the transport is fine, only the identity isn't authorized.
  <sub>2026-10-07 · strata-chat-2026-10-07-17-37.md</sub>

**sshpass**
- Two side notes: `sshpass` isn't installed here, so I can't answer an interactive password prompt from the terminal tool — key auth is the clean path for me.
  <sub>2026-10-07 · strata-chat-2026-10-07-17-37.md</sub>

**strata_install**
- The install is gated. `strata_install` returns a plan first, so the assistant can show you the download size before anything is written to disk.
  <sub>2026-10-07 · strata-chat-2026-10-07-09-31.md</sub>

**sudo returns exactly**
- `sudo -n -l` returns exactly two grant rules: one line expanding to 261 commands, plus `/usr/sbin/visudo -c -f /etc/sudoers.d/ai-user0`.
  <sub>2026-10-05 · strata-chat-2026-10-05-20-19.md</sub>

**sudoers file grants**
- The sudoers file grants nothing. `ai-agent ALL=(ai-agent) NOPASSWD: ALL` means "ai-agent may run any command as ai-agent" — a no-op.
  <sub>2026-10-03 · strata-chat-2026-10-03-18-25.md</sub>

**sudoers.ai-user0.expanded**
- Keep `sudoers.ai-user0.expanded` only as the audit view (it's the readable list of what is and isn't granted).
  <sub>2026-10-05 · strata-chat-2026-10-05-20-19.md</sub>

**terminal**
- Writes: a per-thread temporary directory exposed via `$TMPDIR`, `$TMP`, and `$TEMP` is writable and persists across `terminal` calls in this thread{{#if worktrees}}, along with these project directories:
  <sub>2026-10-06 · strata-chat-2026-10-06-01-06.md</sub>

**terminal__install**
- Minor notes. `terminal__install` with a pyenv path resolves `/home/ai-agent/.pyenv/…` to `/home/user0/.pyenv/…` (the trees are linked) and installs as a user install — it works, but the reported interpreter isn't the one you asked for.
  <sub>2026-10-04 · strata-chat-2026-10-04-03-57.md</sub>

**terminal_check**
- Python tooling that `terminal_check` must auto-detect → install into a pyenv version and `pyenv rehash`, so the shims land on PATH.
  <sub>2026-10-03 · strata-chat-2026-10-03-18-25.md</sub>

**terminal_root**
- Sandboxing — every new tool resolves paths through `inside()`, so they're bound to `TERMINAL_ROOT`; the allowlist gained `ninja, ar, strip, nm, objdump, xxd, clang-tidy, lldb, strace, ltrace, time`.
  <sub>2026-10-03 · strata-chat-2026-10-03-19-51.md</sub>

**terminal_status**
- `terminal_status` could also report the download size limit and whether the state dir is writable, since that's what actually breaks tooling.
  <sub>2026-10-03 · strata-chat-2026-10-03-18-25.md</sub>

**transport type rejected**
- The old SSE transport (`"type": "sse"`) is rejected with an explanatory message.
  <sub>2026-10-04 · strata-chat-2026-10-04-05-16.md</sub>

**when flag active**
- When this flag is active, the server bypasses the strict file-presence checks for vocab.json and spins up a dedicated ScriptedWorker proxy backend instead of the real CUDA daemon.
  <sub>2026-10-09 · strata-chat-2026-10-09-22-41.md</sub>

## Decisions taken

what was chosen, and why, oldest first


**mcp.yaml** · 2 chats
- Not caused by the rename, but worth flagging — 11 pre-existing failures surfaced by the suites: `mcp.yaml` now registers seven servers while `test_hub__shipped_yaml` asserts six; the hub merge API moved (AttributeError in 8 merge cases); the terminal allowlist doesn't catch backtick substitution; and `docs_mcp.create_file(".ssh/authorized_keys")` is accepted where the guard should refuse it.
  <sub>2026-10-10 · strata-chat-2026-10-10-07-17.md</sub>
- Two env additions the running server needs regardless: I already added `TERMINAL_ALLOW_EXTRA` and `RUFF_CACHE_DIR` to `mcp.yaml`, but pid 2351071 was started with the old environment, so `terminal__run` still rejects `sudo` ("'sudo' is not on the allowlist") — as you saw in my test above.
  <sub>2026-10-03 · strata-chat-2026-10-03-18-25.md</sub>

**--port**
- Three bugs it caught and I fixed: `status` printed nothing because `describe()` read `$pid/cmdline` instead of `/proc/$pid/cmdline`; a transient `/proc` entry vanished mid-scan and killed the script under `set -e`; and `--port` parsing used `shift` inside a `for` loop.
  <sub>2026-10-05 · strata-chat-2026-10-05-23-07.md</sub>

**.new**
- Install path is unchanged and still safe: write to `.new`, validate with `visudo -cf`, then `mv` + `chown root:root` + `chmod 440`; on failure it removes the temp file and dies without touching the live file.
  <sub>2026-10-05 · strata-chat-2026-10-05-23-31.md</sub>

**.sudoers_state.json**
- Removed (12,145 bytes total, via `scrape__remove_downloads`, which reports counts): Kept in `/home/ai-user0/downloads/`: `gen_sudoers.py`, `sudoers.ai-user0.fixed`, `sudoers.ai-user0.expanded`, `test_sudoers.py`, `.sudoers_state.json`, plus a new `sudoers.manifest.md`.
  <sub>2026-10-05 · strata-chat-2026-10-05-20-19.md</sub>

**/etc/sudoers.d/ai-agent**
- Those needed the apt privileges I added to `/etc/sudoers.d/ai-agent`.
  <sub>2026-10-03 · strata-chat-2026-10-03-18-25.md</sub>

**/etc/sudoers.d/ai-user0**
- Current (installed): `sudoers.ai-user0.fixed`. It is byte-for-byte the logic running as `/etc/sudoers.d/ai-user0`.
  <sub>2026-10-05 · strata-chat-2026-10-05-20-19.md</sub>

**/home/ai-user0/_notes/ai_setup.revised.sh**
- Done — section 5 of `/home/ai-user0/_Notes/ai_setup.revised.sh` (lines 150–222) now emits the audited sudoers configuration from `/home/ai-user0/downloads/sudoers.ai-user0.fixed`. What changed:
  <sub>2026-10-05 · strata-chat-2026-10-05-23-31.md</sub>

**/home/user0/strata/mcp.yaml**
- `sudo` is not on the terminal allowlist. I added `TERMINAL_ALLOW_EXTRA: sudo,setfacl,getfacl,visudo,apt-get,nproc` to the `terminal` server env in `/home/user0/Strata/mcp.yaml`, but the running `terminal_mcp.py` process (pid 2351071) was started with the old environment, so it still rejects `sudo`.
  <sub>2026-10-03 · strata-chat-2026-10-03-18-25.md</sub>

**/usr/sbin/visudo**
- The two bugs I flagged earlier are fixed in the installed file: the visudo grant now names `/usr/sbin/visudo` (the real path), and docker is granted — `sudo -n /usr/bin/docker ps` returns an empty container table, exit 0.
  <sub>2026-10-05 · strata-chat-2026-10-05-20-19.md</sub>

**cve-2024-31083**
- A fix for `CVE-2024-31083` in X.org software in April 2024 introduced a regression, which has been fixed in xwayland 23.2.6 and xorg-server 21.1.13.
  <sub>2026-10-07 · strata-chat-2026-10-07-18-39.md</sub>

**docs__delete_file**
- Idempotence and cleanup — `scrape__remove_downloads` reports files and bytes removed; `docs__delete_file` has no equivalent at all, and my test files in `/home/user0/tmp … [universal] /home/ai-agent/strata-chat-2026-10-03-15-09.md … 5.
  <sub>2026-10-04 · strata-chat-2026-10-04-05-16.md</sub>

**find build user**
- `find build -user root -type f -delete` removed them, and the directory is writable (`touch third_party/llama.cpp/ggml/src/_probe_write` succeeded).
  <sub>2026-10-11 · hypercore-chat-2026-10-11-14-18.md</sub>

**gen_sudoers.py**
- Keep `gen_sudoers.py` + `sudoers.ai-user0.fixed` as the source of truth; regenerate rather than edit.
  <sub>2026-10-05 · strata-chat-2026-10-05-20-19.md</sub>

**ni_run-q2_0.sh**
- Naming decision. `ni_run-q2_0.sh` is gone by design (T3 replaced it with `restart.sh` + `hypercore_<model>.sh`).
  <sub>2026-10-10 · strata-chat-2026-10-10-05-20.md</sub>

**permissions user0 sandbox**
- Permissions are now `ai-user0:dev-sandbox` (serve 755, files 644) — all three patches applied and verified.
  <sub>2026-10-05 · strata-chat-2026-10-05-20-19.md</sub>

**py_compile**
- Verification: `py_compile` clean on every edited file; `sh -n restart.sh` clean; the affected files run green in isolation (82 passed in 21.7 s), and the full `serve/` suite is green.
  <sub>2026-10-10 · strata-chat-2026-10-10-07-17.md</sub>

**serve/assist.py**
- Patch applied (`serve/assist.py`): `_write_shared()` mirrors every allowlist write to every copy that exists and is writable, `_shared_lines()` merges the call log across copies (dedup, time-ordered), and `call_log()` reads the merged history.
  <sub>2026-10-09 · strata-chat-2026-10-09-15-05.md</sub>

**socket sanitation supervisor**
- Socket sanitation: supervisor evicts stale socket, pid-private paths, cleanup, tests added to install.sh.
  <sub>2026-10-10 · hypercore-chat-2026-10-10-18-54.md</sub>

**verified bugs fixed**
- Verified: Two bugs I fixed in your version: `self._session_counter += 1` inside worker threads is load/add/store, so two threads can land on the same id and overwrite each other's event — now behind a lock, with `_next_session_id()` as the single source.
  <sub>2026-10-09 · strata-chat-2026-10-09-18-55.md</sub>

## Measured on this machine

numbers actually measured, not estimated


**/home/ai-agent/vbtest/triage.sh**
- I wrote and tested a helper at `/home/ai-agent/vbtest/triage.sh` (uses ffprobe 8.0.1 + jq, both installed) that reports bitrate per megapixel: Rule of thumb (my heuristic, not from the docs): 1080p files under ~3 Mbps total are already well encoded — skip them; 1080p above ~6 Mbps or 4K above ~15 Mbps are the ones that give you the 50% win.
  <sub>2026-10-04 · strata-chat-2026-10-04-07-56.md</sub>

**between intent leaders**
- The gap between intent (93% of IT leaders plan to deploy agents within two years) and operational reality is the defining story of 2026, not the capability curve.
  <sub>2026-10-03 · strata-chat-2026-10-03-12-03.md</sub>

**coulomb pseudopotential conventionally**
- `μ` — the Coulomb pseudopotential — is not. It is conventionally fixed to 0.10 (McMillan) or computed by constrained RPA, which is expensive and has ~30–50% uncertainty.
  <sub>2026-10-07 · strata-chat-2026-10-07-18-16.md</sub>

**since subset includes**
- Since 0.1.27 the subset includes every Chinese, Japanese and Korean token (106,299 ids), so answers in those languages are 15-38% faster (Q2_0, RTX 5070).
  <sub>2026-10-03 · strata-chat-2026-10-03-14-03.md</sub>

**word count balance**
- Word-count balance: roughly 90% of the article is Trump's own speech.
  <sub>2026-10-02 · strata-chat-2026-10-02-22-43.md</sub>

## Gotchas

things that bit once and will bite again


**--out**
- `gen_sudoers.py` writes to `--out` and prints to stdout; the header of both generated files says "Generated by gen_sudoers.py - regenerate, do not hand-edit."
  <sub>2026-10-05 · strata-chat-2026-10-05-20-19.md</sub>

**/etc/alternatives/visudo**
- `/usr/bin/visudo -c -f /etc/sudoers.d/ai-user0` never matches: `visudo` is at `/usr/sbin/visudo` (`ls -l /usr/sbin/visudo` → symlink to `/etc/alternatives/visudo`); `/usr/bin/visudo` does not exist.
  <sub>2026-10-05 · strata-chat-2026-10-05-20-19.md</sub>

**/etc/sudoers.d**
- It grants the wrong direction if root access was intended, but changing it needs root (`/etc/sudoers.d` is `root:root 0440`, and my sudo grants don't include `install`, `cp`, or `tee` on that path).
  <sub>2026-10-05 · strata-chat-2026-10-05-20-19.md</sub>

**/home**
- Two defects to fix before it can run: `bash --no-login` isn't a real flag, and `/home` is not writable — the same permission wall that broke my earlier test — so the state directory must not sit directly under the root.
  <sub>2026-10-03 · strata-chat-2026-10-03-15-05.md</sub>

**/home/ai-agent**
- A perfectly good Firefox 157 already existed at `/home/ai-user0/.local/firefox/firefox`, but the agent's `$HOME` is `/home/ai-agent` — so it was never found.
  <sub>2026-10-09 · strata-chat-2026-10-09-09-50.md</sub>

**/home/ai-user0/strata**
- Do not move `/home/ai-user0/Strata`. It is the live system (PID 1552343, port 8081, HTTP 200), and `ni_run-q2_0.sh` hardcodes `cd "/home/ai-user0/Strata"`.
  <sub>2026-10-10 · strata-chat-2026-10-10-05-20.md</sub>

**/usr/bin/visudo**
- My sudoers file has a dead line: `visudo` is at `/usr/sbin/visudo`, not `/usr/bin/visudo`, so that rule never matches.
  <sub>2026-10-03 · strata-chat-2026-10-03-18-25.md</sub>

**ai-agent**
- The breakage is that `mcp.yaml` was never repointed from `ai-agent` to `ai-user0`.
  <sub>2026-10-05 · strata-chat-2026-10-05-20-19.md</sub>

**ai-user0**
- If you want to edit it with the docs tools, the directory needs to be made writable for `ai-user0` (`chmod 775` on the folder, which requires root — the scoped sudoers grants don't include a general `chmod`).
  <sub>2026-10-06 · strata-chat-2026-10-06-18-22.md</sub>

**also caught shell**
- Also caught a shell gotcha worth recording: `pkill -f "python3 -m lm_eval"` matched the ssh `bash -c` wrapper itself and killed the run before it started — kill and run must be separate ssh calls.
  <sub>2026-10-07 · strata-chat-2026-10-07-17-37.md</sub>

**authorized_keys**
- Or, from the peer side: If it still falls back to password after that, check on the peer: `authorized_keys` must not be group-writable (sshd silently rejects it otherwise), and `~/.ssh` must not be world-accessible.
  <sub>2026-10-07 · strata-chat-2026-10-07-17-37.md</sub>

**delete_file**
- `edit_file` bypasses the ownership guard that `write_file`/`delete_file` enforce `serve/docs_mcp.py:255` and `:276` call `tool_permissions.decide(...)`; `edit_file` (`:206`) does not, and then calls `note_created(target)`, so editing a file the session never created both succeeds and grants the session write/delete rights over it.
  <sub>2026-10-06 · strata-chat-2026-10-06-14-10.md</sub>

**httptransport**
- If you want the 54-era leftovers prevented structurally rather than by a per-class `terminate`, the durable fix is for `HttpTransport` to own its server process the way `StdioTransport` does — worth doing only if you plan to run HTTP-transport servers from `mcp.yaml` in production too.
  <sub>2026-10-10 · strata-chat-2026-10-10-19-47.md</sub>

**mcp.yaml**
- Known gaps — the guard is not a shell parser, gdb needs `-g` for useful output, `ptrace_scope` limits breakpoints, Docker volumes intentionally still reference user0, and `mcp.yaml` requires a restart.
  <sub>2026-10-03 · strata-chat-2026-10-03-19-51.md</sub>

**sudo**
- `sudo` is now allowed but still needs a password. `sudo -n apt-get update` returns "interactive authentication is required" — because the server process runs as user0, not ai-agent, so ai-agent's NOPASSWD rules don't apply.
  <sub>2026-10-03 · strata-chat-2026-10-03-18-25.md</sub>

## Still open

not done, deferred, or waiting on a decision


**condense_at**
- Remaining open items are the sudoers line-41 direction, the INTERPRETER group decision, and the unstarted Medium item — token accounting/compaction in the tool layer, which would sit next to the existing `condense_at` / `condense_chars` settings in `mcp.yaml`.
  <sub>2026-10-05 · strata-chat-2026-10-05-23-07.md</sub>

**ruff_cache_dir**
- Remaining open items are the sudoers line‑41 direction, the INTERPRETER group decision, and the `RUFF_CACHE_DIR`/`TERMINAL_ALLOW_EXTRA` settings that still need a hub restart to take effect.
  <sub>2026-10-05 · strata-chat-2026-10-05-23-07.md</sub>
