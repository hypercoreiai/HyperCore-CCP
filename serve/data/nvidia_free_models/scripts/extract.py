#!/usr/bin/env python3
"""Turn the 38 NVIDIA NIM free-endpoint model cards into a structured CSV."""
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

def catalog_index():
    names, blurbs = {}, {}
    path = os.path.join(BASE, "models_index.md")
    if not os.path.exists(path):
        return names, blurbs
    for m in re.finditer(r"- \[([^\]]+)\]\(([^)]*?/([a-z0-9._-]+))\.md\) \u2014 ([^\n]+)",
                         open(path, encoding="utf-8").read()):
        names.setdefault(m.group(3), m.group(1).strip())
        blurbs.setdefault(m.group(3), m.group(4).strip())
    return names, blurbs

NAMES, BLURBS = catalog_index()

def html_to_text(raw):
    s = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", raw, flags=re.S | re.I)
    s = re.sub(r"<br\s*/?>", "\n", s)
    s = re.sub(r"</(p|div|tr|li|h[1-6]|td|th|section|article|dt|dd)>", "\n", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    s = re.sub(r"[ \t]{2,}", " ", s)
    s = re.sub(r"\n\s*\n+", "\n", s)
    return s.strip()

def page_title(raw):
    m = re.search(r"<title>([^<]+)</title>", raw, re.I) or re.search(r'og:title" content="([^"]+)"', raw)
    if not m:
        return ""
    t = html.unescape(m.group(1)).strip()
    t = re.sub(r"\s*\|\s*NVIDIA.*$", "", t)
    t = re.sub(r"\s+Model by NVIDIA$", "", t)
    return t.strip()

def load(slug):
    raw = open(os.path.join(BASE, slug + ".md"), encoding="utf-8", errors="replace").read()
    if raw.lstrip().startswith("---"):
        return raw, "card markdown"
    h = os.path.join(BASE, "mc_" + slug + ".html")
    if os.path.exists(h):
        return html_to_text(open(h, encoding="utf-8", errors="replace").read()), "modelcard page (JS-rendered)"
    extra = json.load(open(os.path.join(BASE, "_html_cards.json")))
    if slug in extra and extra[slug]:
        return extra[slug], "card markdown embedded in page payload"
    return html_to_text(raw), "page shell only"

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
        m = re.search(r"^#{1,4}\s*" + name + r"[^\n]*\n([\s\S]*?)(?=\n#{1,4}\s|\Z)", text, re.M | re.I)
        if m:
            return m.group(1).strip()
    return ""

TOPICS = ["Description", "Model Overview", "License/Terms of Use", "License and Terms of Use",
          "Intended Use", "Known Limitations", "Deployment Geography", "Release Date",
          "Model information", "Model Architecture", "Input", "Output", "Inputs", "Outputs",
          "Use Case", "Software Integration", "Model Versions", "Usage", "Quality Benchmarks",
          "Ethical Considerations", "Generation modes", "API quickstart",
          "Safety, limitations, and provenance", "Governing terms and support"]

def plain_sections(text):
    idx = sorted((m.start(), m.group(0)) for t in TOPICS
                 for m in re.finditer(r"^\s*" + re.escape(t) + r"\s*:?\s*$", text, re.M | re.I))
    out = {}
    for i, (pos, head) in enumerate(idx):
        end = idx[i + 1][0] if i + 1 < len(idx) else len(text)
        key = head.strip().rstrip(":")
        body = text[pos:end].strip()[len(head.strip()):].strip().lstrip(":").strip()
        if body and key not in out:
            out[key] = body
    return out

def kv(block, *keys):
    for k in keys:
        for pat in (r"\*\*" + re.escape(k) + r"(?:\s*\([A-Za-z()]+\))?\s*:\*\*\s*([^\n]+)",
                    r"\*\*" + re.escape(k) + r"\s*:\*\*\s*([^\n]+)",
                    r"^" + re.escape(k) + r"\s*:\s*([^\n]+)"):
            m = re.search(pat, block, re.I | re.M)
            if m:
                return m.group(1).strip()
    return ""

def tidy(s, limit=500):
    if not s:
        return ""
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)
    s = s.replace("\\u003e", " ").replace("\u003e", " ").replace("<br", " ").replace("/>", " ")
    s = re.sub(r"[*_#|`]", " ", s)
    return re.sub(r"\s+", " ", s).strip()[:limit]

