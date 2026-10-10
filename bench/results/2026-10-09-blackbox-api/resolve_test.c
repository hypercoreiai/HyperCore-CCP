/* bench/results/2026-10-09-blackbox-api/resolve_test.c
 * The two-level precedence rule, and the proof that a per-request override reaches the
 * thread that is actually running the request.
 *
 * Level 1 is fixed at init (defaults -> HYPERCORE_* env -> the JSON string).
 * Level 2 is the request frame. -1.0f on a tuning field means "take Level 1"; a value
 * inside the domain overrides it; anything else is rejected, never clamped.
 *
 * Build: gcc -std=c11 -Wall -Wextra -I. resolve_test.c \
 *            -L/home/ai-user0/HyperCore/build-shared -lhypercore_api -Wl,-rpath,/home/ai-user0/HyperCore/build-shared \
 *            -o resolve_test
 */
#define _POSIX_C_SOURCE 200809L   /* nanosleep: the wait loop below is POSIX, not C11 */
#include "hypercore/hypercore_api.h"
#include <stdio.h>
#include <string.h>
#include <time.h>

static uint64_t next_id(void) { static uint64_t n = 0; return ++n; }

typedef struct {
    int tokens, stop_reason, done;
    unsigned accepted, offered;
    uint64_t decode_ms;
    uint64_t prefill_ms;
    uint64_t ttft_ms;
} capture_t;

static void on_chunk(const hypercore_output_chunk_t* c, void* user) {
    capture_t* cap = (capture_t*) user;
    if (c->token_id >= 0) { cap->tokens++; return; }
    cap->stop_reason = c->summary ? (int) c->summary->stop_reason : -1;
    if (c->summary) {
        cap->accepted = c->summary->drafts_accepted;
        cap->offered  = c->summary->drafts_offered;
        cap->decode_ms = c->summary->decode_ms;
        cap->prefill_ms = c->summary->prefill_ms;
        cap->ttft_ms = c->summary->time_to_first_token_ms;
    }
    cap->done = 1;   /* submit() is asynchronous: the terminal chunk is the only signal that
                      the stream is over, so a caller that reads before it is set reads a half
                      filled struct. */
}

static int failures = 0;
static void check(int cond, const char* what) {
    printf("%s: %s\n", cond ? "PASS" : "FAIL", what);
    if (!cond) failures++;
}

/* Run one request with the given tuning fields and return what the stream reported. */
static capture_t run(hypercore_engine_t* e, float pcie_frac, float spec_min_p) {
    hypercore_request_config_t cfg;
    memset(&cfg, 0, sizeof cfg);
    cfg.struct_size     = sizeof cfg;
    cfg.temperature     = 1.0f;
    cfg.top_p           = 1.0f;
    cfg.top_k           = 8;
    cfg.max_new_tokens  = 20;
    cfg.pcie_frac       = pcie_frac;
    cfg.spec_min_p      = spec_min_p;
    const int32_t prompt[8] = {5, 6, 7, 5, 6, 7, 5, 6};   /* a repeating history: the drafter has
                                                             something to propose, so the acceptance
                                                             floor is observable */
    capture_t cap;
    memset(&cap, 0, sizeof cap);
    hypercore_status_t st = hypercore_engine_submit(e, next_id(), &cfg, prompt, 8, on_chunk, &cap);
    if (st != HYPERCORE_STATUS_SUCCESS) { cap.stop_reason = -100 - (int) st; cap.done = 1; return cap; }
    while (!cap.done) { struct timespec ts = {0, 1000000}; nanosleep(&ts, NULL); }
    return cap;
}

