#!/bin/sh
# verify_all_tests.sh - the whole test surface of this install, in one transcript.
#
#   ./verify_all_tests.sh                    run everything (the serve engine must be stopped)
#   ./verify_all_tests.sh --stop            stop the serve engine first, then run
#   ./verify_all_tests.sh --build           rebuild build/hypercore before the tests
#   ./verify_all_tests.sh --only ctest,ple  just those stages
#   ./verify_all_tests.sh --list            show the stages and what each one does
#   ./verify_all_tests.sh --out FILE        where the transcript goes
#
# Everything - the environment fingerprint, every command, every line of output, the
# per-stage verdict and a final tally - goes to one file, so a run can be compared with
# the one before it.  Exit code 0 only when every stage that ran passed.
#
# Why the engine has to be unloaded: 57 of the 99 build tests allocate on the GPU
# (cudaMalloc, cudaSetDevice, the expert cache).  With the server resident the card has
# ~30 MiB free and they all fail with "out of memory".  A clean run needs the card.
#
# The web-ui stage needs node.  Where node is not installed the stage reports SKIP and exits
# 0, the same way the cross-toolchain stage reports SKIP without DAYTONA_API_KEY: a tool
# that is not on this machine is not a failure of the code.
#
# Four environment quirks this script works around, so a failure means a real failure:
#   ple_parity   CMake registers it with no --gguf; it needs HYPERCORE_PLE_GGUF, which is
#                taken from the run config here.
#   pytest       /opt/ai-workspace/.tmp/pytest-of-<user> belongs to another user, so TMPDIR
#                is redirected to a directory this run owns.
#   run_all.py   serve/mcp/tests/run_all.py:69 raises AttributeError on an _ErrorHolder in
#                addSkip; the unittest modules are run directly as the fallback.
#   ctest -j4    GPU tests running four at a time pollute each other's cudaMemGetInfo().
#                Anything ctest reports as failed is rerun serially (stage ctest-serial) so
#                contention is separated from a genuine failure.
#
# The worker-load stage catches what a run script hits at startup: serve/server.py spawns
# serve/server.py spawns build-shared/hypercore-worker, which needs libhypercore_api.so.0
# by soname. cmake --build emits only libhypercore_api.so.<version>; the soname link is
# made by cmake --install. A build tree that has never been installed has no link, and the
# worker dies at exec with "error while loading shared libraries".
set -u

ROOT="${HYPERCORE_ROOT:-$(cd "$(dirname "$0")" && pwd)}"
DAY="$(date -u +%Y-%m-%d)"
STAMP="$(date -u +%Y-%m-%dT%H%M%SZ)"
OUT_DIR="${VERIFY_DIR:-$ROOT/bench/results/verify-$DAY}"
TRANS="${VERIFY_OUT:-$OUT_DIR/verify-$STAMP.log}"
BUILD_DIR="${BUILD_DIR:-$ROOT/build}"
MIN_FREE_MIB="${MIN_FREE_MIB:-12000}"
DO_BUILD=0
DO_STOP=0
ONLY=""
LIMIT_CTEST="${LIMIT_CTEST:-900}"
LIMIT_PY="${LIMIT_PY:-900}"
LIMIT_MCP="${LIMIT_MCP:-600}"
LIMIT_PLE="${LIMIT_PLE:-300}"

ALL_STAGES="preflight build ctest ctest-serial worker-load pytest-tools pytest-serve mcp-tools web-ui ple-io"

usage() { sed -n '2,27p' "$0"; exit 2; }

while [ $# -gt 0 ]; do
    a="$1"; shift
    case "$a" in
        --stop)   DO_STOP=1 ;;
        --build)  DO_BUILD=1 ;;
        --only)   ONLY="${1:-}"; shift ;;
        --list)   printf '%s\n' $ALL_STAGES; exit 0 ;;
        --out)    TRANS="${1:-}"; shift ;;
        --limit)  LIMIT_PY="${1:-900}"; LIMIT_CTEST="${1:-900}"; shift ;;
        -h|--help) usage ;;
        *) echo "verify_all_tests.sh: unknown argument: $a" >&2; usage ;;
    esac
