// tests/core/conversation_copy_test.cpp - #2049 #2065 #1971: the parked-conversation copies beat the #29 watchdog.
// No GPU, no model: the beats are counted in the same Progress the watchdog thread reads.
#include "hypercore/core/conversation_copy.hpp"
#include "hypercore/core/progress.hpp"

#include <chrono>
#include <cstdlib>
#include <iostream>
#include <stdexcept>
#include <vector>

using hypercore::core::progress;
using hypercore::core::ConversationCheckpoint;
using hypercore::core::conversation_detail::copy_beating;
using hypercore::core::conversation_detail::copy_checkpoints_beating;

static void check(bool ok, const char* why) { if (!ok) throw std::runtime_error(why); }

// A checkpoint big enough to cross several 1 MiB slices: 4 MiB of ids, 2 MiB of tails.
static ConversationCheckpoint make_checkpoint(size_t n_ids, size_t n_tails, int depth = 0) {
    ConversationCheckpoint c;
    c.ids.resize(n_ids);
    for (size_t i = 0; i < n_ids; ++i) c.ids[i] = (int32_t) (i % 1000);
    c.gdn.assign(n_tails, 7);
    c.tails.assign(n_tails, 3);
    c.block_pos.assign(n_tails, 11);
    c.used = 42;
    if (depth < 1) c.stage_parts.push_back(make_checkpoint(16, 8, depth + 1));   // a layer-split part, one level deep
    return c;
}

int main() {
    try {
        // 1. The copy is the same bytes, in the same order, including the nested stage parts.
        ConversationCheckpoint src = make_checkpoint(1u << 21, 1u << 21);
        ConversationCheckpoint out = copy_checkpoints_beating({src})[0];
        check(out.ids == src.ids, "ids changed");
        check(out.gdn == src.gdn, "gdn changed");
        check(out.tails == src.tails, "tails changed");
        check(out.block_pos == src.block_pos, "block_pos changed");
        check(out.used == src.used, "the LRU stamp changed");
        check(out.stage_parts.size() == src.stage_parts.size(), "a stage part was lost");
        check(out.stage_parts[0].ids == src.stage_parts[0].ids, "a stage part's ids changed");

        // 2. Every 1 MiB slice is a beat. ids: 2 MiB = 2 slices; gdn/tails/block_pos: 2 MiB each = 2 slices each;
        // the nested part adds its own. The watchdog only needs a beat per second, so a count this large is the point.
        progress().beats.store(0);
        copy_checkpoints_beating({src});
        const uint64_t beats = progress().beats.load();
        check(beats >= 12, "a 10 MiB checkpoint copy made fewer than 12 beats");

        // 3. An empty copy makes no beat and no allocation work.
        progress().beats.store(0);
        check(copy_beating(std::vector<int32_t>{}).empty(), "an empty copy is not empty");
        check(progress().beats.load() == 0, "an empty copy beat");

        // 4. HYPERCORE_TEST_SLOW_COPY_US makes the copy as slow as a page-in, and the beats still come: this is the
        // #2049 repro the watchdog allowance is tested against.
        setenv("HYPERCORE_TEST_SLOW_COPY_US", "1000", 1);
        const auto t0 = std::chrono::steady_clock::now();
        progress().beats.store(0);
        ConversationCheckpoint slow = copy_checkpoints_beating({make_checkpoint(1u << 20, 0)})[0];
        const double ms = std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now() - t0).count();
        check(slow.ids.size() == (1u << 20), "the slow copy lost ids");
        check(progress().beats.load() >= 4, "a slow copy stopped beating");
        check(ms >= 3.0, "the injected page-in delay did not show in the copy time");   // 4 MiB = 4 slices x 1 ms
        std::printf("conversation_copy_test: a 4 MiB copy with a 1 ms per MiB page-in took %.1f ms and beat %llu times\n",
                    ms, (unsigned long long) progress().beats.load());
    } catch (const std::exception& e) {
        std::cerr << "conversation_copy_test: " << e.what() << "\n";
        return 1;
    }
    std::cout << "conversation_copy_test: ok\n";
    return 0;
}
