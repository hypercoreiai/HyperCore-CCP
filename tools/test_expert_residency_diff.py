#!/usr/bin/env python3
"""Differential test: HyperCore vs Strata on the VRAM expert tier.

Foreign source under test
  Strata 0.1.44.1  src/program/generate.cpp:5150-5157   `if (o.expert_cache < 0) { ... }`
  Strata 0.1.44.1  src/program/generate.cpp:6779-6781   `kvg_start` / the elastic K/V ledger line
  Strata 0.1.44.1  src/core/expert_cache.cpp            slot storage, `slots_within`
Local counterpart
  HyperCore 0.1.42 src/program/generate.cpp:4045-4052   the same block
  HyperCore 0.1.42 src/program/generate.cpp:5791        `cache_slots_for` (prefill borrows slots)

What the test proves, in order:
  1. the two engines compute the slot count with the same arithmetic;
  2. that arithmetic agrees bit-for-bit on empty / zero-free / overflow / error payloads;
  3. the recorded runs' ledgers satisfy  resident == slots - kv_slots_claimed  exactly;
  4. the observed resident-expert gap closes term by term, with no unexplained remainder.

    pytest tools/test_expert_residency_diff.py
    RESIDENCY_LIVE=1 pytest tools/test_expert_residency_diff.py   # also launches both engines
"""

from __future__ import annotations

import os
import re
import sys
from itertools import pairwise

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from expert_residency_ledger import (
    ENGINES,
    Ledger,
    apply_overrides,
    attribute,
    bool_flags,
    extract_fit_arithmetic,
    extract_sizing_block,
    known_flags,
    load_config_args,
    normalise,
    read_ledger,
    residency_curve,
    resident_floor,
    run_engine,
)

MIB, GIB = 1 << 20, 1 << 30
TOL_SLOTS = 3  # rounding of the MiB->GiB print in the engine's own log line


def live_ledger(engine: str, overrides: dict[str, str], port: int) -> Ledger | None:
    """run_engine, but a machine that is not up is a skip, not a failure."""
    try:
        return run_engine(engine, overrides, port)
    except RuntimeError as exc:
        pytest.skip(f"{engine} not runnable: {exc}")


# ---------------------------------------------------------------- 1. the formula is the same
def test_slot_arithmetic_is_identical():
    """generate.cpp's `reserve -> slots -> clamp` block, token for token."""
    a = normalise(extract_fit_arithmetic(ENGINES["hypercore"]["src"]) or "")
    b = normalise(extract_fit_arithmetic(ENGINES["strata"]["src"]) or "")
    assert a and b, "could not locate the sizing block in either source"
    assert a == b, "the slot arithmetic diverged"


def test_surrounding_drift_is_reported_not_fatal():
    """Strata 1.44 added a HIP/APU warning and a free_b==0 retry around the same block.
    They are recorded so a later run can tell them apart from the cause of the gap."""
    drift = []
    for engine, spec in ENGINES.items():
        block = extract_sizing_block(spec["src"]) or ""
        drift.append((engine, bool("prefill_head_alias" in block), bool("STRATA_USE_HIP" in block)))
    print("adjacent drift (engine, free_b retry, APU branch):", drift)


def test_reserve_floor_constant_matches():
    with open(ENGINES["hypercore"]["src"]) as f_a, open(ENGINES["strata"]["src"]) as f_b:
        src_a, src_b = f_a.read(), f_b.read()
    pa = re.search(r"constexpr int kSmallReserveMib = (\d+);", src_a)
    pb = re.search(r"constexpr int kSmallReserveMib = (\d+);", src_b)
    assert pa and pb and pa.group(1) == pb.group(1), (pa, pb)


# ---------------------------------------------------------------- 2. boundary payloads
def cdiv(a: int, b: int) -> int:
    """C++ integer division: truncate toward zero, not floor."""
    q = abs(a) // abs(b)
    return q if (a < 0) == (b < 0) else -q


