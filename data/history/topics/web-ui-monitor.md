# The web app and the Monitor

Accumulated from 37 transcripts, 103 entries. Built 2026-10-13. Newer chats append here; within a section the entries are grouped by the thing they are about, newest statement first.


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


**app.js** · 7 chats
- If the garbling disappears with these off and reappears with `HYPERCORE_MMVQ_IL=1 HYPERCORE_NAN_GUARD=1 HYPERCORE_ADAPT_OVERLAP=1`, the engine is the cause; if it persists either way, it's the injected `Complete the open tasks` prompt, and the `app.js` fix is the one that matters.
  <sub>2026-10-13 · strata-chat-2026-10-13-21-31.md</sub>
- `bindTranscript()` refactor in `app.js` — the click/toggle handlers are currently hard-bound to `#chat` only.
  <sub>2026-10-10 · hypercore-chat-2026-10-10-11-52.md</sub>
- New harness `serve/web/test_assist_thought_panel.js` (a small DOM stand-in; it reads `updateAssistant`, `transcriptOf`, `bindTranscript` and the actual `bindTranscript(...)` wiring lines out of `app.js`, so it fails when the app changes): 5 cases, 5 pass, exit 0 — panel opens and shows the reasoning in both transcripts, copy reads the right array, a missing container is a no-op.
  <sub>2026-10-09 · strata-chat-2026-10-09-16-17.md</sub>
- The new cases run the real `paintAssistTop`/`foldAssistTop`/`wireAssistTop` source out of `app.js` against the stand-in DOM: the summary names the selected model and count; a first visit stays open; closing is stored and restored on reload; a programmatic open does not overwrite the user's choice; an older page without the panel does not throw.
  <sub>2026-10-09 · strata-chat-2026-10-09-16-17.md</sub>
- Negative control: deleting `wireAssistTop();` from `app.js` makes 5 of the 10 fail — the harness is sensitive to the wiring, not just to the strings.
  <sub>2026-10-09 · strata-chat-2026-10-09-16-17.md</sub>
- The `app.js` change is static and only needs a browser reload.
  <sub>2026-10-09 · strata-chat-2026-10-09-15-05.md</sub>
- New `serve/test_web_client.py` (8 cases) asserts the shipped `app.js`/`index.html` actually do these things.
  <sub>2026-10-06 · strata-chat-2026-10-06-18-57.md</sub>

**prompt.json** · 5 chats
- Two things worth knowing. Only `prompt.json` is read, looked for beside the server first and then in `prompts/`.
  <sub>2026-10-13 · hypercore-chat-2026-10-13-00-06.md</sub>
- And the catalog is re-read on file change, per `serve/prompts.py`: adding or removing a profile in `prompt.json` changes the number on the next page load, no restart needed.
  <sub>2026-10-13 · hypercore-chat-2026-10-13-00-06.md</sub>
- The profiles are read from `prompt.json` beside the server or `prompts/prompt.json` (the one this repo ships): adding a profile to that file adds a menu entry with nothing to change in the page or the code.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-08-01.md</sub>
- `prompt.json` beside the server is one JSON object: a "system_prompt" that every chat starts with, and one entry per agent after it.
  <sub>2026-10-04 · strata-chat-2026-10-04-05-56.md · also in strata-chat-2026-10-04-05-56.md</sub>
- Nothing is committed to git yet (`prompt.json`, `serve/prompts.py`, `serve/test_prompts.py` are new; `serve/server.py`, `serve/web/`, README and docs are modified).
  <sub>2026-10-04 · strata-chat-2026-10-04-05-56.md</sub>

**prompt json plain** · 3 chats
- Prompt and tool-output costs grow non-linearly, so read narrowly: query the specific key in a config instead of dumping the file … [universal] /home/ai-user0/_Strata_/prompt.json … 144 tokens (max_context=262144).
  <sub>2026-10-13 · strata-chat-2026-10-13-21-31.md</sub>
- The prompt cache does resume. From turn 3 on, 52 of the 57 tokens are reused and only 5 are read.
  <sub>2026-10-13 · strata-chat-2026-10-13-21-31.md</sub>
- prompt.json is a plain JSON file: a "system_prompt" object that every chat starts with, and any number of other top-level objects, each one an agent profile ...
  <sub>2026-10-04 · strata-chat-2026-10-04-05-56.md</sub>