done

STAGES="$ALL_STAGES"
if [ -n "$ONLY" ]; then
    STAGES=""
    for want in $(echo "$ONLY" | tr ',' ' '); do
        case "$want" in
            tools) want=pytest-tools ;;
            serve) want=pytest-serve ;;
            mcp)   want=mcp-tools ;;
            web)   want=web-ui ;;
            ple)   want=ple-io ;;
        esac
        found=0
        for s in $ALL_STAGES; do [ "$s" = "$want" ] && found=1; done
        [ "$found" = 1 ] || { echo "no such stage: $want (try --list)" >&2; exit 2; }
        STAGES="$STAGES $want"
    done
fi

mkdir -p "$OUT_DIR" 2>/dev/null || { OUT_DIR="$ROOT/.verify"; mkdir -p "$OUT_DIR"; }
TMPRUN="$OUT_DIR/tmp-$STAMP"
mkdir -p "$TMPRUN"
RESULT_FILE="$OUT_DIR/results-$STAMP.txt"
JSON_FILE="$OUT_DIR/verify-$STAMP.json"
# the stage scripts run in their own sh; they need these
export OUT_DIR STAMP TMPRUN RESULT_FILE JSON_FILE VERIFY_ROOT VERIFY_BUILD VERIFY_TMP
: > "$RESULT_FILE"
: > "$JSON_FILE.tmp"
: > "$TRANS"

# ---------------------------------------------------------------- helpers
free_mib() { nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits 2>/dev/null | head -1; }

engine_pids() {
    for p in /proc/[0-9]*; do
        pid="${p#/proc/}"
        [ "$pid" = "$$" ] && continue
        [ -r "$p/cmdline" ] || continue
        cl="$(tr '\0' ' ' < "$p/cmdline" 2>/dev/null || true)"
        [ -z "$cl" ] && continue
        case "$cl" in
            *serve/server.py*|*hypercore*--serve*|*strata*--serve*) echo "$pid" ;;
        esac
    done
}

# every line the script prints also goes to the transcript, so one file holds the whole run
say() { printf '%s\n' "$1" | tee -a "$TRANS"; }

# the tally line each suite prints, so the summary says what actually happened
tally_of() {
    log="$1"; name="$2"
    case "$name" in
        ctest)         grep -oE '[0-9]+% tests passed, [0-9]+ tests failed out of [0-9]+' "$log" | tail -1 ;;
        pytest-tools|pytest-serve)
                       grep -oE '[0-9]+ passed[^=]*' "$log" | tail -1 ;;
        mcp-tools)     { grep -oE 'TOTAL +[0-9]+ +[0-9]+ +[0-9]+ +[0-9]+ +[0-9]+ +[A-Z]+' "$log" | tail -1;
                        grep -oE 'Ran [0-9]+ tests' "$log" | tail -1;
                        grep -oE '^(OK|FAILED \(.*\))$' "$log" | tail -1; } ;;
        ple-io)        { grep -oE 'ple_direct_rows_per_s = [0-9]+ rows/s \([0-9.]+ us/token\)[^\n]*' "$log" | tail -1;
                        grep -oE 'real-table check: [A-Za-z-]+' "$log" | tail -1; } ;;
        web-ui)        { grep -oE 'web-ui: [0-9]+ suites, [0-9]+ checks' "$log" | tail -1;
                        grep -oE 'SKIP: node is not installed' "$log" | tail -1; } ;;
        ctest-serial)  { grep -oE 'reran [0-9]+ failed test\(s\): [0-9]+ real, [0-9]+ contention or no-GPU' "$log" | tail -1;
                        grep -oE 'NOT REGISTERED [A-Za-z0-9_]+|no worker binary' "$log" | head -3; } ;;
        worker-load)   grep -oE 'worker handshake: .*' "$log" | tail -1 ;;
        build)         grep -oE 'Linking CXX executable [A-Za-z0-9_]+|No targets' "$log" | tail -1 ;;
        *)             : ;;
    esac
}

