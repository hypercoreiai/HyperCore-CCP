// tests/core/pinned_ring_test.cpp - #1996: the pinned bounce ring behind the prompt path's pageable uploads.
//
// What the ring promises, and what this test checks:
//   1. h2d() from a pageable source: the bytes reach the device even though the caller overwrites its source the
//      moment the call returns (a plain pageable cudaMemcpyAsync does not make that promise).
//   2. The slots are reused safely: a slot is refilled only after the copy that last read it has finished, so a
//      burst of uploads through a 4-slot ring still lands every one of them.
//   3. acquire()/submit() is the gather form the image path uses: many rows into one slot, one DMA.
//   4. d2h_sync() leaves the bytes in a pageable host buffer on return.
//   5. With no pinned RAM, or HYPERCORE_TEST_PAGEABLE=1, every path still produces the same bytes.
//   6. A ring belongs to one device: on a second device acquire() hands out nothing and the copy goes direct.
#include "hypercore/core/pinned_ring.hpp"

#include <cuda_runtime.h>

#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>

using hypercore::core::PinnedRing;

static int fails = 0;
#define CHECK(c) do { if (!(c)) { std::fprintf(stderr, "FAIL %s:%d: %s\n", __FILE__, __LINE__, #c); ++fails; } } while (0)

static void fill(std::vector<uint8_t>& v, int seed) {
    for (size_t i = 0; i < v.size(); ++i) v[i] = (uint8_t) ((i * 2654435761u + (size_t) seed * 101u) & 0xffu);
}

