#!/bin/sh
# debug_mmvq_il_ab.sh - the three-arm A/B for HYPERCORE_MMVQ_IL, one arm after another.
#
# The card must be free: stop the other engine first (the web UI's Stop button, or
#   curl -X POST -H 'Content-Type: application/json' -H 'Authorization: Bearer <key>' \
#        -d '{}' http://127.0.0.1:8081/unload)
#
#   ./debug_mmvq_il_ab.sh                 # all three arms
#   ./debug_mmvq_il_ab.sh 2               # only arm 2
#
# Arm 1  MMVQ_IL=0                      the plain kernels: the control.
# Arm 2  MMVQ_IL=1 REUSE=0             every interleaved call builds its own copy.
# Arm 3  MMVQ_IL=1 REUSE=1 CHECK=1     the fast arm, checked against native_mmvq on the device.
#
# Clean = the reply is ordinary text.  Garbled = token soup ("スポンサー", fragments).
# What the trace lines say:
#   "MMVQ_IL CHECK FAILED: X of Y interleaved calls differ"  -> a copy that is not the source's
#   "interleaved matvec: N copies built, M calls reused one"  -> the guard's behaviour in the window
#
# Output: debug/ab<arm>_<MMVQ_IL>-<REUSE>.txt, plus a one-line summary per arm.
set -eu

cd "/home/ai-user0/black_box"

ARMS="1 2 3"
if [ $# -ge 1 ]; then ARMS="$1"; fi

for arm in $ARMS; do
    case "$arm" in
        1) IL=0; REUSE=1; CHECK=0 ;;
        2) IL=1; REUSE=0; CHECK=1 ;;
        3) IL=1; REUSE=1; CHECK=1 ;;
        *) echo "unknown arm $arm"; exit 1 ;;
    esac
    out="debug/ab${arm}_IL${IL}-REUSE${REUSE}.txt"
    echo "[ab] arm $arm: MMVQ_IL=$IL REUSE=$REUSE CHECK=$CHECK -> $out"
    HYPERCORE_MMVQ_IL="$IL" HYPERCORE_MMVQ_IL_REUSE="$REUSE" HYPERCORE_MMVQ_IL_CHECK="$CHECK" \
      HYPERCORE_MMVQ_IL_TRACE=1 EXE=./engine/hypercore \
      ./debug_mmvq_il.sh >"$out" 2>&1 || echo "[ab] arm $arm exited nonzero (see $out)"
    echo "[ab] arm $arm done: $(grep -c 'MMVQ_IL CHECK FAILED' "$out") failed-check lines, " \
         "$(grep -c 'interleaved matvec' "$out") window reports"
    sleep 6
done
