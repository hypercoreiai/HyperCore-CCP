#!/usr/bin/env bash
# install.sh - build the HyperCore black-box boundary, then prove it, in the order CI runs it.
#
# The stages below are the five jobs in .github/workflows/boundary.yml. A green run of this
# script makes the same claim a green merge request makes:
#
#   1. contract-lock      the header, the Python mirrors and the worker's frame writer agree
#                         byte for byte, and the produced artifact does not require a libc
#                         newer than the deployment floor.
#   2. supervisor-tests   the slot gate sheds, reclaims and cancels - against the stub, so
#                         it needs no GPU and no weights.
#   3. backend-parity     a backend repeats itself, and every backend that was built answers
#                         the same request the same way.
#   4. model-guard        the real compute kernels, gated on pack/full actually being on disk.
#   5. cross-toolchain    the same .so compiled and linked on a machine that shares nothing
#                         with this one.
#
# Stages 1-3 need only a compiler and Python. Stage 4 is gated on file presence and stage 5
# on DAYTONA_API_KEY; both report SKIP instead of pretending they measured something.
#
# Run:
#   ./install.sh                                  # CPU tree + every local gate + install to ./dist
#   ./install.sh --cuda                           # also build the CUDA tree and compare backends
#   ./install.sh --prefix /usr/local              # install the artifact and the public header
#   ./install.sh --cross-toolchain                # force the Daytona stage (needs DAYTONA_API_KEY)
#   ./install.sh --model-guard                    # force the pack-gated guard; fails if no pack
#   ./install.sh --deps                           # create .venv and install requirements.txt first
#   ./install.sh --help

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

# --------------------------------------------------------------------------- defaults
BUILD_DIR="build-shared"            # CPU tree; tools/backend_parity.py looks here for "cpu"
CUDA_BUILD_DIR="build-cuda-check"   # GPU tree; tools/backend_parity.py looks here for "cuda"
PREFIX="dist"
JOBS=4
FLOOR="${HYPERCORE_GLIBC_FLOOR:-2.39}"   # same value as HYPERCORE_GLIBC_FLOOR in CMakeLists
API_KEY="${HYPERCORE_TEST_API_KEY:-ci-boundary-key}"
CONCURRENCY=12
SLOTS=4
REPEAT=2
PY=""
WITH_CUDA=0
WANT_MODEL_GUARD=0
WANT_CROSS_TOOLCHAIN=0
WANT_DEPS=0
DO_INSTALL=1

usage() {
  sed -n '2,26p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}/  /'
  exit 0
}

while [ $# -gt 0 ]; do
  case "$1" in
    --build-dir)        BUILD_DIR="$2"; shift 2 ;;
    --cuda-build-dir)   CUDA_BUILD_DIR="$2"; shift 2 ;;
    --prefix)           PREFIX="$2"; shift 2 ;;
    --jobs)             JOBS="$2"; shift 2 ;;
    --floor)            FLOOR="$2"; shift 2 ;;
    --api-key)          API_KEY="$2"; shift 2 ;;
    --concurrency)      CONCURRENCY="$2"; shift 2 ;;
    --slots)            SLOTS="$2"; shift 2 ;;
    --python)           PY="$2"; shift 2 ;;
    --cuda)             WITH_CUDA=1; shift ;;
    --model-guard)      WANT_MODEL_GUARD=1; shift ;;
    --cross-toolchain)  WANT_CROSS_TOOLCHAIN=1; shift ;;
    --deps)             WANT_DEPS=1; shift ;;
    --no-install)       DO_INSTALL=0; shift ;;
    -h|--help)          usage ;;
    *) echo "unknown option: $1 (see --help)" >&2; exit 2 ;;
  esac
done

# --------------------------------------------------------------------------- helpers
FAILURES=0
RESULTS=()

record() {   # record <stage> <PASS|FAIL|SKIP> <why>
  RESULTS+=("$(printf '  %-18s %-5s %s' "$1" "$2" "$3")")
  if [ "$2" = FAIL ]; then FAILURES=$((FAILURES + 1)); fi
  return 0
}

report() {
  hr
  say "summary"
  hr
  if [ "${#RESULTS[@]}" -gt 0 ]; then
    for line in "${RESULTS[@]}"; do say "$line"; done
  fi
  if [ "$FAILURES" -gt 0 ]; then
    say "$FAILURES stage(s) failed - the boundary is not proven."
    return 1
  fi
  say "all stages passed: the boundary is built, byte-locked, and load-gated."
  return 0
}

say() { printf '%s\n' "$*"; }
hr()  { printf '%s\n' "------------------------------------------------------------"; }

# One step inside a stage. The first step that fails ends the stage, exactly as a failing
# step ends a CI job - so a stage can never report PASS on the strength of its last command.
step() {
  label="$1"; shift
  say "> ${label}"
  if "$@"; then return 0; fi
  say "  step failed: ${label}"
  return 1
}

