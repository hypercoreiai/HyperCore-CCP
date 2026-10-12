#!/usr/bin/env bash
#
# max_tune.sh - multi-dimensional parameter matrix sweep for the HyperCore engine.
#
#   ./tune/max_tune.sh --model q2_0 --short                  calibrate, freeze it, sweep the rest: 17 runs
#   ./tune/max_tune.sh --model q2_0                          the staged sweep, 26 runs
#   ./tune/max_tune.sh --model q2_0 --full                   the whole 3888-run Cartesian product
#   ./tune/max_tune.sh --model q2_0 --layers topology,kv    only these layers
#   ./tune/max_tune.sh --model q2_0 --dry-run               print the command lines, launch nothing
#   ./tune/max_tune.sh --model q2_0 --limit 40              stop after N configurations
#
# Outputs
#   tune/hypercore_max_tuning_matrix-<stamp>.log   the summary table, <stamp> = YYYY-MM-DD_HHMMSS UTC
#   tune/results/matrix-<stamp>.csv        the same rows, machine readable
#   tune/results/run-<stamp>-<label>.log   one engine log per configuration
#   tune/max_config_<model>.sh             the winning parameters
#   tune/max_run_<model>.sh                the production launcher
#   The config and run files are rewritten every time a new winner is measured, so an interrupted
#   sweep (Ctrl-C) still leaves a launcher for the best configuration found so far.
#
# --short
#   Runs the calibration routine first (tools/calibrate.py, the one setup.sh --calibrate uses), takes the
#   argmax of every sweep it measured - pcie-frac, spec-min-p, pool-workers, the adaptive expert tier - and
#   freezes those values for the rest of the sweep. calibrate.py's MIN_GAIN comparison against the product
#   defaults is deliberately not applied here: the highest measured value wins even when it is below the
#   default. The layers those values cover (the pcie half of topology, pool-workers) then have a single
#   option and are dropped, leaving 3 vram + 2 ple-io + 3 kv + 2 kv-grow + 2 host-core + 3 affinity + 2 tail
#   = 17 boots instead of 26. --short --full is the Cartesian product of what is left (432 boots).
#   The calibration is measured at --sweep-context, not at the run config's own context, so the frozen values
#   belong to the conditions the matrix runs under. --calibrate-report <json> reuses an earlier measurement
#   instead of re-measuring; --calibrate-config <json> names the run config to measure. Either of those
#   implies --short: handing the script a report is the same request, without the 15-30 minute measurement.
#   A calibration that fails stops the run rather than quietly degrading into a plain sweep.
#   The modes are covered by tools/test_max_tune_short.py.
#
# CORRECTIONS APPLIED TO THE ORIGINAL BRIEF
#   1. The full product is 3*3*2*3*2*2*3*3*2 = 3888 boots. At ~60-90 s per boot that is
#      two days of wall time. The default is therefore a staged sweep: each layer is
#      swept with the previous layers frozen at their best, 26 runs, and --full is there
#      for the complete matrix. This is the method tune_affinity.sh and tune_pool_workers.sh
#      already use.
#   2. --prompt-cache-tail is inert with the 1024-token prompt in lib.sh. The tail
#      checkpoint only fires when the prompt crosses a prefill chunk boundary
#      (src/program/generate.cpp:6715 needs prompt_cache > 0, prompt_cache_every > 0 and
#      pp_total - done <= the chunk size; --prefill auto chunks at 8192). This script
#      builds a 10240-token prompt by cycling bench/results/exchange-rotation-token-ids.json
#      so the arm can actually differ.
#   3. --vram-reserve-mib 256 does not boot with --spec 4 --mtp on this box: results/
#      tune-hypercore5-2026-10-12/run-256-*.log ends with "mtp: the draft head does not
#      fit" and the engine's own hint asks for ~829 MiB. The arm is kept (the recovery
#      hook handles it) but three FAILED rows are expected.
#   4. "--max-context 131072 prevents early memory allocation stalls" is backwards: a
#      larger context allocates more KV at boot. tune/131072_hypercore_production.log line
#      43 reports 195 MiB free and "requests may stall; add --vram-reserve-mib 829". The
#      value is kept as requested, exposed as --sweep-context, and paired with the
#      --kv-grow arm, which is what actually relieves the pressure.
#   5. --ple-io ram cannot pin the 28.8 GB PLE table here: ulimit -l is 8192 KB and
#      cannot be raised by this account. The engine prints "PLE table mlock failed" and
#      the pages stay unpinned, so the ram arm degrades to mmap. The script detects it
#      and labels the row.
#   6. --pool-workers 0 is not zero workers: 0 means "all physical cores minus the host"
#      (src/program/generate.cpp:409), which is 23 on this i9-14900KF. The 0 and 23 arms
#      are the same pool; the script records the effective count from the INFO line and
#      skips the duplicate.
#   7. set -euo pipefail plus ((i++)) kills the script: the arithmetic command returns the
#      OLD value, so the first increment exits 1. Every counter here uses i=$((i + 1)).
#   8. engine/hypercore --serve is not an HTTP server. It reads "GEN <max_new> <ids>" on
#      stdin and answers on stdout (src/program/generate.cpp:5128-5140). The FIFO is kept
#      open on fd 3 so the engine never sees EOF, and QUIT goes down that fd before the
#      SIGTERM.
#
# Requires: bash 4.4+, nvidia-smi, python3, and a free GPU (./restart.sh stop first).
# The tools run under the project venv when there is one: install.sh and setup.sh put the
# dependencies (regex, for tools/hypercore_tokenizer.py) in .venv, and the system python3
# does not have them. max_tune.sh picks .venv/bin/python and says so before it starts.

set -euo pipefail

# ------------------------------------------------------------------ paths
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENGINE_ROOT="${HYPERCORE_ROOT:-$(dirname "$HERE")}"
ENGINE="$ENGINE_ROOT/engine/hypercore"
PACK="/home/ai-agent/HyperCore-data/packs/q2_0"
NATIVE="/home/ai-agent/HyperCore-data/models/Q2_0/Qwen3.8-Flash-Next-GSQ-RCO-Q2_0-00001-of-00002.gguf"
PLE_GGUF="/home/ai-agent/HyperCore-data/models/Q2_0/Qwen3.8-Flash-Next-GSQ-RCO-Q2_0-00002-of-00002.gguf"
MTP="/home/ai-agent/HyperCore-data/mtp/rt"
CVEC_SCALED="$ENGINE_ROOT/data/experimental-speed-projection/Qwen3.8-Flash-Next-experimental-speed-projection.gguf:1.0"
PROMPT_SRC="$ENGINE_ROOT/bench/results/exchange-rotation-token-ids.json"

RESULTS_DIR="${RESULTS_DIR:-$HERE/results}"
STAMP="$(date -u +%Y-%m-%d_%H%M%S)"          # every file this sweep writes carries it
MATRIX_LOG="${MATRIX_LOG:-$HERE/hypercore_max_tuning_matrix-${STAMP}.log}"
CSV_FILE="${CSV_FILE:-$RESULTS_DIR/matrix-${STAMP}.csv}"

# ------------------------------------------------------------------ defaults
MODEL="q2_0"
MODE="staged"
CALIBRATE=0               # 1 with --short: measure first, freeze the maxima, sweep the rest
CAL_CONFIG=""             # the run config to calibrate; found from the model name when empty
CAL_REPORT=""             # an existing calibrate.py report to reuse instead of measuring
CAL_TIMEOUT=1800          # seconds the calibration is allowed to take
DRY_RUN=0
LIMIT=0
LAYERS=()
EXCLUDE=()

