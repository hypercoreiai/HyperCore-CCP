#!/usr/bin/env python3
"""serve/test_abi_contract.py - the contract lock has to lock, not just report.

tools/check_abi_alignment.py is a build dependency of both hypercore_api and
hypercore-worker, so a false PASS is worse than a crash: it means a build shipped a
layout nobody verified. These cases prove the checker rejects the drifts it claims to
catch, by editing the real header rather than a fixture that could drift away from it.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.check_abi_alignment import (
    HOT_PATH_CONFIG,
    HOT_PATH_CONFIG_BYTES,
    HOT_PATH_CONFIG_OFFSETS,
    parse_packed_structs,
    verify_request_config_alignment,
)

REPO = Path(__file__).resolve().parents[1]
REAL_HEADER = REPO / "include/hypercore/hypercore_api.h"


def run_lock(header: str) -> int:
    """Run the contract lock as the build runs it, against a given header."""
    proc = subprocess.run(
        [sys.executable, "tools/check_abi_alignment.py", "--header", header, "--quiet"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode


def perturbed(edit: tuple[str, str]) -> str:
    """The real header with one change. Everything else about it stays real."""
    old, new = edit
    text = REAL_HEADER.read_text()
    if old not in text:
        raise AssertionError(f"the header no longer contains {old!r}; the test is stale")
    with tempfile.NamedTemporaryFile("w", suffix=".h", delete=False) as fh:
        fh.write(text.replace(old, new, 1))
        return fh.name


class HotPathConfigTest(unittest.TestCase):
    """The request config is the struct every inference call crosses on."""

    def test_the_pinned_offsets_match_the_shipped_header(self) -> None:
        problems = verify_request_config_alignment(parse_packed_structs(REAL_HEADER.read_text()))
        self.assertEqual(problems, [], f"the shipped header does not satisfy its own contract: {problems}")

    def test_a_field_inserted_above_top_k_is_caught(self) -> None:
        path = perturbed(("    uint32_t top_k;", "    uint32_t reserved;\n    uint32_t top_k;"))
        try:
            problems = verify_request_config_alignment(
                parse_packed_structs(Path(path).read_text())
            )
            joined = " ".join(problems)
            self.assertTrue(problems, "inserting a field above top_k was not detected")
            self.assertIn("reserved", joined)
            self.assertIn("top_k", joined)
        finally:
            Path(path).unlink()

    def test_a_field_removed_from_the_hot_path_is_caught(self) -> None:
        path = perturbed(("    float    top_p;            /* [0, 1] */\n", ""))
        try:
            problems = verify_request_config_alignment(
                parse_packed_structs(Path(path).read_text())
            )
            self.assertTrue(problems, "removing top_p was not detected")
            self.assertIn("top_p", " ".join(problems))
        finally:
            Path(path).unlink()

    def test_a_widened_field_is_caught(self) -> None:
        path = perturbed(("    uint32_t top_k;", "    uint64_t top_k;"))
        try:
            problems = verify_request_config_alignment(
                parse_packed_structs(Path(path).read_text())
            )
            self.assertTrue(any("4 bytes" in p for p in problems), problems)
        finally:
            Path(path).unlink()

    def test_a_missing_struct_is_a_failure_not_a_pass(self) -> None:
        self.assertTrue(verify_request_config_alignment({}))

    def test_the_contract_is_written_down_not_derived(self) -> None:
        # A "simplification" that replaces the table with len(fields) would still pass
        # today and would not catch a reorder tomorrow.
        self.assertEqual(HOT_PATH_CONFIG, "hypercore_request_config_t")
        self.assertEqual(HOT_PATH_CONFIG_BYTES, 28)
        self.assertEqual(sorted(HOT_PATH_CONFIG_OFFSETS.values()), list(range(0, 28, 4)))

    def test_the_real_header_passes_end_to_end(self) -> None:
        self.assertEqual(run_lock(str(REAL_HEADER)), 0)

    def test_a_drifted_header_fails_end_to_end(self) -> None:
        path = perturbed(
            ("    uint32_t max_new_tokens;", "    uint32_t max_new_tokens;\n    uint32_t seed;")
        )
        try:
            self.assertEqual(
                run_lock(path), 1, "a drifted header must fail the lock, not warn"
            )
        finally:
            Path(path).unlink()


if __name__ == "__main__":
    unittest.main()
