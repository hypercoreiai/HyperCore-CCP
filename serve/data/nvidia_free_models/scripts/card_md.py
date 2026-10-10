import re, json, sys

def find_md(raw, key="Model Overview"):
    i = raw.find(key)
    if i < 0: return None
    # walk back to the start of the JSON string literal
    start = raw.rfind('"', 0, i)
    if start < 0: return None
    # find end of string literal (unescaped quote)
    j = start + 1
    out = []
    while j < len(raw):
        c = raw[j]
        if c == '\\':
            out.append(raw[j:j+2]); j += 2; continue
        if c == '"':
            break
        out.append(c); j += 1
    s = ''.join(out)
    try:
        s = json.loads('"' + s + '"')
    except Exception:
        s = s.replace('\\n', '\n').replace('\\"', '"').replace('\\/', '/')
    return s

for slug in ['active-speaker-detection','bnr','body-pose','cosmos-transfer2_5-2b','cosmos3-nano','cosmos3-nano-reasoner','kumo-relational','kumo-tabular']:
    raw = open(f'html_{slug}.html', encoding='utf-8', errors='replace').read()
    md = find_md(raw)
    if md:
        open(f'card_{slug}.md', 'w').write(md)
        print(slug, len(md))
    else:
        print(slug, 'NOT FOUND')
