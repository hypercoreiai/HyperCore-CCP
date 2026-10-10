/* src/interface/engine_process.h
 *
 * The boundary's link to a real engine.
 *
 * Until this file existed the boundary could not express model loading: hypercore_engine_init
 * read numeric knobs and run_request produced tokens from a fixture. That is what the note in
 * cli_gateway.cpp called out as the gap. This is the smallest way to close it without
 * rewriting src/program/generate.cpp: the boundary keeps its contract (submit, the stream
 * callback, the terminal summary) and drives the real engine as a child process over the
 * text protocol that engine already speaks in --serve mode.
 *
 * Why a process and not generate.cpp linked in: the engine's setup is process-level - CUDA/HIP
 * context, the expert arena, the pinned embedding, the VRAM tier. generate.cpp is one main()
 * that owns all of it. Linking it into the .so would mean inventing an internal API for it
 * before the boundary has a reason to have one. Spawning it is the shape the engine already
 * has, and the numbers the summary reports then come from the engine's own DONE line rather
 * than from a fixture constant.
 *
 * Not part of the public ABI: hypercore_engine_t is opaque in hypercore_api.h, so an engine
 * instance can hold one of these without changing a single byte of the wire contract.
 */
#ifndef HYPERCORE_ENGINE_PROCESS_H
#define HYPERCORE_ENGINE_PROCESS_H

#include <cstdio>
#include <mutex>
#include <string>
#include <vector>

#include <sys/types.h>

#include "hypercore/hypercore_api.h"

namespace hypercore::iface {

/* A resident engine process, spoken to through its stdin/stdout.
 *
 * The engine's --serve protocol (src/program/generate.cpp):
 *   stdin :  GEN <max_new> <id,id,...>   STOP   QUIT
 *   stdout:  READY <max_context> <stop_id>
 *            INFO model=... batch_slots=... max_context=...
 *            RESUME <n>   REUSED <n>      PP <pos> <total> <ms> <tok/s>
 *            T <id>                       DONE <generated> <prompt> <prompt_ms>
 *                                            <decode_ms> <finish> <drafts_accepted>
 *                                            <drafts_offered> <reused> [chain fields]
 *            ERR <message>
 *
 * Requests are driven one at a time. That is not a limitation of this adapter: the engine's
 * serve loop reads one line, runs it to completion, and only then reads the next. STOP is
 * the exception - it is read on the engine's own input thread and reaches a request that is
 * still running, which is how a cancelled stream ends short.
 */
class EngineProcess {
public:
    EngineProcess() = default;
    ~EngineProcess();

    EngineProcess(const EngineProcess&) = delete;
    EngineProcess& operator=(const EngineProcess&) = delete;

    /* Start the engine and wait for READY. Returns false with an explanation in err if the
       executable cannot be started, the engine reports ERR, or it never becomes ready. */
    bool start(const std::string& exe, const std::vector<std::string>& args,
               double startup_timeout_s, std::string& err);

    /* Run one request. Tokens go to the callback as they arrive; out is filled from the
       engine's DONE line. Returns false if the engine died or reported an error. */
    bool run(const std::vector<int32_t>& prompt, uint32_t max_new,
             hypercore_stream_cb callback, void* user_data,
             hypercore_request_summary_t& out, std::string& err);

    /* Ask the running request to stop. The engine still ends it with a DONE line, so the
       caller always gets a summary. */
    void request_stop();

    /* QUIT and reap. Safe to call twice. */
    void shutdown();

    bool alive() const { return alive_; }
    int64_t max_context() const { return max_context_; }
    int64_t batch_slots() const { return batch_slots_; }
    const std::string& version() const { return version_; }
    const std::string& last_error() const { return last_err_; }

private:
    bool read_line(std::string& out);

    FILE* in_ = nullptr;               // the engine's stdin
    FILE* out_ = nullptr;              // the engine's stdout
    pid_t pid_ = -1;
    bool alive_ = false;
    int64_t max_context_ = 0;
    int64_t batch_slots_ = 0;
    std::string version_;
    std::string last_err_;
    std::mutex req_mu_;                // one request in flight, as the serve loop expects
};

}  // namespace hypercore::iface

#endif  // HYPERCORE_ENGINE_PROCESS_H
