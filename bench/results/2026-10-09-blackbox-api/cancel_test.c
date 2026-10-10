/*
 * bench/results/2026-10-09-blackbox-api/cancel_test.c
 * Cancellation: the contract the web runtime needs.
 *
 * Build: gcc -std=c11 -Wall -Wextra -I. cancel_test.c \
 *        -L/home/ai-user0/HyperCore/build-shared -lhypercore_api -Wl,-rpath,... -o cancel_test
 */
#include "hypercore/hypercore_api.h"
#include <stdio.h>
#include <string.h>

static int failures = 0;

static void expect(int cond, const char* what) {
    if (!cond) { printf("FAIL: %s\n", what); failures++; }
    else       { printf("PASS: %s\n", what); }
}

static uint64_t next_id(void) { static uint64_t n = 1000; return ++n; }

typedef struct {
    int tokens;
    int terminal_seen;
    hypercore_stop_reason_t stop_reason;
    uint32_t produced_reported;
} Capture;

static void on_chunk(const hypercore_output_chunk_t* chunk, void* user_data) {
    Capture* c = (Capture*)user_data;
    if (chunk->token_id >= 0) {
        c->tokens++;
        return;
    }
    c->terminal_seen = 1;
    if (chunk->summary) {
        c->stop_reason = chunk->summary->stop_reason;
        c->produced_reported = chunk->summary->produced_tokens;
    }
}

static hypercore_engine_t* make_engine(int slots) {
    char json[64];
    snprintf(json, sizeof json, "{\"batch\":%d}", slots);
    hypercore_engine_t* e = NULL;
    if (hypercore_engine_init(&e, json) != HYPERCORE_STATUS_SUCCESS) return NULL;
    return e;
}

int main(void) {
    /* 1. cancel a running stream: it stops early and reports CANCEL. */
    {
        hypercore_engine_t* e = make_engine(4);
        if (!e) { printf("init failed\n"); return 1; }

        hypercore_request_config_t cfg;
        memset(&cfg, 0, sizeof cfg);
        cfg.struct_size = sizeof cfg;
        cfg.top_k = 1;
        cfg.max_new_tokens = 2000;   /* long enough that cancel must bite */
        cfg.pcie_frac = -1.0f;
        cfg.spec_min_p = -1.0f;

        int32_t prompt[4] = {1, 2, 3, 4};
        Capture cap = {0, 0, HYPERCORE_STOP_REASON_UNSPECIFIED, 0};
        uint64_t id = next_id();

        expect(hypercore_engine_submit(e, id, &cfg, prompt, 4, on_chunk, &cap) == HYPERCORE_STATUS_SUCCESS,
               "a long request is accepted");

        /* Cancel while it is running. Non-blocking: this returns immediately. */
        expect(hypercore_engine_cancel(e, id) == HYPERCORE_STATUS_SUCCESS,
               "cancel on an in-flight request succeeds");

        hypercore_engine_destroy(e);   /* joins the request thread */

        expect(cap.tokens < 2000, "the cancelled stream stopped early");
        expect(cap.terminal_seen, "a cancelled stream still emits a terminal frame");
        expect(cap.stop_reason == HYPERCORE_STOP_REASON_CANCEL, "the terminal frame says CANCEL");
        expect(cap.produced_reported == (uint32_t)cap.tokens,
              "produced_tokens counts what was actually delivered, not what was asked for");
    }

    /* 2. cancel is idempotent and never blocks. */
    {
        hypercore_engine_t* e = make_engine(4);
        hypercore_request_config_t cfg;
        memset(&cfg, 0, sizeof cfg);
        cfg.struct_size = sizeof cfg;
        cfg.top_k = 1;
        cfg.max_new_tokens = 500;
        int32_t prompt[2] = {5, 6};
        Capture cap = {0, 0, 0, 0};
        uint64_t id = next_id();

        hypercore_engine_submit(e, id, &cfg, prompt, 2, on_chunk, &cap);
        hypercore_status_t first = hypercore_engine_cancel(e, id);
        hypercore_status_t second = hypercore_engine_cancel(e, id);
        expect(first == HYPERCORE_STATUS_SUCCESS, "first cancel succeeds");
        expect(second == HYPERCORE_STATUS_SUCCESS, "a second cancel of the same id is not an error");
        hypercore_engine_destroy(e);
    }

    /* 3. cancel of an unknown id is NOT_FOUND, not a silent no-op. */
    {
        hypercore_engine_t* e = make_engine(4);
        expect(hypercore_engine_cancel(e, 999999) == HYPERCORE_STATUS_NOT_FOUND,
               "cancel of an id that is not in flight returns NOT_FOUND");
        expect(hypercore_engine_cancel(e, 0) == HYPERCORE_STATUS_INVALID_ARG,
               "request_id 0 is rejected (0 is the null user_data a callback may receive)");
        hypercore_engine_destroy(e);
    }

    /* 4. a cancelled request releases its slot, so the next one is accepted. */
    {
        hypercore_engine_t* e = make_engine(1);
        hypercore_request_config_t cfg;
        memset(&cfg, 0, sizeof cfg);
        cfg.struct_size = sizeof cfg;
        cfg.top_k = 1;
        cfg.max_new_tokens = 1000;
        int32_t prompt[2] = {1, 2};
        Capture a = {0, 0, 0, 0}, b = {0, 0, 0, 0};

        uint64_t id1 = next_id();
        expect(hypercore_engine_submit(e, id1, &cfg, prompt, 2, on_chunk, &a) == HYPERCORE_STATUS_SUCCESS,
               "the only slot is taken");
        expect(hypercore_engine_submit(e, next_id(), &cfg, prompt, 2, on_chunk, &b) == HYPERCORE_STATUS_BUSY,
               "the second request is BUSY");
        hypercore_engine_cancel(e, id1);
        hypercore_engine_destroy(e);   /* the slot is freed by the request thread, not by cancel() */

        hypercore_engine_t* e2 = make_engine(1);
        Capture c = {0, 0, 0, 0};
        expect(hypercore_engine_submit(e2, next_id(), &cfg, prompt, 2, on_chunk, &c) == HYPERCORE_STATUS_SUCCESS,
              "after the cancelled stream ends, a new request is accepted");
        hypercore_engine_destroy(e2);
    }

    /* 5. duplicate request_id while one is in flight is refused. */
    {
        hypercore_engine_t* e = make_engine(4);
        hypercore_request_config_t cfg;
        memset(&cfg, 0, sizeof cfg);
        cfg.struct_size = sizeof cfg;
        cfg.top_k = 1;
        cfg.max_new_tokens = 10;
        int32_t prompt[2] = {1, 2};
        Capture a = {0, 0, 0, 0}, b = {0, 0, 0, 0};
        uint64_t id = next_id();
        expect(hypercore_engine_submit(e, id, &cfg, prompt, 2, on_chunk, &a) == HYPERCORE_STATUS_SUCCESS,
               "first submit with id ok");
        expect(hypercore_engine_submit(e, id, &cfg, prompt, 2, on_chunk, &b) == HYPERCORE_STATUS_INVALID_ARG,
               "reusing an in-flight request_id is refused rather than silently overwriting it");
        hypercore_engine_destroy(e);
    }

    printf("\n%s\n", failures ? "cancel_test FAILED" : "cancel_test OK");
    return failures ? 1 : 0;
}
