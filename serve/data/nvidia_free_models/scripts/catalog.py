import re, json, os

def dec(s):
    if s.lstrip().startswith('<'):
        s = s.replace('\\\\n','\n').replace('\\n','\n').replace('\\u003c','<').replace('\\u003e','>').replace('\\u0026','&').replace('\\\\','\\').replace('\\"','"')
    return s

specs = json.load(open('_specs.json'))

TASK = {
 'deepseek-v4.1-flash':'Multimodal reasoning LLM (MoE)',
 'diffusiongemma-26b-a4b-it':'Multimodal LLM (diffusion decoding)',
 'gemma-4-31b-it':'Multimodal instruction LLM',
 'google-paligemma':'Vision-language (caption/VQA)',
 'llama-3.2-11b-vision-instruct':'Vision-language',
 'llama-3.2-90b-vision-instruct':'Vision-language',
 'llama-guard-4-12b':'Safety guardrail',
 'muse-glimmer-30b':'Vision-language (multimodal encoder)',
 'kimi-k3':'Multimodal reasoning LLM (MoE)',
 'active-speaker-detection':'Speaker diarisation / lip reading',
 'bevformer':'BEV 3D object detection',
 'bnr':'Audio background-noise removal',
 'body-pose':'3D human pose estimation',
 'cosmos3-nano':'World model (video/action generation)',
 'cosmos3-nano-reasoner':'Vision-language reasoning (VLM)',
 'ising-calibration-1-35b-a3b':'VLM for quantum-calibration charts',
 'ising-calibration-1.5-31b':'VLM for quantum-calibration charts',
 'kumo-relational':'Relational/tabular prediction',
 'kumo-tabular':'Tabular in-context prediction',
 'magpie-tts-zeroshot':'Text-to-speech (zero-shot voice)',
 'nemotron-3-embed-1b':'Embeddings',
 'nemotron-3-nano-omni-30b-a3b-reasoning':'Omni multimodal reasoning (MoE)',
 'nemotron-3-super-120b-a12b':'Reasoning LLM (MoE)',
 'nemotron-3-ultra-550b-a55b':'Reasoning LLM (MoE)',
 'nemotron-3.5-content-safety':'Content safety / toxicity guardrail',
 'nemotron-3.5-lightning-30b-a3b':'Reasoning LLM (MoE)',
 'nemotron-voicechat':'Speech-to-speech chat',
 'riva-translate-4b-instruct-v2':'Machine translation',
 'sparsedrive':'Sparse 3D scene perception (driving)',
 'streampetr':'Streaming 3D detection/tracking (driving)',
 'studiovoice':'Audio noise suppression',
 'synthetic-video-detector':'Synthetic-vs-real video classifier',
 'gpt-oss-20b':'Reasoning LLM (open weights)',
 'laguna-xs-2.1':'Coding LLM',
 'glm-5-3':'Reasoning LLM',
 'glm-5-3-flash':'Multimodal reasoning LLM',
 'cosmos-transfer2_5-2b':'Video-to-video transfer (world model)',
 'llama-3_1-nemotron-safety-guard-8b-v3':'Content-safety guardrail',
}
MANUAL = {
 'active-speaker-detection': ('65.2M (ASD) / 3.9M (10 GFLOPS variant) / 840K (lip reading)', 'Video, Image', 'Speaker labels, 512-d face embeddings, scores'),
 'bevformer': ('not stated', 'RGB images, vehicle state, camera extrinsics', 'Labels (text string)'),
 'bnr': ('~60M', 'Audio', 'Audio'),
 'body-pose': ('not stated in card', 'Video (RGB)', '3D skeleton (33 joints, SOMA 276-joint topology)'),
 'cosmos3-nano': ('15.75B', 'Text, Image, Video + spatial controls', 'Images, video, action arrays'),
 'cosmos3-nano-reasoner': ('not stated in card', 'Text, Image, Video', 'Text'),
 'kumo-relational': ('31M', 'Tabular (multi-table)', 'JSON predictions'),
 'kumo-tabular': ('28M (Small) / 62M (Medium) / 215M (Large)', 'Tabular', 'JSON predictions'),
 'magpie-tts-zeroshot': ('not stated', 'Text', 'Audio (wav, 22.05 kHz, <=20 s)'),
 'nemotron-voicechat': ('not stated', 'Audio (PCM), Text', 'Audio (PCM)'),
 'sparsedrive': ('not stated', 'Multi-view camera images + intrinsics/extrinsics', 'Labeled 3D bounding boxes, BEV embeddings, lane geometry'),
 'streampetr': ('not stated (Undisclosed)', '6x RGB 256x704 + camera intrinsics/extrinsics', '3D bounding boxes, agent attributes, BEV embeddings'),
 'studiovoice': ('not stated', 'Audio', 'Audio'),
 'synthetic-video-detector': ('172M', 'Video', 'Score / label'),
 'cosmos-transfer2_5-2b': ('2.36B', 'Text + Video/Image', 'Video'),
 'llama-3_1-nemotron-safety-guard-8b-v3': ('8.03B', 'Text', 'Text (toxicity/safety labels)'),
 'google-paligemma': ('2.92B', 'Text, Image', 'Text'),
 'llama-guard-4-12b': ('12B', 'Text, Image', 'Text'),
 'nemotron-3-embed-1b': ('~1.14B', 'Text', '2048-d float vectors'),
}

rows = []
for slug in TASK:
    sp = specs.get(slug, {}).get('spec', [])
    params = ctx = inm = outm = ''
    if sp:
        s = sp[0].replace('\\\\','')
        p = re.search(r'"parameters":(\d+)', s)
        if p:
            n = int(p.group(1)); params = f"{n/1e9:.1f}B" if n>=1e9 else f"{n/1e6:.0f}M"
        c = re.search(r'"contextLength":(\d+)', s)
        if c: ctx = f"{int(c.group(1)):,}"
        mi = re.search(r'"inputModalities":\[(.*?)\]', s); mo = re.search(r'"outputModalities":\[(.*?)\]', s)
        if mi: inm = mi.group(1).replace('"','')
        if mo: outm = mo.group(1).replace('"','')
    if slug in MANUAL:
        if not params: params = MANUAL[slug][0]
        if not inm: inm = MANUAL[slug][1]
        if not outm: outm = MANUAL[slug][2]
    rows.append((slug, params, ctx, inm, outm))

json.dump(rows, open('_catalog_rows.json','w'), indent=1)
for r in rows: print(f"{r[0]:34} {r[1]:32} {r[2]:12} {r[3][:40]:40} -> {r[4][:30]}")
