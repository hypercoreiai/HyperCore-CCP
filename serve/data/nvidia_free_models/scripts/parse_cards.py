#!/usr/bin/env python3
"""Extract structured fields from the 38 NVIDIA NIM free-endpoint model cards."""
import json, re, csv, os, html

BASE = os.path.dirname(os.path.abspath(__file__))
SLUGS = sorted(json.load(open(os.path.join(BASE, "_cards_combined.json"))).keys())

URLS = {}
for line in open("/home/ai-user0/_card_urls.txt"):
    line = line.strip()
    if line:
        URLS[line.lstrip("/")] = "https://build.nvidia.com" + line
URLS["nvidia/cosmos-transfer2_5-2b"] = "https://build.nvidia.com/nvidia/cosmos-transfer2_5-2b"
URLS["nvidia/llama-3_1-nemotron-safety-guard-8b-v3"] = "https://build.nvidia.com/nvidia/llama-3_1-nemotron-safety-guard-8b-v3"

TAG_STRIP = re.compile(r"<[^>]+>")
SCRIPT_RE = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.S | re.I)


def html_to_text(raw):
    raw = SCRIPT_RE.sub(" ", raw)
    raw = re.sub(r"<br\s*/?>", "\n", raw)
    raw = re.sub(r"</(p|div|tr|li|h[1-6]|td|th|section|article)>", "\n", raw)
    raw = TAG_STRIP.sub(" ", raw)
    raw = html.unescape(raw)
    raw = re.sub(r"[ \t]{2,}", " ", raw)
    raw = re.sub(r"\n\s*\n+", "\n", raw)
    return raw.strip()


def get_text(slug):
    md = os.path.join(BASE, slug + ".md")
    raw = open(md, encoding="utf-8", errors="replace").read()
    if raw.lstrip().startswith("---"):
        return raw, "markdown"
    h = os.path.join(BASE, "html_" + slug + ".html")
    if os.path.exists(h):
        return html_to_text(open(h, encoding="utf-8", errors="replace").read()), "html"
    extra = json.load(open(os.path.join(BASE, "_html_cards.json")))
    if slug in extra and extra[slug]:
        return extra[slug], "html-fragment"
    return html_to_text(raw), "html-shell"


def front_matter(text):
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip().strip('"').strip("'")
    return fm


def section(text, *names):
    for name in names:
        pat = re.compile(r"^#{1,4}\s*" + name + r"[^\n]*\n(.*)", re.M | re.I)
        m = pat.search(text)
        if not m:
            continue
        rest = m.group(1)
        nxt = re.search(r"^#{1,4}\s", rest, re.M)
        body = rest[:nxt.start()] if nxt else rest
        return body.strip()
    return ""


def field(block, *patterns):
    for p in patterns:
        m = re.search(p, block, re.I)
        if m:
            return m.group(1).strip()
    return ""


def first_heading(text):
    for line in text.splitlines():
        m = re.match(r"^\s*#\s+(.+)$", line)
        if m:
            t = m.group(1).strip()
            if t and not re.match(r"^(model overview|overview)$", t, re.I):
                return t
    m = re.search(r"^\s*#{1,3}\s+(.+)$", text, re.M)
    return m.group(1).strip() if m else ""


def clean(s, limit=300):
    if not s:
        return ""
    s = re.sub(r"\s+", " ", s).strip().replace("\ufeff", "")
    return s[:limit]


rows = []
for slug in SLUGS:
    text, src = get_text(slug)
    fm = front_matter(text)
    body = text[re.search(r"^---", text, re.S).end():] if src == "markdown" else text

    overview = section(body, "Model Overview", "Overview")
    desc = section(body, "Description") or overview
    meta = section(body, "Model Architecture", "Model Details", "Model Information",
                   "Technical", "Model Specifications") or body

    title = fm.get("title") or first_heading(body)
    publisher = fm.get("publisher") or (URLS.get(slug, "").split("/")[3] if slug in URLS else "")

    size = field(meta, r"model size[^|]*\|\s*([^\n|]+)", r"parameters[^|]*\|\s*([^\n|]+)",
                 r"\b(\d[\d.,]*\s*[BMK])\b\s*(?:parameters|params)")
    ctx = field(meta, r"context length[^|]*\|\s*([^\n|]+)", r"max(?:imal)? sequence length[^|]*\|\s*([^\n|]+)")
    arch = field(meta, r"model architecture[^|]*\|\s*([^\n|]+)", r"architecture[^|]*\|\s*([^\n|]+)")
    inp = field(meta, r"input modality[^|]*\|\s*([^\n|]+)", r"inputs?[^|]*\|\s*([^\n|]+)")
    out = field(meta, r"output modality[^|]*\|\s*([^\n|]+)", r"outputs?[^|]*\|\s*([^\n|]+)")
    release = field(meta, r"release date[^|]*\|\s*([^\n|]+)", r"released[^|]*\|\s*([^\n|]+)")
    lic = section(body, "License", "Terms of Use", "Model License") or field(body, r"license[^|]*\|\s*([^\n|]+)")
    geo = section(body, "Deployment Geography", "Geography", "Deployment")
    usecase = section(body, "Use Case", "Use Cases", "Intended Use")

    rows.append({
        "slug": slug,
        "model_name": clean(title, 120),
        "publisher": publisher,
        "url": URLS.get(slug, "https://build.nvidia.com/nvidia/" + slug),
        "type": fm.get("type", ""),
        "updated": fm.get("updated", ""),
        "size_params": clean(size, 60),
        "context_length": clean(ctx, 60),
        "architecture": clean(arch, 200),
        "input_modalities": clean(inp, 200),
        "output_modalities": clean(out, 200),
        "release_date": clean(release, 120),
        "license": clean(lic, 400),
        "deployment_geography": clean(geo, 200),
        "use_case": clean(usecase, 300),
        "description": clean(desc, 600),
        "source_format": src,
    })

with open(os.path.join(BASE, "nvidia_free_endpoints.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

print(str(len(rows)) + " rows written")
for r in rows:
    print("%-38s %-12s %-12s %-18s %-40s %s" % (r["slug"], r["publisher"], r["size_params"],
          r["context_length"], r["input_modalities"][:40], r["source_format"]))