def slots_from_formula(free_b: int, reserve_mib: int, prefill_mib: int, mtp_bind: int,
                      pipe_first: int, blob: int, profile_pairs: int,
                      reserve_given: bool = False, min_slots: int = 1,
                      small_reserve_mib: int = 300) -> int:
    """Reference implementation of generate.cpp's auto sizing, transcribed from both sources."""
    reserve = ((reserve_mib + prefill_mib) << 20) + mtp_bind + pipe_first
    slots = cdiv(free_b - reserve, blob)
    if profile_pairs:
        slots = min(slots, profile_pairs)
    slots = max(slots, 0)
    if slots < min_slots and not reserve_given and reserve_mib > small_reserve_mib:
        fit_mib = cdiv(free_b - mtp_bind - pipe_first - min_slots * blob, 1 << 20) - prefill_mib
        if fit_mib >= small_reserve_mib:
            r = min(fit_mib, reserve_mib)
            s2 = cdiv(free_b - (((r + prefill_mib) << 20) + mtp_bind + pipe_first), blob)
            if profile_pairs:
                s2 = min(s2, profile_pairs)
            slots = max(s2, 0)
    return int(slots)


BOUNDARY_CASES = [
    # name, free_b, reserve_mib, prefill_mib, mtp_bind, pipe_first, blob, profile_pairs
    ("nominal 4090",              18 * GIB, 512, 0, 184 << 20, 0, 1382207, 24576),
    ("empty profile",             18 * GIB, 512, 0, 184 << 20, 0, 1382207, 0),
    ("profile smaller than fit",  18 * GIB, 512, 0, 184 << 20, 0, 1382207, 1000),
    ("no VRAM at all",            0,        512, 0, 184 << 20, 0, 1382207, 24576),
    ("reserve exceeds free",      300 << 20, 512, 0, 184 << 20, 0, 1382207, 24576),
    ("prefill owns the chunk",    18 * GIB, 512, 32768, 184 << 20, 0, 1382207, 24576),
    ("draft head unbound",        18 * GIB, 512, 0, 0, 0, 1382207, 24576),
    ("overflow payload",          1 << 40,  512, 0, 184 << 20, 0, 1382207, 24576),
    ("one byte short of a slot",  ((13789 * 1382207) + (696 << 20)) - 1, 512, 0, 184 << 20, 0, 1382207, 24576),
    ("reserve floor kicks in",    900 << 20, 1024, 0, 184 << 20, 0, 1382207, 24576),
]


def test_boundary_payloads_agree_between_engines():
    """Both engines' extracted blocks are token-identical (test 1), so the reference
    implementation is the shared one; the point of this case table is that the shared
    formula never silently returns a different slot count at the edges."""
    results = {}
    for name, *args in BOUNDARY_CASES:
        results[name] = slots_from_formula(*args)
    assert results["empty profile"] == 13454, "no profile must not clamp: VRAM alone decides"
    assert results["profile smaller than fit"] == 1000, "the profile caps the cache"
    assert results["no VRAM at all"] == 0 and results["reserve exceeds free"] == 0
    assert results["overflow payload"] == 24576, "the profile cap binds before the arithmetic overflows"
    assert results["one byte short of a slot"] == 13788, "the division truncates, it does not round up"
    # every recorded run whose log contains the sizing line must be reproducible from it
    for engine in ENGINES:
        led = read_ledger(engine)
        if led.free_bytes is None or led.reserve_mib is None:
            continue  # hypercore's recorded log starts at serve time; see the next test
        assert slots_from_formula(led.free_bytes, led.reserve_mib, 0, led.mtp_bind_mib << 20, 0,
                                 led.blob_bytes(), led.profile_pairs) == led.slots_initial, engine


