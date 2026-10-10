#!/usr/bin/env python3
"""tools/check_abi_alignment.py - the build-time contract lock.

One source of truth: include/hypercore/hypercore_api.h. Everything else - the
Python `struct.Struct` mirrors in serve/ipc_parser.py, the C `static_assert`s, the
worker's frame writer - is a copy. Copies drift, and a drifted byte offset does not
crash: it feeds the wrong number into the compute kernels and the model produces
plausible-looking garbage.

This script parses the packed structs out of the header, derives their offsets, and
asserts the Python mirrors agree field by field. Run it from CI or from the CMake
target `hypercore_abi_alignment_check`, which hypercore_api depends on.

Exit codes: 0 = contract holds, 1 = drift found, 2 = the checker itself could not
run (missing header, unparsable struct).

Usage:
    python3 tools/check_abi_alignment.py
    python3 tools/check_abi_alignment.py --json
    python3 tools/check_abi_alignment.py --header path/to/hypercore_api.h
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

# Type -> byte width under `#pragma pack(push, 1)`. Any type not in this table is
# an error, not a silent skip: a new field whose type we do not understand is exactly
# the drift this tool exists to catch.
FIELD_WIDTHS: dict[str, int] = {
    "uint8_t": 1, "int8_t": 1, "bool": 1,
    "uint16_t": 2, "int16_t": 2,
    "uint32_t": 4, "int32_t": 4, "float": 4,
    "uint64_t": 8, "int64_t": 8, "double": 8,
    "size_t": 8,
}

# Structs that must agree, as (C name, python mirror object, note).
# The summary is not mirrored one-to-one: the wire prefixes it with the
# prompt_reused count, so the comparison is against the tail of TERMINAL_WIRE.
CONTRACTS: tuple[tuple[str, str, int], ...] = (
    ("hypercore_request_config_t", "CFG", 0),
    ("hypercore_caps_t", "CAPS_REPLY", 0),
    ("hypercore_request_summary_t", "TERMINAL_WIRE", 4),
)

FORMAT_WIDTHS = {"c": 1, "B": 1, "h": 2, "H": 2, "i": 4, "I": 4, "f": 4,
                "q": 8, "Q": 8, "d": 8, "?": 1}

STRUCT_RE = re.compile(
    r"typedef struct\s+(\w+)\s*\{(.*?)\}\s*\1;", re.DOTALL
)
FIELD_RE = re.compile(
    r"^\s*([A-Za-z_][A-Za-z0-9_ \*]*?)\s+([A-Za-z_][A-Za-z0-9_]*)(?:\[(\d+)\])?\s*$"
)
COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
ASSERT_RE = re.compile(r"static_assert\(\s*sizeof\((\w+)\)\s*==\s*(\d+)")


def strip_comments(text: str) -> str:
    return COMMENT_RE.sub("", text)


ENUM_TYPEDEF_RE = re.compile(r"typedef\s+enum[^;]*?\}\s*(\w+)\s*;", re.DOTALL)


def enum_typedefs(header: str) -> set[str]:
    """Header-declared enum typedefs are 4-byte int enums on every target this
    project builds for. Discovering them beats hard-coding their names: a new enum
    in the contract is picked up automatically."""
    return set(ENUM_TYPEDEF_RE.findall(header))


def field_width(c_type: str, enums: set[str]) -> int:
    """Byte width of a C type inside a packed struct. Raises on anything unknown.

    A pointer is 8 bytes and is allowed in a struct that never crosses the wire (the
    callback chunk does not); check_contract rejects one in a mirrored struct.
    """
    c_type = c_type.strip()
    if "*" in c_type:
        return 8
    # enum typedefs declared in the header are 4-byte int enums on every target
    # this project builds for; treat any header-declared enum as 4.
    if c_type in enums:
        return 4
    if c_type in FIELD_WIDTHS:
        return FIELD_WIDTHS[c_type]
    raise ValueError(f"unrecognised field type {c_type!r}")


def parse_packed_structs(header: str) -> dict[str, list[dict[str, Any]]]:
    """Return {struct_name: [{name, type, offset, size}, ...]} for every typedef struct."""
    structs: dict[str, list[dict[str, Any]]] = {}
    enums = enum_typedefs(header)
    for name, body in STRUCT_RE.findall(header):
        fields: list[dict[str, Any]] = []
        offset = 0
        for raw in strip_comments(body).split(";"):
            raw = raw.strip()
            if not raw:
                continue
            match = FIELD_RE.match(raw)
            if not match:
                raise ValueError(f"cannot parse field {raw!r} in struct {name}")
            c_type, field_name, array_len = match.group(1), match.group(2), match.group(3)
            width = field_width(c_type, enums)
            if array_len:
                width *= int(array_len)
            fields.append({"name": field_name, "type": c_type, "offset": offset, "size": width})
            offset += width
        structs[name] = fields
    return structs


def format_sizes(fmt: str) -> list[int]:
    """Sizes of each field in a standard-layout struct format string."""
    if not fmt.startswith("<"):
        raise ValueError(f"format {fmt!r} is not little-endian standard layout")
    sizes: list[int] = []
    i = 1
    while i < len(fmt):
        count = 0
        while i < len(fmt) and fmt[i].isdigit():
            count = count * 10 + int(fmt[i])
            i += 1
        code = fmt[i]
        if code not in FORMAT_WIDTHS:
            raise ValueError(f"unsupported format character {code!r} in {fmt!r}")
        sizes.extend([FORMAT_WIDTHS[code]] * (count or 1))
        i += 1
    return sizes


def check_contract(c_name: str, mirror, prefix: int, structs: dict[str, list[dict[str, Any]]]) -> list[str]:
    """Compare a C struct's derived layout against a Python struct mirror."""
    problems: list[str] = []
    if c_name not in structs:
        return [f"{c_name}: not found in the header"]
    fields = structs[c_name]
    pointer_fields = [f for f in fields if "*" in f["type"]]
    if pointer_fields:
        names = ", ".join(f["name"] for f in pointer_fields)
        return [f"{c_name}: {names} is a pointer; the wire cannot carry one"]
    c_sizes = [f["size"] for f in fields]
    py_sizes = format_sizes(mirror.format)
    # `prefix` is a byte count (the wire frames the summary with a 4-byte reuse
    # count), so drop whole leading fields until those bytes are accounted for.
    skipped = 0
    tail = py_sizes
    for i, size in enumerate(py_sizes):
        if skipped == prefix:
            tail = py_sizes[i:]
            break
        skipped += size
        if skipped > prefix:
            msg = f"{c_name}: {prefix}-byte framing does not fall on a field boundary in {mirror.format!r}"
            return [msg]
    else:
        tail = []
    if tail != c_sizes:
        problems.append(
            f"{c_name}: field layout differs\n"
            f"    header: {[(f['name'], f['size']) for f in fields]}\n"
            f"    python: {tail}"
        )
        return problems
    for field, offset in zip(fields, [sum(c_sizes[:i]) for i in range(len(c_sizes))]):
        if field["offset"] != offset:
            problems.append(f"{c_name}: {field['name']} offset {field['offset']} != {offset}")
    declared = mirror.size
    actual = prefix + sum(c_sizes)
    if declared != actual:
        problems.append(f"{c_name}: mirror is {declared} bytes, header implies {actual}")
    return problems


