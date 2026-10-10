"""Decide whether a GGUF can be packed for HyperCore, from the header only.

    python tools/compat_probe.py --gguf <first-shard-or-single-file>

Prints a JSON recipe on success. On refusal, prints one mismatch per line to stderr and exits 2.
Tensor bytes are not read: a truncated download still reports geometry, and a wrong architecture
fails before any pack is written.

The engine contract is qwen4exp at embedding 2560, 48 layers, expert width 640, hyper-connection
4 x 320 (include/hypercore/core/layout.hpp). Expert count may be lower (the Coder). Qwen3-Next-80B-A3B
Thinking and Instruct are qwen3next at hidden size 2048 and are refused.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import iq_pack
from gguf_reader import GGUFFile

N_EMBD = 2560
N_LAYERS = 48
N_FF = 640
HC = 4
HC_LR = 320
HC_DIM = HC * N_EMBD
N_EXPERT_MAX = 512
PLE = "per_layer_token_embd.weight"
DOWN = "ffn_down_exps.weight"
ROUTER = "ffn_gate_inp.weight"
HC_DOWN = "hc_attn_down.weight"

# Named here so a qwen3next header gets this sentence, not a generic arch error alone.
QWEN3_NEXT = (
    "Qwen3-Next-80B-A3B Thinking and Instruct are qwen3next (hidden size 2048, expert intermediate 512). "
    "HyperCore's engine runs qwen4exp only (embedding 2560, expert width 640) and will not load this file."
)


def shard_paths(first: pathlib.Path) -> list[pathlib.Path]:
    """llama.cpp split names, matching tools/iq_pack.py. A single file is one shard."""
    match = re.search(r"-(\d{5})-of-(\d{5})\.gguf$", first.name)
    if not match:
        return [first]
    total = int(match.group(2))
    stem = first.name[: match.start()]
    return [first.with_name(f"{stem}-{i:05d}-of-{total:05d}.gguf") for i in range(1, total + 1)]


def _layer(name: str) -> int | None:
    parts = name.split(".")
    if len(parts) >= 2 and parts[0] == "blk" and parts[1].isdigit():
        return int(parts[1])
    return None


def _meta_int(meta: dict, key: str) -> int | None:
    value = meta.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return int(value)


def inspect(first: pathlib.Path) -> tuple[dict | None, list[str]]:
    """Return (recipe, errors). recipe is None when errors is non-empty."""
    first = pathlib.Path(first)
    errors: list[str] = []
    paths = shard_paths(first)
    loaded: list[tuple[pathlib.Path, GGUFFile]] = []
    for path in paths:
        if not path.is_file():
            errors.append(f"missing model shard {path.name}")
            continue
        try:
            loaded.append((path, GGUFFile(path)))
        except (OSError, ValueError) as exc:
            errors.append(f"{path.name} is not a GGUF header ({exc})")
    if not loaded:
        return None, errors or [f"missing model shard {first.name}"]

    metas = [g.metadata for _, g in loaded]
    arch = next((m.get("general.architecture") for m in metas if m.get("general.architecture")), None)
    embd = _meta_int(metas[0], f"{arch}.embedding_length") if arch else None
    if arch == "qwen3next" or (embd == 2048 and arch != "qwen4exp"):
        errors.append(QWEN3_NEXT)
    if arch != "qwen4exp":
        errors.append(f"architecture is {arch or 'missing'}, the kernels require qwen4exp")
    if embd is not None and embd != N_EMBD:
        errors.append(f"n_embd is {embd}, the kernels require {N_EMBD}")
    block = _meta_int(metas[0], f"{arch}.block_count") if arch else None
    if block is not None and block != N_LAYERS:
        errors.append(f"n_layers is {block}, the kernels require {N_LAYERS}")
    # A wrong architecture has nothing further the packer can use.
    if arch != "qwen4exp":
        return None, errors

    tensors = [(path, t) for path, g in loaded for t in g.tensors]
    by_name = {t.name: (path, t) for path, t in tensors}

    def shape_of(suffix: str, layer: int = 0):
        found = by_name.get(f"blk.{layer}.{suffix}")
        return None if found is None else found[1].shape

    router = shape_of(ROUTER)
    n_expert = None
    if router is None or len(router) < 2:
        errors.append(f"missing blk.0.{ROUTER}")
    else:
        if int(router[0]) != N_EMBD:
            errors.append(f"n_embd is {int(router[0])}, the kernels require {N_EMBD}")
        n_expert = int(router[1])
        if n_expert < 1 or n_expert > N_EXPERT_MAX:
            errors.append(f"n_expert is {n_expert}, the kernels require 1..{N_EXPERT_MAX}")

    down0 = shape_of(DOWN)
    if down0 is None or len(down0) < 1:
        errors.append(f"missing blk.0.{DOWN}")
    elif int(down0[0]) != N_FF:
        errors.append(f"n_ff is {int(down0[0])}, the kernels require {N_FF}")

    hc = shape_of(HC_DOWN)
    if hc is None or len(hc) < 2:
        errors.append(f"missing blk.0.{HC_DOWN} (hyper-connection width)")
    elif [int(hc[0]), int(hc[1])] != [HC_DIM, HC_LR]:
        errors.append(
            f"blk.0.{HC_DOWN} is {int(hc[0])}x{int(hc[1])}, the kernels require {HC_DIM}x{HC_LR}"
        )

    down_layers = sorted(_layer(t.name) for _, t in tensors if t.name.endswith(DOWN) and _layer(t.name) is not None)
    if down_layers != list(range(N_LAYERS)):
        missing = [i for i in range(N_LAYERS) if i not in down_layers]
        if missing:
            shown = ", ".join(str(i) for i in missing[:8])
            extra = "" if len(missing) <= 8 else f" (+{len(missing) - 8} more)"
            errors.append(f"missing expert down tensors for layers {shown}{extra}")
        else:
            errors.append(f"n_layers is {len(down_layers)}, the kernels require {N_LAYERS}")

    if n_expert is not None:
        for layer in range(N_LAYERS):
            got = shape_of(ROUTER, layer)
            if got is None or len(got) < 2:
                continue
            if int(got[1]) != n_expert:
                errors.append(f"blk.{layer}.{ROUTER} has {int(got[1])} experts, layer 0 has {n_expert}")
                break

    down_types: set[str] = set()
    for path, t in tensors:
        if not t.name.endswith(DOWN):
            continue
        down_types.add(t.type_name)
        if t.type_name == "Q5_0":
            errors.append(f"Q5_0 expert down is unsupported ({t.name})")
        elif t.type_name.startswith("type"):
            errors.append(f"unsupported expert type {t.type_name} on {t.name}")

    ple = by_name.get(PLE)
    if ple is None:
        errors.append(f"missing {PLE} (the PLE table)")
        ple_shard = None
    else:
        ple_shard = ple[0].name

    compat = False
    for _, t in tensors:
        if iq_pack.needs_bf16(t.name, t.type_name) and t.type_name != "BF16":
            compat = True
            break

    if errors:
        return None, errors
    return {
        "ok": True,
        "architecture": "qwen4exp",
        "compat_bf16": compat,
        "n_expert": n_expert,
        "n_embd": N_EMBD,
        "n_ff": N_FF,
        "n_layers": N_LAYERS,
        "ple_shard": ple_shard,
        "expert_down_types": sorted(down_types),
    }, []


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gguf", required=True, help="the model's first shard, or its only GGUF")
    args = ap.parse_args(argv)
    recipe, errors = inspect(pathlib.Path(args.gguf))
    if errors:
        for line in errors:
            print(line, file=sys.stderr)
        return 2
    print(json.dumps(recipe, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
