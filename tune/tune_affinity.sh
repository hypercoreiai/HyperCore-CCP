#!/bin/bash
# tune_affinity.sh - sweep --pool-affinity (auto | p-cores | all) on the best memory
# topology found by tune_hypercore5.sh.
#
#   ./tune/tune_affinity.sh
#   ./tune/tune_affinity.sh --vram 768 --pcie 0.95
#   ./tune/tune_affinity.sh --dry-run
#
# Results: tune/results/affinity-<date>.csv plus one engine log per run in the same
# directory. The GPU must be free: ./restart.sh stop first.

source "$(dirname "$0")/lib.sh"

VRAM_RESERVE=512
PCIE_FRAC=0.95
MODES=(auto p-cores all)
LOG_FILE="$HERE/results/affinity-$(date -u +%Y-%m-%d).csv"

while [ $# -gt 0 ]; do
    case "$1" in
        --vram)  VRAM_RESERVE="${2:?--vram needs a number}"; shift 2 ;;
        --pcie)  PCIE_FRAC="${2:?--pcie needs a number}"; shift 2 ;;
        --modes) MODES=(${2//,/ }); shift 2 ;;
        --dry-run) export TUNE_DRY_RUN=1; shift ;;
        -h|--help) sed -n '2,8p' "$0"; exit 2 ;;
        *) echo "tune_affinity.sh: unknown argument: $1" >&2; exit 2 ;;
    esac
done

lib_selfcheck || exit 2
require_free_gpu || exit 3
base_args
token_ids

echo "=== HYPERCORE POOL AFFINITY SWEEP ==="
echo "Fixed: --vram-reserve-mib $VRAM_RESERVE --pcie-frac $PCIE_FRAC, prompt $PROMPT_TOKENS tokens, --max-new $MAX_NEW"
echo "Pool_Affinity,Status,Tokens_Per_Sec" > "$LOG_FILE"

best_tps=0
best_mode=""
measured=0

for mode in "${MODES[@]}"; do
    run_engine "affinity-${mode}" --pool-affinity "$mode" --vram-reserve-mib "$VRAM_RESERVE" --pcie-frac "$PCIE_FRAC"
    echo "$mode,$RUN_STATUS,$RUN_TPS" >> "$LOG_FILE"
    if [ "$RUN_STATUS" = PASS ]; then
        measured=$((measured + 1))
        if awk -v a="$RUN_TPS" -v b="$best_tps" 'BEGIN { exit (a > b) ? 0 : 1 }'; then
            best_tps="$RUN_TPS"; best_mode="$mode"
        fi
    fi
done

echo "=========================================="
echo "AFFINITY SWEEP COMPLETE: ${measured} of ${#MODES[@]} measured"
echo "results: $LOG_FILE"
if [ -n "$best_mode" ]; then
    echo "best: --pool-affinity ${best_mode} at ${best_tps} tok/s"
else
    echo "nothing measured; nothing to recommend"
fi
echo "=========================================="
