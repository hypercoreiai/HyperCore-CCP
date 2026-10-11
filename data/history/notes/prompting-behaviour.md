# Turn behaviour and the agent profiles

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
