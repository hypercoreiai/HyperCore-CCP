import json, re, os

def literals(raw, min_len=1200):
    i = 0
    while True:
        i = raw.find('"', i)
        if i < 0: return
        j = i + 1; buf = []
        while j < len(raw):
            c = raw[j]
            if c == '\\':
                buf.append(raw[j:j+2]); j += 2; continue
            if c == '"': break
            buf.append(c); j += 1
        s = ''.join(buf)
        if len(s) >= min_len and '\\n' in s:
            try: yield json.loads('"' + s + '"')
            except Exception: pass
        i = j + 1

SHells = ['magpie-tts-zeroshot','nemotron-voicechat','riva-translate-4b-instruct-v2','studiovoice','synthetic-video-detector']
for slug in SHells:
    raw = open(f'{slug}.md', encoding='utf-8', errors='replace').read()
    best = None
    for s in literals(raw):
        score = sum(k in s for k in ('Description','Deployment Geography','License','Input Type','Release Date','Model Architecture','Use Case'))
        if best is None or score > best[0]:
            best = (score, s)
    if best and best[0] >= 2:
        open(f'card_{slug}.md','w').write(best[1])
        print(slug, 'score', best[0], 'len', len(best[1]))
    else:
        print(slug, 'no card literal found', best[0] if best else None)
