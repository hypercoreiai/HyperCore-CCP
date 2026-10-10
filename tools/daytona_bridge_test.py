#!/usr/bin/env python3
"""Verify the frozen boundary against a machine that shares nothing with this one.

    DAYTONA_API_KEY=... python3 tools/daytona_bridge_test.py

Three checks, none reproducible locally:

  1. Header portability. The public header is compiled by the sandbox's own gcc, with no
     HyperCore source anywhere in sight. If the header needs a GNU extension or a newer
     standard than it claims, this is where it shows up.
  2. Mirror drift on a foreign interpreter. tools/check_abi_alignment.py runs remotely, so
     the Python struct mirrors are checked against the header under a different CPython.
  3. ABI against the shipped artifact. The tests are compiled remotely and linked against
     the .so built here, then run. Different toolchain, same bytes.
  4. glibc floor. Every undefined reference in an artifact carries the symbol version the
     linker resolved it to, so a .so built on a newer glibc can fail to link on an older one
     with nothing in the source saying so. The floor is read off the binary and compared with
     the sandbox's own libc before any test is compiled.

The build-time target `hypercore_abi_alignment_check` catches drift on this machine; this
harness is the one that catches a host that is not this machine. Run it as a CI job, not
as a one-off - a boundary nobody re-tests is a boundary nobody owns.
"""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

try:                                   # the SDK is in .venv_daytona; see requirements-daytona.txt
    from daytona import CreateSandboxFromImageParams, Daytona
except ImportError:                    # importing this file must not break the suite
    Daytona = CreateSandboxFromImageParams = None

SRC = Path(__file__).resolve().parents[1]
LAB = SRC / "bench/results/2026-10-09-blackbox-api"


def _artifact(name: str) -> Path:
    """The built library or worker, wherever this build went. Locally it is in build-shared;
    a CI runner builds into build. Whichever exists is the one to ship to the sandbox.
    """
    for d in ("build-shared", "build"):
        p = SRC / d / name
        if p.exists():
            return p
    return SRC / "build-shared" / name


ARTIFACT = _artifact("libhypercore_api.so.0.1.40")
WORKER = _artifact("hypercore-worker")

# Uploads are keyed by the path they land at in the sandbox, so the C tests can
# `#include "hypercore/hypercore_api.h"` exactly as they do on this machine.
UPLOADS = [
    (SRC / "include/hypercore/hypercore_api.h", "hypercore/hypercore_api.h"),
    (SRC / "serve/ipc_parser.py", "serve/ipc_parser.py"),
    (SRC / "tools/check_abi_alignment.py", "tools/check_abi_alignment.py"),
    (SRC / "tools/glibc_floor.py", "tools/glibc_floor.py"),
    (ARTIFACT, "libhypercore_api.so.0.1.40"),
    # worker_mode_test drives the out-of-process mode through the same entry point, so the
    # remote run needs the worker binary as well. LD_LIBRARY_PATH points it at the uploaded
    # library instead of the build directory baked into its rpath.
    (WORKER, "hypercore-worker"),
]
TESTS = (
    "abi_test.c",
    "busy_test.c",
    "precedence_test.c",
    "summary_test.c",
    "pool_test.c",
    "cancel_test.c",
    "resolve_test.c",
    "worker_mode_test.c",
)

HEADER_ONLY = (
    "gcc -std=c11 -Wall -Wextra -pedantic -I. -x c -c -o /dev/null - <<'EOF'\n"
    '#include "hypercore/hypercore_api.h"\n'
    "int main(void){ hypercore_caps_t c; c.struct_size = sizeof c; "
    "return hypercore_engine_get_caps(0, &c) == HYPERCORE_STATUS_SUCCESS ? 0 : 1; }\n"
    "EOF"
)

ALIGNMENT = "python3 tools/check_abi_alignment.py --header hypercore/hypercore_api.h"

# The floor is measured on the sandbox, not asserted from here: the deployment host is what
# decides what can be linked, not the machine that produced the artifact.
FLOOR = (
    'echo "sandbox_libc: $(ldd --version 2>/dev/null | head -1)"; '
    "python3 tools/glibc_floor.py libhypercore_api.so.0.1.40"
)

