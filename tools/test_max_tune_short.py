"""Tests for the three modes of tune/max_tune.sh and for how it writes its outputs.

--short runs the calibration first, takes the argmax of every sweep in the report - pcie-frac,
spec-min-p, pool-workers, the adaptive expert tier - freezes those values, and drops the layers
that have only one value left. The argmax deliberately ignores calibrate.py's MIN_GAIN gate
against the product defaults: a measured maximum below the default still wins.

The second half runs the sweep against a stub engine, so the real paths are exercised without a
GPU: the matrix log and CSV carry a date-time stamp, Ctrl-C unwinds the engine and still writes
the best-so-far config and run scripts, and those files say they came from a partial sweep.

    python -m unittest tools.test_max_tune_short
"""
from __future__ import annotations

import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tune" / "max_tune.sh"
FIXTURE = ROOT / "tune" / "results" / "calibrate-fixture.json"
ENGINE = ROOT / "engine" / "hypercore"
PACK = Path("/home/ai-agent/HyperCore-data/packs/q2_0")

ALL_LAYERS = ("topology", "ple-io", "kv", "kv-grow", "host-core",
              "pool-affinity", "pool-workers", "prompt-tail")
STAGED_RUNS = 26
SHORT_RUNS = 17
FULL_RUNS = 3888
SHORT_FULL_RUNS = 432
SHORT_LAYERS = ("topology", "ple-io", "kv", "kv-grow", "host-core",
                "pool-affinity", "prompt-tail")

NEEDS_ENGINE = unittest.skipUnless(
    SCRIPT.exists() and ENGINE.exists() and PACK.exists(),
    "max_tune.sh needs the engine binary and the q2_0 pack to build its command lines")


def sweep(args: list[str], report: str | None = None) -> subprocess.CompletedProcess:
    """Run max_tune.sh in --dry-run mode with every output file in a temp directory."""
    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ)
        env["MATRIX_LOG"] = str(Path(tmp) / "matrix.log")
        env["CSV_FILE"] = str(Path(tmp) / "matrix.csv")
        env["RESULTS_DIR"] = tmp
        argv = ["bash", str(SCRIPT)] + args
        if report:
            argv += ["--calibrate-report", report]
        argv.append("--dry-run")
        return subprocess.run(argv, capture_output=True, text=True, env=env, timeout=240, check=False)


def run_count(stdout: str) -> int:
    """Number of configurations the sweep would launch."""
    return sum(1 for line in stdout.splitlines() if line.startswith("[*] run "))


