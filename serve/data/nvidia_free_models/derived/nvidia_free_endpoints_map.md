# NVIDIA NIM — free-endpoint model cards (filter nimType:nim_type_preview)

Captured 2026-10-09. 38 cards, all fetched and parsed locally.

Sources: 25 cards = markdown at build.nvidia.com/<org>/<slug>.md; 8 cards = markdown recovered from the embedded JSON blob in the HTML shell; 5 = no published model card, page metadata only.


## llm_reasoning (12)

| Model | Publisher | Params | Context | Input → Output | License |
|---|---|---|---|---|---|
| deepseek-v4.1-flash | deepseek-ai | 552B | 1,048,576 tokens - | Image, Text → Text | MIT License, Non-commercial, O… |
| kimi-k3 | moonshotai | 2.8T | 1,048,576 tokens - | Text, Image → Text | MIT License, Non-commercial, O… |
| glm-5-3 | z-ai | 753B total, ~40B activated… | 1,048,576 tokens - | — → — | not stated |
| glm-5-3-flash | z-ai | 320B total, 18B activated … | 1,048,576 tokens - | — → — | MIT License |
| laguna-xs-2.1 | poolside | 33B | 262,144 tokens - | Text → Text | Non-commercial, OpenMDW |
| gpt-oss-20b | openai | 20B <br> | 131,072 tokens - | — → — | Apache 2.0, Non-commercial |
| nemotron-3-super-120b-a12b | nvidia | 120B Total / 12B Active | | Up to 1M tokens | | | — → — | Open Model License |
| nemotron-3-ultra-550b-a55b | nvidia | 550B Total / 55B Active | | Up to 1M tokens | | | — → — | OpenMDW |
| nemotron-3.5-lightning-30b-a3b | nvidia | 30B Total / 3B Active | | Up to 1M tokens | | | — → — | OpenMDW |
| nemotron-3.5-content-safety | nvidia | 4 Billion (4B) * | 131,072 tokens - | — → — | OpenMDW |
| ising-calibration-1-35b-a3b | nvidia | ~35B total parameters, ~3B… | 262,144 tokens - | — → — | Non-commercial, Open Model Lic… |
| ising-calibration-1.5-31b | nvidia | Approximately 31B | 262,144 tokens - | — → — | OpenMDW |

## multimodal_vision_language (8)

| Model | Publisher | Params | Context | Input → Output | License |
|---|---|---|---|---|---|
| diffusiongemma-26b-a4b-it | google | 25.2B | 262,144 tokens - | Text, Image, Video → Text | Apache 2.0, Non-commercial, Op… |
| gemma-4-31b-it | google | 30.7B | 262,144 tokens - | Text, Image, Video → Text | Non-commercial, Open Model Lic… |
| paligemma | google | 2,923,466,480 | 8,192 tokens - | — → — | not stated |
| llama-3.2-11b-vision-instruct | meta | 10,670,220,835 | 131,072 tokens - | — → — | Llama 3.2 Community License |
| llama-3.2-90b-vision-instruct | meta | 88,593,355,323 | 131,072 tokens - | — → — | Llama 3.2 Community License |
| llama-guard-4-12b | meta | 12,001,097,216 | 163,840 tokens - | — → — | Non-commercial |
| muse-glimmer-30b | meta | 29.6B | 131,072 tokens - | Text, Image → Text | Non-commercial, Open Model Agr… |
| cosmos3-nano-reasoner | nvidia | — | — | — → — | OpenMDW |

## embeddings_safety (2)

| Model | Publisher | Params | Context | Input → Output | License |
|---|---|---|---|---|---|
| nemotron-3-embed-1b | nvidia | ~1.14B <br> | 32,768 tokens - | — → — | OpenMDW |
| llama-3.1-nemotron-safety-guard-8b-v3 | nvidia | 8.03B | 8,192 tokens - | Text <br> → — | Open Model License |

## speech_audio (5)

| Model | Publisher | Params | Context | Input → Output | License |
|---|---|---|---|---|---|
| Background Noise Removal | nvidia | ~60M | — | — → — | Open Model License |
| Magpie TTS Zeroshot | nvidia | — | — | Text → Audio (speech) | NVIDIA AI Foundation Models Co… |
| Nemotron 3 VoiceChat | nvidia | — | — | Audio/Text → Audio | NVIDIA Software and Model Eval… |
| Riva Translate 4B Instruct v2 | nvidia | — | — | Text → Text | NVIDIA Open Model License Agre… |
| Studio Voice | nvidia | — | — | Audio → Audio | NVIDIA Open Model License |

## video_generation_world_models (3)

| Model | Publisher | Params | Context | Input → Output | License |
|---|---|---|---|---|---|
| cosmos-transfer2.5-2b | nvidia | 2,358,047,744 | — | — → — | Non-commercial, Open Model Lic… |
| cosmos3-nano | nvidia | 15750057456 | 262144 | — → — | NVIDIA Software License, OpenM… |
| Synthetic Video Detector | nvidia | — | — | Video → label | NVIDIA Software and Model Eval… |

## perception_sensing (5)

| Model | Publisher | Params | Context | Input → Output | License |
|---|---|---|---|---|---|
| Active Speaker Detection | nvidia | 65.2M | — | Image → — | NVIDIA Software License, Non-c… |
| bevformer | nvidia | — | — | Multi-view Camera imag… → Labels - | Apache 2.0, Non-commercial |
| 3D Body Pose | nvidia | — | — | — → — | Open Model License |
| sparsedrive | nvidia | — | — | — → — | MIT License, Non-commercial |
| streampetr | nvidia | Undisclosed | — | Multi-view camera imag… → Arrays of detected… | Apache 2.0, Non-commercial, Op… |

## tabular_ml (2)

| Model | Publisher | Params | Context | Input → Output | License |
|---|---|---|---|---|---|
| Kumo Relational | nvidia | 3.1*10^7 | — | Tabular → Tabular | NVIDIA Software License, Non-c… |
| Kumo Tabular | nvidia | Kumo-Tabular-Small about 2… | — | Tabular → Tabular prediction… | NVIDIA Software License, Non-c… |

## Aggregate

- Publishers: {'nvidia': 25, 'deepseek-ai': 1, 'google': 3, 'z-ai': 2, 'openai': 1, 'moonshotai': 1, 'poolside': 1, 'meta': 4}
- Context windows seen: 1,048,576 (4), 262,144 (7), 163,840 (1), 131,072 (5), 32,768 (1), 8,192 (2); 15 cards state none (non-LLM micro-services).
- Largest: kimi-k3 (2.8T total / 104B active), deepseek-v4.1-flash (552B), nemotron-3-ultra-550b-a55b, glm-5-3 (753B).
- Licences: OpenMDW 1.1 (6), Apache 2.0 (5), MIT (4), NVIDIA Open Model License/Agreement (7), NVIDIA Software / Model Evaluation (6), Llama 3.2 Community (2), DINOv3 + Apache 2.0 (1), unstated (2).