#!/bin/bash
# tune/lib.sh - the shared plumbing for every sweep in this directory.
#
# Each sweep needs the same four things: a free GPU, the production argument list, one
# GEN request down stdin, and the decode rate off the DONE line the engine prints for it.
# Only the swept flag differs, so that part lives here and each script just declares its
# own grid.
#
#   source "$(dirname "$0")/lib.sh"
#   require_free_gpu
#   run_engine "affinity-auto" --pool-affinity auto      # sets RUN_STATUS and RUN_TPS
#
# WHY THE OLD SCRIPTS ALL FAILED
#   1. `ROOT="$(dirname "$0")"` is this directory, tune/, not the engine tree, so
#      "$ROOT/engine/hypercore", "$ROOT/data/..." and "$ROOT/bench/results/..." do not
#      exist. tune_host_core.sh additionally pointed the pack and the model at
#      /home/ai-user0/HyperCore-data, which does not exist either; the real one is
#      /home/ai-agent/HyperCore-data. Every row of those sweeps was FAIL_BOOT.
#   2. `engine/hypercore --serve` is not an HTTP server. It reads requests on stdin, one
#      per line (src/program/generate.cpp:5128-5140), and answers on stdout. The HTTP API
#      is serve/server.py. A curl to a port that was never opened can only ever fail.
#   3. A run that dies is reported as a stall. With --vram-reserve-mib 256 the engine
#      exits at boot with "mtp: the draft head does not fit" (src/core/mtp.cpp:624) and
#      the sweep just burns the full timeout and logs CRASH_MID_INITIALIZATION.

set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENGINE_ROOT="${HYPERCORE_ROOT:-$(dirname "$HERE")}"
RESULTS_DIR="$HERE/results"

ENGINE="$ENGINE_ROOT/engine/hypercore"
PACK="/home/ai-agent/HyperCore-data/packs/q2_0"
NATIVE="/home/ai-agent/HyperCore-data/models/Q2_0/Qwen3.8-Flash-Next-GSQ-RCO-Q2_0-00001-of-00002.gguf"
PLE_GGUF="/home/ai-agent/HyperCore-data/models/Q2_0/Qwen3.8-Flash-Next-GSQ-RCO-Q2_0-00002-of-00002.gguf"
EXPERT_PROFILE="$ENGINE_ROOT/data/expert-profile.bin"
MTP="/home/ai-agent/HyperCore-data/mtp/rt"
CVEC_SCALED="$ENGINE_ROOT/data/experimental-speed-projection/Qwen3.8-Flash-Next-experimental-speed-projection.gguf:1.0"
PROMPT="$ENGINE_ROOT/bench/results/exchange-rotation-token-ids.json"

MAX_NEW="${TUNE_MAX_NEW:-256}"
MAX_CONTEXT="${TUNE_MAX_CONTEXT:-4096}"
BOOT_TIMEOUT="${TUNE_BOOT_TIMEOUT:-300}"
RUN_TIMEOUT="${TUNE_RUN_TIMEOUT:-180}"
RESIDENT="${TUNE_RESIDENT:-0}"

RUN_STATUS="FAIL"
RUN_TPS="0.0"
RUN_LOG=""

lib_selfcheck() {
    [ -x "$ENGINE" ] || { echo "tune/lib.sh: no engine at $ENGINE. Build it, or set HYPERCORE_ROOT." >&2; return 2; }
    [ -f "$PROMPT" ] || { echo "tune/lib.sh: no prompt token file at $PROMPT" >&2; return 2; }
    [ -f "$EXPERT_PROFILE" ] || echo "note: no expert profile at $EXPERT_PROFILE; the engine will build one"
    mkdir -p "$RESULTS_DIR"
    return 0
}

free_mib() { nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | head -1; }

require_free_gpu() {
    # A dry run launches nothing, so it does not need the card.
    [ "${TUNE_SKIP_GPU_CHECK:-0}" = 1 ] && return 0
    [ "${TUNE_DRY_RUN:-0}" = 1 ] && return 0
    local free
    free="$(free_mib)"
    if [ "${free:-0}" -lt 12000 ]; then
        echo "GPU busy: ${free} MiB free. Stop the server first: ./restart.sh stop" >&2
        return 3
    fi
    return 0
}

# The reason an engine stopped, taken from its own last complaint.
failure_reason() {
    local log="$1"
    if grep -q "does not fit" "$log"; then
        echo "NO_VRAM_FOR_MTP: the draft head does not fit; raise --vram-reserve-mib, use --draft-vocab en, or lower --max-context"
        return
    fi
    if grep -q "out of memory" "$log"; then
        echo "NO_VRAM: a device allocation failed"
        return
    fi
    local line
    line="$(grep -o 'hypercore [a-z]*: [^\n]*' "$log" | tail -1)"
    [ -n "$line" ] && echo "$line" || echo "the engine exited with no message"
}