SWEEP_CONTEXT=131072          # fixed for the whole sweep, as specified
PRODUCTION_CONTEXT=262144     # written into max_run_<model>.sh
MAX_NEW=512
SPEC_MIN_P=0.80               # the draft floor; --short replaces it with the measured maximum
PROMPT_TOKENS=0               # 0 = choose from the layer list
BOOT_TIMEOUT=300
RUN_TIMEOUT=180
SHUTDOWN_GRACE=15
GPU_MIN_FREE="${GPU_MIN_FREE:-12000}"
GPU_WAIT="${GPU_WAIT:-120}"

VRAM_RESERVES=(256 512 768)
PCIE_FRACS=(0.85 0.95 1.0)
PLE_IO_MODES=(direct ram)
KV_MODES=(q4_0 k8v4 int8)
KV_GROW_MODES=(1 0)
HOST_CORES=(first last)
POOL_AFFINITIES=(all p-cores auto)
POOL_WORKERS=(0 16 23)
TAIL_MODES=(1 0)

ALL_LAYERS=(topology ple-io kv kv-grow host-core pool-affinity pool-workers prompt-tail)

# ------------------------------------------------------------------ state
declare -A CUR=(
    [vram]=512 [pcie]=0.95 [ple_io]=direct [kv]=q4_0 [kv_grow]=0
    [host_core]=last [affinity]=all [workers]=0 [tail]=0
)
declare -A WIN=()
BEST_TPS="-1"
BEST_LABEL=""
BEST_ARGS=""
RUN_STATUS="FAIL"
RUN_TPS="0.0"
RUN_NOTE=""
RUN_INFO=""
RUN_LOG=""
ENGINE_PID=""
CAL_PID=""
INTERRUPTED=0
BEST_CONFIG_FILE=""
BEST_RUN_FILE=""
ROWS=0
PASS_COUNT=0
FAIL_COUNT=0
DUP_COUNT=0
declare -A SEEN_SIG=()
declare -A SEEN_SIG_IDX=()

# ------------------------------------------------------------------ argument parsing
usage() {
    # The whole header block, so the help text never falls behind the script.
    awk 'NR == 1 { next } /^#/ { print; next } { exit }' "$0"
}

while [ $# -gt 0 ]; do
    case "$1" in
        --model)              MODEL="${2:?--model needs a value}"; shift 2 ;;
        --short)              CALIBRATE=1; shift ;;
        --calibrate-report)   CALIBRATE=1; CAL_REPORT="${2:?--calibrate-report needs a path}"; shift 2 ;;
        --calibrate-config)   CAL_CONFIG="${2:?--calibrate-config needs a path}"; shift 2 ;;
        --calibrate-timeout)  CAL_TIMEOUT="${2:?--calibrate-timeout needs a number}"; shift 2 ;;
        --spec-min-p)         SPEC_MIN_P="${2:?--spec-min-p needs a number}"; shift 2 ;;
        --full)               MODE="full"; shift ;;
        --staged)             MODE="staged"; shift ;;
        --layers)             IFS=',' read -r -a LAYERS <<< "${2:?--layers needs a comma separated list}"; shift 2 ;;
        --exclude)            IFS=',' read -r -a EXCLUDE <<< "${2:?--exclude needs a list}"; shift 2 ;;
        --sweep-context)      SWEEP_CONTEXT="${2:?--sweep-context needs a number}"; shift 2 ;;
        --production-context) PRODUCTION_CONTEXT="${2:?--production-context needs a number}"; shift 2 ;;
        --max-new)            MAX_NEW="${2:?--max-new needs a number}"; shift 2 ;;
        --prompt-tokens)      PROMPT_TOKENS="${2:?--prompt-tokens needs a number}"; shift 2 ;;
        --vram)               IFS=',' read -r -a VRAM_RESERVES <<< "${2:?--vram needs a list}"; shift 2 ;;
        --pcie)               IFS=',' read -r -a PCIE_FRACS <<< "${2:?--pcie needs a list}"; shift 2 ;;
        --limit)              LIMIT="${2:?--limit needs a number}"; shift 2 ;;
        --boot-timeout)       BOOT_TIMEOUT="${2:?--boot-timeout needs a number}"; shift 2 ;;
        --run-timeout)        RUN_TIMEOUT="${2:?--run-timeout needs a number}"; shift 2 ;;
        --dry-run)            DRY_RUN=1; shift ;;
        -h|--help)            usage; exit 2 ;;
        *) echo "max_tune.sh: unknown argument: $1" >&2; exit 2 ;;
    esac
done