**serve saving does** · 3 chats
- `node --check serve/web/app.js` → exit 0; `node serve/web/test_surface_slider.js` → all surface checks passed (the Surface slider from the previous turn is intact).
  <sub>2026-10-13 · hypercore-chat-2026-10-13-00-06.md</sub>
- The git diff for serve/web/app.js is only 16 insertions.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-08-01.md</sub>
- `serve/web/app.js:95`: Saving the key does not re-run `loadMcp()`.
  <sub>2026-10-04 · strata-chat-2026-10-04-06-37.md</sub>

**assist** · 2 chats
- But I can check the assist card text in index.html to see what the Assist page does.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-08-01.md</sub>
- There is no server-side record of Assist traffic: `strata-q2_0.log` has zero `assist` entries, `telemetry.py` has none, and the Monitor has no Assist card.
  <sub>2026-10-09 · strata-chat-2026-10-09-12-32.md</sub>

**full check probe** · 2 chats
- Actually, let me check whether Assist.png is referenced in serve/web/index.html or docs.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-08-01.md</sub>
- A full "Check lag" probe ran through the live route: 80 models in 46.5 s, and the result written to the same file the dropdown reads.
  <sub>2026-10-09 · strata-chat-2026-10-09-15-05.md</sub>

**prompts/prompt.json** · 2 chats
- The message comes from `serve/web/app.js:623`: That runs when the page fetches `GET /prompts`, which `serve/prompts.py` builds from `prompts/prompt.json`.
  <sub>2026-10-13 · hypercore-chat-2026-10-13-00-06.md</sub>
- Cause. The dropdown is built at run time from `GET /prompts`, and that endpoint reads `ROOT / "prompt.json"` — but this repo ships the profiles in `prompts/prompt.json`.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-11-46.md · also in 2026-10-11-hypercore-chat-2026-10-11-06-34.md</sub>

**reused** · 2 chats
- The request table's `Reused`, `Tok/s` and `VRAM hit rate` columns are populated.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-08-01.md</sub>
- Native build check: Result: passed, including the ABI alignment check: So the Monitor tab’s `Reused`, `Tok/s`, and `VRAM Hit Rate` columns are no longer empty placeholders; they are fed from the worker terminal frame and rendered by the web app.
  <sub>2026-10-10 · hypercore-chat-2026-10-10-19-47.md</sub>

**text home user0** · 2 chats
- The … [universal] /home/ai-user0/_Strata/docs/AMD_HIP.md … Since 0.1.39 a tuning run by hand (`./setup.sh --calibrate`) is saved for the AMD card it ran on and reused when setup runs again.
  <sub>2026-10-13 · hypercore-chat-2026-10-13-08-16.md · also in hypercore-chat-2026-10-13-08-16.md</sub>
- text /home/ai-user0/Strata/zprompt.system_prompt.json json "system_prompt": "You are the Zed coding agent running inside the Zed editor.
  <sub>2026-10-06 · strata-chat-2026-10-06-01-06.md · also in strata-chat-2026-10-06-01-06.md</sub>

**--prompts**
- `serve/server.py:637` and `:2013` set `prompts_path` to `prompt.json` in the repo root, overridable only by `--prompts` or the run config's `prompts` key.
  <sub>2026-10-06 · strata-chat-2026-10-06-14-10.md</sub>

**/api-monitor**
- Root cause (`serve/server.py:3629`, the `/` and `/api-monitor` handlers): Replacing `<title>` with the script deletes the opening tag, so the served head becomes: Confirmed against the live server: The browser parses `HyperCore` as a stray text node in `<head>`, which is why it shows up in the top-left corner and pushes the banner down.
  <sub>2026-10-13 · hypercore-chat-2026-10-13-00-06.md</sub>

**/home/ai-agent/hypercore-ccp/serve/server.py**
- The same wrong path is in `/home/ai-agent/HyperCore-CCP/serve/server.py`, which also has no root `prompt.json`; say the word and I'll apply the fix there too.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-11-46.md</sub>

**/home/user0/index.html**
- It doesn't turn up — a search for "Current State of AI October 2026" returns unrelated hits (`/home/user0/index.html`, llama.cpp docs, Cursor project files), and `home__status` reports the crawl is idle with 0 files indexed at the root, despite 80,425 rows in the database.
  <sub>2026-10-03 · strata-chat-2026-10-03-14-03.md</sub>