run_stage() {
    name="$1"; limit="$2"; script="$3"
    log="$OUT_DIR/$name-$STAMP.log"
    say "=== $name ==="
    say "\$ sh $script"
    timeout "$limit" sh "$script" > "$log" 2>&1
    code=$?
    cat "$log" | tee -a "$TRANS"
    # every suite returns non-zero when anything failed, so the exit code is the verdict
    verdict="PASS"; [ "$code" != 0 ] && verdict="FAIL"
    tally="$(tally_of "$log" "$name" | tr '\n' ' ')"
    [ -z "$tally" ] && tally="exit $code"
    printf '%-13s %-5s exit=%-3s %s\n' "$name" "$verdict" "$code" "$tally" >> "$RESULT_FILE"
    say "-> $verdict (exit $code): $tally"
    say ""
    printf '%s|%s|%s|%s\n' "$name" "$verdict" "$code" "$tally" >> "$JSON_FILE.tmp"
}

# ---------------------------------------------------------------- the gate
say "verify_all_tests.sh - $(date -u +%Y-%m-%dT%H:%M:%SZ)"
say "root: $ROOT"
say "transcript: $TRANS"

pids="$(engine_pids)"
if [ -n "$pids" ]; then
    if [ "$DO_STOP" = 1 ]; then
        say "serve engine running ($pids); stopping it"
        sh "$ROOT/restart.sh" stop
        waited=0
        while [ "$waited" -lt 40 ]; do
            pids="$(engine_pids)"
            [ -z "$pids" ] && break
            sleep 2; waited=$((waited + 2))
        done
        pids="$(engine_pids)"
    fi
    if [ -n "$pids" ]; then
        say "ENGINE STILL LOADED: $pids"
        say "57 of the 99 build tests need the GPU.  Run ./restart.sh stop, or re-run with --stop."
        say "Continuing - the GPU stages will fail and the summary will say so."
    fi
else
    say "no serve engine loaded - every stage can run"
fi

fm="$(free_mib)"
if [ -n "$fm" ]; then
    if [ "$fm" -lt "$MIN_FREE_MIB" ]; then
        say "GPU free: $fm MiB - below the $MIN_FREE_MIB MiB the parity tests need"
    else
        say "GPU free: $fm MiB - the card is free"
    fi
fi

# ---------------------------------------------------------------- stage scripts
PLE_GGUF="${HYPERCORE_PLE_GGUF:-}"
if [ -z "$PLE_GGUF" ]; then
    for cfg in "$ROOT/ni_hypercore-q2_0.json" "$ROOT/max_run_q2_0.json"; do
        [ -f "$cfg" ] || continue
        PLE_GGUF="$(python3 - "$cfg" <<'PY'
import json, sys
a = json.load(open(sys.argv[1])).get("args", [])
for i, x in enumerate(a):
    if x == "--ple-gguf" and i + 1 < len(a):
        print(a[i + 1]); break
PY
)"
        [ -n "$PLE_GGUF" ] && break
    done
fi
export HYPERCORE_PLE_GGUF="$PLE_GGUF"
export VERIFY_ROOT="$ROOT"
export VERIFY_BUILD="$BUILD_DIR"
export VERIFY_TMP="$TMPRUN"

cat > "$TMPRUN/preflight.sh" <<'EOF'
echo "host: $(hostname)"
echo "date: $(date -u)"
echo "--- git ---"
cd "$VERIFY_ROOT"
git rev-parse HEAD 2>/dev/null
git log -1 --date=iso --format='%h %ad %s' 2>/dev/null
git status --short 2>/dev/null | grep -vE 'data/|history' | head -40
echo "--- engine binaries ---"
ls -la "$VERIFY_BUILD/hypercore" "$VERIFY_ROOT/engine/hypercore" 2>/dev/null
sha256sum "$VERIFY_BUILD/hypercore" "$VERIFY_ROOT/engine/hypercore" 2>/dev/null
echo "--- cpu ---"
lscpu 2>/dev/null | grep -iE 'model name|avx|cache|core(s)' | head -12
echo "--- memory ---"
free -h 2>/dev/null | head -3
cat /sys/fs/cgroup/memory.max 2>/dev/null
echo "--- gpu ---"
nvidia-smi --query-gpu=name,memory.total,memory.free,driver_version --format=csv,noheader 2>/dev/null
echo "--- toolchain ---"
python3 --version
pytest --version
cmake --version | head -1
ctest --version | head -1
echo "--- model paths ---"
echo "ple-gguf: ${HYPERCORE_PLE_GGUF:-not found}"
ls -la "${HYPERCORE_PLE_GGUF:-/dev/null}" 2>/dev/null
EOF

