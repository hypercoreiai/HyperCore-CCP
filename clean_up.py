#!/usr/bin/env python3
"""clean_up.py - which folders hold nothing but weights worth deleting?

This is the disk-space tool: the model shards, the pack the packer built and the
draft-head files are re-downloadable, and they are what fills a data folder. Run it
and it prints the folders and how much each one is, and you delete them:

    python3 clean_up.py /path/to/HyperCore-data /path/to/HyperCore

It is a report, not a cleaner, and setup.py does not call it - there is no
`setup.py --clean`. Resetting a working copy is clean.sh (the build trees and the
caches); freeing the weights is this.

The point of a separate module is the rule: a folder is safe to delete only when it
holds model weights or a pack the tool generated, and never when it holds something
the user wrote. Nothing here deletes anything by itself: removal_targets() returns the
paths, and the caller decides. That is why the tests can run against a temporary
directory.
"""
from __future__ import annotations

import sys
from collections.abc import Iterable
from pathlib import Path

# A data folder's weight directories, by name. These are re-downloadable.
DATA_DIRS = ("models", "packs", "mtp")
# Inside the project: an unpacked model release (always named *-gguf) and the pack the
# packer builds. Everything else in the project is source, config or measured data.
ARTIFACT_SUFFIXES = ("-gguf",)
ARTIFACT_NAMES = ("pack",)
# Never a target, whatever it contains: the expert profiles, prompts, and the source.
KEEP_NAMES = {"data", "src", "serve", "tools", "docs", "engine", "build", "bench"}


def _is_artifact(name: str) -> bool:
    return name in ARTIFACT_NAMES or name.endswith(ARTIFACT_SUFFIXES)


def removal_targets(roots: Iterable[Path | str], repo: Path | str) -> list[Path]:
    """The weight folders under `roots`, excluding anything inside the project itself.

    `repo` is the project directory: its source and its data are never returned, and
    the project directory itself is never a target - only a folder inside it.
    """
    repo = Path(repo).resolve()
    targets: list[Path] = []
    for root in (Path(r).resolve() for r in roots):
        if not root.is_dir():
            continue
        if root == repo:
            for child in sorted(root.iterdir()):
                if child.is_dir() and child.name not in KEEP_NAMES and _is_artifact(child.name):
                    targets.append(child)
            continue
        for name in DATA_DIRS:
            child = root / name
            if child.is_dir():
                targets.append(child)
    return targets


def dir_bytes(path: Path | str) -> int:
    """Total size of every file under `path`. A directory with no files is 0."""
    path = Path(path)
    if not path.is_dir():
        return path.stat().st_size if path.is_file() else 0
    total = 0
    for f in path.rglob("*"):
        if f.is_file():
            try:
                total += f.stat().st_size
            except OSError:
                continue
    return total


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: clean_up.py <data-dir> <project-dir>", file=sys.stderr)
        return 2
    targets = removal_targets(argv[:-1], argv[-1])
    if not targets:
        print("nothing to remove")
        return 0
    for t in targets:
        print(f"{dir_bytes(t) / 1e9:>8.2f} GB  {t}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
