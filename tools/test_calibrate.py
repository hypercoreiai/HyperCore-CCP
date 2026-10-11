"""Tests for tools/calibrate.py and setup's use of it, without a GPU: a stand-in engine whose decode speed is a
function of the settings it runs with.

    python -m unittest tools.test_calibrate
"""
from __future__ import annotations

import json
import os
import struct
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT))
import calibrate as CAL


class FakeEngine:
    """Speed = f(pcie_frac, spec_min_p, workers): the GEN line's tune keys arrive as `hypercore_tune`."""

    def __init__(self, args, speed, info_workers=6, starts=None, adapt=None, tail=None):
        self.args = list(args)
        self.adapt_bonus = (adapt or {}).get(CAL.arg_value(args, "--adapt-swaps"), 1.0)
        self.tail_bonus = tail or {}          # {"off": 1.10}: the speed with the tail skip turned off
        w = CAL.arg_value(args, "--pool-workers")
        self.workers = int(w) if w else info_workers
        self.info = {"pool_workers": info_workers, "pcie_frac": 0.55, "spec_min_p": float(CAL.arg_value(args, "--spec-min-p") or 0)}
        self.speed = speed
        self.last = {}
        self.proc = None
        if starts is not None:
            starts.append(list(args))

    def generate(self, ids, max_new, sampling, cancel):
        tune = sampling.get("hypercore_tune") or {}
        rate = self.speed(tune.get("pcie_frac", 0.55), tune.get("spec_min_p", self.info["spec_min_p"]), self.workers)
        rate *= self.adapt_bonus
        if os.environ.get(CAL.TAIL_SKIP_ENV) == "0":
            rate *= self.tail_bonus.get("off", 1.0)
        for _ in range(max_new):
            yield 1
        self.last = {"generated": max_new, "decode_ms": max_new / rate * 1000.0}


BASE = ["--pack", "p", "--spec", "4", "--spec-min-p", "0.5", "--max-context", "8192"]


