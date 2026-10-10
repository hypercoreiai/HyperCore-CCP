p = 'extract.py'
s = open(p).read()

s = s.replace('''def front_matter(text):''', '''def catalog_blurbs():
    out = {}
    try:
        idx = open(os.path.join(BASE, "models_index.md"), encoding="utf-8").read()
    except OSError:
        return out
    for m in re.finditer(r"- \\[([^\\]]+)\\]\\(([^)]*?/([a-z0-9._-]+))\\.md\\) \\u2014 ([^\\n]+)", idx):
        slug = m.group(3)
        if slug not in out:
            out[slug] = m.group(4).strip()
    return out

BLURBS = catalog_blurbs()

def front_matter(text):''')

s = s.replace('''    desc = section(text, "Description", "Model Overview", "Overview", "Model Information") or plain.get("Description") or plain.get("Model Overview")''',
'''    desc = section(text, "Description", "Model Overview", "Overview", "Model Information") or plain.get("Description") or plain.get("Model Overview") or fm.get("description", "") or BLURBS.get(slug, "")''')

s = s.replace('''    rows.append({
        "slug": slug,''', '''    blob = (desc + " " + inp + " " + out).lower()
    if "text" in blob and ("audio" in blob or "video" in blob or "image" in blob) and "reasoning" in blob:
        cat = "multimodal reasoning LLM"
    elif "audio" in blob and "text" not in blob:
        cat = "speech / audio"
    elif "audio" in blob:
        cat = "speech & audio LLM"
    elif "tabular" in blob or "relational" in blob:
        cat = "tabular / structured data"
    elif "embedding" in desc.lower() or "embed" in out.lower():
        cat = "embeddings / retrieval"
    elif "video" in blob and ("generate" in desc.lower() or "denois" in blob or "watermark" in blob):
        cat = "video generation / world model"
    elif "camera" in blob or "3d" in blob or "pose" in blob or "detect" in desc.lower():
        cat = "vision / detection"
    elif "safety" in desc.lower() or "guard" in desc.lower():
        cat = "safety / guardrail"
    elif "image" in blob and "text" in blob:
        cat = "vision-language model"
    else:
        cat = "language model"

    rows.append({
        "slug": slug,
        "category": cat,''')

open(p, 'w').write(s)
