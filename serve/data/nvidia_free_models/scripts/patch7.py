p = 'extract.py'
s = open(p).read()

names = '''def catalog_index():
    names, blurbs = {}, {}
    try:
        idx = open(os.path.join(BASE, "models_index.md"), encoding="utf-8").read()
    except OSError:
        return names, blurbs
    for m in re.finditer(r"- \\[([^\\]]+)\\]\\(([^)]*?/([a-z0-9._-]+))\\.md\\) \\u2014 ([^\\n]+)", idx):
        slug = m.group(3)
        names.setdefault(slug, m.group(1).strip())
        blurbs.setdefault(slug, m.group(4).strip())
    return names, blurbs

NAMES, BLURBS = catalog_index()

'''
s = s.replace('BLURBS = catalog_blurbs()\n', '')
s = s.replace('def front_matter(text):', names + 'def front_matter(text):')

old = s[s.index('    title = ""'):s.index('    publisher = fm.get(')]
new = '''    title = NAMES.get(slug, "")
    if not title:
        for line in text.splitlines():
            if line.startswith("# "):
                t = line[2:].strip()
                if t and not re.match(r"(model overview|overview|description)$", t, re.I):
                    title = t
                    break
    if not title:
        title = page_title(open(os.path.join(BASE, slug + ".md"), encoding="utf-8", errors="replace").read()) or slug
'''
s = s.replace(old, new)

s = s.replace('    desc = section(text, "Description", "Model Overview", "Overview", "Model Information") or plain.get("Description") or plain.get("Model Overview") or fm.get("description", "") or BLURBS.get(slug, "")',
              '    desc = section(text, "Description", "Model Overview", "Overview", "Model Information") or plain.get("Description") or plain.get("Model Overview") or fm.get("description", "") or BLURBS.get(slug, "")')

cls_old = s[s.index('    i = inp.lower()'):s.index('    rows.append({')]
cls_new = '''    i, o, d = inp.lower(), out.lower(), desc.lower()
    if "float" in o or "embedding" in d:
        cat = "embeddings / retrieval"
    elif "tabular" in i or "tabular" in o or "relational" in d:
        cat = "tabular / structured data"
    elif "audio" in i and "audio" in o:
        cat = "speech enhancement / noise removal"
    elif "audio" in i or "audio" in o:
        cat = "speech / audio (TTS, ASR, voice chat)"
    elif "guard" in slug or "safety" in d or "harm" in d:
        cat = "safety / guardrail"
    elif ("image" in i or "video" in i) and ("image" in o or "video" in o):
        cat = "image/video generation (world model)"
    elif ("image" in i or "video" in i or "audio" in i) and "text" in o and re.search(r"\\d{2,}B", params):
        cat = "multimodal LLM"
    elif "text" in i and "text" in o:
        cat = "language model"
    elif ("image" in i or "video" in i) and "text" in o:
        cat = "vision-language model"
    elif "detect" in d or "segment" in d or "pose" in d or "perception" in d:
        cat = "vision detection / perception"
    else:
        cat = "unclassified"

'''
s = s.replace(cls_old, cls_new)

s = s.replace('''        "total_parameters": tidy(params, 60),''',
'''        "total_parameters": tidy(params, 60) if (not params or re.search(r"\\d", params) or "disclos" in params.lower()) else "",''')

open(p, 'w').write(s)
