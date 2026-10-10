"""tools/kimi_ab.py - does kimi-k3 garble because of the token cap, or the sampling temperature?

Three variants of the same prompt, run in order with a pause between them (the endpoint is throttled):
  A  max_tokens=512, default temperature          <- what the Assist tab does today
  B  max_tokens=512, temperature=0.2
  C  max_tokens=2048, default temperature

Prints finish_reason, token counts and the first 300 characters of each answer, so a garbled reply is
visible rather than inferred. Nothing here writes to the allowlist; it is a measurement, not a change.

Run: .venv/bin/python tools/kimi_ab.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # run it from anywhere
from serve import assist

MODEL = "moonshotai/kimi-k3"
PROMPT = ("Explain in five short bullet points why a MoE model can have a large parameter count "
          "and a small active compute per token.")


def run(label: str, **kwargs) -> dict:
    endpoint, key = assist.load_env()
    payload = {"model": MODEL, "messages": [{"role": "user", "content": PROMPT}], **kwargs}
    started = time.perf_counter()
    try:
        data = assist._request(endpoint, key, "/chat/completions", payload, timeout=60)
    except Exception as exc:
        print(f"--- {label}: FAILED {exc}")
        return {"error": str(exc)}
    choice = (data.get("choices") or [{}])[0]
    text = (choice.get("message") or {}).get("content") or ""
    elapsed = time.perf_counter() - started
    usage = data.get("usage") or {}
    print(f"--- {label}: finish={choice.get('finish_reason')} "
          f"completion_tokens={usage.get('completion_tokens')} chars={len(text)} in {elapsed:.1f}s")
    print(text[:300].replace("\n", " | "))
    print()
    return {"finish": choice.get("finish_reason"), "chars": len(text),
            "tokens": usage.get("completion_tokens")}


def main() -> None:
    results = {}
    for label, kwargs in (
        ("A max_tokens=512 default temp", {"max_tokens": 512}),
        ("B max_tokens=512 temp=0.2", {"max_tokens": 512, "temperature": 0.2}),
        ("C max_tokens=2048 default temp", {"max_tokens": 2048}),
    ):
        results[label] = run(label, **kwargs)
        time.sleep(8)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
