// bench/results/kernel_lab_s2_gemv.cu - a self-contained probe of the S2 GEMV, written to the engine's
// own conventions so the numbers are comparable to Memory/LEDGER L1: same decode, same layout, a CPU
// reference in the same summation order, and three variants measured in one process.
//
//   A  one thread per output row                       (src/kernels/cuda/s2_gemv.cu, the P2 baseline)
//   B  row split across a block, shared reduction       (the orientation the header describes)
//   C  B, with four codes unpacked from one uint32     (the lever this lab is about)
//
// Build: nvcc -O3 -std=c++17 -arch=sm_89 bench/results/kernel_lab_s2_gemv.cu -o /tmp/lab
//
// NOT part of the build; it is a measurement, and it is checked against the reference before it is
// believed. Being faster is never a reason to be trusted.
#include <cuda_fp16.h>
#include <cuda_runtime.h>

#include <cstdio>
#include <cstdlib>
#include <cstdint>
#include <vector>
#include <chrono>
#include <cmath>

namespace lab {

constexpr int QK = 64;

// ---------------------------------------------------------------- A: the baseline
__global__ void gemv_a(const uint16_t* __restrict__ x, const uint8_t* __restrict__ codes,
                       const float* __restrict__ scales, float* __restrict__ y, long long n_in,
                       long long n_out) {
    const long long o = (long long) blockIdx.x * blockDim.x + threadIdx.x;
    if (o >= n_out) return;
    const long long nb = n_in / QK;
    const uint8_t* c = codes + o * nb * (QK / 4);
    const float* s = scales + o * nb;
    float acc = 0.0f;
    for (long long b = 0; b < nb; ++b) {
        const float d = s[b];
        const uint8_t* cb = c + b * (QK / 4);
        const uint16_t* xb = x + b * QK;
        for (int j = 0; j < QK; ++j) {
            const int code = (cb[j >> 2] >> ((j & 3) * 2)) & 0x03;
            acc += (float) (code - 1) * d * __half2float(__ushort_as_half(xb[j]));
        }
    }
    y[o] = acc;
}

// ---------------------------------------------------------------- B: row split across the block
__global__ void gemv_b(const uint16_t* __restrict__ x, const uint8_t* __restrict__ codes,
                       const float* __restrict__ scales, float* __restrict__ y, long long n_in,
                       long long n_out, int tpr) {
    const long long o = blockIdx.x;
    const long long nb = n_in / QK;
    const uint8_t* c = codes + o * nb * (QK / 4);
    const float* s = scales + o * nb;

    float acc = 0.0f;
    // Each thread takes every tpr-th group: the loads of one row are spread over the block.
    for (long long b = threadIdx.x; b < nb; b += tpr) {
        const float d = s[b];
        const uint8_t* cb = c + b * (QK / 4);
        const uint16_t* xb = x + b * QK;
        for (int j = 0; j < QK; ++j) {
            const int code = (cb[j >> 2] >> ((j & 3) * 2)) & 0x03;
            acc += (float) (code - 1) * d * __half2float(__ushort_as_half(xb[j]));
        }
    }
    // Warp shuffle first, then one shared slot per warp.
    for (int off = 16; off > 0; off >>= 1) acc += __shfl_down_sync(0xffffffffu, acc, off);
    __shared__ float part[32];
    const int lane = threadIdx.x & 31, warp = threadIdx.x >> 5;
    if (lane == 0) part[warp] = acc;
    __syncthreads();
    if (threadIdx.x == 0) {
        float total = 0.0f;
        for (int w = 0; w < (tpr + 31) / 32; ++w) total += part[w];
        y[o] = total;
    }
}

// ---------------------------------------------------------------- C: B, four codes per uint32 read
__global__ void gemv_c(const uint16_t* __restrict__ x, const uint8_t* __restrict__ codes,
                       const float* __restrict__ scales, float* __restrict__ y, long long n_in,
                       long long n_out, int tpr) {
    const long long o = blockIdx.x;
    const long long nb = n_in / QK;
    const uint8_t* c = codes + o * nb * (QK / 4);
    const float* s = scales + o * nb;

    float acc = 0.0f;
    for (long long b = threadIdx.x; b < nb; b += tpr) {
        const float d = s[b];
        const uint32_t* cb = (const uint32_t*) (c + b * (QK / 4));   // 16 bytes = 4 uint32, aligned
        const uint16_t* xb = x + b * QK;
        for (int q = 0; q < 4; ++q) {
            const uint32_t w = cb[q];                  // 32 bits = 16 codes
            const __half2* xa = (const __half2*) (xb + q * 16);
            for (int k = 0; k < 16; ++k) {
                // two codes out of one register, two activations out of one __half2
                const float a0 = __half2float(__low2half(xa[k >> 1]));
                const float a1 = __half2float(__high2half(xa[k >> 1]));
                const int c0 = (w >> (2 * k)) & 3, c1 = (w >> (2 * k + 1)) & 3;
                acc += (float) (c0 - 1) * d * a0;
                acc += (float) (c1 - 1) * d * a1;
            }
        }
    }
    for (int off = 16; off > 0; off >>= 1) acc += __shfl_down_sync(0xffffffffu, acc, off);
    __shared__ float part[32];
    const int lane = threadIdx.x & 31, warp = threadIdx.x >> 5;
    if (lane == 0) part[warp] = acc;
    __syncthreads();
    if (threadIdx.x == 0) {
        float total = 0.0f;
        for (int w = 0; w < (tpr + 31) / 32; ++w) total += part[w];
        y[o] = total;
    }
}

// ---------------------------------------------------------------- CPU reference, same order
double reference(const std::vector<uint16_t>& x, const std::vector<uint8_t>& codes,
                 const std::vector<float>& scales, long long n_in, long long n_out, long long o) {
    const long long nb = n_in / QK;
    double acc = 0.0;
    for (long long b = 0; b < nb; ++b) {
        const float d = scales[o * nb + b];
        const uint8_t* cb = &codes[o * nb * (QK / 4) + b * (QK / 4)];
        for (int j = 0; j < QK; ++j) {
            const int code = (cb[j >> 2] >> ((j & 3) * 2)) & 0x03;
            acc += (double) (code - 1) * (double) d * (double) __half2float(__ushort_as_half(x[b * QK + j]));
        }
    }
    return acc;
}

double bench(void (*run)(const uint16_t*, const uint8_t*, const float*, float*, long long, long long, int),
             const std::vector<uint16_t>& x, const std::vector<uint8_t>& codes,
             const std::vector<float>& scales, std::vector<float>& y, long long n_in, long long n_out,
             int tpr, int iters) {
    for (int i = 0; i < 3; ++i) run(x.data(), codes.data(), scales.data(), y.data(), n_in, n_out, tpr);
    cudaDeviceSynchronize();
    auto t0 = std::chrono::steady_clock::now();
    for (int i = 0; i < iters; ++i) run(x.data(), codes.data(), scales.data(), y.data(), n_in, n_out, tpr);
    cudaDeviceSynchronize();
    double s = std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count();
    return (double) n_in * n_out * iters / s / 1e9;   // weights per second
}

}  // namespace lab

