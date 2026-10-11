// tests/core/pin_order_test.cpp - #1: the host arena's pin order follows the routing profile, not the file.
//
// Two contracts, both of which the engine depends on:
//
//   1. `hot_layer_order` turns a ranked (layer, expert) profile into the slice order the arena should register.
//      Pure CPU code; runs everywhere.
//   2. `PinnedArena` honours that order: when the registration is capped, the slices it takes are the ones the
//      order put first, the flags say WHICH of them were taken (not how many), and the slices it did not take
//      are still kept resident by the working-set lock. That half needs a CUDA device, so it is skipped - not
//      failed - where there is none, the same way the other device tests are.
#include "hypercore/core/expert_cache.hpp"
#include "hypercore/core/pinned.hpp"

#include <cuda_runtime.h>

#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>

namespace {
bool eq(const std::vector<uint64_t>& a, const std::vector<uint64_t>& b) { return a == b; }

void fail(const char* what, const std::vector<uint64_t>& got) {
    std::fprintf(stderr, "pin_order_test: %s\n", what);
    std::fprintf(stderr, "got:");
    for (uint64_t x : got) std::fprintf(stderr, " %llu", (unsigned long long) x);
    std::fprintf(stderr, "\n");
    std::exit(1);
}

int fails = 0;
#define CHECK(c) do { if (!(c)) { std::fprintf(stderr, "pin_order_test FAIL %s:%d: %s\n", __FILE__, __LINE__, #c); ++fails; } } while (0)

}  // namespace

