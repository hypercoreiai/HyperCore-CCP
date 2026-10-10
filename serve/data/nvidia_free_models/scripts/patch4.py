p = 'extract.py'
s = open(p).read()
old = s[s.index('    i = inp.lower()'):s.index('    rows.append({')]
new = '''    i = inp.lower()
    o = out.lower()
    d = desc.lower()
    if "float" in o or "embedding" in d:
        cat = "embeddings / retrieval"
    elif "tabular" in i or "tabular" in o or "relational" in d:
        cat = "tabular / structured data"
    elif "audio" in i and "audio" in o:
        cat = "speech enhancement / noise removal"
    elif "audio" in i or "audio" in o:
        cat = "speech / audio (TTS, ASR, voice chat)"
    elif "safety" in d or "guard" in d or "harm" in d:
        cat = "safety / guardrail"
    elif ("video" in o or "image" in o) and ("generat" in d or "denois" in d or "transfer" in d or "world model" in d):
        cat = "image/video generation (world model)"
    elif "detect" in d or "segment" in d or "pose" in d or "perception" in d:
        cat = "vision detection / perception"
    elif ("image" in i or "video" in i) and "text" in o:
        cat = "vision-language model"
    elif "text" in i and "text" in o:
        cat = "language model"
    else:
        cat = "unclassified"

'''
s = s.replace(old, new)
open(p, 'w').write(s)
