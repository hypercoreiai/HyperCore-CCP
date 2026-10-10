/* bench/results/2026-10-09-blackbox-api/worker_mode_test.c
 * The out-of-process mode is an implementation detail, not a second API.
 *
 * Every assertion here uses the same five entry points as the in-process tests. The only
 * difference is one key in the init config. If an embedder has to learn anything else, the
 * encapsulation has leaked.
 *
 * Build: gcc -std=c11 -Wall -Wextra -I. worker_mode_test.c \
 *        -L/home/ai-user0/HyperCore/build-shared -lhypercore_api -Wl,-rpath,/home/ai-user0/HyperCore/build-shared \
 *        -o worker_mode_test
 */
#define _POSIX_C_SOURCE 200809L
#include "hypercore/hypercore_api.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <signal.h>
#include <time.h>

static int failures = 0;

static void wait_ms(int ms) {
    struct timespec ts = { ms / 1000, (long)(ms % 1000) * 1000000L };
    nanosleep(&ts, NULL);
}


static void check(int condition, const char* what) {
    if (!condition) {
        printf("FAIL: %s\n", what);
        ++failures;
    } else {
        printf("PASS: %s\n", what);
    }
}

typedef struct {
    int tokens;
    int terminal;
    int stop_reason;
    uint32_t produced;
    uint32_t struct_size;
} capture;

static void on_chunk(const hypercore_output_chunk_t* chunk, void* user_data) {
    capture* c = (capture*)user_data;
    if (chunk->summary) {
        c->terminal = 1;
        c->stop_reason = chunk->summary->stop_reason;
        c->produced = chunk->summary->produced_tokens;
        c->struct_size = chunk->summary->struct_size;
    } else {
        c->tokens += 1;
    }
}

/* Where the worker binary lives. Hardcoding one build directory makes the test
 * portable only on the machine that built it, so the candidates are tried in
 * order: an explicit override, the local build directory, a build directory
 * derived from this file's own path, then the binary the CI harness uploads next
 * to the test. The library has no default worker binary; assertion 6 checks that,
 * and it clears the override first so the check is honest. */
static char worker_path[1024];

static int usable(const char* path) { return access(path, X_OK) == 0; }

static const char* worker_binary(void) {
    const char* override = getenv("HYPERCORE_WORKER_BINARY");
    if (override && *override) return override;
    if (usable("./hypercore-worker")) return "./hypercore-worker";

    /* Walk up from this file's own directory, so the test is runnable from any
     * cwd rather than only from inside a build directory. */
    char here[900];
    if (__FILE__[0] == '/') {
        snprintf(here, sizeof here, "%s", __FILE__);
    } else {
        char cwd[512];
        if (!getcwd(cwd, sizeof cwd)) return NULL;
        snprintf(here, sizeof here, "%s/%s", cwd, __FILE__);
    }
    for (int level = 0; level < 8; level++) {
        char* slash = strrchr(here, '/');
        if (!slash) break;
        *slash = '\0';
        snprintf(worker_path, sizeof worker_path,
                 "%s/build-shared/hypercore-worker", here);
        if (usable(worker_path)) return worker_path;
        snprintf(worker_path, sizeof worker_path,
                 "%s/build-cuda/hypercore-worker", here);
        if (usable(worker_path)) return worker_path;
    }

    if (usable("/home/ai-user0/HyperCore/build-shared/hypercore-worker"))
        return "/home/ai-user0/HyperCore/build-shared/hypercore-worker";
    return NULL;   /* no binary anywhere: assertion 6 reports it as INVALID_ARG */
}

