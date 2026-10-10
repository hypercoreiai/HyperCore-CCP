import json, re
rows = json.load(open('_free_cards.json'))
def cut(s, n):
    s = re.sub(r'\s+', ' ', s or '').strip()
    s = s.split('**')[0].strip()
    return (s[:n] + '…') if len(s) > n else (s or '—')
out = []
for r in sorted(rows, key=lambda x: (x['publisher'], x['slug'])):
    out.append(f"| {r['name'][:36]} | {r['publisher']} | {cut(r['params'],30)} | {cut(r['context'],26)} | {cut(r['input'],22)} → {cut(r['output'],18)} | {cut(r['license'],28)} |")
open('_free_endpoints_full.md','w').write('# NVIDIA NIM free-endpoint catalogue (38 cards)\n\n' + '\n'.join(out) + '\n')
print('\n'.join(out[:19]))
