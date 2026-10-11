"""Scan the Strata_chats transcripts and print a compact profile of each:
user turns (the actual requests), section headings, and topic-keyword counts.

    python3 tools/scan_chats.py            # profile every file
    python3 tools/scan_chats.py --keys     # only the keyword table
"""
from __future__ import annotations

import argparse
import collections
import re
import sys
from pathlib import Path

CHATS = Path("/home/ai-user0/Strata_chats")

# candidate topics -> the words that show up when a chat is about them
KEYS = {
    "engine_cpp": ["generate.cpp", "expert_cache", "kv cache", "kv-resident", "prefill", "speculative",
                   "MTP", "draft", "rope", "ggml", "gguf", "CUDA", "HIP", "ROCm", "offload", "layer split"],
    "memory_vram": ["VRAM", "vram-reserve", "resident", "expert cache", "RAM", "GB", "OOM", "pinned",
                    "page-locked", "swap"],
    "benchmark_speed": ["tok/s", "benchmark", "bench", "median", "throughput", "latency", "ttft", "speed"],
    "mcp_tools": ["MCP", "mcp.yaml", "server.py", "tools/", "browser_mcp", "playwright", "scrape", "tool call"],
    "web_ui_monitor": ["Monitor", "dropdown", "app.js", "index.html", "CSS", "chat page", "web app", "token"],
    "setup_install": ["setup.sh", "setup.py", "install", "download", "venv", "pip", "apt", "sudo", "Hugging Face",
                      "HF"],
    "model_choice": ["Q2_0", "IQ3", "IQ4", "UD-Q4", "unsloth", "orca", "quant", "mmproj", "vision", "tokenizer"],
    "testing": ["test", "pytest", "unittest", "ruff", "mypy", "assert", "fixture", "mock"],
    "prompting_behaviour": ["system prompt", "agent profile", "thinking", "reasoning", "effort", "turn",
                           "refusal", "censor", "uncensored", "persona"],
    "deployment_ops": ["systemd", "service", "port", "firewall", "docker", "restart", "daemon", "nginx",
                       "proxy", "ssh", "user", "permission", "chmod"],
    "docs_writing": ["README", "docs/", "DETAILS.md", "document", "article", "state of AI", "write", "draft"],
    "hardware": ["RTX 5090", "3090", "GPU", "nvidia-smi", "driver", "PCIe", "CPU", "AVX", "socket"],
    "bugs_diagnosis": ["error", "failed", "crash", "stall", "traceback", "segfault", "hang", "issue #", "fix"],
}


def turns(text: str) -> list[str]:
    """The user's own messages, in order: everything after a '## You' heading."""
    parts = re.split(r"^## You\s*\n", text, flags=re.M)
    out = []
    for part in parts[1:]:
        line = part.strip().split("\n")[0]
        if line:
            out.append(line[:200])
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--keys", action="store_true", help="only the keyword totals across all files")
    ap.add_argument("--limit", type=int, default=0, help="only the first N files")
    a = ap.parse_args()

    files = sorted(p for p in CHATS.iterdir() if p.is_file())
    if a.limit:
        files = files[:a.limit]

    totals: collections.Counter[str] = collections.Counter()
    for p in files:
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            print(f"{p.name}: unreadable ({e})")
            continue
        low = text.lower()
        hits = {k: sum(low.count(w.lower()) for w in words) for k, words in KEYS.items()}
        for k, v in hits.items():
            totals[k] += v
        if a.keys:
            continue
        t = turns(text)
        print(f"=== {p.name}  {p.stat().st_size // 1024} KB  {len(t)} user turns")
        print("    topics: " + ", ".join(f"{k}={v}" for k, v in sorted(hits.items(), key=lambda x: -x[1]) if v))
        for line in t[:4]:
            print("    > " + line)
    if a.keys:
        print("keyword totals across all files:")
        for k, v in totals.most_common():
            print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