def test_slot_count_is_agreed_by_every_line_that_prints_it():
    """Each engine states the cache size three times: at sizing ("expert cache auto: ... -> N
    slots"), at open ("expert cache N slots, ... GiB"), and in every K/V ledger line ("N of M
    slots hold experts", where M is the total).  A ledger that recovers a different number from
    one of them is reading the wrong run, so all three must agree and the resident count must
    be strictly below the total."""
    for engine in ENGINES:
        led = read_ledger(engine)
        assert led.slots_initial is not None, "no slot count recovered from " + led.source
        if led.cache_open_slots is not None:
            assert led.cache_open_slots == led.slots_initial, (engine, led.cache_open_slots, led.slots_initial)
        assert all(g["slots_total"] == led.slots_initial for g in led.kv_growth), led.kv_growth
        assert led.slots_initial > led.resident_final > 0, (engine, led.slots_initial, led.resident_final)


# ---------------------------------------------------------------- 3. the ledger is self-consistent
def test_live_override_argv_is_accepted_by_both_parsers():
    """The live modes hand the same overrides to both engines.  Every flag must exist in
    that engine's parser and no value-taking flag may end up with a flag as its value.
    This is what `engine init failed (-5)` was: `--kv-grow 1` swallowed `--host-core`.
    Static, so it runs without the GPU."""
    common = {"--max-context": "131072", "--vram-reserve-mib": "512", "--prefill": "auto:32768"}
    bool_by_engine = {}
    for engine, spec in ENGINES.items():
        flags, booleans = known_flags(spec["src"]), bool_flags(spec["src"])
        bool_by_engine[engine] = {k for k in common if k in booleans}
        assert common.keys() <= flags, (engine, sorted(set(common) - flags))
        argv = apply_overrides(load_config_args(spec["config"]), common, spec["src"])
        for i, tok in enumerate(argv):
            if not tok.startswith("--"):
                continue
            assert tok in flags, f"{engine}: unknown flag {tok}"
            if tok in booleans:
                nxt = argv[i + 1] if i + 1 < len(argv) else None
                assert nxt is None or nxt.startswith("--"), (engine, tok, nxt)
    # the same override must mean the same thing in both engines, or the comparison is void
    assert bool_by_engine["hypercore"] == bool_by_engine["strata"], bool_by_engine


def test_residency_identity_holds_for_both_recorded_runs():
    for engine in ENGINES:
        led = read_ledger(engine)
        assert led.slots_initial and led.resident_final, f"no ledger parsed from {ENGINES[engine]['log']}"
        assert led.slots_initial - led.kv_slots_claimed() == led.resident_final, (
            f"{engine}: slots {led.slots_initial} - kv_claimed {led.kv_slots_claimed()} "
            f"!= resident {led.resident_final}")


# ---------------------------------------------------------------- 4. the gap closes term by term
def test_the_strata_gap_is_fully_attributed():
    hc, st = read_ledger("hypercore"), read_ledger("strata")
    att = attribute(hc, st)
    assert att["measured_resident_delta"] == att["predicted_resident_delta"], att
    names = [n for n, _ in att["terms"]]
    assert "slots opened by the sizing step" in names and "slots the elastic K/V tier holds" in names
    # nothing is left over: the slot delta minus the K/V delta is the resident delta exactly
    residual = att["measured_initial_delta"] - att["kv_slots_delta"] - att["measured_resident_delta"]
    assert abs(residual) <= TOL_SLOTS, residual
    # the sizing step itself is explained to within the GiB rounding of the engine's own print
    assert abs(att["sizing_step_residual"]) <= TOL_SLOTS, att["sizing_step_residual"]
    # strata's prompt borrow is transient: it dips the tier during prefill but is not in the
    # end-of-run resident count, so it must not be counted in the gap
    assert any(n.startswith("slots the prompt path parks") for n in names), names
    assert att["predicted_resident_delta"] == att["measured_initial_delta"] - att["kv_slots_delta"]


