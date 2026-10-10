p = 'extract.py'
s = open(p).read()
old = s[s.index('    blob = (desc'):s.index('    rows.append({')]
new = '''    i = inp.lower()
    o = out.lower()
    d = desc.lower()
    if "float" in o or "embedding" in d or "embed" in d:
        cat = "embeddings / retrieval"
    elif "tabular" in i or "tabular" in o or "table" in d:
        cat = "tabular / structured data"
    elif "audio" in i and "audio" in o:
        cat = "speech enhancement / noise removal"
    elif "audio" in i or "audio" in o:
        cat = "speech / audio"
    elif ("video" in i or "image" in i) and ("video" in o or "image" in o) and ("generate" in d or "denois" in d or "transfer" in d):
        cat = "image/video generation (world model)"
    elif "safety" in d or "guard" in d or "harm" in d:
        cat = "safety / guardrail"
    elif "detect" in d or "segment" in d or "pose" in d or "perception" in d:
        cat = "vision detection / perception"
    elif "text" in i and "text" in o and ("image" in i or "video" in i):
        cat = "multimodal (vision+text) model"
    elif "text" in i and "text" in o:
        cat = "language model"
    else:
        cat = "other"

'''
s = s.replace(old, new)
open(p, 'w').write(s)
