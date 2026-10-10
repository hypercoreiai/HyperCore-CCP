import re, json, sys, glob

def unescape(s):
    # payload is JSON-escaped twice in the HTML
    s = s.replace('\\\\n', '\n').replace('\\n', '\n').replace('\\\\"', '"').replace('\\"', '"').replace('\\\\', '\\')
    return s

def card_text(html):
    i = html.find('# Model Overview')
    if i < 0:
        return None
    # take until the next RSC chunk boundary line
    j = html.find('\n', i)
    # scan forward for a line-start chunk id pattern like "\n3f:" or end of payload
    m = re.search(r'\n\d{2}[a-z]:', html[i:])
    end = i + m.start() if m else i + 20000
    return unescape(html[i:end])

for f in sorted(glob.glob('html_*.html')):
    t = card_text(open(f, encoding='utf-8', errors='replace').read())
    name = f[5:-5]
    out = 'card_%s.txt' % name
    if t:
        open(out, 'w').write(t)
        print('==', name, len(t))
        print(t[:400].replace('\n', ' | '))
    else:
        print('==', name, 'NO CARD')