**/prompts**
- `serve/web/app.js` (1,073 → 1,148) — agent-profile dropdown built from `/prompts`, API-key save re-runs `loadMcp()`/`loadPrompts()`, tool heartbeat in the composer hint, context-full 400 explained instead of shown raw.
  <sub>2026-10-06 · strata-chat-2026-10-06-23-05.md</sub>

**192.168.74.9**
- `serve/web/app.js:161` polls it continuously; your dashboard at `192.168.74.9` was polling it every few seconds, which is why the identical traceback appears ~20 times.
  <sub>2026-10-10 · strata-chat-2026-10-10-12-04.md</sub>

**_read_path**
- `_writable` now returns a writable sibling with the content copied, so a read-only file can't empty the dropdown, and `_read_path` picks the newest existing copy for reading.
  <sub>2026-10-10 · strata-chat-2026-10-10-07-17.md</sub>

**_request_last**
- `prompt_read` / `prefill_ms` are parsed from the terminal summary in `serve/ipc_parser.py` (`derive_monitor_field`), carried through `_request_last` into the request record, and rendered in `serve/web/app.js`.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-11-46.md</sub>

**actually first double**
- Actually, first let me double-check the README's "The web app" section claims are accurate by checking index.html for the Monitor cards and the Assist tab.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-08-01.md</sub>

**app.css**
- Both UIs are the same four-file kit (`index.html`, `app.js`, `app.css`, `components.css`, `tokens.css`, `monitor.html`, `monitor.js`, `sprite.svg`).
  <sub>2026-10-10 · hypercore-chat-2026-10-10-11-52.md</sub>

**assist_defaults**
- `serve/assist.py` now has its own defaults, documented as deliberately independent of the run config: `converse()` takes `max_tokens=None` and falls back to `ASSIST_DEFAULTS`, and `serve/web/app.js` carries the same note at the call site so nobody wires the two together later.
  <sub>2026-10-09 · strata-chat-2026-10-09-15-05.md</sub>

**assist_mcp.py**
- Real output from the card after two sends: The MCP bridge writes to the same file — I ran `assist_mcp.py` standalone and its call appeared in the log, so Monitor visibility covers both paths.
  <sub>2026-10-09 · strata-chat-2026-10-09-12-32.md</sub>

**changes session limited**
- The web UI changes in this session are limited to app.js (2 changes).
  <sub>2026-10-11 · hypercore-chat-2026-10-11-08-01.md</sub>

**content**
- Everything I can see proposed in this thread is already in the working tree: the `renderAssist`/empty-placeholder fix (app.js:1449-1464), the user-bubble `text`/`content` split, truncation capture (`converse()` → `finish_reason` → `truncated`), the `over_limit` table, the probe panel, the Monitor card, the 500-line log.
  <sub>2026-10-09 · strata-chat-2026-10-09-15-05.md</sub>

**cp_blackbox.sh**
- `unzip -l | grep -c build-cov` returns 0, and the source files are all present (`serve/web/app.js`, `serve/hypercore_supervisor.py`, `src/platform/memory_test.cpp`, `serve/test_fatal_recovery.py`, `cp_blackbox.sh`).
  <sub>2026-10-13 · hypercore-chat-2026-10-13-00-20.md</sub>

**defaults**
- Also worth checking: `DEFAULTS` in `app.js:597` sets `ctx: 132000`, but if your Chat-tab Context cap field is empty or 0, `pruneToContext` returns the payload untouched ("no cap").
  <sub>2026-10-07 · strata-chat-2026-10-07-12-05.md</sub>

**fast**
- Two separate causes, both real: (a) The toast reported `fast`, the dropdown is `kept`. `probe_models()` (serve/assist.py:505-512) builds `kept = fast + held`: a model already on the allowlist is not dropped when the endpoint 429s or times out, because a throttle says nothing about its speed.
  <sub>2026-10-09 · strata-chat-2026-10-09-15-05.md</sub>

**filter.file**
- The Monitor card does surface this (`filter.file` + the "not writable by this user" note), and `_shared_lines()` (assist.py:311) unions the two call logs so the history is one history.
  <sub>2026-10-09 · strata-chat-2026-10-09-15-05.md</sub>

**health.images**
- If your client or browser tab was opened against an `ni` instance (or an old tab still holding a cached health response), it will say images off — the UI's "Images on/off" line is read straight from `health.images` (`serve/web/app.js:340`), which is `svc.vision is not None` (`serve/server.py:882`).
  <sub>2026-10-05 · strata-chat-2026-10-05-23-36.md</sub>

