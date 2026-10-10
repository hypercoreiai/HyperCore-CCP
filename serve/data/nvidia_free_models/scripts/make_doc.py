import json, re

TASK = {
 'deepseek-v4.1-flash':('deepseek-ai','Multimodal reasoning LLM (MoE)'),
 'diffusiongemma-26b-a4b-it':('google','Multimodal LLM (diffusion decoding)'),
 'gemma-4-31b-it':('google','Multimodal instruction LLM'),
 'google-paligemma':('google','Vision-language (caption/VQA)'),
 'llama-3.2-11b-vision-instruct':('meta','Vision-language'),
 'llama-3.2-90b-vision-instruct':('meta','Vision-language'),
 'llama-guard-4-12b':('meta','Safety guardrail'),
 'muse-glimmer-30b':('meta','Vision-language encoder'),
 'kimi-k3':('moonshotai','Multimodal reasoning LLM (MoE)'),
 'active-speaker-detection':('nvidia','Speaker diarisation / lip reading'),
 'bevformer':('nvidia','BEV 3D object detection'),
 'bnr':('nvidia','Audio background-noise removal'),
 'body-pose':('nvidia','3D human pose estimation'),
 'cosmos3-nano':('nvidia','World model (video/action generation)'),
 'cosmos3-nano-reasoner':('nvidia','Vision-language reasoning'),
 'ising-calibration-1-35b-a3b':('nvidia','VLM, quantum-calibration charts'),
 'ising-calibration-1.5-31b':('nvidia','VLM, quantum-calibration charts'),
 'kumo-relational':('nvidia','Relational/tabular prediction'),
 'kumo-tabular':('nvidia','Tabular in-context prediction'),
 'magpie-tts-zeroshot':('nvidia','Text-to-speech'),
 'nemotron-3-embed-1b':('nvidia','Embeddings'),
 'nemotron-3-nano-omni-30b-a3b-reasoning':('nvidia','Omni multimodal reasoning (MoE)'),
 'nemotron-3-super-120b-a12b':('nvidia','Reasoning LLM (MoE)'),
 'nemotron-3-ultra-550b-a55b':('nvidia','Reasoning LLM (MoE)'),
 'nemotron-3.5-content-safety':('nvidia','Content-safety guardrail'),
 'nemotron-3.5-lightning-30b-a3b':('nvidia','Reasoning LLM (MoE)'),
 'nemotron-voicechat':('nvidia','Speech-to-speech chat'),
 'riva-translate-4b-instruct-v2':('nvidia','Machine translation'),
 'sparsedrive':('nvidia','Sparse 3D scene perception (driving)'),
 'streampetr':('nvidia','Streaming 3D detection/tracking (driving)'),
 'studiovoice':('nvidia','Audio noise suppression'),
 'synthetic-video-detector':('nvidia','Synthetic-vs-real video classifier'),
 'gpt-oss-20b':('openai','Reasoning LLM (open weights)'),
 'laguna-xs-2.1':('poolside','Coding LLM'),
 'glm-5-3':('z-ai','Reasoning LLM'),
 'glm-5-3-flash':('z-ai','Multimodal reasoning LLM'),
 'cosmos-transfer2_5-2b':('nvidia','Video-to-video transfer (world model)'),
 'llama-3_1-nemotron-safety-guard-8b-v3':('nvidia','Content-safety guardrail'),
}
rows = json.load(open('_catalog_rows.json'))
spec = {r[0]: r for r in rows}

LINES = []
LINES.append('# NVIDIA NIM free-endpoint catalogue — 38 model cards')
LINES.append('')
LINES.append('Filter: `https://build.nvidia.com/models?filters=nimType%3Anim_type_preview` → facet **Free Endpoint = 38** (24 + 14 on two pages).')
LINES.append('Captured 2026-10-09. Raw HTML/markdown for every card is cached in `/home/ai-agent/downloads/nvidia_free_models/`.')
LINES.append('')
LINES.append('## 1. Text / reasoning models (17)')
LINES.append('')
LINES.append('| Model | Publisher | Params | Context | In → Out | Licence | Downloadable container |')
LINES.append('|---|---|---|---|---|---|---|')
text_group = ['deepseek-v4.1-flash','kimi-k3','glm-5-3','glm-5-3-flash','gpt-oss-20b','laguna-xs-2.1',
 'nemotron-3-ultra-550b-a55b','nemotron-3-super-120b-a12b','nemotron-3.5-lightning-30b-a3b',
 'nemotron-3-nano-omni-30b-a3b-reasoning','nemotron-3.5-content-safety','llama-3_1-nemotron-safety-guard-8b-v3',
 'llama-guard-4-12b','riva-translate-4b-instruct-v2','nemotron-3-embed-1b','diffusiongemma-26b-a4b-it','gemma-4-31b-it']