if [ ${#LAYERS[@]} -eq 0 ]; then
    LAYERS=("${ALL_LAYERS[@]}")
fi
for l in "${LAYERS[@]}"; do
    found=0
    for a in "${ALL_LAYERS[@]}"; do [ "$l" = "$a" ] && found=1; done
    if [ "$found" = 0 ]; then
        echo "max_tune.sh: unknown layer '$l'. Known: ${ALL_LAYERS[*]}" >&2
        exit 2
    fi
done
if [ ${#EXCLUDE[@]} -gt 0 ]; then
    kept=()
    for l in "${LAYERS[@]}"; do
        skip=0
        for e in "${EXCLUDE[@]}"; do [ "$l" = "$e" ] && skip=1; done
        [ "$skip" = 0 ] && kept+=("$l")
    done
    LAYERS=("${kept[@]}")
fi

# The tail checkpoint needs a prompt longer than one prefill chunk (8192 tokens).
if [ "$PROMPT_TOKENS" = 0 ]; then
    if printf '%s\n' "${LAYERS[@]}" | grep -qx 'prompt-tail'; then
        PROMPT_TOKENS=10240
    else
        PROMPT_TOKENS=1024
    fi
fi

# ------------------------------------------------------------------ preflight
preflight() {
    [ -x "$ENGINE" ] || { echo "max_tune.sh: no engine at $ENGINE. Set HYPERCORE_ROOT." >&2; return 2; }
    for p in "$PACK" "$NATIVE" "$PLE_GGUF" "$MTP" "$PROMPT_SRC"; do
        [ -e "$p" ] || { echo "max_tune.sh: missing $p" >&2; return 2; }
    done
    mkdir -p "$RESULTS_DIR"
    # The matrix log and the CSV are written with >, so an existing file this account cannot write
    # (a run made by another user) would abort the sweep at the first row.
    for f in "$MATRIX_LOG" "$CSV_FILE"; do
        if [ -e "$f" ] && [ ! -w "$f" ]; then
            echo "max_tune.sh: $f exists but is not writable here; using $RESULTS_DIR instead" >&2
            if [ "$f" = "$MATRIX_LOG" ]; then MATRIX_LOG="$RESULTS_DIR/matrix-log-${STAMP}.log"
            else CSV_FILE="$RESULTS_DIR/matrix-csv-${STAMP}.csv"; fi
        fi
    done
    return 0
}

free_mib() {
    nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits 2>/dev/null | head -1
}

wait_for_gpu() {
    [ "$DRY_RUN" = 1 ] && return 0
    local free waited=0
    free="$(free_mib)"
    while [ "${free:-0}" -lt "$GPU_MIN_FREE" ] && [ "$waited" -lt "$GPU_WAIT" ]; do
        echo "    [wait] GPU has ${free:-0} MiB free, waiting for the previous run to release it"
        sleep 2
        waited=$((waited + 2))
        free="$(free_mib)"
    done
    if [ "${free:-0}" -lt "$GPU_MIN_FREE" ]; then
        echo "max_tune.sh: the GPU never freed up (${free:-0} MiB free). Stop the server: ./restart.sh stop" >&2
        return 3
    fi
    return 0
}

# A throwaway copy of the learned profile: the sweep must not feed one run's routing
# statistics into the next run.
prepare_profile() {
    PROFILE="$RESULTS_DIR/expert-profile.sweep.bin"
    if [ -f "$ENGINE_ROOT/data/expert-profile.bin" ]; then
        cp -f "$ENGINE_ROOT/data/expert-profile.bin" "$PROFILE"
    else
        echo "note: no expert profile in $ENGINE_ROOT/data; the engine will build one"
        PROFILE=""
    fi
}

build_prompt() {
    TOKEN_IDS="$("$PY" - "$PROMPT_SRC" "$PROMPT_TOKENS" <<'PY'
import json, sys
ids = json.load(open(sys.argv[1]))["input"]
n = int(sys.argv[2])
out = []
while len(out) < n:
    out.extend(ids)
print(",".join(str(t) for t in out[:n]))
PY
)"
    PROMPT_COUNT="$(printf '%s\n' "$TOKEN_IDS" | tr ',' '\n' | wc -l)"
}

# ------------------------------------------------------------------ the interpreter
# install.sh/setup.sh create .venv and install requirements.txt into it; tools/calibrate.py needs
# regex from there. Pick the first interpreter that works, and name it in the calibration banner.
PY="${HC_PYTHON:-}"
CAL_DEPS="${CAL_DEPS:-regex}"

pick_python() {
    local p
    for p in "$PY" \
             "$ENGINE_ROOT/.venv/bin/python" \
             "$ENGINE_ROOT/.venv/bin/python3" \
             "$(command -v python3 2>/dev/null || true)"; do
        [ -n "$p" ] && [ -x "$p" ] || continue
        if "$p" -c "import json" >/dev/null 2>&1; then
            PY="$p"
            return 0
        fi
    done
    return 1
}

# tools/calibrate.py imports regex through tools/hypercore_tokenizer.py. Finding that out 15 minutes
# into a run, after the GPU has been claimed, wastes the whole attempt.
check_calibrate_deps() {
    local missing
    [ -z "$CAL_DEPS" ] && return 0
    missing="$("$PY" -c '
import importlib.util, sys
print(",".join(m for m in sys.argv[1].split(",") if importlib.util.find_spec(m) is None))
' "$CAL_DEPS" 2>/dev/null)"
    if [ -n "$missing" ]; then
        echo "max_tune.sh: $PY cannot import ${missing}. Either install it:" >&2
        echo "    $PY -m pip install ${missing//,/ }" >&2
        echo "  or point the sweep at the venv: HC_PYTHON=.venv/bin/python ./tune/max_tune.sh --short" >&2
        return 1
    fi
    return 0
}

# ------------------------------------------------------------------ calibration prefix (--short)
# The run config the calibration measures: the model's own config, found next to the engine.
find_run_config() {
    local p
    for p in "$ENGINE_ROOT/hypercore-${MODEL}.json" "$ENGINE_ROOT/ni_hypercore-${MODEL}.json"; do
        if [ -f "$p" ]; then printf '%s\n' "$p"; return 0; fi
    done
    p="$(find "$ENGINE_ROOT" -maxdepth 2 -name 'hypercore-*.json' 2>/dev/null | grep -v 'shared-settings' | head -1)"
    if [ -n "$p" ]; then printf '%s\n' "$p"; return 0; fi
    return 1
}

# A run config that does not parse costs 15-30 minutes of GPU time to discover. Check it first.
config_is_readable() {
    local p="$1" err
    err="$("$PY" - "$p" <<'PY'
import json, sys
try:
    cfg = json.loads(open(sys.argv[1], encoding="utf-8-sig").read())
except Exception as e:
    print(e); raise SystemExit(1)
if not isinstance(cfg, dict) or not cfg.get("exe"):
    print("no 'exe' key: this is not a run config"); raise SystemExit(1)
PY
)"
    if [ -n "$err" ]; then
        echo "max_tune.sh: ${p} is not a readable run config: ${err}" >&2
        return 1
    fi
    return 0
}

# A copy of that config with --max-context set to the sweep context, so the calibration measures the same
# conditions the matrix runs under.
calibration_config() {
    local src="$1" out="$RESULTS_DIR/calibrate-config-${STAMP}.json"
    "$PY" - "$src" "$out" "$SWEEP_CONTEXT" <<'PY'
import json, sys
src, out, ctx = sys.argv[1], sys.argv[2], sys.argv[3]
cfg = json.loads(open(src, encoding="utf-8-sig").read())
args = cfg.get("args") or []
keep, i = [], 0
while i < len(args):
    if args[i] in ("--max-context", "--max-new"):
        i += 2
        continue
    keep.append(args[i])
    i += 1
cfg["args"] = keep + ["--max-context", ctx]
open(out, "w", encoding="utf-8").write(json.dumps(cfg, indent=1))
PY
    printf '%s\n' "$out"
}

# The argmax of every sweep in a calibrate.py report. calibrate.py only keeps a value that beats the
# product default by MIN_GAIN; --short ignores that comparison and takes the measured maximum.
# Prints key=value lines on stdout, the medians it chose on stderr.
calibration_maxima() {
    "$PY" - "$1" <<'PY'
import json, statistics, sys

text = open(sys.argv[1], encoding="utf-8-sig").read()
start = text.find("\n{")
res = json.loads(text[start + 1:] if start >= 0 else text)
rep = res.get("report", res) if isinstance(res, dict) else {}

def medians(sweep):
    out = {}
    for key, vals in (sweep or {}).items():
        nums = [float(v) for v in vals if isinstance(v, (int, float))]
        if nums:
            out[str(key)] = statistics.median(nums)
    return out

for label, sweep in (("pcie-frac", rep.get("pcie_sweep")),
                     ("spec-min-p", rep.get("min_p_sweep")),
                     ("pool-workers", rep.get("workers")),
                     ("expert-tier", rep.get("adapt"))):
    med = medians(sweep)
    if not med:
        continue
    best = max(med, key=med.get)
    print("  measured " + label + ": " +
          ", ".join(f"{k}={v:.1f}" for k, v in sorted(med.items(), key=lambda kv: -kv[1])) +
          f" -> fixed {best}", file=sys.stderr)
    if label == "pcie-frac":
        print(f"pcie={best}")
    elif label == "spec-min-p":
        print(f"spec_min_p={best}")
    elif label == "pool-workers":
        print(f"workers={best}")
    elif best != "default":
        print(f"adapt={best}")
PY
}

declare -A CAL_FIXED=()
CAL_REPORT_PATH=""
ADAPT_EVERY=""
ADAPT_SWAPS=""
ADAPT_DECAY=""

apply_calibration() {
    local line key val rest
    while IFS= read -r line; do
        [ -z "$line" ] && continue
        key="${line%%=*}"; val="${line#*=}"
        CAL_FIXED["$key"]="$val"
        case "$key" in
            pcie)       CUR[pcie]="$val";        PCIE_FRACS=("$val") ;;
            spec_min_p) SPEC_MIN_P="$val" ;;
            workers)    CUR[workers]="$val";     POOL_WORKERS=("$val") ;;
            adapt)      ADAPT_EVERY="${val%%/*}"; rest="${val#*/}"
                        ADAPT_SWAPS="${rest%%/*}"; ADAPT_DECAY="${rest#*/}" ;;
        esac
    done < <(calibration_maxima "$1")
}

# A layer whose only remaining option is the value the calibration froze is no longer a sweep.
prune_fixed_layers() {
    local kept=() layer n
    for layer in "${LAYERS[@]}"; do
        n="$(layer_options "$layer" | wc -l)"
        if [ "$n" -gt 1 ]; then
            kept+=("$layer")
        else
            echo "  frozen by calibration: ${layer} -> $(layer_options "$layer")"
        fi
    done
    LAYERS=("${kept[@]}")
}