# run_engine <label> [extra engine flags...]
# Sets RUN_STATUS (PASS / FAIL_BOOT / NO_VRAM_FOR_MTP / NO_TOKENS / TIMEOUT) and RUN_TPS.
run_engine() {
    local label="$1"; shift
    RUN_LOG="$RESULTS_DIR/run-${label}.log"
    RUN_STATUS="FAIL"
    RUN_TPS="0.0"

    echo "[*] ${label}"
    rm -f "$RUN_LOG"

    if [ "${TUNE_DRY_RUN:-0}" = 1 ]; then
        echo "    $ENGINE ${BASE_ARGS[*]} $*"
        return 0
    fi

    local fifo="$RESULTS_DIR/in.fifo"
    rm -f "$fifo"
    mkfifo "$fifo"
    exec 3<>"$fifo"

    "$ENGINE" "${BASE_ARGS[@]}" "$@" <"$fifo" >"$RUN_LOG" 2>&1 &
    local pid=$!

    echo -n "    --> boot... "
    local ready=0 n=0
    while [ "$n" -lt "$BOOT_TIMEOUT" ]; do
        if ! kill -0 "$pid" 2>/dev/null; then break; fi
        if grep -q "session is up" "$RUN_LOG"; then ready=1; echo "ready"; break; fi
        sleep 1
        n=$((n + 1))
    done
    if [ "$ready" = 0 ]; then
        RUN_STATUS="FAIL_BOOT"
        echo "    [FAIL] the engine never reached 'session is up' within ${BOOT_TIMEOUT}s"
        echo "      $(failure_reason "$RUN_LOG")"
        kill -TERM "$pid" 2>/dev/null
        exec 3>&-
        return 1
    fi

    # One request, then QUIT. The rate comes from the DONE line the engine prints for it:
    # DONE <generated> <prompt_tokens> <prompt_ms> <decode_ms> <finish> ... (generate.cpp:10192)
    echo -n "    --> generating ${MAX_NEW} tokens... "
    printf 'GEN %s %s\n' "$MAX_NEW" "$TOKEN_IDS" >&3
    local done=0 m=0
    while [ "$m" -lt "$RUN_TIMEOUT" ]; do
        if ! kill -0 "$pid" 2>/dev/null; then break; fi
        if grep -q '^DONE ' "$RUN_LOG"; then done=1; echo "done"; break; fi
        sleep 1
        m=$((m + 1))
    done
    if [ "$done" = 0 ]; then
        RUN_STATUS="$(grep -o 'does not fit\|out of memory' "$RUN_LOG" | head -1)"
        RUN_STATUS="${RUN_STATUS:+NO_VRAM_FOR_MTP}"
        RUN_STATUS="${RUN_STATUS:-TIMEOUT}"
        echo "    [FAIL] no DONE line within ${RUN_TIMEOUT}s"
        echo "      $(failure_reason "$RUN_LOG")"
        kill -TERM "$pid" 2>/dev/null
        exec 3>&-
        return 1
    fi

    printf 'QUIT\n' >&3
    exec 3>&-
    local g=0
    for _ in 1 2 3 4 5 6 7 8 9 10; do kill -0 "$pid" 2>/dev/null || break; sleep 1; g=$((g + 1)); done
    kill -TERM "$pid" 2>/dev/null
    kill -0 "$pid" 2>/dev/null && kill -KILL "$pid" 2>/dev/null

    RUN_TPS=$(awk '$1 == "DONE" && $5 > 0 { printf "%.2f", $2 * 1000.0 / $5; exit }' "$RUN_LOG")
    [ -z "$RUN_TPS" ] && RUN_TPS="0.0"

    if awk -v t="$RUN_TPS" 'BEGIN { exit (t > 0) ? 0 : 1 }'; then
        RUN_STATUS="PASS"
        echo "    [PASS] ${RUN_TPS} tok/s"
        return 0
    fi
    RUN_STATUS="NO_TOKENS"
    echo "    [FAIL] the request finished but produced no tokens"
    return 1
}

# The argument list every sweep shares; each script appends the flag it is testing.
base_args() {
    BASE_ARGS=(--serve
        --pack "$PACK"
        --native "$NATIVE"
        --ple-gguf "$PLE_GGUF"
        --expert-profile "$EXPERT_PROFILE"
        --expert-cache auto
        --prefill auto
        --spec 4
        --mtp "$MTP"
        --max-context "$MAX_CONTEXT"
        --kv q4_0
        --control-vector-scaled "$CVEC_SCALED"
        --control-vector-layer-range 4 44
        --cvec-mode project
        --cvec-dir per-layer
        --spec-min-p 0.80
        --expert-profile-save-every 0)
    if [ "$RESIDENT" = 1 ]; then BASE_ARGS+=(--resident-experts); else BASE_ARGS+=(--mmap-experts); fi
}

token_ids() {
    TOKEN_IDS=$(python3 - "$PROMPT" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
print(",".join(str(t) for t in d["input"]))
PY
)
    PROMPT_TOKENS=$(printf '%s\n' "$TOKEN_IDS" | tr ',' '\n' | wc -l)
}
