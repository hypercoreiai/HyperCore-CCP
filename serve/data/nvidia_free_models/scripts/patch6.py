p = 'extract.py'
s = open(p).read()

helper = '''def page_title(raw):
    m = re.search(r"<title>([^<]+)</title>", raw, re.I)
    if not m:
        m = re.search(r'og:title" content="([^"]+)"', raw)
    if not m:
        return ''
    t = html.unescape(m.group(1)).strip()
    t = re.sub(r'\\s*\\|\\s*NVIDIA.*$', '', t)
    t = re.sub(r'\\s+Model by NVIDIA$', '', t)
    return t.strip()

'''
s = s.replace('def load(slug):', helper + 'def load(slug):')

old = s[s.index('    title = fm.get('):s.index('    publisher = fm.get(')]
new = '''    title = ''
    for line in text.splitlines():
        if line.startswith('# '):
            t = line[2:].strip()
            if t and not re.match(r'(model overview|overview|description)$', t, re.I):
                title = t
                break
    if not title:
        title = fm.get('title', '')
    if not title or title == slug:
        raw = open(os.path.join(BASE, slug + '.md'), encoding='utf-8', errors='replace').read()
        title = page_title(raw) or slug
'''
s = s.replace(old, new)
open(p, 'w').write(s)
