/* bench/results/2026-10-09-blackbox-api/precedence_test.c
 * The three-layer precedence the contract promises: defaults -> environment -> JSON.
 *
 * Build: gcc -std=c11 -Wall -Wextra -I. precedence_test.c -L. -lhypercore_engine -Wl,-rpath,. -o precedence_test
 *
 * Note what this test can no longer do. The authorized hypercore_caps_t exposes struct_size,
 * backend_type, max_batch_slots and max_context_len - nothing else. HYPERCORE_POOL_WORKERS is still
 * parsed by the bridge, but there is no field through which a caller can see what it resolved to.
 * A setting that can be set but not read is not a capability; it is a side effect. So the
 * precedence assertions below run against the two fields the boundary does report:
 * max_batch_slots and active_pool_workers.
 */
#include "hypercore/hypercore_api.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Reads the caps AFTER the call. Reading them inside the same argument list as the call is the
 * bug that made an earlier run report batch=0 while the bridge had correctly parsed batch=2:
 * C evaluates arguments in an unspecified order, and gcc evaluated them right-to-left. */
static int caps(const char* json, uint32_t* slots, uint32_t* context, int32_t* workers) {
    hypercore_engine_t* eng = NULL;
    if (hypercore_engine_init(&eng, json) != HYPERCORE_STATUS_SUCCESS) return -1;
    hypercore_caps_t c;
    memset(&c, 0, sizeof c);
    c.struct_size = sizeof c;
    int st = hypercore_engine_get_caps(eng, &c);
    *slots = c.max_batch_slots;
    *context = c.max_context_len;
    *workers = c.active_pool_workers;
    hypercore_engine_destroy(eng);
    return st;
}

int main(void) {
    const char* env_batch = getenv("HYPERCORE_BATCH");
    const char* env_pool  = getenv("HYPERCORE_POOL_WORKERS");
    uint32_t s = 0, ctx = 0;
    int32_t w = 0;
    int ok = 1;

    /* 1. defaults only. */
    ok &= caps(NULL, &s, &ctx, &w) == HYPERCORE_STATUS_SUCCESS;
    printf("no env, no json              -> slots=%u context=%u pool=%d\n", s, ctx, w);
    if (!env_batch) ok &= (s == 4 && ctx == 4096);
    ok &= (w > 0);   /* the -1 "engine decides" sentinel must never reach a caller */

    /* 2. the environment overrides the default. */
    if (env_batch) {
        ok &= caps(NULL, &s, &ctx, &w) == HYPERCORE_STATUS_SUCCESS;
        printf("env HYPERCORE_BATCH=%s       -> slots=%u\n", env_batch, s);
        ok &= (s == (uint32_t) atoi(env_batch));
    }
    if (env_pool) {
        ok &= caps(NULL, &s, &ctx, &w) == HYPERCORE_STATUS_SUCCESS;
        printf("env HYPERCORE_POOL_WORKERS=%s -> pool=%d\n", env_pool, w);
        ok &= (w == (int32_t) atoi(env_pool));
    }

    /* 3. JSON overrides the environment, on both fields. */
    ok &= caps("{\"batch\":2,\"max_context\":1024,\"pool_workers\":3}", &s, &ctx, &w) == HYPERCORE_STATUS_SUCCESS;
    printf("env=%s/%s, json batch=2 pool=3 -> slots=%u context=%u pool=%d\n",
           env_batch ? env_batch : "(unset)", env_pool ? env_pool : "(unset)", s, ctx, w);
    ok &= (s == 2 && ctx == 1024 && w == 3);

    /* 4. an unparseable value must not silently become 0. batch=0 is refused at init, so a silent
       0 from a bad parse would surface as an engine that cannot run at all. */
    ok &= caps("{\"batch\":\"four\",\"pool_workers\":\"four\"}", &s, &ctx, &w) == HYPERCORE_STATUS_SUCCESS;
    printf("json batch=\"four\" pool=\"four\" -> slots=%u pool=%d (neither may be 0)\n", s, w);
    ok &= (s != 0 && w != 0);

    printf("%s\n", ok ? "PASS: precedence holds on every reported capability" : "FAIL: precedence");
    return ok ? 0 : 1;
}
