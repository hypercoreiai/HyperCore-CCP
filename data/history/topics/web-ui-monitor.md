# The web app and the Monitor

Accumulated from 2 transcripts, 9 entries. Built 2026-10-11. Newer chats append here; within a section the entries are grouped by the thing they are about, newest statement first.


## Current state

Maintained by hand; the builder keeps it in place.

**One server, one page.** `serve/server.py` serves the app at `/` and the Monitor at
`/api-monitor`; `serve/web/index.html`, `monitor.html`, `app.js`, `app.css`, `tokens.css` and
`components.css` are the front end. The page is served by the same process that answers the API,
so it carries the server's API key in the HTML (`window.HYPERCORE_API_KEY`) and `app.js` uses it
when nothing is stored in the browser — a default-key install works without typing anything into
Settings.

**The Monitor reads `/metrics`.** `/metrics` returns the last 12 requests (`?requests=all` for
everything kept) plus a `history` block of rolling means. The cards are: Reused (the share of the
prompt the GPU did not have to read), Tok/s (decode rate, live while generating, otherwise the
last finished request), VRAM hit rate, and Prefill (the engine's own `prompt_read / prefill_ms`).
When a prompt is still being read there are no decode tokens yet, so the Speed card falls back to
the last completed request instead of showing a blank.

**Fields the engine does not report are derived, not left empty.** `serve/ipc_parser.py`'s
`derive_monitor_field` computes what the terminal summary omits from counters that are present.
A missing number in a card has always meant either the wire did not carry it or the Python side
did not look for it.

**The agent dropdown is built at run time from `prompt.json`.** Any top-level key that is not
`system_prompt` is an agent profile. The server finds that file beside itself or in `prompts/`;
a config that points at the wrong path is why the dropdown showed only "System prompt".

**Context-cap pruning is a server decision, not a client one.** A request larger than the model's
window is condensed before it reaches the engine; the page shows the condensing progress rather
than a dead button.


## What is true now

how the thing works, as the chats established it


**/home/ai-agent/hypercore-ccp/serve/server.py**
- The same wrong path is in `/home/ai-agent/HyperCore-CCP/serve/server.py`, which also has no root `prompt.json`; say the word and I'll apply the fix there too.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-11-46.md</sub>

**_request_last**
- `prompt_read` / `prefill_ms` are parsed from the terminal summary in `serve/ipc_parser.py` (`derive_monitor_field`), carried through `_request_last` into the request record, and rendered in `serve/web/app.js`.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-11-46.md</sub>

**index.html**
- Against the server running on 8081: So `renderAgents()` in `serve/web/app.js` has nothing to add, and the only entry left is the one hard-coded in `index.html`: "System prompt only".
  <sub>2026-10-11 · hypercore-chat-2026-10-11-11-46.md</sub>

**prompts/prompt.json**
- Cause. The dropdown is built at run time from `GET /prompts`, and that endpoint reads `ROOT / "prompt.json"` — but this repo ships the profiles in `prompts/prompt.json`.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-11-46.md</sub>

## Decisions taken

what was chosen, and why, oldest first


**./prompt.json**
- `serve/prompts.py`: added `PROMPT_FILE` / `PROMPT_PLACES = ("", "prompts")` and `find_prompt_file(root)`, which returns the first of `./prompt.json`, `./prompts/prompt.json` that exists.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-11-46.md</sub>

**py_compile**
- `node --check serve/web/app.js` ok; `py_compile` clean; ruff reports nothing on any changed line (3 pre-existing findings elsewhere).
  <sub>2026-10-11 · hypercore-chat-2026-10-11-11-46.md</sub>

## Measured on this machine

numbers actually measured, not estimated


**defensible statement workspace**
- The defensible statement from this workspace is narrower: on this RTX 4090 the working configuration is `--pcie-frac 0.00 --spec-min-p 0.50 --pool-workers 10` (recorded in `2026-10-03/04/08-community-rtx4090-iq3xxs-200k-{code,ru}/env.json`), with decode in the 135-155 tok/s band, and `STRATA_KV_PREFETCH=1` and `"parallel": 2` both measured as losses here (2-4% and 28% respectively).
  <sub>2026-10-11 · hypercore-chat-2026-10-11-15-51.md</sub>

## Gotchas

things that bit once and will bite again


**decode_ms**
- Those were empty for every real request, and the cause was in the engine adapter, not the dashboard: Closing the generator at the end-of-turn token means the worker's terminal frame is never read, so `HyperCoreRequestHandler.last` stayed `None` and every column fed from it (`reused`, `prompt_read`, `decode_ms`, `decode_tok_s`, `hit_rate`) rendered as "–".
  <sub>2026-10-11 · hypercore-chat-2026-10-11-11-46.md</sub>

**want reload model**
- If you don't want to reload the model, `cp prompts/prompt.json prompt.json` makes the running server pick the profiles up on its next fetch — it re-reads the file when its mtime/size changes.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-11-46.md</sub>
