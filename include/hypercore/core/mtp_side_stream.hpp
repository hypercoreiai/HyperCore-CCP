// include/hypercore/core/mtp_side_stream.hpp - #2055 (Strata 0.1.43): which builds get the MTP drafter's branch stream.
//
// The drafter runs the shared expert on `side_`, a stream beside the one the router and the routed experts use, forked
// and joined with two events.  CUDA wants it.  HIP keeps the shared expert on `cs_`, so nothing there uses the branch,
// and #1240 stopped creating it: an R9700 lost prompt speed with it after the first request.  On gfx103x the stream's
// existence alone makes prompts read faster - RX 6800, Windows, HYPERCORE_HIP_PROMPT_F16=1, IQ3_XXS, two runs each: a
// 7.9K-token prompt at 798-808 tok/s with it and 584-596 without, a 30.4K-token one at 855-863 against 553-600;
// HYPERCORE_PREFILL_TIMING=1 puts all of it in the prompt path's "wait copy" phase (3,081 -> 75 ms and 12,642 -> 288
// ms).  Decode and the output are the same.  The two events change nothing, so they stay out.
//
// Measured on one card and one OS; a Linux gfx103x number is welcome.  The decision is a pure function of the arch
// string and the override so it can be tested without a GPU.
#pragma once

#include <cstdlib>

#include "hypercore/kernels/gfx_arch.hpp"

namespace hypercore::core {

/// True when this build should create the drafter's branch stream.
/// `gcn_arch` is hipDeviceProp_t::gcnArchName on HIP and is ignored on CUDA (CUDA always branches);
/// `env` is the raw HYPERCORE_MTP_SIDE_STREAM value, nullptr when unset.  Any non-zero value forces the stream on,
/// "0" forces it off, and an empty string is treated as unset.
inline bool mtp_side_stream_on(const char* gcn_arch, const char* env) {
    if (env != nullptr && *env != 0) return std::atoi(env) != 0;   // "1" on, "0" off; anything else reads as 0
    return hypercore::kernels::gfx_arch_is_gfx103(gcn_arch);
}

}  // namespace hypercore::core
