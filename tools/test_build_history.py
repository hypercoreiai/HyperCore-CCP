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

    def test_only_real_categories_get_a_topic_file(self):
        topics = ROOT / "data" / "history" / "topics"
        if not topics.is_dir():          # never built on this machine: nothing to check
            self.skipTest("data/history has not been built")
        for f in topics.glob("*.md"):
            self.assertIn(f.stem, BH.TOPICS, f.name)   # no invented category
        index = ROOT / "data" / "history" / "index.json"
        if not index.is_file():
            self.skipTest("index.json is missing")
        import json
        # A category with no entries gets no file; one with entries must have one.
        for topic, count in json.loads(index.read_text(encoding="utf-8"))["topics"].items():
            self.assertGreater(count, 0, topic)
            self.assertTrue((topics / f"{topic}.md").is_file(), topic)

    def test_a_topic_file_states_the_current_state_before_the_log(self):
        topics = ROOT / "data" / "history" / "topics"
        if not topics.is_dir():
            self.skipTest("data/history has not been built")
        for f in sorted(topics.glob("*.md")):
            text = f.read_text(encoding="utf-8")
            self.assertIn("# ", text.splitlines()[0], f.name)
            now, log = text.find("## Current state"), text.find("## What is true now")
            if now >= 0 and log >= 0:      # a section with no entries is simply absent
                self.assertLess(now, log, f.name)

    def test_no_entry_is_attributed_to_a_missing_transcript(self):
        index = ROOT / "data" / "history" / "index.json"
        if not index.is_file():
            self.skipTest("data/history has not been built")
        import json
        doc = json.loads(index.read_text(encoding="utf-8"))
        if "source_folders" not in doc:      # built before the builder recorded its folders
            self.skipTest("index.json does not say which folders it was built from")
        folders = [Path(f) for f in doc["source_folders"]]
        for name in doc["sources"]:
            hit = any((folder / name).is_file() or (folder / name.split("/")[-1]).is_file()
                      for folder in folders)
            self.assertTrue(hit, name)

    def test_every_source_folder_named_in_index_json_exists(self):
        index = ROOT / "data" / "history" / "index.json"
        if not index.is_file():
            self.skipTest("data/history has not been built")
        import json
        doc = json.loads(index.read_text(encoding="utf-8"))
        if "source_folders" not in doc:
            self.skipTest("index.json does not record its source folders")
        for folder in doc["source_folders"]:
            self.assertTrue(Path(folder).is_dir(), folder)


class Scrubbing(unittest.TestCase):
    """A history that is shared with the repository carries no personal information."""

    def test_keys_tokens_and_addresses_are_replaced(self):
        s = ("the remote `origin` keeps the token ghp_TESTTOKEN0123456789abcdef "
            "and the account test@example.com, with the Daytona key "
            "dtn_TESTDAYTONA0123456789abcdef and "
            "the NVIDIA key nvapi-TESTNVIDIAKEY0123456789abcdef "
            "and the handle @testuser")
        out = BH.scrub(s)
        for secret in ("ghp_", "dtn_", "nvapi-", "@gmail.com", "@testuser"):
            self.assertNotIn(secret, out, secret)
        for marker in ("[key]", "[email]", "[handle]"):
            self.assertIn(marker, out, marker)

    def test_fastapi_decorators_are_not_read_as_addresses(self):
        for code in ("n@app.get returns the status", "n@app.on startup runs the hub",
                     "the handler @app.post writes the log"):
            self.assertEqual(BH.scrub(code), code, code)

    def test_clean_scrubs_as_well_as_tidying(self):
        self.assertIn("[key]", BH.clean("- the remote `origin` keeps ghp_TESTTOKEN0123456789abcdef"))

    def test_a_sentence_from_a_transcript_survives_scrubbed(self):
        text = ("## You\nrun the checkpoint and push it\n\n"
                "## Assistant\n- the remote `origin` keeps the token "
                "ghp_TESTTOKEN0123456789abcdef for the account test@example.com\n")
        found = BH.sentences(text)
        self.assertTrue(found, "the fixture sentence should be kept")
        for sent in found:
            self.assertNotIn("ghp_", sent, sent)
            self.assertNotIn("@gmail.com", sent, sent)


