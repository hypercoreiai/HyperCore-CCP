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

# "Complete the open tasks", the prompt the web UI used for the A/B runs.
PROMPT_IDS="${PROMPT_IDS:-12188,279,1724,8806}"
MAX_NEW="${MAX_NEW:-128}"

export HYPERCORE_MMVQ_IL="${HYPERCORE_MMVQ_IL:-1}"
export HYPERCORE_MMVQ_IL_CHECK="${HYPERCORE_MMVQ_IL_CHECK:-1}"
export HYPERCORE_MMVQ_IL_REUSE="${HYPERCORE_MMVQ_IL_REUSE:-1}"
export HYPERCORE_MMVQ_IL_TRACE="${HYPERCORE_MMVQ_IL_TRACE:-1}"

echo "[debug_mmvq_il] $EXE  MMVQ_IL=$HYPERCORE_MMVQ_IL MMVQ_IL_CHECK=$HYPERCORE_MMVQ_IL_CHECK "
echo "              MMVQ_IL_REUSE=$HYPERCORE_MMVQ_IL_REUSE MMVQ_IL_TRACE=$HYPERCORE_MMVQ_IL_TRACE"

printf 'GEN %s %s\nGEN %s %s\nQUIT\n' "$MAX_NEW" "$PROMPT_IDS" "$MAX_NEW" "$PROMPT_IDS" |
  "$EXE" --serve $ARGS