# The request config is the only struct that crosses the socket on every request, and
# the compute kernels read it by byte position. These offsets are the frozen contract:
# a field inserted above top_k shifts every field after it and the kernel reads a
# float where an int belongs. Pinned as absolute numbers so drift is reported as a
# named field rather than as a size mismatch.
HOT_PATH_CONFIG = "hypercore_request_config_t"
HOT_PATH_CONFIG_OFFSETS: dict[str, int] = {
    "struct_size": 0,      # uint32
    "temperature": 4,      # float
    "top_p": 8,            # float
    "top_k": 12,           # uint32
    "max_new_tokens": 16,  # uint32
    "pcie_frac": 20,       # float
    "spec_min_p": 24,      # float
}
HOT_PATH_CONFIG_BYTES = 28


def verify_request_config_alignment(
    structs: dict[str, list[dict[str, Any]]]
) -> list[str]:
    """Assert the hot-path request config has not shifted byte boundaries.

    Offsets come from the parsed header (comments stripped, widths taken from the type
    names), not from a hand-split of the struct text: every field carries an inline
    `/* >= 0 */` annotation, and splitting on ';' turns those into phantom fields. It
    also rejects a field that is not 4 bytes, which is what makes the whole layout
    packable under `#pragma pack(push, 1)`.
    """
    fields = structs.get(HOT_PATH_CONFIG)
    if not fields:
        return [f"{HOT_PATH_CONFIG}: not found in the header, cannot verify offsets"]

    problems: list[str] = []
    parsed = {f["name"]: f for f in fields}

    missing = sorted(set(HOT_PATH_CONFIG_OFFSETS) - set(parsed))
    if missing:
        problems.append(
            f"{HOT_PATH_CONFIG}: fields removed from the hot path: {', '.join(missing)}"
        )
    extra = sorted(set(parsed) - set(HOT_PATH_CONFIG_OFFSETS))
    if extra:
        problems.append(
            f"{HOT_PATH_CONFIG}: fields added to the hot path: {', '.join(extra)}"
        )

    for name, expected in HOT_PATH_CONFIG_OFFSETS.items():
        field = parsed.get(name)
        if field is None:
            continue
        if field["offset"] != expected:
            problems.append(
                f"{HOT_PATH_CONFIG}: {name} sits at byte {field['offset']}, "
                f"the contract says {expected}"
            )
        if field["size"] != 4:
            problems.append(
                f"{HOT_PATH_CONFIG}: {name} is {field['size']} bytes; every field in "
                f"the hot path is 4 bytes by contract"
            )

    total = sum(f["size"] for f in fields)
    if total != HOT_PATH_CONFIG_BYTES:
        problems.append(
            f"{HOT_PATH_CONFIG}: {total} bytes, the contract says {HOT_PATH_CONFIG_BYTES}"
        )
    return problems