**index.html**
- Against the server running on 8081: So `renderAgents()` in `serve/web/app.js` has nothing to add, and the only entry left is the one hard-coded in `index.html`: "System prompt only".
  <sub>2026-10-11 · hypercore-chat-2026-10-11-11-46.md · also in hypercore-chat-2026-10-11-08-01.md, strata-chat-2026-10-04-06-37.md</sub>

**j.strata_mcp**
- `serve/web/app.js:1151` still reads `j.strata_mcp`.
  <sub>2026-10-10 · strata-chat-2026-10-10-03-30.md</sub>

**kimi pinned list**
- kimi-k3 is in the pinned list at 0.692 s, so you should see it in the dropdown now.
  <sub>2026-10-09 · strata-chat-2026-10-09-15-05.md</sub>

**logicprompt.json**
- The other files in that folder, `logicprompt.json`, `zedprompt.json`, `zprompt.json`, `many_prompt.json`, are source material and are not served.
  <sub>2026-10-13 · hypercore-chat-2026-10-13-00-06.md</sub>

**many_prompt.json**
- Both `prompt.json` and `many_prompt.json` are untracked (`??` in git status), so there is no committed version to fall back to.
  <sub>2026-10-06 · strata-chat-2026-10-06-14-10.md</sub>

**messages**
- On load or New Chat, insert a system message into the chat showing the injected system prompt + selected agent prompt (rendered as a collapsed card), and set the `messages` array to include `{role: "system", ...}` so apiMessages() includes it as the first message in the API request.
  <sub>2026-10-04 · strata-chat-2026-10-04-05-56.md</sub>

**needs conditions transcript**
- That needs the conditions from the transcript: a ~90k-token shared prefix (`prompt 88903 tokens = 0 reused + 89031 read` is in the log right now from the other client), thinking enabled, and `reasoning_budget_tokens: 24756` reached — at which point `serve/server.py:2682` injects `"\n\nI have thought about this long enough; time to give my answer.\n</think>\n\n"` into the resumed prefix.
  <sub>2026-10-13 · strata-chat-2026-10-13-21-31.md</sub>

**phone open monitor**
- On the phone: open the Monitor tab once (it calls `loadMcp()` at `app.js:80`), confirm it reads `35 tools · 5 of 5 servers connected`, then return to Chat.
  <sub>2026-10-04 · strata-chat-2026-10-04-06-37.md</sub>

**probe_models deliberately keeps**
- `probe_models()` deliberately keeps already-pinned models whose probe failed (`serve/assist.py:454`), so the dropdown stays at 12 while the fast count drops to 11 So the popup was reporting two different numbers as if they were one.
  <sub>2026-10-09 · strata-chat-2026-10-09-15-05.md</sub>

**prompts**
- Server: add an endpoint `prompts` (GET) that reads prompt.json and returns the system prompt plus a list of agent profiles (key, name, role, description/capabilities).
  <sub>2026-10-04 · strata-chat-2026-10-04-05-56.md</sub>

**prompts/logicprompt.json**
- `prompts/logicprompt.json` is left untouched.
  <sub>2026-10-12 · hypercore-chat-2026-10-12-13-18.md</sub>

**renderassistprobe**
- `serve/web/app.js` — `renderAssistProbe` The `group("Not served by this endpoint", unavailable, …)` block is gone; a single line replaces it: > `56 model(s) the endpoint does not serve are not listed: the chat call answers 404 for them, so there is nothing to measure.` Why keep the count. The summary line still says `67 left out`.
  <sub>2026-10-09 · strata-chat-2026-10-09-16-17.md</sub>

**returns dynamic level**
- Returns: Dynamic: any top-level key in prompt.json is treated as a profile; "system_prompt" is the base; everything else is an agent.
  <sub>2026-10-04 · strata-chat-2026-10-04-05-56.md</sub>

**serve/frontend.py**
- And if you want, I can look at how the system prompt is assembled in `serve/frontend.py` / `src/program/generate.cpp` to find where such a line would have to go for it to actually take effect.
  <sub>2026-10-09 · strata-chat-2026-10-09-08-40.md</sub>

**serve/server.py**
- No code change was needed; the dropdown is built from the endpoint, and no agent key is hard-coded in `serve/server.py`, `serve/web/app.js`, or `serve/tool_permissions.py`.
  <sub>2026-10-12 · hypercore-chat-2026-10-12-13-18.md</sub>

