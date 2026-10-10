p = 'extract.py'
s = open(p).read()
s = s.replace('r"^" + re.escape(t) + r"\\s*:?\\s*$"', 'r"^\\s*" + re.escape(t) + r"\\s*:?\\s*$"')
s = s.replace('"Description", "Model Overview", "Overview")', '"Description", "Model Overview", "Overview", "Model Information")')
s = s.replace('"Governing terms")', '"Governing terms") or kv(text, "License", "License, Acceptable Use")')
open(p, 'w').write(s)
print('patched', s.count('^\\s*"'))
