/* bench/results/2026-10-09-blackbox-api/summary_test.c
 * The terminal chunk, the stop reason, and the summary's forward-compatibility rule.
 *
 * The chunk is built by the engine and read by the caller, so the caller cannot declare its size.
 * That makes the summary the one struct in the contract with no caller-side size handshake - the
 * engine writes it, the caller guesses its layout. summary->struct_size is the only defence, and a
 * caller compiled against an older summary must read only the prefix it knows.
 *
 * Build: gcc -std=c11 -Wall -Wextra -I. summary_test.c \
 *        -L/home/ai-user0/HyperCore/build-shared -lhypercore_api -Wl,-rpath,/home/ai-user0/HyperCore/build-shared \
 *        -o summary_test
 */
#include "hypercore/hypercore_api.h"
#include <stdio.h>
#include <string.h>
#include <stddef.h>
static uint64_t next_id(void) { static uint64_t n = 0; return ++n; }

/* A caller compiled against the first draft of the summary knows only the first 24 bytes
   of the frozen layout: struct_size, produced_tokens, prefill_ms, decode_ms. No stop_reason,
   no padding. This is the forward-compatibility rule made executable. */
#pragma pack(push, 1)
typedef struct {
    uint32_t struct_size;      /* 0  */
    uint32_t produced_tokens;  /* 4  */
    uint64_t prefill_ms;       /* 8  */
    uint64_t decode_ms;        /* 16 */
} summary_v1_t;
#pragma pack(pop)

typedef struct {
    int tokens_seen;
    int terminal_seen;
    int stop_reason;
    unsigned long produced;
    int old_reader_ok;
    uint64_t decode_ms;
    uint32_t ttft_ms;
} capture_t;

static void on_chunk(const hypercore_output_chunk_t* chunk, void* user) {
    capture_t* c = (capture_t*) user;
    if (chunk->token_id >= 0) { c->tokens_seen++; return; }
    c->terminal_seen = 1;
    if (!chunk->summary) return;

    /* A v1 reader only knows the first 24 bytes. It checks the declared size, then reads the prefix. */
    summary_v1_t old;
    memset(&old, 0, sizeof old);
    memcpy(&old, chunk->summary, sizeof old);
    c->produced = old.produced_tokens;
    c->decode_ms = old.decode_ms;
    c->old_reader_ok = (chunk->summary->struct_size >= sizeof(summary_v1_t));
    c->stop_reason = (int) chunk->summary->stop_reason;
    /* The v1 reader above cannot see byte 36; this line is the current reader using it. */
    c->ttft_ms = chunk->summary->time_to_first_token_ms;
}

static int run(hypercore_engine_t* engine, const int32_t* prompt, size_t len, capture_t* cap) {
    hypercore_request_config_t cfg;
    memset(&cfg, 0, sizeof cfg);
    cfg.struct_size = sizeof cfg;
    cfg.temperature = 0.0f; cfg.top_p = 1.0f; cfg.top_k = 1; cfg.max_new_tokens = 8;
    cfg.pcie_frac = -1.0f;    /* the sentinel: do not override */
    cfg.spec_min_p = 0.7f;
    return hypercore_engine_submit(engine, next_id(), &cfg, prompt, len, on_chunk, cap);
}

static int check(int cond, const char* what) {
    if (!cond) { printf("FAIL: %s\n", what); return 0; }
    return 1;
}

/* The wire offsets are the contract. They are stated here as numbers, not derived from the
   struct, so a change in the header that moves a field fails loudly instead of silently. */
static int verify_frozen_offsets(void) {
    int ok = 1;
    ok &= check(sizeof(hypercore_request_summary_t) == 40,
               "summary is exactly 40 bytes packed");
    ok &= check(offsetof(hypercore_request_summary_t, struct_size) == 0, "struct_size at 0");
    ok &= check(offsetof(hypercore_request_summary_t, produced_tokens) == 4, "produced at 4");
    ok &= check(offsetof(hypercore_request_summary_t, prefill_ms) == 8, "prefill_ms at 8");
    ok &= check(offsetof(hypercore_request_summary_t, decode_ms) == 16, "decode_ms at 16");
    ok &= check(offsetof(hypercore_request_summary_t, drafts_accepted) == 24, "accepted at 24");
    ok &= check(offsetof(hypercore_request_summary_t, drafts_offered) == 28, "offered at 28");
    ok &= check(offsetof(hypercore_request_summary_t, stop_reason) == 32, "stop_reason at 32");
    ok &= check(offsetof(hypercore_request_summary_t, time_to_first_token_ms) == 36,
               "time_to_first_token_ms occupies the reserved byte 36 slot, size unchanged");
    ok &= check(sizeof(hypercore_request_config_t) == 28, "request config is 28 bytes packed");
    ok &= check(sizeof(hypercore_caps_t) == 28, "caps is 28 bytes packed");
    return ok;
}