**serve/test_assist.py**
- `serve/test_assist.py`, `serve/test_monitor.py`, `serve/test_frontend.py`: 44 passed (18 subtests), including four new `SharedPaths` tests covering the "file owned by the other account" case, the chmod-to-666 convergence, and "Check lag writes to the file the dropdown reads".
  <sub>2026-10-09 · strata-chat-2026-10-09-15-05.md</sub>

**serve/test_mcp.py**
- If you want, I can patch `app.js:95` to call `loadMcp()` after the key is saved — a one-line change, covered by `serve/test_mcp.py`.
  <sub>2026-10-04 · strata-chat-2026-10-04-06-37.md</sub>

**serve/web/app.js**
- `serve/web/app.js` fills it from three endpoints, and only one of them is the config: `loadConfig()` is explicit about it:
  <sub>2026-10-07 · strata-chat-2026-10-07-09-31.md</sub>

**stop_reason**
- `stream()` yields `(token_id, prompt_reused, summary)` where `summary` is a decoded dict with `stop_reason` already normalised to `"limit"`/`"cancel"`/`"eos"`.
  <sub>2026-10-09 · strata-chat-2026-10-09-22-41.md</sub>

**summary.prompt_reused**
- Requests are the unit; conversation reuse is inside the box, observable through `summary.prompt_reused`.
  <sub>2026-10-09 · strata-chat-2026-10-09-18-55.md</sub>

**switch browser settings**
- The switch is off in that browser. Settings live in that browser's localStorage: `settings = {...DEFAULTS, ...store.get("sampling", {})}` (`app.js:479-480`).
  <sub>2026-10-04 · strata-chat-2026-10-04-06-37.md</sub>

**system_prompt**
- The count is simply the number of top-level entries in that file (anything not starting with `_` and not `system_prompt`), and the same list fills the composer's dropdown, the one labelled "Give this chat an agent profile (from prompt.json)", whose default is "System prompt only".
  <sub>2026-10-13 · hypercore-chat-2026-10-13-00-06.md</sub>

**test_a_model_the_endpoint_does_not_answer_for_is_not_listed**
- `python3 -m pytest serve/test_web_client.py serve/test_monitor.py serve/test_assist.py` → 55 passed, 8 subtests, 0 failed, including a new `test_a_model_the_endpoint_does_not_answer_for_is_not_listed` that checks each of the four filter sites and asserts the old group is absent.
  <sub>2026-10-09 · strata-chat-2026-10-09-16-17.md</sub>

## Decisions taken

what was chosen, and why, oldest first


**app.js** · 4 chats
- The two UI items from the investigation are still open and unfixed: `app.js` re-sends `RESUME_PROMPT` even when the last turn is already that prompt, and `turn_tail_check: true` appends `TAIL_CHECK_PROMPT` up to 3× per turn.
  <sub>2026-10-13 · strata-chat-2026-10-13-21-44.md</sub>
- Negative control: the same harness against `app.js` with `bindTranscript($("assist-chat"));` removed fails on `#assist-chat is not bound` and `opening the panel left it empty in #assist-chat` — so the test is not vacuous.
  <sub>2026-10-09 · strata-chat-2026-10-09-16-17.md</sub>
- Live check (just now): The served page contains `assist-card`, `assist-chat`, `assist-probe-results`, and `app.js` has the seven assist hooks — so the UI you're looking at is the patched one.
  <sub>2026-10-09 · strata-chat-2026-10-09-15-05.md</sub>
- The served `app.js` on 8081 is the fixed file (89,842 bytes, probe panel present); the tab you were reading still holds the pre-fix script — hard-refresh it (Ctrl+Shift+R).
  <sub>2026-10-09 · strata-chat-2026-10-09-15-05.md</sub>

**./prompt.json**
- `serve/prompts.py`: added `PROMPT_FILE` / `PROMPT_PLACES = ("", "prompts")` and `find_prompt_file(root)`, which returns the first of `./prompt.json`, `./prompts/prompt.json` that exists.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-11-46.md</sub>

**api_key**
- The "FREE" claim — qualified it and added the missing Assist bullet: I verified those details against the code rather than guessing: `serve/assist.py` reads `API_KEY`/`NVIDIA_API_KEY` and raises if absent; `serve/assist_fast_models.json` pins 14 models with `max_lag_s: 1.0`; `serve/web/app.js` has the "Show every model" toggle and the "Check lag" probe.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-08-31.md</sub>

