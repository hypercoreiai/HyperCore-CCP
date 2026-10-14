// src/kernels/mmvq_il_parity.cpp - native_mmvq_il (2-6 columns from the interleaved q8_1 copy, fork F4) against
// native_mmvq's multi-column kernels, bitwise, for every rows-a-warp choice; --bench times both per call.
//
//     build/mmvq_il_parity [--bench [--emit-table]]
//
// --emit-table (with --bench) prints the rows-a-warp table this card measured, in the source form of kIlRows in
// native_mmvq.cu: per cell the rows count (1/2/4) that takes at least 3% off native_mmvq's time, else 0.
//
// The same Q8_1 bytes feed both paths (quantize_q8_1_rows, then native_q8_1_interleave). Weights are random bytes with
// the block scales rewritten as normal fp16 values, so every output is finite (a NaN would compare equal whatever
// produced it). The bench cycles through enough copies of the weights to miss the L2 cache, as a layer's call does.
#include "hypercore/kernels/iq_kernels.hpp"
#include "hypercore/kernels/native_mmvq.hpp"
#include "hypercore/kernels/q8_1_il_copy.hpp"

#include <cuda_runtime.h>

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <random>
#include <string>
#include <vector>

namespace {
using namespace hypercore::kernels;

struct Cell { int type, T, n_out; double ref; double il[5]; };
std::vector<Cell> g_cells;
struct Case {
    const char* name;
    int type, n_in, n_out, block_elems, block_bytes, scale_at[2];
};
// the engine's dense shapes: qkv 10240 / gate 6144 / out 2560 (GDN), q 12288 / k,v 512 / o 2560 (QSA), the head
const Case CASES[] = {
    {"IQ4_XS 2560x10240", 23, 2560, 10240, 256, 136, {0, -1}},
    {"IQ4_XS 2560x6144", 23, 2560, 6144, 256, 136, {0, -1}},
    {"IQ4_XS 6144x2560", 23, 6144, 2560, 256, 136, {0, -1}},
    {"IQ4_XS 2560x512", 23, 2560, 512, 256, 136, {0, -1}},
    {"Q4_K 2560x10240", 12, 2560, 10240, 256, 144, {0, 2}},
    {"Q4_K 6144x2560", 12, 6144, 2560, 256, 144, {0, 2}},
    {"Q4_K odd rows 2560x2051", 12, 2560, 2051, 256, 144, {0, 2}},
    {"Q5_K 2560x12288", 13, 2560, 12288, 256, 176, {0, 2}},
    {"Q5_K 2560x6144", 13, 2560, 6144, 256, 176, {0, 2}},
    {"Q5_K 6144x2560", 13, 6144, 2560, 256, 176, {0, 2}},
    {"Q5_K head 2560x248320", 13, 2560, 248320, 256, 176, {0, 2}},
    {"Q6_K 2560x12288", 14, 2560, 12288, 256, 210, {208, -1}},
    {"Q6_K 2560x10240", 14, 2560, 10240, 256, 210, {208, -1}},
    {"Q6_K 6144x2560", 14, 6144, 2560, 256, 210, {208, -1}},
    {"Q6_K odd rows 2560x2051", 14, 2560, 2051, 256, 210, {208, -1}},
    {"Q6_K 2560x512", 14, 2560, 512, 256, 210, {208, -1}},
    {"IQ4_XS 2560x12288", 23, 2560, 12288, 256, 136, {0, -1}},
    {"IQ4_XS 2560x640", 23, 2560, 640, 256, 136, {0, -1}},
    {"Q4_K 2560x6144", 12, 2560, 6144, 256, 144, {0, 2}},
    {"Q4_K 2560x640", 12, 2560, 640, 256, 144, {0, 2}},
    {"Q4_K 2560x512", 12, 2560, 512, 256, 144, {0, 2}},
    {"Q5_K 2560x10240", 13, 2560, 10240, 256, 176, {0, 2}},
    {"Q5_K 2560x640", 13, 2560, 640, 256, 176, {0, 2}},
    {"Q5_K 2560x512", 13, 2560, 512, 256, 176, {0, 2}},
    {"Q6_K 2560x6144", 14, 2560, 6144, 256, 210, {208, -1}},
    {"Q6_K 2560x640", 14, 2560, 640, 256, 210, {208, -1}},
    {"Q3_K 2560x10240", 11, 2560, 10240, 256, 110, {108, -1}},
    {"Q3_K 2560x12288", 11, 2560, 12288, 256, 110, {108, -1}},
    {"Q3_K 2560x6144", 11, 2560, 6144, 256, 110, {108, -1}},
    {"Q3_K 6144x2560", 11, 6144, 2560, 256, 110, {108, -1}},
    {"Q3_K 2560x640", 11, 2560, 640, 256, 110, {108, -1}},
    {"Q3_K 2560x512", 11, 2560, 512, 256, 110, {108, -1}},
    {"Q3_K 2560x2051 odd", 11, 2560, 2051, 256, 110, {108, -1}},
};

uint16_t sane_half(std::mt19937& rng) {
    const uint32_t r = rng();
    return (uint16_t) (((r >> 31) << 15) | ((5u + (r >> 10) % 5u) << 10) | (r & 0x3ffu));
}
bool ck(cudaError_t e, const char* what) {
    if (e == cudaSuccess) return true;
    std::printf("CUDA: %s: %s\n", what, cudaGetErrorString(e));
    return false;
}

int run_case(const Case& c, bool bench, cudaStream_t s) {
    if (std::strstr(c.name, "odd") != nullptr) bench = false;   // parity-only shape: not a timing cell of the table
    if (c.type == 13 && c.n_out > 100000 && !bench) { /* the head: parity too, just big */ }
    const std::size_t wbytes = native_mmvq_weight_bytes(c.type, c.n_in, c.n_out);
    std::mt19937 rng(77u + (unsigned) c.type * 31u + (unsigned) c.n_out);
    std::vector<uint8_t> w(wbytes);
    for (auto& b : w) b = (uint8_t) (rng() & 0xff);
    const std::size_t n_blocks = (std::size_t) c.n_out * (std::size_t) (c.n_in / c.block_elems);
    if (n_blocks * (std::size_t) c.block_bytes != wbytes) {
        std::printf("%s: weight bytes mismatch\n", c.name);
        return 1;
    }
    for (std::size_t k = 0; k < n_blocks; ++k)
        for (int at : c.scale_at)
            if (at >= 0) {
                const uint16_t h = sane_half(rng);
                std::memcpy(&w[k * (std::size_t) c.block_bytes + (std::size_t) at], &h, 2);
            }
    const int copies = bench ? (int) std::max<std::size_t>(1, std::min<std::size_t>(24, (192u << 20) / wbytes)) : 1;
    std::vector<void*> dw(copies, nullptr);
    for (int i = 0; i < copies; ++i) {
        if (!ck(cudaMalloc(&dw[i], wbytes), "malloc w") || !ck(cudaMemcpy(dw[i], w.data(), wbytes, cudaMemcpyHostToDevice), "copy w"))
            return 1;
    }
    int bad = 0;
    for (int T = 1; T <= 6; ++T) {   // 5 and 6 are the --spec 4 + MTP window widths (HYPERCORE_MMVQ_IL_WIDE)
        std::vector<float> x((std::size_t) T * c.n_in);
        std::normal_distribution<float> nd(0.f, 1.f);
        for (auto& v : x) v = nd(rng);
        float* dx = nullptr;
        void *xq = nullptr, *xil = nullptr;
        float *yref = nullptr, *yil = nullptr;
        const std::size_t ybytes = (std::size_t) T * c.n_out * 4;
        if (!ck(cudaMalloc(&dx, x.size() * 4), "malloc x") ||
            !ck(cudaMalloc(&xq, native_q8_1_bytes(c.n_in, T)), "malloc xq") ||
            !ck(cudaMalloc(&xil, native_q8_1_il_bytes(c.n_in, T)), "malloc xil") ||
            !ck(cudaMalloc((void**) &yref, ybytes), "malloc yref") || !ck(cudaMalloc((void**) &yil, ybytes), "malloc yil"))
            return 1;
        ck(cudaMemcpy(dx, x.data(), x.size() * 4, cudaMemcpyHostToDevice), "copy x");
        quantize_q8_1_rows(dx, T, c.n_in, xq, s);
        if (T >= 2) native_q8_1_interleave(xq, xil, c.n_in, T, s);
        native_mmvq(c.type, dw[0], xq, yref, c.n_in, c.n_out, T, s);
        ck(cudaStreamSynchronize(s), "ref");
        std::vector<uint32_t> a((std::size_t) T * c.n_out), b(a.size());
        ck(cudaMemcpy(a.data(), yref, ybytes, cudaMemcpyDeviceToHost), "read ref");
        double best_ref = 0, best_il[5] = {0, 0, 0, 0, 0};
        int table_r = 0;
        for (int r : {0, 1, 2, 4}) {
            native_mmvq_il_tune(r);
            cudaMemset(yil, 0xff, ybytes);
            native_mmvq_il(c.type, dw[0], xq, xil, yil, c.n_in, c.n_out, T, s);
            ck(cudaStreamSynchronize(s), "il");
            ck(cudaMemcpy(b.data(), yil, ybytes, cudaMemcpyDeviceToHost), "read il");
            long long diff = 0, nonfinite = 0;
            for (std::size_t i = 0; i < a.size(); ++i) {
                float fa;
                std::memcpy(&fa, &a[i], 4);
                if (!std::isfinite(fa)) ++nonfinite;
                if (a[i] != b[i]) ++diff;
            }
            const bool used = r != 0 || native_mmvq_il_supported(c.type, T, c.n_out);
            if (diff != 0 || nonfinite != 0) {
                ++bad;
                std::printf("FAIL %-26s T=%d rows=%d: %lld bits differ, %lld non-finite of %zu\n", c.name, T, r, diff, nonfinite, a.size());
            }
            (void) used;
            // A wide window has one kernel (two rows a warp), so there is nothing to search or time per row count.
            if (bench && r != 0 && T <= 4) {
                cudaEvent_t e0, e1;
                cudaEventCreate(&e0);
                cudaEventCreate(&e1);
                const int reps = 200;
                for (int rep = 0; rep < 2; ++rep) {   // rep 0 warms, rep 1 times
                    cudaEventRecord(e0, s);
                    for (int i = 0; i < reps; ++i) native_mmvq_il(c.type, dw[i % copies], xq, xil, yil, c.n_in, c.n_out, T, s);
                    cudaEventRecord(e1, s);
                    cudaEventSynchronize(e1);
                }
                float ms;
                cudaEventElapsedTime(&ms, e0, e1);
                best_il[r] = 1000.0 * ms / reps;
                cudaEventDestroy(e0);
                cudaEventDestroy(e1);
            }
        }
        // The stale-copy case verify.cpp's guard has to avoid: x_il still holds the interleaved columns of an
        // earlier x_q8_1. Using it must not reproduce native_mmvq's output; rebuilding it must.
        if (T >= 2 && native_mmvq_il_supported(c.type, T, c.n_out)) {
            std::vector<uint32_t> a((std::size_t) T * c.n_out), b(a.size());
            auto read_bits = [&](float* src, std::vector<uint32_t>& dst) {
                ck(cudaMemcpy(dst.data(), src, ybytes, cudaMemcpyDeviceToHost), "read");
            };
            long long differ = 0;
            std::vector<float> x2((std::size_t) T * c.n_in);
            for (auto& v : x2) v = nd(rng);
            if (!ck(cudaMemcpy(dx, x2.data(), x2.size() * 4, cudaMemcpyHostToDevice), "copy x2")) return 1;
            quantize_q8_1_rows(dx, T, c.n_in, xq, s);
            native_mmvq(c.type, dw[0], xq, yref, c.n_in, c.n_out, T, s);
            native_mmvq_il(c.type, dw[0], xq, xil, yil, c.n_in, c.n_out, T, s);   // xil from the previous xq
            ck(cudaStreamSynchronize(s), "stale");
            read_bits(yref, a); read_bits(yil, b);
            differ = 0; for (std::size_t i = 0; i < a.size(); ++i) if (a[i] != b[i]) ++differ;
            if (differ == 0) {
                ++bad;
                std::printf("FAIL %-26s T=%d stale copy: a stale interleaved copy matched native_mmvq, "
                           "so the guard is not exercising anything\n", c.name, T);
            }
            native_q8_1_interleave(xq, xil, c.n_in, T, s);   // what the guard does before every use
            native_mmvq_il(c.type, dw[0], xq, xil, yil, c.n_in, c.n_out, T, s);
            ck(cudaStreamSynchronize(s), "fresh");
            read_bits(yref, a); read_bits(yil, b);
            differ = 0; for (std::size_t i = 0; i < a.size(); ++i) if (a[i] != b[i]) ++differ;
            if (differ != 0) {
                ++bad;
                std::printf("FAIL %-26s T=%d fresh copy: %lld bits differ after re-interleaving\n", c.name, T, differ);
            }
        }
        native_mmvq_il_tune(0);
        if (bench) {
            cudaEvent_t e0, e1;
            cudaEventCreate(&e0);
            cudaEventCreate(&e1);
            const int reps = 200;
            for (int rep = 0; rep < 2; ++rep) {
                cudaEventRecord(e0, s);
                for (int i = 0; i < reps; ++i) native_mmvq(c.type, dw[i % copies], xq, yref, c.n_in, c.n_out, T, s);
                cudaEventRecord(e1, s);
                cudaEventSynchronize(e1);
            }
            float ms;
            cudaEventElapsedTime(&ms, e0, e1);
            best_ref = 1000.0 * ms / reps;
            (void) table_r;
            g_cells.push_back({c.type, T, c.n_out, best_ref, {0, best_il[1], best_il[2], 0, best_il[4]}});
            std::printf("BENCH %-26s T=%d  multi %.1f us | il rows1 %.1f rows2 %.1f rows4 %.1f us\n", c.name, T, best_ref,
                        best_il[1], best_il[2], best_il[4]);
        }
        cudaFree(dx); cudaFree(xq); cudaFree(xil); cudaFree(yref); cudaFree(yil);
    }
    for (void* p : dw) cudaFree(p);
    return bad;
}

// the table as kIlRows prints it: per (type, ncols, n_out class) the fastest rows count if >= 3% under native_mmvq, else 0.
// A cell with several measured shapes takes the worst (smallest) gain of the best choice, as the shipped table does for
// two cards; a class with no measured shape prints the value of its neighbour below it (or 0).
void emit_table() {
    const int types[] = {23, 12, 13, 14, 11};
    const char* names[] = {"IQ4_XS", "Q4_K", "Q5_K", "Q6_K", "Q3_K"};
    std::printf("// measured on this card by mmvq_il_parity --bench --emit-table\n");
    // per cell: the rows count whose WORST ratio to native_mmvq over the cell's measured shapes is the best, taken only
    // when that worst ratio is under 0.97 (else 0); a class with no measured shape takes its lower neighbour's value
    auto pick_cell = [&](int type, int nc, int cls, int prev) {
        double best_worst = 1e9;
        int best = -1;
        bool any = false;
        for (int r : {1, 2, 4}) {
            double worst = 0;
            bool have = false;
            for (const Cell& c : g_cells) {
                if (c.type != type || c.T != nc) continue;
                const int cc = c.n_out < 2048 ? 0 : c.n_out < 4096 ? 1 : c.n_out < 8192 ? 2 : c.n_out < 12288 ? 3 : 4;
                if (cc != cls || c.il[r] <= 0) continue;
                have = true;
                worst = std::max(worst, c.il[r] / c.ref);
            }
            any = any || have;
            if (have && worst < best_worst) { best_worst = worst; best = r; }
        }
        if (!any) return prev;
        return best_worst < 0.97 ? best : 0;
    };
    for (int ti = 0; ti < 5; ++ti) {
        std::printf("    {%d, {", types[ti]);
        for (int nc = 2; nc <= 4; ++nc) {
            int prev = 0;
            std::printf("{");
            for (int cls = 0; cls < 5; ++cls) {
                prev = pick_cell(types[ti], nc, cls, prev);
                std::printf("%d%s", prev, cls < 4 ? ", " : "");
            }
            std::printf("}%s", nc < 4 ? ", " : "");
        }
        std::printf("}},   // %s\n", names[ti]);
    }
    std::printf("// one column (kIl1RowsShared):\n");
    for (int ti = 0; ti < 5; ++ti) {
        std::printf("    {%d, {", types[ti]);
        int prev = 0;
        for (int cls = 0; cls < 5; ++cls) {
            prev = pick_cell(types[ti], 1, cls, prev);
            std::printf("%d%s", prev, cls < 4 ? ", " : "");
        }
        std::printf("}},   // %s\n", names[ti]);
    }
}

// --sequence: the verify window's own call order through Q81IlCopy.  A layer writes x_q8_1, reads it
// twice with the same shape (qkv then the gate), then re-quantizes for the next projection.  Every
// interleaved call must be bitwise native_mmvq's, the second call must REUSE the copy, and the copy
// after a re-quantize must be rebuilt - the three things a missing invalidate() or a shape-blind
// guard gets wrong, and the reason a window multiplies a layer's weights against another layer's
// activations.
int run_sequence(cudaStream_t s) {
    struct Step { const char* name; int type, n_in, n_out, block_elems, block_bytes, scale_at[2]; bool writes_xq; };
    const Step steps[] = {
        {"qkv    2560x10240", 23, 2560, 10240, 256, 136, {0, -1}, true},    // the fused GR read wrote xq_
        {"gate   2560x6144",  23, 2560, 6144,  256, 136, {0, -1}, false},   // the same columns, same shape
        {"out    6144x2560",  12, 6144, 2560,  256, 144, {0, 2},  true},    // the GDN step re-quantizes
        {"attno  512x2560",   13, 512,  2560,  256, 176, {0, 2},  true},    // the attention output's
        {"head   2560x20480", 11, 2560, 20480, 256, 110, {108, -1}, true},  // the head
    };
    const int max_in = 6144, max_cols = 6;   // a --spec 4 + MTP verify window is six tokens wide
    void* xq = nullptr;
    void* xil = nullptr;
    if (!ck(cudaMalloc(&xq, native_q8_1_bytes(max_in, max_cols)), "malloc xq") ||
        !ck(cudaMalloc(&xil, native_q8_1_il_bytes(max_in, max_cols)), "malloc xil")) return 1;
    int bad = 0;
    std::mt19937 rng(4242u);
    std::normal_distribution<float> nd(0.f, 1.f);
    for (int T = 2; T <= 6; ++T) {
        Q81IlCopy guard;
        guard.init(xil, max_in, max_cols);
        bool any_il = false;
        for (const Step& st : steps) {
            const std::size_t wbytes = native_mmvq_weight_bytes(st.type, st.n_in, st.n_out);
            std::vector<uint8_t> w(wbytes);
            for (auto& b : w) b = (uint8_t) (rng() & 0xff);
            const std::size_t n_blocks = (std::size_t) st.n_out * (std::size_t) (st.n_in / st.block_elems);
            for (std::size_t k = 0; k < n_blocks; ++k)
                for (int at : st.scale_at)
                    if (at >= 0) {
                        const uint16_t h = sane_half(rng);
                        std::memcpy(&w[k * (std::size_t) st.block_bytes + (std::size_t) at], &h, 2);
                    }
            void* dw = nullptr;
            float *ya = nullptr, *yb = nullptr;
            if (!ck(cudaMalloc(&dw, wbytes), "malloc w") ||
                !ck(cudaMalloc(&ya, (std::size_t) T * st.n_out * 4), "malloc ya") ||
                !ck(cudaMalloc(&yb, (std::size_t) T * st.n_out * 4), "malloc yb")) { bad = 1; break; }
            std::vector<float> x((std::size_t) T * st.n_in);
            for (auto& v : x) v = nd(rng);
            float* dx = nullptr;
            if (!ck(cudaMalloc(&dx, x.size() * 4), "malloc dx")) { bad = 1; break; }
            ck(cudaMemcpy(dx, x.data(), x.size() * 4, cudaMemcpyHostToDevice), "copy x");
            if (st.writes_xq) { quantize_q8_1_rows(dx, T, st.n_in, xq, s); guard.invalidate(); }
            native_mmvq(st.type, dw, xq, ya, st.n_in, st.n_out, T, s);
            const void* x_il = guard.read(xq, st.n_in, T, s);   // rebuilds on a shape change or a write
            native_mmvq_il(st.type, dw, xq, x_il, yb, st.n_in, st.n_out, T, s);
            any_il |= native_mmvq_il_supported(st.type, T, st.n_out);
            if (!ck(cudaStreamSynchronize(s), "sequence")) { bad = 1; break; }
            std::vector<uint32_t> a((std::size_t) T * st.n_out), b(a.size());
            ck(cudaMemcpy(a.data(), ya, a.size() * 4, cudaMemcpyDeviceToHost), "read ref");
            ck(cudaMemcpy(b.data(), yb, b.size() * 4, cudaMemcpyDeviceToHost), "read il");
            long long diff = 0;
            for (size_t i = 0; i < a.size(); ++i) if (a[i] != b[i]) ++diff;
            if (diff != 0) {
                ++bad;
                std::printf("FAIL sequence T=%d %-18s: %lld of %zu values differ from native_mmvq "
                           "(copy built %lld times, reused %lld, shape %d x %d)\n",
                           T, st.name, diff, a.size(), (long long) guard.builds(), (long long) guard.uses(),
                           guard.shape_n_in(), guard.shape_ncols());
            }
            cudaFree(dw); cudaFree(ya); cudaFree(yb); cudaFree(dx);
        }
        if (!any_il) {
            ++bad;
            std::printf("FAIL sequence T=%d: no call in the window took the interleaved path\n", T);
        } else if (guard.uses() < 1) {
            ++bad;
            std::printf("FAIL sequence T=%d: the gate projection rebuilt the copy instead of reusing it "
                       "(%lld builds, %lld uses)\n", T, (long long) guard.builds(), (long long) guard.uses());
        } else {
            std::printf("sequence T=%d: %lld copies built, %lld calls reused one, all outputs bitwise\n",
                       T, (long long) guard.builds(), (long long) guard.uses());
        }
    }
    cudaFree(xq); cudaFree(xil);
    return bad;
}

// the per-architecture lookup, no GPU needed for its answers
int check_tables() {
    int bad = 0;
    for (int type : {23, 12, 13, 14, 11})
        for (int nc = 2; nc <= 4; ++nc)
            for (int n_out : {512, 2560, 6144, 10240, 12288, 248320}) {
                const int a = native_mmvq_il_rows_for(86, type, nc, n_out);
                // sm_120 has no table of its own: it answers the shared table (what sm_86 answered before its
                // own 143-dense table, which differs only in Q3_K, a type the shared table does not use).
                const int b = native_mmvq_il_rows_for(120, type, nc, n_out);
                if (b != native_mmvq_il_rows_for(121, type, nc, n_out) || (type != 11 && b != a) || (type == 11 && b != 0)) {
                    ++bad;
                    std::printf("FAIL table: sm_120 differs from the shared table at type %d ncols %d n_out %d\n", type, nc, n_out);
                }
                if (a != 0 && a != 1 && a != 2 && a != 4) { ++bad; std::printf("FAIL table: rows %d\n", a); }
            }
    // Ada (sm_89) reads the table measured on this box's RTX 4090: Q3_K at 2 columns and 512 rows is 0 rows a warp,
    // at 4 columns and 512 rows it is 2; Q4_K at 3 columns and 2560 rows is 1; Q6_K at 2 columns is 0.  Re-measure
    // with mmvq_il_parity --bench --emit-table after a kernel change (docs/MMVQ_IL_TABLE.md).
    if (native_mmvq_il_rows_for(89, 11, 2, 512) != 0 || native_mmvq_il_rows_for(89, 11, 4, 512) != 2 ||
        native_mmvq_il_rows_for(89, 12, 3, 2560) != 1 || native_mmvq_il_rows_for(89, 14, 2, 2560) != 0) {
        ++bad;
        std::printf("FAIL table: the sm_89 table is not the 4090's\n");
    }
    // Volta has its own table (PR 1401): Q6_K at 2 columns, 2560 rows -> 1 row a warp; the Ampere table says 0 there
    if (native_mmvq_il_rows_for(70, 14, 2, 2560) != 1 || native_mmvq_il_rows_for(86, 14, 2, 2560) != 0) {
        ++bad;
        std::printf("FAIL table: the sm_70 table is not the V100's\n");
    }
    // Pascal has its own table too (the P100's): Q6_K, 3 columns, 12288 rows -> 4 rows a warp; sm_75 still has none (the shared one)
    if (native_mmvq_il_rows_for(60, 14, 3, 12288) != 4 || native_mmvq_il_rows_for(60, 23, 2, 512) != 0) {
        ++bad;
        std::printf("FAIL table: the sm_60 table is not the P100's\n");
    }
    if (native_mmvq_il_rows_for(89, 99, 2, 2560) != 0 || native_mmvq_il_rows_for(89, 12, 7, 2560) != 0) {
        ++bad;
        std::printf("FAIL table: an unknown type or an ncols with no kernel must be 0\n");
    }
    // HYPERCORE_MMVQ_IL_WIDE: 5 and 6 columns follow the four-column cell's decision, at two rows a warp;
    // turning the switch off puts every width above four back on native_mmvq's kernels.
    setenv("HYPERCORE_MMVQ_IL_WIDE", "0", 1);
    if (native_mmvq_il_rows_for(89, 12, 5, 2560) != 0 || native_mmvq_il_rows_for(89, 12, 6, 2560) != 0) {
        ++bad;
        std::printf("FAIL table: HYPERCORE_MMVQ_IL_WIDE=0 must leave 5 and 6 columns to native_mmvq\n");
    }
    setenv("HYPERCORE_MMVQ_IL_WIDE", "1", 1);
    for (int nc : {5, 6}) {
        const int four = native_mmvq_il_rows_for(89, 12, 4, 2560);
        const int wide = native_mmvq_il_rows_for(89, 12, nc, 2560);
        if (wide != (four ? 2 : 0)) {
            ++bad;
            std::printf("FAIL table: ncols=%d answered %d, the four-column cell answered %d\n", nc, wide, four);
        }
    }
    return bad;
}

// --guard: the copy guard's state machine on ordinary memory.  native_q8_1_interleave is swapped for a
// host model of the same layout, so a window's call order can be walked with the card busy or absent and
// every read compared against the bytes the source holds at that moment.  This is the test for the one
// thing record_window has to get right: every write to xq_ goes through invalidate().  A write that does
// not is caught here as a read returning bytes that are not the current source's.
float half_to_float(uint16_t h) {
    const uint32_t sign = (h & 0x8000u) ? 0x80000000u : 0u;
    const uint32_t exp = (h >> 10) & 0x3fu, mant = h & 0x3ffu;
    if (exp == 0u) {
        if (mant == 0u) return sign ? -0.0f : 0.0f;
        float v = (float)mant * (1.0f / 16777216.0f);   // subnormal half: mant * 2^-24
        return sign ? -v : v;
    }
    if (exp == 0x3fu) return mant ? (float)NAN : (sign ? -INFINITY : INFINITY);
    uint32_t bits = sign | (((exp - 15u) + 127u) << 23) | (mant << 13);
    float f; std::memcpy(&f, &bits, sizeof f); return f;
}

void host_interleave(const void* src, void* dst, int n_in, int ncols, void*) {
    const int nb = n_in / 32, cp = native_q8_1_il_cp(ncols);
    int* bm = static_cast<int*>(dst);
    int* pm = bm + (size_t)nb * 8 * cp;
    float* d = reinterpret_cast<float*>(bm + 2 * (size_t)nb * 8 * cp);
    for (int c = 0; c < ncols; ++c) {
        for (int b = 0; b < nb; ++b) {
            const uint8_t* blk = static_cast<const uint8_t*>(src) + (size_t)c * nb * 36 + (size_t)b * 36;
            for (int p = 0; p < 8; ++p) {
                int v; std::memcpy(&v, blk + 4 + p * 4, sizeof v);
                bm[((size_t)b * 8 + p) * cp + c] = v;      // block-major, the layout Q81Il reads
                pm[((size_t)p * nb + b) * cp + c] = v;     // position-major, the one the PM families read
            }
            uint16_t lo; std::memcpy(&lo, blk, sizeof lo);
            d[(size_t)b * cp + c] = half_to_float(lo);     // __low2float(ds), the scale the dots use
        }
    }
}

int run_guard() {
    int bad = 0;
    const int N = 2560, ZV = 6144;
    for (int T : {2, 3, 4, 6}) {   // a one-column window never reads the copy at all
        const int max_in = std::max(N, ZV);
        std::vector<uint8_t> xq(native_q8_1_bytes(max_in, T), 0);
        std::vector<uint8_t> il(native_q8_1_il_bytes(max_in, T), 0), want(il.size(), 0);
        Q81IlCopy guard;
        guard.init(il.data(), max_in, T);
        guard.set_builder(host_interleave);
        int calls = 0;   // interleaved calls in the block being walked, i.e. those with ncols >= 2

        auto write_xq = [&](int rows, int seed) {   // a layer quantizing its activations into xq_
            for (size_t i = 0; i < xq.size(); ++i) xq[i] = (uint8_t)(((size_t)seed * 7 + i * 131) & 0xffu);
            (void) rows;   // the real write covers rows' columns; the model writes the whole buffer
        };
        auto read = [&](int n_in, int ncols, const char* what) {
            const void* got = guard.read(xq.data(), n_in, ncols, nullptr);
            if (ncols < 2) return;   // one column: the plain blocks, the copy is not touched
            ++calls;
            host_interleave(xq.data(), want.data(), n_in, ncols, nullptr);
            const size_t bytes = native_q8_1_il_bytes(n_in, ncols);
            if (bytes > il.size()) {
                ++bad;
                std::printf("FAIL guard T=%d %s: (n_in=%d, ncols=%d) needs %zu bytes, the buffer holds %zu\n",
                            T, what, n_in, ncols, bytes, il.size());
                return;
            }
            if (std::memcmp(got, want.data(), bytes) != 0) {
                ++bad;
                std::printf("FAIL guard T=%d %s: the copy for (n_in=%d, ncols=%d) is not the source's current "
                            "bytes - a write to xq_ missed invalidate()\n", T, what, n_in, ncols);
            }
        };

        // One window, in the order record_window walks it: the read's quantize, the qkv and the gate off
        // the same columns, the attention/GDN quantize, its out projection, the shared expert's own
        // quantize into nsw.q8_1 (xq_ when the shared stream is not forked), the next layer, the head.
        write_xq(N, 1); guard.invalidate();
        read(N, T, "qkv layer 1");
        read(N, T, "gate layer 1");        // same shape, no write between: must reuse, and still match
        write_xq(ZV, 2); guard.invalidate();
        read(ZV, T, "out layer 1");
        write_xq(N, 3); guard.invalidate();
        read(N, T, "qkv layer 2");
        write_xq(N, 4); guard.invalidate();   // shared_expert_multi's native_quantize_q8_1(x, nw.q8_1, ...)
        read(N, T, "qkv layer 3");
        write_xq(N, 5); guard.invalidate();   // the head's
        read(N, T, "head");
        if (calls < 2 || guard.builds() != calls - 1 || guard.uses() != 1) {
            ++bad;
            std::printf("FAIL guard T=%d: %d interleaved calls built %lld copies and reused one %lld times; "
                        "one shape read twice with nothing written between is the only legal reuse\n",
                        T, calls, (long long)guard.builds(), (long long)guard.uses());
        }

        // The isolation arm, HYPERCORE_MMVQ_IL_REUSE=0: every call builds.  Same answers, more work - and
        // it is what separates "a write missed invalidate()" from "the kernel is wrong".
        guard.set_reuse(false); guard.reset(); calls = 0;
        write_xq(N, 6); guard.invalidate();
        read(N, T, "qkv, no reuse 1");
        read(N, T, "gate, no reuse 2");
        if (guard.uses() != 0 || guard.builds() != calls) {
            ++bad;
            std::printf("FAIL guard T=%d: REUSE=0 built %lld copies for %d interleaved calls\n",
                       T, (long long)guard.builds(), calls);
        }
        guard.set_reuse(true);

        // The negative control: a write that never reaches the guard.  The read after it must come back
        // different, or this test is measuring nothing.
        guard.reset(); calls = 0;
        write_xq(N, 7); guard.invalidate();
        read(N, T, "qkv, then an unguarded write");
        write_xq(N, 8);                        // no invalidate(): the hole the shared expert had
        const void* stale = guard.read(xq.data(), N, T, nullptr);
        host_interleave(xq.data(), want.data(), N, T, nullptr);
        if (std::memcmp(stale, want.data(), native_q8_1_il_bytes(N, T)) == 0) {
            ++bad;
            std::printf("FAIL guard T=%d: a write without invalidate() was not detected - the test cannot see staleness\n", T);
        }
    }
    return bad;
}
}  // namespace

