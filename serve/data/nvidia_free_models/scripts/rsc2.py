import re, glob

def unescape(s):
    s = s.replace('\\\\n', '\n').replace('\\n', '\n').replace('\\u003c', '<').replace('\\u003e', '>').replace('\\u0026','&')
    s = s.replace('\\\\', '\\').replace('\\"', '"')
    return s

for slug in ['body-pose','cosmos3-nano','cosmos3-nano-reasoner']:
    html = open('html_%s.html' % slug, encoding='utf-8', errors='replace').read()
    # find chunk header preceding the card
    i = html.find('Terms of Use')
    if i < 0:
        print(slug, 'nothing'); continue
    # walk back to the chunk id line
    start = html.rfind('\n', 0, max(0, i-2000))
    end = html.find('\n', i+15000)
    if end < 0: end = i+20000
    txt = unescape(html[start:end])
    open('card_%s.txt' % slug, 'w').write(txt)
    print('==', slug, len(txt))
    print(txt[:600].replace('\n',' | '))
