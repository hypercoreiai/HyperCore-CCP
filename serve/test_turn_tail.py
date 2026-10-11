"""serve/test_turn_tail.py - the end-of-turn task check: ask, and keep the turn open while the work is not done.

    python -m unittest serve.test_turn_tail -v

A turn that would end is followed by one short turn asking whether every task in the request is
finished. A bare confirmation ends the turn; a "no", or the model carrying on with its work, keeps it
open and asks again, up to "turn_tail_checks" times. These tests run against the mock engine: no GPU,
no model pack.
"""
from __future__ import annotations

import json
import sys
import unittest
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from serve.frontend import ChatTemplate
from serve.server import (
    TAIL_CHECK_PROMPT,
    ByteTokenizer,
    MockEngine,
    Service,
    TailHold,
    serve,
    tail_is_done,
)

ROOT = Path(__file__).resolve().parents[1]
CTX = 8192
WORK = "</think>\n\nI wrote the report and the tests for it."
STILL = "</think>\n\nNot yet - the tests are still missing."
DONE = "</think>\n\ndone"
IGNORED = "</think>\n\n"


class CountingEngine(MockEngine):
    """The mock engine, counting how many times a turn was generated and keeping its last prompt."""

    def __init__(self, tokenizer, scripts, max_context: int = CTX):
        super().__init__(tokenizer, scripts, max_context=max_context)
        self.calls, self.prompts = 0, []

    def generate(self, ids, max_new, sampling, cancel, embeddings=None):
        self.calls += 1
        self.prompts.append(list(ids))
        yield from super().generate(ids, max_new, sampling, cancel, embeddings)


