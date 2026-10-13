// src/kernels/route_residency_parity.cu - the two residency-aware routers against a scalar reference of the same
// float arithmetic.  No model, no GPU state: synthetic logits and a synthetic residency table.
//   route_residency_parity            - the parity cases
//   route_residency_parity --bench    - the warp scan timed against the scalar scan it replaces
#include "hypercore/kernels/route_residency.hpp"

#include <cuda_runtime.h>

#include <cfloat>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

using hypercore::kernels::route_prior_top10;
using hypercore::kernels::route_resident_swap;

static const int NE = 512, K = 10;

// ---- the reference, in the same float expressions as the kernels ----

static void ref_prior(const float* lg, const int32_t* res, float lambda, int32_t* ids, float* w) {
    float mx = -INFINITY;
    for (int e = 0; e < NE; ++e) mx = std::max(mx, lg[e]);
    float s[NE];
    for (int e = 0; e < NE; ++e) s[e] = lg[e] + (res[e] >= 0 ? lambda : 0.0f);
    bool taken[NE] = {};
    float sel[K], sel_sum = 0.0f;
    for (int r = 0; r < K; ++r) {
        int be = -1;
        for (int e = 0; e < NE; ++e)
            if (!taken[e] && (be < 0 || s[e] > s[be])) be = e;   // strictly greater: the first index wins a tie
        taken[be] = true; ids[r] = be; sel[r] = expf(lg[be] - mx); sel_sum += sel[r];
    }
    for (int r = 0; r < K; ++r) w[r] = sel[r] / std::max(sel_sum, 1e-30f);
}

// The scalar scan the warp version replaces: the second reference, and the --bench comparison.
static int best_resident_scalar(const float* lg, const int32_t* res, const int32_t* picked) {
    int bi = -1;
    for (int f = 0; f < NE; ++f) {
        if (res[f] < 0) continue;
        bool used = false;
        for (int q = 0; q < K; ++q) used |= picked[q] == f;
        if (used) continue;
        if (bi < 0 || lg[f] > lg[bi]) bi = f;
    }
    return bi;
}

static void ref_resident(const float* lg, const int32_t* res, int32_t* ids, float* w, float margin, int lo, int hi,
                        long long& tail, long long& swaps, long long& before, long long& after) {
    int32_t my[K];
    for (int r = 0; r < K; ++r) my[r] = ids[r];
    for (int r = 0; r < K; ++r) before += res[my[r]] < 0;
    for (int r = lo; r <= hi && r < K; ++r) {
        const int e = my[r];
        if (res[e] >= 0) continue;
        ++tail;
        const int bi = best_resident_scalar(lg, res, my);
        if (bi >= 0 && lg[e] - lg[bi] <= margin) { my[r] = bi; ++swaps; }
    }
    for (int r = 0; r < K; ++r) after += res[my[r]] < 0;
    if (swaps) {
        float m = -INFINITY;
        for (int r = 0; r < K; ++r) m = std::max(m, lg[my[r]]);
        float ex[K], sum = 0.0f;
        for (int r = 0; r < K; ++r) { ex[r] = expf(lg[my[r]] - m); sum += ex[r]; }
        for (int r = 0; r < K; ++r) w[r] = ex[r] / sum;
    }
    for (int r = 0; r < K; ++r) ids[r] = my[r];
}

static void fill(std::mt19937& rng, float* lg) {
    std::uniform_real_distribution<float> d(-12.0f, 12.0f);
    for (int e = 0; e < NE; ++e) lg[e] = d(rng);
}

static void resident_table(std::mt19937& rng, std::vector<int32_t>& res, int n_resident) {
    res.assign(NE, -1);
    std::vector<int> all(NE);
    for (int i = 0; i < NE; ++i) all[i] = i;
    std::shuffle(all.begin(), all.end(), rng);
    for (int i = 0; i < n_resident; ++i) res[all[i]] = 1;
}

static double rel_max(const float* a, const float* b, int n) {
    double worst = 0.0;
    for (int i = 0; i < n; ++i)
        worst = std::max(worst, (double) std::fabs(a[i] - b[i]) / std::max(1e-12, (double) std::fabs(b[i])));
    return worst;
}

