#!/usr/bin/env bash
# hypercore-sycl.sh: the SYCL-built engine as a drop-in `exe` for serve/server.py (--engine hypercore). The port's binary
# needs the oneAPI runtime of the dev image, so this runs it there with stdin/stdout attached (the serve protocol is
# lines on those pipes) and stderr going to the server's log. Paths in the config's args are the container's:
# the data root is mounted at /work.
#   HYPERCORE_SYCL_ROOT   host directory mounted at /work        (default: two levels above this script's repo)
#   HYPERCORE_SYCL_IMAGE  the runtime image                      (default: hypercore-sycl-dev)
#   HYPERCORE_SYCL_BIN    the engine binary, relative to the repo (default: build-sycl-aot/hypercore)
#   HYPERCORE_SYCL_NAME   the container's name                   (default: hypercore-sycl-serve)
#   ONEAPI_DEVICE_SELECTOR  passed in when set (the image pins level_zero:0; level_zero:* for a two-card split, #423)
set -euo pipefail
here=$(cd "$(dirname "$0")/../.." && pwd)                 # the repo
root=${HYPERCORE_SYCL_ROOT:-$(dirname "$here")}
repo_in=/work/$(basename "$here")
name=${HYPERCORE_SYCL_NAME:-hypercore-sycl-serve}
docker rm -f "$name" >/dev/null 2>&1 || true              # a container left behind by a killed server
args=""
for a in "$@"; do args+=" $(printf '%q' "$a")"; done
sel=()
[ -n "${ONEAPI_DEVICE_SELECTOR:-}" ] && sel=(-e "ONEAPI_DEVICE_SELECTOR=$ONEAPI_DEVICE_SELECTOR")
# the port's run-time switches: the device-built verify plan without host handshakes (docs/INTEL.md)
exec docker run --rm -i --name "$name" --device /dev/dri --oom-score-adj 1000 --stop-timeout 30 --no-healthcheck \
    -v "$root:/work" \
    -e HYPERCORE_VERIFY_DEVICE_PLAN=1 -e HYPERCORE_VERIFY_NO_HOST=1 -e HYPERCORE_STAGER_THREADS=12 \
    "${sel[@]}" \
    "${HYPERCORE_SYCL_IMAGE:-hypercore-sycl-dev}" \
    "cd $repo_in && exec ${HYPERCORE_SYCL_BIN:-build-sycl-aot/hypercore}$args"
