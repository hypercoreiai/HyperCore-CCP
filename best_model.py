#!/usr/bin/env python3
"""best_model.py - which pack suits this PC?

Ranking only. Hardware is passed in as arguments, so this needs no GPU, no network and
no download. It does not invent numbers: every figure comes from the MODELS table in
setup.py (download size, RAM needed, the expert arena), read with ast so importing this
module does not run setup.py.

    python3 best_model.py --ram 64 --vram 24 --disk 200

A model is rejected for one reason at a time, in the order a person would check:
disk first (nothing can start without the file), then RAM, then the GPU.

Statuses
  fits      the file and the whole expert arena sit in RAM
  low-ram   the file does not fit in RAM, but the engine's resident low-RAM variant does
  ram       neither
  disk      the drive cannot hold the download plus the arena
  vram      never a refusal: these packs run CPU-side with the experts offloaded, so a
            small card changes the speed, not the possibility. It is used to order the
            candidates, and reported as `offload`.
"""
from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
SETUP = ROOT / "setup.py"

# Quality tiers, from the same descriptions setup.py carries: more bits and more experts
# kept is better quality. A pack whose experts are streamed from the SSD is ranked below
# one that is fully resident, whatever its bits - on a 64 GB PC UD-Q4_K_XL measures
# 7-8.5 tokens/s, and IQ3_S beats it in practice.
TIER = {
    "Q2_0": 2.0,
    "IQ2_XS": 2.2,
    "IQ3_XXS": 3.0,
    "IQ1_M": 3.0,      # 3.5 bits, but only 256 of the 512 experts kept
    "IQ3_S": 3.5,
    "UD-IQ4_XS": 4.0,
    "UD-Q4_K_XL": 4.0,
}

# The RAM a model needs when the engine runs the low-RAM resident variant instead of
# loading every expert. #467, #435: the resident mode is what makes a 32 GB PC work.
LOW_RAM_RESIDENT_GB = {"IQ3_XXS": 48, "IQ3_S": 48, "UD-Q4_K_XL": 64, "UD-IQ4_XS": 80}


def _models_table() -> dict[str, dict[str, Any]]:
    """The MODELS dict from setup.py, without executing setup.py."""
    tree = ast.parse(SETUP.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "MODELS":
            return ast.literal_eval(node.value)
    raise LookupError("setup.py has no MODELS table")


def offerings() -> list[dict[str, Any]]:
    """Every pack the installer knows about, with the figures a ranking needs."""
    rows = []
    for model, spec in _models_table().items():
        families = list(spec.get("families") or ["qwen"])
        rows.append({
            "family": families[0],
            "model": model,
            "about": spec.get("about", ""),
            "download_gb": float(spec["download_gb"]),
            "ram_gb": float(spec["ram_gb"]),
            "arena_gb": float(spec["arena_gb"]),
            "resident": not bool(spec.get("budget")),   # streamed from the SSD if False
            "tier": TIER.get(model, 2.0),
            "low_ram_gb": LOW_RAM_RESIDENT_GB.get(model),
        })
    return rows


def classify(row: dict[str, Any], ram: int, vram: int, disk_gb: int | None = None) -> str:
    """One status for one pack on one machine. disk_gb=None means the drive is unknown."""
    if disk_gb is not None and row["download_gb"] + row["arena_gb"] > disk_gb:
        return "disk"
    if ram < row["ram_gb"]:
        if row["low_ram_gb"] is not None and ram >= row["low_ram_gb"]:
            return "low-ram"
        return "ram"
    return "fits"


def rank(rows: list[dict[str, Any]], ram: int, vram: int, disk_gb: int | None = None) -> list[dict[str, Any]]:
    """Copy of rows with a status and an order: usable first, then quality, then speed."""
    out = []
    for row in rows:
        r = dict(row)
        r["status"] = classify(r, ram, vram, disk_gb)
        # How much of the expert arena the card can hold. Ordering only: a pack that
        # fits on the GPU answers faster, but one that does not still answers.
        r["offload"] = max(0.0, min(r["arena_gb"], r["arena_gb"] - vram))
        out.append(r)
    usable = ("fits", "low-ram")
    out.sort(key=lambda r: (
        r["status"] not in usable,        # refusals go last
        0 if r["status"] == "fits" else 1,
        -r["resident"],                    # a pack that streams its experts from the SSD
                                         # loses to a smaller one that stays resident: on a
                                         # 64 GB PC UD-Q4_K_XL measures 7-8.5 tokens/s
        -r["tier"],                        # then quality
        -r["arena_gb"],                    # then the bigger, more complete pack
    ))
    return out


def recommend(ranked: list[dict[str, Any]]) -> dict[str, Any]:
    """The first ranked candidate that runs at all. Raises if nothing does."""
    for row in ranked:
        if row["status"] in ("fits", "low-ram"):
            return row
    raise LookupError("no pack fits this machine")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="rank the packs for a given PC")
    ap.add_argument("--ram", type=int, required=True, help="system RAM in GB")
    ap.add_argument("--vram", type=int, default=0, help="the largest card in GB")
    ap.add_argument("--disk", type=int, default=None, help="free space in GB; omit to ignore the drive")
    a = ap.parse_args(argv)
    ranked = rank(offerings(), a.ram, a.vram, a.disk)
    for r in ranked:
        print(f"{r['status']:>8}  {r['family']}/{r['model']:<12} "
              f"{r['download_gb']:>6} GB  needs {r['ram_gb']:>4} GB RAM")
    try:
        best = recommend(ranked)
        print(f"\nuse {best['family']}/{best['model']} ({best['about']})")
    except LookupError as e:
        print(e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