# Returns 0 when the frozen values are in place. A failed calibration stops the run rather than quietly
# turning --short into a plain sweep.
run_calibration() {
    local cfg report status
    if [ -n "$CAL_REPORT" ]; then
        if [ ! -f "$CAL_REPORT" ]; then
            echo "max_tune.sh: no calibration report at $CAL_REPORT" >&2
            return 2
        fi
        report="$CAL_REPORT"
        echo "=== CALIBRATION: reusing the report at ${report} ==="
    else
        cfg="$CAL_CONFIG"
        if [ -z "$cfg" ]; then
            if ! cfg="$(find_run_config)"; then
                echo "max_tune.sh: --short needs a run config (hypercore-<model>.json). Give one with --calibrate-config, or reuse a measurement with --calibrate-report <json>." >&2
                return 2
            fi
        fi
        config_is_readable "$cfg" || return 2
        if [ "$DRY_RUN" = 1 ]; then
            echo "max_tune.sh: --dry-run does not measure. Pass --calibrate-report <json> to see the --short" >&2
            echo "  sweep with the frozen values; without it this is the plain staged sweep." >&2
            return 0
        fi
        report="$RESULTS_DIR/calibrate-${STAMP}.json"
        echo "=== CALIBRATION: tools/calibrate.py on ${cfg} at context ${SWEEP_CONTEXT} (15-30 minutes) ==="
        echo "  interpreter: ${PY}"
        check_calibrate_deps || return 2
        wait_for_gpu || return 3
        status=0
        # In the background so Ctrl-C can stop it cleanly instead of waiting for it to return.
        if command -v timeout >/dev/null 2>&1; then
            timeout "$CAL_TIMEOUT" "$PY" "$ENGINE_ROOT/tools/calibrate.py" "$cfg" > "$report" 2>&1 &
        else
            "$PY" "$ENGINE_ROOT/tools/calibrate.py" "$cfg" > "$report" 2>&1 &
        fi
        CAL_PID=$!
        wait "$CAL_PID" || status=$?
        CAL_PID=""
        if [ "$status" -ne 0 ]; then
            echo "max_tune.sh: the calibration did not finish (exit ${status}); its output is in ${report}" >&2
            tail -n 15 "$report" 2>/dev/null | sed 's/^/      /' >&2
            echo "      free the GPU with ./restart.sh stop, or pass --calibrate-report <json> from an earlier run." >&2
            return 2
        fi
    fi
    CAL_REPORT_PATH="$report"
    apply_calibration "$report"
    if [ ${#CAL_FIXED[@]} -eq 0 ]; then
        echo "max_tune.sh: the report carries no measurements, so nothing was frozen. The sweep runs as plain staged." >&2
        return 0
    fi
    prune_fixed_layers
    return 0
}

# The argument list shared by every configuration. Nothing that the sweep touches is here.
base_args() {
    BASE_ARGS=(--serve
        --pack "$PACK"
        --native "$NATIVE"
        --ple-gguf "$PLE_GGUF"
        --prefill auto
        --spec 4
        --mtp "$MTP"
        --max-context "$SWEEP_CONTEXT"
        --max-new "$MAX_NEW"
        --expert-cache auto
        --control-vector-scaled "$CVEC_SCALED"
        --control-vector-layer-range 4 44
        --cvec-mode project
        --cvec-dir per-layer
        --spec-min-p "$SPEC_MIN_P"
        --mmap-experts
        --expert-profile-save-every 0)
    if [ -n "$ADAPT_EVERY" ]; then
        BASE_ARGS+=(--adapt-every "$ADAPT_EVERY" --adapt-swaps "$ADAPT_SWAPS" --adapt-decay "$ADAPT_DECAY")
    fi
    if [ -n "$PROFILE" ]; then BASE_ARGS+=(--expert-profile "$PROFILE"); fi
}

# The swept flags, built from the current parameter set.
sweep_args() {
    local a=()
    a+=(--vram-reserve-mib "${CUR[vram]}" --pcie-frac "${CUR[pcie]}")
    a+=(--ple-io "${CUR[ple_io]}")
    a+=(--kv "${CUR[kv]}")
    if [ "${CUR[kv_grow]}" = 1 ]; then a+=(--kv-grow); fi
    a+=(--host-core "${CUR[host_core]}")
    a+=(--pool-affinity "${CUR[affinity]}")
    a+=(--pool-workers "${CUR[workers]}")
    if [ "${CUR[tail]}" = 1 ]; then a+=(--prompt-cache-tail); fi
    SWEEP_ARG_LIST=("${a[@]}")
}

failure_reason() {
    local log="$1" line
    if grep -q "does not fit" "$log"; then
        echo "NO_VRAM_FOR_MTP: the draft head does not fit at --vram-reserve-mib ${CUR[vram]}; the engine asks for ~829 MiB at context ${SWEEP_CONTEXT}"
        return
    fi
    if grep -q "out of memory" "$log"; then
        echo "NO_VRAM: a device allocation failed at context ${SWEEP_CONTEXT}"
        return
    fi
    if grep -q "unknown --" "$log"; then
        line="$(grep -o 'unknown --[^\n]*' "$log" | tail -1)"
        echo "ARG_BOUNDARY: $line"
        return
    fi
    line="$(grep -o 'hypercore [a-z]*: [^\n]*' "$log" | tail -1)"
    [ -n "$line" ] && echo "$line" || echo "the engine exited with no message"
}

# Clean shutdown: QUIT down the open FIFO, close the writer, SIGTERM, then SIGKILL.
shutdown_engine() {
    local pid="$1" waited=0
    if kill -0 "$pid" 2>/dev/null; then
        printf 'QUIT\n' >&3 2>/dev/null || true
    fi
    exec 3>&- 2>/dev/null || true
    while [ "$waited" -lt "$SHUTDOWN_GRACE" ] && kill -0 "$pid" 2>/dev/null; do
        sleep 1
        waited=$((waited + 1))
    done
    if kill -0 "$pid" 2>/dev/null; then
        kill -TERM "$pid" 2>/dev/null || true
        waited=0
        while [ "$waited" -lt 10 ] && kill -0 "$pid" 2>/dev/null; do
            sleep 1
            waited=$((waited + 1))
        done
        if kill -0 "$pid" 2>/dev/null; then
            kill -KILL "$pid" 2>/dev/null || true
            echo "    [warn] SIGTERM did not unwind the process; sent SIGKILL"
        fi
    fi
    ENGINE_PID=""
}

on_signal() {
    local sig="$1"
    [ "$INTERRUPTED" = 1 ] && return 0        # a second signal while already unwinding
    INTERRUPTED=1
    echo ""
    echo "max_tune.sh: caught ${sig}, unwinding"
    if [ -n "${CAL_PID:-}" ] && kill -0 "$CAL_PID" 2>/dev/null; then
        kill -TERM "$CAL_PID" 2>/dev/null || true
    fi
    if [ -n "${ENGINE_PID:-}" ] && kill -0 "$ENGINE_PID" 2>/dev/null; then
        shutdown_engine "$ENGINE_PID"
    fi
    write_matrix_footer
    save_best_files "interrupted"
    echo ""
    echo "=========================================================================="
    echo " SWEEP STOPPED after ${ROWS} configurations: ${PASS_COUNT} measured, ${FAIL_COUNT} failed"
    echo " best so far: ${BEST_TPS} tok/s (${BEST_LABEL:-nothing measured})"
    echo " matrix: ${MATRIX_LOG}"
    echo " csv:    ${CSV_FILE}"
    if [ -n "$BEST_LABEL" ]; then
        echo " the best configuration found so far is in: ${BEST_CONFIG_FILE} / ${BEST_RUN_FILE}"
        echo " start it with: ${BEST_RUN_FILE}"
    fi
    echo "=========================================================================="
    exit 130
}

trap 'on_signal INT' INT
trap 'on_signal TERM' TERM

# ------------------------------------------------------------------ one configuration
# run_current <layer-label>
# Sets RUN_STATUS, RUN_TPS, RUN_NOTE. Returns 0 on PASS.
run_current() {
    local layer="$1"
    sweep_args
    local label="${layer}-${CUR[vram]}-${CUR[pcie]}-${CUR[ple_io]}-${CUR[kv]}-kv${CUR[kv_grow]}-${CUR[host_core]}-${CUR[affinity]}-${CUR[workers]}-tail${CUR[tail]}"
    RUN_LABEL="$label"
    RUN_LOG="$RESULTS_DIR/run-${STAMP}-${label}.log"
    RUN_STATUS="FAIL"
    RUN_TPS="0.0"
    RUN_NOTE=""
    RUN_INFO=""

    ROWS=$((ROWS + 1))
    echo "[*] run ${ROWS}  layer=${layer}"
    echo "    window: vram=${CUR[vram]}MiB pcie=${CUR[pcie]} ple-io=${CUR[ple_io]} kv=${CUR[kv]} kv-grow=${CUR[kv_grow]} host-core=${CUR[host_core]} affinity=${CUR[affinity]} workers=${CUR[workers]} prompt-cache-tail=${CUR[tail]}"
    echo "    command: ${ENGINE} ${BASE_ARGS[*]} ${SWEEP_ARG_LIST[*]}"

    if [ "$DRY_RUN" = 1 ]; then
        RUN_STATUS="DRY"
        record_row "$layer"
        return 1
    fi

    wait_for_gpu || return 1

    rm -f "$RUN_LOG"
    local fifo="$RESULTS_DIR/in.fifo"
    rm -f "$fifo"
    mkfifo "$fifo"
    exec 3<>"$fifo"

    "$ENGINE" "${BASE_ARGS[@]}" "${SWEEP_ARG_LIST[@]}" <"$fifo" >"$RUN_LOG" 2>&1 &
    local pid=$!
    ENGINE_PID="$pid"

    # Liveness: poll for "session is up", checking the process each iteration so a silent
    # crash (OOM, argument boundary) is caught instead of burning the whole timeout.
    echo -n "    --> boot... "
    local ready=0 n=0
    while [ "$n" -lt "$BOOT_TIMEOUT" ]; do
        if ! kill -0 "$pid" 2>/dev/null; then break; fi
        if grep -q "session is up" "$RUN_LOG"; then ready=1; echo "ready"; break; fi
        sleep 1
        n=$((n + 1))
    done

    if [ "$ready" = 0 ]; then
        RUN_STATUS="FAIL_BOOT"
        if kill -0 "$pid" 2>/dev/null; then
            echo "    [FAIL] still not 'session is up' after ${BOOT_TIMEOUT}s; the process was alive but never initialised"
        else
            echo "    [FAIL] the engine exited at second ${n} without reaching 'session is up'"
        fi
        echo "      $(failure_reason "$RUN_LOG")"
        shutdown_engine "$pid"
        record_row "$layer"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        return 1
    fi

    # One request. The rate comes from the DONE line:
    # DONE <generated> <prompt_tokens> <prompt_ms> <decode_ms> <stop|length> ...
    echo -n "    --> generating ${MAX_NEW} tokens over a ${PROMPT_COUNT}-token prompt... "
    printf 'GEN %s %s\n' "$MAX_NEW" "$TOKEN_IDS" >&3
    local done=0 m=0
    while [ "$m" -lt "$RUN_TIMEOUT" ]; do
        if ! kill -0 "$pid" 2>/dev/null; then break; fi
        if grep -q '^DONE ' "$RUN_LOG"; then done=1; echo "done"; break; fi
        sleep 1
        m=$((m + 1))
    done

    if [ "$done" = 0 ]; then
        RUN_STATUS="TIMEOUT"
        echo "    [FAIL] no DONE line within ${RUN_TIMEOUT}s"
        echo "      $(failure_reason "$RUN_LOG")"
        shutdown_engine "$pid"
        record_row "$layer"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        return 1
    fi

    RUN_TPS="$(awk '$1 == "DONE" && $5 > 0 { printf "%.2f", $2 * 1000.0 / $5; exit }' "$RUN_LOG")"
    [ -z "$RUN_TPS" ] && RUN_TPS="0.0"
    RUN_INFO="$(grep -m1 '^INFO ' "$RUN_LOG" || true)"

    # Verify the flags the engine actually applied, and note the two silent degradations
    # this box can produce.
    local eff_ctx eff_kv eff_workers
    eff_ctx=""; eff_kv=""; eff_workers=""
    if [ -n "$RUN_INFO" ]; then
        eff_ctx="$(printf '%s' "$RUN_INFO" | sed -n 's/.*context=\([0-9]*\).*/\1/p')"
        eff_kv="$(printf '%s' "$RUN_INFO" | sed -n 's/.* kv=\([a-z0-9_]*\).*/\1/p')"
        eff_workers="$(printf '%s' "$RUN_INFO" | sed -n 's/.*pool_workers=\([0-9]*\).*/\1/p')"
        if [ -n "$eff_ctx" ] && [ "$eff_ctx" != "$SWEEP_CONTEXT" ]; then
            RUN_NOTE="context applied as ${eff_ctx}, not ${SWEEP_CONTEXT}"
        fi
        if [ -n "$eff_kv" ] && [ "$eff_kv" != "${CUR[kv]}" ]; then
            RUN_NOTE="${RUN_NOTE} kv applied as ${eff_kv}"
        fi
        if [ -n "$eff_workers" ] && [ "$eff_workers" != "${CUR[workers]}" ]; then
            RUN_NOTE="${RUN_NOTE} pool-workers ${CUR[workers]} resolved to ${eff_workers}"
        fi
    fi
    if grep -q "mlock failed" "$RUN_LOG"; then
        RUN_NOTE="${RUN_NOTE} ple-io ram degraded to mmap (ulimit -l is $(ulimit -l) KB)"
    fi

    shutdown_engine "$pid"

    # The signature uses what the engine actually applied, so --pool-workers 0 and
    # --pool-workers 23 (the same pool on this box) are recognised as one row.
    local sig="${CUR[vram]}|${CUR[pcie]}|${CUR[ple_io]}|${eff_kv:-${CUR[kv]}}|${CUR[kv_grow]}|${CUR[host_core]}|${CUR[affinity]}|${eff_workers:-${CUR[workers]}}|${CUR[tail]}"
    if [ -n "${SEEN_SIG[$sig]:-}" ]; then
        RUN_STATUS="DUPLICATE"
        RUN_TPS="${SEEN_SIG[$sig]}"
        DUP_COUNT=$((DUP_COUNT + 1))
        echo "    [skip] identical to run ${SEEN_SIG_IDX[$sig]}: ${sig}"
        record_row "$layer"
        return 1
    fi

    if awk -v t="$RUN_TPS" 'BEGIN { exit (t > 0) ? 0 : 1 }'; then
        RUN_STATUS="PASS"
        SEEN_SIG[$sig]="$RUN_TPS"
        SEEN_SIG_IDX[$sig]="$ROWS"
        echo "    [PASS] ${RUN_TPS} tok/s${RUN_NOTE:+ (${RUN_NOTE})}"
        PASS_COUNT=$((PASS_COUNT + 1))
        if awk -v a="$RUN_TPS" -v b="$BEST_TPS" 'BEGIN { exit (a > b) ? 0 : 1 }'; then
            BEST_TPS="$RUN_TPS"
            BEST_LABEL="$label"
            BEST_ARGS="${SWEEP_ARG_LIST[*]}"
            WIN=()
            for k in "${!CUR[@]}"; do WIN["$k"]="${CUR[$k]}"; done
            save_best_files progress
        fi
        record_row "$layer"
        return 0
    fi

    RUN_STATUS="NO_TOKENS"
    echo "    [FAIL] the request finished but produced no tokens"
    echo "      $(failure_reason "$RUN_LOG")"
    record_row "$layer"
    FAIL_COUNT=$((FAIL_COUNT + 1))
    return 1
}

layer_options() {
    case "$1" in
        topology)
            for v in "${VRAM_RESERVES[@]}"; do
                for p in "${PCIE_FRACS[@]}"; do printf 'vram=%s pcie=%s\n' "$v" "$p"; done
            done ;;
        ple-io)        for x in "${PLE_IO_MODES[@]}"; do printf 'ple_io=%s\n' "$x"; done ;;
        kv)            for x in "${KV_MODES[@]}"; do printf 'kv=%s\n' "$x"; done ;;
        kv-grow)       for x in "${KV_GROW_MODES[@]}"; do printf 'kv_grow=%s\n' "$x"; done ;;
        host-core)     for x in "${HOST_CORES[@]}"; do printf 'host_core=%s\n' "$x"; done ;;
        pool-affinity) for x in "${POOL_AFFINITIES[@]}"; do printf 'affinity=%s\n' "$x"; done ;;
        pool-workers)  for x in "${POOL_WORKERS[@]}"; do printf 'workers=%s\n' "$x"; done ;;
        prompt-tail)   for x in "${TAIL_MODES[@]}"; do printf 'tail=%s\n' "$x"; done ;;
    esac
}