**browser**
- Switching agent profiles, adding an MCP server (I added `browser` this session — the tool catalog is part of the system prompt), or changing reasoning effort when it's rendered at the top of the prompt.
  <sub>unknown · unknown-context.md · also in context.txt</sub>

**expert_logic_reasoning_agent**
- Added as `expert_logic_reasoning_agent`, the last entry in `prompts/prompt.json` (file now 24,057 bytes, valid JSON, 8 top-level keys).
  <sub>2026-10-12 · hypercore-chat-2026-10-12-13-18.md</sub>

**expert_x_comment_agent**
- What the test asserts. `serve/test_prompts.py:132` checks the live file against a hard-coded list: What your file has now. `prompt.json` is at `_meta.version: 5`, "v4: added expert_x_comment_agent", so `catalog()` returns four profiles: the three the test expects plus `expert_x_comment_agent`.
  <sub>2026-10-06 · strata-chat-2026-10-06-14-10.md</sub>

**held**
- The probe response now carries `previous`, `removed`, `held`, and `pinned` separately, and `renderAssistProbe()` (app.js:1401) names each model that left and why.
  <sub>2026-10-09 · strata-chat-2026-10-09-15-05.md</sub>

**home agent strata**
- /home/ai-agent/Strata/prompt.json The dropdown menu shuould populate dynamically so that additional agent profiles can be added.
  <sub>2026-10-04 · 2026-10-04-strata-chat-2026-10-04-05-56.md</sub>

**prompt.json**
- A silent refresh fires when the menu is focused and when New Chat is pressed, so a profile added to `prompt.json` while the page is open reaches the menu without a reload.
  <sub>2026-10-04 · strata-chat-2026-10-04-05-56.md</sub>

**prompt_reused**
- The Monitor path is now connected end to end: The populated fields include: I also found and fixed a real bridge bug: the terminal frame was discarding `prompt_reused`.
  <sub>2026-10-10 · hypercore-chat-2026-10-10-19-47.md</sub>

**py_compile**
- `node --check serve/web/app.js` ok; `py_compile` clean; ruff reports nothing on any changed line (3 pre-existing findings elsewhere).
  <sub>2026-10-11 · hypercore-chat-2026-10-11-11-46.md · also in hypercore-chat-2026-10-11-07-09.md</sub>

**serve/assist_fast_models.json**
- Why the lag test "changed nothing". Two separate lists, both current: the dropdown is the pinned list (13 of 80, `serve/assist_fast_models.json`, measured 14:42), the long list is the full catalog behind "Show every model" (80) plus the "Probe results" panel naming the 67 left out and why (slow / 404 / throttled).
  <sub>2026-10-09 · strata-chat-2026-10-09-15-05.md</sub>

**there file monitor**
- There is now one file, and the Monitor card prints the merge note (`merged 2 copies of … into …; removed …`) in the "Path" fact when a merge happens.
  <sub>2026-10-09 · strata-chat-2026-10-09-15-05.md</sub>

**web_mcp.py**
- SSRF guard reused, not reimplemented. `public_url()` is the same function `web_mcp.py` uses, so both servers refuse private/loopback hosts identically.
  <sub>2026-10-03 · strata-chat-2026-10-03-14-03.md</sub>

## Measured on this machine

numbers actually measured, not estimated


**prefix reuse long** · 2 chats
- Fix the long-context routing miss. 94.1% hit rate at 68k context vs 98.7% at 67 tokens is the measurable gap.
  <sub>2026-10-10 · hypercore-chat-2026-10-10-16-40.md</sub>
- Prefix reuse is why long sessions stay fast: 128,894 of 128,934 tokens reused, only 40 read in 204 ms.
  <sub>2026-10-07 · strata-chat-2026-10-07-09-31.md</sub>

**--resident-experts**
- The Q2_0 arena is 34.0 GB on a 32 GB PC, so setup chose `--resident-experts` — and it's working: the log reports "0 blob reads from the file" and an 87–92% expert hit rate.
  <sub>2026-10-07 · strata-chat-2026-10-07-09-31.md</sub>