cat > "$TMPRUN/build.sh" <<'EOF'
cmake --build "$VERIFY_BUILD" -j 4 --target hypercore
EOF

cat > "$TMPRUN/ctest.sh" <<'EOF'
ctest --test-dir "$VERIFY_BUILD" -j 4 --output-on-failure
EOF

cat > "$TMPRUN/ctest-serial.sh" <<'EOF'
# Anything ctest failed is rerun one at a time. A GPU test that passes on its own and fails
# in a -j4 batch was starved by the other three, not broken.
names="$(sed -n '/The following tests FAILED/,/Errors while running CTest/p' \
        "${CLTEST_LOG:-$(ls -1t "$OUT_DIR"/ctest-[0-9]*.log 2>/dev/null | head -1)}" 2>/dev/null \
        | grep -oE '[A-Za-z0-9_]+ \(Failed\)' | sed 's/ (Failed)//')"
if [ -z "$names" ]; then
    echo "nothing to rerun: no failed tests found in ${CLTEST_LOG:-$(ls -1t "$OUT_DIR"/ctest-[0-9]*.log 2>/dev/null | head -1)}"
    exit 0
fi
real=0; contention=0
for n in $names; do
    out="$(timeout 120 ctest --test-dir "$VERIFY_BUILD" -R "^${n}$" --output-on-failure 2>&1)"
    if echo "$out" | grep -qE "No tests were found"; then
        echo "NOT REGISTERED $n: this build tree does not register that test. It was registered by the"
        echo "  configure the failed run used; the tree has been reconfigured since. Re-run cmake -configure"
        echo "  (or --build) before trusting this result."
        contention=$((contention + 1))
    elif echo "$out" | grep -qE "Test #.* Passed"; then
        echo "CONTENTION $n: passes serially - it was starved by the -j4 batch"
        contention=$((contention + 1))
    elif echo "$out" | grep -qiE 'out of memory|busy or unavailable|CUDA-capable|cudaMalloc failed|could not be allocated'; then
        echo "NO GPU $n: the card is not free; stop the serve engine and rerun"
        contention=$((contention + 1))
    else
        echo "REAL FAILURE $n:"
        echo "$out" | sed -n '1,12p' | sed 's/^/    /'
        real=$((real + 1))
    fi
done
echo "reran $(echo $names | wc -w) failed test(s): $real real, $contention contention or no-GPU"
[ "$real" = 0 ] || exit 1
EOF

cat > "$TMPRUN/worker-load.sh" <<'EOF'
# The serve path spawns the worker process. Check it can be loaded and completes the READY
# handshake before any run script is asked to start it.
cd "$VERIFY_ROOT"
WORKER="${VERIFY_WORKER:-}"
if [ -z "$WORKER" ]; then
    for c in ni_hypercore-q2_0.json max_run_q2_0.json; do
        [ -f "$c" ] || continue
        WORKER="$(python3 - "$c" <<'PY'
import json, sys
c = json.load(open(sys.argv[1]))
print(c.get("worker") or "")
PY
)"
        [ -n "$WORKER" ] && break
    done
fi
[ -n "$WORKER" ] || WORKER="$VERIFY_ROOT/build-shared/hypercore-worker"
[ -f "$WORKER" ] || WORKER="$VERIFY_ROOT/build/hypercore-worker"
if [ ! -f "$WORKER" ]; then
    echo "no worker binary: build it with cmake --build build-shared --target hypercore-worker"
    exit 1
