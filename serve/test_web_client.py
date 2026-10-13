"""serve/test_web_client.py - what the shipped web app does with the events this server sends.

These are contract tests on the files the page ships: the agent dropdown, the heartbeat the
page shows while a tool is running, the context-full 400, and the API-key path that used to
leave a fresh browser with no tools. No browser and no GPU are involved - the assertions are
about the code the page loads.

    python3 -m unittest serve.test_web_client
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "serve" / "web" / "app.js").read_text(encoding="utf-8")
PAGE = (ROOT / "serve" / "web" / "index.html").read_text(encoding="utf-8")


class AgentDropdown(unittest.TestCase):
    def test_the_menu_is_built_from_prompts_not_from_the_page(self):
        self.assertIn('<select id="agent-select"', PAGE)
        self.assertEqual(PAGE.count('<option value="">System prompt only</option>'), 1)
        self.assertIn("fetch(\"prompts\"", APP)
        for name in ("HyperCore-Nexus-Architect", "HyperCore-Intel-Scout", "HyperCore-Vision-Reader"):
            self.assertNotIn(name, PAGE)

    def test_a_refresh_that_changes_nothing_leaves_the_menu_alone(self):
        """loadPrompts compares the catalog's stamp and returns before touching the select."""
        body = re.search(r"async function loadPromts|async function loadPrompts\(quiet = false\) \{(.*?)\n\}", APP, re.S)
        self.assertTrue(body, "loadPrompts is not in the page")
        code = body.group(1)
        self.assertIn("stamp === promptStamp", code)
        self.assertIn("renderAgents()", code)

    def test_an_agent_profile_is_sent_as_a_system_turn(self):
        # the profile is prepended to the payload before the context cap prunes it,
        # and pruneToContext is documented to keep the profile system turn
        self.assertIn('if (agent && agent.prompt) payload.unshift({role: "system", content: agent.prompt});', APP)
        self.assertIn('const body = {model: health.model, messages: kept.messages, stream: true', APP)


class Heartbeat(unittest.TestCase):
    def test_a_running_tool_is_reported_in_the_composer(self):
        self.assertIn("function beatText()", APP)
        self.assertIn("function paintBeat()", APP)
        self.assertIn("beat = {name: x.name, since: Date.now(), round: x.round}", APP)

    def test_the_keep_alive_lines_are_the_beat(self):
        """A tool runs on the server while the stream is quiet; the comment lines are the pulse."""
        self.assertIn('if (!line.startsWith("data:")) {', APP)
        self.assertIn("if (beat) paintBeat();", APP)

    def test_each_mcp_server_has_a_switch(self):
        self.assertIn("data-mcp-server", APP)
        self.assertIn('fetch("mcp", {method: "POST"', APP)
        self.assertIn("The model stays loaded", APP)

    def test_a_condensed_round_is_recorded_and_does_not_create_a_phantom_tool(self):
        self.assertIn('if (x.event === "condensed")', APP)
        self.assertIn("m.condensed = (m.condensed || 0) + (x.chars || 0)", APP)

    def test_the_context_full_400_is_explained_and_not_just_shown(self):
        self.assertIn("/leaves no room/i.test(msg)", APP)
        self.assertIn("Start a new chat", APP)
        self.assertIn("max_result_chars", APP)

    def test_a_full_window_is_compacted_instead_of_dropped(self):
        self.assertIn("function summarizeDropped(", APP)
        self.assertIn("compacted by HyperCore", APP)
        self.assertIn('if (x.event === "compacted")', APP)
        self.assertIn("compactState", APP)
        # the handoff is stored for the next send, and it must not be pruned away
        self.assertIn("function isHandoff(", APP)
        self.assertIn("Earlier turns were summarized", APP)


class ApiKey(unittest.TestCase):
    def test_saving_a_key_re_runs_the_calls_that_need_one(self):
        """The bug seen from a phone: the key was stored but /mcp was never asked again, so the
        model was offered no tools until the page was reloaded."""
        start = APP.find('$("api-key").onchange')
        self.assertGreater(start, 0, "the api-key handler is not in the page")
        self.assertIn("loadMcp(); loadPrompts(true);", APP[start:start + 400])


