/* bench/results/2026-10-09-blackbox-api/config_test.c
 * The two config forms: inline JSON and a path to a JSON file.
 *
 * Build:
 *   gcc -std=c11 -Wall -Wextra -I. config_test.c \
 *       -L/home/ai-user0/HyperCore/build-shared -lhypercore_api -Wl,-rpath,/home/ai-user0/HyperCore/build-shared -o config_test
 *
 * The rule being tested is decided by the first non-whitespace character, so every case
 * here is a case where a heuristic would have been needed - and there is none.
 */
#define _POSIX_C_SOURCE 200809L
#include "hypercore/hypercore_api.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

static int failures = 0;

static void check(int condition, const char* what) {
    printf("%s: %s\n", condition ? "PASS" : "FAIL", what);
    if (!condition) failures++;
}

/* Build an engine from a config and report the resolved batch slots. */
static long slots_from(const char* config) {
    hypercore_engine_t* engine = NULL;
    if (hypercore_engine_init(&engine, config) != HYPERCORE_STATUS_SUCCESS) return -1;
    hypercore_caps_t caps;
    memset(&caps, 0, sizeof caps);
    caps.struct_size = (uint32_t) sizeof caps;   /* the caller declares its own layout */
    long slots = -1;
    if (hypercore_engine_get_caps(engine, &caps) == HYPERCORE_STATUS_SUCCESS)
        slots = (long) caps.max_batch_slots;
    hypercore_engine_destroy(engine);
    return slots;
}

static void write_file(const char* path, const char* body) {
    FILE* f = fopen(path, "wb");
    if (!f) { printf("FAIL: cannot write %s\n", path); failures++; return; }
    fwrite(body, 1, strlen(body), f);
    fclose(f);
}

