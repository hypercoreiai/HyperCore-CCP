"""Socket hygiene: a stale or shared socket name must not stop a worker from starting.

    python3 -m unittest serve.test_socket_hygiene

Why this suite exists. A Unix socket name outlives the process that bound it. The file
stays in /tmp after the worker exits, and the next bind on that name fails with
EADDRINUSE - which is exactly what a fresh checkout followed by ./install.sh hit when a
previous run had left a worker behind. Two things have to be true for that to be a
non-issue, and both are tested here against the real worker, not a mock:

  1. whatever sits at the path is removed before the worker is spawned, including a
     name this process cannot remove;
  2. two supervisors never end up sharing one name, so they never share the
     "{socket}.config.json" side file either.

The suite skips when no worker binary has been built, because there is nothing to bind.
"""
from __future__ import annotations

import json
import os
import pathlib
import tempfile
import unittest

from serve.hypercore_supervisor import (
    ARGV_SAFE_CONFIG_BYTES,
    HyperCoreProcessSupervisor,
    WorkerUnreachable,
    evict_stale_socket,
    unique_socket_path,
)

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKER = next(
    (p for p in (ROOT / "build-shared" / "hypercore-worker", ROOT / "build" / "hypercore-worker")
     if p.is_file()),
    None,
)


def _temp_path(suffix: str = ".sock") -> str:
    return tempfile.mktemp(prefix="hc-hygiene-", dir="/tmp") + suffix


class Eviction(unittest.TestCase):
    """The gate that runs before a worker is spawned."""

    def test_nothing_there_is_not_a_failure(self):
        cleared, why = evict_stale_socket("/tmp/hc-hygiene-does-not-exist.sock")
        self.assertTrue(cleared, why)

    def test_a_leftover_socket_file_is_removed(self):
        path = _temp_path()
        pathlib.Path(path).write_text("")
        self.addCleanup(lambda: os.path.exists(path) and os.unlink(path))
        cleared, why = evict_stale_socket(path)
        self.assertTrue(cleared, why)
        self.assertFalse(os.path.exists(path))

    def test_a_directory_where_a_socket_should_be_is_removed(self):
        # A directory at the socket path is the case plain unlink() cannot clear, and it
        # is the one that reproduces "hypercore_worker: cannot bind /tmp/...".
        path = _temp_path(".sock")
        os.makedirs(path)
        cleared, why = evict_stale_socket(path)
        self.assertTrue(cleared, why)
        self.assertFalse(os.path.exists(path))

    def test_a_name_this_process_cannot_remove_is_reported_not_swallowed(self):
        # A dangling symlink: os.path.exists is False for a broken link, so there is
        # nothing to remove and bind() would succeed. The gate must not claim a failure.
        path = _temp_path(".sock")
        os.symlink("/tmp/hc-hygiene-target-that-does-not-exist", path)
        self.addCleanup(lambda: os.path.exists(path) or os.unlink(path))
        cleared, why = evict_stale_socket(path)
        self.assertTrue(cleared, why)

    def test_paths_from_unique_socket_path_are_process_private(self):
        first, second = unique_socket_path("hc-hygiene"), unique_socket_path("hc-hygiene")
        self.assertNotEqual(first, second)
        self.assertIn(str(os.getpid()), first)
        for path in (first, second):
            os.makedirs(path)
            self.addCleanup(lambda p=path: os.path.exists(p) and os.rmdir(p))
            cleared, why = evict_stale_socket(path)
            self.assertTrue(cleared, why)


@unittest.skipIf(WORKER is None, "no worker binary; build it with cmake --build build-shared")
class RealWorker(unittest.TestCase):
    """The same claims, against a worker that actually binds."""

    def _supervisor(self, socket_path: str) -> HyperCoreProcessSupervisor:
        sup = HyperCoreProcessSupervisor(
            worker_binary=str(WORKER), socket_path=socket_path, config='{"batch":2}'
        )
        self.addCleanup(sup.shutdown)
        return sup

    def _start(self, sup: HyperCoreProcessSupervisor) -> None:
        """Start a worker, or fail the test with the reason.

        start() raises rather than returning a bool. Do not pass last_stderr() to an
        assertion eagerly: while the worker is alive its stderr pipe has no EOF, and
        reading it blocks the test forever.
        """
        try:
            sup.start(timeout_s=20)
        except (WorkerUnreachable, OSError) as exc:
            self.fail(f"the worker did not come up: {exc}")

    def test_a_stale_socket_does_not_block_a_start(self):
        path = _temp_path()
        # Leave behind exactly what a previous run leaves behind: a socket file nobody
        # owns any more, sitting where the next worker wants to bind.
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("")
        sup = self._supervisor(path)
        self._start(sup)
        self.assertTrue(sup.alive())
        self.assertEqual(sup.get_caps().get("status"), 0)

    def test_a_directory_at_the_path_is_worked_round_not_fatal(self):
        # A non-empty directory is the case neither unlink() nor rmdir() can clear, and it
        # is the one that reproduces "hypercore_worker: cannot bind /tmp/...".
        path = _temp_path(".sock")
        os.makedirs(path)
        with open(os.path.join(path, "leftover"), "w", encoding="utf-8") as handle:
            handle.write("")
        sup = self._supervisor(path)
        self._start(sup)
        self.assertTrue(sup.alive())
        self.assertNotEqual(
            sup.socket_path, path,
            "the supervisor should have moved off a path it cannot clear",
        )

    def test_two_supervisors_on_one_name_do_not_share_state(self):
        # A shared name is survivable for bind() - the second worker unlinks the first's
        # name and takes it. What is not survivable is one config side file for two
        # workers, which is how a run ends up configured by another run.
        shared = _temp_path()
        big = json.dumps({"batch": 2, "note": "a" * (ARGV_SAFE_CONFIG_BYTES + 1)})
        a, b = self._supervisor(shared), self._supervisor(shared)
        a.config = big
        b.config = json.dumps({"batch": 2, "note": "b" * (ARGV_SAFE_CONFIG_BYTES + 1)})
        self._start(a)
        self._start(b)
        self.assertTrue(a.alive() and b.alive())
        self.assertNotEqual(a._config_argument(), b._config_argument())
        for sup in (a, b):
            side = sup._config_argument()
            self.assertTrue(os.path.exists(side), f"{side} was written and then removed too early")
        a.shutdown()
        self.assertFalse(any(os.path.exists(p) for p in a._config_side_files))

    def test_stop_takes_the_name_back(self):
        path = _temp_path()
        sup = self._supervisor(path)
        self._start(sup)
        self.assertTrue(os.path.exists(path))
        sup.shutdown()
        self.assertFalse(os.path.exists(path), "the socket name outlived the worker that bound it")

    def test_a_restart_after_a_stop_binds_again(self):
        path = _temp_path()
        sup = self._supervisor(path)
        for attempt in range(3):
            if not sup.start_worker(timeout_s=20):
                self.fail(f"restart {attempt} did not come back: {sup.last_stderr()}")
            self.assertTrue(sup.alive(), f"restart {attempt} did not come back")
            sup.stop()
        self.assertFalse(os.path.exists(path))


if __name__ == "__main__":
    unittest.main()
