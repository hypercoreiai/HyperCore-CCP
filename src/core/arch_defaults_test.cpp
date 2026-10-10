// src/core/arch_defaults_test.cpp - the per-architecture default table (no GPU needed).
#include "hypercore/core/arch_defaults.hpp"

#include <cstdio>
#include <cstdlib>
#include <string>

static int fails = 0;
#define CHECK(c) do { if (!(c)) { std::printf("FAIL line %d: %s\n", __LINE__, #c); ++fails; } } while (0)

static void unset(const char* k) {
#if defined(_WIN32)
    _putenv_s(k, "");
#else
    unsetenv(k);
#endif
}
static void put(const char* k, const char* v) {
#if defined(_WIN32)
    _putenv_s(k, v);
#else
    setenv(k, v, 1);
#endif
}

int main() {
    using namespace hypercore::core;
    unset("HYPERCORE_GFX1151_DEFAULTS");
    // other architectures (and CUDA, which passes an empty name): nothing
    CHECK(arch_default_env("gfx1100").empty());
    CHECK(arch_default_env("gfx1201:sramecc-:xnack-").empty());
    CHECK(arch_default_env("gfx1150").empty());
    CHECK(arch_default_env("gfx11510").empty());   // not a prefix match
    CHECK(arch_default_env("").empty());
    CHECK(arch_default_env(nullptr).empty());
    // gfx1151, plain and with its feature suffix: the table, and no bit-changing switch in it
    for (const char* a : {"gfx1151", "gfx1151:sramecc-:xnack-"}) {
        const auto t = arch_default_env(a);
        CHECK(t.size() >= 10);
        for (const auto& kv : t) {
            CHECK(kv.first.rfind("HYPERCORE_", 0) == 0);
            for (const char* bits : {"HYPERCORE_PF_GEMM", "HYPERCORE_PF_FUSED", "HYPERCORE_HC_UPMIX", "HYPERCORE_PA_FAST", "HYPERCORE_HIP_WMMA",
                                     "HYPERCORE_SELECT_WMMA", "HYPERCORE_HC_Q8", "HYPERCORE_PF_HCDOWN", "HYPERCORE_WMMA_GEMM"})
                CHECK(kv.first != bits);
        }
    }
    // a user's setting wins, whatever it is; the rest are set
    put("HYPERCORE_TSUM", "0");
    unset("HYPERCORE_QFUSE");
    const auto set = apply_arch_defaults("gfx1151");
    CHECK(std::getenv("HYPERCORE_TSUM") != nullptr && std::string(std::getenv("HYPERCORE_TSUM")) == "0");
    CHECK(std::getenv("HYPERCORE_QFUSE") != nullptr && std::string(std::getenv("HYPERCORE_QFUSE")) == "1");
    for (const auto& n : set) CHECK(n != "HYPERCORE_TSUM");
    // the opt-out
    put("HYPERCORE_GFX1151_DEFAULTS", "0");
    CHECK(arch_default_env("gfx1151").empty());
    CHECK(apply_arch_defaults("gfx1151").empty());
    std::printf(fails ? "arch_defaults_test: %d FAILED\n" : "arch_defaults_test: OK\n", fails);
    return fails ? 1 : 0;
}
