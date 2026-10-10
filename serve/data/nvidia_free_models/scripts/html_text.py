import re, sys, html
def text(p):
    s=open(p,encoding='utf-8',errors='replace').read()
    s=re.sub(r'<script[\s\S]*?</script>',' ',s)
    s=re.sub(r'<style[\s\S]*?</style>',' ',s)
    s=re.sub(r'<[^>]+>','\n',s)
    s=html.unescape(s)
    s=re.sub(r'[ \t]+',' ',s)
    s=re.sub(r'\n\s*\n+','\n',s)
    return s.strip()
for slug in ['active-speaker-detection','bnr','body-pose','cosmos-transfer2_5-2b','cosmos3-nano','cosmos3-nano-reasoner','kumo-relational','kumo-tabular']:
    t=text(f'html_{slug}.html')
    open(f'text_{slug}.txt','w').write(t)
    print(slug, len(t))
