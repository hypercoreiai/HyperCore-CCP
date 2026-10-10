#!/usr/bin/env python3
"""tools/assist_latency_probe.py - time every Assist endpoint model and pin the fast ones.

The Assist tab's "External assistant" dropdown is built from serve/assist.py's list_models(), which
honours a pinned allowlist (serve/assist_fast_models.json by default, or HYPERCORE_ASSIST_FAST_LIST).
This probe measures the lag of each model on the cached NVIDIA endpoint and writes that allowlist:
only models whose median time-to-first-token is under --max-lag survive.

    python tools/assist_latency_probe.py                          # probe everything, keep the <1s ones
    python tools/assist_latency_probe.py --rounds 3 --max-lag 0.8
    python tools/assist_latency_probe.py --show                   # print the table, write nothing

The output file is plain JSON and can be edited by hand; the dropdown reads whatever is in it.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from serve import assist


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-lag", type=float, default=assist.DEFAULT_MAX_LAG,
                    help="keep models whose median first-token lag is under this many seconds")
    ap.add_argument("--rounds", type=int, default=2, help="requests per model (median taken)")
    ap.add_argument("--workers", type=int, default=8, help="parallel probes")
    ap.add_argument("--out", default=str(assist.FAST_LIST_PATH), help="allowlist file to write")
    ap.add_argument("--show", action="store_true", help="print the table without writing the allowlist")
    ap.add_argument("--timeout", type=int, default=assist.DEFAULT_TIMEOUT)
    args = ap.parse_args()

    out = None if args.show else args.out
    result = assist.probe_models(max_lag=args.max_lag, rounds=args.rounds,
                                 workers=args.workers, timeout=args.timeout, out=out)

    print(f"{result['fast']} of {result['probed']} model(s) answered under {result['max_lag_s']}s"
          + (f", {result['held']} already pinned kept without a measurement" if result.get("held") else "")
          + (f" -> {result['file']}" if result.get("file") else ""))
    for row in result["models"]:
        if row["ok"]:
            print(f"  {row['id']:55s} {row['ttft_s']:.3f}s  (best {row['best_s']:.3f}, worst {row['worst_s']:.3f})")
        else:
            print(f"  {row['id']:55s} {row.get('reason', 'failed')}: {row['error']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
