/* bench/results/2026-10-09-blackbox-api/abi_test.c - does the struct_size rule actually hold?
 *
 * "Accept smaller, refuse larger" is only safe if the library writes no more than the caller declared.
 * The old-shaped struct here is followed immediately by a guard, so an over-write is visible.
 *
 * Build: gcc -std=c11 -Wall -Wextra -I. abi_test.c -L. -lhypercore_api -Wl,-rpath,. -o abi_test
 */
#include "hypercore/hypercore_api.h"
#include <stdio.h>
#include <string.h>
static uint64_t next_id(void) { static uint64_t n = 0; return ++n; }

typedef struct {
    uint32_t struct_size;
    uint32_t backend_type;
} caps_v0_t;                        /* what a caller compiled against v0 has */

typedef struct { caps_v0_t caps; char guard[16]; } probe_t;   /* guard sits right after it */

static int seen = 0;
static void on_chunk(const hypercore_output_chunk_t* c, void* user) { (void) c; (void) user; ++seen; }

int main(void) {
    hypercore_engine_t* engine = NULL;
    if (hypercore_engine_init(&engine, "{\"batch\":2}") != HYPERCORE_STATUS_SUCCESS) { printf("init failed\n"); return 1; }

    /* Case 1: a v0 caller. It declared 8 bytes; the library must write 8 bytes. */
    probe_t p;
    memset(&p, 0, sizeof p);
    p.caps.struct_size = sizeof p.caps;
    memset(p.guard, 'G', sizeof p.guard);
    hypercore_status_t st = hypercore_engine_get_caps(engine, (hypercore_caps_t*) &p.caps);
    int touched = memcmp(p.guard, "GGGGGGGGGGGGGGGG", 16) != 0;
    printf("v0 caller (declared %zu bytes): status=%d, guard overwritten=%d\n",
           (size_t) p.caps.struct_size, st, touched);

    /* Case 2: a caller that never set struct_size - the memset-zero default a C programmer reaches for. */
    probe_t z;
    memset(&z, 0, sizeof z);
    hypercore_status_t st2 = hypercore_engine_get_caps(engine, (hypercore_caps_t*) &z.caps);
    printf("struct_size=0 caller: status=%d accepted=%d\n", st2, st2 == HYPERCORE_STATUS_SUCCESS);

    /* Case 3: a caller from a future header. Must be refused. */
    hypercore_caps_t future;
    memset(&future, 0, sizeof future);
    future.struct_size = (uint32_t) (sizeof future + 16);
    printf("future caller: status=%d refused=%d\n",
           hypercore_engine_get_caps(engine, &future), hypercore_engine_get_caps(engine, &future) == HYPERCORE_STATUS_INVALID_ARG);

    /* Case 4: prompt + max_new exceeds max_context. generate.cpp:2164 makes this an error; the boundary
       claims to be the place that catches it. */
    hypercore_request_config_t cfg;
    memset(&cfg, 0, sizeof cfg);
    cfg.struct_size = sizeof cfg;
    cfg.temperature = 0.0f; cfg.top_k = 20; cfg.top_p = 1.0f; cfg.max_new_tokens = 4096;
    int32_t prompt[4] = {1, 2, 3, 4};
    hypercore_status_t st4 = hypercore_engine_submit(engine, next_id(), &cfg, prompt, 4, on_chunk, NULL);
    printf("prompt 4 + max_new 4096, max_context 4096: status=%d rejected=%d\n", st4, st4 == HYPERCORE_STATUS_INVALID_ARG);

    hypercore_engine_destroy(engine);
    printf("%s\n", touched ? "FAIL: the prefix rule writes past the caller's struct" : "PASS: prefix rule holds");
    return touched ? 1 : 0;
}