class Calibrate(unittest.TestCase):
    def run_with(self, speed, workers=6, base=BASE, adapt=None, tail=None, envs=None):
        starts = []

        def start(a):
            if envs is not None:
                envs.append(os.environ.get(CAL.TAIL_SKIP_ENV))   # what the engine saw at its own start
            return FakeEngine(a, speed, workers, starts, adapt, tail)

        res = CAL.measure(base, [[1, 2, 3]] * 3, start, say=lambda *_: None)
        return res, starts

    def test_defaults_kept_when_flat(self):
        res, _ = self.run_with(lambda f, p, w: 50.0)
        self.assertEqual(res["settings"], {})

    def test_small_gain_is_noise(self):
        # 2% better at pcie 0.35: below MIN_GAIN, so the default stays
        res, _ = self.run_with(lambda f, p, w: 51.0 if abs(f - 0.35) < 1e-6 else 50.0)
        self.assertEqual(res["settings"], {})

    def test_finds_pcie_and_min_p(self):
        def speed(f, p, w):
            return 50.0 + (10.0 if abs(f - 0.2) < 1e-6 else 0.0) + (5.0 if abs(p - 0.7) < 1e-6 else 0.0)
        res, _ = self.run_with(speed)
        self.assertEqual(res["settings"].get("--pcie-frac"), "0.20")
        self.assertEqual(res["settings"].get("--spec-min-p"), "0.70")
        self.assertNotIn("--pool-workers", res["settings"])

    def test_fewer_workers(self):
        # a hybrid CPU: half the workers is 20% faster
        res, starts = self.run_with(lambda f, p, w: 60.0 if w == 3 else 50.0, workers=6)
        self.assertEqual(res["settings"].get("--pool-workers"), "3")
        # one start per worker count, per expert-tier candidate and per tail-skip candidate, plus the sweep
        self.assertEqual(len(starts), 1 + len(CAL.worker_candidates(6)) + len(CAL.ADAPT_CANDIDATES)
                        + len(CAL.TAIL_CANDIDATES))
        self.assertEqual(CAL.arg_value(starts[0], "--spec-min-p"), "0.5")   # measured against the product default

    def test_a_failed_restart_keeps_the_measurements_1337(self):
        # the top PCIe share wins by far; every later restart (the worker counts, the expert tier) fails to start
        n = {"starts": 0}

        def start(args):
            n["starts"] += 1
            if n["starts"] > 1:
                raise RuntimeError("the engine exited before it was ready: cudaMalloc failed (213 MiB free)")
            return FakeEngine(args, lambda f, p, w: 80.0 if f == 0.75 else 50.0, 6)
        said = []
        res = CAL.measure(BASE, [[1, 2, 3]] * 3, start, say=said.append)
        self.assertEqual(res["settings"].get("--pcie-frac"), "0.75")        # steps 1-3 survived
        self.assertGreater(len(res["report"]["failed_starts"]), 1)
        self.assertTrue(any("did not start" in x and "cudaMalloc" in x for x in said))
        self.assertEqual(res["report"]["workers"], {})
        self.assertEqual(res["report"]["adapt"], {})

    def test_one_failing_worker_count_only_drops_that_candidate_1337(self):
        def start(args):
            if CAL.arg_value(args, "--pool-workers") == "3":
                raise RuntimeError("out of memory")
            return FakeEngine(args, lambda f, p, w: 60.0 if w == 2 else 50.0, 6)
        res = CAL.measure(BASE, [[1, 2, 3]] * 3, start, say=lambda *_: None)
        self.assertEqual(res["settings"].get("--pool-workers"), "2")
        self.assertEqual(list(res["report"]["failed_starts"]), ["3 workers"])

    def test_adaptive_tier(self):
        # a slow-RAM PC: swapping 160 experts per round is 10% faster, 80 is 2% (noise)
        res, starts = self.run_with(lambda f, p, w: 50.0, adapt={"160": 1.10, "80": 1.02})
        self.assertEqual([res["settings"].get(f) for f in CAL.ADAPT_FLAGS], ["1", "160", "0.97"])
        flat, _ = self.run_with(lambda f, p, w: 50.0, adapt={"160": 1.02})
        self.assertFalse(any(f in flat["settings"] for f in CAL.ADAPT_FLAGS))
        # the candidates are measured with the worker count chosen before
        res, starts = self.run_with(lambda f, p, w: 60.0 if w == 3 else 50.0, workers=6, adapt={"160": 1.10})
        self.assertEqual(res["settings"].get("--pool-workers"), "3")
        self.assertTrue(all(CAL.arg_value(a, "--pool-workers") == "3" for a in starts[-len(CAL.ADAPT_CANDIDATES):]))
        a = CAL.apply(BASE, res["settings"])
        self.assertEqual(CAL.arg_value(a, "--adapt-swaps"), "160")
        self.assertIsNone(CAL.arg_value(CAL.apply(a, {}), "--adapt-swaps"))
        # the tier's step is longer than the sweep's, so the effect can show
        self.assertEqual(CAL.TIER_MAX_NEW, 512)

    def test_the_tail_skip_is_measured_and_only_kept_when_it_wins(self):
        # turning it off is 10% faster here: the setting is written, and the engine is started with the
        # variable set for that candidate and unset for the other
        envs: list = []
        res, _ = self.run_with(lambda f, p, w: 50.0, tail={"off": 1.10}, envs=envs)
        self.assertEqual(res["env"], {CAL.TAIL_SKIP_ENV: "0"})
        self.assertEqual(res["report"]["tok_s"], 55.0)
        # the variable is set in the environment at the start, not in the args: one candidate sees it, one does not
        self.assertEqual(envs.count("0"), 1)
        self.assertIsNone(envs[-2])          # the engine's own rank is measured with the variable unset
        self.assertNotIn(CAL.TAIL_SKIP_ENV, os.environ)                # the environment is restored
        # a 2% gain is inside the noise floor: nothing is written
        flat, _ = self.run_with(lambda f, p, w: 50.0, tail={"off": 1.02})
        self.assertEqual(flat["env"], {})
        self.assertIn("engine default", flat["report"]["tail_skip"])
        self.assertIn("off", flat["report"]["tail_skip"])

    def test_the_link_is_read_without_a_card_and_never_raises(self):
        self.assertEqual(CAL.link_info({}), {})                       # no GPU in the test box
        self.assertEqual(CAL.link_info({"gpu": [0], "backend": "hip"}), {})

    def test_the_sweep_rotates_and_reports_medians(self):
        seen = []
        s = CAL.Session(FakeEngine(BASE, lambda f, p, w: 50.0), [[1, 2, 3]] * 3)
        out = CAL.sweep(s, [0.0, 0.2, 0.55], {"spec_min_p": 0.5}, "pcie_frac", "PCIe share", seen.append)
        self.assertEqual({k: len(v) for k, v in out.items()}, {0.0: 3, 0.2: 3, 0.55: 3})
        # round 1 forward, round 2 reversed, round 3 forward: every value is visited the same number of times
        self.assertEqual(len(seen), CAL.SWEEP_ROUNDS + 1)
        self.assertIn("median of 3", seen[-1])

    def test_old_calibration_is_the_baseline_reset(self):
        # a config tuned earlier: the measurement starts from the product defaults, not from those values
        base = CAL.apply(BASE, {"--pcie-frac": "0.20", "--pool-workers": "3", "--spec-min-p": "0.70"})
        _, starts = self.run_with(lambda f, p, w: 50.0, base=base)
        self.assertIsNone(CAL.arg_value(starts[0], "--pcie-frac"))
        self.assertIsNone(CAL.arg_value(starts[0], "--pool-workers"))
        self.assertEqual(CAL.arg_value(starts[0], "--spec-min-p"), "0.5")

    def test_apply(self):
        a = CAL.apply(BASE, {"--pcie-frac": "0.35", "--pool-workers": "4"})
        self.assertEqual(CAL.arg_value(a, "--pcie-frac"), "0.35")
        self.assertEqual(CAL.arg_value(a, "--pool-workers"), "4")
        self.assertEqual(CAL.arg_value(a, "--spec-min-p"), "0.5")
        b = CAL.apply(a, {})                                # back to the defaults
        self.assertIsNone(CAL.arg_value(b, "--pcie-frac"))
        self.assertIsNone(CAL.arg_value(b, "--pool-workers"))
        self.assertEqual(b.count("--spec-min-p"), 1)

    def test_engine_args_are_the_servers(self):
        # #447: a "gpu" list is a layer split only with two or more cards; "0,2" is one too; split_skip_if_fits counts
        helper = {"args": BASE + ["--expert-cache-device1", "1800"], "gpu": [0], "env": {"CUDA_VISIBLE_DEVICES": "0,1"}}
        self.assertEqual(CAL.engine_args(helper), helper["args"])                 # one stage + a helper card: no split
        self.assertEqual(CAL.engine_args({"args": BASE, "gpu": 1}), BASE)
        self.assertEqual(CAL.engine_args({"args": BASE, "gpu": [0, 2]}), BASE + ["--layer-split", "auto"])
        self.assertEqual(CAL.engine_args({"args": BASE, "gpu": "0,2", "layer_split": "18"}),
                         BASE + ["--layer-split", "18"])
        self.assertEqual(CAL.engine_args({"args": BASE, "gpu": [0, 1], "split_skip_if_fits": True}),
                         BASE + ["--layer-split", "auto", "--split-skip-if-fits"])
        own = BASE + ["--layer-split", ""]                                       # the config's own value wins
        self.assertEqual(CAL.engine_args({"args": own, "gpu": [0, 1]}), own)

    def test_run_measures_with_the_servers_args(self):
        with tempfile.TemporaryDirectory() as d:
            tok = Path(d)
            (tok / "vocab.json").write_text(json.dumps({"a": 0, "b": 1}))
            (tok / "merges.txt").write_text("")
            (tok / "token_type.json").write_text(json.dumps([1, 1]))
            seen = []
            saved = CAL.measure
            CAL.measure = lambda args, ids_list, start_engine, say=print, extra=(): seen.append(args) or {}
            fake = type("ST", (), {"Tokenizer": lambda *a: type("T", (), {"encode": lambda s, t, **k: [0]})()})
            try:
                with mock.patch.dict(sys.modules, {"hypercore_tokenizer": fake}):
                    CAL.run({"tokenizer": d, "args": list(BASE), "gpu": [0]}, start_engine=lambda a: None)
            finally:
                CAL.measure = saved
        self.assertEqual(seen, [BASE])

    def test_engine_error(self):
        with tempfile.TemporaryDirectory() as d:
            log = Path(d) / "hypercore-x.log"
            log.write_text("hypercore generate: an old error\n", encoding="utf-8")
            since = log.stat().st_size
            with open(log, "a", encoding="utf-8") as f:
                f.write("loading ...\nhypercore generate: --expert-cache-remote with a layer split needs a GPU that runs "
                        "no stage (2 visible, 2 used by the split)\n\n")
            self.assertEqual(CAL.engine_error(str(log), since), "hypercore generate: --expert-cache-remote with a layer "
                             "split needs a GPU that runs no stage (2 visible, 2 used by the split)")
            with open(log, "a", encoding="utf-8") as f:
                f.write("Segmentation fault\n")
            self.assertIn("--expert-cache-remote", CAL.engine_error(str(log), since))   # the engine's own line first
            self.assertEqual(CAL.engine_error(str(log), log.stat().st_size), None)   # nothing new since
            self.assertIsNone(CAL.engine_error(None))
            self.assertIsNone(CAL.engine_error(str(Path(d) / "missing.log")))

    def test_worker_candidates(self):
        self.assertEqual(CAL.worker_candidates(6), [6, 4, 3, 2])
        self.assertEqual(CAL.worker_candidates(23), [23, 15, 12, 6])        # a quarter: 4 beat 15 on 8P + 16E
        self.assertEqual(CAL.worker_candidates(23, (7,)), [23, 15, 12, 6, 7])   # P-cores - 1
        self.assertEqual(CAL.worker_candidates(35, (17,)), [35, 23, 18, 9, 17])  # 2 sockets: one socket's cores - 1
        self.assertEqual(CAL.worker_candidates(15, (7, 23)), [15, 10, 8, 4, 7, 23])  # a config that pins 15 still
        # measures the engine's own count (24 physical cores minus the host's) and the P-cores
        self.assertEqual(CAL.worker_candidates(6, (6, 1, 9)), [6, 4, 3, 2, 9])    # an extra above the default is kept
        self.assertEqual(CAL.worker_candidates(6, (1, 200)), [6, 4, 3, 2])        # none below 2, none over 128
        self.assertEqual(CAL.worker_candidates(3), [3, 2])
        self.assertEqual(CAL.worker_candidates(1), [1])

    def test_pick(self):
        self.assertEqual(CAL.pick({"a": [50, 51, 49], "b": [53, 52, 60]}, "a"), "b")
        self.assertEqual(CAL.pick({"a": [50, 51, 49], "b": [51, 51.5, 51]}, "a"), "a")
        self.assertEqual(CAL.pick({}, "a"), "a")


