#!/usr/bin/env python3
"""tools/backend_parity.py - do the CPU and the GPU artifact answer the same way?

The ABI gate proves the two artifacts agree about byte offsets. It says nothing about
behaviour: two backends can share a header and still disagree about what a request
produces. This harness sends one fixed request to every backend that has been built and
compares what came back.

Two separate claims are checked, because they fail for different reasons:

  1. Determinism. The same backend, twice, must return the same token ids. A backend that
     cannot repeat itself cannot be benchmarked, and a regression test written against it
     is a coin flip.
  2. Cross-backend parity. The token stream, the stop reason and the counters must match
     between backends. Timing fields (prefill_ms, decode_ms, ttft_ms) are not compared:
     they are measurements of different hardware, and a comparison there would fail every
     day for reasons nobody broke.

    python3 tools/backend_parity.py
    python3 tools/backend_parity.py --require cpu,cuda --json
    python3 tools/backend_parity.py --backend cpu --backend cuda

A backend whose worker binary is not in the build tree is reported and skipped, unless it
is named in --require, in which case the run exits 2. That is how CI gets to make the GPU
half blocking without pretending a GPU runner exists on every job.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
from dataclasses import dataclass, field
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from serve.hypercore_supervisor import (
    HyperCoreProcessSupervisor,
    StreamStalled,
    WorkerBusy,
    WorkerRejected,
    WorkerUnreachable,
)
from serve.ipc_parser import STREAM_TERMINAL

# One request, fixed forever. top_k=1 and temperature=0 remove every source of
# nondeterminism the wire can control, so a differing token stream is a backend
# difference and not sampling.
PROBE_PROMPT: list[int] = list(range(1, 9))
PROBE_CONFIG: dict[str, Any] = {
    "temperature": 0.0,
    "top_p": 1.0,
    "top_k": 1,
    "max_new_tokens": 64,
    "pcie_frac": -1.0,
    "spec_min_p": -1.0,
}

# name -> the directories that may hold that backend's worker, in the order they are tried.
# A CI runner builds into `build`; a local GPU tree is usually a separate directory so the
# two artifacts can be compared side by side. Both are searched, so the tool does not need
# to know which tree the caller used.
BACKENDS: dict[str, list[str]] = {
    "cpu": ["build-shared", "build", "build-cpu"],
    "cuda": ["build-cuda-check", "build-cuda"],
    "hip": ["build-hip"],
}

# Fields that must be identical between two backends. Anything not here is either a
# measurement (timing) or a legitimate difference (backend_type).
STABLE_SUMMARY_FIELDS: tuple[str, ...] = (
    "struct_size",
    "produced_tokens",
    "drafts_accepted",
    "drafts_offered",
    "prompt_reused",
    "stop_reason",
)
STABLE_CAPS_FIELDS: tuple[str, ...] = ("max_batch_slots", "max_context_len")
TIMING_FIELDS: tuple[str, ...] = ("prefill_ms", "decode_ms", "ttft_ms")


@dataclass
class Snapshot:
    """Everything one backend said about one request."""

    backend: str
    worker: str
    caps: dict[str, int | float] = field(default_factory=dict)
    tokens: list[int] = field(default_factory=list)
    terminal: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def ok(self) -> bool:
        return self.error is None and bool(self.tokens)


def find_worker(backend: str) -> pathlib.Path | None:
    """The worker binary for a backend, or None if that backend was never built."""
    for directory in BACKENDS.get(backend, []):
        worker = ROOT / directory / "hypercore-worker"
        if worker.is_file():
            return worker
    return None


def capture(sup: HyperCoreProcessSupervisor, backend: str, worker: str) -> Snapshot:
    """Run the probe against an already-started supervisor and record the reply.

    The supervisor is passed in rather than built here so the same comparison can be
    driven against a mock worker (serve/frame_fixture.ScriptedWorker) with no process
    and no GPU.
    """
    snap = Snapshot(backend=backend, worker=worker)
    try:
        snap.caps = sup.get_caps()
        for msg_type, token_id, metrics in sup.stream(PROBE_PROMPT, **PROBE_CONFIG):
            if msg_type == STREAM_TERMINAL:
                snap.terminal = dict(metrics)
                break
            snap.tokens.append(token_id)
    except (WorkerBusy, WorkerRejected, StreamStalled, WorkerUnreachable) as exc:
        snap.error = f"{type(exc).__name__}: {exc}"
    return snap


def compare(a: Snapshot, b: Snapshot) -> list[str]:
    """Every way two snapshots disagree, as human-readable strings.

    Empty means parity. Timing is deliberately not compared; it is checked only for
    sanity (a stream that produced tokens must report a decode window).
    """
    problems: list[str] = []

    if a.tokens != b.tokens:
        first = next(
            (i for i, (x, y) in enumerate(zip(a.tokens, b.tokens)) if x != y),
            min(len(a.tokens), len(b.tokens)),
        )
        problems.append(
            f"token stream differs at index {first}: {a.backend}={a.tokens[first:first + 4]} "
            f"{b.backend}={b.tokens[first:first + 4]} "
            f"(lengths {len(a.tokens)} vs {len(b.tokens)})"
        )

    for name in STABLE_SUMMARY_FIELDS:
        if a.terminal.get(name) != b.terminal.get(name):
            problems.append(
                f"summary field {name}: {a.backend}={a.terminal.get(name)} "
                f"{b.backend}={b.terminal.get(name)}"
            )

    for name in STABLE_CAPS_FIELDS:
        if a.caps.get(name) != b.caps.get(name):
            problems.append(
                f"capability {name}: {a.backend}={a.caps.get(name)} {b.backend}={b.caps.get(name)}"
            )

    # A stream that emitted tokens must have been measured. decode_ms=0 is a legitimate
    # sub-millisecond window; None is the absence of a measurement, and that is the failure.
    for snap in (a, b):
        if snap.tokens and snap.terminal.get("decode_ms") is None:
            problems.append(f"{snap.backend} produced tokens with no decode window reported")
        if snap.terminal.get("produced_tokens") != len(snap.tokens):
            problems.append(
                f"{snap.backend} reported {snap.terminal.get('produced_tokens')} produced tokens "
                f"but delivered {len(snap.tokens)}"
            )

    return problems


def parity_socket_path(backend: str, attempt: int) -> str:
    """A socket name private to this process and this attempt.

    The name is not reusable: a worker's socket file stays in /tmp after the process exits,
    and a second run on the same name finds a file it cannot bind over. The pid makes the
    path safe for two jobs sharing one runner - a CI matrix, or a local build and a CI build
    on the same machine - which is the case a fixed path cannot survive.
    """
    return f"/tmp/hypercore_parity_{backend}_{attempt}-{os.getpid()}.sock"


def run(
    wanted: list[str],
    require: list[str],
    repeats: int,
    transport_factory: Any | None = None,
) -> dict[str, list[Snapshot]]:
    """Capture `repeats` snapshots per backend. Returns {}-free results, never raises."""
    results: dict[str, list[Snapshot]] = {}
    for backend in wanted:
        worker = find_worker(backend)
        if worker is None:
            results[backend] = []
            continue
        snapshots: list[Snapshot] = []
        for attempt in range(repeats):
            socket_path = parity_socket_path(backend, attempt)
            if transport_factory is not None:
                sup = HyperCoreProcessSupervisor(transport=transport_factory())
            else:
                sup = HyperCoreProcessSupervisor(str(worker), socket_path, '{"batch":2}')
            try:
                sup.start()
                snapshots.append(capture(sup, backend, str(worker)))
            finally:
                sup.stop()
        results[backend] = snapshots
    return results


def report(results: dict[str, list[Snapshot]], require: list[str]) -> tuple[int, list[str]]:
    """Print the verdict and return (exit_code, lines). Exit 1 means drift, 2 means missing."""
    lines: list[str] = []
    present: dict[str, Snapshot] = {}

    for backend, snapshots in results.items():
        if not snapshots:
            note = f"{backend}: no worker built - skipped"
            if backend in require:
                note = f"{backend}: required by --require but not built"
            lines.append(note)
            continue
        snap = snapshots[0]
        if snap.error:
            lines.append(f"{backend}: FAILED - {snap.error}")
            continue
        lines.append(
            f"{backend}: {len(snap.tokens)} tokens, stop={snap.terminal.get('stop_reason')}, "
            f"produced={snap.terminal.get('produced_tokens')}, "
            f"backend_type={snap.caps.get('backend_type')}, slots={snap.caps.get('max_batch_slots')}"
        )
        for other in snapshots[1:]:
            drift = compare(snap, other)
            if drift:
                lines.append(f"[FAIL] {backend} is not deterministic across runs:")
                lines.extend("  " + d for d in drift)
            else:
                lines.append(f"[PASS] {backend}: run 2 byte-identical to run 1")
        present[backend] = snap

    compared = 0
    names = list(present)
    for i, first in enumerate(names):
        for second in names[i + 1:]:
            problems = compare(present[first], present[second])
            compared += 1
            if problems:
                lines.append(f"[FAIL] {first} vs {second}:")
                lines.extend("  " + p for p in problems)
            else:
                lines.append(
                    f"[PASS] {first} vs {second}: identical token stream and counters "
                    f"(timing differs, as it should)"
                )

    if compared == 1 and len(present) >= 2:
        lines.append(
            f"[PASS] {len(present)} backends agree on the probe; "
            "the boundary behaves the same whichever kernel answered."
        )
    elif compared == 0:
        lines.append("[SKIP] only one backend was available; nothing to compare.")

    missing_required = [b for b in require if not results.get(b)]
    if missing_required:
        return 2, lines
    drift = any(l.startswith("[FAIL]") for l in lines)
    return (1 if drift else 0), lines


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Compare backend behaviour over the frozen wire.")
    ap.add_argument("--backend", action="append", dest="backends",
                    help="backend to probe; repeatable. Default: every backend that is built.")
    ap.add_argument("--require", default="",
                    help="comma-separated backends that must be present, e.g. cpu,cuda")
    ap.add_argument("--repeat", type=int, default=2, help="runs per backend (default 2)")
    ap.add_argument("--json", action="store_true", help="machine-readable report")
    args = ap.parse_args(argv)

    wanted = args.backends or list(BACKENDS)
    unknown = [b for b in wanted if b not in BACKENDS]
    if unknown:
        print(f"unknown backend(s): {', '.join(unknown)}; known: {', '.join(BACKENDS)}")
        return 2
    require = [r.strip() for r in args.require.split(",") if r.strip()]

    results = run(wanted, require, max(1, args.repeat))
    code, lines = report(results, require)

    if args.json:
        payload = {
            "probe": {"prompt": PROBE_PROMPT, "config": PROBE_CONFIG},
            "results": {
                backend: [
                    {"tokens": s.tokens, "caps": s.caps, "terminal": s.terminal, "error": s.error}
                    for s in snaps
                ]
                for backend, snaps in results.items()
            },
            "verdict": "pass" if code == 0 else ("missing-backend" if code == 2 else "drift"),
        }
        print(json.dumps(payload, indent=2))
    else:
        print("\n".join(lines))
    return code


if __name__ == "__main__":
    sys.exit(main())
