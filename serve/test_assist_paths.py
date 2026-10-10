"""The Assist files are shared by more than one account. No network.

serve/assist_fast_models.json and serve/data/assist_calls.jsonl were created by another user, so this
account can read them but not write them. A probe that writes one file while the dropdown reads another
pins 12 models and the page still shows 10 - which is exactly what looked like a bug. These tests cover
the fallback: which file is written, which file is read, and that the reason is reported instead of
failing quietly.
"""
import json
import tempfile
import unittest
from pathlib import Path

from serve import assist


class SharedProject(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.serve = self.root / "serve"
        self.serve.mkdir()
        self.saved = (assist.FAST_LIST_PATH, assist.FAST_LIST_NOTE,
                      assist.LOG_PATH, assist.LOG_NOTE)
        assist.LOG_PATH = self.root / "calls.jsonl"      # keep the real log out of the test
        assist.LOG_NOTE = ""
        assist.FAST_LIST_PATH = self.serve / "assist_fast_models.json"
        assist.FAST_LIST_NOTE = ""

    def tearDown(self):
        assist.FAST_LIST_PATH, assist.FAST_LIST_NOTE = self.saved[:2]
        assist.LOG_PATH, assist.LOG_NOTE = self.saved[2:]
        self.tmp.cleanup()

    def test_a_read_only_file_falls_back_and_says_so(self):
        theirs = assist.FAST_LIST_PATH
        theirs.write_text(json.dumps({"max_lag_s": 1.0, "models": [{"id": "nvidia/other-account"}]}),
                         encoding="utf-8")
        theirs.chmod(0o444)                              # readable by everyone, writable by nobody
        path, note = assist._writable(theirs)
        self.assertEqual(path, self.root / "assist_fast_models.json")
        self.assertIn("not writable", note)
        # The fallback is a copy, not an empty file: an empty one would un-pin the dropdown.
        self.assertEqual([m["id"] for m in assist._pinned_models()], ["nvidia/other-account"])

    def test_the_newest_existing_file_is_the_one_written_to(self):
        older = self.root / "assist_fast_models.json"
        older.write_text(json.dumps({"models": [{"id": "nvidia/older"}]}), encoding="utf-8")
        newer = self.serve / "assist_fast_models.json"
        newer.write_text(json.dumps({"models": [{"id": "nvidia/newer"}]}), encoding="utf-8")
        self.assertEqual(assist._read_path(newer), newer)
        path, note = assist._writable(newer)
        self.assertEqual(path, newer)
        self.assertEqual(note, "")

    def test_a_probe_writes_the_file_the_dropdown_then_reads(self):
        theirs = assist.FAST_LIST_PATH
        theirs.write_text(json.dumps({"max_lag_s": 1.0, "models": [{"id": "nvidia/other-account"}]}),
                         encoding="utf-8")
        theirs.chmod(0o444)
        assist.FAST_LIST_PATH, assist.FAST_LIST_NOTE = assist._writable(theirs)
        saved = assist._timed_chat
        assist._timed_chat = lambda endpoint, key, model, timeout: {"ttft": 0.2, "total": 0.3}
        try:
            result = assist.probe_models(models=["nvidia/new-fast"], max_lag=1.0, rounds=1, workers=1)
        finally:
            assist._timed_chat = saved
        self.assertEqual(result["file"], str(assist.FAST_LIST_PATH))
        self.assertIn("not writable", result["note"])                # the page has to be able to say it
        self.assertEqual([m["id"] for m in assist._pinned_models()], ["nvidia/new-fast"])
        listed = assist.list_models()
        self.assertEqual(listed["filter"]["file"], str(assist.FAST_LIST_PATH))
        self.assertIn("not writable", listed["filter"]["note"])

    def test_a_broken_fallback_does_not_empty_the_dropdown(self):
        assist.FAST_LIST_PATH = self.root / "assist_fast_models.json"
        assist.FAST_LIST_PATH.write_text("{not json", encoding="utf-8")
        self.assertEqual(assist._pinned_models(), [])


if __name__ == "__main__":
    unittest.main()
