"""Pull the useful parts out of the chat transcripts under ~/black_box_chats and
~/Strata_chats, grouped by topic.

A chat transcript is mostly reasoning. What is worth keeping is: what the user asked
for, what was decided, what was changed, what was measured, and what is still open.
This script extracts those, tags each line with the topics it belongs to, and writes
one evidence file per topic under data/history/raw/.

    python3 tools/extract_history.py            # write data/history/raw/<topic>.md
    python3 tools/extract_history.py --stats    # only the counts per topic and file
"""
from __future__ import annotations

import argparse
import collections
import re
import sys
import os
from pathlib import Path

# Transcript folders, read in the order given. Override with CHAT_SOURCE (comma
# separated) or --source.
DEFAULT_SOURCES = (Path("/home/ai-user0/black_box_chats"), Path("/home/ai-user0/Strata_chats"))
SOURCES = [Path(p) for p in (os.environ.get("CHAT_SOURCE") or "").split(",") if p.strip()] or list(DEFAULT_SOURCES)
OUT = Path(__file__).resolve().parents[1] / "data" / "history" / "raw"

TOPICS = {
    "engine-internals": [
        "expert cache", "expert_cache", "kv cache", "kv-resident", "kv cache", "prefill", "speculative",
        "draft", "mtp", "rope", "yarn", "ggml", "gguf", "layer split", "layer_split", "offload",
        "ipc", "frame", "worker", "socket", "abi", "wire", "token id", "im_end", "eos", "sampler",
        "top_k", "min_p", "temperature", "control vector", "cvec", "speed projection", "resident experts",
    ],
    "performance-benchmarks": [
        "tok/s", "tokens/s", "benchmark", "bench_", "median", "throughput", "ttft", "latency", "ms",
        "speed", "calibrat", "parity", "lm-eval", "needle",
    ],
    "memory-vram": [
        "vram", "ram", "gb", "mib", "gib", "resident", "pinned", "page-locked", "oom", "swap",
        "reserve", "arena", "blob", "memory",
    ],
    "mcp-tooling": [
        "mcp", "mcp.yaml", "tools/", "browser_mcp", "playwright", "camoufox", "scrape", "docs_mcp",
        "terminal__", "home__", "assist__", "tool call", "tool server", "max_rounds", "stdio", "json-rpc",
    ],
    "web-ui-monitor": [
        "monitor", "index.html", "app.js", "app.css", "dropdown", "agent profile", "system prompt",
        "chat page", "web app", "ui", "card", "spark", "hit rate", "reused", "browser", "theme",
    ],
    "setup-configuration": [
        "setup.sh", "setup.py", "run-", "hypercore-", ".json", "install.sh", "config", "download",
        "venv", "pip", "apt", "sudo", "hugging face", "hf ", "catalog", "quant", "mmproj", "vision",
        "tokenizer", "pack", "api key", "host", "port",
    ],
    "prompting-behaviour": [
        "thinking", "reasoning", "effort", "turn", "refusal", "uncensored", "persona", "system prompt",
        "agent", "instruction", "hallucinat", "stop token", "tail check", "completion check",
    ],
    "testing-quality": [
        "test", "pytest", "unittest", "ruff", "mypy", "pylint", "assert", "fixture", "mock", "golden",
        "coverage", "flake", "lint",
    ],
    "deployment-permissions": [
        "systemd", "service", "daemon", "docker", "restart.sh", "permission", "chmod", "owner",
        "ai-agent", "ai-user0", "user0", "sudo", "ssh", "lan", "192.168", "firewall", "proxy",
        "path", "directory", "file is", "writable",
    ],
    "hardware-environment": [
        "rtx", "5090", "3090", "gpu", "nvidia-smi", "driver", "cuda", "hip", "rocm", "pcie", "cpu",
        "avx", "socket", "amd", "radeon", "display", "xvfb",
    ],
    "issue-log": [
        "error", "failed", "crash", "stall", "traceback", "segfault", "hang", "issue #", "bug",
        "fix", "root cause", "repro", "401", "404", "500", "timeout", "leak",
    ],
    "open-decisions": [
        "todo", "next step", "remaining", "open", "decide", "should", "not done", "pending",
        "recommend", "option", "choice",
    ],
    "general-knowledge": [
        "ollama", "ghidra", "hanbrake", "handbrake", "twitter", "tweet", "video", "state of ai",
        "2026", "paper", "benchmark suite", "question",
    ],
}

# a line is worth keeping when it states something that survives the chat
KEEP = re.compile(
    r"(?i)(fixed|changed|added|removed|implemented|wrote|created|patched|set to|now |default|"
    r"root cause|the reason|because|decision|verified|confirmed|measured|runs|does not|fails|"
    r"must|should|caution|warning|note:|rule|protocol|contract)"
)
NUM = re.compile(r"\d+(\.\d+)?\s*(tok/s|ms|s\b|GB|MiB|GiB|%|k\b)")

# what kind of statement a sentence is; only the first four are worth keeping
KIND = [
    ("fix", r"(?i)\b(fixed|patched|resolved|corrected|replaced|removed the|works now|no longer)"),
    ("decision", r"(?i)\b(decided|chose|set to|default|switched to|renamed|moved to|added |implements|is now)"),
    ("measure", r"(?i)(measured|benchmark|\d+(\.\d+)?\s*(tok/s|ms|gb|mib|gib|%))"),
    ("rule", r"(?i)\b(must|never|always|only when|the contract|the rule|by design|because)"),
    ("question", r"(?i)^(can you|could you|what |why |how |is it|do you|should i)"),
    ("reason", r"(?i)^(i |let me |i need|i should|i will|this seems|it looks|perhaps|maybe)"),
]


