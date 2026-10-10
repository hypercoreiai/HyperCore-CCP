# NVIDIA NIM free-endpoint catalogue — 38 model cards

Filter: `https://build.nvidia.com/models?filters=nimType%3Anim_type_preview` → facet **Free Endpoint = 38** (24 + 14 on two pages).
Captured 2026-10-09. Raw HTML and per-card markdown for every model are archived beside this file: `raw/` and `cards/`.

## 1. Text / reasoning models (17)

| Model | Publisher | Params | Context | In → Out | Licence | Downloadable container |
|---|---|---|---|---|---|---|
| [deepseek-v4.1-flash](https://build.nvidia.com/deepseek-ai/deepseek-v4.1-flash) | deepseek-ai | 552B | 1,048,576 | Text,Image → Text |
| [kimi-k3](https://build.nvidia.com/moonshotai/kimi-k3) | moonshotai | 2.8T | 1,048,576 | Text,Image → Text |
| [glm-5-3](https://build.nvidia.com/z-ai/glm-5-3) | z-ai | 753B | 1,048,576 | Text → Text |
| [glm-5-3-flash](https://build.nvidia.com/z-ai/glm-5-3-flash) | z-ai | 320B | 1,048,576 | Text,Image → Text |
| [gpt-oss-20b](https://build.nvidia.com/openai/gpt-oss-20b) | openai | 21.0B | 131,072 | Text → Text |
| [laguna-xs-2.1](https://build.nvidia.com/poolside/laguna-xs-2.1) | poolside | 33.0B | 262,144 | Text → Text |
| [nemotron-3-ultra-550b-a55b](https://build.nvidia.com/nvidia/nemotron-3-ultra-550b-a55b) | nvidia | 560.5B | 1,048,576 | Text → Text |
| [nemotron-3-super-120b-a12b](https://build.nvidia.com/nvidia/nemotron-3-super-120b-a12b) | nvidia | 123.6B | 1,048,576 | Text → Text |
| [nemotron-3.5-lightning-30b-a3b](https://build.nvidia.com/nvidia/nemotron-3.5-lightning-30b-a3b) | nvidia | 30.0B | 1,048,576 | Text → Text |
| [nemotron-3-nano-omni-30b-a3b-reasoning](https://build.nvidia.com/nvidia/nemotron-3-nano-omni-30b-a3b-reasoning) | nvidia | 33.0B | 262,144 | Video,Audio,Image,Text → Text |
| [nemotron-3.5-content-safety](https://build.nvidia.com/nvidia/nemotron-3.5-content-safety) | nvidia | 4.3B | 131,072 | Text,Image → Text |
| [llama-3_1-nemotron-safety-guard-8b-v3](https://build.nvidia.com/nvidia/llama-3_1-nemotron-safety-guard-8b-v3) | nvidia | 8.0B | 8,192 | Text → Text |
| [llama-guard-4-12b](https://build.nvidia.com/meta/llama-guard-4-12b) | meta | 12.0B | 163,840 | Text,Image → Text |
| [riva-translate-4b-instruct-v2](https://build.nvidia.com/nvidia/riva-translate-4b-instruct-v2) | nvidia | 4.2B | 8,192 | Text → Text |
| [nemotron-3-embed-1b](https://build.nvidia.com/nvidia/nemotron-3-embed-1b) | nvidia | 1.1B | 32,768 | Text → 2048-d float vectors |
| [diffusiongemma-26b-a4b-it](https://build.nvidia.com/google/diffusiongemma-26b-a4b-it) | google | 25.8B | 262,144 | Text,Image,Video → Text |
| [gemma-4-31b-it](https://build.nvidia.com/google/gemma-4-31b-it) | google | 32.7B | 262,144 | Text,Image,Video → Text |

## 2. Vision / perception (7)

| Model | Publisher | Params | Notes | In → Out |
|---|---|---|---|---|
| [google-paligemma](https://build.nvidia.com/google/google-paligemma) | google | 2.9B | Vision-language (caption/VQA) | Text,Image → Text |
| [llama-3.2-11b-vision-instruct](https://build.nvidia.com/meta/llama-3.2-11b-vision-instruct) | meta | 10.7B | Vision-language | Text,Image → Text |
| [llama-3.2-90b-vision-instruct](https://build.nvidia.com/meta/llama-3.2-90b-vision-instruct) | meta | 88.6B | Vision-language | Text,Image → Text |
| [muse-glimmer-30b](https://build.nvidia.com/meta/muse-glimmer-30b) | meta | 29.8B | Vision-language encoder | Text,Image → Text |
| [active-speaker-detection](https://build.nvidia.com/nvidia/active-speaker-detection) | nvidia | 65.2M (ASD) / 3.9M (10 GFLOPS variant) / 840K (lip reading) | Speaker diarisation / lip reading | Video, Image → Speaker labels, 512-d face embeddings, scores |
| [body-pose](https://build.nvidia.com/nvidia/body-pose) | nvidia | not stated in card | 3D human pose estimation | Video (RGB) → 3D skeleton (33 joints, SOMA 276-joint topology) |
| [synthetic-video-detector](https://build.nvidia.com/nvidia/synthetic-video-detector) | nvidia | 172M | Synthetic-vs-real video classifier | Video → Score / label |

## 3. Driving / 3D scene (3)

- **sparsedrive** — Multi-view camera images + intrinsics/extrinsics → Labeled 3D bounding boxes, BEV embeddings, lane geometry
- **streampetr** — 6x RGB 256x704 + camera intrinsics/extrinsics → 3D bounding boxes, agent attributes, BEV embeddings
- **bevformer** — RGB images, vehicle state, camera extrinsics → Labels (text string)

## 4. Audio / speech (4)

- **bnr** — Audio → Audio
- **studiovoice** — Audio → Audio
- **magpie-tts-zeroshot** — Text → Audio (wav, 22.05 kHz, <=20 s)
- **nemotron-voicechat** — Audio (PCM), Text → Audio (PCM)

## 5. World models / video generation (3)

- **cosmos3-nano** — 15.8B params, ctx 262,144 | Text, Image, Video + spatial controls → Images, video, action arrays
- **cosmos3-nano-reasoner** — not stated in card params, ctx n/a | Text, Image, Video → Text
- **cosmos-transfer2_5-2b** — 2.36B params, ctx n/a | Text + Video/Image → Video

## 6. Tabular / structured (2)

- **kumo-tabular** — 28M (Small) / 62M (Medium) / 215M (Large) | Tabular → JSON predictions
- **kumo-relational** — 31M | Tabular (multi-table) → JSON predictions

## 7. Domain-specific VLM (2)

- **ising-calibration-1-35b-a3b** — 31.3B params, ctx 262,144 | Image,Text → Text
- **ising-calibration-1.5-31b** — 31.3B params, ctx 262,144 | Image,Text → Text

## Licence distribution

- Open / open-weight: MIT (deepseek-v4.1-flash, gpt-oss-20b), OpenMDW 1.1 (cosmos3-nano, ising-calibration, nemotron-3-embed), Apache 2.0 (nemotron-3-embed weights), Llama 3.2 Community (meta models).
- NVIDIA Open Model License / non-commercial: kumo-*, bnr, active-speaker-detection, body-pose, streampetr, sparsedrive, synthetic-video-detector, ising-* (MIT + NVIDIA OML mix).
- Trial-service layer on top of everything: NVIDIA API Terms of Use (or API Trial ToS for preview endpoints).

## How the cards were retrieved (reproducible)

1. `GET /models?filters=nimType%3Anim_type_preview` → 38 card links (2 pages).
2. `GET /<publisher>/<slug>.md` → markdown card for ~30 models.
3. For 8 slugs the `.md` route returns an HTML error shell; the card text is embedded in the Next.js RSC payload of `/<publisher>/<slug>` — decode `\n` escapes and slice from `# Model Overview` / `License/Terms of Use`.
4. Structured specs (`contextLength`, `parameters`, `inputModalities`, `outputModalities`) are in a `"specifications":{...}` JSON blob inside every model page — 23 of 38 expose it.