"""serve/test_prompts.py - the agent profiles in prompt.json, and what GET /prompts hands the web app.

    python -m unittest serve.test_prompts -v

The dropdown in the chat composer is built from this endpoint, so a profile added to the file is a
choice in the menu with nothing changed in the page or in the code. These tests run against the mock
engine: no GPU, no model pack.
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from serve.frontend import ChatTemplate
from serve.prompts import MAX_PROMPT_CHARS, catalog, render_prompt
from serve.server import ByteTokenizer, MockEngine, serve

ROOT = Path(__file__).resolve().parents[1]

PROFILE = {
    "system_prompt": {
        "role_and_persona": "You are the core operating layer.",
        "architectural_guidelines": {"context_management": "Be concise."},
        "formatting_and_communication": ["Use Markdown.", "Be direct."],
    },
    "expert_coding_agent": {
        "agent_profile": {"name": "HyperCore-Nexus-Architect", "role": "Principal Engineer",
                         "capabilities": ["test_driven_development"]},
        "execution_framework": {"phase_1_ingestion": ["Read the state file."]},
    },
    "expert_research_agent": {
        "agent_profile": {"name": "HyperCore-Intel-Scout", "role": "OSINT Researcher"},
        "intelligence_reporting_standards": {"citation_policy": "Cite every claim."},
    },
}


class Catalog(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = Path(self.dir) / "prompt.json"
        self.write(PROFILE)

    def write(self, data):
        self.path.write_text(json.dumps(data), encoding="utf-8")

    def test_the_system_prompt_and_every_agent_are_read(self):
        c = catalog(self.path)
        self.assertEqual(c["agents"] and [a["key"] for a in c["agents"]],
                        ["expert_coding_agent", "expert_research_agent"])
        self.assertIn("core operating layer", c["system"])
        coder = c["agents"][0]
        self.assertEqual(coder["name"], "HyperCore-Nexus-Architect")
        self.assertEqual(coder["role"], "Principal Engineer")
        self.assertEqual(coder["capabilities"], ["Test Driven Development"])
        self.assertIn("Read the state file.", coder["prompt"])

    def test_a_profile_added_to_the_file_appears_without_restarting(self):
        first = catalog(self.path)
        self.assertEqual(len(first["agents"]), 2)
        extra = dict(PROFILE)
        extra["expert_vision_agent"] = {"agent_profile": {"name": "HyperCore-Vision-Reader"}}
        self.write(extra)
        now = catalog(self.path)
        self.assertEqual([a["key"] for a in now["agents"]],
                        ["expert_coding_agent", "expert_research_agent", "expert_vision_agent"])
        self.assertEqual(now["agents"][2]["name"], "HyperCore-Vision-Reader")

    def test_a_key_without_a_name_is_titled_from_the_key(self):
        self.write({"system_prompt": "Be helpful.", "vision_agent": {"scope": "images"}})
        a = catalog(self.path)["agents"][0]
        self.assertEqual(a["key"], "vision_agent")
        self.assertEqual(a["name"], "Vision Agent")
        self.assertIn("Scope", a["prompt"])

    def test_the_file_is_not_re_read_when_it_has_not_changed(self):
        first = catalog(self.path)
        self.assertIs(catalog(self.path), first)

    def test_a_missing_or_broken_file_is_not_an_error(self):
        self.path.unlink()
        c = catalog(self.path)
        self.assertEqual(c["agents"], [])
        self.assertEqual(c["system"], "")
        self.assertIn("is not there", c["error"])
        self.path.write_text("{not json", encoding="utf-8")
        c = catalog(self.path)
        self.assertEqual(c["agents"], [])
        self.assertIn("could not read", c["error"])

    def test_a_very_long_profile_is_cut_off_not_sent_whole(self):
        self.write({"system_prompt": {"notes": ["x" * 30_000]}})
        c = catalog(self.path)
        self.assertEqual(len(c["system"]), MAX_PROMPT_CHARS + len("\n[... the rest of this profile is not shown]"))
        self.assertTrue(c["system"].endswith("[... the rest of this profile is not shown]"))

    def test_empty_entries_are_not_offered(self):
        self.write({"system_prompt": "hi", "draft_agent": {}, "other_agent": None})
        self.assertEqual(catalog(self.path)["agents"], [])

    def test_meta_keys_are_not_offered_as_agents(self):
        self.write({"_meta": {"version": "3", "note": "schema notes"},
                    "system_prompt": "hi",
                    "_draft": {"agent_profile": {"name": "Should not appear"}}})
        c = catalog(self.path)
        self.assertEqual([a["key"] for a in c["agents"]], [])
        self.assertNotIn("schema notes", c["system"])

    def test_the_temporal_tokens_are_filled_from_the_clock(self):
        import datetime
        self.write({"system_prompt": {"anchor": "Today is {{current_date}}. "
                                      "The year is {{current_year}}."}})
        text = catalog(self.path)["system"]
        today = datetime.datetime.now(datetime.timezone.utc).date()
        self.assertIn(f"Today is {today.isoformat()}", text)
        self.assertIn(f"The year is {today.year}", text)
        self.assertNotIn("{{current_date}}", text)

    def test_render_prompt_is_markdown(self):
        text = render_prompt({"agent_profile": {"name": "Nexus"}, "rules": ["a", "b"]})
        self.assertIn("## Agent Profile", text)
        self.assertIn("### Name\nNexus", text)
        self.assertIn("- a", text)

    def test_the_real_prompt_json_offers_the_shipped_profiles(self):
        """The profiles the repo ships are offered; the file is the user's own, so extra
        profiles they have added are not a failure - they must simply be well-formed."""
        c = catalog(ROOT / "prompt.json")
        keys = [a["key"] for a in c["agents"]]
        for shipped in ("expert_coding_agent", "expert_research_agent", "expert_vision_agent"):
            self.assertIn(shipped, keys)
        self.assertTrue(c["system"])
        for a in c["agents"]:
            self.assertTrue(a["name"] and a["prompt"])
        self.assertFalse(any(a["key"].startswith("_") for a in c["agents"]))

    def test_the_page_ships_an_empty_dropdown(self):
        """The menu's entries come from /prompts at run time, not from the page."""
        html = (ROOT / "serve" / "web" / "index.html").read_text(encoding="utf-8")
        self.assertIn('<select id="agent-select"', html)
        self.assertNotIn("HyperCore-Nexus-Architect", html)
        self.assertEqual(html.count('<option value="">System prompt only</option>'), 1)


