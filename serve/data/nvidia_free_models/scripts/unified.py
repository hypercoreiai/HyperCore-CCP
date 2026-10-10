import re, json, glob, os

def decode(s):
    if s.lstrip().startswith('<'):
        s = s.replace('\\\\n','\n').replace('\\n','\n').replace('\\u0026','&').replace('\\u003c','<').replace('\\u003e','>').replace('\\\\','\\').replace('\\"','"')
    return s

def card_region(s):
    for pat in ['# Model Overview','## Model Overview','## Description','Intended Application','License/Terms of Use','License and Terms of Use']:
        i = s.find(pat)
        if i >= 0:
            m = re.search(r'\n\d{2}[A-Za-z]:', s[i:])
            end = i + m.start() if m else i + 30000
            return s[i:end]
    return ''

def sections(md):
    out = {}; cur=None; buf=[]
    for ln in md.split('\n'):
        m = re.match(r'^(#{1,4})\s*(.+?)\s*$', ln)
        if m:
            if cur: out[cur]='\n'.join(buf).strip()
            cur=m.group(1).strip(); buf=[]
        elif cur: buf.append(ln)
    if cur: out[cur]='\n'.join(buf).strip()
    return out

def get(sec, *keys):
    for k in keys:
        for h,v in sec.items():
            if h.lower().startswith(k.lower()) or k.lower() in h.lower():
                return v
    return ''

def find(text, *pats):
    for p in pats:
        m = re.search(p, text, re.I|re.S)
        if m: return m.group(1).strip()
    return ''

slugs = [l.strip().split('/')[-1] for l in open('/home/ai-user0/_card_urls.txt') if l.strip()]
slugs += ['cosmos-transfer2_5-2b','llama-3_1-nemotron-safety-guard-8b-v3']
out = []
for slug in slugs:
    raw = ''
    for cand in [slug+'.md', 'card_'+slug+'.txt', 'card_'+slug+'.md']:
        if os.path.exists(cand):
            raw = open(cand, encoding='utf-8', errors='replace').read(); break
    dec = decode(raw)
    region = card_region(dec)
    sec = sections(region)
    arch = get(sec,'Model Architecture','Architecture Type','Model Architecture:')
    rec = {
      'slug': slug,
      'name': find(dec, r'<title>(.*?)</title>') or slug,
      'card_chars': len(region),
      'desc': find(region, r'(?i)description[:\n]{1,3}(.{0,300})') or find(dec, r'<meta name="description" content="([^"]{0,300})'),
      'params': find(arch + ' ' + get(sec,'Model Size','Model Size:'), r'(?i)(?:model size|total parameters|parameters)[:\s*]{1,4}([0-9][^\n|]{0,40})'),
      'active': find(arch, r'(?i)active parameters[:\s*]{1,4}([0-9][^\n|]{0,20})'),
      'context': find(arch, r'(?i)context length[:\s*]{1,4}([0-9][^\n|]{0,20})'),
      'archtype': find(arch, r'(?i)architecture type[:\s*]{1,4}([^\n|]{0,80})'),
      'input': find(region, r'(?i)input type\(s\)[:\s*]{1,4}([^\n]{0,120})'),
      'output': find(region, r'(?i)output type\(s\)[:\s*]{1,4}([^\n]{0,120})'),
      'license': re.sub(r'\[|\]\(.*?\)','', get(sec,'License','Terms of Use'))[:300],
      'geo': get(sec,'Deployment Geography')[:60],
      'release': re.sub(r'\[|\]\(.*?\)','', get(sec,'Release Date'))[:200],
    }
    out.append(rec)
json.dump(out, open('_unified.json','w'), indent=1)
for r in out:
    print(f"{r['slug']:34} card={r['card_chars']:5} params={r['params'][:22]:22} ctx={r['context']:12} in={r['input'][:28]:28} out={r['output'][:22]}")
