# Open decisions and deferred work

Accumulated from 8 transcripts, 8 entries. Built 2026-10-13. Newer chats append here; within a section the entries are grouped by the thing they are about, newest statement first.


## Current state

Maintained by hand; the builder keeps it in place.

- **Anthropic and Responses routes and the turn-tail check.** The check is wired into all three
  routes now; the remaining work is measuring whether it changes answer quality in practice, not
  whether it runs.
- **`--no-turn-tail-check` as a per-model setting.** The flag exists and is remembered in the
  config; a global off switch for a whole install is not.
- **The live server must be restarted for any config change to take effect.** This is the most
  common cause of "I changed it and nothing happened" and there is no hot reload.
- **Fact-checking the 2026 state-of-AI document** — content work, not code, still open.
- **The INTERPRETER grant in sudoers** and the operator rule fallback were left undecided.
- **Pre-existing lint and mypy findings** in `serve/mcp/web_scrape_mcp.py` and `serve/docs_mcp.py`
  are known and not blocking; no test failure is caused by them.
- **A single turn larger than the context cap cannot be pruned and still returns 400.** The
  condenser handles multi-turn conversations; a lone oversized turn is not solved.


## What is true now

how the thing works, as the chats established it


**.mcp_test_state.json** · 2 chats
- This is the item already recorded as "Not done" in `.mcp_test_state.json`.
  <sub>2026-10-07 · strata-chat-2026-10-07-12-05.md</sub>
- `.mcp_test_state.json` updated: loop 2, verified list refreshed with the full run, `next_step` = no test failures outstanding; remaining work is content item [2] and the by-design open items in [21].
  <sub>2026-10-06 · strata-chat-2026-10-06-23-05.md</sub>

**calls means round1**
- Hmm, calls==3 means: round1 (WORK) → not done → check round 2 (IGNORED) → text empty → `tail_is_done("")` False → then the guard `not (svc.turn_tail_check and checks < ...
  <sub>2026-10-11 · hypercore-chat-2026-10-11-11-46.md</sub>

**state file next**
- The state file's next step (rebuild, `./setup.sh --calibrate`, record the measured pcie-frac) is still open, and I updated it to note that the attempt needs the GPU free.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-15-51.md</sub>

**test_recovery_is_the_supervisors_and_is_bounded**
- Reverted it; the residual flakiness in `test_recovery_is_the_supervisors_and_is_bounded` predates this work and is still open.
  <sub>2026-10-10 · strata-chat-2026-10-10-08-34.md</sub>

## Measured on this machine

numbers actually measured, not estimated


**strata_deferred_register layer registration**
- `STRATA_DEFERRED_REGISTER=1` (per-layer registration pipelined with the load) exists but is opt-in and Windows-only, because it measured ~10% slower decode.
  <sub>2026-10-10 · hypercore-chat-2026-10-10-18-06.md</sub>

## Still open

not done, deferred, or waiting on a decision


**.git**
- Open items: commit the rename, re-point the docs links, fix the 21 pre-existing `serve/` test failures (all in files that are untracked at HEAD, none rename-related), and decide what to do about the 3 `.git` object-pack hits that would need a history rewrite.
  <sub>2026-10-10 · strata-chat-2026-10-10-07-17.md</sub>

**ruff_cache_dir**
- Remaining open items are the sudoers line‑41 direction, the INTERPRETER group decision, and the `RUFF_CACHE_DIR`/`TERMINAL_ALLOW_EXTRA` settings that still need a hub restart to take effect.
  <sub>2026-10-05 · strata-chat-2026-10-05-23-07.md</sub>