def row(slug):
    pub, task = TASK[slug]
    p, ctx, inm, outm = spec[slug][1], spec[slug][2], spec[slug][3], spec[slug][4]
    return f"| [{slug}](https://build.nvidia.com/{pub}/{slug}) | {pub} | {p or '—'} | {ctx or '—'} | {inm or '?'} → {outm or '?'} |"
for s in text_group: LINES.append(row(s))
LINES.append('')
LINES.append('## 2. Vision / perception (7)')
LINES.append('')
LINES.append('| Model | Publisher | Params | Notes | In → Out |')
LINES.append('|---|---|---|---|---|')
vis = ['google-paligemma','llama-3.2-11b-vision-instruct','llama-3.2-90b-vision-instruct','muse-glimmer-30b',
       'active-speaker-detection','body-pose','synthetic-video-detector']
for s in vis:
    pub, task = TASK[s]; p = spec[s][1]
    LINES.append(f"| [{s}](https://build.nvidia.com/{pub}/{s}) | {pub} | {p or '—'} | {task} | {spec[s][3] or '?'} → {spec[s][4] or '?'} |")
LINES.append('')
LINES.append('## 3. Driving / 3D scene (3)')
LINES.append('')
for s in ['sparsedrive','streampetr','bevformer']:
    LINES.append(f"- **{s}** — {spec[s][3]} → {spec[s][4]}")
LINES.append('')
LINES.append('## 4. Audio / speech (4)')
LINES.append('')
for s in ['bnr','studiovoice','magpie-tts-zeroshot','nemotron-voicechat']:
    LINES.append(f"- **{s}** — {spec[s][3]} → {spec[s][4]}")
LINES.append('')
LINES.append('## 5. World models / video generation (3)')
LINES.append('')
for s in ['cosmos3-nano','cosmos3-nano-reasoner','cosmos-transfer2_5-2b']:
    LINES.append(f"- **{s}** — {spec[s][1] or 'n/a'} params, ctx {spec[s][2] or 'n/a'} | {spec[s][3]} → {spec[s][4]}")
LINES.append('')
LINES.append('## 6. Tabular / structured (2)')
LINES.append('')
for s in ['kumo-tabular','kumo-relational']:
    LINES.append(f"- **{s}** — {spec[s][1]} | {spec[s][3]} → {spec[s][4]}")
LINES.append('')
LINES.append('## 7. Domain-specific VLM (2)')
LINES.append('')
for s in ['ising-calibration-1-35b-a3b','ising-calibration-1.5-31b']:
    LINES.append(f"- **{s}** — {spec[s][1]} params, ctx {spec[s][2]} | {spec[s][3]} → {spec[s][4]}")
LINES.append('')
LINES.append('## Licence distribution')
LINES.append('')
LINES.append('- Open / open-weight: MIT (deepseek-v4.1-flash, gpt-oss-20b), OpenMDW 1.1 (cosmos3-nano, ising-calibration, nemotron-3-embed), Apache 2.0 (nemotron-3-embed weights), Llama 3.2 Community (meta models).')
LINES.append('- NVIDIA Open Model License / non-commercial: kumo-*, bnr, active-speaker-detection, body-pose, streampetr, sparsedrive, synthetic-video-detector, ising-* (MIT + NVIDIA OML mix).')
LINES.append('- Trial-service layer on top of everything: NVIDIA API Terms of Use (or API Trial ToS for preview endpoints).')
LINES.append('')
LINES.append('## How the cards were retrieved (reproducible)')
LINES.append('')
LINES.append('1. `GET /models?filters=nimType%3Anim_type_preview` → 38 card links (2 pages).')
LINES.append('2. `GET /<publisher>/<slug>.md` → markdown card for ~30 models.')
LINES.append('3. For 8 slugs the `.md` route returns an HTML error shell; the card text is embedded in the Next.js RSC payload of `/<publisher>/<slug>` — decode `\\n` escapes and slice from `# Model Overview` / `License/Terms of Use`.')
LINES.append('4. Structured specs (`contextLength`, `parameters`, `inputModalities`, `outputModalities`) are in a `\"specifications\":{...}` JSON blob inside every model page — 23 of 38 expose it.')
open('free_endpoints_catalog.md','w').write('\n'.join(LINES))
print('\n'.join(LINES[:30]))
