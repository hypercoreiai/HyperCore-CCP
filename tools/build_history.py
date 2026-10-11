"""Build the accumulated development state under data/history/ from the chat transcripts.

Two views of the same extraction:

  topics/<topic>.md        every fact, decision, measurement, warning and open item about a
                         topic, grouped by the thing it is about (newest statement first), each
                         dated and attributed
  chats/<date>-<name>.md  what one transcript asked for and what came of it
  index.json              the machine-readable version of both
  sources.md              the reverse index: which transcript contributed to which topic

    python3 tools/build_history.py            # rebuild
    python3 tools/build_history.py --topics   # just the topic counts

Re-running is safe: the transcripts are the source of truth and the files are regenerated from
them. A hand-written note in topics/<topic>.notes.md is left alone.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

CHATS = Path("/home/ai-user0/Strata_chats")
HIST = Path(__file__).resolve().parents[1] / "data" / "history"

# ---------------------------------------------------------------- the categories
TOPICS = {
    "engine-internals": (
        "Engine internals",
        {"expert cache": 3, "expert_cache": 3, "expert tier": 3, "kv cache": 3, "kv-resident": 3,
         "prefill": 3, "prefill_ms": 4, "decode_ms": 3, "speculative": 3, "draft": 2, "mtp": 3,
         "rope": 3, "yarn": 2, "ggml": 3, "gguf": 2, "layer split": 3, "offload": 2, "ipc": 3,
         "abi": 3, "im_end": 3, "eos": 2, "sampler": 3, "top_k": 2, "min_p": 2, "control vector": 3,
         "cvec": 3, "speed projection": 3, "resident experts": 3, "pool_workers": 3, "pcie_frac": 3,
         "stop token": 3, "batch slot": 3, "terminal frame": 4, "worker": 2, "frame": 2},
    ),
    "performance-benchmarks": (
        "Performance and benchmarks",
        {"tok/s": 3, "tokens/s": 3, "benchmark": 3, "bench_": 3, "median": 2, "throughput": 3,
         "ttft": 3, "latency": 2, "calibrat": 3, "parity": 3, "lm-eval": 3, "needle": 3,
         "speed up": 2, "ms ": 2, "seconds": 2},
    ),
    "memory-vram": (
        "Memory, VRAM and RAM",
        {"vram": 3, "mib": 2, "gib": 2, "pinned": 3, "page-locked": 3, "oom": 3, "reserve": 2,
         "arena": 3, "blob": 3, "swap": 2, "free memory": 3, "vram-reserve": 4, "resident experts": 3,
         "expert profile": 3, "ram": 2, "memory": 2},
    ),
    "mcp-tooling": (
        "MCP servers and tools",
        {"mcp.yaml": 4, "browser_mcp": 4, "playwright": 4, "camoufox": 4, "invisible_playwright": 4,
         "scrape": 3, "docs_mcp": 4, "terminal__": 4, "home__": 4, "assist__": 4, "tool server": 4,
         "max_rounds": 4, "json-rpc": 4, "stdio": 3, "tool call": 2, "condense": 3, "mcp_servers": 4,
         "serve/mcp": 4, "rag.sqlite": 4, "reindex": 4, "mcp": 2},
    ),
    "web-ui-monitor": (
        "The web app and the Monitor",
        {"monitor": 3, "index.html": 4, "app.js": 4, "app.css": 4, "dropdown": 4, "agent profile": 4,
         "system prompt": 3, "chat page": 3, "sse": 3, "spark": 3, "hit rate": 4, "reused": 4,
         "theme": 3, "context cap": 4, "prompt.json": 4, "agent-select": 4, "api-monitor": 4,
         "card": 2, "tok/s": 3},
    ),
    "setup-configuration": (
        "Setup, run configs and defaults",
        {"setup.sh": 4, "setup.py": 4, "run-q2_0": 4, "run-": 3, "install.sh": 4, "venv": 3,
         "hugging face": 3, "catalog": 3, "quant": 3, "mmproj": 4, "vision encoder": 4,
         "tokenizer": 3, "api key": 4, "api_key": 4, "hypercore-q2_0.json": 4, "run config": 4,
         "turn_tail_check": 4, "host 0.0.0.0": 4, "max-context": 3, "rope-scale": 3, "default": 2},
    ),
    "prompting-behaviour": (
        "Prompting, agents and turn behaviour",
        {"reasoning": 3, "effort": 3, "refusal": 3, "uncensored": 4, "persona": 4,
         "system prompt": 3, "agent prompt": 4, "hallucinat": 3, "tail check": 4, "turn-tail": 4,
         "completion check": 4, "cjk": 3, "thinking budget": 4, "reasoning_budget_tokens": 4,
         "thinking block": 3, "chat_template": 4},
    ),
    "testing-quality": (
        "Testing and code quality",
        {"unittest": 4, "pytest": 4, "ruff": 4, "mypy": 4, "pylint": 4, "fixture": 4, "mock": 3,
         "golden": 4, "coverage": 3, "test_prompts": 4, "test_server": 4, "contract test": 4,
         "subtest": 3, "scriptedworker": 4, "test_mcp": 4, "test_setup": 4, "abi_contract": 4},
    ),
    "deployment-permissions": (
        "Deployment, paths and permissions",
        {"systemd": 4, "daemon": 4, "docker": 4, "restart.sh": 4, "permission": 3, "chmod": 4,
         "owner": 3, "ai-agent": 3, "ai-user0": 3, "sudo": 3, "ssh": 4, "lan": 4, "192.168": 4,
         "firewall": 4, "proxy": 3, "writable": 4, "socket": 2, "sudoers": 4, "not writable": 4,
         "port": 2, "pid": 2},
    ),
    "hardware-environment": (
        "Hardware and environment",
        {"rtx": 3, "5090": 4, "3090": 4, "nvidia-smi": 4, "driver": 3, "cuda": 3, "hip": 4, "rocm": 4,
         "pcie": 4, "avx": 4, "amd": 4, "radeon": 4, "xvfb": 4, "compute capability": 4, "gpu": 2},
    ),
    "issue-log": (
        "Issues, root causes and fixes",
        {"root cause": 4, "the reason is": 4, "segfault": 4, "stall": 3, "crash": 3, "traceback": 3,
         "issue #": 4, "repro": 3, "false positive": 4, "leak": 3, "401": 3, "exit code": 3,
         "no frame for": 4, "unhandled": 3, "hung": 3, "bug": 2, "fix": 2},
    ),
    "open-decisions": (
        "Open decisions and deferred work",
        {"not done": 4, "still open": 4, "deferred": 4, "todo": 4, "remaining": 3, "next step": 3,
         "open item": 4, "not implemented": 4, "pending": 3, "left out": 2, "not yet": 3},
    ),
    "general-knowledge": (
        "General knowledge outside the project",
        {"ollama": 3, "ghidra": 4, "handbrake": 4, "hanbrake": 4, "twitter": 4, "tweet": 4,
         "state of ai": 4, "kim jong": 4, "trump": 3, "lm-evaluation": 4, "nist": 4, "caisi": 4},
    ),
}

# A sentence is worth keeping when it names something concrete: a file, a flag, an identifier,
# or a number with a unit.
CODE = re.compile(r"(?i)(`[^`]{2,}`|--[a-z][a-z-]|/[a-z_]+/[a-z_]+|\w+\.(py|cpp|md|json|sh|hpp|h|js)|"
                  r"\d+(?:\.\d+)?\s*(tok/s|tokens/s|ms|gb|mib|gib|%|k tokens|tokens|seconds|s\b))")
# The reasoning out loud, not the result of it.
NOISE = re.compile(r"(?i)^(let me|let's|i will|i need|i should|i can|i'd|i have to|this seems|it looks|"
                  r"perhaps|maybe|first,|next,|to understand|there are multiple|now let|good question|"
                  r"solve the|act as|here are \d+|answer these|thought for|sure,|great,|understood|"
                  r"i could also|you can|you should|if you'd rather|would you|please|the user says|"
                  r"i'll|i'm going|my plan|before i|once i|that's a good idea|that is a good idea|"
                  r"both places|so i'll|i am going|the plan is|what i can do|note that this|"
                  r"in other words, i|option \d|one-line change|quick wins|say the word|"
                  r"i also created|i also added|i changed|i edited|i fixed|the fix is to|"
                  r"it is worth|worth knowing|worth noting|worth trying)")
QUESTION = re.compile(r"(?i)^(is|are|should|would|could|can|do|does|did|why|how|what|which|where|when|who|will)\b.*\?$")
SKIP_LINE = re.compile(r"Traceback|File \"|line \d+|ResourceWarning|\.{5,}|\$ |did you mean|"
                       r"undefined reference|\[summary\]|^Usage:|\(see \"|Compiling|Building|\[\d+%\]|"
                       r"^warning:|^error:|^\s*$")


def kind(s: str) -> str:
    """Which section of a topic file a fact belongs to."""
    low = s.lower()
    if re.search(r"(?i)^(open|todo|not done|still|deferred|remaining|pending|not implemented|not yet|"
                 r"left to|caveat|one thing to note|not yet done)", low):
        return "open"
    if re.search(r"(?i)(caution|warning|beware|do not|don't|never|must not|pitfall|gotcha|careful|"
                 r"trap|known gap|only if|unless)", low):
        return "gotchas"
    if re.search(r"\d+(?:\.\d+)?\s*(tok/s|tokens/s|ms|gb|mib|gib|%)", low):
        return "numbers"
    if re.search(r"(?i)(fixed|patched|resolved|changed|replaced|added|removed|switched|renamed|moved|"
                 r"implemented|wired|edited|applied)", low):
        return "decisions"
    return "current"


def topic_scores(sentence: str) -> dict[str, int]:
    low = sentence.lower()
    scores: dict[str, int] = {}
    for topic, words in ((t, kw) for t, (_, kw) in TOPICS.items()):
        for word, weight in words.items():
            if word in low:
                scores[topic] = scores.get(topic, 0) + weight
    return scores


def chat_date(name: str) -> str:
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", name)
    return "-".join(m.groups()) if m else "unknown"


def turns(text: str) -> list[tuple[str, str]]:
    """[(who, body)] with the thinking and the code fences out: they are the working, not the finding."""
    out = []
    for part in re.split(r"^## ", text, flags=re.MULTILINE)[1:]:
        head, _, body = part.partition("\n")
        body = re.sub(r"<details>.*?</details>", " ", body, flags=re.DOTALL)
        body = re.sub(r"```.*?```", " ", body, flags=re.DOTALL)
        out.append((head.strip(), body))
    return out


def user_asks(text: str) -> list[str]:
    out = []
    for who, body in turns(text):
        if who != "You":
            continue
        block = re.sub(r"\s+", " ", body).strip()
        if 10 <= len(block) <= 400:
            out.append(block)
    return out


def sentences(text: str) -> list[str]:
    """Complete declarative sentences from the assistant's prose.

    A bullet that wraps over three lines is one sentence, so bullets are reassembled before
    they are split; paragraphs are handled the same way.
    """
    out = []
    for who, body in turns(text):
        if who == "You":
            continue
        items: list[str] = []
        for line in body.split("\n"):
            s = line.strip()
            if not s or s.startswith(("|", "#", "$", "{", "}")):
                continue
            if s.startswith(("- ", "* ", "+ ")) and len(s) > 2:
                items.append(re.sub(r"^[-*+] ", "", s))
            elif items and not s.startswith(("|", "#", "$", "{", "}")):
                items[-1] += " " + s          # a wrapped continuation of the bullet above
            else:
                items.append(s)
        for item in items:
            if SKIP_LINE.search(item):
                continue
            for sent in re.split(r"(?<=[.!?])\s+", item):
                sent = clean(sent)
                if not (40 <= len(sent) <= 400):
                    continue
                if sent.startswith(("}", "{", "//", "#define", "typedef", "struct ", "uint", "const ", "|")):
                    continue
                if sent.count("//") > 1 or sent.count("{") > 2:
                    continue          # a line of source, not a statement about the project
                if not CODE.search(sent) or not STATE_OK.search(sent):
                    continue
                if NOISE.match(sent) or QUESTION.match(sent):
                    continue
                out.append(sent)
    return out


def clean(s: str) -> str:
    """Drop the markdown emphasis and the bullet lead so a sentence reads as a sentence."""
    s = re.sub(r"\*+", "", s)
    s = re.sub(r"^[-*\s]+", "", s)
    s = re.sub(r"\s{2,}", " ", s).strip()
    return s


STATE_OK = re.compile(r"(?i)\b(is|are|does|do|works|fails|refuses|keeps|means|requires|allows|prevents|"
                      r"returns|reads|writes|stores|holds|takes|costs|causes|defaults|sett|resolves|"
                      r"fixed|added|removed|changed|implemented|set|built|runs|stops|starts|capped|"
                      r"limited|needs|should not|must)\b")


def normalise(s: str) -> str:
    return re.sub(r"[^\w]+", " ", s.lower()).strip()


STOP = {"the", "a", "an", "is", "are", "of", "to", "and", "or", "in", "on", "for", "with", "that",
        "this", "it", "as", "by", "at", "from", "be", "has", "have", "was", "were", "which", "any",
        "all", "not", "no", "so", "if", "then", "than", "into", "about", "its", "your", "our", "they"}


def shingles(s: str) -> set[str]:
    words = [w for w in normalise(s).split() if w not in STOP and len(w) > 2]
    return set(words)


def similar(a: str, b: str) -> bool:
    """Two sentences are the same finding when most of their content words agree."""
    x, y = shingles(a), shingles(b)
    if not x or not y:
        return False
    return len(x & y) / min(len(x), len(y)) > 0.72


def accumulate(items: list[dict]) -> list[dict]:
    """Merge restatements of the same finding, keeping the newest wording and every source.

    A topic file should say the current state once, not the same thing four times from four
    chats. Where two entries agree, the later one wins and every source that said it is kept
    as provenance - including the one that was there first.
    """
    merged: list[dict] = []
    for it in items:
        for m in merged:
            if similar(it["text"], m["text"]):
                if it["date"] >= m["date"]:
                    if m["source"] not in m["also"]:
                        m["also"].append(m["source"])
                    m["text"], m["source"] = it["text"], it["source"]
                if it["source"] != m["source"] and it["source"] not in m["also"]:
                    m["also"].append(it["source"])
                m["date"] = max(m["date"], it["date"])
                break
        else:
            merged.append(dict(it, also=[]))
    return merged


def subject(text: str) -> str:
    """What a sentence is about, in a form two sentences about the same thing share.

    The identifiers in backticks are the subject; without them, the first content words are.
    Grouping by this is what turns a chronological dump into an accumulated state: everything
    the chats said about `turn_tail_check` ends up together instead of scattered through the
    file in date order.
    """
    ids = sorted(set(re.findall(r"`([a-z0-9_./-]{3,})`", text.lower())))
    if ids:
        return ids[0]
    words = [w for w in normalise(text).split() if w not in STOP and len(w) > 3]
    return " ".join(words[:3])


def group(items: list[dict]) -> list[tuple[str, list[dict]]]:
    """Entries about the same thing, newest statement first.

    Two groups merge when their subjects share a word, so `prefill_ms` and `prefill` are one
    thread rather than two. Threads are ordered by how many chats contributed to them: the
    better-established facts come first.
    """
    groups: dict[str, list[dict]] = {}
    for it in items:
        s = subject(it["text"])
        hit = next((g for g in groups if set(g.split()) & set(s.split())), None)
        groups.setdefault(hit or s, []).append(it)
    for g in groups.values():
        g.sort(key=lambda e: (e["date"], e["source"]), reverse=True)
    return sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0]))


def extract() -> dict:
    entries: dict[str, list[dict]] = defaultdict(list)
    seen: dict[str, set[str]] = defaultdict(set)
    sources: dict[str, dict] = {}

    for path in sorted(CHATS.iterdir()):
        if not path.is_file() or path.stat().st_size < 500:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        d = chat_date(path.name)
        asks = user_asks(text)
        found = sentences(text)
        here: set[str] = set()
        for sentence in found:
            key = normalise(sentence)[:200]
            for topic, score in sorted(topic_scores(sentence).items(), key=lambda kv: -kv[1])[:2]:
                if score < 4 or key in seen[topic]:
                    continue
                seen[topic].add(key)
                here.add(topic)
                entries[topic].append({"date": d, "source": path.name,
                                      "section": kind(sentence), "text": sentence})
        sources[path.name] = {"date": d, "size_kb": path.stat().st_size // 1024,
                             "requests": len(asks), "topics": sorted(here), "asks": asks[:12],
                             "outcomes": [f for f in found if kind(f) in ("decisions", "current")][:15]}

    for items in entries.values():
        items.sort(key=lambda e: (e["date"], e["source"]))
    return {"entries": {t: accumulate(v) for t, v in entries.items()}, "sources": sources}


SECTIONS = {
    "current": ("What is true now", "how the thing works, as the chats established it"),
    "decisions": ("Decisions taken", "what was chosen, and why, oldest first"),
    "numbers": ("Measured on this machine", "numbers actually measured, not estimated"),
    "gotchas": ("Gotchas", "things that bit once and will bite again"),
    "open": ("Still open", "not done, deferred, or waiting on a decision"),
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--topics", action="store_true", help="only print the topic counts")
    a = ap.parse_args()

    data = extract()
    entries, sources = data["entries"], data["sources"]

    if a.topics:
        for t, v in sorted(entries.items(), key=lambda kv: -len(kv[1])):
            print(f"{t}: {len(v)} entries from {len({i['source'] for i in v})} transcripts")
        return 0

    (HIST / "topics").mkdir(parents=True, exist_ok=True)
    (HIST / "chats").mkdir(parents=True, exist_ok=True)
    notes_dir = HIST / "notes"

    for topic, items in sorted(entries.items()):
        title = TOPICS[topic][0]
        body = [f"# {title}\n",
                f"Accumulated from {len({i['source'] for i in items})} transcripts, {len(items)} entries. "
                f"Built {date.today()}. Newer chats append here; within a section the entries are "
                "grouped by the thing they are about, newest statement first.\n"]
        note = notes_dir / f"{topic}.md"
        if note.is_file():
            text = note.read_text(encoding="utf-8").strip()
            text = re.sub(r"^# .*\n+", "", text)          # the topic file already has the heading
            if text:
                body.append("\n## Current state\n\nMaintained by hand; the builder keeps it in place.\n\n"
                            + text + "\n")
        for section, (heading, note) in SECTIONS.items():
            rows = [i for i in items if i["section"] == section]
            if not rows:
                continue
            body.append(f"\n## {heading}\n\n{note}\n")
            for key, thread in group(rows):
                label = f" · {len(thread)} chats" if len(thread) > 1 else ""
                body.append(f"\n**{key}**{label}")
                for r in thread:
                    also = f" · also in {', '.join(sorted(set(r['also'])))}" if r["also"] else ""
                    body.append(f"- {r['text']}\n  <sub>{r['date']} · {r['source']}{also}</sub>")
        (HIST / "topics" / f"{topic}.md").write_text("\n".join(body) + "\n", encoding="utf-8")

    for name, s in sorted(sources.items(), key=lambda kv: kv[1]["date"]):
        body = [f"# {name}\n",
                f"{s['date']} · {s['size_kb']} KB · {s['requests']} requests · topics: "
                f"{', '.join(s['topics']) or 'nothing worth keeping'}\n",
                "## What was asked"]
        body += [f"- {q}" for q in s["asks"]]
        body.append("\n## What came of it")
        body += [f"- {o}" for o in s["outcomes"]] or ["- nothing that survived the transcript"]
        (HIST / "chats" / f"{s['date']}-{Path(name).stem}.md").write_text("\n".join(body) + "\n",
                            encoding="utf-8")

    (HIST / "index.json").write_text(json.dumps({
        "built": str(date.today()), "transcripts": len(sources),
        "categories": {t: TOPICS[t][0] for t in TOPICS},
        "topics": {t: len(v) for t, v in sorted(entries.items())},
        "sources": sources,
    }, indent=1) + "\n", encoding="utf-8")

    lines = ["# Sources\n", "Which transcript contributed to which category.\n"]
    for name, s in sorted(sources.items(), key=lambda kv: kv[1]["date"]):
        lines.append(f"- {s['date']} `{name}` ({s['size_kb']} KB, {s['requests']} requests): "
                     f"{', '.join(s['topics']) or 'nothing worth keeping'}")
    (HIST / "sources.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    readme = ["# data/history — the accumulated development state\n",
             "What was learned across the chat transcripts, merged by topic instead of by chat. "
             "A new chat appends to the topics it touched; nothing has to be re-read from the raw "
             "transcripts to know the current state.\n",
             "## Layout",
             "- `topics/<topic>.md` — one file per category; entries are dated, attributed, and "
             "grouped by the thing they are about",
             "- `notes/<topic>.md` — the hand-written current state, inserted at the top of each topic",
             "- `chats/<date>-<name>.md` — one file per transcript: what was asked, what came of it",
             "- `index.json` — the machine-readable version of both",
             "- `sources.md` — the reverse index, category by transcript",
             "\n## Categories",
             "\n".join(f"- `topics/{t}.md` — {TOPICS[t][0]} ({len(v)} entries)"
                       for t, v in sorted(entries.items(), key=lambda kv: -len(kv[1]))),
             "\n## Rebuild",
             "```bash\npython3 tools/build_history.py\n```\n",
             "The extraction is deterministic: the transcripts are the source of truth. Anything added "
             "by hand to a topic file is lost on a rebuild — the current state lives in "
             "`notes/<topic>.md`, which the builder reads and keeps.",
             ""]
    (HIST / "README.md").write_text("\n".join(readme) + "\n", encoding="utf-8")
    print(f"{len(sources)} transcripts -> {len(entries)} categories, "
          f"{sum(len(v) for v in entries.values())} entries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
