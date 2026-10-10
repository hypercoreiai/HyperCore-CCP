#!/usr/bin/env python3
"""A client that stops reading a streamed answer early must not leave its tokens to the next request.

Two ways to run it:

  python3 tools/early_close_test.py http://127.0.0.1:8090        against a server you started
  HYPERCORE_URL=http://127.0.0.1:8090 python3 -m pytest tools/early_close_test.py

With no URL this skips rather than fails: it is a live-server probe, and a CI job that
has not started a server has nothing to probe.
"""
import json
import os
import sys
import threading
import unittest
import urllib.request

URL = os.environ.get("HYPERCORE_URL", "").rstrip("/")   # argv is read in __main__, not here:
KEY = os.environ.get("HYPERCORE_KEY", "")                # under pytest argv is the test file


def req(content, stream, max_tokens=300):
    body = json.dumps({"model": "m", "max_tokens": max_tokens, "temperature": 0, "stream": stream,
                       "messages": [{"role": "user", "content": content}],
                       "chat_template_kwargs": {"enable_thinking": False}}).encode()
    return urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json",
                                                          "Authorization": f"Bearer {KEY}"})


def early_close(content, keep_lines=5):
    r = urllib.request.urlopen(req(content, True), timeout=600)
    for _ in range(keep_lines):
        r.readline()
    r.close()                                   # the client goes away mid-answer


def answer(content):
    with urllib.request.urlopen(req(content, False, 60), timeout=600) as r:
        m = json.load(r)["choices"][0]["message"]
        return (m.get("content") or "") + " " + (m.get("reasoning_content") or m.get("reasoning") or "")


def probe(url):
    """Both paths: solo, then with a second request in a batch slot. True if neither leaks."""
    global URL
    URL = url
    ok = True
    for label, background in (("solo", False), ("batch", True)):
        bg = None
        if background:
            bg = threading.Thread(target=answer, args=("Count slowly from 1 to 60, one number per line.",))
            bg.start()
        early_close("Describe the weather in Montpellier in great detail, at length.")
        a = answer("Reply with exactly one word: the color of the sky on a clear day.")
        good = "blue" in a.lower() and "montpellier" not in a.lower()
        ok &= good
        print(f"{label}: {'OK' if good else 'STALE'} -> {a[:120]!r}", flush=True)
        if bg:
            bg.join()
    return ok


class EarlyClose(unittest.TestCase):
    def test_an_early_close_does_not_leak_into_the_next_request(self):
        if not URL:
            self.skipTest("no server: pass a URL as argv[1] or set HYPERCORE_URL")
        self.assertTrue(probe(URL), "a request cut short left its tokens in the conversation cache")


if __name__ == "__main__":
    url = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else URL
    if not url:
        print("usage: early_close_test.py http://127.0.0.1:8090", file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(0 if probe(url) else 1)