apply_option() {
    local opt="$1" kv k v
    for kv in $opt; do
        k="${kv%%=*}"; v="${kv#*=}"
        CUR[$k]="$v"
    done
}

# Staged: freeze every layer already swept, sweep the next one, keep its best.
run_staged() {
    local layer prev_opt best_tps best_opt
    for layer in "${LAYERS[@]}"; do
        if [ "$LIMIT" -gt 0 ] && [ "$ROWS" -ge "$LIMIT" ]; then
            echo "max_tune.sh: reached --limit ${LIMIT}, stopping"
            return 0
        fi
        echo ""
        echo "=== LAYER: ${layer} ==="
        prev_opt=""
        for k in vram pcie ple_io kv kv_grow host_core affinity workers tail; do
            prev_opt="${prev_opt} ${k}=${CUR[$k]}"
        done
        best_tps="-1"; best_opt=""
        while IFS= read -r opt; do
            if [ "$LIMIT" -gt 0 ] && [ "$ROWS" -ge "$LIMIT" ]; then break; fi
            apply_option "$opt"
            if run_current "$layer"; then
                if awk -v a="$RUN_TPS" -v b="$best_tps" 'BEGIN { exit (a > b) ? 0 : 1 }'; then
                    best_tps="$RUN_TPS"; best_opt="$opt"
                fi
            fi
        done < <(layer_options "$layer")
        if [ -n "$best_opt" ]; then
            apply_option "$best_opt"
            echo "--- layer ${layer}: locked ${best_opt} at ${best_tps} tok/s"
        else
            apply_option "$prev_opt"
            echo "--- layer ${layer}: nothing measured, keeping the previous values"
        fi
    done
}

