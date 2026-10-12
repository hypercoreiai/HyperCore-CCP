#!/bin/sh
# gpu_tests.sh - run the GPU parity tests only when the card is actually free.
#
# The parity harnesses allocate their own weights and activations, so they fail with
# "CUDA: malloc ... out of memory" the moment serve or another engine holds the card.
# This script waits for the VRAM to be free, then runs the tests. If the card never
# frees up it exits 3 without running anything, so a busy GPU is never mistaken for a
# failing one.
#
#   ./gpu_tests.sh                                   run the new harnesses, once, no waiting
#   ./gpu_tests.sh --wait 600                        poll until the card is free, up to 10 minutes
#   ./gpu_tests.sh --min-free-mib 12000              how much free VRAM counts as free
#   ./gpu_tests.sh --stop-serve                      stop the running server first (restart.sh stop)
#   ./gpu_tests.sh --tests 'nan_guard_parity|mmvq_il_parity'   which ctest tests to run
#   ./gpu_tests.sh --all                             every registered test
#   ./gpu_tests.sh --bench                           pass --bench --emit-table to the IL harness
#   ./gpu_tests.sh --dry-run                         print what would run, touch nothing
#
# Exit codes: 0 all tests passed, 1 a test failed, 3 the GPU never freed up, 2 bad arguments.
set -eu

ROOT="${HYPERCORE_ROOT:-$(cd "$(dirname "$0")" && pwd)}"
BUILD="$ROOT/build"
MIN_FREE_MIB=12000
WAIT_S=0
POLL_S=5
TESTS='nan_guard_parity|mmvq_il_parity'
RUN_ALL=0
STOP_SERVE=0
BENCH=0
DRY=0
STAMP="$(date -u +%Y-%m-%d_%H%M%S)"
LOG="$ROOT/build/gpu_tests_$STAMP.log"

usage() {
    sed -n '2,16p' "$0"
    exit 2
}

while [ $# -gt 0 ]; do
    case "$1" in
        --min-free-mib) MIN_FREE_MIB="${2:?--min-free-mib needs a number}"; shift 2 ;;
        --wait)         WAIT_S="${2:?--wait needs seconds}"; shift 2 ;;
        --poll)         POLL_S="${2:?--poll needs seconds}"; shift 2 ;;
        --tests)        TESTS="${2:?--tests needs a ctest regex}"; shift 2 ;;
        --all)          RUN_ALL=1; shift ;;
        --stop-serve)   STOP_SERVE=1; shift ;;
        --bench)        BENCH=1; shift ;;
        --dry-run)      DRY=1; shift ;;
        -h|--help)      usage ;;
        *) echo "gpu_tests.sh: unknown argument: $1" >&2; usage ;;
    esac
done

say() { printf '%s\n' "$*"; }

free_vram_mib() {
    # nvidia-smi is the only reliable "is the card free" source here: CUDA's own
    # cudaMemGetInfo needs a context, and creating one on a full card is what we are
    # trying to avoid.
    if ! command -v nvidia-smi >/dev/null 2>&1; then return -1; fi
    nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits 2>/dev/null |
        head -1 | tr -d ' '
}

gpu_free() {
    f="$(free_vram_mib)"
    [ "$f" = "" ] && return 1
    [ "$f" -ge "$MIN_FREE_MIB" ]
}

if [ ! -d "$BUILD" ]; then
    say "no build directory at $BUILD: configure and build first"
    exit 2
fi

if [ "$DRY" = 1 ]; then
    say "project : $ROOT"
    say "build   : $BUILD"
    say "free now: $(free_vram_mib) MiB of $(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null | head -1) MiB"
    say "gate    : at least $MIN_FREE_MIB MiB free, waiting up to $WAIT_S s"
    if [ "$RUN_ALL" = 1 ]; then
        say "tests   : every registered test (ctest --test-dir $BUILD)"
    else
        say "tests   : ctest --test-dir $BUILD -R '$TESTS'"
    fi
    [ "$BENCH" = 1 ] && say "extra   : --bench --emit-table on the IL harness"
    exit 0
fi

if [ "$STOP_SERVE" = 1 ]; then
    "$ROOT/restart.sh" stop >/dev/null 2>&1 || say "no server to stop"
    sleep 3
fi

tries=0
while :; do
    tries=$((tries + 1))
    if gpu_free; then break; fi
    if [ "$WAIT_S" -le 0 ]; then
        say "GPU busy: $(free_vram_mib) MiB free, the tests need $MIN_FREE_MIB MiB."
        say "Run with --wait <seconds> to poll until the card is free, or stop the server first (--stop-serve)."
        exit 3
    fi
    if [ $((tries * POLL_S)) -ge "$WAIT_S" ]; then
        say "GPU still busy after ${WAIT_S}s: $(free_vram_mib) MiB free."
        exit 3
    fi
    say "GPU busy ($(free_vram_mib) MiB free), polling every ${POLL_S}s for up to ${WAIT_S}s ..."
    sleep "$POLL_S"
done

say "GPU free: $(free_vram_mib) MiB available. Running the tests, log: $LOG"

status=0
if [ "$RUN_ALL" = 1 ]; then
    ctest --test-dir "$BUILD" > "$LOG" 2>&1 || status=1
else
    ctest --test-dir "$BUILD" -R "$TESTS" > "$LOG" 2>&1 || status=1
fi
cat "$LOG"

if [ "$BENCH" = 1 ] && [ -x "$BUILD/mmvq_il_parity" ]; then
    say "--- IL row table measured on this card (docs/MMVQ_IL_TABLE.md)"
    "$BUILD/mmvq_il_parity" --bench --emit-table >> "$LOG" 2>&1 || status=1
    tail -40 "$LOG"
fi

if [ "$status" -ne 0 ]; then
    say "result: failures. See $LOG"
    exit 1
fi
say "result: all tests passed. Log: $LOG"
