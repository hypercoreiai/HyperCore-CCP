"""Tests for tools/build_history.py - the accumulated development state under data/history/.

The builder reads the chat transcripts and writes one file per topic. What has to hold:
a sentence about the same thing said in four chats is kept once, with the four sources;
the hand-written current state in notes/ survives a rebuild; nothing outside the
categories is invented.

    python -m unittest tools.test_build_history
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
import build_history as BH  # noqa: E402


class Categories(unittest.TestCase):
    """Every category has a name and a word list; a sentence lands in the topic it is about."""

    def test_every_topic_is_well_formed(self):
        for topic, (title, words) in BH.TOPICS.items():
            with self.subTest(topic=topic):
                self.assertTrue(title)
                self.assertTrue(words)
                self.assertTrue(all(isinstance(w, str) and w.lower() == w for w in words))

    def test_a_sentence_is_classified_by_what_it_is_about(self):
        self.assertIn("mcp-tooling", BH.topic_scores("the browser_mcp server speaks stdio JSON-RPC"))
        self.assertIn("memory-vram", BH.topic_scores("vram-reserve-mib keeps 1024 MiB free on the card"))
        self.assertEqual(BH.topic_scores("a completely unrelated sentence about gardening"), {})

    def test_sections(self):
        self.assertEqual(BH.kind("the stall was fixed by separating the ack wall from the stream wall"),
                         "decisions")
        self.assertEqual(BH.kind("prefill of 116240 tokens took 31235 ms"), "numbers")
        self.assertEqual(BH.kind("never read the transcript again for this"), "gotchas")
        self.assertEqual(BH.kind("still open: the model choice is undecided"), "open")


class Accumulate(unittest.TestCase):
    """The point of the history: one statement per finding, not one per chat."""

    def test_restatements_merge_into_one_entry(self):
        items = [
            {"date": "2026-10-01", "source": "a.md", "text": "the hub starts every MCP server at boot"},
            {"date": "2026-10-02", "source": "b.md", "text": "the hub starts every MCP server at boot time"},
            {"date": "2026-10-03", "source": "c.md", "text": "the hub starts every MCP server at boot, not on demand"},
        ]
        merged = BH.accumulate(items)
        self.assertEqual(len(merged), 1, merged)
        self.assertEqual(merged[0]["date"], "2026-10-03")
        self.assertEqual(merged[0]["source"], "c.md")
        self.assertEqual(sorted(merged[0]["also"]), ["a.md", "b.md"])   # the first source is not lost

    def test_different_findings_stay_apart(self):
        items = [
            {"date": "2026-10-01", "source": "a.md", "text": "the expert cache hit rate was 86.7 percent"},
            {"date": "2026-10-02", "source": "b.md", "text": "the browser MCP worker times out after 80 seconds"},
        ]
        self.assertEqual(len(BH.accumulate(items)), 2)

    def test_the_newer_wording_wins(self):
        items = [
            {"date": "2026-10-01", "source": "a.md", "text": "turn_tail_check is opt in and off by default"},
            {"date": "2026-10-11", "source": "b.md", "text": "turn_tail_check is opt in and on by default now"},
        ]
        merged = BH.accumulate(items)
        self.assertEqual(len(merged), 1, merged)
        self.assertEqual(merged[0]["source"], "b.md")
        self.assertIn("on by default", merged[0]["text"])
        self.assertEqual(merged[0]["also"], ["a.md"])


class Grouping(unittest.TestCase):
    """A topic file is read by subject, not by date: everything about one thing together."""

    def test_the_subject_is_the_identifier_it_names(self):
        self.assertEqual(BH.subject("the `turn_tail_check` flag is on by default"), "turn_tail_check")
        self.assertEqual(BH.subject("the two files `prompt.json` and `prompts.py` are both read"),
                         "prompt.json")   # the first sorted identifier
        # without an identifier, the first content words stand in for it
        self.assertEqual(BH.subject("the worker binds its socket before the model loads"),
                         "worker binds socket")

    def test_related_subjects_join_one_thread(self):
        items = [
            {"date": "2026-10-01", "source": "a.md", "text": "`prefill_ms` is the engine's own read time"},
            {"date": "2026-10-02", "source": "b.md", "text": "`prefill_ms` was missing, so it is derived"},
            {"date": "2026-10-03", "source": "c.md", "text": "`decode_ms` measures the emit window"},
        ]
        threads = BH.group(items)
        self.assertEqual(len(threads), 2, threads)
        first = threads[0][1]
        self.assertEqual([r["source"] for r in first], ["b.md", "a.md"])   # newest first
        self.assertEqual(threads[0][0], "prefill_ms")

    def test_unrelated_entries_do_not_merge(self):
        threads = BH.group([{"date": "2026-10-01", "source": "a.md", "text": "`mcp.yaml` registers servers"},
                            {"date": "2026-10-02", "source": "b.md", "text": "`valgrind` is a Tier 3 tool"}])
        self.assertEqual(len(threads), 2)


class Noise(unittest.TestCase):
    """Thinking out loud is not a finding."""

    def test_reasoning_and_questions_are_dropped(self):
        self.assertTrue(BH.NOISE.match("I will edit the file and run the tests"))
        self.assertTrue(BH.QUESTION.match("should the run script carry the API key?"))
        self.assertFalse(BH.NOISE.match("the hub starts every MCP server at boot"))

    def test_a_source_line_is_not_a_sentence(self):
        self.assertTrue(BH.SKIP_LINE.search("Traceback (most recent call last):"))
        self.assertFalse(BH.SKIP_LINE.search("the worker binds its socket in milliseconds"))


class Output(unittest.TestCase):
    """The files that are written are the ones the README describes."""

    def test_topic_files_exist_for_every_category(self):
        topics = ROOT / "data" / "history" / "topics"
        if not topics.is_dir():          # never built on this machine: nothing to check
            self.skipTest("data/history has not been built")
        for topic in BH.TOPICS:
            self.assertTrue((topics / f"{topic}.md").is_file(), topic)

    def test_a_topic_file_states_the_current_state_before_the_log(self):
        topics = ROOT / "data" / "history" / "topics"
        if not topics.is_dir():
            self.skipTest("data/history has not been built")
        for f in sorted(topics.glob("*.md")):
            text = f.read_text(encoding="utf-8")
            self.assertIn("# ", text.splitlines()[0], f.name)
            self.assertLess(text.find("## Current state"), text.find("## What is true now"), f.name)

    def test_no_entry_is_attributed_to_a_missing_transcript(self):
        index = ROOT / "data" / "history" / "index.json"
        if not index.is_file():
            self.skipTest("data/history has not been built")
        import json
        sources = json.loads(index.read_text(encoding="utf-8"))["sources"]
        for name in sources:
            self.assertTrue((BH.CHATS / name).is_file(), name)


if __name__ == "__main__":
    unittest.main()