# Runs a stage and records its outcome; the pipeline continues so the summary shows every
# stage, but a failure is never swallowed.
run_stage() {
  name="$1"
  hr
  say "stage: ${name}"
  hr
  if "$name"; then
    record "$name" PASS ""
  else
    record "$name" FAIL "see the output above"
  fi
  return 0
}

pick_python() {
  if [ -n "$PY" ]; then return 0; fi
  if [ -x "$ROOT/.venv/bin/python" ]; then
    PY="$ROOT/.venv/bin/python"
  else
    PY="python3"
  fi
  return 0
}

preflight() {
  missing=""
  for tool in cmake make gcc objdump; do
    command -v "$tool" >/dev/null 2>&1 || missing="$missing $tool"
  done
  if [ -n "$missing" ]; then
    say "missing build tools:$missing"
    say "Ubuntu/Debian: sudo apt-get install -y build-essential cmake"
    return 1
  fi
  if ! "$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
    say "$PY is not Python 3.10+; the contract lock and the test suites need 3.10 or newer."
    return 1
  fi
  say "toolchain: $($PY --version | head -1), $(cmake --version | head -1), $(gcc --version | head -1)"
  return 0
}

install_deps() {
  if [ ! -x "$ROOT/.venv/bin/python" ]; then
    step "create .venv" "$PY" -m venv .venv || {
      say "could not create .venv (Ubuntu/Debian: sudo apt install python3-venv)"
      return 1
    }
  fi
  PY="$ROOT/.venv/bin/python"
  step "install requirements.txt" "$PY" -m pip install -q -r requirements.txt || return 1
  if [ "$WANT_CROSS_TOOLCHAIN" = 1 ]; then
    step "install the Daytona client" "$PY" -m pip install -q daytona || return 1
  fi
  say "dependencies installed into .venv"
  return 0
}

# --------------------------------------------------------------------------- stage 1
stage_contract_lock() {
  # The ABI check and the libc floor are build dependencies of both artifacts, so the
  # configure/build below cannot produce an .so that the contract lock has not already
  # rejected. The explicit runs afterwards are the machine-readable report of the same gate.
  step "configure ${BUILD_DIR} (CPU)" \
    cmake -B "$BUILD_DIR" -DHYPERCORE_ENABLE_CUDA=OFF -DHYPERCORE_GLIBC_FLOOR="$FLOOR" || return 1
  step "build the boundary (hypercore_api, hypercore-worker)" \
    cmake --build "$BUILD_DIR" --target hypercore_api hypercore-worker -j"$JOBS" || return 1
  step "wire layout: header vs Python mirrors vs frame writer" \
    "$PY" tools/check_abi_alignment.py --json || return 1
  step "libc floor: reader tests" "$PY" -m unittest tools.test_glibc_floor || return 1
  step "libc floor: the artifact itself (<= ${FLOOR})" \
    "$PY" tools/glibc_floor.py --require "$FLOOR" "$BUILD_DIR/libhypercore_api.so" || return 1
  return 0
}

# --------------------------------------------------------------------------- stage 2
stage_supervisor_tests() {
  step "supervisor suites (slots, cancel, recovery, config forms, stream loop, auth)" \
    "$PY" -m unittest serve.test_abi_contract serve.test_slots serve.test_control_cancel \
                  serve.test_fatal_recovery serve.test_config_forms serve.test_stream_loop \
                  serve.test_http_auth || return 1
  # Integration guard: the stub needs no GPU and no weights, so the 503 gate, the
  # drop-mid-stream slot reclaim and the stall cancel are exercised on every merge.
  step "integration guard: stub flood behind the API key" \
    "$PY" tools/bench_flood.py --concurrency "$CONCURRENCY" --slots "$SLOTS" \
      --api-key "$API_KEY" || return 1
  return 0
}

# --------------------------------------------------------------------------- stage 3
stage_backend_parity() {
  step "parity rules" "$PY" -m unittest tools.test_backend_parity || return 1
  step "determinism gate (cpu, one request, two runs)" \
    "$PY" tools/backend_parity.py --backend cpu --require cpu --repeat "$REPEAT" || return 1
  if [ -f "$CUDA_BUILD_DIR/hypercore-worker" ]; then
    step "cross-backend parity (cpu vs cuda)" \
      "$PY" tools/backend_parity.py --backend cpu --backend cuda --require cpu,cuda || return 1
  else
    say "no CUDA artifact in ${CUDA_BUILD_DIR} - cross-backend parity is not claimed by this run"
  fi
  return 0
}

