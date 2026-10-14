#!/bin/sh
# debug_mmvq_il.sh - run the Q2_0 engine directly (no web UI) with the interleaved
# dense matvec on and its parity check on, so a wrong xil_ copy is named in the log
# instead of showing up as garbled text.
#
# The engine holds the whole card: stop the other engine before running this.
#
#   ./debug_mmvq_il.sh                                  # MMVQ_IL=1 + CHECK=1
#   HYPERCORE_MMVQ_IL=0 ./debug_mmvq_il.sh             # the clean A/B arm
#   EXE=engine/hypercore ./debug_mmvq_il.sh            # the binary nih_run uses
#
# Three arms, in the order they separate the causes:
#   MMVQ_IL=0                    the plain kernels; the control
#   MMVQ_IL=1 REUSE=0          every interleaved call rebuilds its own copy: if this is clean and
#                              REUSE=1 is not, a write to the activations missed invalidate()
#   MMVQ_IL=1 REUSE=1 CHECK=1  the fast arm, with the device-side comparison on
#
# What to look for in the output:
#   "hypercore serve: MMVQ_IL CHECK FAILED: X of Y interleaved calls differ ..."  -> wrong values
#   "interleaved matvec: N copies built, M calls reused one (K calls)"            -> what the window did
#   "MMVQ_IL trace, the N-token window: ..."                                      -> the shapes, in order
# plus a DONE line per request and no core dump.
set -eu

cd "/home/ai-user0/black_box"

EXE="${EXE:-./build/hypercore}"
CFG="${CFG:-ni_hypercore-q2_0.json}"

# The engine arguments come from the model's own config, so this never drifts from setup.sh.
ARGS=$(python3 -c 'import json,sys; print(" ".join(json.load(open(sys.argv[1]))["args"]))' "$CFG")
# Arguments on the command line are appended after the config's, so they override a same flag
# (generate.cpp reads flags in order and the last one wins):  ./debug_mmvq_il.sh --prefill 0
if [ $# -gt 0 ]; then ARGS="$ARGS $*"; fi

# "Complete the open tasks", the prompt the web UI used for the A/B runs.
# A long prompt needs PROMPT_IDS on the SAME line as the command: a bare `PROMPT_IDS=...` in an
# interactive shell is not exported, and the script silently falls back to the 4-token prompt.
PROMPT_IDS="${PROMPT_IDS:-12188,279,1724,8806}"
MAX_NEW="${MAX_NEW:-128}"

export HYPERCORE_MMVQ_IL="${HYPERCORE_MMVQ_IL:-1}"
export HYPERCORE_MMVQ_IL_CHECK="${HYPERCORE_MMVQ_IL_CHECK:-1}"
export HYPERCORE_MMVQ_IL_REUSE="${HYPERCORE_MMVQ_IL_REUSE:-1}"
export HYPERCORE_MMVQ_IL_TRACE="${HYPERCORE_MMVQ_IL_TRACE:-1}"

echo "[debug_mmvq_il] $EXE  MMVQ_IL=$HYPERCORE_MMVQ_IL MMVQ_IL_CHECK=$HYPERCORE_MMVQ_IL_CHECK "
echo "              MMVQ_IL_REUSE=$HYPERCORE_MMVQ_IL_REUSE MMVQ_IL_TRACE=$HYPERCORE_MMVQ_IL_TRACE"
echo "[debug_mmvq_il] prompt: $(( $(printf '%s' "$PROMPT_IDS" | tr -cd ',' | wc -c) + 1 )) token ids"
if [ "${DRY:-0}" = "1" ]; then        # show the command without touching the card
    echo "[debug_mmvq_il] dry run: $EXE --serve $ARGS"
    exit 0
fi

# SANITIZER=1: run the engine under compute-sanitizer. A kernel fault is sticky, so the engine's own
# check() reports it at the next call (here always copy_i32); memcheck names the kernel that actually
# faulted and the out-of-bounds address. It is slow - keep MAX_NEW small and make one request.
if [ "${SANITIZER:-0}" = "1" ]; then
    CS="$(command -v compute-sanitizer || echo /usr/local/cuda/bin/compute-sanitizer)"
    if [ ! -x "$CS" ]; then
        echo "[debug_mmvq_il] compute-sanitizer not found; tried PATH and /usr/local/cuda/bin"
        exit 127
    fi
    echo "[debug_mmvq_il] under $CS (memcheck): one request, MAX_NEW=$MAX_NEW"
    printf 'GEN %s %s\nQUIT\n' "$MAX_NEW" "$PROMPT_IDS" |
      "$CS" --tool memcheck --launch-timeout 120 "$EXE" --serve $ARGS
    exit $?
fi

printf 'GEN %s %s\nGEN %s %s\nQUIT\n' "$MAX_NEW" "$PROMPT_IDS" "$MAX_NEW" "$PROMPT_IDS" |
  "$EXE" --serve $ARGS
