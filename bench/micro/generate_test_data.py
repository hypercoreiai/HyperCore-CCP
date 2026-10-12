#!/usr/bin/env python3
"""Generate the PLE parity capture: bench/micro/ple_in.bin and bench/micro/ple_out.bin.

Why this exists: `src/kernels/ple_parity.cpp` compares the CUDA PLE block against a
captured ggml graph, and every oracle in section C (the pack-vs-capture weight check, the
"normalized vs gated" trap, the conv tap-order trap, the host f32 reference) is only
meaningful if the capture carries a signal.  A zero-filled fixture makes all of them
compare 0 against 0, which is the failure mode the test exists to catch.

Every weight is read from the pack the GPU kernel reads (pack/full/dense.bin), so the
capture and the kernel describe the SAME tensor.  The activations are a seeded,
reproducible signal with the statistics a real PLE layer has: unit-rms embeddings and
hidden states, and a history whose rows look like the `normalized` rows the block writes
back into it.

Run from the engine root:  python3 bench/micro/generate_test_data.py
"""
from __future__ import annotations

import struct
import sys
from pathlib import Path

import numpy as np

# Engine geometry, identical to hypercore::kernels::ple in include/hypercore/kernels/ple.hpp.
N_EMBD: int = 2560
HC: int = 4
NT: int = 4
KERN: int = 4
DIL: int = 3
EPS: float = 1e-6
HCD: int = HC * N_EMBD
HIST: int = (KERN - 1) * DIL
SEED: int = 20261011

# The two quantized regions, matching hypercore::kernels::ple_oracle in
# src/kernels/ple_oracle_vectors.inc.  Quantized tensors are not addressable by name in
# the pack index, so these come from the same constants the C++ test uses.
KEY_CODES_OFFSET: int = 1017723776
KEY_CODES_BYTES: int = 6553600
KEY_SCALES_OFFSET: int = 1024277376
KEY_SCALES_BYTES: int = 819200
VALUE_OFFSET: int = 1025219456
VALUE_BYTES: int = 26214400

FLOAT_TENSORS: dict[str, str] = {
    "blk.1.ple_conv1d.weight": "w_conv",
    "blk.1.ple_norm_conv.weight": "w_nc",
    "blk.1.ple_norm_key.weight": "w_nk",
    "blk.1.ple_norm_query.weight": "w_nq",
}


def read_at(path: Path, offset: int, nbytes: int) -> bytes:
    with open(path, "rb") as f:
        f.seek(offset)
        blob = f.read(nbytes)
    if len(blob) != nbytes:
        raise SystemExit(f"{path}: wanted {nbytes} bytes at {offset}, got {len(blob)}")
    return blob


def float_tensor_offsets(index: Path) -> dict[str, tuple[int, int, int]]:
    """name -> (kind, dense_offset, dense_bytes) for the F32/F16 tensors in the pack index."""
    want: dict[str, tuple[int, int, int]] = {}
    with open(index, "r") as f:
        for line in f:
            if line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 5 or parts[0] not in FLOAT_TENSORS:
                continue
            want[parts[0]] = (int(parts[2]), int(parts[3]), int(parts[4]))
    missing = sorted(set(FLOAT_TENSORS) - set(want))
    if missing:
        raise SystemExit(f"pack index has no record for {', '.join(missing)}")
    return want


def dequant_q2_0(codes: bytes, scales: np.ndarray) -> np.ndarray:
    """ggml's Q2_0 rule: value = (code - 1) * scale[block], block = element // 64."""
    # Same unpacking as the C++ oracle: element d of byte b is (b >> (2*(d%4))) & 3.
    b = np.frombuffer(codes, dtype=np.uint8).astype(np.int64)
    codes_int = ((b[:, None] >> np.array([0, 2, 4, 6])) & 3).ravel().astype(np.int64)
    blocks = np.arange(codes_int.size) // 64
    return ((codes_int - 1).astype(np.float64) * scales[blocks].astype(np.float64)).astype(np.float32)


def grouped_norm(x: np.ndarray, w: np.ndarray) -> np.ndarray:
    """Per-stream rms norm, exactly as the block's `gnorm` does it."""
    y = np.empty_like(x, dtype=np.float32)
    for c in range(HC):
        s = x[c * N_EMBD:(c + 1) * N_EMBD].astype(np.float64)
        mean = float(np.dot(s, s) / N_EMBD)
        scale = 1.0 / np.sqrt(mean + EPS)
        y[c * N_EMBD:(c + 1) * N_EMBD] = (
            x[c * N_EMBD:(c + 1) * N_EMBD] * scale * w[c * N_EMBD:(c + 1) * N_EMBD]
        ).astype(np.float32)
    return y