class SetupIntegration(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old = {k: os.environ.get(k) for k in ("APPDATA", "XDG_CONFIG_HOME")}
        os.environ["APPDATA"] = self.tmp.name
        os.environ["XDG_CONFIG_HOME"] = self.tmp.name
        import setup as S
        self.S = S
        self.saved = (S.gpu_info, S.cpu_info, S.ram_gb, CAL.run)
        S.gpu_info = lambda pick=None: {"name": "RTX Test", "vram_gb": 12.0, "arch": "120", "count": 1, "index": 0}
        S.cpu_info = lambda: ("Test CPU", True, True)
        S.ram_gb = lambda: 64.0

    def tearDown(self):
        self.S.gpu_info, self.S.cpu_info, self.S.ram_gb, CAL.run = self.saved
        for k, v in self.old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        self.tmp.cleanup()

    def test_calibrate_config_writes_and_remembers(self):
        cfg_path = Path(self.tmp.name) / "hypercore-q2_0.json"
        cfg = {"exe": "x", "args": list(BASE), "model_name": "qwen3.8-flash-next-q2_0"}
        cfg_path.write_text(json.dumps(cfg))
        CAL.run = lambda c, say=print, start_engine=None: {"settings": {"--pcie-frac": "0.20"}, "report": {"tok_s": 61.2}}
        self.assertTrue(self.S.calibrate_config(cfg_path))
        written = json.loads(cfg_path.read_text())
        self.assertEqual(CAL.arg_value(written["args"], "--pcie-frac"), "0.20")
        saved = self.S.saved_calibration(written)
        self.assertEqual(saved["settings"], {"--pcie-frac": "0.20"})
        # another model on the same PC has no calibration yet
        self.assertIsNone(self.S.saved_calibration({**written, "model_name": "swift-iq2_xs"}))
        # another context size is another key (its KV cache changes the expert cache)
        other = dict(written, args=CAL.with_arg(written["args"], "--max-context", "131072"))
        self.assertIsNone(self.S.saved_calibration(other))

    def test_failed_calibration_keeps_defaults(self):
        cfg_path = Path(self.tmp.name) / "hypercore-q2_0.json"
        cfg_path.write_text(json.dumps({"exe": "x", "args": list(BASE), "model_name": "m"}))

        def boom(*a, **k):
            raise RuntimeError("the engine exited before it was ready")
        CAL.run = boom
        self.assertFalse(self.S.calibrate_config(cfg_path))
        self.assertEqual(json.loads(cfg_path.read_text())["args"], BASE)
        self.assertIsNone(self.S.saved_calibration({"args": BASE, "model_name": "m"}))

    def test_failed_calibration_says_the_engines_reason(self):
        # #447: the engine's last error line is printed, and the --calibrate run repeats the failure before it starts
        import contextlib
        import io
        log = Path(self.tmp.name) / "hypercore-q2_0.log"
        log.write_text("hypercore generate: an error of an earlier start\n", encoding="utf-8")
        cfg_path = Path(self.tmp.name) / "hypercore-q2_0.json"
        cfg_path.write_text(json.dumps({"exe": "x", "args": list(BASE), "model_name": "m", "log": str(log)}))

        def boom(*a, **k):
            with open(log, "a", encoding="utf-8") as f:
                f.write("hypercore generate: --expert-cache-remote with a layer split needs a GPU that runs no stage\n")
            raise RuntimeError(f"the engine exited before it was ready (see {log})")
        CAL.run = boom
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertFalse(self.S.calibrate_config(cfg_path))
        self.assertIn("the engine said: hypercore generate: --expert-cache-remote with a layer split", out.getvalue())
        self.assertNotIn("an earlier start", out.getvalue())
        out = io.StringIO()
        with mock.patch.object(self.S, "ROOT", Path(self.tmp.name)), \
                mock.patch.object(self.S, "data_folder", lambda d: (Path(self.tmp.name) / "data", [])), \
                mock.patch.object(self.S, "update_installed_engine", lambda *a: None), \
                mock.patch.object(sys, "argv", ["setup.py", "--calibrate", "--no-start"]), \
                contextlib.redirect_stdout(out):
            self.assertEqual(self.S.main(), 0)
        self.assertIn("this PC is NOT tuned: the tuning failed (the reason is above); the model keeps the default "
                      "settings", out.getvalue())


class DefaultEnginePath(unittest.TestCase):
    """setup.py --calibrate calls run() with no start_engine.

    That default imported serve.server.HyperCoreEngine, which moved to
    serve/fixtures/legacy_engine.py when the binary IPC worker became production. The
    import raised, setup caught it, and the config kept the defaults - the reported
    "the tuning did not finish (cannot import name 'HyperCoreEngine' from 'serve.server')".
    Nothing here covers the real worker, which is why it went unnoticed.
    """

    def scripted(self, **kw):
        from serve.frame_fixture import ScriptedWorker
        return ScriptedWorker(max_slots=1, tokens=16, draft_s=0.02,
                             instance_pcie_frac=0.55, instance_spec_min_p=0.5,
                             pool_workers=6, **kw)

    def test_default_builder_starts_a_real_request_handler(self):
        """No GPU, no pack: the ScriptedWorker is the worker on the other end of the socket."""
        worker = self.scripted()
        eng = CAL.worker_engine({"args": list(BASE)}, list(BASE), transport=worker.connect)
        try:
            self.assertTrue(eng.alive(), "the worker must complete the READY handshake")
            info = eng.info
            for key in ("pcie_frac", "spec_min_p", "pool_workers"):
                self.assertIn(key, info, f"measure() reads {key}; the worker must report it")
            self.assertEqual(info["pool_workers"], 6)
            self.assertEqual(info["max_batch_slots"], 1)
        finally:
            CAL.close(eng)
        self.assertFalse(eng.alive(), "close() must stop the supervisor, not just send QUIT")

    def test_the_tuning_worker_is_given_the_model_load_allowance(self):
        """The tuning run loads the real model. With the supervisor's 30 s default the
        calibration stopped at "worker did not accept a connection within 30.0s" on a PC
        that starts the same model without trouble (setup --setup, Step 7).
        """
        from serve.hypercore_supervisor import HyperCoreProcessSupervisor
        seen = {}
        real = HyperCoreProcessSupervisor

        class Spy(real):
            def __init__(self, **kw):
                seen.update(kw)
                super().__init__(**kw)

        worker = self.scripted()
        with mock.patch("serve.hypercore_supervisor.HyperCoreProcessSupervisor", Spy):
            eng = CAL.worker_engine({"args": list(BASE), "exe": "/engine/hypercore"},
                                   list(BASE), transport=worker.connect)
            CAL.close(eng)
        self.assertEqual(seen.get("startup_timeout_s"), 180.0,
                        "the tuning worker must get the model's start allowance, not 30 s")


    def test_measure_runs_end_to_end_against_the_real_handler(self):
        worker = self.scripted()
        cfg = {"args": list(BASE)}
        start = lambda args: CAL.worker_engine(cfg, args, transport=worker.connect)
        res = CAL.measure(list(BASE), [[1, 2, 3]] * 3, start, say=lambda *_: None)
        self.assertTrue(res["report"]["default"], "the instance baseline was never read")
        self.assertGreater(res["report"]["default"]["pcie_frac"], 0.0)
        self.assertGreater(res["report"]["default"]["pool_workers"], 0)

    def test_a_per_request_tune_reaches_the_wire(self):
        """The text engine took the tune as one block; the worker needs the two keys flat."""
        from serve.ipc_parser import CMD_SUBMIT
        worker = self.scripted()
        eng = CAL.worker_engine({"args": list(BASE)}, list(BASE), transport=worker.connect)
        try:
            sampling = {"temperature": 0, "pcie_frac": 0.2, "spec_min_p": 0.7,
                        "hypercore_tune": {"pcie_frac": 0.2, "spec_min_p": 0.7}}
            list(eng.generate([1, 2, 3], 8, sampling, threading.Event()))
            submits = [r for r in worker.received if r[0] == CMD_SUBMIT]
            self.assertTrue(submits, "no request frame was recorded")
            pcie, minp = struct.unpack("<ff", submits[0][2][20:28])
            self.assertAlmostEqual(pcie, 0.2, places=6)
            self.assertAlmostEqual(minp, 0.7, places=6)
        finally:
            CAL.close(eng)


class MeasurementWindow(unittest.TestCase):
    """Where the rate comes from: the engine's own decode window when it reports one,
    the wall clock when the boundary worker's token loop is instant (decode_ms 0)."""

    class Engine:
        def __init__(self, tokens: int, decode_ms: float, wall_s: float):
            self.tokens, self.decode_ms, self.wall_s = tokens, decode_ms, wall_s
            self.last = {}

        def generate(self, ids, max_new, sampling, cancel):
            for _ in range(self.tokens):
                yield 1
            left = self.wall_s - 0.0
            if left > 0:
                time.sleep(left)
            self.last = {"generated": self.tokens, "decode_ms": self.decode_ms}

    def test_a_reported_window_beats_the_wall_clock(self):
        s = CAL.Session(self.Engine(20, 100.0, 5.0), [[1] * 20])
        self.assertAlmostEqual(s.rate(), 200.0, places=1)

    def test_an_instant_token_loop_is_still_measured(self):
        s = CAL.Session(self.Engine(20, 0.0, 0.100), [[1] * 20])
        rate = s.rate()
        self.assertGreater(rate, 0.0, "a zero decode_ms made the whole sweep meaningless")
        self.assertLess(rate, 300.0, "the wall clock was not used")

    def test_a_stream_that_produced_nothing_measures_zero(self):
        s = CAL.Session(self.Engine(4, 0.0, 0.01), [[1] * 4])
        self.assertEqual(s.rate(), 0.0)


if __name__ == "__main__":
    unittest.main()
