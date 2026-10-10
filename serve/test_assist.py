"""The Assist dropdown's pinned list. No network: the endpoint and the timing are both faked.

serve/assist_fast_models.json is what the dropdown reads. It is written by tools/assist_latency_probe.py
after timing every model, and edited by hand afterwards - so the tests cover both paths.
"""
import json
import os
import tempfile
import time
import unittest
from pathlib import Path

from serve import assist

CATALOG = ["nvidia/fast-one", "nvidia/fast-two", "nvidia/slow-one", "nvidia/gone"]


class Endpoint(unittest.TestCase):
    """list_models() against a pinned allowlist."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "assist_fast_models.json"
        self.original = assist.FAST_LIST_PATH
        assist.FAST_LIST_PATH = self.path
        self.request = assist._request
        assist._request = lambda endpoint, key, path, payload=None, timeout=None: {
            "data": [{"id": m, "owned_by": "nvidia", "created": 1} for m in CATALOG]}

    def tearDown(self):
        assist._request = self.request
        assist.FAST_LIST_PATH = self.original
        self.tmp.cleanup()

    def test_without_a_pinned_file_everything_is_offered(self):
        listed = assist.list_models()
        self.assertFalse(listed["pinned"])
        self.assertEqual([m["id"] for m in listed["models"]], sorted(CATALOG))

    def test_the_pinned_ids_are_the_dropdown(self):
        self.path.write_text(json.dumps({"max_lag_s": 1.0, "updated": "2026-10-09T00:00:00+0000",
                                        "models": [{"id": "nvidia/fast-one", "ttft_s": 0.31},
                                                   {"id": "nvidia/fast-two", "ttft_s": 0.94}]}), encoding="utf-8")
        listed = assist.list_models()
        self.assertTrue(listed["pinned"])
        self.assertEqual([m["id"] for m in listed["models"]], ["nvidia/fast-one", "nvidia/fast-two"])
        self.assertEqual(listed["models"][0]["lag_s"], 0.31)
        self.assertEqual(listed["filter"]["max_lag_s"], 1.0)

    def test_show_all_ignores_the_pin(self):
        self.path.write_text(json.dumps({"models": [{"id": "nvidia/fast-one"}]}), encoding="utf-8")
        self.assertEqual(len(assist.list_models(show_all=True)["models"]), len(CATALOG))

    def test_a_plain_list_of_ids_is_as_good_as_the_objects(self):
        self.path.write_text(json.dumps({"models": ["nvidia/fast-two"]}), encoding="utf-8")
        self.assertEqual([m["id"] for m in assist.list_models()["models"]], ["nvidia/fast-two"])

    def test_a_model_the_endpoint_no_longer_serves_is_dropped(self):
        self.path.write_text(json.dumps({"models": [{"id": "nvidia/retired"}, {"id": "nvidia/fast-one"}]}),
                            encoding="utf-8")
        listed = assist.list_models()
        self.assertEqual([m["id"] for m in listed["models"]], ["nvidia/fast-one"])
        self.assertEqual(listed["filter"]["dropped"], ["nvidia/retired"])

    def test_a_broken_file_does_not_empty_the_dropdown(self):
        self.path.write_text("{not json", encoding="utf-8")
        self.assertFalse(assist.list_models()["pinned"])
        self.assertEqual(len(assist.list_models()["models"]), len(CATALOG))


class Probe(unittest.TestCase):
    """probe_models() writes the allowlist from measured lag."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "assist_fast_models.json"
        self.original = assist.FAST_LIST_PATH
        assist.FAST_LIST_PATH = self.path
        self.saved_log, self.saved_keep = assist.LOG_PATH, assist.LOG_KEEP
        assist.LOG_KEEP = 0                                       # probe_models records itself; not while testing
        self.request = assist._request
        assist._request = lambda endpoint, key, path, payload=None, timeout=None: {
            "data": [{"id": m} for m in CATALOG]}
        self.timed = assist._timed_chat
        lags = {"nvidia/fast-one": 0.3, "nvidia/fast-two": 0.9, "nvidia/slow-one": 4.2}

        def timed(endpoint, key, model, timeout):
            if model not in lags:
                raise RuntimeError("HTTP 404: model not found")
            return {"ttft": lags[model], "total": lags[model] + 0.1}

        assist._timed_chat = timed

    def tearDown(self):
        assist._timed_chat = self.timed
        assist._request = self.request
        assist.FAST_LIST_PATH = self.original
        assist.LOG_PATH, assist.LOG_KEEP = self.saved_log, self.saved_keep
        self.tmp.cleanup()

    def test_only_models_under_the_limit_survive(self):
        result = assist.probe_models(max_lag=1.0, rounds=2, workers=2, out=self.path)
        self.assertEqual(result["probed"], len(CATALOG))
        self.assertEqual(result["kept"], 2)
        pinned = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual([m["id"] for m in pinned["models"]], ["nvidia/fast-one", "nvidia/fast-two"])
        self.assertEqual(pinned["max_lag_s"], 1.0)

    def test_the_models_over_the_limit_are_kept_in_the_same_file(self):
        assist.probe_models(max_lag=1.0, rounds=2, workers=2, out=self.path)
        pinned = json.loads(self.path.read_text(encoding="utf-8"))
        # the fixture times fast-one 0.31s and fast-two 0.44s; slow-one is 2.4s and gone 404s
        self.assertEqual([m["id"] for m in pinned["models"]], ["nvidia/fast-one", "nvidia/fast-two"])
        self.assertEqual([m["id"] for m in pinned["over_limit"]], ["nvidia/slow-one", "nvidia/gone"])
        self.assertEqual([m["id"] for m in assist._over_limit_models()], ["nvidia/slow-one", "nvidia/gone"])
        # the dropdown is still only the pinned ones
        self.assertEqual([m["id"] for m in assist.list_models()["models"]], ["nvidia/fast-one", "nvidia/fast-two"])
        # ... and the Assist tab is told why the others are not there, with the reason
        listed = assist.list_models()
        self.assertEqual([m["id"] for m in listed["over_limit"]], ["nvidia/slow-one", "nvidia/gone"])
        self.assertEqual(listed["over_limit"][0]["ttft_s"], 4.2)
        self.assertIn("404", listed["over_limit"][1]["error"])

    def test_a_truncated_answer_is_recorded_as_truncated(self):
        assist._request = lambda endpoint, key, path, payload=None, timeout=None: {
            "model": "nvidia/fast-one", "id": "x",
            "choices": [{"message": {"content": "a very long answer"}, "finish_reason": "length"}],
            "usage": {"completion_tokens": 512},
        }
        saved_log, saved_keep = assist.LOG_PATH, assist.LOG_KEEP
        assist.LOG_PATH = Path(self.tmp.name) / "calls.jsonl"
        assist.LOG_KEEP = 10
        try:
            result = assist.converse("nvidia/fast-one", [{"role": "user", "content": "hi"}], max_tokens=512)
            self.assertEqual(result["finish_reason"], "length")
            entry = json.loads(assist.LOG_PATH.read_text(encoding="utf-8"))
            self.assertTrue(entry["truncated"])
        finally:
            assist.LOG_PATH, assist.LOG_KEEP = saved_log, saved_keep

    def test_the_model_that_never_answers_is_left_out(self):
        result = assist.probe_models(max_lag=1.0, rounds=1, workers=1, out=self.path)
        slow = [m for m in result["models"] if not m["ok"]]
        self.assertEqual([m["id"] for m in slow], ["nvidia/gone"])
        self.assertIn("404", slow[0]["error"])
        self.assertNotIn("nvidia/gone", [m["id"] for m in result["allowlist"]])

    def test_the_pin_it_writes_is_what_the_dropdown_reads(self):
        assist.probe_models(max_lag=1.0, rounds=2, workers=2, out=self.path)
        self.assertEqual([m["id"] for m in assist.list_models()["models"]], ["nvidia/fast-one", "nvidia/fast-two"])

    def test_everything_survives_when_no_model_is_fast(self):
        result = assist.probe_models(max_lag=0.01, rounds=1, workers=2, out=self.path)
        self.assertEqual(result["kept"], 0)
        # an empty dropdown is worse than a slow one: the file still holds the whole table
        self.assertEqual(len(json.loads(self.path.read_text(encoding="utf-8"))["models"]), len(CATALOG))

    def test_a_throttled_probe_does_not_drop_a_model_it_pinned_before(self):
        """kimi-k3 disappearing from the dropdown because the endpoint 429'd is not a finding about kimi."""
        self.path.write_text(json.dumps({"models": [{"id": "nvidia/throttled-one", "ttft_s": 0.4, "ok": True}]}),
                            encoding="utf-8")
        assist._request = lambda endpoint, key, path, payload=None, timeout=None: {
            "data": [{"id": m} for m in CATALOG + ["nvidia/throttled-one"]]}
        saved_delay = assist.RETRY_DELAY_S
        assist.RETRY_DELAY_S = 0.0

        def timed(endpoint, key, model, timeout):
            if model == "nvidia/throttled-one":
                raise assist.urllib.error.HTTPError("", 429, "Too Many Requests", None, None)
            if model in ("nvidia/fast-one", "nvidia/fast-two"):
                return {"ttft": 0.3, "total": 0.4}
            if model == "nvidia/slow-one":
                return {"ttft": 4.2, "total": 4.3}
            raise RuntimeError("HTTP 404: model not found")

        assist._timed_chat = timed
        try:
            result = assist.probe_models(max_lag=1.0, rounds=1, workers=2, out=self.path)
            pinned = json.loads(self.path.read_text(encoding="utf-8"))
            ids = [m["id"] for m in pinned["models"]]
            self.assertIn("nvidia/throttled-one", ids)          # kept, flagged as unverified
            self.assertEqual(result["held"], 1)
            self.assertEqual([m["reason"] for m in pinned["models"] if m["id"] == "nvidia/throttled-one"],
                            ["rate limited"])
            # a model that is genuinely slower than the limit is still dropped
            self.assertNotIn("nvidia/slow-one", ids)
            self.assertIn("nvidia/slow-one", [m["id"] for m in pinned["over_limit"]])
            # ... and the dropdown says why the kept one has no lag
            listed = assist.list_models()
            entry = [m for m in listed["models"] if m["id"] == "nvidia/throttled-one"][0]
            self.assertIsNone(entry["lag_s"])
            self.assertIn("429", entry["error"])
        finally:
            assist.RETRY_DELAY_S = saved_delay

    def test_a_404_is_reported_as_not_available_not_as_slow(self):
        assist.probe_models(max_lag=1.0, rounds=1, workers=2, out=self.path)
        over = json.loads(self.path.read_text(encoding="utf-8"))["over_limit"]
        self.assertEqual([m["reason"] for m in over], ["over the limit", "not available"])

    def test_a_model_measured_slow_after_being_pinned_is_dropped(self):
        self.path.write_text(json.dumps({"models": [{"id": "nvidia/slow-one", "ttft_s": 0.5, "ok": True}]}),
                            encoding="utf-8")
        result = assist.probe_models(max_lag=1.0, rounds=1, workers=2, out=self.path)
        ids = [m["id"] for m in json.loads(self.path.read_text(encoding="utf-8"))["models"]]
        self.assertNotIn("nvidia/slow-one", ids)
        self.assertEqual(result["held"], 0)