fi
echo "worker: $WORKER"
soname="$(objdump -p "$WORKER" 2>/dev/null | awk '/NEEDED/ && /libhypercore_api/ {print $2; exit}')"
dir="$(dirname "$WORKER")"
if ldd "$WORKER" 2>/dev/null | grep -q "not found"; then
    versioned="$(ls "$dir"/libhypercore_api.so.*.* 2>/dev/null | head -1)"
    if [ -n "$versioned" ] && [ -n "$soname" ]; then
        echo "the build tree has $(basename "$versioned") but no soname link for $soname"
        echo "cmake --build does not create it; cmake --install does. Creating it here:"
        ln -sf "$(basename "$versioned")" "$dir/$soname"
        ln -sf "$soname" "$dir/libhypercore_api.so"
    else
        echo "cannot find a libhypercore_api artifact next to the worker"
    fi
fi
ldd "$WORKER" 2>/dev/null | head -4
python3 - "$WORKER" "$VERIFY_TMP/worker-probe.sock" <<'PY'
import sys
from serve.hypercore_supervisor import HyperCoreProcessSupervisor
worker, sock = sys.argv[1], sys.argv[2]
try:
    sup = HyperCoreProcessSupervisor(worker_binary=worker, socket_path=sock,
                                    config='{"batch": 2}')
    sup.start(timeout_s=30)
    ok = sup.ping()
    sup.stop()
    print(f"worker handshake: {'OK' if ok else 'READY but no reply to ping'}")
    sys.exit(0 if ok else 1)
except Exception as exc:
    print(f"worker handshake: FAILED - {exc}")
    sys.exit(1)
PY
EOF

cat > "$TMPRUN/pytest-tools.sh" <<'EOF'
cd "$VERIFY_ROOT" && TMPDIR="$VERIFY_TMP" python3 -m pytest tools/ -q
EOF

cat > "$TMPRUN/pytest-serve.sh" <<'EOF'
cd "$VERIFY_ROOT" && TMPDIR="$VERIFY_TMP" python3 -m pytest serve/ -q
EOF

cat > "$TMPRUN/mcp-tools.sh" <<'EOF'
cd "$VERIFY_ROOT"
python3 serve/mcp/tests/run_all.py --no-live --json "$VERIFY_TMP/mcp-report.json"
if [ $? -ne 0 ]; then
    echo "run_all.py did not complete; running the modules directly"
    python3 -m unittest serve.mcp.tests.test_contracts serve.mcp.tests.test_terminal \
        serve.mcp.tests.test_scrape serve.mcp.tests.test_docs serve.mcp.tests.test_home \
        serve.mcp.tests.test_web serve.mcp.tests.test_browser serve.mcp.tests.test_hub
fi
EOF

cat > "$TMPRUN/web-ui.sh" <<'EOF'
# The page ships as files, so its tests read them: no browser, no GPU, no weights.
cd "$VERIFY_ROOT"
if ! command -v node >/dev/null 2>&1; then
    echo "SKIP: node is not installed on this machine"
    exit 0
fi
suites=0; checks=0
for t in test_stop_start_buttons test_surface_slider test_assist_thought_panel; do
    echo "--- serve/web/$t.js"
    out="$(node "serve/web/$t.js")" || { echo "$out"; exit 1; }
    echo "$out"
    n=$(printf '%s\n' "$out" | grep -c '^ok')
    suites=$((suites + 1)); checks=$((checks + n))
done
echo "web-ui: $suites suites, $checks checks"
EOF

cat > "$TMPRUN/ple-io.sh" <<'EOF'
# The direct-vs-mmap A/B, GPU-free: this is what --ple-io direct measures at startup.
cd "$VERIFY_ROOT"
GGUF="${HYPERCORE_PLE_GGUF:-}"
[ -f "$GGUF" ] || { echo "no PLE table: set HYPERCORE_PLE_GGUF or point at a run config"; exit 1; }
python3 - "$VERIFY_ROOT/bench/results/exchange-rotation-token-ids.json" > "$VERIFY_TMP/tokens.txt" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
print(",".join(str(t) for t in d["input"]))
PY
for arm in "" "--direct-first" "--direct-only"; do
    echo "--- ple_reader_test ${arm:-default order}"
    "$VERIFY_BUILD/ple_reader_test" --gguf "$GGUF" --rows 20000 \
        --tokens "$VERIFY_TMP/tokens.txt" --inflight 256 $arm | tee -a "$VERIFY_TMP/ple-ab.txt"
