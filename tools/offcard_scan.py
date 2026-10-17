#!/usr/bin/env python3
"""Scan every recorded optuna bench log and report the off-card expert share.

Off-card share = 1 - (hits / lookups) on the engine's own
"decode expert cache hit rate: X% (H hits / L lookups)" line, which is what
optuna_tune/prompt_transfer.py:240-266 (off_card_share) computes.
"""
import glob
import re

HIT = re.compile(r"decode expert cache hit rate: ([0-9.]+)% \((\d+) hits / (\d+) lookups\)")
REQ = re.compile(r"prompt (\d+) tokens = \d+ reused \+ \d+ read in [\d.]+ ms "
                 r"\([\d.]+ tok/s\), (\d+) generated in")


def main() -> None:
    rows = []
    for path in glob.glob("optuna_tune/results/*.log"):
        text = open(path, errors="replace").read()
        hits = HIT.findall(text)
        if not hits:
            continue
        reqs = REQ.findall(text)
        rate, h, l = hits[-1]
        off = 100.0 - float(rate)
        prompt, gen = reqs[-1] if reqs else (None, None)
        rows.append((off, prompt, gen, int(l), int(h), path.split("/")[-1]))
    rows.sort()
    print(f"{len(rows)} log files with counters")
    for off, prompt, gen, l, h, name in rows:
        print(f"  off={off:5.2f}%  prompt={prompt}  gen={gen}  lookups={l}  hits={h}  {name}")


if __name__ == "__main__":
    main()
