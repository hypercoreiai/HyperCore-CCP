import json, re, os, glob

SLUGS = sorted({os.path.basename(p)[:-3] for p in glob.glob('*.md')
                if not p.startswith('_') and not p.startswith('card_') and p != 'models_index.md'})

def src(slug):
    a = open(f'{slug}.md', encoding='utf-8', errors='replace').read()
    if a.startswith('---'): return a, True
    c = f'card_{slug}.md'
    if os.path.exists(c): return open(c, encoding='utf-8', errors='replace').read(), False
    return a, False

def front(t):
    m = re.match(r'---\n(.*?)\n---', t, re.S)
    if not m: return {}
    d = {}
    for line in m.group(1).splitlines():
        k, _, v = line.partition(':')
        d[k.strip()] = v.strip().strip('"')
    return d

def page_title(slug):
    try:
        raw = open(f'html_{slug}.html', encoding='utf-8', errors='replace').read()
    except OSError:
        return ''
    m = re.search(r'<title>(.*?)</title>', raw)
    if not m: return ''
    t = m.group(1).replace('Model by NVIDIA | NVIDIA NIM', '').strip()
    return t

def section(t, *names):
    for n in names:
        m = re.search(r'(?mi)^#{1,4}\s*(?:\*\*)?' + n + r'[^:]*:?\s*\n(.*?)(?=\n#{1,4}\s|\Z)', t, re.S)
        if m: return m.group(1).strip()
    return ''

def find(t, *pats):
    for p in pats:
        m = re.search(p, t, re.I | re.S)
        if m:
            g = m.group(1) if m.groups() else m.group(0)
            return re.sub(r'\s+', ' ', g).strip()
    return ''

LIC = ['MIT License','Apache 2.0','Llama 3.2 Community License','Llama 3 Community','OpenMDW',
       'Open Model License','Open Model Agreement','NVIDIA Software License','BSD','Creative Commons',
       'GPL','Non-commercial']

rows = []
for slug in SLUGS:
    t, has_fm = src(slug)
    fm = front(t)
    title = fm.get('title') or page_title(slug) or slug
    params = find(t,
        r'"parameters":\s*(\d+)',
        r'\*\*Total Parameters:\*\*\s*(.{0,120})',
        r'\*\*Number of (?:model|trainable model) parameters:?\*\*\s*(.{0,120})',
        r'\*\*Number of model parameters:?\*\*\s*(.{0,120})',
        r'(?i)model size[:*\s]*\n?(.{0,120})',
        r'(?i)total parameters[:*\s]*([0-9.,]+\s*[BMKT]\b)')
    ctx = find(t,
        r'"contextLength":\s*(\d+)',
        r'\*\*Context Length:?\*\*\s*(.{0,80})',
        r'(?i)context length is\s*([0-9,]+\s*tokens)',
        r'(?i)context of up to\s*([0-9,]+\s*tokens)',
        r'(?i)maximum context[:\s]*([0-9,]+\s*tokens)',
        r'(?i)context length[:\s]*([0-9,]+)',
        r'(?i)context window[:\s]*([0-9,]+)')
    lic_raw = section(t, 'License', 'Terms of Use', 'Governing Terms')
    lic = ', '.join(sorted({l for l in LIC if l.lower() in (lic_raw + t[:3000]).lower()})) or 'not stated'
    inp = find(t, r'\*\*Input Types?:\*\*\s*(.{0,120})', r'(?i)^#+\s*Input:?\s*\n(.{0,200})')
    outp = find(t, r'\*\*Output Types?:\*\*\s*(.{0,120})', r'(?i)^#+\s*Output:?\s*\n(.{0,200})')
    arch = find(t, r'\*\*Architecture Type:\*\*\s*(.{0,80})', r'\*\*Network Architecture:\*\*\s*(.{0,80})')
    desc = fm.get('description') or section(t, 'Description', 'Model Overview', 'Cosmos3 Nano')[:300]
    rows.append({
        'slug': slug, 'name': title,
        'publisher': fm.get('publisher') or 'nvidia',
        'canonical': fm.get('canonical') or f'https://build.nvidia.com/nvidia/{slug}',
        'description': desc, 'params': params,
        'active': find(t, r'\*\*Active Parameters:\*\*\s*(.{0,60})'),
        'context': ctx, 'input': inp, 'output': outp, 'arch': arch,
        'license': lic,
        'geography': re.sub(r'\s+', ' ', section(t, 'Deployment Geography'))[:40],
        'release': find(t, r'Release Date[:\s]*\n?(.{0,200})'),
        'source': 'model card md' if has_fm else 'embedded card (html shell)',
    })
json.dump(rows, open('_free_cards.json', 'w'), indent=1)
print(len(rows))
