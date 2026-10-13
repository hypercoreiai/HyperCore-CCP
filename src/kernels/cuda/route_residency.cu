// src/kernels/cuda/route_residency.hpp's implementation: the two residency-aware routing kernels.
// Both are one warp per token, coalesced over the 512 experts (lane j reads j, j+32, ...), and reduced inside the
// warp.  A scalar version of the same scan cost ~45 us per layer, which was as much as the PCIe experts it removed;
// the warp form is what makes the option worth turning on.
#include "hypercore/kernels/route_residency.hpp"

#include <cuda_runtime.h>

#include <cfloat>
#include <cmath>
#include <stdexcept>

namespace hypercore::kernels {
namespace {

__device__ __forceinline__ float warp_max(float v) {
#pragma unroll
    for (int m = 16; m; m >>= 1) v = fmaxf(v, __shfl_xor_sync(0xffffffffu, v, m, 32));
    return v;
}

// HYPERCORE_ROUTE_PRIOR=lambda.  One warp per token; 512 experts = 16 values per lane, as the native router.
// The selection score is the biased logit, the weight the router's own probability, so a bonus never reshapes the
// probabilities the experts are combined with.
__global__ void route_prior_k(const float* __restrict__ logits, const int32_t* __restrict__ res, float lambda,
                              int32_t* __restrict__ ids, float* __restrict__ weights) {
    const float* lg = logits + (size_t) blockIdx.x * 512;
    int32_t* id = ids + (size_t) blockIdx.x * 10;
    float* w = weights + (size_t) blockIdx.x * 10;
    const int lane = (int) threadIdx.x;
    float p[16], s[16];
    float mx = -INFINITY;
#pragma unroll
    for (int i = 0; i < 16; ++i) { p[i] = lg[lane + 32 * i]; mx = fmaxf(mx, p[i]); }
    mx = warp_max(mx);
#pragma unroll
    for (int i = 0; i < 16; ++i) {
        s[i] = p[i] + (res[lane + 32 * i] >= 0 ? lambda : 0.0f);   // the selection score
        p[i] = expf(p[i] - mx);                                    // the router's probability, unnormalised
    }
    float sel_p = 0.0f, sel_sum = 0.0f;
    for (int rank = 0; rank < 10; ++rank) {
        float best = -FLT_MAX, bp = 0.0f;
        int be = 1 << 30;
#pragma unroll
        for (int i = 0; i < 16; ++i)
            if (s[i] > best) { best = s[i]; be = lane + 32 * i; bp = p[i]; }
#pragma unroll
        for (int m = 16; m; m >>= 1) {   // strictly greater wins; the smallest expert index breaks a tie
            const float ob = __shfl_xor_sync(0xffffffffu, best, m, 32);
            const int oe = __shfl_xor_sync(0xffffffffu, be, m, 32);
            const float op = __shfl_xor_sync(0xffffffffu, bp, m, 32);
            if (ob > best || (ob == best && oe < be)) { best = ob; be = oe; bp = op; }
        }
        if ((be & 31) == lane) s[be >> 5] = -FLT_MAX;   // only the owning lane can remove it
        if (lane == rank) { id[rank] = be; sel_p = bp; }
        sel_sum += bp;                                   // the same running sum on every lane
    }
    if (lane < 10) w[lane] = sel_p / fmaxf(sel_sum, 1e-30f);
}

// HYPERCORE_ROUTE_RESIDENT=margin.  The ranks are still visited in order (a swap changes the set already picked),
// but the 512 scan is coalesced and reduced in the warp instead of walked by one thread per token.
// stats: [0] tail entries seen, [1] swaps, [2] non-resident before, [3] after.
__global__ void route_resident_k(const float* __restrict__ logits, int32_t* __restrict__ ids,
                                 float* __restrict__ weights, const int32_t* __restrict__ res, int n_tok,
                                 float margin, int lo, int hi, unsigned long long* __restrict__ stats) {
    const int t = (int) blockIdx.x;
    if (t >= n_tok) return;
    const int lane = (int) threadIdx.x;
    const float* l = logits + (size_t) t * 512;
    int32_t* id = ids + (size_t) t * 10;
    int32_t my[10];
    for (int r = 0; r < 10; ++r) my[r] = id[r];
    int swaps = 0, tail = 0, before = 0;
    if (lane == 0)
        for (int r = 0; r < 10; ++r) before += res[my[r]] < 0;
    for (int r = lo; r <= hi && r < 10; ++r) {
        const int e = my[r];
        if (res[e] >= 0) continue;                       // already resident: the branch is uniform across the warp
        if (lane == 0) ++tail;
        float bv = -INFINITY;
        int bi = -1;
        for (int f = lane; f < 512; f += 32) {
            if (res[f] < 0) continue;
            bool used = false;
            for (int q = 0; q < 10; ++q) used |= my[q] == f;
            if (used) continue;
            if (l[f] > bv) { bv = l[f]; bi = f; }
        }
#pragma unroll
        for (int off = 16; off > 0; off >>= 1) {
            const float ov = __shfl_down_sync(0xffffffffu, bv, off);
            const int oi = __shfl_down_sync(0xffffffffu, bi, off);
            if (ov > bv || (ov == bv && oi >= 0 && (bi < 0 || oi < bi))) { bv = ov; bi = oi; }
        }
        if (lane == 0 && bi >= 0 && l[e] - bv <= margin) { my[r] = bi; ++swaps; }
        my[r] = __shfl_sync(0xffffffffu, my[r], 0);     // every lane sees the same picked set
    }
    int after = 0;
    if (lane == 0)
        for (int r = 0; r < 10; ++r) after += res[my[r]] < 0;
    const int sw = __shfl_sync(0xffffffffu, swaps, 0);
    if (sw) {   // only a token that actually moved re-derives its weights; the others keep the router's bits
        float m = -INFINITY;
        for (int r = 0; r < 10; ++r) m = fmaxf(m, l[my[r]]);
        float ex[10], sum = 0.0f;
        for (int r = 0; r < 10; ++r) { ex[r] = expf(l[my[r]] - m); sum += ex[r]; }
        for (int r = 0; r < 10; ++r) weights[(size_t) t * 10 + r] = ex[r] / sum;
    }
    if (lane == 0) {
        for (int r = 0; r < 10; ++r) id[r] = my[r];
        if (stats) {
            atomicAdd(stats + 0, (unsigned long long) tail);
            atomicAdd(stats + 1, (unsigned long long) sw);
            atomicAdd(stats + 2, (unsigned long long) before);
            atomicAdd(stats + 3, (unsigned long long) after);
        }
    }
}

}  // namespace

void route_prior_top10(const float* logits, const int32_t* res_layer, float lambda, int32_t* ids, float* weights,
                       int n_tok, void* stream) {
    if (n_tok <= 0) return;
    if (logits == nullptr || res_layer == nullptr || ids == nullptr || weights == nullptr)
        throw std::invalid_argument("route prior needs [n,512] logits, a residency table and [n,10] outputs");
    if (lambda <= 0.0f) return;   // no bonus: the router's own answer stands
    route_prior_k<<<(unsigned) n_tok, 32, 0, static_cast<cudaStream_t>(stream)>>>(
        logits, res_layer, lambda, ids, weights);
    const auto error = cudaGetLastError();
    if (error != cudaSuccess) throw std::runtime_error(std::string("route prior: ") + cudaGetErrorString(error));
}

void route_resident_swap(const float* logits, int32_t* ids, float* weights, const int32_t* res_layer, int n_tok,
                         float margin, int rank_lo, int rank_hi, unsigned long long* stats, void* stream) {
    if (n_tok <= 0) return;
    if (logits == nullptr || res_layer == nullptr || ids == nullptr || weights == nullptr)
        throw std::invalid_argument("route resident needs [n,512] logits, a residency table and [n,10] outputs");
    if (margin < 0.0f || rank_lo > rank_hi || rank_lo >= 10) return;   // a zero margin still swaps an equal or better resident expert
    if (rank_hi > 9) rank_hi = 9;
    route_resident_k<<<(unsigned) n_tok, 32, 0, static_cast<cudaStream_t>(stream)>>>(
        logits, ids, weights, res_layer, n_tok, margin, rank_lo, rank_hi, stats);
    const auto error = cudaGetLastError();
    if (error != cudaSuccess) throw std::runtime_error(std::string("route resident: ") + cudaGetErrorString(error));
}

}  // namespace hypercore::kernels
