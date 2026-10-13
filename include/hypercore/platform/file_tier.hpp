// include/hypercore/platform/file_tier.hpp - #1407 #1984 #1971: how much of the file tier the OS is reading for us.
//
// The #29 watchdog stops an engine whose heartbeat stands still for HYPERCORE_WATCHDOG_S seconds.  On a host with
// less RAM than the model, a prompt layer's experts are re-read from the pack and the page-in of the parked
// conversation's checkpoints takes minutes while the heartbeat stands still: the engine is slow, not stuck.  The OS
// counts that work (Linux: major page faults plus bytes read from storage; Windows: read transfers plus page
// faults), so a growing count is a beat the engine did not have to make itself.
//
// The counter is monotonic and meaningless in absolute terms: only the difference between two samples one second
// apart is compared.  kBusyUnits is that difference, in the mixed unit the counter is kept in (faults + MiB).  16
// in a second is well above what an idle process does and well below what a page-in at ~200 faults/s makes, so a
// thrashing host reads as busy and a genuinely hung engine does not.
//
// Zero where the platform has no measure (nothing is inferred from absence: the watchdog simply gets no allowance).
#pragma once

#include <cstdint>

namespace hypercore::platform {

// The file tier's activity as the OS counts it.  Monotonic for the life of the process.
uint64_t file_tier_activity();

// One second of real file work: at least kBusyUnits more than the sample a second ago.
constexpr uint64_t kBusyUnits = 16;

inline bool file_tier_busy(uint64_t previous, uint64_t now) {
    return now >= previous && now - previous >= kBusyUnits;   // subtracted, not added: no wrap near UINT64_MAX
}

}  // namespace hypercore::platform
