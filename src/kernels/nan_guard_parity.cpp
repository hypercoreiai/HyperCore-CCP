// src/kernels/nan_guard_parity.cpp - #879, the NaN guard: logits_nonfinite_rows against a host scan.
//
// The guard must (a) flag exactly the rows that hold a NaN or an infinity, (b) flag nothing else, and (c) leave the
// logits it reads untouched.  Every (row, block) cell is compared, not just the row, so a slice that is missed shows
// up as a disagreement in one of the 16 words.
//
//   cmake -S . -B build -DHYPERCORE_ENABLE_CUDA=ON && cmake --build build --target nan_guard_parity
//   ./build/nan_guard_parity            (or --selftest, the same thing, for ctest)
#include <cuda_runtime.h>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <random>
#include <string>
#include <vector>

#include "hypercore/kernels/verify_kernels.hpp"

using hypercore::kernels::kNonfiniteBlocks;
using hypercore::kernels::kVerifyMaxT;

static bool host_flags(const std::vector<float>& logits, int rows, int n, std::vector<uint32_t>& out) {
    out.assign((size_t) rows * kNonfiniteBlocks, 0u);
    const int per_block = (n + kNonfiniteBlocks - 1) / kNonfiniteBlocks;
    for (int r = 0; r < rows; ++r)
        for (int b = 0; b < kNonfiniteBlocks; ++b) {
            int lo = b * per_block, hi = std::min(n, lo + per_block);
            for (int v = lo; v < hi; ++v)
                if (!std::isfinite(logits[(size_t) r * n + v])) { out[(size_t) r * kNonfiniteBlocks + b] = 1u; break; }
        }
    return true;
}

// One case: rows x n logits, `plants` = (row, column) pairs set to a non-finite value.  Returns 0 on a match.
static int run_case(int rows, int n, const std::vector<std::pair<int, int>>& plants, bool bench) {
    if (rows <= 0 || rows > kVerifyMaxT || n <= 0) return 0;
    std::vector<float> host((size_t) rows * n, 0.0f);
    std::mt19937 rng((uint32_t) (rows * 1000 + n));
    std::uniform_real_distribution<float> u(-1e3f, 1e3f);
    for (float& x : host) x = u(rng);
    for (auto [r, c] : plants) host[(size_t) r * n + c] = (c % 2) ? std::nanf("") : INFINITY;

    float* dev = nullptr;
    uint32_t* dev_flags = nullptr;
    if (cudaMalloc(&dev, host.size() * sizeof(float)) != cudaSuccess) { std::printf("FAIL cudaMalloc logits\n"); return 1; }
    if (cudaMalloc(&dev_flags, (size_t) rows * kNonfiniteBlocks * sizeof(uint32_t)) != cudaSuccess) {
        std::printf("FAIL cudaMalloc flags\n"); cudaFree(dev); return 1;
    }
    if (cudaMemcpy(dev, host.data(), host.size() * sizeof(float), cudaMemcpyHostToDevice) != cudaSuccess) {
        std::printf("FAIL cudaMemcpy logits\n"); cudaFree(dev); cudaFree(dev_flags); return 1;
    }
    // the flags start dirty on purpose: the kernel writes every cell it is asked about
    std::vector<uint32_t> dirty((size_t) rows * kNonfiniteBlocks, 0xDEADu);
    if (cudaMemcpy(dev_flags, dirty.data(), dirty.size() * sizeof(uint32_t), cudaMemcpyHostToDevice) != cudaSuccess) {
        std::printf("FAIL cudaMemcpy flags\n"); cudaFree(dev); cudaFree(dev_flags); return 1;
    }

    hypercore::kernels::logits_nonfinite_rows(dev, rows, n, dev_flags, nullptr);
    if (cudaGetLastError() != cudaSuccess) {
        std::printf("FAIL %s: %s\n", "logits_nonfinite_rows", cudaGetErrorString(cudaGetLastError()));
        cudaFree(dev); cudaFree(dev_flags); return 1;
    }
    std::vector<uint32_t> got((size_t) rows * kNonfiniteBlocks, 0u);
    if (cudaMemcpy(got.data(), dev_flags, got.size() * sizeof(uint32_t), cudaMemcpyDeviceToHost) != cudaSuccess) {
        std::printf("FAIL cudaMemcpy flags back\n"); cudaFree(dev); cudaFree(dev_flags); return 1;
    }
    std::vector<float> back(host.size(), 0.0f);
    if (cudaMemcpy(back.data(), dev, back.size() * sizeof(float), cudaMemcpyDeviceToHost) != cudaSuccess) {
        std::printf("FAIL cudaMemcpy logits back\n"); cudaFree(dev); cudaFree(dev_flags); return 1;
    }

    std::vector<uint32_t> want;
    host_flags(host, rows, n, want);

    int bad = 0;
    for (size_t i = 0; i < want.size(); ++i) bad += (got[i] != want[i]);
    // the guard reads, it never writes: the logits come back bit for bit
    size_t changed = 0;
    for (size_t i = 0; i < host.size(); ++i) changed += (std::abs(back[i] - host[i]) > 1e-3f);

    if (bad || changed) {
        std::printf("FAIL rows=%d n=%d plants=%zu: %d flag cells differ, %zu logits changed\n",
                   rows, n, plants.size(), bad, changed);
        return 1;
    }
    if (bench) {
        const int iters = 200;
        cudaEvent_t e0, e1;
        cudaEventCreate(&e0); cudaEventCreate(&e1);
        cudaEventRecord(e0);
        for (int i = 0; i < iters; ++i) hypercore::kernels::logits_nonfinite_rows(dev, rows, n, dev_flags, nullptr);
        cudaEventRecord(e1);
        cudaEventSynchronize(e1);
        float ms = 0.0f; cudaEventElapsedTime(&ms, e0, e1);
        cudaEventDestroy(e0); cudaEventDestroy(e1);
        std::printf("bench rows=%d n=%d: %.1f us a window (%d iterations)\n", rows, n, ms * 1000.0 / iters, iters);
    }
    std::printf("ok rows=%d n=%d plants=%zu\n", rows, n, plants.size());
    return 0;
}

int main(int argc, char** argv) {
    const bool bench = argc > 1 && std::string(argv[1]) == "--bench";
    int fails = 0;

    // every row clean
    fails += run_case(1, 1024, {}, bench);
    fails += run_case(kVerifyMaxT, 151936, {}, bench);

    // one non-finite value in a row: only that row's cells are set
    fails += run_case(4, 151936, {{2, 0}}, bench);
    fails += run_case(4, 151936, {{2, 151935}}, bench);          // the last column, the last block
    fails += run_case(3, 1000, {{0, 62}, {2, 999}}, bench);      // n not a multiple of the block size
    fails += run_case(8, 16, {{7, 15}}, bench);                  // n smaller than kNonfiniteBlocks
    fails += run_case(8, 151936, {{0, 1}, {1, 2}, {2, 3}, {3, 4}, {4, 5}, {5, 6}, {6, 7}, {7, 8}}, bench);

    // a value that is large but finite is not a flag
    std::vector<std::pair<int, int>> none;
    fails += run_case(2, 4096, none, false);

    if (fails == 0) std::printf("nan_guard_parity: all cases match the host scan\n");
    else std::printf("nan_guard_parity: %d case(s) failed\n", fails);
    return fails ? 1 : 0;
}