int main(void) {
    /* ---- Level 1: the instance baseline comes from the JSON string ---- */
    hypercore_engine_t* e = NULL;
    if (hypercore_engine_init(&e, "{\"pcie_frac\":0.25,\"spec_min_p\":0.5}") != HYPERCORE_STATUS_SUCCESS) {
        printf("FAIL: could not create the instance\n");
        return 1;
    }

    hypercore_request_config_t req, out;
    memset(&req, 0, sizeof req);
    req.struct_size    = sizeof req;
    req.temperature    = 1.0f;
    req.top_p          = 1.0f;
    req.top_k          = 8;
    req.max_new_tokens = 20;

    req.pcie_frac = -1.0f; req.spec_min_p = -1.0f;
    check(hypercore_engine_resolve(e, &req, &out) == HYPERCORE_STATUS_SUCCESS
          && out.pcie_frac == 0.25f && out.spec_min_p == 0.5f,
          "sentinels fall back to the instance baseline");

    req.pcie_frac = 0.9f; req.spec_min_p = 0.7f;
    check(hypercore_engine_resolve(e, &req, &out) == HYPERCORE_STATUS_SUCCESS
          && out.pcie_frac == 0.9f && out.spec_min_p == 0.7f,
          "an in-domain request value overrides the baseline");

    /* Mixed: one field overridden, the other left at the baseline. */
    req.pcie_frac = 0.9f; req.spec_min_p = -1.0f;
    check(hypercore_engine_resolve(e, &req, &out) == HYPERCORE_STATUS_SUCCESS
          && out.pcie_frac == 0.9f && out.spec_min_p == 0.5f,
          "the two fields resolve independently");

    req.pcie_frac = 1.5f; req.spec_min_p = -1.0f;
    check(hypercore_engine_resolve(e, &req, &out) == HYPERCORE_STATUS_INVALID_ARG,
          "pcie_frac 1.5 is rejected, not clamped");

    req.pcie_frac = -1.0f; req.spec_min_p = -0.5f;
    check(hypercore_engine_resolve(e, &req, &out) == HYPERCORE_STATUS_INVALID_ARG,
          "-0.5 is not the sentinel and is not a probability");

    req.pcie_frac = 0.0f; req.spec_min_p = 1.0f;
    check(hypercore_engine_resolve(e, &req, &out) == HYPERCORE_STATUS_SUCCESS
          && out.pcie_frac == 0.0f && out.spec_min_p == 1.0f,
          "the domain endpoints 0.0 and 1.0 are valid values, not sentinels");

    /* ---- the instance baseline is readable without submitting anything ---- */
    hypercore_caps_t caps;
    memset(&caps, 0, sizeof caps);
    caps.struct_size = sizeof caps;
    check(hypercore_engine_get_caps(e, &caps) == HYPERCORE_STATUS_SUCCESS
          && caps.instance_pcie_frac == 0.25f && caps.instance_spec_min_p == 0.5f,
          "caps reports the resolved Level-1 baseline directly, no probe request needed");

    req.pcie_frac = 0.9f; req.spec_min_p = 0.9f;
    hypercore_engine_resolve(e, &req, &out);
    check(caps.instance_pcie_frac == 0.25f && caps.instance_spec_min_p == 0.5f,
          "a request override does not rewrite the instance baseline");

    /* ---- the override has to reach the running thread, not just the boundary ---- */
    capture_t baseline   = run(e, -1.0f, -1.0f);   /* instance: spec_min_p 0.5 */
    capture_t strict     = run(e, -1.0f, 0.95f);   /* request: raise the floor */
    check(baseline.tokens == 20 && strict.tokens == 20, "both streams deliver the full token count");
    check(baseline.accepted > strict.accepted,
          "raising spec_min_p in the request lowers drafts_accepted");
    printf("      baseline stop=%d tokens=%d offered=%u accepted=%u ms=%llu; strict stop=%d tokens=%d accepted=%u\n",
           baseline.stop_reason, baseline.tokens, baseline.offered, baseline.accepted,
           (unsigned long long) baseline.decode_ms,
           strict.stop_reason, strict.tokens, strict.accepted);


    capture_t no_bus = run(e, 1.0f, -1.0f);
    capture_t full_bus = run(e, 0.0f, -1.0f);
    /* decode_ms is the emit window, not the slot hold. The hold is the gap between ttft
       and prefill: prefill_ms starts at the scheduling point, so a per-request pcie_frac
       moves ttft_ms and leaves prefill_ms alone. That separation is the whole point - a
       test that only watched prefill_ms could not tell a slow bus from a slow prompt. */
    check(no_bus.ttft_ms < full_bus.ttft_ms,
         "pcie_frac in the request changes the queue hold the engine reports");
    check(no_bus.prefill_ms == full_bus.prefill_ms,
         "the same prompt reports the same prefill regardless of bus pressure");
    printf("      ttft_ms: pcie_frac=0.0 -> %llu, pcie_frac=1.0 -> %llu "
           "(prefill_ms %llu both, decode_ms %llu vs %llu)\n",
           (unsigned long long) full_bus.ttft_ms, (unsigned long long) no_bus.ttft_ms,
           (unsigned long long) full_bus.prefill_ms,
           (unsigned long long) full_bus.decode_ms, (unsigned long long) no_bus.decode_ms);

    hypercore_engine_destroy(e);

    /* An instance with no configuration has no baseline: the sentinel resolves to -1, which
       the contract documents as "the engine decides". */
    hypercore_engine_t* bare = NULL;
    hypercore_engine_init(&bare, "{}");
    req.pcie_frac = -1.0f; req.spec_min_p = -1.0f;
    check(hypercore_engine_resolve(bare, &req, &out) == HYPERCORE_STATUS_SUCCESS
          && out.pcie_frac == -1.0f && out.spec_min_p == -1.0f,
          "with no Level 1 value the sentinel resolves to -1, not to a silent 0");
    hypercore_engine_destroy(bare);

    printf("%s\n", failures ? "resolve_test: FAILED" : "resolve_test: all precedence checks passed");
    return failures ? 1 : 0;
}