def check_self_asserts(header: str, structs: dict[str, list[dict[str, Any]]]) -> list[str]:
    """The header asserts its own sizes; those assertions must match the parse."""
    problems = []
    for name, declared in ASSERT_RE.findall(header):
        if name in structs:
            derived = sum(f["size"] for f in structs[name])
            if derived != int(declared):
                problems.append(f"{name}: static_assert says {declared}, parse says {derived}")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description="Lock the C/Python wire layout together.")
    ap.add_argument("--header", default=None, help="path to hypercore_api.h")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--quiet", action="store_true", help="print only on failure")
    args = ap.parse_args()

    root = Path(__file__).resolve().parents[1]
    header_path = Path(args.header) if args.header else root / "include/hypercore/hypercore_api.h"
    if not header_path.exists():
        print(f"[FAIL] contract header not found: {header_path}", file=sys.stderr)
        return 2

    header = header_path.read_text()
    try:
        structs = parse_packed_structs(header)
    except ValueError as e:
        print(f"[FAIL] could not parse the header: {e}", file=sys.stderr)
        return 2

    sys.path.insert(0, str(root))
    try:
        from serve import ipc_parser
    except ImportError as e:
        print(f"[FAIL] could not import serve.ipc_parser: {e}", file=sys.stderr)
        return 2

    problems: list[str] = []
    report: dict[str, Any] = {"header": str(header_path), "structs": {}}
    for c_name, mirror_name, prefix in CONTRACTS:
        mirror = getattr(ipc_parser, mirror_name, None)
        if mirror is None:
            problems.append(f"{c_name}: no Python mirror named {mirror_name}")
            continue
        problems.extend(check_contract(c_name, mirror, prefix, structs))
        report["structs"][c_name] = {
            "fields": [{"name": f["name"], "offset": f["offset"], "size": f["size"]} for f in structs.get(c_name, [])],
            "bytes": sum(f["size"] for f in structs.get(c_name, [])),
            "mirror": mirror_name,
            "mirror_bytes": mirror.size,
        }

    problems.extend(check_self_asserts(header, structs))

    hot_path = verify_request_config_alignment(structs)
    problems.extend(hot_path)
    report["hot_path_config"] = {
        "struct": HOT_PATH_CONFIG,
        "bytes": HOT_PATH_CONFIG_BYTES,
        "offsets": HOT_PATH_CONFIG_OFFSETS,
        "ok": not hot_path,
    }

    if args.json:
        print(json.dumps({"ok": not problems, "problems": problems, **report}, indent=2))
    elif problems:
        print("[FAIL] wire contract drift detected:")
        for problem in problems:
            print("  " + problem)
        return 1
    elif not args.quiet:
        for name, info in report["structs"].items():
            print(f"[PASS] {name}: {info['bytes']} bytes == {info['mirror']} ({info['mirror_bytes']} with framing)")
        locked = ", ".join(f"{n}@{o}" for n, o in HOT_PATH_CONFIG_OFFSETS.items())
        print(f"[PASS] {HOT_PATH_CONFIG}: {HOT_PATH_CONFIG_BYTES} bytes, hot-path offsets locked ({locked})")
        print("[PASS] header, worker and Python mirrors agree field by field")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
