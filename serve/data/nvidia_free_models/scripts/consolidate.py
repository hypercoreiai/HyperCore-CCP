import json, re, os, glob

SLUGS = sorted({os.path.basename(p)[:-3] for p in glob.glob('*.md')
                if not p.startswith('_') and not p.startswith('card_') and p != 'models_index.md'})

def src(slug):
    a = open(f'{slug}.md', encoding='utf-8', errors='replace').read()
    if a.startswith('---'):
        return a, True
    c = f'card_{slug}.md'
    if os.path.exists(c):
        return open(c, encoding='utf-8', errors='replace').read(), False
    return a, False

def front(text):
    m = re.match(r'---\n(.*?)\n---', text, re.S)
    if not m: return {}
    d = {}
    for line in m.group(1).splitlines():
        k, _, v = line.partition(':')
        d[k.strip()] = v.strip().strip('"')
    return d

def section(text, *names):
    for n in names:
        m = re.search(r'(?mi)^#{1,4}\s*(?:\*\*)?' + n + r'[^:]*:?\s*\n(.*?)(?=\n#{1,4}\s|\Z)', text, re.S)
        if m: return m.group(1).strip()
    return ''

def find(text, *pats):
    for p in pats:
        m = re.search(p, text, re.I|re.S)
        if m: return re.sub(r'\s+', ' ', m.group(1)).strip()
    return ''

LIC = ['MIT License','Apache 2.0','Apache-2.0','Llama 3.2 Community License','Llama 3 Community',
       'OpenMDW','Open Model License','Open Model Agreement','NVIDIA Software License','BSD',
       'Creative Commons','GPL','Silvanus','Z.ai License','Poolside','Non-commercial']

rows = []
for slug in SLUGS:
    text, has_fm = src(slug)
    fm = front(text)
    title = fm.get('title') or re.findall(r'(?m)^#\s+(.+)$', text)[:1] or [slug]
    title = title[0] if isinstance(title, list) else title
    lic_raw = section(text, 'License', 'License and Terms of Use', 'Governing Terms', 'Terms of Use')
    lic = ', '.join(sorted({l for l in LIC if l.lower() in (lic_raw + text[:2000]).lower()})) or 'not stated'
    geo = section(text, 'Deployment Geography') or find(text, r'Deployment Geography[:\s]*\n?(.{0,60})')
    rel = find(text, r'Release Date[:\s]*\n?(.{0,200})')
    params = find(text,
        r'\*\*Total Parameters:\*\*\s*(.{0,60})',
        r'Model Size[:\*\s]*\n?(.{0,120})',
        r'\*\*Model Size:\*\*\s*(.{0,80})',
        r'(?i)total parameters[:\s]*([0-9.,]+\s*[BMKT]\b)')
    ctx = find(text,
        r'\*\*Context Length:\*\*\s*(.{0,80})',
        r'(?i)context length is\s*([0-9,]+\s*tokens)',
        r'(?i)context of up to\s*([0-9,]+\s*tokens)',
        r'(?i)maximum context[:\s]*([0-9,]+\s*tokens)',
        r'(?i)context length[:\s]*([0-9,]+)',
        r'(?i)context window[:\s]*([0-9,]+)')
    inp = find(text, r'\*\*Input Types?:\*\*\s*(.{0,120})', r'(?i)^### Input:\n(.{0,200})')
    outp = find(text, r'\*\*Output Types?:\*\*\s*(.{0,120})', r'(?i)^### Output:\n(.{0,200})')
    arch = find(text, r'\*\*Architecture Type:\*\*\s*(.{0,80})', r'\*\*Network Architecture:\*\*\s*(.{0,80})')
    desc = fm.get('description') or (section(text, 'Description', 'Model Overview')[:300])
    rows.append({
        'slug': slug, 'name': title,
        'publisher': fm.get('publisher') or 'nvidia',
        'canonical': fm.get('canonical') or f'https://build.nvidia.com/nvidia/{slug}',
        'description': desc,
        'params': params, 'active': find(text, r'\*\*Active Parameters:\*\*\s*(.{0,60})'),
        'context': ctx, 'input': inp, 'output': outp, 'arch': arch,
        'license': lic, 'geography': re.sub(r'\s+', ' ', geo)[:60],
        'release': rel, 'source': 'model card md' if has_fm else 'embedded card (html shell)',
    })

json.dump(rows, open('_free_cards.json', 'w'), indent=1)
print(len(rows), 'cards')
for r in rows:
    print(f"{r['slug'][:34]:34} | {r['publisher'][:12]:12} | {r['params'][:28]:28} | {r['context'][:30]:30} | {r['input'][:24]:24} -> {r['output'][:20]:20} | {r['license'][:40]}")
