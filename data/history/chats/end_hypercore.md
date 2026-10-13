# end_hypercore.txt

unknown · 329 KB · 1 requests · topics: setup-configuration

## What was asked
- the workflow has never run - GPU numerical parity is still untested: the CUDA artifacts build and the ABI is byte-identical, but nothing compares token output between the CPU and CUDA backends. [key] https://app.daytona.io/api

## What came of it
- cross-toolchain: build `hypercore_api hypercore_glibc_floor_check` so the floor is reported, and also run the artifact floor check against the sandbox floor.
- tools/glibc_floor.py reads it off the binary; --require fails the build.
- README section 26 documents the failure, the fix, and the measured floors; `.blackbox_api_state.json` is at loop 42 and parses.
- The floor gate special-cases `sqrtf`; a newly versioned symbol from ggml would fail the build with the symbol named, and the fix is one more `__wrap_` shim — there is no generated shim yet.