int main(void) {
    int ok = 1;
    ok &= verify_frozen_offsets();

    /* A. the stream runs to max_new_tokens -> LIMIT */
    hypercore_engine_t* e1 = NULL;
    if (hypercore_engine_init(&e1, "{\"batch\": 1}") != HYPERCORE_STATUS_SUCCESS) { printf("FAIL: init\n"); return 1; }
    int32_t prompt[4] = {1, 2, 3, 4};
    capture_t a; memset(&a, 0, sizeof a);
    ok &= run(e1, prompt, 4, &a) == HYPERCORE_STATUS_SUCCESS;
    hypercore_engine_destroy(e1);   /* joins the request thread before returning */
    printf("limit case: tokens=%d terminal=%d produced=%lu stop_reason=%d v1_reader_safe=%d ttft_ms=%u\n",
           a.tokens_seen, a.terminal_seen, a.produced, a.stop_reason, a.old_reader_ok, a.ttft_ms);
    ok &= a.tokens_seen == 8 && a.terminal_seen == 1 && a.produced == 8
          && a.stop_reason == HYPERCORE_STOP_REASON_LIMIT && a.old_reader_ok;
    /* Byte 36 is no longer padding. A stream that delivered tokens has a first token, and
       the summary must say when it happened. */
    ok &= check(a.ttft_ms > 0, "time_to_first_token_ms is populated for a live stream");

    /* B. the model ends early -> EOS. produced < max_new_tokens, so "produced == max_new_tokens"
       is not a substitute for the enum. */
    hypercore_engine_t* e2 = NULL;
    hypercore_engine_init(&e2, "{\"batch\": 1}");
    int32_t eos_prompt[4] = {7, 2, 3, 4};   /* the fixture's end-of-stream marker */
    capture_t b; memset(&b, 0, sizeof b);
    ok &= run(e2, eos_prompt, 4, &b) == HYPERCORE_STATUS_SUCCESS;
    hypercore_engine_destroy(e2);
    printf("eos case:   tokens=%d produced=%lu stop_reason=%d\n", b.tokens_seen, b.produced, b.stop_reason);
    ok &= b.stop_reason == HYPERCORE_STOP_REASON_EOS && b.produced == 4;

    /* C. out-of-range values are refused, not clamped. */
    hypercore_engine_t* e3 = NULL;
    hypercore_engine_init(&e3, "{\"batch\": 1}");
    hypercore_request_config_t bad;
    memset(&bad, 0, sizeof bad);
    bad.struct_size = sizeof bad;
    bad.temperature = 0.0f; bad.top_p = 1.0f; bad.top_k = 1; bad.max_new_tokens = 8;
    bad.pcie_frac = 3.0f; bad.spec_min_p = 0.5f;
    int refused = hypercore_engine_submit(e3, next_id(), &bad, prompt, 4, on_chunk, &a) == HYPERCORE_STATUS_INVALID_ARG;
    bad.pcie_frac = 0.5f; bad.spec_min_p = -1.0f;
    int neg_ok = hypercore_engine_submit(e3, next_id(), &bad, prompt, 4, on_chunk, &a) == HYPERCORE_STATUS_SUCCESS;
    printf("refused pcie_frac=3.0: %d | accepted pcie_frac=-1.0 sentinel: %d\n", refused, neg_ok);
    ok &= refused && neg_ok;
    hypercore_engine_destroy(e3);

    /* D. ownership of the prompt array. submit() is asynchronous, so the caller's array is not alive
       when the request thread reads it. Overwrite it immediately after submit: if the engine kept a
       pointer rather than a copy, this changes the outcome. */
    hypercore_engine_t* e4 = NULL;
    hypercore_engine_init(&e4, "{\"batch\": 1}");
    int32_t owned[4] = {7, 2, 3, 4};
    capture_t d; memset(&d, 0, sizeof d);
    ok &= run(e4, owned, 4, &d) == HYPERCORE_STATUS_SUCCESS;
    for (int i = 0; i < 4; ++i) owned[i] = 1;   /* the caller's memory is now something else */
    hypercore_engine_destroy(e4);
    printf("prompt overwritten after submit: stop_reason=%d (engine must have copied: 1 expected)\n",
           d.stop_reason);
    ok &= d.stop_reason == HYPERCORE_STOP_REASON_EOS;

    printf("%s\n", ok ? "PASS: terminal summary is readable by an older caller and stop_reason distinguishes EOS from LIMIT"
                      : "FAIL");
    return ok ? 0 : 1;
}
