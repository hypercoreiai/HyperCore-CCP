#!/usr/bin/env bash
# max_config_q2_0.sh - generated 2026-10-12 13:08:59 UTC by max_tune.sh (sweep 2026-10-12_121818)
# Peak measured decode: 171.31 tok/s at --max-context 131072 (17 configurations evaluated, 10 measured).
# Complete sweep.
# pcie-frac, spec-min-p and pool-workers were frozen by tools/calibrate.py before the sweep.
# Source this file, or let max_run_q2_0.sh read it.
#
HC_MODEL="q2_0"
HC_SWEEP_STAMP="2026-10-12_121818"
HC_COMPLETE=1
HC_ENGINE="/home/ai-user0/black_box/engine/hypercore"
HC_PACK="/home/ai-agent/HyperCore-data/packs/q2_0"
HC_NATIVE="/home/ai-agent/HyperCore-data/models/Q2_0/Qwen3.8-Flash-Next-GSQ-RCO-Q2_0-00001-of-00002.gguf"
HC_PLE_GGUF="/home/ai-agent/HyperCore-data/models/Q2_0/Qwen3.8-Flash-Next-GSQ-RCO-Q2_0-00002-of-00002.gguf"
HC_MTP="/home/ai-agent/HyperCore-data/mtp/rt"
HC_EXPERT_PROFILE="/home/ai-user0/black_box/data/expert-profile.bin"
HC_CVEC_SCALED="/home/ai-user0/black_box/data/experimental-speed-projection/Qwen3.8-Flash-Next-experimental-speed-projection.gguf:1.0"
# Winning topology
HC_VRAM_RESERVE_MIB=512
HC_PCIE_FRAC=1.0
HC_PLE_IO=direct
HC_KV=q4_0
HC_KV_GROW=0
HC_HOST_CORE=last
HC_POOL_AFFINITY=all
HC_POOL_WORKERS=15
HC_PROMPT_CACHE_TAIL=0
HC_MAX_CONTEXT=262144
HC_MAX_NEW=512
HC_SPEC_MIN_P=0.7
HC_PEAK_TPS=171.31
# Standalone argument string, in the order the engine expects.
HC_ARGS=(
    --pack "/home/ai-agent/HyperCore-data/packs/q2_0"
    --native "/home/ai-agent/HyperCore-data/models/Q2_0/Qwen3.8-Flash-Next-GSQ-RCO-Q2_0-00001-of-00002.gguf"
    --ple-gguf "/home/ai-agent/HyperCore-data/models/Q2_0/Qwen3.8-Flash-Next-GSQ-RCO-Q2_0-00002-of-00002.gguf"
    --expert-profile "/home/ai-user0/black_box/data/expert-profile.bin"
    --expert-cache auto
    --prefill auto
    --spec 4
    --mtp "/home/ai-agent/HyperCore-data/mtp/rt"
    --max-context "262144"
    --kv "q4_0"
    --ple-io "direct"
    --host-core "last"
    --pool-affinity "all"
    --pool-workers "15"
    --control-vector-scaled "/home/ai-user0/black_box/data/experimental-speed-projection/Qwen3.8-Flash-Next-experimental-speed-projection.gguf:1.0"
    --control-vector-layer-range 4 44
    --cvec-mode project
    --cvec-dir per-layer
    --spec-min-p 0.7
    --mmap-experts
    --vram-reserve-mib "512"
    --pcie-frac "1.0"
)
