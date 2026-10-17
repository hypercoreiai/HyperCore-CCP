#!/usr/bin/env python3
"""Differential ledger of the VRAM expert tier: HyperCore vs Strata.

Foreign source under test: Strata 0.1.44, `src/program/generate.cpp` lines 5150-5157
(`if (o.expert_cache < 0) { ... }`) and `src/program/generate.cpp:6779` / `kvg_ensure`
(the elastic K/V that takes cache slots as the context grows).
Local counterpart: HyperCore, `src/program/generate.cpp` lines 4045-4052 and the same
`--kv-grow` path.

Every number in a Ledger comes from a line the engine itself printed to stderr, so the
attribution is measured, not inferred.

    python tools/expert_residency_ledger.py                       # offline: the two recorded runs
    python tools/expert_residency_ledger.py --live                # launch both engines, same args
    python tools/expert_residency_ledger.py --sweep               # one-factor-at-a-time on one engine
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from dataclasses import dataclass, field

MIB = 1 << 20
GIB = 1 << 30

# "log" is a frozen snapshot of a recorded run, copied into data/recorded/ so that a live
# run can never overwrite the evidence the differential tests are built on.  serve/server.py
# sends the engine's stderr to cfg["log"] (serve/server.py:5194, `stderr_log=cfg.get("log")`),
# so a live EngineSession must give the engine its own log path or it clobbers the fixture.
ENGINES = {
    "hypercore": {
        "repo": "/home/ai-user0/black_box",
        "exe": "/home/ai-user0/black_box/engine/hypercore",
        "config": "/home/ai-user0/black_box/max_run_q2_0.json",
        "log": "/home/ai-user0/black_box/data/recorded/hypercore-0.1.42-max_run_q2_0.log",
        "src": "/home/ai-user0/black_box/src/program/generate.cpp",
    },
    "strata": {
        "repo": "/home/ai-user0/Strata_144",
        "exe": "/home/ai-user0/Strata/engine/strata",
        "config": "/home/ai-user0/Strata_144/max_run_q2_0.json",
        "log": "/home/ai-user0/black_box/data/recorded/strata-0.1.44.1-max_run_q2_0.log",
        "src": "/home/ai-user0/Strata_144/src/program/generate.cpp",
    },
}

# Every pattern is anchored on text the engine prints verbatim.
PATTERNS = {
    "version": r"session is up \(engine ([0-9.]+)\)",
    "blob_max_mib": r"native pack: .*largest blob ([0-9.]+) MB",
    "profile_pairs": r"profile [^:]*: (\d+) ranked pairs, built for (\d+) slots",
    "mtp_vram_mib": r"mtp: draft layer loaded, (\d+) MiB of VRAM \(experts (\d+), dense (\d+)\)",
    "cache_auto": (r"expert cache auto: ([0-9.]+) GiB free, (\d+) MiB reserved "
                   r"\(\+(\d+) MiB for the draft head\) -> (\d+) slots"),
    "cache_open": r"expert cache (\d+) slots, ([0-9.]+) GiB of VRAM",
    "prefill_chunk": r"prompt chunk auto: (\d+) tokens, a (\d+)-slot ring",
    "prompt_borrow": r"the prompt path borrows (\d+) CUDA0 cache slots \(([0-9.]+) GiB\)",
    "kv_init": (r"elastic K/V: (\d+) of (\d+) cells in VRAM \(([0-9.]+) of ([0-9.]+) GiB\); "
                r"the expert cache \((\d+) slots\) gives the K/V room below slot (\d+)"),
    "kv_growth": (r"K/V grown to (\d+) cells \(([0-9.]+) GiB\); the expert cache gave (\d+) slots "
                  r"for it, (\d+) hotter experts moved to colder ones' slots \((\d+) of (\d+) slots hold experts\)"),
    "kv_trim": r"K/V trimmed to (\d+) cells; (\d+) slots back to the expert cache",
    "verify_buffers": r"verify: window up to (\d+) tokens, ([0-9.]+) MiB of device buffers",
    "free_at_request": r"serve: (\d+) MiB of VRAM free at the start of this request",
    "hit_rate": r"decode expert cache hit rate: ([0-9.]+)% \((\d+) hits / (\d+) lookups\)",
}


@dataclass
class Ledger:
    engine: str
    source: str
    version: str | None = None
    args: list[str] = field(default_factory=list)
    blob_max_mib: float | None = None
    profile_pairs: int | None = None
    mtp_vram_mib: int | None = None
    free_bytes: int | None = None          # cudaMemGetInfo free at the sizing moment
    reserve_mib: int | None = None         # --vram-reserve-mib as given
    mtp_bind_mib: int | None = None        # the "+N MiB for the draft head" term
    slots_initial: int | None = None
    cache_open_slots: int | None = None   # the "expert cache N slots" line, kept as a cross-check
    cache_bytes: int | None = None
    prompt_borrow_slots: int | None = None
    kv_cells_initial: int | None = None
    kv_cells_max: int | None = None
    kv_room_below_slot: int | None = None
    kv_max_gib: float | None = None
    kv_growth: list[dict] = field(default_factory=list)
    kv_returns: list[int] = field(default_factory=list)   # "N slots back to the expert cache"
    resident_final: int | None = None
    free_at_request_mib: list[int] = field(default_factory=list)
    hit_rates: list[float] = field(default_factory=list)

    # --- derived terms, all in bytes ---
    def reserve_bytes(self) -> int | None:
        if self.reserve_mib is None or self.mtp_bind_mib is None:
            return None
        # generate.cpp: reserve = (vram_reserve_mib + prefill_mib) << 20 + mtp_bind + pipe_first
        return (self.reserve_mib << 20) + (self.mtp_bind_mib << 20)

    def blob_bytes(self) -> int | None:
        """The per-slot size the auto sizing used: (free - reserve) // slots."""
        if self.free_bytes is None or self.slots_initial is None or self.slots_initial == 0:
            return None
        return (self.free_bytes - self.reserve_bytes()) // self.slots_initial

    def kv_slots_claimed(self) -> int:
        """Slots the elastic K/V tier holds at the end of the run.

        Measured from the engine's own snapshot (total slots - slots holding experts), which
        is what generate.cpp computes as `kvg.lo + (xcache.slots() - kvg.top)`.  The sum of
        the per-grow "gave N slots" lines is only the increment: hypercore's tier already
        holds a window before its first logged grow, so the increments alone under-count it.
        """
        if self.kv_growth and self.slots_initial is not None:
            return self.kv_growth[-1]["window"]
        return max(0, sum(g["slots"] for g in self.kv_growth) - sum(self.kv_returns))

    def kv_window_peak(self) -> int:
        """The widest K/V window the tier reached, in slots."""
        return max((g["window"] for g in self.kv_growth), default=0)

    def resident_trace(self) -> list[int]:
        """Every resident-expert count the engine printed, in the order it printed them."""
        return [g["resident"] for g in self.kv_growth]

    def min_resident(self) -> int | None:
        t = self.resident_trace()
        return min(t) if t else None

    def low_water_resident(self) -> int | None:
        """The fewest experts the tier ever held during the run.

        The prompt path parks its buffers in cache slots before the K/V tier starts growing,
        so the deepest dip is `slots - prompt_borrow`; the K/V line confirms it by naming the
        slot below which the K/V may grow.
        """
        cands = [v for v in (self.min_resident(),
                             (self.slots_initial - self.prompt_borrow_slots)
                             if self.slots_initial and self.prompt_borrow_slots else None,
                             self.kv_room_below_slot if self.kv_room_below_slot else None)
                 if v is not None]
        return min(cands) if cands else None

    def kv_window_peak_mib(self) -> float | None:
        blob = self.blob_bytes()
        if blob is None:
            return None
        return self.kv_window_peak() * blob / MIB

    def parse(self, text: str) -> Ledger:
        for name, pat in PATTERNS.items():
            ms = re.findall(pat, text)
            if not ms:
                continue
            # the K/V and hit-rate lines repeat once per request: every one is a data point
            if name in ("kv_growth", "kv_trim", "free_at_request", "hit_rate"):
                groups = [t if isinstance(t, tuple) else (t,) for t in ms]
            else:
                groups = [ms[0] if isinstance(ms[0], tuple) else (ms[0],)]
            for m in groups:
                if name == "version":
                    self.version = m[0]
                elif name == "blob_max_mib":
                    self.blob_max_mib = float(m[0])
                elif name == "profile_pairs":
                    self.profile_pairs = int(m[0])
                elif name == "mtp_vram_mib":
                    self.mtp_vram_mib = int(m[0])
                elif name == "cache_auto":
                    self.free_bytes = round(float(m[0]) * GIB)
                    self.reserve_mib = int(m[1])
                    self.mtp_bind_mib = int(m[2])
                    self.slots_initial = int(m[3])
                elif name == "cache_open":
                    self.cache_open_slots = int(m[0])
                    self.slots_initial = self.slots_initial or int(m[0])
                    self.cache_bytes = round(float(m[1]) * GIB)
                elif name == "prompt_borrow":
                    self.prompt_borrow_slots = int(m[0])
                elif name == "kv_init":
                    self.kv_cells_initial = int(m[0])
                    self.kv_cells_max = int(m[1])
                    self.kv_max_gib = float(m[3])
                    self.kv_room_below_slot = int(m[5])
                elif name == "kv_growth":
                    self.kv_growth.append({"cells": int(m[0]), "gib": float(m[1]),
                                          "slots": int(m[2]), "moved": int(m[3]),
                                          "resident": int(m[4]), "slots_total": int(m[5]),
                                          "window": int(m[5]) - int(m[4])})
                    self.resident_final = int(m[4])
                    # the engine never printed its sizing line in this run (serve mode), but the
                    # K/V ledger line states the cache's total slot count, so recover it from there
                    self.slots_initial = self.slots_initial or int(m[5])
                elif name == "kv_trim":
                    self.kv_returns.append(int(m[1]))
                elif name == "free_at_request":
                    self.free_at_request_mib.append(int(m[0]))
                elif name == "hit_rate":
                    self.hit_rates.append(float(m[0]))
        return self

    def arg_from_config(self, key: str) -> str | None:
        cfg = self.args
        for i, a in enumerate(cfg):
            if a == key and i + 1 < len(cfg):
                return cfg[i + 1]
        return None

    def as_dict(self) -> dict:
        d = {k: v for k, v in self.__dict__.items() if k != "args"}
        d["args"] = self.args
        return d


