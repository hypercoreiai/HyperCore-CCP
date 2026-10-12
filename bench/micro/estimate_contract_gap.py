#!/usr/bin/env python3
"""Host estimate of the GPU-vs-capture gap the ple_parity `result` bound (1e-2) has to absorb.

The CUDA block reads the pack's Q2_0 key codes with Q8_0-quantized activations and the
BF16-truncated value weights; the capture holds the F32 weights and unrounded activations.
This script reproduces that contract on the host and reports how far the final `result`
moves, so the tolerance in src/kernels/ple_parity.cpp can be checked without a GPU.
"""
from __future__ import annotations

import numpy as np
from pathlib import Path

N, HC, NT, KERN, DIL, HIST, EPS = 2560, 4, 4, 4, 3, 9, 1e-6
HCD = HC * N
ROOT = Path(__file__).resolve().parent.parent.parent


def read_pack(offset: int, nbytes: int) -> bytes:
    with open(ROOT / "pack/full/dense.bin", "rb") as f:
        f.seek(offset)
        return f.read(nbytes)


def bf16(x: np.ndarray) -> np.ndarray:
    """Round to bf16 the way the pack does: keep the top 16 bits of the float32 pattern."""
    u = np.asarray(x, dtype=np.float32).view(np.uint32)
    return ((u + 0x8000) & 0xFFFF0000).view(np.float32)


def q8_0(x: np.ndarray) -> np.ndarray:
    """The activation contract: scale = max|x|/127, round away from zero, clamp."""
    amax = float(np.abs(x).max())
    if amax == 0.0:
        return np.zeros_like(x)
    scale = amax / 127.0
    q = np.trunc(x / scale + np.copysign(0.5, x))
    return np.clip(q, -127, 127) * scale


def grouped_norm(x: np.ndarray, w: np.ndarray) -> np.ndarray:
    y = np.empty_like(x)
    for c in range(HC):
        s = x[c * N:(c + 1) * N]
        mean = float(np.dot(s.astype(np.float64), s.astype(np.float64)) / N)
        scale = 1.0 / np.sqrt(mean + EPS)
        y[c * N:(c + 1) * N] = s * scale * w[c * N:(c + 1) * N]
    return y


def rel(x: np.ndarray, y: np.ndarray) -> float:
    denom = float(np.abs(y).sum())
    return float(np.abs(x - y).sum() / denom) if denom > 0 else float("inf")


def main() -> int:
    body = np.fromfile(ROOT / "bench/micro/ple_in.bin", dtype="<f4")[6:]
    sizes = [NT * N, NT * HCD, HCD * N, N * N, HCD, HCD, HCD, HCD * KERN, HIST * HCD]
    pos, fields = 0, []
    for n in sizes:
        fields.append(body[pos:pos + n])
        pos += n
    emb, hidden, w_key, w_value, w_nk, w_nq, w_nc, w_conv, hist = fields
    out = np.fromfile(ROOT / "bench/micro/ple_out.bin", dtype="<f4")[3:]
    osizes = [NT * HCD, NT * N, NT * HC, NT * HCD, NT * HCD, NT * HCD, NT * HCD]
    pos, orows = 0, []
    for n in osizes:
        orows.append(out[pos:pos + n])
        pos += n
    _, _, _, _, normalized_ref, conv_ref, result_ref = orows

    codes = ((np.frombuffer(read_pack(1017723776, 6553600), dtype=np.uint8).astype(np.int64)[:, None]
             >> np.array([0, 2, 4, 6])) & 3).ravel()
    scales = np.frombuffer(read_pack(1024277376, 819200), dtype="<f2").astype(np.float64)
    key_w = ((codes - 1) * scales[np.arange(codes.size) // 64]).astype(np.float32).reshape(HCD, N)
    value_w = bf16(w_value).reshape(N, N)
    w_value = w_value.reshape(N, N)

    hist_ref = hist.copy()
    cols = np.arange(HCD)
    worst_result = 0.0
    for t in range(NT):
        e_full = emb[t * N:(t + 1) * N]
        e = e_full.astype(np.float64)
        qe = q8_0(e_full).astype(np.float64)
        k_exact = (key_w.astype(np.float64) @ e).astype(np.float32)
        k_contract = (key_w.astype(np.float64) @ qe).astype(np.float32)
        v_exact = (w_value.astype(np.float64) @ e).astype(np.float32)
        v_contract = (value_w.astype(np.float64) @ bf16(e).astype(np.float64)).astype(np.float32)
        for name, a, b in (("key", k_contract, k_exact), ("value", v_contract, v_exact)):
            print(f"token {t} {name}: contract vs capture rel {rel(a, b):.3e}")
        nk = grouped_norm(k_contract, w_nk)
        nq = grouped_norm(hidden[t * HCD:(t + 1) * HCD], w_nq)
        gate = np.zeros(HC, dtype=np.float32)
        for c in range(HC):
            s = float(np.dot(nk[c * N:(c + 1) * N].astype(np.float64),
                            nq[c * N:(c + 1) * N].astype(np.float64))) / np.sqrt(float(N))
            mag = np.sqrt(max(abs(s), 1e-6))
            sgn = 1.0 if s > 0 else (-1.0 if s < 0 else 0.0)
            gate[c] = np.float32(1.0 / (1.0 + np.exp(-sgn * mag)))
        g = v_contract[np.arange(HCD) % N] * gate[np.arange(HCD) // N]
        n = grouped_norm(g, w_nc)
        acc = np.zeros(HCD, dtype=np.float64)
        for kk in range(KERN):
            row = HIST - (KERN - 1 - kk) * DIL
            src = n.astype(np.float64) if row == HIST else hist_ref[row + HIST * cols].astype(np.float64)
            acc += w_conv[kk + KERN * cols].astype(np.float64) * src
        cv = (acc / (1.0 + np.exp(-acc))).astype(np.float32)
        res = (hidden[t * HCD:(t + 1) * HCD].astype(np.float64) + g.astype(np.float64) + cv.astype(np.float64)).astype(np.float32)
        ref_res = result_ref[t * HCD:(t + 1) * HCD]
        r = rel(res, ref_res)
        worst_result = max(worst_result, r)
        print(f"token {t} result: contract vs capture rel {r:.3e} (mean |result| {float(np.abs(ref_res).mean()):.4f})")
        h = hist_ref.reshape(HCD, HIST)
        h[:, :HIST - 1] = np.copy(h[:, 1:])
        h[:, HIST - 1] = n
    print(f"worst result rel {worst_result:.3e} against the 1e-2 bound")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