def turn(scripts, check=True, checks=3, prompt=None, stream=False, max_tokens=400):
    """One POST /v1/chat/completions against a mock server, and the engine that answered it."""
    tok = ByteTokenizer()
    engine = CountingEngine(tok, scripts)
    svc = Service(engine, tok, ChatTemplate(ROOT / "serve/chat_template.jinja"))
    svc.turn_tail_check = check
    svc.turn_tail_checks = checks
    if prompt:
        svc.turn_tail_prompt = prompt
    httpd = serve(svc, port=0)
    base = f"http://127.0.0.1:{httpd.server_address[1]}"
    body = {"model": "m", "messages": [{"role": "user", "content": "write the report and its tests"}],
           "max_tokens": max_tokens, "stream": stream}
    try:
        req = urllib.request.Request(base + "/v1/chat/completions", data=json.dumps(body).encode(),
                                    headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            if not stream:
                return json.loads(r.read()), engine, svc
            events = []
            for line in r.read().decode().splitlines():
                if line.startswith("data: ") and line != "data: [DONE]":
                    events.append(json.loads(line[6:]))
            return events, engine, svc
    finally:
        httpd.shutdown()
        httpd.server_close()


def content_of(events):
    return "".join((c["choices"][0]["delta"].get("content") or "") for c in events)


def tail_events(events):
    return [c["hypercore_mcp"] for c in events if c.get("hypercore_mcp") and
            c["hypercore_mcp"].get("event") == "tail_check"]


def turn_api(api, scripts, check=True, checks=3, stream=False, max_tokens=400):
    """One POST against a mock server on the Anthropic or Responses route."""
    tok = ByteTokenizer()
    engine = CountingEngine(tok, scripts)
    svc = Service(engine, tok, ChatTemplate(ROOT / "serve/chat_template.jinja"))
    svc.turn_tail_check = check
    svc.turn_tail_checks = checks
    httpd = serve(svc, port=0)
    base = f"http://127.0.0.1:{httpd.server_address[1]}"
    prompt = "write the report and its tests"
    if api == "anthropic":
        body = {"model": "m", "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens, "stream": stream}
        path = "/v1/messages"
    else:
        body = {"model": "m", "input": [{"role": "user", "content": prompt}],
                "max_output_tokens": max_tokens, "stream": stream}
        path = "/v1/responses"
    try:
        req = urllib.request.Request(base + path, data=json.dumps(body).encode(),
                                    headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            if not stream:
                return json.loads(r.read()), engine, svc
            events = []
            for line in r.read().decode().splitlines():
                if line.startswith("data: ") and line != "data: [DONE]":
                    events.append(json.loads(line[6:]))
            return events, engine, svc
    finally:
        httpd.shutdown()
        httpd.server_close()


def anthropic_text(body):
    return "".join(b.get("text", "") for b in body.get("content", []) if b.get("type") == "text")


def responses_text(body):
    return "".join(part.get("text", "") for item in body.get("output", []) if item.get("type") == "message"
                   for part in item.get("content", []) if part.get("type") == "output_text")


class Confirmation(unittest.TestCase):
    """What counts as "the work is finished"."""

    def test_a_bare_confirmation_is_done(self):
        for text in ("done", "Done.", "yes", "Yes, everything is complete.", "all tasks done",
                     "nothing outstanding", "finished"):
            self.assertTrue(tail_is_done(text), text)

    def test_work_still_open_is_not(self):
        for text in ("", "no", "not yet", "I still need to write the tests", "I'll continue with the rest",
                    "the report is done but the tests are outstanding",
                    "yes, and here is the code that goes with it: " + "print(1)\n" * 40):
            self.assertFalse(tail_is_done(text), text)

    def test_a_confirmation_longer_than_a_word_or_two_is_the_model_working(self):
        self.assertFalse(tail_is_done("done " * 40))


class Hold(unittest.TestCase):
    """A confirmation is never shown; anything else is streamed as soon as it is clear."""

    def test_a_confirmation_is_held_and_never_emitted(self):
        hold = TailHold()
        self.assertEqual(hold.push("do"), "")
        self.assertEqual(hold.push("ne"), "")
        self.assertEqual(hold.flush(), "done")

    def test_work_is_streamed_once_it_cannot_be_a_confirmation(self):
        hold = TailHold()
        self.assertEqual(hold.push("Not "), "")
        out = hold.push("yet, the tests are missing.")
        self.assertEqual(out, "Not yet, the tests are missing.")
        self.assertEqual(hold.push("and I will add them."), "and I will add them.")
        self.assertEqual(hold.flush(), "")


class TurnTail(unittest.TestCase):
    def test_a_confirmed_turn_ends_after_one_check(self):
        body, engine, _ = turn([WORK, DONE])
        self.assertEqual(engine.calls, 2)
        self.assertEqual(body["choices"][0]["message"]["content"], "I wrote the report and the tests for it.")
        self.assertEqual(body["choices"][0]["finish_reason"], "stop")

    def test_the_confirmation_is_not_part_of_the_answer(self):
        body, _, _ = turn([WORK, DONE])
        self.assertNotIn("done", body["choices"][0]["message"]["content"])

    def test_a_turn_that_says_no_keeps_working(self):
        body, engine, _ = turn([WORK, STILL, DONE])
        self.assertEqual(engine.calls, 3)
        answer = body["choices"][0]["message"]["content"]
        self.assertIn("the tests are still missing", answer)

    def test_a_check_that_produces_nothing_ends_the_turn(self):
        # Ignoring the question is not an answer, but a round that writes no text has no work
        # left in it: the turn ends rather than being asked again.
        body, engine, _ = turn([WORK, IGNORED, DONE])
        self.assertEqual(engine.calls, 2)
        self.assertEqual(body["choices"][0]["message"]["content"], "I wrote the report and the tests for it.")

    def test_the_check_is_asked_at_most_the_configured_number_of_times(self):
        body, engine, _ = turn([WORK, STILL], check=True, checks=2)
        self.assertEqual(engine.calls, 3)                       # the turn, then two checks
        self.assertIn("the tests are still missing", body["choices"][0]["message"]["content"])

    def test_zero_checks_leaves_the_turn_as_it_was(self):
        body, engine, _ = turn([WORK, DONE], check=True, checks=0)
        self.assertEqual(engine.calls, 1)
        self.assertEqual(body["choices"][0]["message"]["content"], "I wrote the report and the tests for it.")

    def test_off_by_default_the_turn_is_not_touched(self):
        body, engine, _ = turn([WORK, DONE], check=False)
        self.assertEqual(engine.calls, 1)
        self.assertEqual(body["choices"][0]["message"]["content"], "I wrote the report and the tests for it.")

    def test_the_model_is_asked_in_the_check_turn(self):
        _, engine, svc = turn([WORK, DONE])
        asked = svc.tok.decode(engine.prompts[1])
        self.assertIn(svc.turn_tail_prompt, asked)
        self.assertIn("I wrote the report", asked)             # its own answer is in the transcript it is asked about

    def test_a_custom_check_prompt_is_used(self):
        _, engine, svc = turn([WORK, DONE], prompt="Are you finished?")
        self.assertIn("Are you finished?", svc.tok.decode(engine.prompts[1]))

    def test_every_round_counts_in_the_usage(self):
        body, engine, _ = turn([WORK, STILL, DONE])
        self.assertEqual(engine.calls, 3)
        self.assertGreater(body["usage"]["completion_tokens"], len(WORK))

    def test_a_streamed_turn_says_when_it_checked(self):
        events, _, _ = turn([WORK, STILL, DONE], stream=True)
        checks = tail_events(events)
        self.assertEqual([c["result"] for c in checks], ["continue", "continue", "complete"])
        self.assertEqual(content_of(events), "I wrote the report and the tests for it."
                                        + "Not yet - the tests are still missing.")

    def test_the_default_prompt_is_the_shipped_one(self):
        _, _, svc = turn([WORK, DONE])
        self.assertEqual(svc.turn_tail_prompt, TAIL_CHECK_PROMPT)


class OtherAPIs(unittest.TestCase):
    """The same turn-tail behaviour on the Anthropic and Responses routes."""

    def test_anthropic_a_confirmed_turn_ends_after_one_check(self):
        body, engine, _ = turn_api("anthropic", [WORK, DONE])
        self.assertEqual(engine.calls, 2)
        self.assertEqual(anthropic_text(body), "I wrote the report and the tests for it.")
        self.assertEqual(body["stop_reason"], "end_turn")

    def test_anthropic_a_no_keeps_the_turn_open(self):
        body, engine, _ = turn_api("anthropic", [WORK, STILL, DONE])
        self.assertEqual(engine.calls, 3)
        self.assertEqual(anthropic_text(body), "I wrote the report and the tests for it."
                                             + "Not yet - the tests are still missing.")
        self.assertEqual(body["stop_reason"], "end_turn")

    def test_responses_a_confirmed_turn_ends_after_one_check(self):
        body, engine, _ = turn_api("responses", [WORK, DONE])
        self.assertEqual(engine.calls, 2)
        self.assertEqual(responses_text(body), "I wrote the report and the tests for it.")
        self.assertEqual(body["status"], "completed")

    def test_responses_a_no_keeps_the_turn_open(self):
        body, engine, _ = turn_api("responses", [WORK, STILL, DONE])
        self.assertEqual(engine.calls, 3)
        self.assertEqual(responses_text(body), "I wrote the report and the tests for it."
                                             + "Not yet - the tests are still missing.")
        self.assertEqual(body["status"], "completed")


if __name__ == "__main__":
    unittest.main()
