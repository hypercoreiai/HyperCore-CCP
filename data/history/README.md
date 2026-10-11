# data/history — the accumulated development state

What was learned across the chat transcripts, merged by topic instead of by chat. A new chat appends to the topics it touched; nothing has to be re-read from the raw transcripts to know the current state.

## Layout
- `topics/<topic>.md` — one file per category; entries are dated, attributed, and grouped by the thing they are about
- `notes/<topic>.md` — the hand-written current state, inserted at the top of each topic
- `chats/<date>-<name>.md` — one file per transcript: what was asked, what came of it
- `index.json` — the machine-readable version of both
- `sources.md` — the reverse index, category by transcript

## Categories
- `topics/hardware-environment.md` — Hardware and environment (15 entries)
- `topics/setup-configuration.md` — Setup, run configs and defaults (11 entries)
- `topics/web-ui-monitor.md` — The web app and the Monitor (9 entries)
- `topics/testing-quality.md` — Testing and code quality (9 entries)
- `topics/prompting-behaviour.md` — Prompting, agents and turn behaviour (5 entries)
- `topics/memory-vram.md` — Memory, VRAM and RAM (4 entries)
- `topics/issue-log.md` — Issues, root causes and fixes (3 entries)
- `topics/performance-benchmarks.md` — Performance and benchmarks (3 entries)
- `topics/deployment-permissions.md` — Deployment, paths and permissions (3 entries)
- `topics/open-decisions.md` — Open decisions and deferred work (2 entries)
- `topics/engine-internals.md` — Engine internals (2 entries)
- `topics/mcp-tooling.md` — MCP servers and tools (1 entries)

## Rebuild
```bash
python3 tools/build_history.py
```

The extraction is deterministic: the transcripts are the source of truth. Anything added by hand to a topic file is lost on a rebuild — the current state lives in `notes/<topic>.md`, which the builder reads and keeps.