rows = []
for slug in SLUGS:
    text, src = load(slug)
    fm = front_matter(text)

    title = NAMES.get(slug) or fm.get("title") or ""
    if not title:
        for line in text.splitlines():
            if line.startswith("# ") and not re.match(r"(model overview|overview|description)$",
                                                      line[2:].strip(), re.I):
                title = line[2:].strip()
                break
    if not title:
        title = page_title(open(os.path.join(BASE, slug + ".md"), encoding="utf-8", errors="replace").read()) or slug

    publisher = fm.get("publisher") or ""
    if not publisher:
        for key in URLS:
            if key.endswith("/" + slug):
                publisher = key.split("/")[0]
                break

    plain = plain_sections(text)
    arch = section(text, "Model Architecture", "Model information", "Model Details", "Model Parameters") \
        or plain.get("Model Architecture") or plain.get("Model information") or text

    params = kv(arch, "Total Parameters", "Number of model parameters", "Model Size", "Parameter Count", "Parameters")
    if not params:
        params = kv(text, "Total Parameters", "Number of model parameters", "Parameters", "Model Size")
    if not params:
        m = re.search(r"(?i)\|\s*(?:model size|total parameters|parameters)\s*\|\s*([^\n|]+)", text)
        if m:
            params = m.group(1).strip()
    if params and not re.search(r"\d", params) and "disclos" not in params.lower():
        params = ""

    active = kv(arch, "Active Parameters", "Activated Parameters")
    arch_type = kv(arch, "Architecture Type")
    arch_net = kv(arch, "Network Architecture")
    ctx = kv(arch, "Context Length", "Maximum Sequence Length", "Max Sequence Length", "Context Window",
            "Input Context Length")
    if not ctx:
        m = re.search(r"context (?:length|window)[^\n]{0,80}?(\d[\d,]{4,})\s*tokens", text, re.I)
        if m:
            ctx = m.group(1) + " tokens"

    inp = kv(section(text, "Input", "Inputs") or plain.get("Input", "") or arch,
            "Input Type", "Input Modalities", "Input Types", "Input Format")
    out = kv(section(text, "Output", "Outputs") or plain.get("Output", "") or arch,
            "Output Type", "Output Modalities", "Output Types", "Output Format")

    m = re.search(r"input modalities[^\n]*\n\s*\|([^\n]*)", text, re.I)
    if m and not inp:
        cells = [c.strip() for c in m.group(1).split("|") if c.strip()]
        if len(cells) >= 3:
            inp, out = cells[1], cells[2]

    rel_block = section(text, "Release Date", "Release") or plain.get("Release Date", "")
    rel = kv(rel_block, "Build.NVIDIA.com", "HuggingFace", "Release Date")
    if not rel:
        m = re.search(r"\d{1,2}/\d{1,2}/\d{4}", rel_block)
        if m:
            rel = m.group(0)

    lic = section(text, "License and Terms of Use", "License/Terms of Use", "License", "Terms of Use",
                  "Governing terms") or plain.get("License/Terms of Use") or plain.get("License and Terms of Use") \
        or plain.get("Governing terms and support") or kv(text, "License")
    geo = section(text, "Deployment Geography", "Geography") or plain.get("Deployment Geography")
    usecase = section(text, "Use Case", "Intended Use", "Use Cases") or plain.get("Intended Use")
    desc = section(text, "Description", "Model Overview", "Overview", "Model Information") \
        or plain.get("Description") or plain.get("Model Overview") or fm.get("description") or BLURBS.get(slug, "")
    dl = "yes" if re.search(r"Downloadable Free Endpoint|Download and Post-Train|Download NIM|Download Now", text, re.I) else ""

    i, o, d = inp.lower(), out.lower(), desc.lower()
    nm = title.lower() + " " + slug
    if "embed" in nm or ("embedding" in d and "float" in o):
        cat = "embeddings / retrieval"
    elif "guard" in nm or "safety" in nm or "harm" in d:
        cat = "safety / guardrail"
    elif "tabular" in nm or "relational" in nm or "tabular" in i:
        cat = "tabular / structured data"
    elif "detect" in nm or "pose" in nm or "segment" in nm or "perception" in d or "bounding box" in o or "detection" in o:
        cat = "detection / perception (CV)"
    elif ("audio" in i and ("image" in i or "video" in i)) and "text" in o:
        cat = "multimodal (omni) LLM"
    elif ("audio" in i and "audio" in o) or "noise" in nm or "voice" in nm:
        cat = "speech enhancement / noise removal"
    elif "audio" in i or "audio" in o or "tts" in nm or "speech" in nm:
        cat = "speech / audio (TTS, ASR, voice chat)"
    elif any(k in nm for k in ("cosmos", "diffusion", "muse", "glimmer", "transfer")) or \
         ("text-to-image" in d or "generative model" in d or ("generat" in d and ("image" in o or "video" in o))):
        cat = "image/video generation (world model)"
    elif ("image" in i or "video" in i) and "text" in o:
        cat = "multimodal LLM (vision+text)"
    elif "text" in i and "text" in o:
        cat = "language model"
    else:
        cat = "unclassified (card does not state modalities)"

    rows.append({
        "slug": slug, "model_name": tidy(title, 120), "publisher": publisher,
        "card_url": URLS.get(slug, "https://build.nvidia.com/nvidia/" + slug),
        "access": "free endpoint (preview)", "download_available_in_card_text": dl, "category": cat,
        "model_type": fm.get("type", ""),
        "total_parameters": tidy(params, 60), "active_parameters": tidy(active, 60),
        "context_length": tidy(ctx, 60),
        "architecture_type": tidy(arch_type, 120), "network_architecture": tidy(arch_net, 120),
        "input_modalities": tidy(inp, 200), "output_modalities": tidy(out, 200),
        "release_date": tidy(rel, 120), "license": tidy(lic, 500),
        "deployment_geography": tidy(geo, 120), "use_case": tidy(usecase, 300),
        "description": tidy(desc, 700), "card_updated": fm.get("updated", ""),
        "source_format": src,
    })

with open(os.path.join(BASE, "nvidia_free_endpoints.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print("wrote", len(rows), "rows")
