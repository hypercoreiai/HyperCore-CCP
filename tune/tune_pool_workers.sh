#!/bin/bash
# tune_pool_workers.sh - sweep --pool-workers on the best memory topology found by
# tune_hypercore5.sh. 0 is the engine's own default (every physical core except the one
# the host loop spins on), so it is the baseline every other row is compared against.
#
#   ./tune/tune_pool_workers.sh
#   ./tune/tune_pool_workers.sh --workers 0,8,16
#   ./tune/tune_pool_workers.sh --dry-run
#
# Results: tune/results/pool-workers-<date>.csv plus one engine log per run.
# The GPU must be free: ./restart.sh stop first.

source "$(dirname "$0")/lib.sh"

VRAM_RESERVE=512
PCIE_FRAC=0.95
CORES="$(nproc)"
WORKERS=(0 4 8 16 "$CORES")
LOG_FILE="$HERE/results/pool-workers-$(date -u +%Y-%m-%d).csv"

while [ $# -gt 0 ]; do
    case "$1" in
        --vram)     VRAM_RESERVE="${2:?--vram needs a number}"; shift 2 ;;
        --pcie)     PCIE_FRAC="${2:?--pcie needs a number}"; shift 2 ;;
        --workers)  WORKERS=(${2//,/ }); shift 2 ;;
        --dry-run)  export TUNE_DRY_RUN=1; shift ;;
        -h|--help)  sed -n '2,8p' "$0"; exit 2 ;;
        *) echo "tune_pool_workers.sh: unknown argument: $1" >&2; exit 2 ;;
    esac
done

lib_selfcheck || exit 2
require_free_gpu || exit 3
base_args
token_ids

echo "=== HYPERCORE CPU POOL WORKER SWEEP ==="
echo "Fixed: --vram-reserve-mib $VRAM_RESERVE --pcie-frac $PCIE_FRAC, ${CORES} cores visible, prompt $PROMPT_TOKENS tokens, --max-new $MAX_NEW"
echo "Pool_Workers,Status,Tokens_Per_Sec" > "$LOG_FILE"

best_tps=0
best_workers=""
measured=0

for w in "${WORKERS[@]}"; do
    run_engine "workers-${w}" --pool-workers "$w" --vram-reserve-mib "$VRAM_RESERVE" --pcie-frac "$PCIE_FRAC"
    echo "$w,$RUN_STATUS,$RUN_TPS" >> "$LOG_FILE"
    if [ "$RUN_STATUS" = PASS ]; then
        measured=$((measured + 1))
        if awk -v a="$RUN_TPS" -v b="$best_tps" 'BEGIN { exit (a > b) ? 0 : 1 }'; then
            best_tps="$RUN_TPS"; best_workers="$w"
        fi
    fi
done

echo "=========================================="
echo "POOL WORKER SWEEP COMPLETE: ${measured} of ${#WORKERS[@]} measured"
echo "results: $LOG_FILE"
if [ -n "$best_workers" ]; then
    echo "best: --pool-workers ${best_workers} at ${best_tps} tok/s"
else
    echo "nothing measured; nothing to recommend"
fi
echo "=========================================="