def load_config_args(path: str) -> list[str]:
    with open(path) as f:
        cfg = json.load(f)
    return list(cfg.get("args", []))


def read_ledger(engine: str) -> Ledger:
    spec = ENGINES[engine]
    text = ""
    if os.path.exists(spec["log"]):
        with open(spec["log"], errors="replace") as f:
            text = f.read()
    led = Ledger(engine=engine, source=spec["log"], args=load_config_args(spec["config"]))
    return led.parse(text)


# ---------------------------------------------------------------- static formula comparison
def extract_sizing_block(src: str) -> str | None:
    """The auto-sizing block, from `if (o.expert_cache < 0) {` to `o.expert_cache = (int) fit;`."""
    with open(src) as f:
        body = f.read()
    start = body.find("if (o.expert_cache < 0) {")
    if start < 0:
        return None
    end = body.find("o.expert_cache = (int) fit;", start)
    if end < 0:
        return None
    return body[start:end + len("o.expert_cache = (int) fit;")]


def extract_fit_arithmetic(src: str) -> str | None:
    """Just the arithmetic that turns free VRAM into a slot count:
    `reserve -> slots -> clamp`, from inside the `if (o.expert_cache < 0)` block."""
    with open(src) as f:
        body = f.read()
    i = body.find("if (o.expert_cache < 0) {")
    if i < 0:
        return None
    j = body.find("const int64_t reserve =", i)
    k = body.find("o.expert_cache = (int) std::max<int64_t>(slots, 0);", i)
    if j < 0 or k < 0:
        return None
    return body[j:k + len("o.expert_cache = (int) std::max<int64_t>(slots, 0);")]