# Full Cartesian product.
walk_layers() {
    local idx="$1"
    if [ "$LIMIT" -gt 0 ] && [ "$ROWS" -ge "$LIMIT" ]; then return 0; fi
    if [ "$idx" -ge ${#LAYERS[@]} ]; then
        run_current "matrix" || true
        return 0
    fi
    local layer="${LAYERS[idx]}" opt
    while IFS= read -r opt; do
        if [ "$LIMIT" -gt 0 ] && [ "$ROWS" -ge "$LIMIT" ]; then return 0; fi
        apply_option "$opt"
        walk_layers $((idx + 1))
    done < <(layer_options "$layer")
}

# ------------------------------------------------------------------ matrix log
write_matrix_header() {
    {
        printf '# HyperCore max tuning matrix\n'
        printf '# generated %s by max_tune.sh (engine %s)\n' "$(date -u '+%Y-%m-%d %H:%M:%S UTC')" "$ENGINE"
        printf '# model=%s mode=%s layers=%s\n' "$MODEL" "$MODE" "${LAYERS[*]}"
        if [ "$CALIBRATE" = 1 ]; then
            printf '# frozen from calibration (%s):' "$CAL_REPORT_PATH"
            for k in "${!CAL_FIXED[@]}"; do printf ' %s=%s' "$k" "${CAL_FIXED[$k]}"; done
            printf '\n'
        fi
        printf '# sweep context=%s production context=%s max-new=%s prompt tokens=%s\n' \
            "$SWEEP_CONTEXT" "$PRODUCTION_CONTEXT" "$MAX_NEW" "$PROMPT_TOKENS"
        printf '# tok/s = generated tokens * 1000 / decode ms, read off the DONE line the engine prints\n'
        printf '#\n'
        printf '%4s  %-13s %5s %5s %-7s %-5s %-7s %-9s %-9s %7s %4s  %-10s %8s\n' \
            "run" "layer" "vram" "pcie" "ple-io" "kv" "kvgrow" "hostcore" "affinity" "worker" "tail" "status" "tok/s"
        printf '%s\n' "------------------------------------------------------------------------------------------------------------------------"
    } > "$MATRIX_LOG"
    printf 'run,label,vram_reserve_mib,pcie_frac,ple_io,kv,kv_growth,host_core,pool_affinity,pool_workers,prompt_cache_tail,status,tokens_per_sec\n' > "$CSV_FILE"
}

append_matrix_row() {
    printf '%4d  %-13s %5s %5s %-7s %-5s %-7s %-9s %-9s %7s %4s  %-10s %8s  %s\n' \
        "$ROWS" "$1" "${CUR[vram]}" "${CUR[pcie]}" "${CUR[ple_io]}" "${CUR[kv]}" \
        "$([ "${CUR[kv_grow]}" = 1 ] && echo on || echo off)" \
        "${CUR[host_core]}" "${CUR[affinity]}" "${CUR[workers]}" \
        "$([ "${CUR[tail]}" = 1 ] && echo on || echo off)" \
        "$RUN_STATUS" "$RUN_TPS" "${RUN_NOTE:-}" >> "$MATRIX_LOG"
}

# record_row writes the CSV and the matrix log for every configuration, pass or fail.
# record_row <layer> - the parameter columns are the configuration; the full label lives
# in the per-run log file name and in the CSV.
record_row() {
    local layer="$1"
    printf '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' \
        "$ROWS" "$RUN_LABEL" "${CUR[vram]}" "${CUR[pcie]}" "${CUR[ple_io]}" "${CUR[kv]}" \
        "${CUR[kv_grow]}" "${CUR[host_core]}" "${CUR[affinity]}" "${CUR[workers]}" \
        "${CUR[tail]}" "$RUN_STATUS" "$RUN_TPS" >> "$CSV_FILE"
    append_matrix_row "$layer"
}

write_matrix_footer() {
    {
        printf '%s\n' "------------------------------------------------------------------------------------------------------------------------"
        printf 'runs=%d measured=%d failed=%d skipped-duplicate=%d best=%s tok/s (%s)\n' \
            "$ROWS" "$PASS_COUNT" "$FAIL_COUNT" "$DUP_COUNT" "$BEST_TPS" "${BEST_LABEL:-none}"
        if [ -n "$BEST_LABEL" ]; then
            printf 'winner args: %s\n' "$BEST_ARGS"
        fi
    } >> "$MATRIX_LOG"
}

# ------------------------------------------------------------------ exports
sanitize_model() {
    printf '%s' "$MODEL" | tr -c 'A-Za-z0-9_-' '_'
}

# Write the best configuration found so far. Called after every new winner, so an interrupted
# sweep leaves a launcher for whatever was measured up to that point.
# save_best_files <why> - "progress" while the sweep runs, "interrupted" from the signal handler.
save_best_files() {
    local why="${1:-progress}"
    [ -z "$BEST_LABEL" ] && return 0
    BEST_CONFIG_FILE="$(write_config_file "$why")"
    BEST_RUN_FILE="$(write_run_file "$why")"
    if [ "$why" != progress ]; then
        echo "    [saved] best so far ${BEST_TPS} tok/s -> ${BEST_CONFIG_FILE} and ${BEST_RUN_FILE}"
    fi
    return 0
}

write_config_file() {
    local why="${1:-progress}"
    model="$(sanitize_model)"
    cfg="$HERE/max_config_${model}.sh"
    {
        printf '#!/usr/bin/env bash\n'
        printf '# max_config_%s.sh - generated %s by max_tune.sh (sweep %s)\n' "$model" "$(date -u '+%Y-%m-%d %H:%M:%S UTC')" "$STAMP"
        printf '# Peak measured decode: %s tok/s at --max-context %s (%d configurations evaluated, %d measured).\n' \
            "$BEST_TPS" "$SWEEP_CONTEXT" "$ROWS" "$PASS_COUNT"
        if [ "$why" = progress ]; then
            printf '# Complete sweep.\n'
        else
            printf '# The sweep was stopped (%s) at run %d: these are the best values measured so far, not\n' "$why" "$ROWS"
            printf '# the winner of the whole matrix. Re-run max_tune.sh to complete it.\n'
        fi
        if [ "$CALIBRATE" = 1 ]; then
            printf '# pcie-frac, spec-min-p and pool-workers were frozen by tools/calibrate.py before the sweep.\n'
        fi
        printf '# Source this file, or let max_run_%s.sh read it.\n' "$model"
        printf '#\n'
        printf 'HC_MODEL="%s"\n' "$model"
        printf 'HC_SWEEP_STAMP="%s"\n' "$STAMP"
        printf 'HC_COMPLETE=%s\n' "$([ "$why" = progress ] && echo 1 || echo 0)"
        printf 'HC_ENGINE="%s"\n' "$ENGINE"
        printf 'HC_PACK="%s"\n' "$PACK"
        printf 'HC_NATIVE="%s"\n' "$NATIVE"
        printf 'HC_PLE_GGUF="%s"\n' "$PLE_GGUF"
        printf 'HC_MTP="%s"\n' "$MTP"
        printf 'HC_EXPERT_PROFILE="%s"\n' "$ENGINE_ROOT/data/expert-profile.bin"
        printf 'HC_CVEC_SCALED="%s"\n' "$CVEC_SCALED"
        printf '# Winning topology\n'
        printf 'HC_VRAM_RESERVE_MIB=%s\n' "${WIN[vram]}"
        printf 'HC_PCIE_FRAC=%s\n' "${WIN[pcie]}"
        printf 'HC_PLE_IO=%s\n' "${WIN[ple_io]}"
        printf 'HC_KV=%s\n' "${WIN[kv]}"
        printf 'HC_KV_GROW=%s\n' "${WIN[kv_grow]}"
        printf 'HC_HOST_CORE=%s\n' "${WIN[host_core]}"
        printf 'HC_POOL_AFFINITY=%s\n' "${WIN[affinity]}"
        printf 'HC_POOL_WORKERS=%s\n' "${WIN[workers]}"
        printf 'HC_PROMPT_CACHE_TAIL=%s\n' "${WIN[tail]}"
        printf 'HC_MAX_CONTEXT=%s\n' "$PRODUCTION_CONTEXT"
        printf 'HC_MAX_NEW=%s\n' "$MAX_NEW"
        printf 'HC_SPEC_MIN_P=%s\n' "$SPEC_MIN_P"
        printf 'HC_PEAK_TPS=%s\n' "$BEST_TPS"
        printf '# Standalone argument string, in the order the engine expects.\n'
        printf 'HC_ARGS=(\n'
        printf '    --pack "%s"\n' "$PACK"
        printf '    --native "%s"\n' "$NATIVE"
        printf '    --ple-gguf "%s"\n' "$PLE_GGUF"
        printf '    --expert-profile "%s"\n' "$ENGINE_ROOT/data/expert-profile.bin"
        printf '    --expert-cache auto\n'
        printf '    --prefill auto\n'
        printf '    --spec 4\n'
        printf '    --mtp "%s"\n' "$MTP"
        printf '    --max-context "%s"\n' "$PRODUCTION_CONTEXT"
        printf '    --kv "%s"\n' "${WIN[kv]}"
        if [ "${WIN[kv_grow]}" = 1 ]; then printf '    --kv-grow\n'; fi
        printf '    --ple-io "%s"\n' "${WIN[ple_io]}"
        printf '    --host-core "%s"\n' "${WIN[host_core]}"
        printf '    --pool-affinity "%s"\n' "${WIN[affinity]}"
        printf '    --pool-workers "%s"\n' "${WIN[workers]}"
        if [ "${WIN[tail]}" = 1 ]; then printf '    --prompt-cache-tail\n'; fi
        printf '    --control-vector-scaled "%s"\n' "$CVEC_SCALED"
        printf '    --control-vector-layer-range 4 44\n'
        printf '    --cvec-mode project\n'
        printf '    --cvec-dir per-layer\n'
        printf '    --spec-min-p %s\n' "$SPEC_MIN_P"
        if [ -n "$ADAPT_EVERY" ]; then
            printf '    --adapt-every %s\n' "$ADAPT_EVERY"
            printf '    --adapt-swaps %s\n' "$ADAPT_SWAPS"
            printf '    --adapt-decay %s\n' "$ADAPT_DECAY"
        fi
        printf '    --mmap-experts\n'
        printf '    --vram-reserve-mib "%s"\n' "${WIN[vram]}"
        printf '    --pcie-frac "%s"\n' "${WIN[pcie]}"
        printf ')\n'
    } > "$cfg"
    chmod +x "$cfg"
    echo "$cfg"
}

write_run_file() {
    local why="${1:-progress}"
    model="$(sanitize_model)"
    run="$HERE/max_run_${model}.sh"
    {
        printf '#!/usr/bin/env bash\n'
        printf '# max_run_%s.sh - generated %s by max_tune.sh (sweep %s)\n' "$model" "$(date -u '+%Y-%m-%d %H:%M:%S UTC')" "$STAMP"
        if [ "$why" = progress ]; then
            printf '# From the complete sweep: peak %s tok/s.\n' "$BEST_TPS"
        else
            printf '# From a sweep stopped (%s) at run %d: peak %s tok/s measured so far.\n' "$why" "$ROWS" "$BEST_TPS"
        fi
        cat <<'RUNEOF'
# max_run_<model>.sh - production daemon wrapper for the winning configuration.
#
#   ./tune/max_run_q2_0.sh              start the engine in the background and return
#   ./tune/max_run_q2_0.sh --check      verify paths and the GPU, launch nothing
#   ./tune/max_run_q2_0.sh --status     is it running, and what is the last DONE line
#   ./tune/max_run_q2_0.sh --stop       QUIT down the FIFO, then SIGTERM
#
# Reads max_config_<model>.sh from its own directory. The engine is not an HTTP server:
# requests arrive on stdin as "GEN <max_new> <token ids>", so the FIFO stays open on fd 3.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODEL_ID="$(basename "$0" | sed 's/^max_run_//; s/\.sh$//')"
CONFIG="$HERE/max_config_${MODEL_ID}.sh"
PID_FILE="$HERE/max_run_${MODEL_ID}.pid"
FIFO="$HERE/max_run_${MODEL_ID}.fifo"
LOG="$HERE/max_run_${MODEL_ID}.log"
BOOT_TIMEOUT="${BOOT_TIMEOUT:-300}"
GPU_MIN_FREE="${GPU_MIN_FREE:-12000}"

[ -f "$CONFIG" ] || { echo "max_run_${MODEL_ID}.sh: no $CONFIG. Run max_tune.sh first." >&2; exit 1; }
# shellcheck source=/dev/null
source "$CONFIG"

if [ "${HC_COMPLETE:-1}" != 1 ]; then
    echo "note: this configuration came from an incomplete sweep (HC_COMPLETE=0). max_tune.sh can finish it."
fi

CHECK_ONLY=0
ACTION="start"
while [ $# -gt 0 ]; do
    case "$1" in
        --check)  CHECK_ONLY=1; shift ;;
        --status) ACTION="status"; shift ;;
        --stop)   ACTION="stop"; shift ;;
        --context) HC_MAX_CONTEXT="${2:?--context needs a number}"; shift 2 ;;
        -h|--help) sed -n '2,10p' "$0"; exit 2 ;;
        *) echo "max_run_${MODEL_ID}.sh: unknown argument: $1" >&2; exit 2 ;;
    esac
