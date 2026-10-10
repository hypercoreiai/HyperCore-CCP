/* bench/results/2026-10-09-blackbox-api/pool_test.c
 * What the restored pool field has to prove:
 *   1. active_pool_workers is a resolved number under all three config layers, and a caller
 *      that predates the field still reads a valid caps prefix.
 *   2. BUSY releases the slot it bounced. A bounce that leaks a slot turns the engine into a
 *      slow deadlock instead of a backpressure signal.
 *   3. The engine spine is actually inside the .so: the token stream comes from hypercore_spec's
 *      suffix drafter, so a repeating prompt produces real draft counts.
 *
 * Build: gcc -std=c11 -Wall -Wextra -I. pool_test.c -L. -lhypercore_api -Wl,-rpath,. -o pool_test
 */
#define _POSIX_C_SOURCE 200808L   /* setenv/unsetenv/nanosleep under -std=c11 */
#include "hypercore/hypercore_api.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <time.h>
static uint64_t next_id(void) { static uint64_t n = 0; return ++n; }

static int failures = 0;
static void expect(int cond, const char* what) {
    if (!cond) { printf("FAIL: %s\n", what); ++failures; }
}

/* A caller compiled against the header before active_pool_workers existed: it knows four
   fields and declares a 16-byte prefix. The layout is written out rather than derived from
   the current struct, so growing hypercore_caps_t cannot silently move the goalposts. */
typedef struct caps_v1 {
    uint32_t struct_size;      /* 4 */
    uint32_t backend_type;     /* 4 */
    uint32_t max_batch_slots;  /* 4 */
    uint32_t max_context_len;  /* 4 */
    char     guard[16];        /* 28 bytes total; the engine must not touch these */
} caps_v1;

static int g_frames = 0, g_reason = 0, g_tokens = 0;
static int g_draft_offered = 0, g_draft_accepted = 0;
static void count_cb(const hypercore_output_chunk_t* chunk, void* user_data) {
    (void) user_data;
    ++g_frames;
    if (chunk->token_id < 0 && chunk->summary) {
        g_reason        = (int) chunk->summary->stop_reason;
        g_tokens        = (int) chunk->summary->produced_tokens;
        g_draft_offered = (int) chunk->summary->drafts_offered;
        g_draft_accepted = (int) chunk->summary->drafts_accepted;
    }
}

static int32_t read_pool(const char* json) {
    hypercore_engine_t* e = NULL;
    if (hypercore_engine_init(&e, json) != HYPERCORE_STATUS_SUCCESS) return -100;
    hypercore_caps_t c;
    memset(&c, 0, sizeof c);
    c.struct_size = sizeof c;
    if (hypercore_engine_get_caps(e, &c) != HYPERCORE_STATUS_SUCCESS) { hypercore_engine_destroy(e); return -101; }
    hypercore_engine_destroy(e);
    return c.active_pool_workers;
}

