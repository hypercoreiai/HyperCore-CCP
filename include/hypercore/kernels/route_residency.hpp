// include/hypercore/kernels/route_residency.hpp - the two opt-in, output-changing routing adjustments that read a
// layer's residency table (Strata #1737 family).  Both are off unless the environment names them, and both need the
// native router's 512 x 10 shape.
//
//   HYPERCORE_ROUTE_PRIOR=lambda   - "Mixture of Cache-Conditional Experts" (arXiv 2412.00099) without training:
//                                    a resident expert gets `lambda` added to its logit for the SELECTION only; the
//                                    weights stay the router's own softmax.
//   HYPERCORE_ROUTE_RESIDENT=margin - after the top-10, ranks rank_lo..rank_hi that landed on a non-resident expert
//                                    are swapped to the best resident expert not already picked when its logit is
//                                    within `margin` of the replaced one.  Tokens with no swap keep the router's bits.
//
// The point of both is the same: fewer experts to copy over PCIe or compute on the CPU.  The cost is that the output
// changes, so neither is on by default.
#pragma once

#include <cstdint>

namespace hypercore::kernels {

/// Top-10 per token over `logits` ([n_tok][512]) where a resident expert (`res_layer[e] >= 0`, the layer's residency
/// table) gets `lambda` added to its logit for the selection; the weights are the router's probabilities (softmax over
/// the 512 unbiased logits) renormalised over the 10 picked, exactly as native_router_top10_multi does.
void route_prior_top10(const float* logits, const int32_t* res_layer, float lambda, int32_t* ids, float* weights,
                       int n_tok, void* stream);

/// Post-router residency swap over the ranks [rank_lo, rank_hi] of the already-picked `ids`.
/// `stats`, when not null, is a device block of 8 uint64: [0] tail entries seen, [1] swaps, [2] non-resident entries
/// before, [3] after, and the same four for the decode windows (n_tok <= 8).  nullptr is fine: the swap runs without
/// the counters.
void route_resident_swap(const float* logits, int32_t* ids, float* weights, const int32_t* res_layer, int n_tok,
                         float margin, int rank_lo, int rank_hi, unsigned long long* stats, void* stream);

}  // namespace hypercore::kernels
