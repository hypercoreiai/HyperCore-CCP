import re, json

def literals(raw, min_len=800):
    i = 0
    while True:
        i = raw.find('"', i)
        if i < 0: return
        j = i + 1
        buf = []
        while j < len(raw):
            c = raw[j]
            if c == '\\':
                buf.append(raw[j:j+2]); j += 2; continue
            if c == '"':
                break
            buf.append(c); j += 1
        s = ''.join(buf)
        if len(s) >= min_len and '\\n' in s:
            try:
                yield json.loads('"' + s + '"')
            except Exception:
                pass
        i = j + 1

for slug in ['body-pose','cosmos3-nano','cosmos3-nano-reasoner']:
    raw = open(f'html_{slug}.html', encoding='utf-8', errors='replace').read()
    best = None
    for s in literals(raw):
        score = sum(k in s for k in ('Architecture','Deployment','License','Input Modalities','Output','Model Size','Context'))
        if best is None or score > best[0]:
            best = (score, s)
    if best:
        print(slug, 'score', best[0], 'len', len(best[1]))
        open(f'card_{slug}.md','w').write(best[1])