def kind_of(s: str) -> str:
    for name, pattern in KIND:
        if re.search(pattern, s):
            return name
    return "other"


def user_turns(text: str) -> list[str]:
    out = []
    for part in re.split(r"^## You\s*\n", text, flags=re.M)[1:]:
        block = part.split("\n\n")[0]
        block = re.sub(r"\s+", " ", block).strip()
        if 15 <= len(block) <= 300:
            out.append(block)
    return out


SKIP = re.compile(
    r"(?i)^(let me|i will|i need|i should|i can|this seems|it looks|perhaps|maybe|first,|next,|"
    r"to understand|there are multiple|i have to|let's|now let|good question|sure,|here is how)"
)


def score(line: str) -> int:
    """How much of this line survives the chat: a number, a file, a decision, a cause."""
    s = 0
    if NUM.search(line):
        s += 3
    if re.search(r"/\w+/\w+|\.py|\.cpp|\.md|\.json|\.sh", line):
        s += 2
    if re.search(r"(?i)\b(fixed|added|changed|removed|implemented|root cause|the reason is|"
                r"must not|never|always|default|contract|rule|protocol)\b", line):
        s += 2
    if re.search(r"(?i)^(note|caution|warning|decision|open|todo|next)", line):
        s += 1
    return s


CONCRETE = re.compile(r"(?i)(`[^`]+`|--[a-z][a-z-]|/[a-z_]+/[a-z_]|\b[a-z_]+\.py|\b[a-z_]+\.(cpp|md|json|sh|hpp|h)|\d+(\.\d+)?\s*(tok/s|ms|gb|mib|gib|%|k tokens|tokens))")


def sentences(text: str) -> list[str]:
    """Sentences from the assistant's turns. Terminal dumps, code and the thinking blocks are left out."""
    out = []
    for block in re.split(r"^## .*\n", text, flags=re.M):
        block = re.sub(r"<details><summary>Thinking</summary>.*?</details>", " ", block, flags=re.S)
        block = re.sub(r"```.*?```", " ", block, flags=re.S)
        for line in block.split("\n"):
            s = line.strip()
            if not s or s.startswith(("#", ">", "|", "$", "[strata]", "[hypercore]", "...", "....", "user0@", "ai-user0@", "Thought for")):
                continue
            if re.search(r"Traceback|File \"|line \d+|ResourceWarning|\.{5,}|\$ |Error 2|not found, did you mean", s):
                continue
            for sent in re.split(r"(?<=[.!?])\s+", s):
                sent = sent.strip()
                k = kind_of(sent)
                if k in ("fix", "decision", "measure", "rule") and 40 <= len(sent) <= 320 \
                        and CONCRETE.search(sent) and score(sent) >= 3:
                    out.append(sent)
    return out


def assistant_facts(text: str) -> list[str]:
    """Assistant sentences that state a result, a cause, or a number - not the reasoning."""
    return sentences(text)


def tag(line: str) -> list[str]:
    low = line.lower()
    return [t for t, words in TOPICS.items() if any(w in low for w in words)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--max-lines", type=int, default=400, help="evidence lines kept per topic")
    a = ap.parse_args()

    per_topic: dict[str, list[tuple[str, str]]] = collections.defaultdict(list)
    file_topics: dict[str, collections.Counter] = {}

    for folder in SOURCES:
        if not folder.is_dir():
            continue
        for p in sorted(folder.iterdir()):
            if not p.is_file() or p.stat().st_size < 500:
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            counts: collections.Counter[str] = collections.Counter()
            lines = user_turns(text) + assistant_facts(text)
            for line in lines:
                for t in tag(line):
                    counts[t] += 1
                    per_topic[t].append((p.name, line))
            file_topics[p.name] = counts

    if a.stats:
        for name, c in sorted(file_topics.items()):
            top = ", ".join(f"{k}={v}" for k, v in c.most_common(5))
            print(f"{name}: {top}")
        print()
        for t, c in sorted(counts_total(per_topic).items(), key=lambda x: -x[1]):
            print(f"{t}: {c} evidence lines")
        return 0

    OUT.mkdir(parents=True, exist_ok=True)
    for topic, items in sorted(per_topic.items()):
        seen = set()
        kept = []
        for src, line in items:
            key = re.sub(r"\s+", " ", line)[:140]
            if key in seen:
                continue
            seen.add(key)
            kept.append((score(line), src, line))
        kept.sort(key=lambda x: -x[0])
        body = "\n".join(f"- {line}  [src: {src}]" for _, src, line in kept[:a.max_lines])
        (OUT / f"{topic}.md").write_text(
            f"# {topic}\n\n{len(items)} candidate lines, {len(seen)} distinct, the {min(len(seen), a.max_lines)} "
            f"most informative kept below. Each entry names the transcript it came from.\n\n{body}\n",
            encoding="utf-8",
        )
    print(f"wrote {len(per_topic)} topic files under {OUT}")
    return 0


def counts_total(per_topic) -> dict[str, int]:
    return {t: len(v) for t, v in per_topic.items()}


if __name__ == "__main__":
    sys.exit(main())
