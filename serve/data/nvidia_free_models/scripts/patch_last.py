p = 'extract.py'
s = open(p).read()
old = s[s.index('    i, o, d = inp.lower()'):s.index('    rows.append({')]
new = '''    i, o, d = inp.lower(), out.lower(), desc.lower()
    nm = title.lower() + " " + slug
    if "embed" in nm or ("embedding" in d and "float" in o):
        cat = "embeddings / retrieval"
    elif "guard" in nm or "safety" in nm or "harm" in d:
        cat = "safety / guardrail"
    elif "tabular" in nm or "relational" in nm or "tabular" in i:
        cat = "tabular / structured data"
    elif "detect" in nm or "pose" in nm or "segment" in nm or "perception" in d:
        cat = "detection / perception (CV)"
    elif ("audio" in i and ("image" in i or "video" in i)) and "text" in o:
        cat = "multimodal (omni) LLM"
    elif ("audio" in i and "audio" in o) or "noise" in nm or "voice" in nm:
        cat = "speech enhancement / noise removal"
    elif "audio" in i or "audio" in o or "tts" in nm or "speech" in nm:
        cat = "speech / audio (TTS, ASR, voice chat)"
    elif any(k in nm for k in ("cosmos", "diffusion", "muse", "glimmer", "transfer")) or \\
         ("text-to-image" in d or "generative model" in d or ("generat" in d and ("image" in o or "video" in o))):
        cat = "image/video generation (world model)"
    elif ("image" in i or "video" in i) and "text" in o:
        cat = "multimodal LLM (vision+text)"
    elif "text" in i and "text" in o:
        cat = "language model"
    else:
        cat = "unclassified (card does not state modalities)"

'''
s = s.replace(old, new)
open(p, 'w').write(s)