class AssistModelPicker(unittest.TestCase):
    """The Assist tab's model panel folds like the thought box.

    Behaviour is exercised by serve/web/test_assist_thought_panel.js, which runs the real fold code
    against a stand-in DOM; these checks are the wiring that harness reads from the same files."""

    def test_the_panel_is_a_details_with_a_summary(self):
        self.assertIn('<details class="st-collapse assist-top" id="assist-top" open>', PAGE)
        self.assertIn('<span class="muted small assist-top__pick" id="assist-top-pick"', PAGE)
        self.assertIn('<div class="st-collapse__body assist-top__body">', PAGE)
        for el in ("assist-model", "assist-status", "assist-probe", "assist-all", "assist-clear"):
            self.assertIn(f'id="{el}"', PAGE)
        self.assertIn(".assist-top__body {", (ROOT / "serve" / "web" / "app.css").read_text(encoding="utf-8"))

    def test_the_fold_is_remembered_and_names_the_selection(self):
        start = APP.find('const assistTop = $("assist-top");')
        self.assertGreater(start, 0, "the fold block is not in the page")
        block = APP[start:APP.find("wireAssistTop();", start)]
        for line in ("function paintAssistTop()", "function foldAssistTop(open)", "function wireAssistTop()",
                     'if (!store.get("assistTopOpen", true)) foldAssistTop(false);',
                     'store.set("assistTopOpen", assistTop.open);'):
            self.assertIn(line, block, f"the fold does not contain {line}")
        self.assertIn("on the endpoint", block)          # the summary says which model is answering
        self.assertIn("if (!assistTop) return;", block)  # an older page has nothing to fold

    def test_a_folded_panel_is_opened_when_the_user_needs_it(self):
        for line in ('foldAssistTop(true);        // there is nothing to pick unless the panel is open',
                     'foldAssistTop(true);        // the picker is where another model is chosen',
                     'foldAssistTop(true);        // the results are in the panel; folding them away hides the whole run'):
            self.assertIn(line, APP)

    def test_a_model_the_endpoint_does_not_answer_for_is_not_listed(self):
        """A 404 is not a slow model and not a throttle: there is nothing to measure. The panel counts
        those and leaves them out of the table; the behaviour is exercised in the JS harness."""
        start = APP.find("function renderAssistProbe(data)")
        body = APP[start:APP.find("\n}\n", start)]
        self.assertIn('const notServed = (m) => m.reason === "not available"', body)
        self.assertIn("const listed = (m) => !notServed(m);", body)
        for filtered in (".filter((m) => m.ok === false && listed(m))",
                        "over.filter((m) => m.ttft_s != null && listed(m))",
                        "over.filter((m) => m.ttft_s == null && listed(m))",
                        "((assistProbe && assistProbe.removed) || []).filter(listed)"):
            self.assertIn(filtered, body, f"the probe table does not filter {filtered}")
        self.assertNotIn('group("Not served by this endpoint"', body)
        self.assertIn("the endpoint does not serve are not listed", body)


