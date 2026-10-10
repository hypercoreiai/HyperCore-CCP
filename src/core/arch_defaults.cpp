// src/core/arch_defaults.cpp - see include/hypercore/core/arch_defaults.hpp.
#include "hypercore/core/arch_defaults.hpp"

#include "hypercore/kernels/gfx_arch.hpp"

#include <cstdio>
#include <cstdlib>
#include <cstring>

namespace hypercore::core {

std::vector<std::pair<std::string, std::string>> arch_default_env(const char* gcn_arch) {
    std::vector<std::pair<std::string, std::string>> t;
    if (!hypercore::kernels::gfx_arch_is_gfx1151(gcn_arch)) return t;
    const char* off = std::getenv("HYPERCORE_GFX1151_DEFAULTS");
    if (off != nullptr && off[0] == '0') return t;
    // Exact (bitwise) on Aurora, each with its measured gain in aurora_s23.md:
    t = {
        // prompt
        {"HYPERCORE_GDN_HEAD", "1"},        // the GDN recurrence, four lanes a column + the grid-stride norm (S23)
        {"HYPERCORE_GDN_PP", "2"},          //   two columns per lane: 64K prompt +2.9% (stream A, round 2)
        {"HYPERCORE_GDN_CONVL2", "1"},      // conv + q/k L2 norm in one kernel: 64K -0.3 s (stream A)
        {"HYPERCORE_GDN_NOY", "1"},         // no dead FP32 store of the norm (stream A)
        {"HYPERCORE_CVEC_FUSE", "1"},       // a steered layer's write, control vector and next norm in one pass (S23)
        {"HYPERCORE_HCD_EXACT", "1"},       // the HC down GEMM in hipBLASLt solution 1176's k order: 64K +1.8% (stream S)
        {"HYPERCORE_PF_PAD", "1"},          // padded GEMM row strides (acts with HYPERCORE_PF_GEMM; inert without it) (S23)
        // decode
        {"HYPERCORE_Q8_PACKED", "1"},       // the packed Q8_0 decode layout: +2.3% (S26)
        {"HYPERCORE_Q6_PACKED", "1"},       // the packed Q6_K heads (S26)
        {"HYPERCORE_MMVF_ROWS", "1"},       // bf16 multi-row GEMV, 4 rows per block (S25)
        {"HYPERCORE_ATTN_LANECELL", "1"},   // decode attention scores, one cell per thread (S25)
        {"HYPERCORE_EXPERT_V2", "1"},       // the grouped decode experts, IQ3_S gate/up + IQ4_NL down (S26)
        {"HYPERCORE_TSUM", "1"},            // several warp sums as one transposed butterfly (S26)
        {"HYPERCORE_LFUSE", "1"},           // fewer launches around the shared expert and the KV append (S26)
        {"HYPERCORE_GDN_SPLIT", "1"},       // the GDN step over 4 blocks per head (S25/S26)
        {"HYPERCORE_QFUSE", "1"},           // activation q8_1 images written by their producers (S26)
        {"HYPERCORE_PLE_BATCH", "1"},       // the verify window's PLE key / value projections at once (S25)
        {"HYPERCORE_SH_STREAM", "1"},       // the shared expert on its own stream: decode +1.8% / +6.7% (UD-Q4_K_XL) (140-m)
    };
    return t;
}

std::vector<std::string> apply_arch_defaults(const char* gcn_arch) {
    std::vector<std::string> set;
    for (const auto& kv : arch_default_env(gcn_arch)) {
        if (std::getenv(kv.first.c_str()) != nullptr) continue;   // the user's setting wins, whatever it is
#if defined(_WIN32)
        _putenv_s(kv.first.c_str(), kv.second.c_str());
#else
        setenv(kv.first.c_str(), kv.second.c_str(), 0);
#endif
        set.push_back(kv.first);
    }
    if (!set.empty()) {
        std::fprintf(stderr, "hypercore: gfx1151 (Strix Halo): %zu exact speed switches on by default (HYPERCORE_GFX1151_DEFAULTS=0 turns "
                             "them off; a switch you set is kept): ", set.size());
        for (size_t i = 0; i < set.size(); ++i) std::fprintf(stderr, "%s%s", i ? " " : "", set[i].c_str() + 7);
        std::fprintf(stderr, "\n");
    }
    return set;
}

}  // namespace hypercore::core
