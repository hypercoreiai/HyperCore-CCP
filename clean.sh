#!/usr/bin/env bash
# clean.sh - remove what this project generates, never what it is.
#
#   ./clean.sh                      the same as --builds
#   ./clean.sh --builds             the build trees and the Python caches
#   ./clean.sh --all                --builds plus .venv, .venv_daytona and dist/
#   ./clean.sh --scratch            the tracked scratch files at the root, through git rm
#   ./clean.sh --dry-run            with any tier: report the sizes, delete nothing
#   ./clean.sh --root DIR          operate on DIR instead of the folder this script sits in
#
# Never deleted, whatever the flags:
#   engine/  third_party/  data/  bench/  serve/  src/  tools/  tests/  docs/
#   prompts/ include/  sycl/  ref/   and the run configs (hypercore-*.json, run-*.sh)
# Those are the engine binary, the vendored llama.cpp the GGUF tools import, the measured
# data and setup.py's own output. A reset has to be recoverable with ./install.sh, not a
# loss of work.
#
# After --builds the engine is one command away:
#   cmake -B build -DHYPERCORE_ENABLE_CUDA=OFF && cmake --build build -j4
# After --all, ./install.sh recreates the environment and the build.

set -eu

usage() { sed -n '2,19p' "$0" | sed 's/^# \{0,1\}//'; }

ROOT=""
DRY=0
WANT_BUILD=0
WANT_ALL=0
WANT_SCRATCH=0

while [ $# -gt 0 ]; do
  case "$1" in
    --builds)  WANT_BUILD=1 ;;
    --all)     WANT_ALL=1; WANT_BUILD=1 ;;
    --scratch) WANT_SCRATCH=1 ;;
    --dry-run) DRY=1 ;;
    --root)
      shift
      ROOT="${1:-}"
      [ -n "$ROOT" ] || { echo "clean.sh: --root needs a directory" >&2; exit 2; }
      ;;
    -h|--help) usage; exit 0 ;;
    *) echo "clean.sh: unknown flag: $1" >&2; usage; exit 2 ;;
  esac
  shift
done

if [ -z "$ROOT" ]; then ROOT="$(dirname "$0")"; fi
if [ ! -d "$ROOT" ]; then echo "clean.sh: no such directory: $ROOT" >&2; exit 2; fi
ROOT="$(cd "$ROOT" && pwd)"

# No tier named means the safe one.
if [ "$WANT_BUILD" -eq 0 ] && [ "$WANT_ALL" -eq 0 ] && [ "$WANT_SCRATCH" -eq 0 ]; then
  WANT_BUILD=1
fi

TARGETS=()

add_target() {
  p="$1"
  [ -e "$p" ] || return 0
  if [ ${#TARGETS[@]} -gt 0 ]; then
    for t in "${TARGETS[@]}"; do
      case "$p" in "$t"/*) return 0 ;; esac   # already covered by a parent we listed
    done
  fi
  TARGETS+=("$p")
}

bytes_of() {
  if [ -d "$1" ]; then du -sb "$1" 2>/dev/null | head -1 | cut -f1; else stat -c%s "$1" 2>/dev/null || echo 0; fi
}

human() {
  awk -v n="$1" 'BEGIN {
    if (n >= 1073741824) printf "%.1f GB", n / 1073741824
    else if (n >= 1048576) printf "%.1f MB", n / 1048576
    else printf "%.0f KB", n / 1024
  }'
}

tiers=""
[ "$WANT_BUILD" -eq 1 ] && tiers="builds"
[ "$WANT_ALL" -eq 1 ] && tiers="${tiers:+$tiers + }all"
[ "$WANT_SCRATCH" -eq 1 ] && tiers="${tiers:+$tiers + }scratch"

# 1. the build trees and the caches they leave behind
if [ "$WANT_BUILD" -eq 1 ] || [ "$WANT_ALL" -eq 1 ]; then
  for d in "$ROOT"/build*/; do
    [ -d "$d" ] || continue
    add_target "${d%/}"
  done
  while IFS= read -r c; do add_target "$c"; done < <(
    find "$ROOT" -type d \( -name __pycache__ -o -name .pytest_cache \) \
      -not -path "*/.venv*" -not -path "*/.git/*" -not -path "*/third_party/*" 2>/dev/null
  )
fi

# 2. the environment and the staged install
if [ "$WANT_ALL" -eq 1 ]; then
  for d in .venv .venv_daytona dist; do add_target "$ROOT/$d"; done
fi

# 3. the tracked logs and backups that accumulated at the root
if [ "$WANT_SCRATCH" -eq 1 ]; then
  if git -C "$ROOT" rev-parse --git-dir >/dev/null 2>&1; then
    while IFS= read -r f; do
      case "$f" in
        .review_*|.bb_*|.ci_*|.mcp_run_all*|.full_suite_after.txt|.run_all_now.txt|\
        .tools_tests_*|.docs_sync_marker.txt|_*.py|*.orig*|*.bak)
          add_target "$ROOT/$f" ;;
      esac
    done < <(git -C "$ROOT" ls-files | grep -v / || true)
  else
    echo "clean.sh: --scratch needs a git repository; skipped" >&2
  fi
fi

if [ ${#TARGETS[@]} -eq 0 ]; then
  echo "clean.sh: nothing to remove in $ROOT"
  exit 0
fi

total=0
echo "clean.sh --$tiers on $ROOT"
for t in "${TARGETS[@]}"; do
  b="$(bytes_of "$t")"
  total=$((total + b))
  printf '  %-10s  %s\n' "$(human "$b")" "${t#"$ROOT"/}"
done
echo "  ----------"
printf '  %-10s  %s\n' "$(human "$total")" "total"
echo "  kept: engine/ third_party/ data/ bench/ serve/ src/ tools/ tests/ docs/ prompts/ include/ sycl/ ref/ and the run configs"

if [ "$DRY" -eq 1 ]; then
  echo "  (dry run: nothing was removed)"
  exit 0
fi

for t in "${TARGETS[@]}"; do
  rel="${t#"$ROOT"/}"
  if git -C "$ROOT" ls-files -- "$rel" 2>/dev/null | grep -q .; then
    git -C "$ROOT" rm -q -- "$rel"          # tracked: delete it where git can see it
  else
    rm -rf "$t"
  fi
done
echo "  removed $(human "$total"); source and data untouched"
if [ "$WANT_BUILD" -eq 1 ] || [ "$WANT_ALL" -eq 1 ]; then
  echo "  rebuild: cmake -B build -DHYPERCORE_ENABLE_CUDA=OFF && cmake --build build -j4"
fi
