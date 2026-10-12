#!/bin/bash
# tune_host_core.sh - sweep --host-core (first | last) on the best memory topology found
# by tune_hypercore5.sh. This pins the thread that runs the host loop before the pool and
# the session pin anything else (src/program/generate.cpp:1915), so the two arms differ
# only in which core the decode driver sits on.
#
#   ./tune/tune_host_core.sh
#   ./tune/tune_host_core.sh --vram 768 --pcie 0.95
#   ./tune/tune_host_core.sh --dry-run
#
# Results: tune/results/host-core-<date>.csv plus one engine log per run.
# The GPU must be free: ./restart.sh stop first.

source "$(dirname "$0")/lib.sh"

VRAM_RESERVE=512
PCIE_FRAC=0.95
AFFINITY=auto
CORES=(first last)
LOG_FILE="$HERE/results/host-core-$(date -u +%Y-%m-%d).csv"

while [ $# -gt 0 ]; do
    case "$1" in
        --vram)     VRAM_RESERVE="${2:?--vram needs a number}"; shift 2 ;;
        --pcie)     PCIE_FRAC="${2:?--pcie needs a number}"; shift 2 ;;
        --affinity) AFFINITY="${2:?--affinity needs auto, p-cores or all}"; shift 2 ;;
        --cores)    CORES=(${2//,/ }); shift 2 ;;
        --dry-run)  export TUNE_DRY_RUN=1; shift ;;
        -h|--help)  sed -n '2,8p' "$0"; exit 2 ;;
        *) echo "tune_host_core.sh: unknown argument: $1" >&2; exit 2 ;;
    esac
done

lib_selfcheck || exit 2
require_free_gpu || exit 3
base_args
token_ids

echo "=== HYPERCORE HOST CORE STRATEGY SWEEP ==="
echo "Fixed: --vram-reserve-mib $VRAM_RESERVE --pcie-frac $PCIE_FRAC --pool-affinity $AFFINITY, prompt $PROMPT_TOKENS tokens, --max-new $MAX_NEW"
echo "Host_Core,Status,Tokens_Per_Sec" > "$LOG_FILE"

best_tps=0
best_core=""
measured=0

for core in "${CORES[@]}"; do
    run_engine "host-core-${core}" --host-core "$core" --pool-affinity "$AFFINITY" \
        --vram-reserve-mib "$VRAM_RESERVE" --pcie-frac "$PCIE_FRAC"
    echo "$core,$RUN_STATUS,$RUN_TPS" >> "$LOG_FILE"
    if [ "$RUN_STATUS" = PASS ]; then
        measured=$((measured + 1))
        if awk -v a="$RUN_TPS" -v b="$best_tps" 'BEGIN { exit (a > b) ? 0 : 1 }'; then
            best_tps="$RUN_TPS"; best_core="$core"
        fi
    fi
done

echo "=========================================="
echo "HOST CORE SWEEP COMPLETE: ${measured} of ${#CORES[@]} measured"
echo "results: $LOG_FILE"
if [ -n "$best_core" ]; then
    echo "best: --host-core ${best_core} at ${best_tps} tok/s"
else
    echo "nothing measured; nothing to recommend"
fi
echo "=========================================="