def normalise(block: str) -> list[str]:
    """Strip comments, fold the namespace prefix, and return the arithmetic token stream."""
    block = re.sub(r"//[^\n]*", "", block)
    block = re.sub(r"\b(strata|hypercore)::", "", block)
    block = re.sub(r"\s+", " ", block)
    return re.findall(r"[A-Za-z_][A-Za-z0-9_]*|[0-9]+|[^\sA-Za-z0-9_]+", block)


def formula_diff(a_src: str, b_src: str) -> list[str]:
    ta = normalise(extract_sizing_block(a_src) or "")
    tb = normalise(extract_sizing_block(b_src) or "")
    if ta == tb:
        return []
    # report the first differing window so the drift is locatable
    i = 0
    while i < min(len(ta), len(tb)) and ta[i] == tb[i]:
        i += 1
    ctx_a = " ".join(ta[max(0, i - 12):i + 12])
    ctx_b = " ".join(tb[max(0, i - 12):i + 12])
    return [f"first divergence at token {i}:\n  hypercore: {ctx_a}\n  strata:      {ctx_b}"]


# ---------------------------------------------------------------- live runs
# ---------------------------------------------------------------- argument handling
def known_flags(src: str) -> set[str]:
    """Every flag the engine's own parser recognises, read from generate.cpp."""
    with open(src) as f:
        body = f.read()
    return set(re.findall(r'a == "(--[a-z0-9-]+)"', body))


