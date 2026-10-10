// bench/results/2026-10-09-blackbox-api/hypercore_bridge_v2.cpp
// The v1 boundary, implemented as the contract specifies: submit() is ASYNCHRONOUS. It reserves a
// batch slot, returns, and the stream callback fires from the request's own thread, ending with the
// terminal summary chunk.
//
// This is the version an embedder can actually test against. The bug it exposes is in the adapter,
// not here: a synchronous read of the metrics right after submit() sees nothing.
#include "hypercore/hypercore_blackbox.h"

#include <atomic>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <new>
#include <thread>
#include <vector>

namespace hypercore {
    struct InternalEngineOptions {
        int32_t  pool_workers  = -1;
        float    pcie_frac     = -1.0f;
        float    spec_min_p    = -1.0f;
        int32_t  batch_slots   = 4;      // int32 so a bad parse is distinguishable from 0
        uint32_t max_context   = 4096;
    };

    class EngineContext {
    public:
        InternalEngineOptions options;
        std::atomic<int64_t> active{0};
        std::vector<std::thread> running;   // the async requests, joined on destroy
        bool is_initialized = false;
    };
}

static const char* safe_getenv(const char* var) { return std::getenv(var); }

static bool parse_int(const char* s, int32_t& out) {
    char* end = nullptr;
    const long v = std::strtol(s, &end, 10);
    if (end == s || *end != '\0') return false;
    out = (int32_t) v;
    return true;
}
static bool parse_float(const char* s, float& out) {
    char* end = nullptr;
    const double v = std::strtod(s, &end);
    if (end == s || *end != '\0') return false;
    out = (float) v;
    return true;
}

static void merge_env_into_options(hypercore::InternalEngineOptions& opts) {
    if (const char* v = safe_getenv("HYPERCORE_POOL_WORKERS"))  parse_int(v, opts.pool_workers);
    if (const char* v = safe_getenv("HYPERCORE_PCIE_FRAC"))     parse_float(v, opts.pcie_frac);
    if (const char* v = safe_getenv("HYPERCORE_SPEC_MIN_P"))    parse_float(v, opts.spec_min_p);
    if (const char* v = safe_getenv("HYPERCORE_BATCH"))         parse_int(v, opts.batch_slots);
}

static bool json_number(const char* s, const char* key, double& out) {
    const char* p = std::strstr(s, key);
    if (p == nullptr) return false;
    p += std::strlen(key);
    while (*p == ' ' || *p == ':') ++p;
    char* end = nullptr;
    const double v = std::strtod(p, &end);
    if (end == p) return false;
    out = v;
    return true;
}

static void merge_json_into_options(const char* json, hypercore::InternalEngineOptions& opts) {
    if (json == nullptr) return;
    double v;
    if (json_number(json, "\"pool_workers\"", v))  opts.pool_workers = (int32_t) v;
    if (json_number(json, "\"pcie_frac\"", v))     opts.pcie_frac = (float) v;
    if (json_number(json, "\"spec_min_p\"", v))    opts.spec_min_p = (float) v;
    if (json_number(json, "\"batch\"", v))         opts.batch_slots = (uint32_t) v;
    if (json_number(json, "\"max_context\"", v))   opts.max_context = (uint32_t) v;
}

static bool abi_declared_ok(uint32_t declared, size_t full, size_t minimum) {
    return declared >= minimum && declared <= full;
}