int main(void) {
    const char* worker = worker_binary();
    if (!worker) {
        printf("FAIL: no hypercore-worker binary found; build it or set HYPERCORE_WORKER_BINARY\n");
        return 1;
    }

    /* ---- 1. the same contract, one extra key ---- */
    char config[512];
    snprintf(config, sizeof config,
             "{\"engine_mode\":\"worker\",\"worker_binary\":\"%s\","
             "\"ipc_socket\":\"/tmp/hc_mode_test.sock\",\"batch\":2}", worker);

    hypercore_engine_t* engine = NULL;
    check(hypercore_engine_init(&engine, config) == HYPERCORE_STATUS_SUCCESS,
          "worker mode initialises through the same entry point");
    if (!engine) return 1;

    hypercore_caps_t caps = {0};
    caps.struct_size = sizeof caps;
    check(hypercore_engine_get_caps(engine, &caps) == HYPERCORE_STATUS_SUCCESS,
          "caps are readable in worker mode");
    check(caps.max_batch_slots == 2 && caps.active_pool_workers > 0,
          "caps report resolved numbers, not the -1 sentinel");

    /* ---- 2. a request crosses the process boundary and comes back as frames ---- */
    int32_t prompt[] = {5, 6, 7, 5, 6, 7, 5, 6, 7};
    hypercore_request_config_t cfg = {0};
    cfg.struct_size = sizeof cfg;
    cfg.max_new_tokens = 12;
    cfg.top_k = 1;

    capture got = {0};
    check(hypercore_engine_submit(engine, 1, &cfg, prompt, sizeof prompt / sizeof prompt[0], on_chunk, &got)
              == HYPERCORE_STATUS_SUCCESS,
          "submit() returns the same status in both modes");

    for (int waited = 0; waited < 200 && !got.terminal; ++waited) wait_ms(50);

    check(got.terminal == 1, "the stream terminates with a summary frame");
    check(got.tokens > 0, "tokens arrive through the caller's own callback");
    check(got.produced == (uint32_t)got.tokens,
          "produced_tokens matches the number of token frames delivered");
    check(got.stop_reason == HYPERCORE_STOP_REASON_LIMIT ||
          got.stop_reason == HYPERCORE_STOP_REASON_EOS,
          "the stop reason is a real one");

    /* ---- 3. two requests share one socket and stay separated ---- */
    capture a = {0}, b = {0};
    cfg.max_new_tokens = 120;   /* long enough that both are still running when the gate is tested */
    check(hypercore_engine_submit(engine, 10, &cfg, prompt, sizeof prompt / sizeof prompt[0], on_chunk, &a)
              == HYPERCORE_STATUS_SUCCESS, "first concurrent request accepted");
    check(hypercore_engine_submit(engine, 11, &cfg, prompt, sizeof prompt / sizeof prompt[0], on_chunk, &b)
              == HYPERCORE_STATUS_SUCCESS, "second concurrent request accepted");

    /* ---- 4. the slot gate still refuses a third request ---- */
    check(hypercore_engine_submit(engine, 12, &cfg, prompt, sizeof prompt / sizeof prompt[0], on_chunk, &a)
              == HYPERCORE_STATUS_BUSY,
          "the boundary still answers BUSY when every slot is held");

    /* ---- 5. cancel reaches the child over the wire ---- */
    check(hypercore_engine_cancel(engine, 10) == HYPERCORE_STATUS_SUCCESS,
          "cancel() works in worker mode");
    check(hypercore_engine_cancel(engine, 999) == HYPERCORE_STATUS_NOT_FOUND,
          "an unknown request id is still reported as not found");

    for (int waited = 0; waited < 200 && !(a.terminal && b.terminal); ++waited) wait_ms(50);
    check(a.terminal && b.terminal, "both streams reach a terminal frame");
    check(a.stop_reason == HYPERCORE_STOP_REASON_CANCEL,
          "the cancelled stream ends with STOP_REASON_CANCEL, not a silent truncation");
    check(b.tokens > 0 && a.tokens < b.tokens,
          "cancel shortened one stream without stopping the other");

    /* ---- 6. an engine process that cannot start is reported, not propagated ---- */
    hypercore_engine_t* dead = NULL;
    char bad[256];
    snprintf(bad, sizeof bad,
             "{\"engine_mode\":\"worker\",\"worker_binary\":\"/bin/false\","
             "\"ipc_socket\":\"/tmp/hc_dead_test.sock\"}");
    check(hypercore_engine_init(&dead, bad) == HYPERCORE_STATUS_ENGINE_DEAD,
          "a worker that exits immediately gives ENGINE_DEAD, not a signal in the host");
    check(dead == NULL, "a failed init leaves no half-built engine behind");

    /* src/interface/hypercore_bridge.cpp:445 takes the worker binary from the
     * environment before the JSON, the same precedence as every other setting.
     * A bare {"engine_mode":"worker"} is therefore only a missing-binary error
     * when the override is clear; with HYPERCORE_WORKER_BINARY set the binary
     * exists and init must succeed. Clear the override to test the refusal, then
     * restore it and prove the environment is honoured as a real source. */
    const char* env_worker = getenv("HYPERCORE_WORKER_BINARY");
    unsetenv("HYPERCORE_WORKER_BINARY");
    check(hypercore_engine_init(&dead, "{\"engine_mode\":\"worker\"}") == HYPERCORE_STATUS_INVALID_ARG,
          "worker mode with no binary from JSON or the environment is an argument error, not a silent fallback");
    if (env_worker && *env_worker) {
        setenv("HYPERCORE_WORKER_BINARY", env_worker, 1);
        hypercore_engine_t* from_env = NULL;
        check(hypercore_engine_init(&from_env,
                "{\"engine_mode\":\"worker\",\"ipc_socket\":\"/tmp/hc_env_test.sock\"}")
              == HYPERCORE_STATUS_SUCCESS,
              "the environment override is honoured as a worker binary source");
        if (from_env) hypercore_engine_destroy(from_env);
    }

    if (engine) hypercore_engine_destroy(engine);

    /* A second engine in the default mode must still work in the same process. */
    hypercore_engine_t* local = NULL;
    check(hypercore_engine_init(&local, "{\"batch\":1}") == HYPERCORE_STATUS_SUCCESS,
          "in-process mode is still the default and still works");
    if (local) {
        capture c2 = {0};
        cfg.max_new_tokens = 8;
        check(hypercore_engine_submit(local, 1, &cfg, prompt, sizeof prompt / sizeof prompt[0], on_chunk, &c2)
                  == HYPERCORE_STATUS_SUCCESS,
              "the default engine runs side by side with a worker-mode one");
        for (int waited = 0; waited < 100 && !c2.terminal; ++waited) wait_ms(50);
        check(c2.terminal, "the default engine's stream completes");
        hypercore_engine_destroy(local);
    }

    printf("%s\n", failures ? "worker mode: FAILURES" : "worker mode: all checks passed");
    return failures ? 1 : 0;
}