done

for p in "$HC_ENGINE" "$HC_PACK" "$HC_NATIVE" "$HC_PLE_GGUF" "$HC_MTP"; do
    [ -e "$p" ] || { echo "max_run_${MODEL_ID}.sh: missing $p" >&2; exit 1; }
done

if [ "$ACTION" = "status" ]; then
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        pid="$(cat "$PID_FILE")"
        echo "running, pid ${pid}, log ${LOG}"
        grep -E '^(DONE|INFO) ' "$LOG" | tail -3 || echo "no telemetry yet"
    else
        echo "not running"
    fi
    exit 0
fi

if [ "$ACTION" = "stop" ]; then
    if [ -f "$PID_FILE" ]; then
        pid="$(cat "$PID_FILE")"
        if kill -0 "$pid" 2>/dev/null; then
            if [ -e "$FIFO" ]; then printf 'QUIT\n' > "$FIFO"; fi
            kill -TERM "$pid" 2>/dev/null || true
            n=0
            while [ "$n" -lt 20 ] && kill -0 "$pid" 2>/dev/null; do sleep 1; n=$((n + 1)); done
            kill -0 "$pid" 2>/dev/null && kill -KILL "$pid" 2>/dev/null || true
            echo "stopped pid ${pid}"
        else
            echo "pid ${pid} is not running"
        fi
        rm -f "$PID_FILE"
    else
        echo "no pid file; nothing to stop"
    fi
    exit 0