class CallLog(unittest.TestCase):
    """record_call()/call_log() - what the Monitor's "External assistants" card reads. No network."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.log = Path(self.tmp.name) / "calls.jsonl"
        self.saved_log, self.saved_keep = assist.LOG_PATH, assist.LOG_KEEP
        assist.LOG_PATH = self.log

    def tearDown(self):
        assist.LOG_PATH, assist.LOG_KEEP = self.saved_log, self.saved_keep
        self.tmp.cleanup()

    def test_calls_are_read_back_newest_first(self):
        assist.record_call("chat", "nvidia/fast-one", True, 1.2,
                          {"prompt_tokens": 10, "completion_tokens": 5}, chars=42)
        assist.record_call("chat", "nvidia/gone", False, 3.4, error="the model returned no choices")
        log = assist.call_log(limit=10)
        self.assertEqual([c["model"] for c in log["calls"]], ["nvidia/gone", "nvidia/fast-one"])
        self.assertFalse(log["calls"][0]["ok"])
        self.assertEqual(log["calls"][1]["completion_tokens"], 5)
        self.assertEqual(log["call_count"], 2)

    def test_the_log_stays_bounded(self):
        assist.LOG_KEEP = 3
        for i in range(10):
            assist.record_call("chat", f"nvidia/m{i}", True, 0.1)
        self.assertEqual(len(assist.call_log(limit=50)["calls"]), 3)

    def test_turning_the_log_off_writes_nothing(self):
        assist.LOG_KEEP = 0
        assist.record_call("chat", "nvidia/fast-one", True, 0.2)
        self.assertFalse(self.log.exists())
        self.assertEqual(assist.call_log()["calls"], [])



class SharedPaths(unittest.TestCase):
    """More than one account works on this project, and a file one of them owns is not writable by the
    next. Two files with the same name and different contents is the "the popup said 12 and the list
    still shows 10" report: one number, one file, and the stale copy removed."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "serve").mkdir()
        self.configured = self.root / "serve" / "assist_fast_models.json"
        self.configured.write_text(json.dumps({"models": [{"id": "nvidia/fast-one", "ttft_s": 0.4}]}),
                                   encoding="utf-8")
        self.saved = assist.FAST_LIST_PATH, assist.FAST_LIST_NOTE, assist.LOG_PATH, assist.LOG_KEEP

    def tearDown(self):
        assist.FAST_LIST_PATH, assist.FAST_LIST_NOTE, assist.LOG_PATH, assist.LOG_KEEP = self.saved
        self.tmp.cleanup()

    def test_two_copies_converge_into_one_and_the_stale_one_is_deleted(self):
        other = self.root / "assist_fast_models.json"
        other.write_text(json.dumps({"models": [{"id": "nvidia/old-one", "ttft_s": 0.9}]}), encoding="utf-8")
        other.chmod(0o666)
        stamp = time.time() + 60                           # the configured copy is the newer of the two
        os.utime(self.configured, (stamp, stamp))
        path, note = assist._converge(self.configured, assist._merge_json)
        self.assertEqual(path, self.configured)            # the documented path, not a per-user copy
        self.assertFalse(other.exists())
        self.assertIn("merged 2 copies", note)
        self.assertEqual([m["id"] for m in json.loads(path.read_text(encoding="utf-8"))["models"]],
                        ["nvidia/fast-one"])               # newest content, not the older sibling

    def test_a_copy_another_account_owns_is_rewritten_in_place_not_beside_it(self):
        self.configured.chmod(0o444)                      # readable, not writable: it belongs to someone else
        path, _ = assist._converge(self.configured, assist._merge_json)
        self.assertEqual(path, self.configured)
        self.assertTrue(path.stat().st_mode & 0o066)      # the next account can write the same file
        assist.FAST_LIST_PATH = path
        # the content survives the rewrite: an empty file would un-pin the dropdown
        self.assertEqual([m["id"] for m in assist._pinned_models()], ["nvidia/fast-one"])

    def test_the_newer_copy_wins_when_the_configured_one_cannot_be_written(self):
        other = self.root / "assist_fast_models.json"
        other.write_text(json.dumps({"models": [{"id": "nvidia/fast-two", "ttft_s": 0.2}]}), encoding="utf-8")
        other.chmod(0o666)
        os.utime(other, (time.time() + 60, time.time() + 60))
        self.configured.chmod(0o444)
        path, _ = assist._converge(self.configured, assist._merge_json)
        assist.FAST_LIST_PATH = path
        self.assertEqual([m["id"] for m in assist._pinned_models()], ["nvidia/fast-two"])

    def test_check_lag_writes_to_the_file_the_dropdown_reads(self):
        self.configured.chmod(0o444)
        assist.FAST_LIST_PATH, _ = assist._converge(self.configured, assist._merge_json)
        saved = assist._request, assist._timed_chat, assist.LOG_KEEP
        assist._request = lambda *a, **k: {"data": [{"id": "nvidia/fast-one"}, {"id": "nvidia/slow-one"}]}
        assist._timed_chat = lambda e, k, m, t: {"ttft": 0.2 if m == "nvidia/fast-one" else 5.0, "total": 1.0}
        assist.LOG_KEEP = 0
        try:
            result = assist.probe_models(max_lag=1.0, rounds=1, workers=2)
            self.assertEqual(result["file"], str(assist.FAST_LIST_PATH))
            self.assertEqual(result["pinned"], 1)
            self.assertEqual([m["id"] for m in assist.list_models()["models"]], ["nvidia/fast-one"])
            self.assertEqual([m["id"] for m in assist.list_models()["over_limit"]], ["nvidia/slow-one"])
        finally:
            assist._request, assist._timed_chat, assist.LOG_KEEP = saved

    def test_a_probe_leaves_one_file_not_two(self):
        other = self.root / "assist_fast_models.json"
        other.write_text(json.dumps({"models": [{"id": "nvidia/old-one", "ttft_s": 0.4}]}), encoding="utf-8")
        other.chmod(0o666)
        self.configured.chmod(0o666)
        os.utime(self.configured, (time.time() + 60, time.time() + 60))
        assist.FAST_LIST_PATH, _ = assist._converge(self.configured, assist._merge_json)
        saved = assist._request, assist._timed_chat, assist.LOG_KEEP
        assist._request = lambda *a, **k: {"data": [{"id": "nvidia/fast-one"}, {"id": "nvidia/slow-one"}]}
        assist._timed_chat = lambda e, k, m, t: {"ttft": 0.2 if m == "nvidia/fast-one" else 5.0, "total": 1.0}
        assist.LOG_KEEP = 0
        try:
            assist.probe_models(max_lag=1.0, rounds=1, workers=2)
            # There is no second file to read stale: the probe and the dropdown use the same one.
            self.assertFalse(other.exists())
            self.assertEqual([m["id"] for m in json.loads(self.configured.read_text(encoding="utf-8"))["models"]],
                             ["nvidia/fast-one"])
            self.assertTrue(self.configured.stat().st_mode & 0o066)
        finally:
            assist._request, assist._timed_chat, assist.LOG_KEEP = saved

    def test_the_call_log_is_one_history_not_two(self):
        own = self.root / "serve" / "calls.jsonl"
        other = self.root / "calls.jsonl"
        own.write_text('{"ts": "2026-10-09T12:00:00+0000", "kind": "chat", "model": "a", "ok": true}\n',
                       encoding="utf-8")
        other.write_text('{"ts": "2026-10-09T11:00:00+0000", "kind": "probe", "model": "b", "ok": true}\n'
                         + '{"ts": "2026-10-09T12:00:00+0000", "kind": "chat", "model": "a", "ok": true}\n',
                         encoding="utf-8")
        saved = assist.LOG_PATH, assist.LOG_KEEP
        merged, _ = assist._converge(own, assist._merge_jsonl)
        assist.LOG_PATH, assist.LOG_KEEP = merged, 10
        try:
            self.assertFalse(other.exists())
            assist.record_call("chat", "c", True, 0.3)
            models = [c["model"] for c in assist.call_log()["calls"]][:3]
            self.assertEqual(models, ["c", "a", "b"])      # newest first, both files, the duplicate once
        finally:
            assist.LOG_PATH, assist.LOG_KEEP = saved