class SurfaceSlider(unittest.TestCase):
    """The Surface slider in the Sampling drawer. The palette maths is exercised in
    serve/web/test_surface_slider.js; these are the contract tests on the shipped files."""

    CSS = (ROOT / "serve" / "web" / "app.css").read_text(encoding="utf-8")
    TOKENS = (ROOT / "serve" / "web" / "tokens.css").read_text(encoding="utf-8")

    def test_the_drawer_carries_the_slider(self):
        for el in ("s-surface", "o-surface"):
            self.assertIn(f'id="{el}"', PAGE)
        self.assertIn('class="st-slider st-slider--metal" type="range"', PAGE)
        self.assertIn('min="0" max="100" step="1"', PAGE)

    def test_the_slider_walks_the_metallic_range(self):
        for anchor in ("--st-metal-white:#ffffff", "--st-metal-chrome:#cfd4d8",
                       "--st-metal-silver:#b6bcc2", "--st-metal-graphite:#787d83",
                       "--st-metal-onyx:#14171a"):
            self.assertIn(anchor, self.TOKENS)
        self.assertIn(".st-slider--metal {", self.CSS)

    def test_the_background_is_painted_from_the_sampled_colour(self):
        self.assertIn('body[data-surface="metal"] {', self.CSS)
        for layer in ("--st-metal-spec", "--st-metal-streak", "--st-metal-top", "var(--st-bg)"):
            self.assertIn(layer, self.CSS)

    def test_the_palette_is_derived_from_one_position_and_stays_local(self):
        for line in ("function metalPalette(pos) {", "function metalColor(t) {",
                     'root.dataset.surface = "metal";', 'store.set("surface", p.pos)',
                     'const savedSurface = store.get("surface", 0);'):
            self.assertIn(line, APP)
        self.assertNotIn("surface", APP[APP.find("function sharedDefaults"):APP.find("async function saveShared")])


class StopStartPair(unittest.TestCase):
    """The composer's Stop/Start pair, and the banner's two-click Shut Down.

    The banner is deliberately not a Start button: it arms on the first click and shuts the
    server down on the second. The /v1/stop - /v1/start pair stays on the server for the API
    and the Monitor. The behaviour is exercised in serve/web/test_stop_start_buttons.js; these
    are the contract tests on the shipped files."""

    CSS = (ROOT / "serve" / "web" / "components.css").read_text(encoding="utf-8")
    SERVER = (ROOT / "serve" / "server.py").read_text(encoding="utf-8")

    def test_the_composer_button_has_a_start_state(self):
        for el in ("stop-btn", "stop-icon", "stop-text"):
            self.assertIn(f'id="{el}"', PAGE)
        for line in ('const RESUME_PROMPT = "Complete the open tasks";',
                     "function paintStopButton(mode) {",
                     'btn.dataset.mode = mode;',
                     'web/sprite.svg#i-bolt',
                     'function endTurn() {',
                     'turnEnded = true;'):
            self.assertIn(line, APP, f"the composer's Start button no longer has {line}")
        self.assertIn('$("input").value = RESUME_PROMPT;', APP)
        self.assertIn("endTurn();", APP[APP.find("busy = null;"):APP.find("saveChat();")])

    def test_the_banner_button_is_a_plain_shut_down(self):
        for el in ("shutdown-btn", "shutdown-text"):
            self.assertIn(f'id="{el}"', PAGE)
        for line in ("let shuttingDown = false, armed = false;",
                     'btn.dataset.armed = "1";',
                     'setTimeout(() => { if (!shuttingDown) disarmShutdown(); }, 8000);',
                     'fetch("v1/shutdown"'):
            self.assertIn(line, APP, f"the banner's two-click Shut Down no longer has {line}")
        self.assertNotIn('fetch("v1/stop"', APP, "the banner must not stop the engine instead of the server")
        self.assertNotIn('fetch("v1/start"', APP, "the banner must not be a Start button")

    def test_the_start_state_is_styled(self):
        self.assertIn('.st-btn[data-mode="start"]{', self.CSS)

    def test_the_server_answers_both_halves(self):
        self.assertIn('if path in ("/v1/stop", "/v1/start"):', self.SERVER)
        self.assertIn("svc.engine_stopped = True", self.SERVER)
        self.assertIn("def start_engine(self) -> bool:", self.SERVER)
        self.assertIn("raise EngineStopped(", self.SERVER)
        self.assertIn('"engine_stopped"', self.SERVER)
        # stopping the engine must not end the process: only /v1/shutdown sets that flag
        stop_block = self.SERVER[self.SERVER.find('if path in ("/v1/stop", "/v1/start")'):
                         self.SERVER.find('if path in ("/v1/stop", "/v1/start")') + 2400]
        self.assertNotIn("stop_requested.set()", stop_block)


if __name__ == "__main__":
    unittest.main()
