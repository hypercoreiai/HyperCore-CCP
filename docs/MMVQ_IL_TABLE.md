# The interleaved small-batch matvec (HYPERCORE_MMVQ_IL): how to measure a table for your card

The decode and verify windows run their dense projections (2 to 4 tokens at a time) through `native_mmvq_il`, which reads an
interleaved copy of the q8_1 activations. Every choice it makes gives the same bits as the plain kernels
(`HYPERCORE_MMVQ_IL=0` turns the whole path off); only the speed differs. How many matrix rows one warp takes
(1, 2 or 4, or 0 = use the plain kernel) is a table in `src/kernels/cuda/native_mmvq.cu`, indexed by the
quantisation type (IQ4_XS, Q4_K, Q5_K, Q6_K, and Q3_K where measured), the token count (2-4) and the matrix's row count
(five classes).

Which table a card gets:

| card | table |
|---|---|
| sm_86 (Ampere consumer) | its own table `kIlRows_86`, measured on an RTX A4000 with the engine's real shapes (Q3_K included) |
| sm_89 (Ada) | its own table `kIlRows_89`, measured on an RTX 4090 here with `mmvq_il_parity --bench --emit-table`, twice; where the two runs disagreed the lower row count was kept |
| sm_120 (Blackwell consumer) and every other sm_80+ card | `kIlRowsShared`, read off an RTX 3060 and an RTX 5070 together (a cell is non-zero only if the worse of the two cards still gains 3%) |
| sm_70 (Volta) | `kIlRows_70`, measured on a V100-SXM2-32GB. Off unless `HYPERCORE_SM70_TABLE=1`. |
| sm_60 (Pascal) | `kIlRows_60`, measured on a Tesla P100-PCIE-16GB. On unless `HYPERCORE_SM60_TABLE=0`. |
| sm_75 and any other card | the path is off; the plain kernels run |

## Measuring a card that has no table yet

1. Build with tests: `cmake -S . -B build -DHYPERCORE_BUILD_TESTS=ON` and `cmake --build build --target mmvq_il_parity`.
2. Close everything else on the GPU, then run `build/mmvq_il_parity --bench --emit-table` (a few minutes).
   It first checks bit-for-bit parity of every shape and every rows choice (it must end with `mmvq_il_parity: OK`),
   prints a `BENCH` line per shape and token count, and last a ready-to-paste block, one line per type.
3. Post the whole output on the issue. A maintainer pastes the block as `kIlRows_89[]` and adds
   `{89, kIlRows_89, sizeof(kIlRows_89) / sizeof(IlRows)}` to `kIlArch`.
4. To try a table without rebuilding, set `HYPERCORE_MMVQ_IL_ROWS="type:ncols:r0,r1,r2,r3,r4;..."`, for example
   `HYPERCORE_MMVQ_IL_ROWS="23:3:0,0,2,4,4;12:2:0,1,1,1,1"` (the five numbers are the row classes below 2048, 4096, 8192,
   12288 and above; each is 0, 1, 2 or 4). Then A/B the decode: same flags, `HYPERCORE_MMVQ_IL_ROWS` set or unset, 10
   interleaved pairs, medians.

The emit rule: per cell, the fastest rows count if it takes at least 3% off the plain kernel's time, else 0; shapes of one
class that disagree give 0; a class with no measured shape copies its neighbour below.
