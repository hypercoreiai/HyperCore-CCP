#!/bin/sh
# tools/rename_hypercore.sh - hypercore -> hypercore, applied in one pass.
#
# Order matters: file names first (git mv keeps history), then identifiers.
# Only source, build config, and tests are touched; build directories are regenerated.
set -e
cd "$(dirname "$0")/.."

# 1. the public header moves to its own clean location (idempotent: safe to re-run)
if [ -f include/hypercore/hypercore_blackbox.h ]; then
  mkdir -p include/hypercore
  git mv include/hypercore/hypercore_blackbox.h include/hypercore/hypercore_api.h 2>/dev/null \
    || mv include/hypercore/hypercore_blackbox.h include/hypercore/hypercore_api.h
fi

# 2. the internal include tree follows
if [ -d include/hypercore ]; then
  mkdir -p include/hypercore
  for entry in include/hypercore/*; do mv "$entry" include/hypercore/; done
  rmdir include/hypercore
fi

# 3. the interface translation units
if [ -f src/interface/hypercore_bridge.cpp ]; then
  git mv src/interface/hypercore_bridge.cpp src/interface/hypercore_bridge.cpp 2>/dev/null \
    || mv src/interface/hypercore_bridge.cpp src/interface/hypercore_bridge.cpp
fi

# 4. identifiers. Whole-word only; build outputs are set by OUTPUT_NAME, not by sed.
FILES=$(grep -rl 'hypercore' --include='*.h' --include='*.hpp' --include='*.hxx' --include='*.c' --include='*.cpp' \
        --include='*.cu' --include='*.cuh' --include='*.inc' --include='*.inl' --include='*.py' \
        --include='*.sh' --include='*.json' --include='CMakeLists.txt' \
        src include sycl serve tools bench CMakeLists.txt 2>/dev/null | grep -v 'rename_hypercore.sh')

for f in $FILES; do
  sed -i \
    -e 's|#include "hypercore/|#include "hypercore/|g' \
    -e 's|#include <hypercore/|#include <hypercore/|g' \
    -e 's/namespace hypercore/namespace hypercore/g' \
    -e 's/hypercore::/hypercore::/g' \
    -e 's/HYPERCORE_/HYPERCORE_/g' \
    -e 's/\bhypercore-/hypercore-/g' \
    -e 's/\bhypercore_/hypercore_/g' \
    -e 's/add_executable(hypercore /add_executable(hypercore /g' \
    "$f"
done

echo "renamed $(echo "$FILES" | wc -l) files"
