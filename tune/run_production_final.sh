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
BOOT_TIMEOUT=300

[ -x "$ENGINE" ] || { echo "Error: Missing engine binary at $ENGINE" >&2; exit 1; }

# Reset layout buffers cleanly
rm -f "$FIFO_IN"
mkfifo "$FIFO_IN"
exec 3<>"$FIFO_IN"

echo "[*] Initializing HyperCore Peak-Performance Engine Cluster..."
echo "    -> VRAM Reserve: 512 MiB | PCIe Fraction: 0.95"
echo "    -> Core Affinity: ALL cores enabled"
echo "    -> Thread Model: Auto-calculated pool defaults (workers 0)"
echo "    -> Host Orchestrator Routing Thread: LAST core isolation pinned"
echo "    -> Cache Layer Mode: Asynchronous Adaptive Swapping Enabled"

# Launch high performance daemon with fully optimized layout parameters
"$ENGINE" --serve \
    --pack "$PACK" \
    --native "$NATIVE" \
    --ple-gguf "$PLE_GGUF" \
    --expert-profile "$EXPERT_PROFILE" \
    --expert-cache auto \
    --prefill auto \
    --spec 4 \
    --mtp "$MTP" \
    --max-context 262144 \
    --kv q4_0 \
    --resident-experts \
    --control-vector-scaled "$CVEC_SCALED" \
    --control-vector-layer-range 4 44 \
    --cvec-mode project \
    --cvec-dir per-layer \
    --spec-min-p 0.80 \
    --pcie-frac 0.95 \
    --vram-reserve-mib 512 \
    --pool-affinity all \
    --pool-workers 0 \
    --host-core last \
    --adapt-async 1 \
    --expert-profile-save-every 10 \
    <"$FIFO_IN" >"$PRODUCTION_LOG" 2>&1 &

ENGINE_PID=$!

cleanup() {
    echo -e "\n[*] Intercepted termination signal. Shutting down cleanly..."
    if kill -0 "$ENGINE_PID" 2>/dev/null; then
        if [ -e "$FIFO_IN" ]; then
            printf 'QUIT\n' >&3 2>/dev/null || true
        fi
        exec 3>&- 2>/dev/null || true
        sleep 2
        kill -TERM "$ENGINE_PID" 2>/dev/null || true
    fi
    rm -f "$FIFO_IN"
    echo "[*] Shutdown complete. VRAM and Resident Arenas unlocked."
}
trap cleanup SIGINT SIGTERM EXIT

# Monitor pipeline allocation lifecycle
echo -n "    --> Mapping structures and pinning RAM blocks... "
boot_counter=0
ready=0
while [ "$boot_counter" -lt "$BOOT_TIMEOUT" ]; do
    if ! kill -0 "$ENGINE_PID" 2>/dev/null; then break; fi
    if grep -q "session is up" "$PRODUCTION_LOG"; then
        ready=1
        echo "Ready!"
        break
    fi
    sleep 1
    ((boot_counter++))
done

if [ "$ready" = 0 ]; then
    echo "FAILED"
    echo "[-] Engine dropped during initialization sequence. Output tail:"
    tail -n 10 "$PRODUCTION_LOG" | sed 's/^/      /'
    exit 1
fi

echo "=========================================================================="
echo " HyperCore Production Server is running daemonized (PID: $ENGINE_PID)."
echo " Stream runtime tracking logs via: tail -f $PRODUCTION_LOG"
echo " Send interactive generation strings directly down: $FIFO_IN"
echo " send work: printf 'GEN 64 1234,5678\n' > $FIFO_IN"
echo " Press [Ctrl+C] to gracefully terminate this instance and unlock VRAM."
echo "=========================================================================="

wait "$ENGINE_PID" 2>/dev/null || true
