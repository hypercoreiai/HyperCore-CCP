# Issues, root causes and fixes

Accumulated from 3 transcripts, 3 entries. Built 2026-10-11. Newer chats append here; within a section the entries are grouped by the thing they are about, newest statement first.


## Current state

Maintained by hand; the builder keeps it in place.

**"no frame for 30.0s" / StreamStalled.** The supervisor used the 30 s submit-ack timeout as the
per-frame wall. A 116k-token prompt takes ~31 s to read, so a healthy request was declared stalled
in the middle of its prefill. The silence wall now belongs to the supervisor (`self.silence_s`,
from the config's `engine_silence_s`, default 300 s; 0 waits as long as the request needs) and
`stream()` measures from the last frame. `timeout_s` is only the ack wall.

**The agent dropdown showed only the system prompt.** The server looked for `ROOT/prompt.json`;
the profiles are in `prompts/prompt.json`. `find_prompt_file` now checks both.

**Monitor cards blank (Reused, Tok/s, hit rate, prefill).** The terminal summary's `prompt_read`
and `prefill_ms` were parsed nowhere, so the derived fields never existed. `derive_monitor_field`
in `serve/ipc_parser.py` now computes what the worker does not report.

**"Exception occurred during processing of request".** An unhandled exception inside `do_POST`
left a half-written SSE body and the stdlib traceback. The handler now records the failure, closes
the stream with an error event, and returns a 500 JSON only when nothing was sent yet.

**401 from the web page.** A server started with an API key serves a page that does not know it.
The page now carries the key it requires.

**Worker socket EADDRINUSE.** A Unix socket file outlives the process that bound it; the next bind
on the same name fails. Two supervisors sharing a name also share the `{socket}.config.json` side
file. Socket names are pid- or port-namespaced for this reason.

**A stalled link is not a dead link.** `WorkerUnreachable` and `StreamStalled` are different
exceptions and the HTTP layer must distinguish them; conflating them caused needless engine
restarts.


## What is true now

how the thing works, as the chats established it


**/metrics**
- Live proof: `/metrics` shows a 146,161-token prompt with `prompt_ms 36888.0` finishing `finish: "stop"`, and `grep -c "no frame for" hypercore-q2_0.log` is 0.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-13-20.md</sub>

**do_post**
- Request exception — an unhandled exception inside `do_POST` no longer leaves a half-written SSE body and the stdlib traceback; it now closes the stream with an error event and returns a 500 JSON only when nothing was sent.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-11-46.md</sub>

**start_engine**
- It is a traceback from `tools/calibrate.py:401`: It died at the first `start_engine` call (`calibrate.py:258`), before any sweep ran.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-15-51.md</sub>