int main(int argc, char** argv) {
    // ---- 1. the ordering function ----
    // No profile: no order. The caller keeps the old arena-order behaviour.
    if (!eq(hypercore::core::hot_layer_order({}, 4, 2), {}))
        fail("an empty profile must produce an empty order", hypercore::core::hot_layer_order({}, 4, 2));

    // A layer's weight is the sum of its experts' rank distances. Here layer 2 has the two hottest pairs,
    // layer 0 the next, layer 1 the last.
    std::vector<std::pair<int32_t, int32_t>> ranked = {{2, 0}, {2, 1}, {0, 0}, {1, 0}};
    if (!eq(hypercore::core::hot_layer_order(ranked, 3, 2), {2, 0, 1}))
        fail("hottest layers must come first", hypercore::core::hot_layer_order(ranked, 3, 2));

    // Equal heat keeps arena order. This is what makes a profile that says nothing about some layers safe:
    // those layers are not moved ahead of each other. Layer 2 is hotter than 0 and 1, which are tied - the
    // tie must not be broken by the sort.
    std::vector<std::pair<int32_t, int32_t>> tied = {{2, 0}, {2, 1}, {0, 0}, {1, 0}, {0, 1}, {1, 1}};
    if (!eq(hypercore::core::hot_layer_order(tied, 3, 2), {2, 0, 1}))
        fail("equal heat must preserve arena order", hypercore::core::hot_layer_order(tied, 3, 2));

    // Out-of-range pairs are ignored rather than poisoning the order.
    std::vector<std::pair<int32_t, int32_t>> bad = {{9, 0}, {1, 0}, {0, 0}};
    if (!eq(hypercore::core::hot_layer_order(bad, 2, 2), {1, 0}))
        fail("out-of-range pairs must be ignored", hypercore::core::hot_layer_order(bad, 2, 2));

    // Degenerate geometry returns empty instead of indexing a zero-size vector.
    if (!eq(hypercore::core::hot_layer_order({{0, 0}}, 0, 2), {}))
        fail("zero layers must produce an empty order", hypercore::core::hot_layer_order({{0, 0}}, 0, 2));
    if (!eq(hypercore::core::hot_layer_order({{0, 0}}, 2, 0), {}))
        fail("zero experts must produce an empty order", hypercore::core::hot_layer_order({{0, 0}}, 2, 0));

    // ---- 1b. the flat-profile guard ----
    // A capped pin covers a fixed number of bytes, so the order only pays when the heat is concentrated. The
    // profile this node actually runs (data/expert-profile.bin: 48 layers, 512 experts each) is flat: its best
    // prefix is 1.6% better than layers 0..k. Ordering it would scatter the tail lock for nothing, so the
    // function must return an empty order and the arena must keep the pin it already had.
    {
        std::vector<std::pair<int32_t, int32_t>> flat;
        for (int l = 0; l < 12; ++l) for (int e = 0; e < 4; ++e) flat.push_back({l, e});
        if (!eq(hypercore::core::hot_layer_order(flat, 12, 4), {}))
            fail("a flat profile must produce no order", hypercore::core::hot_layer_order(flat, 12, 4));
    }
    // The measured spread, reproduced: layers at 1.155 and 0.831 of the mean, best prefix gain 1.6%.
    {
        const double w[16] = {1.155, 1.116, 1.096, 1.095, 1.089, 1.087, 1.071, 1.065,
                              1.059, 1.055, 1.053, 1.050, 0.920, 0.918, 0.914, 0.831};
        std::vector<std::pair<int32_t, int32_t>> spread;
        // rank the pairs so each layer's pairs sit at the position its weight implies
        std::vector<int> layer(16);
        for (int i = 0; i < 16; ++i) layer[i] = i;
        std::stable_sort(layer.begin(), layer.end(), [&](int a, int b) { return w[a] > w[b]; });
        for (int r = 0; r < 16; ++r)
            for (int e = 0; e < 4; ++e) spread.push_back({layer[r], e});
        if (!eq(hypercore::core::hot_layer_order(spread, 16, 4), {}))
            fail("a profile with a 1.6% best-prefix gain is flat and must produce no order",
                hypercore::core::hot_layer_order(spread, 16, 4));
    }
    // A concentrated profile is ordered: four of sixteen layers carry most of the heat.
    {
        std::vector<std::pair<int32_t, int32_t>> conc;
        for (int l = 12; l < 16; ++l) for (int e = 0; e < 4; ++e) conc.push_back({l, e});
        for (int l = 0; l < 12; ++l) for (int e = 0; e < 4; ++e) conc.push_back({l, e});
        const std::vector<uint64_t> o = hypercore::core::hot_layer_order(conc, 16, 4);
        if (o.empty()) fail("a concentrated profile must produce an order", o);
        for (int i = 0; i < 4; ++i) CHECK(o[(size_t) i] >= 12);
    }

    // ---- 1c. the profile this node actually runs ----
    // Passed as argv[1] by CMake. If it is present, the guard must reject it: the measured best-prefix gain of
    // data/expert-profile.bin is 1.6%, under PIN_ORDER_MIN_GAIN. This is the case that decides whether #1 is
    // worth shipping, so it is asserted rather than printed.
    if (argc > 1) {
        // the header carries the geometry, so read it directly rather than guessing it
        std::FILE* f = std::fopen(argv[1], "rb");
        if (f) {
            unsigned char hdr[24];
            if (std::fread(hdr, 1, 24, f) == 24) {
                uint32_t ver = 0, nl = 0, ne = 0, np = 0;
                std::memcpy(&ver, hdr + 4, 4); std::memcpy(&nl, hdr + 8, 4);
                std::memcpy(&ne, hdr + 12, 4); std::memcpy(&np, hdr + 16, 4);
                (void) ver;
                std::vector<std::pair<int32_t, int32_t>> pairs((size_t) np);
                for (uint32_t i = 0; i < np; ++i) {
                    unsigned short l, e;
                    if (std::fread(&l, 1, 2, f) != 2 || std::fread(&e, 1, 2, f) != 2) break;
                    pairs[i] = {l, e};
                }
                std::fclose(f);
                const std::vector<uint64_t> o = hypercore::core::hot_layer_order(pairs, (int64_t) nl, (int64_t) ne);
                std::printf("pin_order_test: %s has %u layers; the guard %s (PIN_ORDER_MIN_GAIN=%.2f)\n",
                            argv[1], nl, o.empty() ? "dropped the order: the layer heat is flat" : "kept it",
                            hypercore::core::PIN_ORDER_MIN_GAIN);
                CHECK(o.empty());   // this profile is flat; ordering its pin would change nothing
            } else {
                std::fclose(f);
            }
        }
    }

    // ---- 2. the registration ----
    int devices = 0;
    if (cudaGetDeviceCount(&devices) != cudaSuccess || devices == 0) {
        std::printf("pin_order_test: ordering contract ok; no CUDA device, the registration path is not exercised\n");
        return fails ? 1 : 0;
    }
    // cudaHostRegister needs a little device memory for the mapping itself. An engine already holding the whole
    // card leaves none, and every registration below would fail for a reason that has nothing to do with the
    // order. Skip rather than fail, the same way the other device tests do.
    //
    // `cudaMemGetInfo`'s free bytes are not the test. A driver whose pinned-memory pool is already taken by
    // another process refuses a registration with MiB still free on the card - which is exactly what a running
    // engine does. So ask the driver: register 1 MiB, and if that alone is refused, nothing below can be
    // measured and the registration half of this test is skipped.
    size_t free_mem = 0, total_mem = 0;
    if (cudaMemGetInfo(&free_mem, &total_mem) != cudaSuccess) free_mem = 0;
    const uint64_t probe_bytes = 1ull << 20;
    void* probe = std::malloc(probe_bytes);
    bool can_register = false;
    if (probe) {
        std::memset(probe, 0, probe_bytes);   // registration pins what is resident now; touch it first
        can_register = cudaHostRegister(probe, probe_bytes, cudaHostRegisterPortable) == cudaSuccess;
        if (can_register) cudaHostUnregister(probe);
        (void) cudaGetLastError();
        std::free(probe);
    }
    if (!can_register) {
        std::printf("pin_order_test: ordering contract ok; the device (%zu MiB free) refused a 1 MiB "
                   "registration - the registration path is not exercised\n", free_mem >> 20);
        return fails ? 1 : 77;
    }

    const uint64_t MiB = 1ull << 20;
    const int n = 4;
    std::vector<uint64_t> bounds;
    for (int i = 0; i < n; ++i) bounds.push_back((uint64_t) i * MiB);
    bounds.push_back((uint64_t) n * MiB);

    // (a) no cap: one registration of the whole arena. No flags are needed, and every slice reads as pinned.
    {
        hypercore::core::PinnedArena all((uint64_t) n * MiB, bounds);
        CHECK(all.valid());
        CHECK(all.registered_bytes == (uint64_t) n * MiB);
        CHECK(all.registered.empty());
        for (int i = 0; i < n; ++i) CHECK(all.slice_registered((size_t) i));
    }

    // (b) a cap with no order: the old behaviour, a prefix. Layers 0..k, whatever the run reads.
    {
        hypercore::core::PinnedArena plain((uint64_t) n * MiB, bounds, 2 * MiB);
        CHECK(plain.valid());
        CHECK(plain.registered_slices == 2);
        CHECK(plain.registered_bytes == 2 * MiB);          // a prefix: the total is the prefix's end
        CHECK(plain.slice_registered(0) && plain.slice_registered(1));
        CHECK(!plain.slice_registered(2) && !plain.slice_registered(3));
    }

    // (c) the same cap, the hot layers first: the pin covers the read layers. `registered_bytes` is a total now,
    // not a prefix, so the flags are the only way to know which layers are DMA-registered.
    {
        const std::vector<uint64_t> order = hypercore::core::hot_layer_order({{3, 0}, {3, 1}, {1, 0}}, n, 2);
        if (!eq(order, {3, 1, 0, 2})) fail("the profile must order the layers hottest first", order);
        hypercore::core::PinnedArena hot((uint64_t) n * MiB, bounds, 2 * MiB, std::string{}, 0, order);
        CHECK(hot.valid());
        CHECK(hot.registered_slices == 2);
        CHECK(hot.registered_bytes == 2 * MiB);
        CHECK(hot.slice_registered(3) && hot.slice_registered(1));
        CHECK(!hot.slice_registered(0) && !hot.slice_registered(2));
        // The slices CUDA did not take must still be resident, one at a time: an ordered pin leaves them
        // scattered, so the single tail lock cannot cover them.
        if (hot.backing != hypercore::core::PageBacking::LargePages)
            CHECK(hot.locked_bytes == 2 * MiB);
        CHECK(!hot.slice_bounds.empty());
        if (!hot.note.empty()) std::printf("pin_order_test: arena note: %s\n", hot.note.c_str());
    }

    // (d) a slice that does not fit the remaining cap is skipped, not fatal. Sizes [4,1,1] MiB, cap 2 MiB: the
    // first slice is too big on its own, and the two smaller ones after it still get pinned. Before #634 the
    // loop broke at the first slice that did not fit and nothing after it was registered.
    {
        std::vector<uint64_t> uneven = {0, 4 * MiB, 5 * MiB, 6 * MiB};
        hypercore::core::PinnedArena a(6 * MiB, uneven, 2 * MiB, std::string{}, 0, {0, 1, 2});
        CHECK(a.valid());
        CHECK(a.registered_slices == 2);
        CHECK(!a.slice_registered(0) && a.slice_registered(1) && a.slice_registered(2));
        CHECK(a.registered_bytes == 2 * MiB);
    }

    // (e) an order that repeats or names out-of-range slices does not register a slice twice.
    {
        hypercore::core::PinnedArena a((uint64_t) n * MiB, bounds, 3 * MiB, std::string{}, 0, {2, 2, 9, 1});
        CHECK(a.valid());
        CHECK(a.registered_slices == 3);
        CHECK(a.slice_registered(2) && a.slice_registered(1) && a.slice_registered(0) && !a.slice_registered(3));
    }

    std::printf("pin_order_test: %s\n", fails ? "FAILED" : "ok");
    return fails ? 1 : 0;
}