def main() -> int:
    root = Path(__file__).resolve().parent.parent.parent
    pack = root / "pack" / "full"
    dense = pack / "dense.bin"
    if not dense.exists():
        raise SystemExit("pack/full/dense.bin is required (it is a hard link into the pack directory)")
    index = dense.resolve().parent / "index.txt"
    if not index.exists():
        raise SystemExit(f"pack index not found next to dense.bin: {index}")
    offs = float_tensor_offsets(index)

    w_key = dequant_q2_0(
        read_at(dense, KEY_CODES_OFFSET, KEY_CODES_BYTES),
        np.frombuffer(read_at(dense, KEY_SCALES_OFFSET, KEY_SCALES_BYTES), dtype="<f2"),
    ).reshape(HCD, N_EMBD)

    # ple_value is stored in the pack as F32; the kernel truncates it to BF16 at load time
    # (see the `value_bf16` block in ple_parity.cpp).  The capture keeps the F32, so the gap
    # between the two IS the BF16 contract the test describes.
    raw = np.frombuffer(read_at(dense, VALUE_OFFSET, VALUE_BYTES), dtype="<u4")
    w_value = raw.view(np.float32).reshape(N_EMBD, N_EMBD)

    def f32(name: str) -> np.ndarray:
        kind, off, nbytes = offs[name]
        dtype = "<f4" if kind == 2 else "<f2"
        return np.frombuffer(read_at(dense, off, nbytes), dtype=dtype).astype(np.float32)

    w_conv = f32("blk.1.ple_conv1d.weight")      # ggml order: flat = k + kern*c
    w_nc = f32("blk.1.ple_norm_conv.weight")
    w_nk = f32("blk.1.ple_norm_key.weight")
    w_nq = f32("blk.1.ple_norm_query.weight")

    rng = np.random.default_rng(SEED)
    emb = rng.standard_normal((NT, N_EMBD), dtype=np.float32)
    hidden = rng.standard_normal((NT, HCD), dtype=np.float32)
    # Each history row is a `normalized`-shaped vector; the capture stores it ggml-native,
    # ne=(hist, hc_dim), so flat = row + hist*channel.
    rows = np.stack([grouped_norm(rng.standard_normal(HCD, dtype=np.float32), w_nc) for _ in range(HIST)])
    hist_flat = np.ascontiguousarray(rows.T).reshape(-1).astype(np.float32)

    key = np.zeros((NT, HCD), dtype=np.float32)
    value = np.zeros((NT, N_EMBD), dtype=np.float32)
    gate = np.zeros((NT, HC), dtype=np.float32)
    gated = np.zeros((NT, HCD), dtype=np.float32)
    normalized = np.zeros((NT, HCD), dtype=np.float32)
    conv_out = np.zeros((NT, HCD), dtype=np.float32)
    result = np.zeros((NT, HCD), dtype=np.float32)

    hist_ref = hist_flat.copy()
    for t in range(NT):
        e = emb[t].astype(np.float64)
        k = grouped_norm((w_key.astype(np.float64) @ e).astype(np.float32), w_nk)
        q = grouped_norm(hidden[t], w_nq)
        v = (w_value.astype(np.float64) @ e).astype(np.float32)
        for c in range(HC):
            a = float(np.dot(k[c * N_EMBD:(c + 1) * N_EMBD].astype(np.float64),
                            q[c * N_EMBD:(c + 1) * N_EMBD].astype(np.float64)))
            s = a / np.sqrt(float(N_EMBD))
            mag = np.sqrt(max(abs(s), 1e-6))
            sgn = 1.0 if s > 0 else (-1.0 if s < 0 else 0.0)
            gate[t, c] = np.float32(1.0 / (1.0 + np.exp(-sgn * mag)))
        g = v[np.arange(HCD) % N_EMBD] * gate[t][np.arange(HCD) // N_EMBD]
        n = grouped_norm(g, w_nc)
        cv = np.zeros(HCD, dtype=np.float32)
        cols = np.arange(HCD)
        acc = np.zeros(HCD, dtype=np.float64)
        for kk in range(KERN):
            row = HIST - (KERN - 1 - kk) * DIL
            src = n.astype(np.float64) if row == HIST else hist_ref[row + HIST * cols].astype(np.float64)
            acc += w_conv[kk + KERN * cols].astype(np.float64) * src
        cv = (acc / (1.0 + np.exp(-acc))).astype(np.float32)
        key[t], value[t], gated[t], normalized[t], conv_out[t] = k, v, g, n, cv
        result[t] = (hidden[t].astype(np.float64) + g.astype(np.float64) + cv.astype(np.float64)).astype(np.float32)
        h = hist_ref.reshape(HCD, HIST)
        h[:, :HIST - 1] = np.copy(h[:, 1:])
        h[:, HIST - 1] = n

    out_dir = root / "bench" / "micro"
    in_path, out_path = out_dir / "ple_in.bin", out_dir / "ple_out.bin"
    with open(in_path, "wb") as f:
        f.write(struct.pack("5i", N_EMBD, HC, NT, KERN, DIL))
        f.write(struct.pack("f", EPS))
        for arr in (emb, hidden, w_key, w_value, w_nk, w_nq, w_nc, w_conv, hist_flat):
            f.write(np.asarray(arr, dtype=np.float32).tobytes())
    with open(out_path, "wb") as f:
        f.write(struct.pack("3i", N_EMBD, HCD, NT))
        for arr in (key, value, gate, gated, normalized, conv_out, result):
            f.write(np.asarray(arr, dtype=np.float32).tobytes())

    print(f"wrote {in_path} ({in_path.stat().st_size} B) and {out_path} ({out_path.stat().st_size} B)")
    print(f"mean |normalized| {float(np.abs(normalized).mean()):.4f}, "
          f"mean |result| {float(np.abs(result).mean()):.4f}, "
          f"mean |conv_out| {float(np.abs(conv_out).mean()):.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
