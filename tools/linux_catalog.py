"""Extra model families for Linux setup. Windows does not import this module.

A row is another file of the same qwen4exp model HyperCore already runs (embedding 2560, 48 layers,
expert width 640). tools/compat_probe.py checks the header and chooses whether iq_pack.py needs
--compat-bf16. Qwen3-Next-80B-A3B is not a row: the probe refuses it.

Adding another same-architecture quant is a new entry under "quants", with the Hugging Face
filename pattern. Do not point these families at the GSQ-RCO second shard or the AVX-512 Q2_0 packer.
"""
from __future__ import annotations

import pathlib

# Published file sizes (GB). arena_gb for the unvalidated mradermacher quants is the file size
# minus 30 GB for the on-disk PLE table and the small dense tensors. It is an install estimate,
# not a measurement. OrcaRouter IQ3_XXS uses the arena from docs/ORCA.md.
_PLE_AND_DENSE_GB = 30.0


def _estimate(download_gb: float) -> dict:
    arena = round(download_gb - _PLE_AND_DENSE_GB, 1)
    return {"download_gb": download_gb, "arena_gb": arena, "ram_gb": round(arena + 14), "shards": 1,
            "validated": False}


def iq_pack_argv(python: str, gguf, out, compat_bf16: bool, extra: tuple = ()) -> list[str]:
    """The iq_pack.py command for a catalog family. compat-bf16 is the probe's decision."""
    cmd = [str(python), str(pathlib.Path(__file__).resolve().parent / "iq_pack.py"),
           "--gguf", str(gguf), "--out", str(out)]
    if compat_bf16:
        cmd.append("--compat-bf16")
    cmd.extend(extra)
    return cmd


def shard_names(fam: dict, quant: str) -> list[str]:
    """Filenames for one catalog quant. {q} is the quant, {i} the 1-based shard, {n} the count."""
    spec = fam["quants"][quant]
    n = spec["shards"]
    pattern = spec.get("file", fam["file"])
    if "{i}" not in pattern:
        return [pattern.format(q=quant)]
    return [pattern.format(q=quant, i=i, n=n) for i in range(1, n + 1)]


# Keys match setup.py FAMILIES, plus catalog/vision/quants. vision False: no mmproj in the recipe.
CATALOG_FAMILIES = {
    "orca": {
        "title": "OrcaRouter Uncensored",
        "by": "OrcaRouter's abliterated Qwen3.8-Flash-Next",
        "about": "same qwen4exp model; ordinary GGUF, packed with compat-bf16",
        "hf": "https://huggingface.co/orcarouter/Qwen3.8-Flash-Next-Uncensored-GGUF/resolve/e43d00f4e2b8b40b89f75e9adeb1045ac34c8acc/",
        "file": "Qwen3.8-Flash-Next-Uncensored-{q}-0000{i}-of-{n:05d}.gguf",
        "tag": "orca-",
        "name": "orcarouter-qwen3.8-flash-next-uncensored",
        "catalog": True,
        "vision": False,
        "quants": {
            "IQ3_XXS": {
                "about": "3-bit i-quant, the validated OrcaRouter size (docs/ORCA.md)",
                "download_gb": 85.2, "ram_gb": 64, "arena_gb": 49.8, "shards": 2, "validated": True,
            },
        },
    },
    "flashgguf": {
        "title": "Qwen3.8-Flash-Next GGUF",
        "by": "mradermacher's static quants of Qwen/Qwen3.8-Flash-Next",
        "about": "same qwen4exp model as a single GGUF; the probe picks the pack flag",
        "hf": "https://huggingface.co/mradermacher/Qwen3.8-Flash-Next-GGUF/resolve/266483d59c37345026eab1d195777fe06e212815/",
        "file": "Qwen3.8-Flash-Next.{q}.gguf",
        "tag": "flashgguf-",
        "name": "qwen3.8-flash-next",
        "catalog": True,
        "vision": False,
        "quants": {
            "Q2_K": {"about": "2-bit K-quant, one file; size is an estimate until packed", **_estimate(80.5)},
            "Q3_K_S": {"about": "3-bit K-quant, one file; size is an estimate until packed", **_estimate(88.9)},
            "Q3_K_M": {"about": "3-bit K-quant, one file; size is an estimate until packed", **_estimate(94.2)},
            "Q3_K_L": {"about": "3-bit K-quant, one file; size is an estimate until packed", **_estimate(96.8)},
            "IQ4_XS": {"about": "4-bit i-quant, one file; size is an estimate until packed", **_estimate(98.5)},
        },
    },
}
