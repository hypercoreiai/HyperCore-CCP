"""serve/test_context_trim.py - --trim-context: a prompt that does not fit the context is fitted
by dropping the oldest turns and head/tail-truncating the newest, instead of answering 400.

    python -m unittest serve.test_context_trim -v

The default is unchanged (reject with 400, like llama.cpp), so every case here that does not pass
trim_context asserts the old behaviour too.
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
    CTX_SLACK,
    ByteTokenizer,
    MockEngine,
    Service,
    serve,
)

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ChatTemplate(ROOT / "serve/chat_template.jinja")


def make_service(max_context: int, trim: bool) -> Service:
    tok = ByteTokenizer()                       # one id per byte, so tokens are comparable to characters
    return Service(MockEngine(tok, "ok", max_context=max_context), tok, TEMPLATE, trim_context=trim)


def conversation(turns: int, size: int) -> list[dict]:
    out = [{"role": "system", "content": "You are a test model."}]
    for i in range(turns):
        out.append({"role": "user", "content": f"turn {i}: " + "a" * size})
        out.append({"role": "assistant", "content": "b" * size})
    return out


def fits(ids: list[int], ctx: int, max_new: int) -> bool:
    return len(ids) + CTX_SLACK + max_new <= ctx


class WithoutTheFlag(unittest.TestCase):
    """The contract: a prompt that does not fit is refused, never silently shortened."""

    def test_an_oversized_prompt_is_still_rejected(self):
        svc = make_service(512, trim=False)
        with self.assertRaises(ValueError) as cm:
            svc.prepare(conversation(4, 200), None, {}, max_new=16)
        self.assertIn("never truncated", str(cm.exception))
        self.assertIsNone(svc.last_trim)

    def test_a_prompt_that_fits_is_never_touched(self):
        svc = make_service(4096, trim=True)
        msgs = conversation(2, 100)
        _, _, _ = svc.prepare(msgs, None, {}, max_new=16)
        self.assertIsNone(svc.last_trim)
        self.assertEqual(len(msgs), 5)


class WithTheFlag(unittest.TestCase):
    def test_the_oldest_turns_go_and_the_profile_stays(self):
        svc = make_service(1200, trim=True)
        msgs = conversation(4, 200)
        ids, _, max_new = svc.prepare(msgs, None, {}, max_new=16)
        self.assertTrue(fits(ids, 1200, max_new), f"prompt of {len(ids)} tokens does not fit 1200")
        trim = svc.last_trim
        self.assertIsNotNone(trim)
        self.assertGreater(trim["dropped"], 0)
        self.assertLess(trim["tokens_after"], trim["tokens_before"])
        self.assertEqual(msgs[0]["role"], "system")                       # the profile is not a turn to drop
        self.assertNotIn("turn 0", json.dumps(msgs))                      # the oldest conversation turn is gone
        self.assertIn("turn 3", json.dumps(msgs))                         # the newest one is kept

    def test_one_oversized_turn_keeps_its_beginning_and_its_end(self):
        svc = make_service(512, trim=True)
        msgs = [{"role": "user", "content": "x" * 1200}]
        ids, _, max_new = svc.prepare(msgs, None, {}, max_new=16)
        self.assertTrue(fits(ids, 512, max_new))
        self.assertGreater(svc.last_trim["clipped_chars"], 0)
        text = msgs[0]["content"]
        self.assertTrue(text.startswith("xxxxx"), "the head of the turn was cut")
        self.assertTrue(text.endswith("xxxxx"), "the tail of the turn was cut")
        self.assertIn("omitted", text)
        self.assertLess(len(text), 1200)

    def test_a_part_list_turn_is_clipped_in_its_text_parts_only(self):
        svc = make_service(512, trim=True)
        msgs = [{"role": "user", "content": [{"type": "text", "text": "y" * 900},
                                            {"type": "image_url", "image_url": {"url": "keep.png"}}]}]
        ids, _, max_new = svc.prepare(msgs, None, {}, max_new=16)
        self.assertTrue(fits(ids, 512, max_new))
        self.assertGreater(svc.last_trim["clipped_chars"], 0)
        self.assertEqual(msgs[0]["content"][1], {"type": "image_url", "image_url": {"url": "keep.png"}})

    def test_nothing_can_be_dropped_and_the_request_is_still_refused(self):
        svc = make_service(64, trim=True)
        with self.assertRaises(ValueError) as cm:
            svc.prepare([{"role": "user", "content": "z" * 200}], None, {}, max_new=16)
        self.assertIn("never truncated", str(cm.exception))

    def test_the_http_path_answers_200_where_it_used_to_answer_400(self):
        svc = make_service(512, trim=True)
        httpd = serve(svc, port=0)
        base = f"http://127.0.0.1:{httpd.server_address[1]}"
        try:
            body = json.dumps({"model": "m", "max_tokens": 16, "messages": conversation(4, 200)}).encode()
            req = urllib.request.Request(base + "/v1/chat/completions", data=body,
                                        headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as r:
                self.assertEqual(r.status, 200)
                payload = json.loads(r.read().decode())
            self.assertIn("message", payload["choices"][0])
            message = payload["choices"][0]["message"]
            self.assertTrue(message.get("content") or message.get("reasoning_content"))
        finally:
            httpd.shutdown()
            httpd.server_close()


if __name__ == "__main__":
    unittest.main()
