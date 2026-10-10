import re, json, urllib.request, os, time

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
slugs = [l.strip().split('/')[-1] for l in open('/home/ai-user0/_card_urls.txt') if l.strip()]
slugs += ['cosmos-transfer2_5-2b','llama-3_1-nemotron-safety-guard-8b-v3']

def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    return urllib.request.urlopen(req, timeout=25).read().decode('utf-8','replace')

out = {}
for s in slugs:
    fn = 'page_%s.html' % s
    if os.path.exists(fn):
        h = open(fn, encoding='utf-8', errors='replace').read()
    else:
        for u in ['https://build.nvidia.com/nvidia/%s' % s]:
            try:
                h = get(u); open(fn,'w').write(h)
            except Exception as e:
                print('fail', s, e); h=''; break
        time.sleep(0.3)
    spec = re.search(r'"specifications":\{([^}]*)\}', h)
    rec = {'slug': s, 'spec': spec.group(1) if spec else ''}
    m = re.search(r'<title>(.*?)</title>', h); rec['title'] = m.group(1) if m else ''
    m = re.search(r'"downloadAvailable":(true|false)', h); rec['downloadable'] = m.group(1) if m else ''
    out[s] = rec
    print(s, '|', rec['spec'][:80], '| dl=', rec['downloadable'])
json.dump(out, open('_specs.json','w'), indent=1)
