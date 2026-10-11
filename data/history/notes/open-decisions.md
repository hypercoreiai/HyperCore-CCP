# Things decided but not yet done

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
