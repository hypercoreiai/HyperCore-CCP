// src/platform/file_tier.cpp - see include/hypercore/platform/file_tier.hpp (#1407 #1984 #1971)
#include "hypercore/platform/file_tier.hpp"

#include <cstdio>
#include <cstring>

#if defined(_WIN32)
#include <windows.h>
#include <psapi.h>
#pragma comment(lib, "psapi.lib")
#endif

namespace hypercore::platform {

uint64_t file_tier_activity() {
#if defined(__linux__)
    uint64_t total = 0;
    // /proc/self/stat: after the closing paren of the command name comes
    // state ppid pgrp session tty tpgid flags minflt cminflt majflt - the hard faults only.
    if (std::FILE* f = std::fopen("/proc/self/stat", "r")) {
        char buf[1024] = {};
        const size_t n = std::fread(buf, 1, sizeof buf - 1, f);
        std::fclose(f);
        const char* p = std::strrchr(buf, ')');
        if (p != nullptr && n > 0) {
            unsigned long long majflt = 0;
            if (std::sscanf(p + 2, "%*c %*d %*d %*d %*d %*d %*u %*u %*u %llu", &majflt) == 1) total += majflt;
        }
    }
    // /proc/self/io: read_bytes is bytes actually taken from the storage layer, not from the page cache.
    if (std::FILE* f = std::fopen("/proc/self/io", "r")) {
        char line[256];
        while (std::fgets(line, sizeof line, f) != nullptr) {
            unsigned long long v = 0;
            if (std::sscanf(line, "read_bytes: %llu", &v) == 1) total += v >> 20;   // MiB
        }
        std::fclose(f);
    }
    return total;
#elif defined(_WIN32)
    // #1984 #1971: Windows had no measure here, so a prompt waiting on mapped-file page-ins never got the
    // allowance.  Bytes read (MiB) plus page faults / 8: a host that pages hard faults from the pagefile at
    // ~200 a second (#2049: 190/s, one thread waiting on one page at a time), which at /64 is 3 a second and
    // never counts as busy.  Windows counts soft faults too; a stuck engine makes almost none.
    uint64_t total = 0;
    IO_COUNTERS io{};
    if (GetProcessIoCounters(GetCurrentProcess(), &io)) total += io.ReadTransferCount >> 20;
    PROCESS_MEMORY_COUNTERS pmc{};
    if (K32GetProcessMemoryInfo(GetCurrentProcess(), &pmc, sizeof pmc)) total += pmc.PageFaultCount >> 3;
    return total;
#else
    return 0;
#endif
}

}  // namespace hypercore::platform