def bool_flags(src: str) -> set[str]:
    """Flags that take no value: `else if (a == "--kv-grow") o.kv_grow = true;`.
    Feeding one a value makes the parser fall through and the engine exit with init -5."""
    with open(src) as f:
        body = f.read()
    return set(re.findall(r'a == "(--[a-z0-9-]+)"\)\s*o\.[a-z_]+ = (?:true|false);', body))


def apply_overrides(args: list[str], overrides: dict[str, str], src: str) -> list[str]:
    """Merge overrides into the engine's own argv without breaking its parser."""
    flags, booleans = known_flags(src), bool_flags(src)
    out = list(args)
    for key, value in overrides.items():
        if key not in flags:
            raise ValueError(f"{key} is not a flag of this engine; near matches: "
                            + ", ".join(sorted(f for f in flags if key[2:6] in f[2:])))
        if key in booleans:
            want = str(value).lower() not in ("", "0", "false", "off")
            off = "--no-" + key[2:]
            if want:
                if key not in out:
                    out.append(key)
            elif off in flags and off not in out:
                out.append(off)
            continue
        if key in out:
            i = out.index(key)
            if i + 1 < len(out) and not out[i + 1].startswith("--"):
                out[i + 1] = str(value)
            else:
                out.insert(i + 1, str(value))
        else:
            out += [key, str(value)]
    return out


def reachable(port: int, timeout_s: int = 3) -> bool:
    """Is an engine already answering on this port?  Live modes use this to fail
    with a message instead of a wall of 'Connection refused'.  A 401 counts as up: the
    question is whether a process is holding the GPU, not whether we have the API key."""
    import urllib.error
    import urllib.request
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/v1/models", timeout=timeout_s) as r:
            return r.status == 200
    except urllib.error.HTTPError:
        return True
    except OSError:
        return False


class EngineSession:
    """One engine process, several requests.

    Starting an engine is the expensive part (model load, minutes); the residency curve
    must not pay it once per prompt.  run_engine is the one-shot wrapper.
    """

    def __init__(self, engine: str, overrides: dict[str, str], port: int, timeout_s: int = 900):
        spec = ENGINES[engine]
        with open(spec["config"]) as f:
            cfg = json.load(f)
        self.engine, self.port = engine, port
        self.args = apply_overrides(list(cfg.get("args", [])), overrides, spec["src"])
        self.log_path = f"/tmp/residency_{engine}_{port}.log"
        own_port = int(cfg.get("port") or 0)
        if own_port and own_port != port and reachable(own_port):
            raise RuntimeError(
                f"{engine} is already resident on port {own_port} (pid holding the GPU). A second "
                f"instance of the same engine cannot fit in 24 GB, so the run on port {port} will "
                f"fail at init. Stop it, or run the live modes against that server: "
                f"--port {own_port} (the overrides are then ignored).")
        cfg["args"], cfg["exe"], cfg["port"] = self.args, spec["exe"], port
        # serve/server.py routes the engine's stderr to cfg["log"]; pointing it at our own file
        # is what makes a live run readable, and what keeps the recorded fixture intact.
        cfg["log"] = self.log_path
        cfg_path = f"/tmp/residency_{engine}_{port}.json"
        with open(cfg_path, "w") as f:
            json.dump(cfg, f)
        self.log_file = open(self.log_path, "w")  # noqa: SIM115 - held open for the subprocess, closed in close()
        self.proc = subprocess.Popen(
            [sys.executable, f"{spec['repo']}/serve/server.py",
             "--engine", engine, "--config", cfg_path, "--port", str(port)],
            stdout=subprocess.DEVNULL, stderr=self.log_file, cwd=spec["repo"],
        )
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            if self.proc.poll() is not None:
                break
            if reachable(port):
                return
            time.sleep(2)
        if not reachable(port):
            code = self.proc.poll()
            self.close()
            tail = []
            try:
                with open(self.log_path, errors="replace") as f:
                    tail = [l for l in f.read().splitlines() if l.strip()][-6:]
            except OSError:
                pass
            raise RuntimeError(f"{engine} did not come up on port {port}"
                              + (f" (server exit {code})" if code is not None else "")
                              + ": " + ("; ".join(tail) if tail else "no stderr captured"))

    def ask(self, prompt: str, max_tokens: int = 64, timeout_s: int = 900) -> None:
        body = json.dumps({"messages": [{"role": "user", "content": prompt}],
                           "max_tokens": max_tokens, "stream": False}).encode()
        req = urllib.request.Request(f"http://127.0.0.1:{self.port}/v1/chat/completions",
                                    data=body, headers={"Content-Type": "application/json"})
        try:
            urllib.request.urlopen(req, timeout=timeout_s).read()
        except OSError as exc:  # the ledger is what matters, not the reply
            print(f"  request failed: {exc}", file=sys.stderr)

    def ledger(self) -> Ledger:
        with open(self.log_path, errors="replace") as f:
            return Ledger(engine=self.engine, source=self.log_path, args=self.args).parse(f.read())

    def close(self) -> None:
        self.proc.terminate()
        try:
            self.proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            self.proc.kill()
        self.log_file.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def run_engine(engine: str, overrides: dict[str, str], port: int,
               prompt: str = "Explain what an expert cache is in one sentence.",
               max_tokens: int = 64, timeout_s: int = 900) -> Ledger:
    """Start serve/server.py with the engine's own config plus overrides, ask once, stop it."""
    with EngineSession(engine, overrides, port, timeout_s) as s:
        s.ask(prompt, max_tokens)
        return s.ledger()