class SeparateFromTheLocalEngine(unittest.TestCase):
    """The Assist tab is not the local model. Inheriting the run config's temperature, sampler or
    context size would make a hosted endpoint's limits look like the local engine's, and the answer
    would be blamed on the wrong one."""

    def setUp(self):
        self.saved = assist._request, assist.LOG_KEEP

    def tearDown(self):
        assist._request, assist.LOG_KEEP = self.saved

    def _fake(self, captured):
        def fake_request(endpoint, key, path, payload=None, timeout=None):
            captured["body"] = payload
            return {"model": "nvidia/other", "choices": [{"message": {"content": "fine"},
                                                          "finish_reason": "stop"}], "usage": {}}
        return fake_request

    def test_the_bridge_carries_its_own_defaults(self):
        self.assertGreater(assist.ASSIST_DEFAULTS["max_tokens"], 0)
        self.assertGreater(assist.ASSIST_DEFAULTS["timeout_s"], 0)
        self.assertGreaterEqual(assist.ASSIST_DEFAULTS["max_lag_s"], 0.0)

    def test_the_request_body_has_no_local_sampling_fields(self):
        captured = {}
        assist._request = self._fake(captured)
        assist.LOG_KEEP = 0
        assist.converse("nvidia/other", [{"role": "user", "content": "hi"}])
        body = captured["body"]
        self.assertEqual(body["max_tokens"], assist.ASSIST_DEFAULTS["max_tokens"])
        for key in ("temperature", "top_p", "top_k", "reasoning_effort", "seed", "context"):
            self.assertNotIn(key, body)

    def test_a_caller_can_still_set_the_cap(self):
        captured = {}
        assist._request = self._fake(captured)
        assist.LOG_KEEP = 0
        assist.converse("nvidia/other", [{"role": "user", "content": "hi"}], max_tokens=64)
        self.assertEqual(captured["body"]["max_tokens"], 64)

if __name__ == "__main__":
    unittest.main()
