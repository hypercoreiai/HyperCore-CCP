#!/bin/bash
# run_production.sh - production launch of the tuned configuration.
#
#   ./tune/run_production.sh              start it and stay attached (Ctrl+C shuts down)
#   ./tune/run_production.sh --check      verify the paths and the GPU, launch nothing
#
# The parameters are the ones tune_hypercore5.sh measured best on this box:
# --vram-reserve-mib 512, --pcie-frac 0.95. That measurement was taken at
# --max-context 4096; this launcher runs the production 262144 context, so the tok/s of
# the two are not comparable.
#
# THREE BUGS THIS VERSION FIXES
#   1. ROOT was this directory (tune/), so "$ROOT/engine/hypercore", "$ROOT/data/..." and
#      "$ROOT/data/experimental-speed-projection/..." did not exist.
#   2. `set -euo pipefail` plus `((boot_counter++))`: the arithmetic command returns the
#      OLD value, so the first increment (0) is a non-zero exit status and the script died
#      after one second of boot, always reporting "Engine dropped during initialization".
#   3. No check that the GPU is free. With serve already running the engine boots into a
#      VRAM it does not have.

set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="${HYPERCORE_ROOT:-$(dirname "$HERE")}"
ENGINE="$ROOT/engine/hypercore"
PACK="/home/ai-agent/HyperCore-data/packs/q2_0"
NATIVE="/home/ai-agent/HyperCore-data/models/Q2_0/Qwen3.8-Flash-Next-GSQ-RCO-Q2_0-00001-of-00002.gguf"
PLE_GGUF="/home/ai-agent/HyperCore-data/models/Q2_0/Qwen3.8-Flash-Next-GSQ-RCO-Q2_0-00002-of-00002.gguf"
EXPERT_PROFILE="$ROOT/data/expert-profile.bin"
MTP="/home/ai-agent/HyperCore-data/mtp/rt"
CVEC_SCALED="$ROOT/data/experimental-speed-projection/Qwen3.8-Flash-Next-experimental-speed-projection.gguf:1.0"

FIFO_IN="$HERE/production_in.fifo"
PRODUCTION_LOG="$HERE/hypercore_production.log"
BOOT_TIMEOUT="${BOOT_TIMEOUT:-300}"
VRAM_RESERVE=512
PCIE_FRAC=0.95
MAX_CONTEXT=262144
CHECK_ONLY=0

while [ $# -gt 0 ]; do
    case "$1" in
        --vram)        VRAM_RESERVE="${2:?--vram needs a number}"; shift 2 ;;
        --pcie)        PCIE_FRAC="${2:?--pcie needs a number}"; shift 2 ;;
        --max-context) MAX_CONTEXT="${2:?--max-context needs a number}"; shift 2 ;;
        --check)       CHECK_ONLY=1; shift ;;
        -h|--help)     sed -n '2,15p' "$0"; exit 2 ;;
        *) echo "run_production.sh: unknown argument: $1" >&2; exit 2 ;;
    esac
done

for p in "$ENGINE" "$PACK" "$NATIVE" "$PLE_GGUF" "$MTP"; do
    [ -e "$p" ] || { echo "run_production.sh: missing $p" >&2; exit 1; }
done
[ -f "$EXPERT_PROFILE" ] || echo "note: no expert profile at $EXPERT_PROFILE; the engine will build one"

free="$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | head -1)"
if [ "${free:-0}" -lt 12000 ]; then
    echo "run_production.sh: GPU busy, ${free} MiB free. Stop the running server first: ./restart.sh stop" >&2
    exit 3
fi

if [ "$CHECK_ONLY" = 1 ]; then
    echo "paths ok, engine at $ENGINE, ${free} MiB of GPU free"
    exit 0
fi

rm -f "$FIFO_IN"
mkfifo "$FIFO_IN"
exec 3<>"$FIFO_IN"   # keep a writer open so the engine's stdin never sees EOF

echo "[*] Starting HyperCore: vram-reserve ${VRAM_RESERVE} MiB, pcie-frac ${PCIE_FRAC}, resident experts, context ${MAX_CONTEXT}"

"$ENGINE" --serve \
    --pack "$PACK" \
    --native "$NATIVE" \
    --ple-gguf "$PLE_GGUF" \
    --expert-profile "$EXPERT_PROFILE" \
    --expert-cache auto \
    --prefill auto \
    --spec 4 \
    --mtp "$MTP" \
    --max-context "$MAX_CONTEXT" \
    --kv q4_0 \
    --resident-experts \
    --control-vector-scaled "$CVEC_SCALED" \
    --control-vector-layer-range 4 44 \
    --cvec-mode project \
    --cvec-dir per-layer \
    --spec-min-p 0.80 \
    --pcie-frac "$PCIE_FRAC" \
    --vram-reserve-mib "$VRAM_RESERVE" \
    --expert-profile-save-every 10 \
    <"$FIFO_IN" >"$PRODUCTION_LOG" 2>&1 &

ENGINE_PID=$!

cleanup() {
    echo "[*] termination signal: shutting down cleanly"
    if kill -0 "$ENGINE_PID" 2>/dev/null; then
        printf 'QUIT\n' >&3 2>/dev/null || true
        exec 3>&- 2>/dev/null || true
        sleep 2
        kill -TERM "$ENGINE_PID" 2>/dev/null || true
        kill -0 "$ENGINE_PID" 2>/dev/null && kill -KILL "$ENGINE_PID" 2>/dev/null
    fi
    rm -f "$FIFO_IN"
    echo "[*] shutdown complete"
}
trap cleanup SIGINT SIGTERM EXIT

echo -n "    --> loading weights, pinning the arena, building the graphs... "
booted=0
ready=0
while [ "$booted" -lt "$BOOT_TIMEOUT" ]; do
    if ! kill -0 "$ENGINE_PID" 2>/dev/null; then break; fi
    if grep -q "session is up" "$PRODUCTION_LOG"; then
        ready=1
        echo "ready"
        break
    fi
    sleep 1
    booted=$((booted + 1))
done

if [ "$ready" = 0 ]; then
    echo "FAILED"
    echo "[-] the engine exited during startup; last lines of $PRODUCTION_LOG:"
    tail -n 10 "$PRODUCTION_LOG" | sed 's/^/      /'
    exit 1
fi

echo "=========================================================================="
echo " HyperCore is running (pid $ENGINE_PID)."
echo " watch it:  tail -f $PRODUCTION_LOG"
echo " send work: printf 'GEN 64 1234,5678\n' > $FIFO_IN"
echo " stop it:   Ctrl+C"
echo "=========================================================================="

wait "$ENGINE_PID" 2>/dev/null || true