class Source(unittest.TestCase):
    """The transcripts are outside the repository, and more than one folder can be read
    in a single pass."""

    def test_the_default_is_the_current_tree_then_the_older_one(self):
        self.assertEqual([str(p) for p in BH.DEFAULT_SOURCES],
                         ["/home/ai-user0/black_box_chats", "/home/ai-user0/Strata_chats"])
        self.assertEqual(BH.SOURCES, list(BH.DEFAULT_SOURCES))

    def test_parse_sources_splits_a_comma_or_space_separated_list(self):
        got = BH.parse_sources("/a/b, /a/c")
        self.assertEqual([str(p) for p in got], ["/a/b", "/a/c"])
        self.assertEqual(BH.parse_sources(None), list(BH.DEFAULT_SOURCES))

    def test_a_source_and_an_out_dir_given_on_the_command_line_are_used(self):
        import tempfile
        fixture = ("# chat\n\n## You\nrun the checkpoint and push it\n\n"
                   "## Assistant\n- the `browser_mcp` server keeps the token "
                   "ghp_TESTTOKEN0123456789abcdef for test@example.com\n"
                   "- the `browser_mcp` server is a separate worker process\n")
        with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as out:
            Path(src, "2026-10-11-chat.md").write_text(fixture * 6, encoding="utf-8")
            saved, sys.argv = sys.argv, ["build_history.py", "--source", src, "--out", out]
            try:
                code = BH.main()
                used = list(BH.SOURCES)
            finally:
                sys.argv, BH.SOURCES, BH.HIST = saved, list(BH.DEFAULT_SOURCES), BH.HIST
            self.assertEqual(code, 0, "the builder found the transcripts it was given")
            self.assertEqual(used, [Path(src)])
            written = [p for p in Path(out).rglob("*") if p.is_file()]
            self.assertTrue(written, "nothing was written")
            for p in written:
                self.assertNotIn("ghp_", p.read_text(encoding="utf-8"), p.name)

    def test_two_folders_are_merged_in_one_pass(self):
        import json
        import tempfile
        a = ("# chat a\n\n## You\nfix the browser worker\n\n"
             "## Assistant\n- the `browser_mcp` server keeps its worker alive between requests\n")
        b = ("# chat b\n\n## You\ncheck the cache\n\n"
             "## Assistant\n- the `expert_source.cpp` expert cache is cleared on every layer split\n")
        with tempfile.TemporaryDirectory() as fa, tempfile.TemporaryDirectory() as fb, \
             tempfile.TemporaryDirectory() as out:
            Path(fa, "2026-10-11-chat.md").write_text(a * 6, encoding="utf-8")
            Path(fb, "2026-10-02-chat.md").write_text(b * 6, encoding="utf-8")
            saved, sys.argv = sys.argv, ["build_history.py", "--source", f"{fa},{fb}", "--out", out]
            try:
                code = BH.main()
            finally:
                sys.argv, BH.SOURCES, BH.HIST = saved, list(BH.DEFAULT_SOURCES), BH.HIST
            self.assertEqual(code, 0)
            doc = json.loads((Path(out) / "index.json").read_text(encoding="utf-8"))
            self.assertEqual(doc["transcripts"], 2, doc["transcripts"])
            self.assertEqual(sorted(doc["source_folders"]), sorted([fa, fb]))
            text = "".join(p.read_text(encoding="utf-8") for p in Path(out, "topics").glob("*.md"))
            self.assertIn("browser_mcp", text)
            self.assertIn("expert cache", text)

    def test_the_same_file_name_in_two_folders_is_not_collapsed(self):
        import json
        import tempfile
        body = ("# chat\n\n## You\nfix the worker\n\n"
                "## Assistant\n- the `browser_mcp` server keeps its worker alive between requests\n")
        with tempfile.TemporaryDirectory() as fa, tempfile.TemporaryDirectory() as fb, \
             tempfile.TemporaryDirectory() as out:
            Path(fa, "2026-10-11-chat.md").write_text(body * 6, encoding="utf-8")
            Path(fb, "2026-10-11-chat.md").write_text(body * 6, encoding="utf-8")
            saved, sys.argv = sys.argv, ["build_history.py", "--source", f"{fa},{fb}", "--out", out]
            try:
                BH.main()
            finally:
                sys.argv, BH.SOURCES, BH.HIST = saved, list(BH.DEFAULT_SOURCES), BH.HIST
            doc = json.loads((Path(out) / "index.json").read_text(encoding="utf-8"))
            labels = sorted(doc["sources"])
            self.assertEqual(len(labels), 2, labels)          # both kept, not merged
            self.assertTrue(any("/" in l for l in labels), labels)

    def test_a_hand_written_note_is_inserted_scrubbed(self):
        import tempfile
        fixture = ("# chat\n\n## You\nrun the checkpoint and push it\n\n"
                   "## Assistant\n- the `browser_mcp` server keeps the token "
                   "ghp_TESTTOKEN0123456789abcdef for test@example.com\n"
                   "- the `browser_mcp` server is a separate worker process\n")
        with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as out:
            Path(src, "2026-10-11-chat.md").write_text(fixture * 6, encoding="utf-8")
            notes = Path(out, "notes")
            notes.mkdir(parents=True)
            for topic in BH.TOPICS:
                (notes / f"{topic}.md").write_text(
                    f"# {topic}\n\nthe account is test@example.com and the key is "
                    "ghp_TESTTOKEN0123456789abcdef\n", encoding="utf-8")
            saved, sys.argv = sys.argv, ["build_history.py", "--source", src, "--out", out]
            try:
                code = BH.main()
            finally:
                sys.argv, BH.SOURCES, BH.HIST = saved, list(BH.DEFAULT_SOURCES), BH.HIST
            self.assertEqual(code, 0)
            for f in Path(out, "topics").glob("*.md"):
                text = f.read_text(encoding="utf-8")
                self.assertIn("## Current state", text, f.name)   # the note is kept
                self.assertNotIn("ghp_TESTTOKEN", text, f.name)   # but scrubbed
                self.assertNotIn("test@example.com", text, f.name)

    def test_a_missing_source_reports_and_returns_non_zero(self):
        saved, BH.SOURCES, sys.argv = BH.SOURCES, [Path("/no/such/transcript/folder")], ["build_history.py"]
        try:
            self.assertEqual(BH.main(), 1)
        finally:
            sys.argv, BH.SOURCES = saved, list(BH.DEFAULT_SOURCES)


if __name__ == "__main__":
    unittest.main()