int main(void) {
    /* 1. every layer resolves to a real worker count, never the -1 sentinel */
    unsetenv("HYPERCORE_POOL_WORKERS");
    int32_t dflt = read_pool(NULL);
    expect(dflt > 0, "default pool reports a positive worker count, not the -1 sentinel");

    setenv("HYPERCORE_POOL_WORKERS", "7", 1);
    int32_t from_env = read_pool(NULL);
    expect(from_env == 7, "env HYPERCORE_POOL_WORKERS is reported through caps");

    setenv("HYPERCORE_POOL_WORKERS", "7", 1);
    int32_t from_json = read_pool("{\"pool_workers\":3}");
    expect(from_json == 3, "json beats env, per the documented precedence");

    unsetenv("HYPERCORE_POOL_WORKERS");

    /* 2. an older caller reads the prefix and its own trailing bytes are untouched */
    caps_v1 old;
    memset(&old, 0, sizeof old);
    memset(old.guard, 0x5A, sizeof old.guard);
    old.struct_size = 16;   /* the prefix that existed before active_pool_workers */

    hypercore_engine_t* e = NULL;
    if (hypercore_engine_init(&e, "{\"batch\":2}") != HYPERCORE_STATUS_SUCCESS) { printf("init failed\n"); return 1; }
    hypercore_caps_t probe;
    memset(&probe, 0, sizeof probe);
    probe.struct_size = sizeof probe;
    expect(hypercore_engine_get_caps(e, &probe) == HYPERCORE_STATUS_SUCCESS, "full caller accepted");
    expect(probe.active_pool_workers > 0, "full caller sees a resolved pool size");

    int status = hypercore_engine_get_caps(e, (hypercore_caps_t*) &old);
    expect(status == HYPERCORE_STATUS_SUCCESS, "v1 caller accepted via the prefix rule");
    expect(old.max_batch_slots == 2, "v1 caller still gets batch slots");
    expect(old.guard[0] == 0x5A && old.guard[15] == 0x5A, "the engine wrote nothing past the declared prefix");
    expect(sizeof(hypercore_caps_t) == 28,
         "caps grew by the two baseline floats; an old caller is unaffected only because the prefix rule holds");

    /* 3. The spine is really inside this .so, not merely linked to it. The token stream is
       produced by hypercore_spec's suffix drafter: a prompt with a repeating trigram yields real
       draft proposals, a prompt with no repeat yields none. If the archive had not been forced
       in, both would be zero and this test could not tell the difference. */
    g_frames = g_reason = g_tokens = 0;
    int32_t repeat_prompt[6] = {5, 6, 7, 5, 6, 7};
    hypercore_request_config_t cfg;
    memset(&cfg, 0, sizeof cfg);
    cfg.struct_size = sizeof cfg;
    cfg.temperature = 0.0f;
    cfg.top_p = 1.0f;
    cfg.top_k = 1;              /* top_k == 0 is rejected by the boundary, see notes in README */
    cfg.max_new_tokens = 64;
    cfg.pcie_frac = -1.0f;
    cfg.spec_min_p = -1.0f;

    expect(hypercore_engine_submit(e, next_id(), &cfg, repeat_prompt, 6, count_cb, NULL) == HYPERCORE_STATUS_SUCCESS,
           "a repeating prompt is accepted");
    /* busy_test relies on the request holding its slot for ~40+ ms; sleep long enough to be sure
       the request thread has finished and released it. */
    struct timespec ts = {0, 200 * 1000000L};
    nanosleep(&ts, NULL);
    expect(g_reason == HYPERCORE_STOP_REASON_LIMIT, "a stream with no early marker runs to the ceiling");
    expect(g_draft_offered > 0 && g_draft_accepted > 0, "the suffix drafter in the archive produced drafts");
    expect(g_tokens == 64, "the ceiling is honoured exactly");
    expect(g_frames > 1, "a full stream emits token frames plus a terminal frame");

    g_frames = g_reason = g_tokens = 0;
    int32_t flat_prompt[4] = {1, 2, 3, 4};
    expect(hypercore_engine_submit(e, next_id(), &cfg, flat_prompt, 4, count_cb, NULL) == HYPERCORE_STATUS_SUCCESS,
           "a non-repeating prompt is accepted");
    nanosleep(&ts, NULL);
    expect(g_draft_offered == 0, "no repeat means no drafts - the drafter is not fabricating counts");

    /* 4. the slot is back: two BUSY bounces must not consume anything */
    int32_t p2[2] = {1, 1};
    expect(hypercore_engine_submit(e, next_id(), &cfg, p2, 2, count_cb, NULL) == HYPERCORE_STATUS_SUCCESS,
           "a slot is available after the previous request finished");
    expect(hypercore_engine_submit(e, next_id(), &cfg, p2, 2, count_cb, NULL) == HYPERCORE_STATUS_SUCCESS,
           "both declared slots are in use now");
    expect(hypercore_engine_submit(e, next_id(), &cfg, p2, 2, count_cb, NULL) == HYPERCORE_STATUS_BUSY,
           "the third request bounces");
    expect(hypercore_engine_submit(e, next_id(), &cfg, p2, 2, count_cb, NULL) == HYPERCORE_STATUS_BUSY,
           "the fourth bounce also returns BUSY, not UNSUPPORTED or INVALID_ARG");

    nanosleep(&ts, NULL);
    expect(hypercore_engine_submit(e, next_id(), &cfg, p2, 2, count_cb, NULL) == HYPERCORE_STATUS_SUCCESS,
           "BUSY did not leak a slot: the engine is usable again once the running requests end");

    /* Behaviour pinned, not assumed: top_k == 0 is rejected rather than treated as "unset".
       If the intent is "no top-k truncation", the boundary needs a sentinel for it. */
    hypercore_request_config_t zero_topk = cfg;
    zero_topk.top_k = 0;
    expect(hypercore_engine_submit(e, next_id(), &zero_topk, p2, 2, count_cb, NULL) == HYPERCORE_STATUS_INVALID_ARG,
           "top_k == 0 is refused, not silently clamped");

    hypercore_request_config_t big_topk = cfg;
    big_topk.top_k = 65;
    expect(hypercore_engine_submit(e, next_id(), &big_topk, p2, 2, count_cb, NULL) == HYPERCORE_STATUS_INVALID_ARG,
           "top_k above the documented ceiling is refused, not clamped to 64");

    hypercore_engine_destroy(e);
    if (failures) { printf("%d failure(s)\n", failures); return 1; }
    printf("PASS: pool size is observable through every config layer, BUSY releases nothing, "
           "and the drafter inside the archive produced real draft counts\n");
    return 0;
}
