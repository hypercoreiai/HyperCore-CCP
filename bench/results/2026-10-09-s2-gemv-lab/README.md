# 2026-10-09 — S2 GEMV lab (attempted, not run)

`s2_gemv_lab.cu` is a self-contained probe of the S2 GEMV written to the engine's conventions: the same
decode as `src/kernels/cuda/s2_gemv.cu`, a CPU reference in the same summation order, and three variants
side by side —

| | orientation | what it tests |
|---|---|---|
| A | one thread per output row | the P2 baseline, as shipped |
| B | row split across a block, warp shuffle + shared reduction | the orientation the header describes |
| C | B, with 16 codes unpacked from one `uint32` | whether fewer bit-extract instructions help |

Build:

```
nvcc -O3 -std=c++17 -arch=sm_89 s2_gemv_lab.cu -o /tmp/lab && /tmp/lab
```

**Result: no numbers.** The engine was resident on the device while this was attempted —
`nvidia-smi` reported 24,074 of 24,564 MiB in use and 93% utilisation on the RTX 4090, and a 4 KB
`cudaMalloc` from a second process returned `out of memory`. The program now says so instead of hanging:

```
no device
```

The lab is kept because the code is the part worth keeping; the measurement needs the GPU. Park the
engine (`stop` the model, or run this on a machine with headroom) and re-run it — the parity check against
the CPU reference is already in the file and prints the max relative error before any timing is believed.

Nothing here has been adopted. Until it is measured on a quiet machine it is a hypothesis, and this
repository's rule is that a hypothesis does not get to be a kernel.