# ---------------------------------------------------------------- attribution
def residency_curve(engine: str, max_context: int, token_steps: list[int], port: int) -> list[dict]:
    """Feed one engine prompts of increasing length and record the resident count after
    every K/V growth event.  This is the curve that walks 13k down to 9k.

    The engine is started once: model load is minutes, a request is seconds.
    """
    rows = []
    with EngineSession(engine, {"--max-context": str(max_context), "--kv-grow": "on"}, port) as s:
        led = s.ledger()
        rows.append({"prompt_tokens": 0, "resident": led.slots_initial,
                     "kv_cells": led.kv_cells_initial, "slots_taken": 0})
        seen = 0
        for n in token_steps:
            words = ("the quick brown fox jumps over the lazy dog " * (n // 8 + 1)).strip()[:n * 4]
            s.ask(words, max_tokens=8)
            led = s.ledger()
            new = led.kv_growth[seen:]
            seen = len(led.kv_growth)
            if new:
                for g in new:
                    rows.append({"prompt_tokens": n, "resident": g["resident"],
                                "kv_cells": g["cells"], "slots_taken": g["window"]})
            else:
                rows.append({"prompt_tokens": n, "resident": led.resident_final or led.slots_initial,
                            "kv_cells": led.kv_cells_initial, "slots_taken": 0})
    return rows


def attribute(a: Ledger, b: Ledger) -> dict:
    """Why b has fewer resident experts than a, term by term, in slots.

    The engine's own arithmetic is:  slots = min(profile_pairs, (free - reserve) // max_blob)
    and then the elastic K/V tier takes slots as the context grows, so
        resident_experts == slots_initial - kv_slots_claimed
    holds exactly.  Every term below is measured from the engine's stderr.
    """
    if a.slots_initial is None or b.slots_initial is None:
        raise ValueError(
            "cannot attribute a gap: missing ledger for "
            + ", ".join(l.engine for l in (a, b) if l.slots_initial is None)
            + " (check the recorded log paths in ENGINES)")
    blob = a.blob_bytes() or b.blob_bytes()
    terms = []
    if blob and a.free_bytes and b.free_bytes:
        terms.append(("free VRAM at the sizing moment", (b.free_bytes - a.free_bytes) // blob))
    if blob and a.reserve_bytes() and b.reserve_bytes():
        terms.append(("--vram-reserve-mib + draft-head bind", -(b.reserve_bytes() - a.reserve_bytes()) // blob))
    d_slots = (b.slots_initial or 0) - (a.slots_initial or 0)
    terms.append(("slots opened by the sizing step", d_slots))
    if blob and a.free_bytes and b.free_bytes:
        terms.append(("  free VRAM at the sizing moment", (b.free_bytes - a.free_bytes) // blob))
    if blob and a.reserve_bytes() and b.reserve_bytes():
        terms.append(("  --vram-reserve-mib + draft-head bind", -(b.reserve_bytes() - a.reserve_bytes()) // blob))
    sub = [v for n, v in terms if n.startswith("  ")]   # the sizing step's own sub-terms
    residual = d_slots - sum(sub)
    if a.free_bytes is not None and b.free_bytes is not None:
        terms.append(("unexplained in the sizing step", residual))
    d_kv = b.kv_slots_claimed() - a.kv_slots_claimed()
    terms.append(("slots the elastic K/V tier holds", -d_kv))
    d_borrow = (b.prompt_borrow_slots or 0) - (a.prompt_borrow_slots or 0)
    if d_borrow:
        terms.append(("slots the prompt path parks (transient, not in the final count)", -d_borrow))
    ceiling = None
    if blob and a.kv_max_gib and b.kv_max_gib:
        ceiling = {"hypercore": resident_floor(a), "strata": resident_floor(b)}
    return {
        "blob_bytes": blob,
        "terms": terms,
        "measured_initial_delta": d_slots,
        "kv_slots_delta": d_kv,
        "low_water_resident": {"hypercore": a.low_water_resident(), "strata": b.low_water_resident()},
        "measured_resident_delta": (b.resident_final or 0) - (a.resident_final or 0),
        "predicted_resident_delta": d_slots - d_kv,
        "sizing_step_residual": residual,
        "resident_floor_if_context_maxes_out": ceiling,
    }


def resident_floor(led: Ledger) -> int | None:
    """Experts still in the VRAM tier once the elastic K/V has grown to --max-context."""
    blob = led.blob_bytes()
    if not blob or led.slots_initial is None or led.kv_max_gib is None:
        return None
    return led.slots_initial - int(led.kv_max_gib * GIB / blob)


def table(a: Ledger, b: Ledger) -> str:
    rows = [
        ("engine version", a.version, b.version),
        ("--max-context", a.arg_from_config("--max-context"), b.arg_from_config("--max-context")),
        ("--vram-reserve-mib", a.arg_from_config("--vram-reserve-mib"), b.arg_from_config("--vram-reserve-mib")),
        ("--prefill", a.arg_from_config("--prefill"), b.arg_from_config("--prefill")),
        ("free VRAM at sizing (MiB)", (a.free_bytes or 0) // MIB, (b.free_bytes or 0) // MIB),
        ("reserve incl. draft head (MiB)", (a.reserve_bytes() or 0) // MIB, (b.reserve_bytes() or 0) // MIB),
        ("slots opened", a.slots_initial, b.slots_initial),
        ("bytes per slot", a.blob_bytes(), b.blob_bytes()),
        ("prompt path borrows (slots)", a.prompt_borrow_slots, b.prompt_borrow_slots),
        ("K/V cells ceiling", a.kv_cells_max, b.kv_cells_max),
        ("K/V slots held (measured)", a.kv_slots_claimed(), b.kv_slots_claimed()),
        ("K/V slots peak window", a.kv_window_peak(), b.kv_window_peak()),
        ("K/V slots from grow lines only", sum(g["slots"] for g in a.kv_growth),
         sum(g["slots"] for g in b.kv_growth)),
        ("experts resident at the end", a.resident_final, b.resident_final),
        ("experts resident during prefill", (a.slots_initial - a.prompt_borrow_slots) if a.slots_initial and a.prompt_borrow_slots is not None else None,
         (b.slots_initial - b.prompt_borrow_slots) if b.slots_initial and b.prompt_borrow_slots is not None else None),
        ("resident floor if context maxes out", resident_floor(a), resident_floor(b)),
        ("lowest free VRAM during a request (MiB)", min(a.free_at_request_mib) if a.free_at_request_mib else None,
         min(b.free_at_request_mib) if b.free_at_request_mib else None),
        ("decode cache hit rate (%)", max(a.hit_rates) if a.hit_rates else None,
         max(b.hit_rates) if b.hit_rates else None),
    ]
    w = max(len(r[0]) for r in rows)
    lines = [f"{'term'.ljust(w)}  {'hypercore':>14}  {'strata':>14}"]
    lines.append("-" * (w + 31))
    for name, x, y in rows:
        xs = "-" if x is None else str(x)
        ys = "-" if y is None else str(y)
        lines.append(f"{name.ljust(w)}  {xs:>14}  {ys:>14}")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--live", action="store_true", help="run both engines with identical args")
    ap.add_argument("--sweep", action="store_true", help="one-factor-at-a-time on one engine")
    ap.add_argument("--curve", action="store_true", help="walk the resident count down with context length")
    ap.add_argument("--json", action="store_true", help="emit the ledgers as JSON")
    ap.add_argument("--engine", default="hypercore", choices=list(ENGINES))
    ap.add_argument("--port", type=int, default=8091)
    ap.add_argument("--max-context", type=int, default=262144)
    ap.add_argument("--prompt", default="Explain what an expert cache is in one sentence.")
    args = ap.parse_args()

    if args.curve:
        for engine in ("hypercore", "strata"):
            print(f"\nresident-expert curve, {engine}")
            try:
                curve = residency_curve(engine, args.max_context,
                                       [1024, 4096, 8192, 16384, 32768, 65536], args.port)
            except RuntimeError as exc:
                print(f"  {exc}")
                print(f"  start it with: {ENGINES[engine]['repo']}/serve/server.py "
                      f"--engine {engine} --config {ENGINES[engine]['config']} --port {args.port}")
                continue
            for row in curve:
                if row["resident"] is None:
                    continue
                kv = row["kv_cells"] if row["kv_cells"] is not None else "-"
                print(f"  prompt {row['prompt_tokens']:>6} tok  kv {kv:>7} cells  "
                      f"slots taken {row.get('slots_taken') or 0:>5}  resident {row['resident']:>6}")
        return 0

    if args.live:
        common = {"--max-context": "131072", "--vram-reserve-mib": "512", "--prefill": "auto:32768"}
        a = run_engine("hypercore", common, args.port)
        b = run_engine("strata", common, args.port + 1)
    else:
        a, b = read_ledger("hypercore"), read_ledger("strata")

    if args.json:
        print(json.dumps({"hypercore": a.as_dict(), "strata": b.as_dict()}, indent=2))
        return 0

    print(table(a, b))
    print()
    att = attribute(a, b)
    print("attribution of the resident-expert gap (strata - hypercore), in slots:")
    for name, delta in att["terms"]:
        print(f"  {name:<48} {delta:>8} slots  ({delta * (att['blob_bytes'] or 0) / MIB:>8.1f} MiB)")
    print(f"  measured initial slot delta:     {att['measured_initial_delta']}")
    print(f"  measured resident delta:         {att['measured_resident_delta']}")
    print(f"  predicted resident delta:        {att['predicted_resident_delta']}")
    low = att["low_water_resident"]
    print(f"  lowest resident count in the run: hypercore {low['hypercore']}, strata {low['strata']} "
          f"(the strata dip is the prompt path parking {b.prompt_borrow_slots} slots, returned after prefill)")
    for led in (a, b):
        if led.slots_initial is None:
            print(f"  identity check: no ledger parsed from {led.source} "
                  f"(the engine never printed an 'expert cache auto' line in that run)")
            break
    else:
        print(f"  identity check (slots - kv_claimed == resident): "
              f"{a.slots_initial - a.kv_slots_claimed()} vs {a.resident_final} (hypercore), "
              f"{b.slots_initial - b.kv_slots_claimed()} vs {b.resident_final} (strata)")
    floor = att["resident_floor_if_context_maxes_out"]
    if floor:
        print(f"  resident floor if the K/V tier reaches --max-context: hypercore {floor['hypercore']}, strata {floor['strata']}")

    if args.sweep:
        print("\none-factor-at-a-time sweep on", args.engine)
        base = run_engine(args.engine, {}, args.port)
        for key, value in (("--vram-reserve-mib", "768"), ("--max-context", "262144"),
                          ("--prefill", "auto"), ("--kv-grow", "0")):
            led = run_engine(args.engine, {key: value}, args.port)
            print(f"  {key}={value}: slots={led.slots_initial} kv_claimed={led.kv_slots_claimed()} "
                  f"resident={led.resident_final}  (base {base.slots_initial}/{base.resident_final})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

