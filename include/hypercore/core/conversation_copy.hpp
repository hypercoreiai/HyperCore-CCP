// include/hypercore/core/conversation_copy.hpp - #2049 #2065 #1971: the copies that park a conversation, told to
// the #29 watchdog.
//
// Parking a conversation moves its running checkpoints and K/V into ordinary pageable host memory, and that stretch
// is silent: the heartbeat has no token, no prompt chunk and no verify window in it.  When the OS has written that
// memory to the pagefile the copy runs at the drive's page-in speed (the reports measured ~190 hard faults a
// second, under 1 MB/s) and one memcpy of it stands still past the 60 s limit, so the watchdog ended an engine that
// was only slow.  One beat per 1 MiB slice keeps a copy that moves alive and still lets a real stall show.
//
// HYPERCORE_TEST_SLOW_COPY_US=N (tests only): every 1 MiB slice of a checkpoint copy takes N microseconds more, as
// when the OS has paged the checkpoints out and each slice is read back from the drive.  Unset: no delay.
#pragma once

#include "hypercore/core/conversation_cache.hpp"
#include "hypercore/core/progress.hpp"

#include <algorithm>
#include <chrono>
#include <cstddef>
#include <cstdlib>
#include <thread>
#include <vector>

namespace hypercore::core::conversation_detail {

inline long test_slow_copy_us() {
    // Read every call: a test sets the variable between two copies, and a cached value would hide the second one.
    const char* e = std::getenv("HYPERCORE_TEST_SLOW_COPY_US");
    return e ? std::atol(e) : 0L;
}

// A copy of `src` that beats as it goes, one 1 MiB slice at a time.
template<class T>
inline std::vector<T> copy_beating(const std::vector<T>& src) {
    std::vector<T> out;
    out.reserve(src.size());
    const size_t step = std::max<size_t>(1, ((size_t) 1 << 20) / sizeof(T));
    for (size_t at = 0; at < src.size(); at += step) {
        out.insert(out.end(), src.begin() + (std::ptrdiff_t) at,
                   src.begin() + (std::ptrdiff_t) std::min(src.size(), at + step));
        if (const long us = test_slow_copy_us(); us > 0)
            std::this_thread::sleep_for(std::chrono::microseconds(us));
        core::progress_beat();
    }
    return out;
}

inline ConversationCheckpoint copy_checkpoint_beating(const ConversationCheckpoint& c) {
    ConversationCheckpoint o;
    o.ids = copy_beating(c.ids);
    o.imgs = copy_beating(c.imgs);
    o.gdn = copy_beating(c.gdn);
    o.ple = copy_beating(c.ple);
    o.tails = copy_beating(c.tails);
    o.dead = copy_beating(c.dead);
    o.block_pos = copy_beating(c.block_pos);
    o.used = c.used;
    o.stage_parts.reserve(c.stage_parts.size());
    for (const auto& part : c.stage_parts) o.stage_parts.push_back(copy_checkpoint_beating(part));
    return o;
}

inline std::vector<ConversationCheckpoint> copy_checkpoints_beating(const std::vector<ConversationCheckpoint>& cs) {
    std::vector<ConversationCheckpoint> out;
    out.reserve(cs.size());
    for (const auto& c : cs) out.push_back(copy_checkpoint_beating(c));
    return out;
}

}  // namespace hypercore::core::conversation_detail