**defensible statement workspace**
- The defensible statement from this workspace is narrower: on this RTX 4090 the working configuration is `--pcie-frac 0.00 --spec-min-p 0.50 --pool-workers 10` (recorded in `2026-10-03/04/08-community-rtx4090-iq3xxs-200k-{code,ru}/env.json`), with decode in the 135-155 tok/s band, and `STRATA_KV_PREFETCH=1` and `"parallel": 2` both measured as losses here (2-4% and 28% respectively).
  <sub>2026-10-11 · hypercore-chat-2026-10-11-15-51.md</sub>

**live decode throughput**
- From the live log, decode throughput against prompt length: Expert cache hit rate is 97.5–98.3% across that range, with only 1.3–2.7% of routed experts read over PCIe — at ~785 KB per blob that is well under 1 GB/s, nowhere near the PCIe limit.
  <sub>2026-10-10 · hypercore-chat-2026-10-10-18-06.md</sub>

**reserving 1024 instead**
- Reserving 1024 instead takes ~324 MiB off that — roughly 2.3% fewer slots, so the hit rate (currently 87–92%) will drop slightly.
  <sub>unknown · context.txt</sub>

## Gotchas

things that bit once and will bite again


**agent-select**
- [12] `GET /prompts` is served, and the web app builds the agent dropdown from it at run time (`agent-select` in `index.html`, `loadPrompts`/`renderAgents` in `app.js`), with a stamp check so an unchanged catalog never touches the menu.
  <sub>2026-10-06 · strata-chat-2026-10-06-18-57.md</sub>

**decode_ms**
- Those were empty for every real request, and the cause was in the engine adapter, not the dashboard: Closing the generator at the end-of-turn token means the worker's terminal frame is never read, so `HyperCoreRequestHandler.last` stayed `None` and every column fed from it (`reused`, `prompt_read`, `decode_ms`, `decode_tok_s`, `hit_rate`) rendered as "–".
  <sub>2026-10-11 · hypercore-chat-2026-10-11-11-46.md</sub>

**expert cache rate**
- Expert cache hit rate 87–92% on a 512-expert MoE: 11,022 slots (14.5 GiB) in VRAM plus 20.72 GiB of experts page-locked in RAM, and the log says "0 blob reads from the file" — the SSD is never touched during decode.
  <sub>2026-10-07 · strata-chat-2026-10-07-09-31.md</sub>

**many_prompt.json**
- `many_prompt.json` (76 profiles, owned by `user0`) is never read.
  <sub>2026-10-06 · strata-chat-2026-10-06-14-10.md</sub>

**measured under dropdown**
- So "10 measured under 1.0 s" and "12 in the dropdown" are both true and were never reconciled.
  <sub>2026-10-09 · strata-chat-2026-10-09-15-05.md</sub>

**rendermcp sets hidden**
- `renderMcp()` sets `$("mcp-row").hidden = true` (`app.js:392-393`), so the switch is never shown.
  <sub>2026-10-04 · strata-chat-2026-10-04-06-37.md</sub>

**several gpus when**
- Several GPUs (#498): when the RAM holds … [universal] /home/ai-user0/Strata/prompt.json … not fetch a web page to check what a screenshot shows unless the question needs an outside fact.", "encoder_available": "Images reach the model through the strata-vision … [universal] /home/ai-user0/Strata/docs/DETAILS.md … from-mcp-servers) above, where the Strata model calls your MCP tools.
  <sub>2026-10-05 · strata-chat-2026-10-05-23-36.md</sub>

**vram free everything**
- And "193 MiB of VRAM free with everything loaded - LOW: requests may stall" and "WARNING: only 51 MiB of VRAM free at the start of this request (below 512 MiB): when the card is this full the driver can page GPU memory to system RAM, decode falls to a few tok/s and a window may never finish (#2065)".
  <sub>2026-10-13 · strata-chat-2026-10-13-21-31.md</sub>

**want reload model**
- If you don't want to reload the model, `cp prompts/prompt.json prompt.json` makes the running server pick the profiles up on its next fetch — it re-reads the file when its mtime/size changes.
  <sub>2026-10-11 · hypercore-chat-2026-10-11-11-46.md</sub>

## Still open

not done, deferred, or waiting on a decision


**initial_title**
- Not implemented, and why: subagent context isolation needs an agent-level `spawn` tool, not a change to the tool layer (the existing substitutes are `save_to` and `terminal__process` log files, which the docs tools can read); streaming `ToolCallEventStream`/`initial_title` has nothing to render into here; a lazy skill catalog would duplicate what `prompt.json` already carries.
  <sub>2026-10-05 · strata-chat-2026-10-05-23-07.md</sub>