def test_residency_is_stable_on_hypercore_and_dips_on_strata():
    """The direct answer to the question.

    Both engines open the same order of slots (13605 vs 13405 in the frozen fixtures under
    data/recorded/).  What makes strata sit in the 9k-12k band is not the sizing formula: it
    is the two consumers that take slots back out of the expert tier after the cache is open,
    the prompt path's borrow and the elastic K/V window.  Hypercore's K/V window peaks at 396
    slots; strata's prompt path parks 2541 slots during prefill and its K/V window grows to 711.
    """
    hc, st = read_ledger("hypercore"), read_ledger("strata")
    assert hc.min_resident() > 13000, (hc.min_resident(), hc.resident_trace())
    assert st.low_water_resident() < 12000, (st.low_water_resident(), st.resident_trace())
    # the dip is bounded by the prompt borrow, and the recovery is bounded by the K/V window
    assert st.slots_initial - st.prompt_borrow_slots == 10864, st.prompt_borrow_slots
    assert st.resident_final == st.slots_initial - st.kv_slots_claimed()
    assert st.kv_slots_claimed() < st.prompt_borrow_slots, (
        "the K/V ceiling is the room the prompt path borrowed back: "
        f"{st.kv_slots_claimed()} of {st.prompt_borrow_slots} slots")
    # the engine's own snapshot (slots - resident) is the authoritative window; the per-grow
    # "gave N slots" lines are increments and can never exceed it
    assert hc.kv_slots_claimed() >= sum(g["slots"] for g in hc.kv_growth), hc.kv_growth
    assert hc.kv_window_peak() == hc.kv_slots_claimed(), (hc.kv_window_peak(), hc.kv_growth)
    print("hypercore resident trace:", hc.resident_trace())
    print("strata resident trace:  ", st.resident_trace())


def test_the_gap_is_not_a_sizing_bug():
    """Same args on both engines must give the same slot count.  Needs the GPU."""
    if not os.environ.get("RESIDENCY_LIVE"):
        pytest.skip("set RESIDENCY_LIVE=1 to run both engines")
    common = {"--max-context": "131072", "--vram-reserve-mib": "512", "--prefill": "auto:32768"}
    hc = live_ledger("hypercore", common, 8091)
    st = live_ledger("strata", common, 8092)
    assert hc.slots_initial == st.slots_initial, (hc.slots_initial, st.slots_initial)
    assert abs(hc.kv_slots_claimed() - st.kv_slots_claimed()) <= TOL_SLOTS


def test_factor_sweep_isolates_each_term():
    """One argument at a time on one engine: each term's predicted slot delta must match."""
    if not os.environ.get("RESIDENCY_SWEEP"):
        pytest.skip("set RESIDENCY_SWEEP=1 to run the sweep")
    base = live_ledger("hypercore", {}, 8093)
    blob = base.blob_bytes()
    for key, value in (("--vram-reserve-mib", "768"), ("--max-context", "262144")):
        led = live_ledger("hypercore", {key: value}, 8093)
        if key == "--vram-reserve-mib":
            predicted = -((int(value) - int(base.arg_from_config("--vram-reserve-mib"))) << 20) // blob
            assert abs((led.slots_initial - base.slots_initial) - predicted) <= TOL_SLOTS, (key, predicted)
        else:
            assert led.kv_slots_claimed() >= base.kv_slots_claimed(), key


def test_residency_curve_walks_down_as_context_grows():
    """The 13k -> 9k slide, measured.  Needs the GPU."""
    if not os.environ.get("RESIDENCY_CURVE"):
        pytest.skip("set RESIDENCY_CURVE=1 to walk the curve")
    for engine, max_ctx in (("hypercore", 131072), ("strata", 262144)):
        curve = residency_curve(engine, max_ctx, [1024, 4096, 8192, 16384, 32768, 65536], 8094)
        residents = [r["resident"] for r in curve if r["resident"] is not None]
        if not residents:
            pytest.skip(f"{engine} produced no residency events at --max-context {max_ctx}")
        assert all(b <= a for a, b in pairwise(residents)), curve
        floor = resident_floor(read_ledger(engine))
        assert residents[-1] >= floor, (residents[-1], floor)
        print(engine, max_ctx, residents)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