fi

free="$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits 2>/dev/null | head -1)"
if [ "${free:-0}" -lt "$GPU_MIN_FREE" ]; then
    echo "max_run_${MODEL_ID}.sh: GPU busy, ${free:-0} MiB free. Stop the running server first: ./restart.sh stop" >&2
    exit 3
fi

if [ "$CHECK_ONLY" = 1 ]; then
    echo "paths ok, engine at $HC_ENGINE, ${free} MiB of GPU free, context ${HC_MAX_CONTEXT}"
    exit 0
fi

rm -f "$FIFO"
mkfifo "$FIFO"
exec 3<>"$FIFO"

echo "[*] Starting HyperCore ${MODEL_ID}: vram-reserve ${HC_VRAM_RESERVE_MIB} MiB, pcie-frac ${HC_PCIE_FRAC}, kv ${HC_KV}, kv-grow ${HC_KV_GROW}, ple-io ${HC_PLE_IO}, host-core ${HC_HOST_CORE}, affinity ${HC_POOL_AFFINITY}, workers ${HC_POOL_WORKERS}, context ${HC_MAX_CONTEXT}"

"$HC_ENGINE" --serve "${HC_ARGS[@]}" <"$FIFO" >"$LOG" 2>&1 &
ENGINE_PID=$!
printf '%s\n' "$ENGINE_PID" > "$PID_FILE"

cleanup() {
    if kill -0 "$ENGINE_PID" 2>/dev/null; then
        printf 'QUIT\n' >&3 2>/dev/null || true
        exec 3>&- 2>/dev/null || true
        sleep 2
        kill -TERM "$ENGINE_PID" 2>/dev/null || true
        kill -0 "$ENGINE_PID" 2>/dev/null && kill -KILL "$ENGINE_PID" 2>/dev/null || true
    fi
    rm -f "$PID_FILE"
    echo "[*] shutdown complete"
}
trap cleanup SIGINT SIGTERM

echo -n "    --> loading weights, pinning the arena, building the graphs... "
ready=0
booted=0
while [ "$booted" -lt "$BOOT_TIMEOUT" ]; do
    if ! kill -0 "$ENGINE_PID" 2>/dev/null; then break; fi
    if grep -q "session is up" "$LOG"; then
        ready=1
        echo "ready"
        break
    fi
    sleep 1
    booted=$((booted + 1))
done

if [ "$ready" = 0 ]; then
    echo "FAILED"
    echo "[-] the engine exited during startup; last lines of $LOG:"
    tail -n 10 "$LOG" | sed 's/^/      /'
    exit 1
fi

echo "=========================================================================="
echo " HyperCore ${MODEL_ID} is running in the background (pid ${ENGINE_PID})."
echo " peak tok/s from the sweep: ${HC_PEAK_TPS}"
echo " watch it:  tail -f $LOG"
echo " send work: printf 'GEN 64 1234,5678\n' > $FIFO"
echo " stop it:   $0 --stop"
echo "=========================================================================="
RUNEOF
    } > "$run"
    chmod +x "$run"
    echo "$run"
}

# ------------------------------------------------------------------ main
main() {
    preflight || exit 2
    pick_python || { echo "max_tune.sh: no usable python3 found. Set HC_PYTHON=<path>." >&2; exit 2; }
    if [ "$CALIBRATE" = 1 ]; then
        run_calibration || exit 2
    fi
    prepare_profile
    build_prompt
    base_args
    write_matrix_header

    total=1
    staged_runs=0
    for l in "${LAYERS[@]}"; do
        n="$(layer_options "$l" | wc -l)"
        total=$((total * n))
        staged_runs=$((staged_runs + n))
    done

    echo "=========================================================================="
    echo " HyperCore parameter matrix sweep"
    echo " model: ${MODEL}   engine: ${ENGINE}"
    if [ "$MODE" = "full" ]; then
        echo " mode: full   configurations: ${total}   layers: ${LAYERS[*]}"
    else
        echo " mode: ${MODE}   runs: ${staged_runs} (the full product of these layers is ${total})   layers: ${LAYERS[*]}"
    fi
    echo " fixed: --max-context ${SWEEP_CONTEXT} --max-new ${MAX_NEW} --spec-min-p ${SPEC_MIN_P}, prompt ${PROMPT_TOKENS} tokens"
    echo " interpreter: ${PY}"
    if [ "$CALIBRATE" = 1 ] && [ ${#CAL_FIXED[@]} -gt 0 ]; then
        frozen=""
        for k in pcie spec_min_p workers adapt; do
            [ -n "${CAL_FIXED[$k]:-}" ] && frozen="${frozen} ${k}=${CAL_FIXED[$k]}"
        done
        echo " frozen by calibration:${frozen} (layers left: ${LAYERS[*]})"
    fi
    if [ "$MODE" = "full" ]; then
        echo " note: ${total} engine boots. At 60-90 s each that is roughly $((total * 75 / 3600)) hours."
    else
        echo " staged sweep: each layer is frozen at the best of the previous ones."
    fi
    echo "=========================================================================="

    if [ "$MODE" = "full" ]; then
        walk_layers 0
    else
        run_staged
    fi

    write_matrix_footer

    echo ""
    echo "=========================================================================="
    echo " SWEEP COMPLETE: ${ROWS} configurations, ${PASS_COUNT} measured, ${FAIL_COUNT} failed, ${DUP_COUNT} duplicate"
    echo " matrix: ${MATRIX_LOG}"
    echo " csv:    ${CSV_FILE}"
    if [ -n "$BEST_LABEL" ]; then
        echo " peak: ${BEST_TPS} tok/s"
        echo " winner: ${BEST_ARGS}"
        save_best_files progress
        echo " wrote ${BEST_CONFIG_FILE}"
        echo " wrote ${BEST_RUN_FILE}"
        echo " start the production daemon with: ${BEST_RUN_FILE}"
    else
        echo " nothing measured: no configuration produced tokens. Nothing was written."
        echo " Check ${MATRIX_LOG} for the failure reasons."
    fi
    echo "=========================================================================="
}

main