int main() {
    // The engine is live on this GPU; report honestly rather than hang.
    if (cudaDeviceSynchronize() != cudaSuccess) { printf("no device\n"); return 1; }
    // The expert gate/up shape the header names: [2560 x 640].
    const long long n_in = 2560, n_out = 640;
    const long long nb = n_in / lab::QK;
    std::vector<uint16_t> x(n_in);
    std::vector<uint8_t> codes(n_out * nb * (lab::QK / 4));
    std::vector<float> scales(n_out * nb);
    std::vector<float> y(n_out), ref(n_out);
    size_t free_b = 0, total_b = 0;
    if (cudaMemGetInfo(&free_b, &total_b) != cudaSuccess) { printf("cudaMemGetInfo failed\n"); return 1; }
    printf("device: %zu MiB free of %zu MiB\n", free_b / 1048576, total_b / 1048576);
    if (free_b < 64u * 1048576u) {
        printf("not enough headroom to benchmark: the engine holds the device. Park it and re-run.\n");
        return 1;
    }

    for (size_t i = 0; i < x.size(); ++i) x[i] = (uint16_t) ((i * 7919) % 65536);
    for (size_t i = 0; i < codes.size(); ++i) codes[i] = (uint8_t) ((i * 104729) % 256);
    for (size_t i = 0; i < scales.size(); ++i) scales[i] = (float) (((i * 2654435761) % 2000) - 1000) / 1000.0f;

    auto runA = [](const uint16_t* xp, const uint8_t* cp, const float* sp, float* yp, long long ni,
                   long long no, int) {
        const int threads = 128;
        lab::gemv_a<<<(unsigned) ((no + threads - 1) / threads), threads>>>(xp, cp, sp, yp, ni, no);
    };
    auto runB = [](const uint16_t* xp, const uint8_t* cp, const float* sp, float* yp, long long ni,
                   long long no, int tpr) { lab::gemv_b<<<(unsigned) no, tpr>>>(xp, cp, sp, yp, ni, no, tpr); };
    auto runC = [](const uint16_t* xp, const uint8_t* cp, const float* sp, float* yp, long long ni,
                   long long no, int tpr) { lab::gemv_c<<<(unsigned) no, tpr>>>(xp, cp, sp, yp, ni, no, tpr); };

    const int iters = 200;
    for (int pass = 0; pass < 3; ++pass) {
        printf("pass %d\n", pass);
        for (int tpr : {32, 64, 128}) {
            double ga = lab::bench(runA, x, codes, scales, y, n_in, n_out, 0, iters);
            double gb = lab::bench(runB, x, codes, scales, y, n_in, n_out, tpr, iters);
            double gc = lab::bench(runC, x, codes, scales, y, n_in, n_out, tpr, iters);
            printf("  tpr=%3d  A %7.1f G w/s   B %7.1f G w/s   C %7.1f G w/s\n", tpr, ga, gb, gc);
        }
    }

    // Parity against the reference, in the engine's terms: max relative error per output row.
    for (long long o = 0; o < n_out; ++o) ref[o] = lab::reference(x, codes, scales, n_in, n_out, o);
    runB(x.data(), codes.data(), scales.data(), y.data(), n_in, n_out, 64);
    cudaDeviceSynchronize();
    double worst = 0.0;
    for (long long o = 0; o < n_out; ++o) {
        double r = std::fabs(ref[o]) < 1e-9 ? 1e-9 : std::fabs(ref[o]);
        worst = std::max(worst, std::fabs((double) y[o] - ref[o]) / r);
    }
    printf("parity B vs CPU reference: max relative error %.3e\n", worst);
    return 0;
}
