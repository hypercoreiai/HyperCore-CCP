p = 'extract.py'
s = open(p).read()
s = s.replace('''    rel = kv(section(text, "Release Date", "Release") or plain.get("Release Date", ""),
             "Build.NVIDIA.com", "HuggingFace", "Release Date")''',
'''    rel_block = section(text, "Release Date", "Release") or plain.get("Release Date", "")
    rel = kv(rel_block, "Build.NVIDIA.com", "HuggingFace", "Release Date")
    if not rel:
        m = re.search(r"(\\d{1,2}/\\d{1,2}/\\d{4})", rel_block)
        if m:
            rel = m.group(1)
    if not rel:
        m = re.search(r"released[^\\n]{0,40}?\\d{1,2}/\\d{1,2}/\\d{4}", text, re.I)
        if m:
            rel = re.search(r"\\d{1,2}/\\d{1,2}/\\d{4}", m.group(0)).group(0)''')
s = s.replace('''    if not inp:
        inp = kv(arch, "Input Type", "Input Modalities")
    if not out:
        out = kv(arch, "Output Type", "Output Modalities")''',
'''    if not inp:
        inp = kv(arch, "Input Type", "Input Modalities", "Input Format")
    if not out:
        out = kv(arch, "Output Type", "Output Modalities", "Output Format")''')
open(p, 'w').write(s)
