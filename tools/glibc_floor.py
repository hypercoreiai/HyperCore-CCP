#!/usr/bin/env python3
"""tools/glibc_floor.py - what glibc does this artifact actually require?

A shared object built on one machine can quietly require a newer glibc than the
machine it is shipped to. The requirement is written into the binary: every
undefined reference carries the symbol version the linker resolved it to, e.g.
`sqrtf@GLIBC_2.43`. Nothing in the source says "needs glibc 2.43"; the binary
does, and the first place it surfaces is a link error on the customer's box.

This tool reads the floor straight off the artifact so CI can gate on it.

Run:
    python3 tools/glibc_floor.py build-shared/libhypercore_api.so.0.1.40
    python3 tools/glibc_floor.py --require 2.34 build-shared/libhypercore_api.so.0.1.40
    python3 tools/glibc_floor.py --emit-shims build-shared/libhypercore_api.so.0.1.40

`--require` defaults to CONTRACT_FLOOR below, so a standalone run gates the same way the
build does. `--emit-shims` prints the `__wrap_` shim and the link flag for every reference
above that line, which is what turns "the artifact is too new" into a patch to paste.
"""
from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

# glibc versions are not always two parts: GLIBC_2.2.5 is a real node. Capturing
# only the first two parts would report a 2.2.5 reference as "2.2".
VERSION_RE = re.compile(r"GLIBC_(\d+(?:\.\d+)*)")

# Oldest libc the shipped artifact is allowed to require. This is the same value as
# HYPERCORE_GLIBC_FLOOR in CMakeLists.txt; 2.39 is the Ubuntu 24.04 base image in
# Dockerfile. The tool's default is a mirror of the build-time gate so a standalone
# run cannot disagree with the build.
CONTRACT_FLOOR = "2.39"

# Symbols we can supply ourselves instead of resolving against the host libm.
# (return type, parameters, body) for the shim in src/interface/glibc_compat.c.
# The body must not call the versioned symbol: a wrapper that calls __real_sqrtf
# keeps the very stamp wrapping was meant to remove. GCC lowers these __builtin_
# calls to a single SSE instruction, so the shim is the same code the inlined call
# would have produced.
SHIMS: dict[str, tuple[str, str, str]] = {
    "sqrtf": ("float", "float value", "return __builtin_sqrtf(value);"),
    "sqrt": ("double", "double value", "return __builtin_sqrt(value);"),
    "sqrtl": ("long double", "long double value", "return __builtin_sqrtl(value);"),
    "fabsf": ("float", "float value", "return value < 0.0f ? -value : value;"),
    "fabs": ("double", "double value", "return value < 0.0 ? -value : value;"),
}


def referenced_versions(binary: Path) -> list[tuple[str, str]]:
    """(symbol, glibc_version) for every versioned undefined reference."""
    out = subprocess.run(
        ["objdump", "-T", str(binary)], capture_output=True, text=True, check=False
    )
    if out.returncode != 0:
        raise RuntimeError(f"objdump failed on {binary}: {out.stderr.strip()}")

    found: list[tuple[str, str]] = []
    for line in out.stdout.splitlines():
        # ... DF *UND*  0000  GLIBC_2.43  sqrtf
        if "*UND*" not in line:
            continue
        match = VERSION_RE.search(line)
        if not match:
            continue
        symbol = line.split()[-1]
        found.append((symbol, match.group(1)))
    return found


def parse_version(text: str) -> tuple[int, ...]:
    return tuple(int(part) for part in text.split("."))


def offenders(refs: list[tuple[str, str]], floor: str) -> list[tuple[str, str]]:
    """(symbol, version) for every reference above the allowed floor, newest first.

    Versions are padded to three parts before negating so 2.2.5 and 2.3 compare as
    numbers rather than as tuples of different length.
    """
    limit = parse_version(floor)
    above = {(s, v) for s, v in refs if parse_version(v) > limit}
    return sorted(above, key=lambda pair: tuple(-p for p in parse_version(pair[1]) + (0, 0, 0)[:3]) + (pair[0],))


def shim_block(offending: list[tuple[str, str]]) -> tuple[str, list[str]]:
    """The C shim and the link flags needed to bring the artifact back under the floor.

    Returns (source for src/interface/glibc_compat.c, ["-Wl,--wrap=sqrtf", ...]).
    A symbol with no builtin equivalent still gets the flag and a comment saying so,
    so the build failure names the work instead of leaving the reader to guess.
    """
    sources: list[str] = []
    flags: list[str] = []
    for symbol, version in offending:
        flags.append(f"-Wl,--wrap={symbol}")
        spec = SHIMS.get(symbol)
        if spec is None:
            sources.append(
                f"/* {symbol}@GLIBC_{version}: no builtin equivalent. Implement it locally, "
                f"or drop the call - a wrapper that calls __real_{symbol} keeps the stamp. */"
            )
            continue
        ret, params, body = spec
        sources.append(f"{ret} __wrap_{symbol}({params})\n{{\n    {body}\n}}")
    return "\n\n".join(sources), flags


def main() -> int:
    ap = argparse.ArgumentParser(description="Report the glibc floor of an artifact.")
    ap.add_argument("binary", help="path to the .so or executable")
    ap.add_argument("--require", default=CONTRACT_FLOOR,
                    help=f"fail if the floor exceeds this glibc version (default {CONTRACT_FLOOR})")
    ap.add_argument("--emit-shims", action="store_true",
                    help="print the __wrap_ shim and the link flag for every reference above --require")
    args = ap.parse_args()

    binary = Path(args.binary)
    if not binary.exists():
        print(f"[FAIL] {binary} does not exist")
        return 1

    refs = referenced_versions(binary)
    if not refs:
        print(f"[PASS] {binary.name}: no versioned glibc references")
        return 0

    floor = max((parse_version(v) for _, v in refs))
    floor_text = ".".join(str(part) for part in floor)
    newest = sorted({v for _, v in refs}, key=parse_version)

    above = offenders(refs, args.require)
    if above:
        print(f"[FAIL] {binary.name} requires glibc {floor_text}, the contract allows {args.require}")
        for symbol, version in above:
            print(f"  {symbol}@GLIBC_{version}")
        if args.emit_shims:
            source, flags = shim_block(above)
            print("  fix: add to src/interface/glibc_compat.c")
            for line in source.splitlines():
                print(f"    {line}")
            print("  fix: add to the target's link options")
            for flag in flags:
                print(f"    {flag}")
        return 1

    print(f"[INFO] {binary.name}: glibc floor {floor_text}; versions referenced: {', '.join(newest)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
