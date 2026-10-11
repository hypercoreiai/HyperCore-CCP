# Deployment, paths and permissions

Accumulated from 2 transcripts, 3 entries. Built 2026-10-11. Newer chats append here; within a section the entries are grouped by the thing they are about, newest statement first.


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


**build/hypercore-worker**
- `tools/calibrate.py hypercore-q2_0.json` exits with `WorkerUnreachable: worker exited during startup (1)`, and running `build/hypercore-worker` standalone gives `engine init failed (-5)` because the live server (pid 834276, port 8081) holds the GPU.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-13-20.md</sub>

**interpreter**
- sudoers/mcp.yaml: open items are the operator-rule fallback and the `INTERPRETER` grant.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-13-20.md</sub>

## Decisions taken

what was chosen, and why, oldest first


**find build user**
- `find build -user root -type f -delete` removed them, and the directory is writable (`touch third_party/llama.cpp/ggml/src/_probe_write` succeeded).
  <sub>2026-10-11 · hypercore-chat-2026-10-11-14-18.md</sub>
