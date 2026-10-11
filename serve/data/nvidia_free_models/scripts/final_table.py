import json, re

rows = json.load(open('_final_cards.json'))

def norm_params(p):
    if not p: return ''
    p = p.replace('<br>', ' ')
    m = re.search(r'(\d[\d,.]*\s*(?:B|T|M|K))', p)
    if m: return m.group(1)
    m = re.search(r'(\d{6,})', p)
    if m:
        n = int(m.group(1))
        return f"{n/1e9:.1f}B" if n > 1e8 else f"{n/1e6:.0f}M"
    return p[:30]

def norm_ctx(c):
    if not c: return ''
    m = re.search(r'([\d,]{4,})', c)
    return m.group(1) if m else ''

def task_type(r):
    d = (r['desc'] + ' ' + r.get('input','') + ' ' + r.get('output','')).lower()
    slug = r['slug']
    if 'embed' in slug: return 'Embeddings'
    if any(k in d for k in ['speech-to-text','asr','transcri']): return 'Speech ASR'
    if any(k in d for k in ['tts','voice','text-to-speech','noise','audio']): return 'Speech / Audio'
    if any(k in d for k in ['tabular','relational']): return 'Tabular / Structured'
    if any(k in d for k in ['bird','autonomous driving','camera','pose','speaker','detect','segment','gaze','video input','3d']): 
        if 'world' in d or 'generates' in d: return 'World / Video generation'
        return 'Vision / Perception'
    if any(k in d for k in ['video','image','vision-language','multimodal']): return 'Vision-language'
    if any(k in d for k in ['world','physics','video']): return 'World / Video generation'
    if any(k in d for k in ['safety','guard','toxicity']): return 'Safety / Guardrail'
    return 'LLM / Reasoning'

def lic_short(l):
    l = l or ''
    out = []
    for k in ['OpenMDW','MIT','Apache 2.0','Llama 3.2 Community','NVIDIA Open Model','NVIDIA Software License','NVIDIA API Trial','Open Model License','proprietary']:
        if k.lower() in l.lower(): out.append(k)
    return ', '.join(dict.fromkeys(out)) or 'not stated'

def in_out(r):
    i = r.get('input','') or ''
    o = r.get('output','') or ''
    def mod(s):
        s = s.lower()
        found = []
        for k in ['text','image','video','audio','tabular','json','label','embedding','string']:
            if k in s and k not in found: found.append(k)
        return found
    mi, mo = mod(i), mod(o)
    if not mi and not mo: return ''
    return ('+'.join(mi) or '?') + ' -> ' + ('+'.join(mo) or '?')

order = ['deepseek-ai','google','meta','moonshotai','openai','poolside','z-ai','nvidia']
rows.sort(key=lambda r: (order.index(r['publisher']) if r['publisher'] in order else 99, r['slug']))

lines = []
lines.append('# NVIDIA NIM — free-endpoint model cards (38)')
lines.append('')
lines.append('Source: https://build.nvidia.com/models?filters=nimType%3Anim_type_preview  (facet "Free Endpoint" = 38)')
lines.append('All cards fetched 2026-10-09. Raw cards cached in /home/ai-agent/downloads/nvidia_free_models/')
lines.append('')
lines.append('| # | Model | Publisher | Task | Parameters | Active | Context | Modality in -> out | License | Release |')
lines.append('|---|-------|-----------|------|------------|--------|---------|------------------|---------|---------|')
for n, r in enumerate(rows, 1):
    act = ''
    src = r.get('params','')
    m = re.search(r'[Aa]ctive[^:]*:\s*([0-9][^\s<|]*)', src)
    if m: act = m.group(1)
    lines.append('| %d | [%s](%s) | %s | %s | %s | %s | %s | %s | %s | %s |' % (
        n, r['name'] or r['slug'], r['url'], r['publisher'], task_type(r),
        norm_params(r.get('params','')), act, norm_ctx(r.get('context','')),
        in_out(r), lic_short(r.get('license','')), (r.get('release') or '')[:60]))
lines.append('')

# summary
from collections import Counter
pub = Counter(r['publisher'] for r in rows)
tk = Counter(task_type(r) for r in rows)
lic = Counter(lic_short(r.get('license','')) for r in rows)
lines.append('## Counts')
lines.append('Publishers: ' + ', '.join(f'{k} {v}' for k, v in pub.most_common()))
lines.append('Task types: ' + ', '.join(f'{k} {v}' for k, v in tk.most_common()))
lines.append('Licences: ' + ', '.join(f'{k} {v}' for k, v in lic.most_common()))
lines.append('')
lines.append('## Notes on retrieval')
lines.append('- 30 of 38 cards are served as markdown at `<publisher>/<slug>.md`.')
lines.append('- 8 cards (`active-speaker-detection, bnr, body-pose, cosmos-transfer2_5-2b, cosmos3-nano, cosmos3-nano-reasoner, kumo-relational, kumo-tabular`) return an HTML shell for the .md path; their card text is embedded in the Next.js RSC payload of the page and was recovered by decoding that payload.')
lines.append('- `body-pose`, `cosmos3-nano`, `cosmos3-nano-reasoner` state no parameter count in the card.')
open('_free_endpoints_full.md','w').write('\n'.join(lines))
print('\n'.join(lines[:45]))
