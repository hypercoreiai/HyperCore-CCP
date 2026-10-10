/* bench/results/2026-10-09-blackbox-api/busy_test.c
 * HYPERCORE_STATUS_BUSY has to be reachable, and it has to mean "slots full", not "the counter is stuck".
 *
 * The engine releases a slot when the stream ends, so a test that wants to prove BUSY must keep the
 * streams running while it submits. max_new_tokens drives the stub's duration (40ms + 0.5ms/token),
 * so 128 tokens holds a slot for ~104 ms.
 *
 * Build: gcc -std=c11 -Wall -Wextra -I. busy_test.c -L. -lhypercore_engine -Wl,-rpath,. -o busy_test
 */
#include "hypercore/hypercore_api.h"
#include <stdio.h>
#include <string.h>
static uint64_t next_id(void) { static uint64_t n = 0; return ++n; }

static void on_chunk(const hypercore_output_chunk_t* c, void* u) { (void) c; (void) u; }

int main(void) {
    hypercore_engine_t* engine = NULL;
    if (hypercore_engine_init(&engine, "{\"batch\": 2}") != HYPERCORE_STATUS_SUCCESS) { printf("FAIL: init\n"); return 1; }

    hypercore_caps_t caps;
    memset(&caps, 0, sizeof caps);
    caps.struct_size = sizeof caps;
    hypercore_engine_get_caps(engine, &caps);
    printf("engine reports %u slots\n", caps.max_batch_slots);

    hypercore_request_config_t cfg;
    memset(&cfg, 0, sizeof cfg);
    cfg.struct_size = sizeof cfg;
    cfg.temperature = 0.0f; cfg.top_k = 1; cfg.top_p = 1.0f; cfg.max_new_tokens = 128;
    cfg.pcie_frac = -1.0f; cfg.spec_min_p = -1.0f;

    int32_t prompt[2] = {1, 2};
    int first_busy = -1;
    for (int i = 0; i < 4; ++i) {
        hypercore_status_t st = hypercore_engine_submit(engine, next_id(), &cfg, prompt, 2, on_chunk, NULL);
        printf("submit %d -> %s\n", i,
               st == HYPERCORE_STATUS_SUCCESS ? "ok" : (st == HYPERCORE_STATUS_BUSY ? "BUSY" : "rejected"));
        if (st == HYPERCORE_STATUS_BUSY && first_busy < 0) first_busy = i;
    }

    hypercore_engine_destroy(engine);   /* joins the streams; slots are released by the engine */

    printf("%s\n", first_busy == 2 ? "PASS: BUSY exactly when the slots are full" : "FAIL: slot accounting wrong");
    return first_busy == 2 ? 0 : 1;
}
