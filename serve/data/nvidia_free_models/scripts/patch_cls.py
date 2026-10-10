p = 'extract.py'
s = open(p).read()
old = s[s.index('    i, o, d = inp.lower()'):s.index('    rows.append({')]
new = '''    i, o, d = inp.lower(), out.lower(), desc.lower()
    nm = title.lower() + " " + slug
    if "embed" in nm or "embedding" in d:
        cat = "embeddings / retrieval"
    elif "guard" in nm or "safety" in nm or "harm" in d or "toxic" in d:
        cat = "safety / guardrail"
    elif "tabular" in nm or "relational" in nm or "tabular" in i:
        cat = "tabular / structured data"
    elif ("audio" in i and "audio" in o) or "noise" in nm or "voice" in nm or "speaker" in nm:
        cat = "speech enhancement / noise removal"
    elif "audio" in i or "audio" in o or "tts" in nm or "speech" in nm:
        cat = "speech / audio (TTS, ASR, voice chat)"
    elif "generat" in d and ("video" in d or "image" in d) and "detect" not in nm:
        cat = "image/video generation (world model)"
    elif "detect" in nm or "pose" in nm or "segment" in nm or "perception" in d:
        cat = "vision detection / perception"
    elif ("image" in i or "video" in i or "audio" in i) and "text" in o:
        cat = "multimodal LLM"
    elif "text" in i and "text" in o:
        cat = "language model"
    elif ("image" in i or "video" in i) and "text" in o:
        cat = "vision-language model"
    else:
        cat = "unclassified (card does not state modalities)"

'''
s = s.replace(old, new)
open(p, 'w').write(s)