int main() {
    if (cudaFree(nullptr) != cudaSuccess) {
        std::printf("pinned_ring_test: no CUDA device - skipped\n");
        return 0;
    }
    const bool forced = std::getenv("HYPERCORE_TEST_PAGEABLE") != nullptr;
    std::printf("pinned_ring_test: %s\n", forced ? "pageable forced (HYPERCORE_TEST_PAGEABLE=1)" : "pinned ring");

    // 1. a pageable source is free to change the moment h2d returns
    {
        const size_t n = 1u << 20;
        std::vector<uint8_t> src(n), back(n);
        fill(src, 1);
        void* dst = nullptr;
        CHECK(cudaMalloc(&dst, n) == cudaSuccess);
        PinnedRing ring;
        CHECK(ring.h2d(dst, src.data(), n, nullptr) == cudaSuccess);
        fill(src, 2);                       // the caller reuses its buffer at once
        CHECK(cudaStreamSynchronize(nullptr) == cudaSuccess);
        CHECK(cudaMemcpy(back.data(), dst, n, cudaMemcpyDeviceToHost) == cudaSuccess);
        CHECK(std::memcmp(back.data(), src.data(), n) != 0);   // the device kept the OLD bytes
        for (size_t i = 0; i < n; ++i) {
            if (back[i] != (uint8_t) ((i * 2654435761u + 101u) & 0xffu)) {
                std::fprintf(stderr, "FAIL: byte %zu is %u, expected the first pattern\n", i, back[i]);
                ++fails;
                break;
            }
        }
        cudaFree(dst);
    }

    // 2. more uploads than slots: every one lands, in order, through the ring
    {
        constexpr int k = 8;
        const size_t n = 4096;
        void* dst[k] = {};
        for (int i = 0; i < k; ++i) CHECK(cudaMalloc(&dst[i], n) == cudaSuccess);
        std::vector<uint8_t> src(n);
        PinnedRing ring;
        for (int i = 0; i < k; ++i) {
            fill(src, i);
            CHECK(ring.h2d(dst[i], src.data(), n, nullptr) == cudaSuccess);
            fill(src, 100 + i);            // overwritten before the DMA has run
        }
        CHECK(cudaDeviceSynchronize() == cudaSuccess);
        for (int i = 0; i < k; ++i) {
            std::vector<uint8_t> back(n);
            CHECK(cudaMemcpy(back.data(), dst[i], n, cudaMemcpyDeviceToHost) == cudaSuccess);
            for (size_t j = 0; j < n; ++j) {
                if (back[j] != (uint8_t) ((j * 2654435761u + (size_t) i * 101u) & 0xffu)) {
                    std::fprintf(stderr, "FAIL: upload %d byte %zu came through wrong\n", i, j);
                    ++fails;
                    break;
                }
            }
            cudaFree(dst[i]);
        }
    }

    // 3. acquire()/submit(): a run of rows gathered into one slot and uploaded as one copy
    {
        const size_t row = 1024, rows = 3;
        void* dst = nullptr;
        CHECK(cudaMalloc(&dst, row * rows) == cudaSuccess);
        PinnedRing ring;
        void* stage = ring.acquire(row * rows);
        if (stage == nullptr) {
            std::printf("pinned_ring_test: no pinned slot could be had, the gather goes direct\n");
            std::vector<uint8_t> all(row * rows);
            for (size_t r = 0; r < rows; ++r) {
                std::vector<uint8_t> one(row);
                fill(one, (int) r);
                std::memcpy(&all[r * row], one.data(), row);
            }
            CHECK(PinnedRing::direct(dst, all.data(), row * rows, nullptr) == cudaSuccess);
        } else {
            for (size_t r = 0; r < rows; ++r) {
                std::vector<uint8_t> one(row);
                fill(one, (int) r);
                std::memcpy((char*) stage + r * row, one.data(), row);   // each row's source is a dead stack buffer
            }
            CHECK(ring.submit(dst, stage, row * rows, nullptr) == cudaSuccess);
        }
        CHECK(cudaStreamSynchronize(nullptr) == cudaSuccess);
        std::vector<uint8_t> back(row * rows);
        CHECK(cudaMemcpy(back.data(), dst, row * rows, cudaMemcpyDeviceToHost) == cudaSuccess);
        for (size_t r = 0; r < rows; ++r)
            for (size_t j = 0; j < row; ++j)
                if (back[r * row + j] != (uint8_t) ((j * 2654435761u + r * 101u) & 0xffu)) {
                    std::fprintf(stderr, "FAIL: gathered row %zu byte %zu wrong\n", r, j);
                    ++fails;
                    break;
                }
        cudaFree(dst);
    }

    // 4. d2h_sync into a pageable host buffer
    {
        const size_t n = 65536;
        std::vector<uint8_t> src(n), back(n, 0);
        fill(src, 7);
        void* dev = nullptr;
        CHECK(cudaMalloc(&dev, n) == cudaSuccess);
        CHECK(cudaMemcpy(dev, src.data(), n, cudaMemcpyHostToDevice) == cudaSuccess);
        PinnedRing ring;
        CHECK(ring.d2h_sync(back.data(), dev, n, nullptr) == cudaSuccess);
        CHECK(std::memcmp(back.data(), src.data(), n) == 0);
        CHECK(ring.d2h_sync(back.data(), dev, 0, nullptr) == cudaSuccess);
        cudaFree(dev);
    }

    // 5. an empty upload is a no-op, not an error
    {
        PinnedRing ring;
        CHECK(ring.h2d(nullptr, nullptr, 0, nullptr) == cudaSuccess);
        CHECK(PinnedRing::direct(nullptr, nullptr, 0, nullptr) == cudaSuccess);
    }

    // 6. release() frees the slots and the ring is usable again
    {
        PinnedRing ring;
        const size_t n = 4096;
        void* dst = nullptr;
        CHECK(cudaMalloc(&dst, n) == cudaSuccess);
        std::vector<uint8_t> src(n);
        fill(src, 3);
        CHECK(ring.h2d(dst, src.data(), n, nullptr) == cudaSuccess);
        ring.release();                       // slots freed, the ring is usable again
        fill(src, 4);
        CHECK(ring.h2d(dst, src.data(), n, nullptr) == cudaSuccess);
        CHECK(cudaStreamSynchronize(nullptr) == cudaSuccess);
        std::vector<uint8_t> back(n);
        CHECK(cudaMemcpy(back.data(), dst, n, cudaMemcpyDeviceToHost) == cudaSuccess);
        for (size_t i = 0; i < n; ++i)
            if (back[i] != (uint8_t) ((i * 2654435761u + 404u) & 0xffu)) {
                std::fprintf(stderr, "FAIL: after release() byte %zu is %u\n", i, back[i]);
                ++fails;
                break;
            }
        cudaFree(dst);
    }

    int devices = 0;
    if (cudaGetDeviceCount(&devices) == cudaSuccess && devices > 1) {
        PinnedRing ring;
        void* dst0 = nullptr, *dst1 = nullptr;
        CHECK(cudaMalloc(&dst0, 4096) == cudaSuccess);
        std::vector<uint8_t> src(4096), back(4096);
        CHECK(cudaSetDevice(1) == cudaSuccess);
        CHECK(cudaMalloc(&dst1, 4096) == cudaSuccess);
        fill(src, 5);
        CHECK(ring.h2d(dst1, src.data(), 4096, nullptr) == cudaSuccess);   // the ring takes device 1
        CHECK(cudaSetDevice(0) == cudaSuccess);
        fill(src, 6);
        CHECK(ring.h2d(dst0, src.data(), 4096, nullptr) == cudaSuccess);   // goes direct, still correct
        CHECK(cudaDeviceSynchronize() == cudaSuccess);
        CHECK(cudaMemcpy(back.data(), dst0, 4096, cudaMemcpyDeviceToHost) == cudaSuccess);
        for (size_t i = 0; i < 4096; ++i)
            if (back[i] != (uint8_t) ((i * 2654435761u + 606u) & 0xffu)) {
                std::fprintf(stderr, "FAIL: the second device's direct upload byte %zu is %u\n", i, back[i]);
                ++fails;
                break;
            }
        cudaFree(dst0);
        CHECK(cudaSetDevice(1) == cudaSuccess);
        cudaFree(dst1);
        CHECK(cudaSetDevice(0) == cudaSuccess);
    }

    if (fails) {
        std::fprintf(stderr, "pinned_ring_test: %d FAILURES\n", fails);
        return 1;
    }
    std::printf("pinned_ring_test: ok\n");
    return 0;
}
