import re
def unescape(s):
    s = s.replace('\\\\n', '\n').replace('\\n', '\n').replace('\\u0026','&').replace('\\u003c','<').replace('\\u003e','>').replace('\\u003','<').replace('\\u003e','>')
    s = s.replace('\\\\','\\').replace('\\"','"')
    return s
for slug in ['body-pose','cosmos3-nano','cosmos3-nano-reasoner']:
    h = open('html_%s.html'%slug, encoding='utf-8', errors='replace').read()
    m = re.search(r'(License/Terms of Use|License and Terms of Use|Intended Application)', h)
    i = m.start()
    txt = unescape(h[max(0,i-4000): i+22000])
    txt = re.sub(r'<[^>]{0,200}>', '', txt)
    open('card_%s.txt'%slug,'w').write(txt)
    print('===', slug, len(txt))
    for pat in ['Model Size','Model Parameters','Parameters','Context Length','Architecture','Input Type','Output Type','Deployment Geography','Release Date','Model Version','Network Architecture']:
        for mm in re.finditer(pat, txt, re.I):
            print(' ', pat, '->', txt[mm.start():mm.start()+120].replace('\n',' ')[:120])
            break