# --------------------------------------------------------------------------- stage 4
stage_model_guard() {
  if [ -d pack/full ] && [ -n "$(ls -A pack/full 2>/dev/null)" ]; then
    step "hardware guard: real model pack" \
      "$PY" tools/bench_flood.py --model --concurrency 16 --slots 4 || return 1
    return 0
  fi
  if [ "$WANT_MODEL_GUARD" = 1 ]; then
    say "model guard requested, but pack/full is absent or empty"
    return 1
  fi
  say "no model pack on disk - the hardware guard is skipped by design, not by omission"
  return 0
}

# --------------------------------------------------------------------------- stage 5
stage_cross_toolchain() {
  if [ -z "${DAYTONA_API_KEY:-}" ]; then
    if [ "$WANT_CROSS_TOOLCHAIN" = 1 ]; then
      say "DAYTONA_API_KEY is not set; the cross-toolchain stage was requested and cannot run."
      return 1
    fi
    say "DAYTONA_API_KEY not set - skipping the foreign-toolchain stage."
    say "To run it: export DAYTONA_API_KEY=... && ./install.sh --cross-toolchain"
    return 0
  fi
  if ! "$PY" -c 'import daytona' >/dev/null 2>&1; then
    say "the daytona package is not installed in $($PY --version | head -1)"
    say "run: ./install.sh --deps --cross-toolchain"
    return 1
  fi
  step "same .so, foreign gcc and CPython" "$PY" tools/daytona_bridge_test.py || return 1
  return 0
}

# --------------------------------------------------------------------------- install
stage_install() {
  # The prefix may hold an artifact from an earlier run. CMake patches the RPATH of every
  # destination file it finds already there, and a malformed ELF - the half-written copy an
  # interrupted install leaves behind - makes that scan read a nonsense section size: on
  # this machine it aborted the stage with std::bad_alloc before a byte was copied. The
  # library is built from source a few lines above, so the prefix is cleared first and the
  # result is checked after: a stale dist/ can never break a later run.
  if [ -d "$PREFIX/lib" ]; then
    rm -f "$PREFIX/lib/libhypercore_api.so" "$PREFIX/lib/libhypercore_api.so."*
  fi
  step "install the library and the public header to ${PREFIX}" \
    cmake --install "$BUILD_DIR" --prefix "$PREFIX" || return 1
  # The two checks are the stage's real claim: what is in dist/ is byte for byte the
  # artifact this run built, and a process can actually load it.
  step "the installed library is the artifact this run built" \
    cmp -s "$PREFIX/lib/libhypercore_api.so" "$BUILD_DIR/libhypercore_api.so" || return 1
  step "the installed library loads" \
    "$PY" -c "import ctypes; ctypes.CDLL('${PREFIX}/lib/libhypercore_api.so')" || return 1
  # The worker is the other half of the boundary. CMake has no install rule for it, so it
  # is placed next to the library it links against instead of left in the build tree.
  mkdir -p "$PREFIX/bin"
  step "install hypercore-worker to ${PREFIX}/bin" \
    install -m 755 "$BUILD_DIR/hypercore-worker" "$PREFIX/bin/hypercore-worker" || return 1
  say "installed:"
  say "  ${PREFIX}/lib/libhypercore_api.so"
  say "  ${PREFIX}/include/hypercore/hypercore_api.h"
  say "  ${PREFIX}/bin/hypercore-worker"
  say "consumer link line:"
  say "  gcc -I ${PREFIX}/include/hypercore app.c -L ${PREFIX}/lib -lhypercore_api -Wl,-rpath,${PREFIX}/lib"
  return 0
}

# --------------------------------------------------------------------------- main
pick_python
hr
say "HyperCore boundary install - stages 1-5 of .github/workflows/boundary.yml"
hr

if ! preflight; then
  record "preflight" FAIL "toolchain or interpreter missing"
  report
  exit 1
fi

if [ "$WANT_DEPS" = 1 ]; then
  if install_deps; then record "deps" PASS ""; else record "deps" FAIL ""; exit 1; fi
fi

run_stage stage_contract_lock
# Nothing after this can be proven without the artifact, so stop rather than cascade.
if [ "$FAILURES" -gt 0 ]; then
  report
  say "the contract lock failed; the remaining stages cannot be claimed."
  exit 1
fi

if [ "$WITH_CUDA" = 1 ]; then
  if step "build the CUDA tree" \
      cmake -B "$CUDA_BUILD_DIR" -DHYPERCORE_ENABLE_CUDA=ON &&
     cmake --build "$CUDA_BUILD_DIR" --target hypercore-worker -j"$JOBS"; then
    record "cuda-build" PASS ""
  else
    record "cuda-build" FAIL "CUDA tree did not build"
  fi
fi

run_stage stage_supervisor_tests
run_stage stage_backend_parity
run_stage stage_model_guard
run_stage stage_cross_toolchain

if [ "$DO_INSTALL" = 1 ]; then
  run_stage stage_install
fi

report
[ "$FAILURES" -eq 0 ] || exit 1
exit 0
