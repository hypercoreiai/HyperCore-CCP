# The chat page and the Monitor

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