class Endpoint(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tok = ByteTokenizer()
        cls.svc = Serviceless(tok)
        cls.httpd = serve(cls.svc, port=0)
        cls.base = f"http://127.0.0.1:{cls.httpd.server_address[1]}"

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def get(self, path):
        with urllib.request.urlopen(self.base + path, timeout=30) as r:
            return r.status, json.loads(r.read())

    def test_prompts_lists_the_catalog(self):
        status, body = self.get("/prompts")
        self.assertEqual(status, 200)
        # what the endpoint hands the page is what the file holds, key for key
        self.assertEqual([a["key"] for a in body["agents"]],
                         [a["key"] for a in catalog(self.svc.prompts_path)["agents"]])
        self.assertIn("core operating layer", body["system"])
        self.assertEqual(body["path"], self.svc.prompts_path)

    def test_a_new_profile_reaches_the_dropdown_without_a_restart(self):
        _, before = self.get("/prompts")
        data = json.loads(Path(self.svc.prompts_path).read_text())
        data["expert_ops_agent"] = {"agent_profile": {"name": "HyperCore-Ops-Runner"}}
        Path(self.svc.prompts_path).write_text(json.dumps(data), encoding="utf-8")
        _, after = self.get("/prompts")
        self.assertEqual(len(after["agents"]), len(before["agents"]) + 1)
        self.assertEqual(after["agents"][-1]["name"], "HyperCore-Ops-Runner")


def Serviceless(tok):
    from serve.server import Service
    svc = Service(MockEngine(tok, "ok"), tok, ChatTemplate(ROOT / "serve/chat_template.jinja"))
    dir_ = tempfile.mkdtemp()
    svc.prompts_path = str(Path(dir_) / "prompt.json")
    Path(svc.prompts_path).write_text(json.dumps(PROFILE), encoding="utf-8")
    return svc


if __name__ == "__main__":
    unittest.main()
