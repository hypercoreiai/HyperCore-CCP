import re
def decode(s):
    return s.replace('\\\\n','\n').replace('\\n','\n').replace('\\u0026','&').replace('\\u003c','<').replace('\\u003e','>').replace('\\\\','\\').replace('\\"','"')
for t in ['magpie-tts-zeroshot','studiovoice','nemotron-voicechat','synthetic-video-detector','riva-translate-4b-instruct-v2']:
    s = decode(open('html_%s.html'%t, encoding='utf-8', errors='replace').read())
    hits = [m.start() for m in re.finditer(r'(Model Overview|Input Type|Model Size|Architecture Type|License/Terms|License and Terms|Intended Use|Description)', s)]
    print('=====', t, 'hits', len(hits))
    if hits:
        i = hits[0]
        region = s[i:i+6000]
        open('card_%s.txt'%t,'w').write(region)
        for pat in ['Model Size','Parameters','Context Length','Input Type','Output Type','Architecture Type','Release Date','Deployment Geography','License']:
            m = re.search(pat, region, re.I)
            if m: print('  ', pat, '->', region[m.start():m.start()+140].replace('\n',' ')[:140])