def layer_counts(stdout: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for line in stdout.splitlines():
        if line.startswith("[*] run "):
            layer = line.split("layer=", 1)[1].strip()
            counts[layer] = counts.get(layer, 0) + 1
    return counts


def commands(stdout: str) -> list[str]:
    """The engine command line of every configuration, in launch order."""
    return [line.split("command: ", 1)[1].strip()
            for line in stdout.splitlines() if line.startswith("    command: ")]


@NEEDS_ENGINE
class Modes(unittest.TestCase):
    def test_default_is_the_staged_sweep(self):
        proc = sweep(["--model", "q2_0"])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(run_count(proc.stdout), STAGED_RUNS)
        self.assertIn("mode: staged", proc.stdout)
        self.assertEqual(set(layer_counts(proc.stdout)), set(ALL_LAYERS))

    def test_full_is_the_cartesian_product(self):
        proc = sweep(["--model", "q2_0", "--full"])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(run_count(proc.stdout), FULL_RUNS)
        self.assertIn("mode: full", proc.stdout)

    def test_short_freezes_the_measured_maxima(self):
        proc = sweep(["--model", "q2_0", "--short"], str(FIXTURE))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("frozen by calibration: pool-workers -> workers=16", proc.stdout)
        self.assertEqual(run_count(proc.stdout), SHORT_RUNS)
        self.assertEqual(set(layer_counts(proc.stdout)), set(SHORT_LAYERS))
        for cmd in commands(proc.stdout):
            with self.subTest(cmd=cmd[:80]):
                self.assertIn("--pcie-frac 0.75", cmd)
                self.assertIn("--spec-min-p 0.7", cmd)
                self.assertIn("--pool-workers 16", cmd)
                self.assertIn("--adapt-every 1 --adapt-swaps 160 --adapt-decay 0.97", cmd)
                self.assertNotIn("--pool-workers 0", cmd)

    def test_short_full_is_the_pruned_product(self):
        proc = sweep(["--model", "q2_0", "--short", "--full"], str(FIXTURE))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(run_count(proc.stdout), SHORT_FULL_RUNS)
        self.assertIn("mode: full", proc.stdout)

    def test_a_report_alone_is_short(self):
        proc = sweep(["--model", "q2_0"], str(FIXTURE))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(run_count(proc.stdout), SHORT_RUNS)

    def test_layers_can_still_be_narrowed(self):
        proc = sweep(["--model", "q2_0", "--short", "--layers", "kv,kv-grow"], str(FIXTURE))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(run_count(proc.stdout), 5)  # staged: 3 kv values, then 2 kv-grow values
        self.assertEqual(set(layer_counts(proc.stdout)), {"kv", "kv-grow"})

    def test_a_missing_report_stops_the_run(self):
        proc = sweep(["--model", "q2_0", "--short"], str(ROOT / "tune" / "results" / "nope.json"))
        self.assertEqual(proc.returncode, 2)
        self.assertIn("no calibration report", proc.stderr)
        self.assertEqual(run_count(proc.stdout), 0)

    def test_a_broken_run_config_is_reported_before_the_gpu_is_touched(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json") as fh:
            fh.write('{\n "exe": "engine/hypercore",\n "args": ["--a" "b"]\n}\n')
            fh.flush()
            proc = sweep(["--model", "q2_0", "--short",
                         "--calibrate-config", fh.name])
        self.assertEqual(proc.returncode, 2, proc.stderr)
        self.assertIn("is not a readable run config", proc.stderr)
        self.assertIn("Expecting ',' delimiter", proc.stderr)
        self.assertEqual(run_count(proc.stdout), 0)

    def test_dry_run_does_not_measure(self):
        proc = sweep(["--model", "q2_0", "--short"])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("--dry-run does not measure", proc.stderr)
        self.assertEqual(run_count(proc.stdout), STAGED_RUNS)

    def test_the_interpreter_is_named_and_the_venv_is_preferred(self):
        root = stub_root()
        try:
            (root / ".venv" / "bin").mkdir(parents=True)
            os.symlink(sys.executable, root / ".venv" / "bin" / "python")
            proc = run_stub(root, ["--model", "q2_0", "--dry-run"])
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn(f"interpreter: {root / '.venv' / 'bin' / 'python'}", proc.stdout)
        finally:
            shutil.rmtree(root)

    def test_a_missing_dependency_is_reported_before_the_gpu_is_touched(self):
        root = stub_root()
        try:
            env = sweep_env(root)
            env["CAL_DEPS"] = "regex,not_a_real_module_xyz"
            proc = subprocess.run(["bash", str(root / "tune" / "max_tune.sh"),
                                  "--model", "q2_0", "--short", "--layers", "kv"],
                                  capture_output=True, text=True, env=env,
                                  timeout=120, check=False)
            self.assertEqual(proc.returncode, 2, proc.stderr)
            self.assertIn("cannot import not_a_real_module_xyz", proc.stderr)
            self.assertIn("pip install", proc.stderr)
            self.assertNotIn("LAYER:", proc.stdout)   # the sweep never started
        finally:
            shutil.rmtree(root)

    def test_an_empty_report_falls_back_to_the_plain_sweep(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json") as fh:
            json.dump({"settings": {}, "report": {}}, fh)
            fh.flush()
            path = fh.name
            proc = sweep(["--model", "q2_0", "--short"], path)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("carries no measurements", proc.stderr)
        self.assertEqual(run_count(proc.stdout), STAGED_RUNS)


@NEEDS_ENGINE
class ArgmaxNotTheDefault(unittest.TestCase):
    """calibrate.py only keeps a value that beats the product default by MIN_GAIN. --short
    takes the measured maximum whatever the default says."""

    def test_a_maximum_below_the_default_still_wins(self):
        report = {
            "settings": {},
            "report": {
                "default": {"pcie_frac": 0.55, "spec_min_p": 0.5, "pool_workers": 23},
                "pcie_sweep": {"0.1": [70.0, 70.4], "0.35": [74.0, 74.6], "0.5": [71.0, 71.2]},
                "min_p_sweep": {"0.2": [74.0], "0.4": [73.0]},
                "workers": {"23": [74.0], "8": [76.0]},
                "adapt": {"default": [76.0], "1/80/0.97": [75.0]},
            },
        }
        with tempfile.NamedTemporaryFile("w", suffix=".json") as fh:
            json.dump(report, fh)
            fh.flush()
            proc = sweep(["--model", "q2_0", "--short"], fh.name)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("-> fixed 0.35", proc.stderr)
        self.assertIn("-> fixed 0.2", proc.stderr)
        self.assertIn("frozen by calibration: pool-workers -> workers=8", proc.stdout)
        for cmd in commands(proc.stdout):
            self.assertIn("--pcie-frac 0.35", cmd)
            self.assertIn("--spec-min-p 0.2", cmd)
            self.assertIn("--pool-workers 8", cmd)
        self.assertEqual(run_count(proc.stdout), SHORT_RUNS)




# ---------------------------------------------------------------- the real paths, with a stub engine
STUB_ENGINE = """#!/usr/bin/env bash
# A stand-in for engine/hypercore: boots, answers one GEN, and reports a rate that rises
# with --vram-reserve-mib so the staged sweep has a winner. QUIT unwinds it cleanly.
vram=0; prev=""
for a in "$@"; do
  case "$prev" in --vram-reserve-mib) vram="$a" ;; esac
  prev="$a"
done
sleep 1
echo "INFO context=131072 kv=q4_0 pool_workers=0"
echo "session is up"
while IFS= read -r line; do
  case "$line" in
    QUIT) echo "stub: clean exit"; break ;;
    GEN*) echo "DONE 512 1024 900 $(( 5120000 / (100 + vram) )) length" ;;
  esac
done
"""

STAMP_RE = r"\d{4}-\d{2}-\d{2}_\d{6}"


def stub_root() -> Path:
    """A throwaway engine root: a copy of max_tune.sh, a stub engine, and the prompt file.

    max_tune.sh derives every output path from its own directory, so a copy in a temp
    directory keeps the whole sweep - logs, CSV, config and run files - out of the repo.
    """
    root = Path(tempfile.mkdtemp())          # this is the engine root max_tune.sh will use
    tune = root / "tune"
    tune.mkdir()
    (tune / "max_tune.sh").write_text(SCRIPT.read_text(encoding="utf-8"), encoding="utf-8")
    (root / "engine").mkdir()
    stub = root / "engine" / "hypercore"
    stub.write_text(STUB_ENGINE, encoding="utf-8")
    stub.chmod(0o755)
    bench = root / "bench" / "results"
    bench.mkdir(parents=True)
    src = ROOT / "bench" / "results" / "exchange-rotation-token-ids.json"
    ids = json.loads(src.read_text(encoding="utf-8")) if src.exists() else {"input": [1, 2, 3]}
    (bench / "exchange-rotation-token-ids.json").write_text(json.dumps(ids), encoding="utf-8")
    # A calibration that takes a minute: lets the tests interrupt it.
    (root / "tools").mkdir()
    (root / "tools" / "calibrate.py").write_text(
        "import time\ntime.sleep(60)\n", encoding="utf-8")
    (root / "hypercore-q2_0.json").write_text(json.dumps(
        {"exe": str(root / "engine" / "hypercore"), "args": [], "log": str(root / "engine.log")},
        indent=1), encoding="utf-8")
    return root


def sweep_env(root: Path) -> dict[str, str]:
    env = dict(os.environ)
    env["GPU_MIN_FREE"] = "0"          # the stub needs no card
    env["CAL_DEPS"] = ""               # the stub calibrate.py needs no third-party imports
    return env


def run_stub(root: Path, args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(["bash", str(root / "tune" / "max_tune.sh")] + args,
                          capture_output=True, text=True, env=sweep_env(root),
                          timeout=180, check=False)


@NEEDS_ENGINE
class Outputs(unittest.TestCase):
    """Every file a sweep writes carries its date and time, so two runs never overwrite
    each other."""

    def test_matrix_log_csv_and_run_logs_are_timestamped(self):
        root = stub_root()
        try:
            proc = run_stub(root, ["--model", "q2_0", "--layers", "kv"])
            self.assertEqual(proc.returncode, 0, proc.stderr)
            matrix = re.search(r"matrix:\s+(\S+)", proc.stdout)
            csv = re.search(r"csv:\s+(\S+)", proc.stdout)
            self.assertTrue(matrix and csv, proc.stdout)
            self.assertRegex(Path(matrix.group(1)).name,
                            r"hypercore_max_tuning_matrix-" + STAMP_RE + r"\.log")
            self.assertRegex(Path(csv.group(1)).name, r"matrix-" + STAMP_RE + r"\.csv")
            logs = sorted((root / "tune" / "results").glob("run-*"))
            self.assertTrue(logs)
            for log in logs:
                self.assertRegex(log.name, r"run-" + STAMP_RE + r"-.*\.log")
        finally:
            shutil.rmtree(root)

    def test_a_second_sweep_does_not_clobber_the_first(self):
        root = stub_root()
        try:
            first = run_stub(root, ["--model", "q2_0", "--layers", "kv"])
            second = run_stub(root, ["--model", "q2_0", "--layers", "kv"])
            a = re.search(r"matrix:\s+(\S+)", first.stdout).group(1)
            b = re.search(r"matrix:\s+(\S+)", second.stdout).group(1)
            self.assertNotEqual(a, b)
            self.assertTrue(os.path.getsize(a) > 0 and os.path.getsize(b) > 0)
        finally:
            shutil.rmtree(root)


@NEEDS_ENGINE
class Interrupt(unittest.TestCase):
    """Ctrl-C stops the sweep, unwinds the engine, and keeps the best configuration found."""

    def test_ctrl_c_unwinds_and_saves_the_best_so_far(self):
        root = stub_root()
        try:
            proc = subprocess.Popen(["bash", str(root / "tune" / "max_tune.sh"), "--model", "q2_0",
                                    "--layers", "topology"],
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    text=True, env=sweep_env(root))
            time.sleep(6)                       # a few configurations in
            proc.send_signal(signal.SIGINT)
            out = proc.communicate(timeout=90)[0]
            self.assertEqual(proc.returncode, 130, out)
            self.assertIn("caught INT, unwinding", out)
            self.assertIn("SWEEP STOPPED after", out)
            self.assertIn("best so far:", out)
            # The engine's own log is where the graceful QUIT shows up, not the sweep stdout.
            logs = sorted((root / "tune" / "results").glob("run-*.log"))
            self.assertTrue(logs, out)
            self.assertIn("stub: clean exit", logs[-1].read_text(encoding="utf-8"))

            cfg = root / "tune" / "max_config_q2_0.sh"
            run = root / "tune" / "max_run_q2_0.sh"
            self.assertTrue(cfg.exists(), out)
            self.assertTrue(run.exists(), out)
            text = cfg.read_text(encoding="utf-8")
            self.assertIn("The sweep was stopped (interrupted)", text)
            self.assertIn("HC_COMPLETE=0", text)
            self.assertIn("HC_PEAK_TPS=", text)
            self.assertIn("From a sweep stopped", run.read_text(encoding="utf-8"))
            check = subprocess.run(["bash", "-n", str(run)], capture_output=True,
                                   text=True, check=False)
            self.assertEqual(check.returncode, 0, check.stderr)

            matrix = next((root / "tune").glob("hypercore_max_tuning_matrix-*.log"), None)
            self.assertTrue(matrix is not None)
            lines = [l for l in matrix.read_text(encoding="utf-8").splitlines() if l.startswith("runs=")]
            self.assertTrue(lines, matrix.read_text())
        finally:
            shutil.rmtree(root)

    def test_ctrl_c_stops_a_running_calibration(self):
        root = stub_root()
        try:
            proc = subprocess.Popen(["bash", str(root / "tune" / "max_tune.sh"), "--model", "q2_0",
                                    "--short", "--layers", "kv"],
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    text=True, env=sweep_env(root))
            time.sleep(4)
            proc.send_signal(signal.SIGINT)
            out = proc.communicate(timeout=60)[0]
            self.assertEqual(proc.returncode, 130, out)
            self.assertIn("CALIBRATION: tools/calibrate.py", out)
            self.assertIn("caught INT, unwinding", out)
            self.assertNotIn("LAYER:", out)          # the sweep never started
        finally:
            shutil.rmtree(root)

    def test_interrupting_before_any_result_writes_nothing(self):
        root = stub_root()
        try:
            proc = subprocess.Popen(["bash", str(root / "tune" / "max_tune.sh"), "--model", "q2_0",
                                    "--layers", "topology"],
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    text=True, env=sweep_env(root))
            time.sleep(1)
            proc.send_signal(signal.SIGINT)
            out = proc.communicate(timeout=90)[0]
            self.assertEqual(proc.returncode, 130, out)
            self.assertIn("nothing measured", out)
            self.assertFalse((root / "tune" / "max_config_q2_0.sh").exists())
        finally:
            shutil.rmtree(root)


if __name__ == "__main__":

    unittest.main()
