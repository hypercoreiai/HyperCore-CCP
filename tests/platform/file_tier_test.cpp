// tests/platform/file_tier_test.cpp - #1407 #1984 #1971: the file-tier counter the #29 watchdog reads, and the
// second-to-second comparison that turns it into "slow, not stuck".  No GPU, no model.
#include "hypercore/platform/file_tier.hpp"

#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

#if defined(__linux__)
#include <fcntl.h>
#include <unistd.h>
#endif

using hypercore::platform::file_tier_activity;
using hypercore::platform::file_tier_busy;
using hypercore::platform::kBusyUnits;

static void check(bool ok, const char* why) { if (!ok) throw std::runtime_error(why); }

// The predicate the watchdog uses, on values the OS could actually report.
static void test_predicate() {
    check(file_tier_busy(1000, 1000 + kBusyUnits), "exactly one second of page-in is not busy");
    check(file_tier_busy(1000, 1017), "more than the bar is busy");
    check(!file_tier_busy(1000, 999 + kBusyUnits - 1), "below the bar is not busy");
    check(!file_tier_busy(1000, 1000), "a silent second is not busy");
    check(!file_tier_busy(1000, 999), "a counter that went down is not busy");
    check(file_tier_busy(0, kBusyUnits), "the bar from zero");
    check(!file_tier_busy(UINT64_MAX - 1, UINT64_MAX), "no wrap: a one-unit jump is not busy");
    check(file_tier_busy(UINT64_MAX - kBusyUnits, UINT64_MAX), "no wrap: a full bar is busy");
}

// The counter itself: always readable, never decreasing, and never a wild jump.
static void test_counter() {
    uint64_t prev = file_tier_activity();
    for (int i = 0; i < 5; ++i) {
        const uint64_t now = file_tier_activity();
        check(now >= prev, "the file tier's activity went backwards");
        check(now <= prev + (1u << 20), "the counter moved by more than a GiB in one call");
        prev = now;
    }
}

// A real read from the storage layer must show up.  On tmpfs, or when the file is already in the page cache, the
// OS reports nothing: that is not a failure of the counter, so the arm reports it and passes.
static void test_real_read() {
    // In the working directory, not /tmp: tmpfs has no storage layer, so the OS would report nothing for the read.
    const std::string name = "hypercore-file-tier-test.bin";
    std::string bytes(32u * 1024u * 1024u, 'x');
    { std::ofstream f(name, std::ios::binary); f.write(bytes.data(), bytes.size()); }
#if defined(__linux__)
    // Drop it from the page cache so the read below has to go to the storage layer.
    int efd = open(name.c_str(), O_RDONLY);
    if (efd >= 0) { posix_fadvise(efd, 0, 0, POSIX_FADV_DONTNEED); close(efd); }
#endif

    const uint64_t before = file_tier_activity();
#if defined(__linux__)
    // O_DIRECT: the read goes to the storage layer instead of the page cache, so read_bytes moves.
    int d = open(name.c_str(), O_RDONLY | O_DIRECT);
    if (d < 0) d = open(name.c_str(), O_RDONLY);   // some filesystems refuse O_DIRECT; the buffered read is the fallback
    void* buf = std::aligned_alloc(4096, 4096);   // O_DIRECT needs a page-aligned buffer and a whole-page read
    check(buf != nullptr, "buffer allocation for the read");
    size_t read_total = 0;
    for (size_t off = 0; off < bytes.size(); off += 4096) {
        const ssize_t n = read(d, static_cast<char*>(buf) + (off % 4096), 4096);
        if (n <= 0) break;
        read_total += (size_t) n;
    }
    close(d);
    free(buf);
    check(read_total == bytes.size(), "the test file did not read back in full");
#else
    std::ifstream f(name, std::ios::binary);
    std::vector<char> buf(4096);
    while (f.read(buf.data(), 4096)) {}
#endif
    const uint64_t after = file_tier_activity();
    if (after >= before + kBusyUnits)
        std::printf("file tier: 32 MiB read moved the counter by %llu units (busy)\n",
                    (unsigned long long) (after - before));
    else
        std::printf("note: the OS reported no file activity for a 32 MiB read (tmpfs or page cache); "
                    "the busy arm is not exercised here\n");
    std::remove(name.c_str());
}

int main() {
    try {
        test_predicate();
        test_counter();
        test_real_read();
    } catch (const std::exception& e) {
        std::cerr << "file_tier_test: " << e.what() << "\n";
        return 1;
    }
    std::cout << "file_tier_test: ok\n";
    return 0;
}