int main(int argc, char** argv) {
    const bool bench = argc > 1 && std::string(argv[1]) == "--bench";
    const int n_tok = 128;
    std::mt19937 rng(20261013u);

    std::vector<float> logits((size_t) n_tok * NE);
    for (int t = 0; t < n_tok; ++t) fill(rng, logits.data() + (size_t) t * NE);
    std::vector<int32_t> table_a, table_b;
    resident_table(rng, table_a, 300);   // mostly resident: the common case
    resident_table(rng, table_b, 40);    // mostly cold: every rank is a candidate

    float* d_logits = nullptr;
    int32_t* d_ids = nullptr;
    int32_t* d_res = nullptr;
    float* d_weights = nullptr;
    unsigned long long* d_stats = nullptr;
    if (cudaMalloc((void**) &d_logits, (size_t) n_tok * NE * 4) != cudaSuccess ||
        cudaMalloc((void**) &d_ids, (size_t) n_tok * K * 4) != cudaSuccess ||
        cudaMalloc((void**) &d_weights, (size_t) n_tok * K * 4) != cudaSuccess ||
        cudaMalloc((void**) &d_res, NE * 4) != cudaSuccess ||
        cudaMalloc((void**) &d_stats, 8 * sizeof(unsigned long long)) != cudaSuccess) {
        std::fprintf(stderr, "route_residency_parity: cudaMalloc failed (the GPU is busy?)\n");
        return 2;
    }
    if (cudaMemcpy(d_logits, logits.data(), (size_t) n_tok * NE * 4, cudaMemcpyHostToDevice) != cudaSuccess) {
        std::fprintf(stderr, "route_residency_parity: the upload failed\n");
        return 2;
    }

    int failures = 0;
    auto fail = [&](const std::string& what) { std::fprintf(stderr, "route_residency_parity: %s\n", what.c_str()); ++failures; };

    // 1. HYPERCORE_ROUTE_PRIOR=lambda against the reference, on a warm and a cold table.
    const std::vector<int32_t>* tables[2] = {&table_a, &table_b};
    for (int ti = 0; ti < 2; ++ti) {
        const std::vector<int32_t>& table = *tables[ti];
        int n_res = 0;
        for (int32_t v : table) n_res += v >= 0;
        if (cudaMemcpy(d_res, table.data(), NE * 4, cudaMemcpyHostToDevice) != cudaSuccess) { fail("upload"); break; }
        for (const float lambda : {0.25f, 3.0f, 25.0f}) {
            std::vector<int32_t> got((size_t) n_tok * K, -1), want((size_t) n_tok * K, -1);
            std::vector<float> gw((size_t) n_tok * K, 0.0f), ww((size_t) n_tok * K, 0.0f);
            try {
                route_prior_top10(d_logits, d_res, lambda, d_ids, d_weights, n_tok, nullptr);
            } catch (const std::exception& e) { fail(e.what()); continue; }
            if (cudaMemcpy(got.data(), d_ids, (size_t) n_tok * K * 4, cudaMemcpyDeviceToHost) != cudaSuccess ||
                cudaMemcpy(gw.data(), d_weights, (size_t) n_tok * K * 4, cudaMemcpyDeviceToHost) != cudaSuccess) {
                fail("readback"); break;
            }
            for (int t = 0; t < n_tok; ++t)
                ref_prior(logits.data() + (size_t) t * NE, table.data(), lambda,
                        want.data() + (size_t) t * K, ww.data() + (size_t) t * K);
            double worst = 0.0;
            bool ids_ok = true;
            for (int t = 0; t < n_tok; ++t) {
                for (int r = 0; r < K; ++r) ids_ok &= got[(size_t) t * K + r] == want[(size_t) t * K + r];
                worst = std::max(worst, rel_max(gw.data() + (size_t) t * K, ww.data() + (size_t) t * K, K));
            }
            if (!ids_ok || worst > 1e-6)
                fail("route prior lambda=" + std::to_string(lambda) + " on a " + std::to_string(n_res) + "-resident table");
            else
                std::printf("route prior: lambda=%g, %d resident experts - %d tokens match the reference (worst weight rel %.1e)\n",
                            lambda, n_res, n_tok, worst);
        }
    }

    // 2. lambda = 0 leaves the router's answer untouched.
    {
        std::vector<int32_t> seed((size_t) n_tok * K, 7), out((size_t) n_tok * K, 0);
        std::vector<float> seedw((size_t) n_tok * K, 0.5f);
        if (cudaMemcpy(d_ids, seed.data(), (size_t) n_tok * K * 4, cudaMemcpyDeviceToHost) != cudaSuccess ||
            cudaMemcpy(d_weights, seedw.data(), (size_t) n_tok * K * 4, cudaMemcpyDeviceToHost) != cudaSuccess) fail("setup");
        route_prior_top10(d_logits, d_res, 0.0f, d_ids, d_weights, n_tok, nullptr);
        if (cudaMemcpy(out.data(), d_ids, (size_t) n_tok * K * 4, cudaMemcpyDeviceToHost) != cudaSuccess) fail("readback");
        if (out != seed) fail("lambda=0 changed the ids");
        else std::printf("route prior: lambda=0 is a no-op\n");
    }

    // 3. HYPERCORE_ROUTE_RESIDENT=margin against the scalar reference, counters included.
    for (const float margin : {0.0f, 1.0f, 6.0f}) {
        std::vector<int32_t> seed((size_t) n_tok * K, -1);
        std::vector<float> seedw((size_t) n_tok * K, 0.0f);
        for (int t = 0; t < n_tok; ++t)   // start where the router would have left the picks
            ref_prior(logits.data() + (size_t) t * NE, table_a.data(), 0.0f,
                    seed.data() + (size_t) t * K, seedw.data() + (size_t) t * K);
        if (cudaMemcpy(d_res, table_a.data(), NE * 4, cudaMemcpyHostToDevice) != cudaSuccess ||
            cudaMemcpy(d_ids, seed.data(), (size_t) n_tok * K * 4, cudaMemcpyDeviceToHost) != cudaSuccess ||
            cudaMemcpy(d_weights, seedw.data(), (size_t) n_tok * K * 4, cudaMemcpyDeviceToHost) != cudaSuccess ||
            cudaMemset(d_stats, 0, 8 * sizeof(unsigned long long)) != cudaSuccess) { fail("setup"); break; }
        route_resident_swap(d_logits, d_ids, d_weights, d_res, n_tok, margin, 6, 9, d_stats, nullptr);
        std::vector<int32_t> got((size_t) n_tok * K, 0);
        std::vector<float> gw((size_t) n_tok * K, 0.0f);
        unsigned long long stats[8] = {};
        if (cudaMemcpy(got.data(), d_ids, (size_t) n_tok * K * 4, cudaMemcpyDeviceToHost) != cudaSuccess ||
            cudaMemcpy(gw.data(), d_weights, (size_t) n_tok * K * 4, cudaMemcpyDeviceToHost) != cudaSuccess ||
            cudaMemcpy(stats, d_stats, sizeof stats, cudaMemcpyDeviceToHost) != cudaSuccess) { fail("readback"); break; }
        long long tail = 0, swaps = 0, before = 0, after = 0;
        for (int t = 0; t < n_tok; ++t) {
            std::vector<int32_t> ids(seed.begin() + (size_t) t * K, seed.begin() + (size_t) t * K + K);
            std::vector<float> w(seedw.begin() + (size_t) t * K, seedw.begin() + (size_t) t * K + K);   // a token that
            // does not swap keeps the router's weights, so the reference starts from them too
            long long t2 = 0, s2 = 0, b2 = 0, a2 = 0;
            ref_resident(logits.data() + (size_t) t * NE, table_a.data(), ids.data(), w.data(), margin, 6, 9, t2, s2, b2, a2);
            for (int r = 0; r < K; ++r) if (got[(size_t) t * K + r] != ids[r]) {
                fail("route resident ids");
                if (failures <= 4) {   // a few concrete examples, so the difference can be read
                    std::fprintf(stderr, "  token %d rank %d: got %d want %d (logits got %.4f want %.4f)\n",
                                t, r, got[(size_t) t * K + r], ids[r],
                                logits[(size_t) t * NE + got[(size_t) t * K + r]],
                                logits[(size_t) t * NE + ids[r]]);
                }
                break;
            }
            if (rel_max(gw.data() + (size_t) t * K, w.data(), K) > 1e-6) fail("route resident weights");
            tail += t2; swaps += s2; before += b2; after += a2;
        }
        if (stats[0] != (unsigned long long) tail || stats[1] != (unsigned long long) swaps ||
            stats[2] != (unsigned long long) before || stats[3] != (unsigned long long) after)
            fail("the swap counters disagree with the reference");
        std::printf("route resident: margin=%g - %d tokens match, %lld tail entries, %lld swaps, non-resident %lld -> %lld\n",
                    margin, n_tok, tail, swaps, before, after);
    }

    // 4. An all-resident table swaps nothing and leaves the weights alone.
    {
        std::vector<int32_t> all_res(NE, 0);
        if (cudaMemcpy(d_res, all_res.data(), NE * 4, cudaMemcpyDeviceToHost) != cudaSuccess) fail("setup");
        std::vector<int32_t> seed((size_t) n_tok * K, 3), out((size_t) n_tok * K, 0);
        std::vector<float> seedw((size_t) n_tok * K, 0.11f), ow((size_t) n_tok * K, 0.0f);
        if (cudaMemcpy(d_ids, seed.data(), (size_t) n_tok * K * 4, cudaMemcpyDeviceToHost) != cudaSuccess ||
            cudaMemcpy(d_weights, seedw.data(), (size_t) n_tok * K * 4, cudaMemcpyDeviceToHost) != cudaSuccess) fail("setup");
        route_resident_swap(d_logits, d_ids, d_weights, d_res, n_tok, 2.0f, 0, 9, nullptr, nullptr);
        if (cudaMemcpy(out.data(), d_ids, (size_t) n_tok * K * 4, cudaMemcpyDeviceToHost) != cudaSuccess ||
            cudaMemcpy(ow.data(), d_weights, (size_t) n_tok * K * 4, cudaMemcpyDeviceToHost) != cudaSuccess) fail("readback");
        if (out != seed) fail("an all-resident table changed the picks");
        else if (rel_max(ow.data(), seedw.data(), (int) ow.size()) > 1e-9) fail("an all-resident table changed the weights");
        else std::printf("route resident: an all-resident table is a no-op\n");
    }

    if (bench) {
        double t_warp = 0.0, t_scalar = 0.0;
        std::vector<int32_t> seed((size_t) n_tok * K, -1);
        std::vector<float> seedw((size_t) n_tok * K, 0.0f);
        for (int t = 0; t < n_tok; ++t)
            ref_prior(logits.data() + (size_t) t * NE, table_a.data(), 0.0f,
                    seed.data() + (size_t) t * K, seedw.data() + (size_t) t * K);
        if (cudaMemcpy(d_res, table_a.data(), NE * 4, cudaMemcpyDeviceToHost) != cudaSuccess ||
            cudaMemcpy(d_ids, seed.data(), (size_t) n_tok * K * 4, cudaMemcpyDeviceToHost) != cudaSuccess) fail("setup");
        for (int rep = 0; rep < 20; ++rep) {
            auto t0 = std::chrono::steady_clock::now();
            route_resident_swap(d_logits, d_ids, d_weights, d_res, n_tok, 1.0f, 6, 9, nullptr, nullptr);
            cudaStreamSynchronize(0);
            t_warp += std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now() - t0).count();
            auto s0 = std::chrono::steady_clock::now();
            long long a = 0, b = 0, c = 0, d = 0;
            for (int t = 0; t < n_tok; ++t)
                ref_resident(logits.data() + (size_t) t * NE, table_a.data(),
                            seed.data() + (size_t) t * K, seedw.data() + (size_t) t * K, 1.0f, 6, 9, a, b, c, d);
            t_scalar += std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now() - s0).count();
        }
        std::printf("bench: %d tokens swapped in %.3f ms on the GPU, the scalar reference %.3f ms on the CPU\n",
                    n_tok, t_warp / 20.0, t_scalar / 20.0);
    }

    cudaFree(d_logits); cudaFree(d_ids); cudaFree(d_weights); cudaFree(d_res); cudaFree(d_stats);
    if (failures) { std::printf("route_residency_parity: %d failures\n", failures); return 1; }
    std::printf("route_residency_parity: ok\n");
    return 0;
}