int main(void) {
    const char* cfg = "/tmp/hc_config_test.json";
    const char* empty = "/tmp/hc_config_empty.json";
    const char* array = "/tmp/hc_config_array.json";
    const char* huge = "/tmp/hc_config_huge.json";

    /* 1. Inline JSON still works, and is not confused with a path. */
    check(slots_from("{\"batch\":3}") == 3, "inline JSON is used verbatim");
    check(slots_from("  {\"batch\":4}  ") == 4, "padded inline JSON is still inline");

    /* 2. A path is read once and applied. */
    write_file(cfg, "{\"batch\": 5, \"pool_workers\": 2}");
    check(slots_from(cfg) == 5, "a file path is read and applied");
    check(slots_from("   ") > 0, "a blank config is accepted as no config");

    /* 3. A path with leading whitespace is still a path. */
    check(slots_from("   /tmp/hc_config_test.json") == 5, "a padded path resolves to the file");

    /* 4. A missing file is an argument error, not "no config". */
    hypercore_engine_t* engine = NULL;
    check(hypercore_engine_init(&engine, "/tmp/does-not-exist.json") == HYPERCORE_STATUS_INVALID_ARG,
          "a missing file is INVALID_ARG, not defaults");
    if (engine) { hypercore_engine_destroy(engine); engine = NULL; }

    /* 5. A file that is not an object is refused. */
    write_file(array, "[1, 2, 3]");
    check(hypercore_engine_init(&engine, array) == HYPERCORE_STATUS_INVALID_ARG,
          "a JSON array is not an engine config");
    if (engine) { hypercore_engine_destroy(engine); engine = NULL; }

    /* 6. An empty file is a hard configuration error, not "no config": a provisioning
          script that created the file but never wrote it must not run on hidden defaults. */
    write_file(empty, "");
    check(hypercore_engine_init(&engine, empty) == HYPERCORE_STATUS_INVALID_ARG,
          "an empty file is INVALID_ARG, not defaults");
    if (engine) { hypercore_engine_destroy(engine); engine = NULL; }
    write_file(empty, "   \n  ");
    check(hypercore_engine_init(&engine, empty) == HYPERCORE_STATUS_INVALID_ARG,
          "whitespace is not a configuration either");
    if (engine) { hypercore_engine_destroy(engine); engine = NULL; }
    check(hypercore_engine_init(&engine, NULL) == HYPERCORE_STATUS_SUCCESS,
          "an absent argument is the only way to get defaults");
    if (engine) { hypercore_engine_destroy(engine); engine = NULL; }

    /* 7. The ceiling is 10 MB: one byte over is refused before anything is allocated,
          and a valid 9 MB object is accepted. */
    {
        FILE* f = fopen(huge, "wb");
        if (f) {
            fputs("{\"batch\":6}", f);
            for (long i = 0; i < 10u * 1024u * 1024u + 8; ++i) fputc(' ', f);
            fclose(f);
        }
        check(hypercore_engine_init(&engine, huge) == HYPERCORE_STATUS_INVALID_ARG,
              "a config larger than 10 MB is refused, not half-read");
        if (engine) hypercore_engine_destroy(engine);
        engine = NULL;

        FILE* g = fopen(huge, "wb");
        if (g) {
            fputs("{\"batch\":7}", g);
            for (long i = 0; i < 9u * 1024u * 1024u; ++i) fputc(' ', g);
            fclose(g);
        }
        check(slots_from(huge) == 7, "a 9 MB configuration is accepted");
    }

    /* 8. The same ceiling applies to an inline argument, checked before the copy. */
    {
        const size_t n = 10u * 1024u * 1024u;
        char* over = (char*)malloc(n + 16);
        char* at   = (char*)malloc(n + 1);
        if (!over || !at) { printf("FAIL: out of memory\n"); failures++; return 1; }
        over[0] = '{';
        for (size_t i = 1; i < n + 8; ++i) over[i] = ' ';
        over[n + 8] = '}';
        over[n + 9] = '\0';
        check(hypercore_engine_init(&engine, over) == HYPERCORE_STATUS_INVALID_ARG,
              "an inline payload over 10 MB is refused");
        if (engine) { hypercore_engine_destroy(engine); engine = NULL; }

        memcpy(at, "{\"batch\":8}", 11);   /* exactly 10 MB once padded inside the object */
        for (size_t i = 11; i < n; ++i) at[i] = ' ';
        at[n] = '\0';
        check(slots_from(at) == 8, "an inline payload of exactly 10 MB is accepted");
        free(over); free(at);
    }

    /* 9. Worker mode with a path: the child is handed the resolved text, never the path,
       so the file is read exactly once and a restart cannot read a changed file. */
    {
        const char* worker_cfg = "/tmp/hc_config_worker.json";
        write_file(worker_cfg,
                  "{\"engine_mode\": \"worker\", "
                  "\"worker_binary\": \"/home/ai-user0/HyperCore/build-shared/hypercore-worker\", "
                  "\"ipc_socket\": \"/tmp/hc_config_worker.sock\", "
                  "\"batch\": 6}");
        hypercore_engine_t* e = NULL;
        int ok = 0;
        if (hypercore_engine_init(&e, worker_cfg) == HYPERCORE_STATUS_SUCCESS) {
            hypercore_caps_t caps;
            memset(&caps, 0, sizeof caps);
            caps.struct_size = (uint32_t) sizeof caps;
            ok = hypercore_engine_get_caps(e, &caps) == HYPERCORE_STATUS_SUCCESS &&
                 caps.max_batch_slots == 6;
            hypercore_engine_destroy(e);   /* also reaps the child */
        } else if (e) {
            hypercore_engine_destroy(e);
        }
        check(ok, "a path config also drives the out-of-process worker");
    }

    /* 10. Precedence is unchanged: the file sits at the same level as inline JSON,
       so it beats the environment. */
    {
        const char* before = getenv("HYPERCORE_POOL_WORKERS");
        setenv("HYPERCORE_POOL_WORKERS", "7", 1);
        write_file(cfg, "{\"pool_workers\": 2}");
        hypercore_caps_t caps;
        memset(&caps, 0, sizeof caps);
        caps.struct_size = (uint32_t) sizeof caps;
        hypercore_engine_t* e = NULL;
        int ok = 0;
        if (hypercore_engine_init(&e, cfg) == HYPERCORE_STATUS_SUCCESS) {
            ok = hypercore_engine_get_caps(e, &caps) == HYPERCORE_STATUS_SUCCESS &&
                 caps.active_pool_workers == 2;
            hypercore_engine_destroy(e);
        }
        check(ok, "a file config overrides the environment, exactly as inline JSON does");
        if (before) setenv("HYPERCORE_POOL_WORKERS", before, 1); else unsetenv("HYPERCORE_POOL_WORKERS");
    }

    printf("\n%s: %d failure(s)\n", failures ? "CONFIG TEST FAILED" : "config test passed", failures);
    return failures ? 1 : 0;
}
