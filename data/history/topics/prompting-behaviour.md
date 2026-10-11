# Prompting, agents and turn behaviour

Accumulated from 3 transcripts, 5 entries. Built 2026-10-11. Newer chats append here; within a section the entries are grouped by the thing they are about, newest statement first.


## Current state

Maintained by hand; the builder keeps it in place.

**`prompt.json` is the profile file.** One top-level `system_prompt`, then one object per agent.
The server's `/prompts` returns the base plus the profiles; the web app builds the dropdown from
that. The file lives beside the server or in `prompts/` — `find_prompt_file(ROOT)` checks both.
A config that points at only one of them is why the dropdown showed a single entry.

**Thinking is opt-in per request.** `reasoning_effort` and `reasoning_budget_tokens` control it;
a request that reaches max tokens while still thinking has no answer, and the server says so
rather than returning an empty completion. `effort_position` decides where the effort instruction
is placed in the prompt.

**The turn-tail check.** When a turn would end with `finish=stop`, the server appends one short
user turn asking whether every task in the turn is done. A yes ends the turn; a no, an ignored
question, or more work keeps it open and the model continues, up to `turn_tail_checks` times
(default 3, capped 10). It is wired into the OpenAI chat, Anthropic and Responses routes. A turn
that ends on a length stop, a cancel, a forced tool call, or with no text at all is not checked.
Each check is another read of the conversation, so it costs prompt time.

**Refusal and persona are configured, not inherent.** The uncensored profiles exist because the
base model refuses things it should not; the profiles are the mechanism, not the model.


## What is true now

how the thing works, as the chats established it


**--turn-tail-check** · 3 chats
- `tools/test_setup_config.py`: new `ServerDefaults` class (new install gets all three; `--host 127.0.0.1 --api-key s3cret --no-turn-tail-check` wins; an existing config keeps its own values; the run script carries `--turn-tail-check` and honours a config that turns it off).
  <sub>2026-10-11 · hypercore-chat-2026-10-11-13-20.md</sub>
- Opt-in via `--turn-tail-check` or `"turn_tail_check": true`; the question text is overridable with `--turn-tail-prompt` / `turn_tail_prompt`.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-11-46.md</sub>
- One caveat: the turn-tail check is off by default — the running server was started without `--turn-tail-check`, so it won't fire until you add the flag or set `"turn_tail_check": true` in the profile.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-11-46.md</sub>

**.calibrate_progress.log**
- `.calibrate_progress.log` shows: The calibrator starts its own worker while the live server (pid 998337, started 14:04, `--port 8081 --turn-tail-check`) already holds the model, so the second engine cannot get VRAM.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-14-18.md</sub>

**/health**
- Live state: pid 793996 on port 8081, started from `run-q2_0.sh` with `--host 0.0.0.0 --turn-tail-check`; `/health` reports `api_key: true`, and a streamed request emitted `tail_check {"result":"continue","checks":1,"max_checks":3}`, so the turn-tail check is active.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-13-20.md</sub>
