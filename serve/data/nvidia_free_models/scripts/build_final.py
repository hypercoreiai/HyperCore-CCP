import json, re, glob

def clean(s):
    if not s: return ''
    s = re.sub(r'\s+', ' ', s).strip()
    s = s.split('## ')[0].split('### ')[0].strip()
    return s[:160]

def sections(md):
    """split markdown into {heading: body}"""
    out = {}
    lines = md.split('\n')
    cur = None; buf = []
    for ln in lines:
        m = re.match(r'^(#{1,4})\s*(.+)$', ln.strip())
        if m:
            if cur: out[cur] = '\n'.join(buf).strip()
            cur = m.group(2).strip(); buf = []
        elif cur:
            buf.append(ln)
    if cur: out[cur] = '\n'.join(buf).strip()
    return out

def field(sec, keys):
    for k in keys:
        for h, v in sec.items():
            if h.lower().startswith(k.lower()):
                return v
    return ''

def grab_num(text, pat):
    m = re.search(pat, text, re.I)
    return m.group(1).strip() if m else ''

cards = json.load(open('_free_cards.json'))
extra = {}
for f in glob.glob('card_*.txt'):
    slug = f[5:-5]
    extra[slug] = sections(open(f, encoding='utf-8').read())

rows = []
for c in cards:
    slug = c['slug']
    sec = extra.get(slug)
    r = {
        'slug': slug,
        'publisher': c.get('publisher',''),
        'name': c.get('name',''),
        'desc': clean(c.get('description','')),
        'url': c.get('canonical',''),
    }
    if sec:
        arch = field(sec, ['Model Architecture','Architecture Type'])
        r['arch'] = clean(arch)
        r['params'] = clean(grab_num(arch + ' ' + field(sec,['Model Size','Parameters','Size']), r'(?i)(?:model size|total parameters|parameters)[:\s]*([0-9][^\n|]{0,40})'))
        r['context'] = clean(grab_num(arch, r'(?i)context length[:\s]*([0-9][^\n|]{0,30})'))
        r['input'] = clean(field(sec, ['Input']))[:120]
        r['output'] = clean(field(sec, ['Output']))[:120]
        r['license'] = clean(field(sec, ['License','Terms of Use','Terms of use']))[:160]
        r['geo'] = clean(field(sec, ['Deployment Geography']))[:80]
        r['release'] = clean(field(sec, ['Release Date']))[:120]
        r['use'] = clean(field(sec, ['Use Case']))[:120]
        r['source'] = 'embedded card (html shell, full parse)'
    else:
        r['arch'] = clean(c.get('arch',''))
        r['params'] = clean(c.get('params',''))
        r['context'] = clean(c.get('context',''))
        r['input'] = clean(c.get('input',''))[:120]
        r['output'] = clean(c.get('output',''))[:120]
        r['license'] = clean(c.get('license',''))[:160]
        r['geo'] = clean(c.get('geography',''))[:80]
        r['release'] = clean(c.get('release',''))[:120]
        r['use'] = ''
        r['source'] = 'model card md' if c.get('source')=='model card md' else 'html shell only (card client-rendered)'
    rows.append(r)

json.dump(rows, open('_final_cards.json','w'), indent=1)
print(len(rows), 'rows')
for r in rows:
    print(f"{r['publisher']:12} {r['slug']:34} {r['params'][:28]:28} {r['context'][:14]:14} {r['license'][:40]}")