int main(int argc, char** argv) {
    // --tables: the rows-a-warp lookup alone, no GPU work.  Useful when the card is busy with a running engine.
    const bool only_tables = argc > 1 && std::string(argv[1]) == "--tables";
    const bool only_guard = argc > 1 && std::string(argv[1]) == "--guard";   // the copy guard, on the host
    if (only_guard) {
        int bad = run_guard();
        std::printf("%s\n", bad ? "mmvq_il_parity: FAIL (guard)" : "mmvq_il_parity: OK (the copy guard, no card)");
        return bad ? 1 : 0;
    }
    const bool bench = argc > 1 && std::string(argv[1]) == "--bench";
    const bool emit = bench && argc > 2 && std::string(argv[2]) == "--emit-table";
    cudaStream_t s;
    cudaStreamCreate(&s);
    int bad = 0;
    bad += check_tables();
    if (only_tables) {
        std::printf("%s\n", bad ? "mmvq_il_parity: FAIL (table)" : "mmvq_il_parity: OK (the table only, no kernel ran)");
        return bad ? 1 : 0;
    }
    const char* only = std::getenv("MMVQ_IL_ONLY");   // 143-dense: only the cases whose name contains this
    for (const Case& c : CASES)
        if (only == nullptr || std::strstr(c.name, only) != nullptr) bad += run_case(c, bench, s);
    if (emit) emit_table();
    bad += run_sequence(s);   // the window's call order through the copy guard, always
    std::printf("%s\n", bad ? "mmvq_il_parity: FAIL" : "mmvq_il_parity: OK (every case, T 1-4, rows 1/2/4 and the table, bitwise)");
    return bad ? 1 : 0;
}
