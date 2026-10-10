import json, re
rows = json.load(open('_free_cards.json'))
def clean(s, n=40):
    s = re.sub(r'\*\*.*', '', s) if '**' in s else s
    s = re.sub(r'\s+', ' ', s).strip()
    return s[:n] or '—'
def short(s, n=28):
    s = re.sub(r'\s+', ' ', s or '').strip()
    return (s[:n] + '…') if len(s) > n else (s or '—')
hdr = "| # | Model | Publisher | Params | Context | Input → Output | License | Released | Card source |"
sep = "|---|---|---|---|---|---|---|---|---|"
lines = [hdr, sep]
for i, r in enumerate(sorted(rows, key=lambda x: (x['publisher'], x['slug'])), 1):
    inp = clean(r['input'], 26); out = clean(r['output'], 22)
    lines.append(f"| {i} | {short(r['name'],34)} | {r['publisher']} | {short(r['params'],32)} | {short(r['context'],28)} | {inp} → {out} | {short(r['license'],34)} | {short(r['release'].split('via')[0],24)} | {r['source']} |")
open('_free_endpoints_full.md','w').write('# NVIDIA NIM free-endpoint catalogue (nimType:nim_type_preview)\n\n' + '\n'.join(lines) + '\n')
print('\n'.join(lines))
