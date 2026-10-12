#!/usr/bin/env python3
"""Independent, GPU-free check that the PLE fixture carries a signal.

Mirrors the three non-CUDA assertions in section C of src/kernels/ple_parity.cpp:
the pack-vs-capture weight agreement, the gated-vs-normalized trap, and the reversed
conv tap-order trap.  Run: python3 bench/micro/check_fixture_signal.py
"""
from __future__ import annotations

import numpy as np
from pathlib import Path

N, HC, NT, KERN, DIL, HIST = 2560, 4, 4, 4, 3, 9
HCD = HC * N
ROOT = Path(__file__).resolve().parent.parent.parent


def rel(x: np.ndarray, y: np.ndarray) -> float:
    denom = float(np.abs(y).sum())
    return float(np.abs(x - y).sum() / denom) if denom > 0 else float("inf")


def read_pack(offset: int, nbytes: int) -> bytes:
    with open(ROOT / "pack/full/dense.bin", "rb") as f:
        f.seek(offset)
        return f.read(nbytes)


def main() -> int:
    raw_in = np.fromfile(ROOT / "bench/micro/ple_in.bin", dtype="<f4")
    raw_out = np.fromfile(ROOT / "bench/micro/ple_out.bin", dtype="<f4")
    body = raw_in[6:]
    sizes = [NT * N, NT * HCD, HCD * N, N * N, HCD, HCD, HCD, HCD * KERN, HIST * HCD]
    if sum(sizes) != body.size:
        raise SystemExit(f"ple_in.bin payload is {body.size} floats, expected {sum(sizes)}")
    pos, fields = 0, []
    for n in sizes:
        fields.append(body[pos:pos + n])
        pos += n
    emb, hidden, w_key, w_value, w_nk, w_nq, w_nc, w_conv, hist = fields

    out = raw_out[3:]
    osizes = [NT * HCD, NT * N, NT * HC, NT * HCD, NT * HCD, NT * HCD, NT * HCD]
    if sum(osizes) != out.size:
        raise SystemExit(f"ple_out.bin payload is {out.size} floats, expected {sum(osizes)}")
    pos, orows = 0, []
    for n in osizes:
        orows.append(out[pos:pos + n])
        pos += n
    key, value, gate, gated, normalized, conv_out, result = orows

    codes = ((np.frombuffer(read_pack(1017723776, 6553600), dtype=np.uint8).astype(np.int64)[:, None]
             >> np.array([0, 2, 4, 6])) & 3).ravel()
    scales = np.frombuffer(read_pack(1024277376, 819200), dtype="<f2").astype(np.float64)
    decoded = ((codes - 1) * scales[np.arange(codes.size) // 64]).astype(np.float32)

    cols = np.arange(HCD)
    reversed_taps = np.zeros(HCD * NT, dtype=np.float32)
    for t in range(NT):
        norm_t = normalized[t * HCD:(t + 1) * HCD]
        acc = np.zeros(HCD, dtype=np.float64)
        for kk in range(KERN):
            row = HIST - (KERN - 1 - kk) * DIL
            src = norm_t.astype(np.float64) if row == HIST else hist[row + HIST * cols].astype(np.float64)
            acc += w_conv[kk + KERN * cols].astype(np.float64) * src
        reversed_taps[t * HCD:(t + 1) * HCD] = (acc / (1.0 + np.exp(-acc))).astype(np.float32)

    print(f"pack ple_key row 0 vs capture w_key row 0: worst |d| {float(np.abs(decoded[:N] - w_key[:N]).max()):.3e}")
    print(f"normalized vs gated apart: {rel(normalized, gated) * 100:.2f}%")
    print(f"reversed conv tap order vs capture conv_out: {rel(conv_out, reversed_taps) * 100:.2f}% apart")
    print(f"mean |normalized| {float(np.abs(normalized).mean()):.4f}, mean |result| {float(np.abs(result).mean()):.4f}")
    print(f"result == hidden + gated + conv_out: rel {rel(result, hidden + gated + conv_out):.3e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
