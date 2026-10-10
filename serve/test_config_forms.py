#!/usr/bin/env python3
"""serve/test_config_forms.py - the CLI accepts a path or inline JSON.

The rule is the one the C boundary uses: the first non-whitespace character decides.
These tests assert the Python side makes the same decision, so `--config` cannot mean
one thing to the server and another to hypercore_engine_init.
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from serve.hypercore_supervisor import HyperCoreProcessSupervisor
from serve.server import (
    hypercore_worker_config,
    is_inline_config,
    load_config_text,
    resolve_configuration_payload,
    verbatim_object_slice,
)


class ConfigFormTest(unittest.TestCase):
    def test_inline_json_is_not_read_as_a_path(self) -> None:
        cfg = load_config_text('{"batch": 3, "sampling": {"temperature": 0.0}}')
        self.assertEqual(cfg["batch"], 3)

    def test_padded_inline_json_is_still_inline(self) -> None:
        self.assertTrue(is_inline_config("   {\"a\": 1}"))
        self.assertFalse(is_inline_config("  /tmp/whatever.json"))
        self.assertFalse(is_inline_config(""))

    def test_a_path_is_read(self) -> None:
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            f.write('{"exe": "build-shared/hypercore-worker", "batch": 2}')
            path = f.name
        try:
            cfg = load_config_text(path)
            self.assertEqual(cfg["batch"], 2)
            self.assertEqual(cfg["exe"], "build-shared/hypercore-worker")
        finally:
            Path(path).unlink()

    def test_a_missing_path_is_an_error_not_an_empty_config(self) -> None:
        with self.assertRaises(SystemExit):
            load_config_text("/tmp/definitely-not-here.json")

    def test_a_non_object_json_is_rejected(self) -> None:
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            f.write("[1, 2, 3]")
            path = f.name
        try:
            with self.assertRaises(SystemExit):
                load_config_text(path)
        finally:
            Path(path).unlink()

    def test_no_config_is_no_config(self) -> None:
        self.assertEqual(load_config_text(None), {})
        self.assertEqual(load_config_text(""), {})
        self.assertEqual(load_config_text("   "), {})


def write_tmp(body: str) -> str:
    """Write a config file and return its path; the caller removes it."""
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
        handle.write(body)
        return handle.name


class ConfigPayloadTest(unittest.TestCase):
    """The bytes the worker receives are the bytes the deployment wrote."""

    PRETTY = '{\n  "worker_config": {\n    "batch": 4,\n    "pool_workers": 12\n  }\n}'

    def test_inline_json_is_forwarded_verbatim(self) -> None:
        raw = '{\n  "batch": 3,\n  "sampling": {\n    "temperature": 0.0\n  }\n}'
        self.assertEqual(resolve_configuration_payload(raw), raw)
        # the mutation the rule is guarding against
        self.assertNotEqual(json.dumps(json.loads(raw)), raw)

    def test_a_worker_block_keeps_its_exact_characters(self) -> None:
        cfg = json.loads(self.PRETTY)
        forwarded = hypercore_worker_config(cfg, self.PRETTY)
        self.assertEqual(forwarded, verbatim_object_slice(self.PRETTY, "worker_config"))
        self.assertEqual(json.loads(forwarded), cfg["worker_config"])
        self.assertNotEqual(forwarded, json.dumps(cfg["worker_config"]))

    def test_a_synthesised_config_is_still_built_from_flags(self) -> None:
        cfg = {"args": ["--batch", "6"]}
        self.assertEqual(json.loads(hypercore_worker_config(cfg, json.dumps(cfg)))["batch"], 6)

    def test_an_empty_file_is_a_hard_error(self) -> None:
        for body in ("", "   \n  "):
            path = write_tmp(body)
            try:
                with self.assertRaises(ValueError):
                    resolve_configuration_payload(path)
            finally:
                Path(path).unlink()

    def test_the_ceiling_is_ten_megabytes(self) -> None:
        limit = 10 * 1024 * 1024
        with self.assertRaises(ValueError):
            resolve_configuration_payload('{"batch":4}' + " " * (limit - 10))      # limit + 1 bytes
        payload = '{"batch":4}' + " " * (limit - 11)                              # exactly limit
        self.assertEqual(len(payload), limit)
        self.assertEqual(json.loads(resolve_configuration_payload(payload))["batch"], 4)

        big = write_tmp('{"batch":5}' + " " * limit)
        ok = write_tmp('{"batch":5}' + " " * (9 * 1024 * 1024))
        try:
            with self.assertRaises(ValueError):
                resolve_configuration_payload(big)
            self.assertEqual(load_config_text(ok)["batch"], 5)
        finally:
            Path(big).unlink()
            Path(ok).unlink()

    def test_a_config_too_large_for_argv_is_handed_over_by_path(self) -> None:
        big = '{"batch":4,"pad":' + '"' + "x" * 200000 + '"}'
        supervisor = HyperCoreProcessSupervisor(
            worker_binary="/nonexistent-worker",
            socket_path="/tmp/hc_argv_probe.sock",
            config=big,
        )
        argument = supervisor._config_argument()
        self.assertNotEqual(argument, big)                    # would exceed MAX_ARG_STRLEN
        self.assertEqual(Path(argument).read_text(encoding="utf-8"), big)
        Path(argument).unlink()

        supervisor.config = '{"batch":2}'
        self.assertEqual(supervisor._config_argument(), '{"batch":2}')   # small stays inline


if __name__ == "__main__":
    unittest.main()