done
python3 - "$VERIFY_TMP/ple-ab.txt" <<'PY'
import re, sys
best = None
for line in open(sys.argv[1]):
    m = re.search(r"direct ([0-9.]+) us/token", line)
    if m:
        us = float(m.group(1))
        if us > 0: best = us if best is None else min(best, us)
if best:
    rps = 16000000.0 / best          # 16 rows per token
    print(f"ple_direct_rows_per_s = {rps:.0f} rows/s ({best:.1f} us/token)"
          + (" - under the 15000 bar, mmap would be worth a look" if rps < 15000 else " - above the 15000 bar, direct is the right choice"))
PY
EOF

# ---------------------------------------------------------------- run
for stage in $STAGES; do
    case "$stage" in
        build)
            [ "$DO_BUILD" = 1 ] || { say "=== build === (skipped: pass --build to rebuild)"; continue; }
            run_stage build 900 "$TMPRUN/build.sh" ;;
        ctest)         run_stage ctest "$LIMIT_CTEST" "$TMPRUN/ctest.sh"
                       CLTEST_LOG="$OUT_DIR/ctest-$STAMP.log" ;;
        ctest-serial)  run_stage ctest-serial 300 "$TMPRUN/ctest-serial.sh" ;;
        worker-load)   run_stage worker-load 120 "$TMPRUN/worker-load.sh" ;;
        pytest-tools)  run_stage pytest-tools "$LIMIT_PY" "$TMPRUN/pytest-tools.sh" ;;
        pytest-serve)  run_stage pytest-serve "$LIMIT_PY" "$TMPRUN/pytest-serve.sh" ;;
        mcp-tools)     run_stage mcp-tools "$LIMIT_MCP" "$TMPRUN/mcp-tools.sh" ;;
        web-ui)        run_stage web-ui 120 "$TMPRUN/web-ui.sh" ;;
        ple-io)        run_stage ple-io "$LIMIT_PLE" "$TMPRUN/ple-io.sh" ;;
        preflight)     run_stage preflight 120 "$TMPRUN/preflight.sh" ;;
    esac
done

# ---------------------------------------------------------------- summary
say ""
say "================ summary ================"
cat "$RESULT_FILE" | tee -a "$TRANS"
say "======================================="
npass=$(grep -c ' PASS' "$RESULT_FILE" || true)
nfail=$(grep -c ' FAIL' "$RESULT_FILE" || true)
say "stages passed: ${npass:-0}, failed: ${nfail:-0}"
say "transcript:    $TRANS"
say "per-stage logs: $OUT_DIR/"
say "machine-readable: $JSON_FILE"

# compare with the previous run in the same directory, so a regression is visible at a glance
prev="$(ls -1 "$OUT_DIR"/results-*.txt 2>/dev/null | grep -v "$STAMP" | tail -1)"
if [ -n "$prev" ]; then
    say ""
    say "--- diff against the previous run ($prev) ---"
    diff -u "$prev" "$RESULT_FILE" | sed 's/^/  /' | tee -a "$TRANS"
    [ -f "$prev" ] && diff -u "$prev" "$RESULT_FILE" >/dev/null && say "  identical verdicts"
fi
{
    printf '{\n  "run": "%s",\n  "root": "%s",\n  "stages": [\n' "$STAMP" "$ROOT"
    first=1
    while IFS='|' read -r name verdict code tally; do
        [ "$first" = 1 ] || printf ',\n'
        first=0
        printf '    {"stage": "%s", "verdict": "%s", "exit": %s, "tally": "%s"}' \
            "$name" "$verdict" "$code" "$(printf '%s' "$tally" | tr -d '"')"
    done < "$JSON_FILE.tmp"
    printf '\n  ]\n}\n'
} > "$JSON_FILE"
rm -f "$JSON_FILE.tmp"

[ "${nfail:-0}" = 0 ] && exit 0
exit 1