extern "C" {

struct hypercore_engine_t {
    hypercore::EngineContext ctx;
};

HYPERCORE_API hypercore_status_t hypercore_engine_init(hypercore_engine_t** out_engine, const char* json_config_string) {
    if (!out_engine) return HYPERCORE_STATUS_INVALID_ARG;
    hypercore_engine_t* engine = new (std::nothrow) hypercore_engine_t();
    if (!engine) return HYPERCORE_STATUS_UNSUPPORTED;

    hypercore::InternalEngineOptions opts;
    merge_env_into_options(opts);
    merge_json_into_options(json_config_string, opts);
    if (opts.batch_slots == 0) return HYPERCORE_STATUS_INVALID_ARG;   // a zero-slot engine cannot run
    engine->ctx.options = opts;
    engine->ctx.is_initialized = true;
    *out_engine = engine;
    return HYPERCORE_STATUS_SUCCESS;
}

HYPERCORE_API hypercore_status_t hypercore_engine_get_caps(const hypercore_engine_t* engine, hypercore_caps_t* out_caps) {
    if (!engine || !out_caps) return HYPERCORE_STATUS_INVALID_ARG;
    if (!abi_declared_ok(out_caps->struct_size, sizeof(hypercore_caps_t),
                         offsetof(hypercore_caps_t, backend_type) + sizeof(uint32_t)))
        return HYPERCORE_STATUS_INVALID_ARG;

    hypercore_caps_t full;
    memset(&full, 0, sizeof full);
    full.struct_size      = out_caps->struct_size;   // tell the caller what IT declared
    full.backend_type     = 1;
    full.max_batch_slots  = engine->ctx.options.batch_slots;
    full.max_context_len  = engine->ctx.options.max_context;
    /* active_pool_workers is a resolved number, never the -1 "engine decides" sentinel. A caller
       that reads -1 as "zero workers" is the failure mode the field exists to prevent. */
    int32_t workers = engine->ctx.options.pool_workers;
    if (workers <= 0) {
        unsigned hw = std::thread::hardware_concurrency();
        workers = (hw > 0) ? (int32_t) hw : 1;
    }
    full.active_pool_workers = workers;

    memcpy(out_caps, &full, out_caps->struct_size);
    return HYPERCORE_STATUS_SUCCESS;
}

/* The request thread. The fixture models both terminal cases so the tests can tell them apart:
 *   prompt_tokens[0] == 7  -> the stream ends early, STOP_REASON_EOS
 *   prompt_tokens[0] == 9  -> the stream is aborted mid-way, STOP_REASON_CANCEL
 *   otherwise              -> the stream runs to max_new_tokens, STOP_REASON_LIMIT
 * A fixture that always reports EOS cannot test the field the enum exists for. */
static void run_request(hypercore_engine_t* engine,
                        const hypercore_request_config_t cfg,
                        const std::vector<int32_t>& prompt,
                        hypercore_stream_cb callback,
                        void* user_data) {
    /* The stub must actually hold the slot for the time it reports. A fixture that reports 104 ms and
       returns in 10 microseconds cannot test backpressure: BUSY becomes a race instead of a property. */
    const long wait_ms = 40 + (long) cfg.max_new_tokens / 2;
    std::this_thread::sleep_for(std::chrono::milliseconds(wait_ms));

    /* The prompt is read AFTER the wait, on purpose: a real engine reads it after scheduling, so a
       boundary that kept a pointer to the caller's array would be reading memory the caller has since
       freed. This is the only place the fixture can prove the copy belongs to the engine. */
    const bool ended_early = prompt[0] == 7;
    const bool cancelled   = prompt[0] == 9;
    const uint32_t produced = cancelled ? cfg.max_new_tokens / 4
                                       : (ended_early ? cfg.max_new_tokens / 2 : cfg.max_new_tokens);
    const double ms = 40.0 + 0.5 * produced;   // deterministic, so tests are reproducible

    hypercore_request_summary_t summary;
    memset(&summary, 0, sizeof summary);
    summary.struct_size      = sizeof summary;
    summary.decode_ms        = (uint64_t) ms;
    summary.produced_tokens  = produced;
    summary.drafts_accepted  = produced / 4;
    summary.drafts_offered   = produced / 2;
    summary.stop_reason      = cancelled ? HYPERCORE_STOP_REASON_CANCEL
                        : ended_early  ? HYPERCORE_STOP_REASON_EOS
                        :              HYPERCORE_STOP_REASON_LIMIT;

    for (uint32_t i = 0; i < produced; ++i) {
        hypercore_output_chunk_t chunk;
        memset(&chunk, 0, sizeof chunk);
        chunk.token_id = (int32_t) (1000 + i);
        chunk.summary = nullptr;
        callback(&chunk, user_data);
    }

    hypercore_output_chunk_t terminal;
    memset(&terminal, 0, sizeof terminal);
    terminal.token_id = -1;
    terminal.summary = &summary;
    callback(&terminal, user_data);

    /* The slot is released when the stream ends, by the engine, not by the caller. If this were
       missing, every request would hold a slot forever and the sweep would starve at batch slots. */
    engine->ctx.active.fetch_sub(1);
}
HYPERCORE_API hypercore_status_t hypercore_engine_submit(hypercore_engine_t* engine, const hypercore_request_config_t* config,
                                               const int32_t* prompt_tokens, size_t prompt_len,
                                               hypercore_stream_cb callback, void* user_data) {
    if (!engine || !config || !prompt_tokens || prompt_len == 0 || !callback) return HYPERCORE_STATUS_INVALID_ARG;
    if (!abi_declared_ok(config->struct_size, sizeof(hypercore_request_config_t),
                         offsetof(hypercore_request_config_t, max_new_tokens) + sizeof(uint32_t)))
        return HYPERCORE_STATUS_INVALID_ARG;

    if (config->top_k < 1 || config->top_k > 64) return HYPERCORE_STATUS_INVALID_ARG;
    if (config->top_p < 0.0f || config->top_p > 1.0f) return HYPERCORE_STATUS_INVALID_ARG;
    if (config->temperature < 0.0f) return HYPERCORE_STATUS_INVALID_ARG;
    if (config->max_new_tokens < 1) return HYPERCORE_STATUS_INVALID_ARG;
    if ((uint64_t) prompt_len + config->max_new_tokens > engine->ctx.options.max_context)
        return HYPERCORE_STATUS_INVALID_ARG;
    /* pcie_frac/spec_min_p: negative is the "do not override" sentinel; anything else must be a
       real probability. A single chained comparison here silently accepted 3.0. */
    if (config->pcie_frac >= 0.0f && config->pcie_frac > 1.0f) return HYPERCORE_STATUS_INVALID_ARG;
    if (config->spec_min_p >= 0.0f && config->spec_min_p > 1.0f) return HYPERCORE_STATUS_INVALID_ARG;

    if (engine->ctx.active.fetch_add(1) >= (int64_t) engine->ctx.options.batch_slots) {
        engine->ctx.active.fetch_sub(1);
        return HYPERCORE_STATUS_BUSY;
    }

    /* A copy of the config AND the prompt: submit() is asynchronous, so the caller's arrays are gone
       by the time the request thread reads them. The header's lifetime rule covers the output frame
       only; the input arrays need the same rule, and the engine has to own the copy. */
    hypercore_request_config_t copy = *config;
    std::vector<int32_t> prompt(prompt_tokens, prompt_tokens + prompt_len);
    engine->ctx.running.emplace_back(run_request, engine, copy, std::move(prompt), callback, user_data);
    return HYPERCORE_STATUS_SUCCESS;
}

HYPERCORE_API void hypercore_engine_destroy(hypercore_engine_t* engine) {
    if (!engine) return;
    for (auto& t : engine->ctx.running) t.join();
    delete engine;
}

}  // extern "C"
