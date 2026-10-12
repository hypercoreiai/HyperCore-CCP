#!/bin/sh
# bench/flag_ab.sh - decode A/B of the two switches ported from Strata:
#   HYPERCORE_ADAPT_OVERLAP  (1 vs 0)
#   HYPERCORE_MMVQ_IL        (1 vs 0)
#
# Same binary, same prompt token ids, same sampling, same --max-new. Only the
# environment variable changes. The prompt is the fixed token list in
# bench/results/exchange-rotation-token-ids.json, so the two arms of each pair
# decode exactly the same context.
#
#   ./bench/flag_ab.sh                      both pairs, 256 decode tokens each
#   ./bench/flag_ab.sh --max-new 512       longer decode
#   ./bench/flag_ab.sh --pair adapt        only the ADAPT_OVERLAP pair
#   ./bench/flag_ab.sh --pair il           only the MMVQ_IL pair
#
# Requires the GPU to be free: stop serve first (./restart.sh stop).
set -eu

ROOT="${HYPERCORE_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
EXE="$ROOT/build/hypercore"
PROMPT="$ROOT/bench/results/exchange-rotation-token-ids.json"
MAX_NEW=256
PAIR="both"
OUT="$ROOT/bench/results/flag-ab-$(date -u +%Y-%m-%d)"

usage() { sed -n '2,15p' "$0"; exit 2; }

while [ $# -gt 0 ]; do
    case "$1" in
        --max-new) MAX_NEW="${2:?--max-new needs a number}"; shift 2 ;;
        --pair)    PAIR="${2:?--pair needs adapt or il}"; shift 2 ;;
        --exe)     EXE="${2:?--exe needs a path}"; shift 2 ;;
        -h|--help) usage ;;
        *) echo "flag_ab.sh: unknown argument: $1" >&2; usage ;;
    esac
done

[ -x "$EXE" ] || { echo "no engine at $EXE: build first"; exit 2; }
[ -f "$PROMPT" ] || { echo "no prompt token file at $PROMPT"; exit 2; }

free_mib() { nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | head -1; }
if [ "$(free_mib)" -lt 12000 ]; then
    echo "GPU busy: $(free_mib) MiB free. Stop the server first: ./restart.sh stop"
    exit 3
fi

ARGS=$(python3 - "$PROMPT" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
print(",".join(str(t) for t in d["input"]))
PY
)

CFG="$ROOT/ni_hypercore-q2_0.json"
BASE=$(python3 - "$CFG" <<'PY'
import json, sys
a = json.load(open(sys.argv[1]))["args"]
# --serve-only flags do not apply to a single generate run.
drop = {"--prompt-cache-every", "--short-read", "--batch", "--slots"}
out, i = [], 0
while i < len(a):
    if a[i] in drop:
        i += 2
        continue
    out.append(a[i]); i += 1
print(" ".join(out))
PY
)

mkdir -p "$OUT"
run() {  # run <arm-name> <env-assignment>
    name="$1"; envassign="$2"
    log="$OUT/$name.log"
    echo "--- $name ($envassign)"
    env $envassign "$EXE" generate $BASE --tokens "$ARGS" --max-new "$MAX_NEW" > "$log" 2>&1
    # The engine's own summary line; grep it rather than recomputing.
    grep -iE "decode|predicted_per_second|tokens/s|tok/s" "$log" | tail -3
    echo "    full log: $log"
}

if [ "$PAIR" = "both" ] || [ "$PAIR" = "adapt" ]; then
    run adapt_off "HYPERCORE_ADAPT_OVERLAP=0"
    run adapt_on  "HYPERCORE_ADAPT_OVERLAP=1"
fi
if [ "$PAIR" = "both" ] || [ "$PAIR" = "il" ]; then
    run il_off "HYPERCORE_MMVQ_IL=0"
    run il_on  "HYPERCORE_MMVQ_IL=1"
fi
echo "results in $OUT"