RUN = (
    "export LD_LIBRARY_PATH=.; "
    "fail=0; "
    "for t in " + " ".join(n[:-2] for n in TESTS) + "; do "
    "  if ! gcc -std=c11 -Wall -Wextra -I. $t.c -L. -lhypercore_api -Wl,-rpath,. -o $t 2>/tmp/cerr.txt; "
    "  then echo \"COMPILE FAIL: $t\"; head -3 /tmp/cerr.txt; fail=1; continue; fi; "
    "  if ! ./$t > /tmp/rout.txt 2>&1; "
    "  then echo \"RUN FAIL: $t\"; grep -E 'FAIL|error' /tmp/rout.txt | head -4; fail=1; fi; "
    "done; echo \"remote_c_fail=$fail\"; exit $fail"
)


def say(line: str) -> None:
    print(line, flush=True)


def main() -> int:
    key = os.environ.get("DAYTONA_API_KEY")
    if not key:
        say("DAYTONA_API_KEY is not set; this harness needs a sandbox, it has no local mode.")
        return 2
    if not ARTIFACT.exists() or not WORKER.exists():
        say(
            f"missing build output: {ARTIFACT} or {WORKER}\n"
            "Build it first: cmake --build build-shared --target hypercore-api hypercore-worker"
        )
        return 2

    daytona = Daytona()
    sandbox = daytona.create(CreateSandboxFromImageParams(image="python:3.11"))
    try:
        say(f"sandbox: {sandbox.name}  artifact: {ARTIFACT.stat().st_size} bytes")
        for local, remote in UPLOADS:
            if not local.exists():
                say(f"missing upload: {local}")
                return 2
            sandbox.fs.upload_file(str(local), remote)
        # The artifact carries a soname (libhypercore_api.so.0), so the loader needs that
        # name too - a bare `libhypercore_api.so` symlink is not enough to run it. Uploads
        # arrive without the execute bit, so the worker has to be made runnable. Both have
        # to happen after the files land, not before.
        sandbox.process.exec(
            "ln -sf libhypercore_api.so.0.1.40 libhypercore_api.so && "
            "ln -sf libhypercore_api.so.0.1.40 libhypercore_api.so.0 && "
            "chmod +x hypercore-worker"
        )
        for name in TESTS:
            sandbox.fs.upload_file(str(LAB / name), name)

        header = sandbox.process.exec(HEADER_ONLY, timeout=60)
        say(f"header-only compile: {'ok' if header.exit_code == 0 else header.result}")
        if header.exit_code != 0:
            return 1

        align = sandbox.process.exec(ALIGNMENT, timeout=60)
        say(f"mirror drift check: {'ok' if align.exit_code == 0 else align.result}")
        if align.exit_code != 0:
            return 1

        floor = sandbox.process.exec(FLOOR, timeout=60)
        say(floor.result.strip())
        if floor.exit_code != 0:
            say("the artifact cannot be linked on this host; the C ABI stage cannot run.")
            return 1

        run = sandbox.process.exec(RUN, timeout=120)
        say(run.result)
        if run.exit_code != 0:
            say(
                "the header and the mirror checks passed, so the contract is sound; the "
                "stage above names which test failed and why. A COMPILE FAIL is an ABI or "
                "libc problem, a RUN FAIL is behaviour on a foreign host."
            )
        return 0 if run.exit_code == 0 else 1
    finally:
        daytona.delete(sandbox)


class DaytonaBridge(unittest.TestCase):
    """Collected by pytest, skipped when there is no SDK or no key to use it with."""

    def test_the_remote_boundary_harness_runs(self):
        if Daytona is None:
            self.skipTest("Daytona SDK not installed: pip install -r requirements-daytona.txt")
        if not os.environ.get("DAYTONA_API_KEY"):
            self.skipTest("no DAYTONA_API_KEY")
        self.assertEqual(main(), 0, "the cross-machine boundary checks failed")


if __name__ == "__main__":
    if Daytona is None:
        print("the Daytona SDK is not installed: pip install -r requirements-daytona.txt", file=sys.stderr)
        raise SystemExit(2)
    sys.exit(main())
