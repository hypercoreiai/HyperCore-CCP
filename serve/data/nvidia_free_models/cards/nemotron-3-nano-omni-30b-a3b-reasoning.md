---
title: "nemotron-3-nano-omni-30b-a3b-reasoning"
publisher: "nvidia"
type: "endpoint"
updated: "2026-04-28T15:37:00.315Z"
description: "Nemotron 3 Nano Omni is an omni-modal reasoning model that understands images, video, speech, text."
canonical: "https://build.nvidia.com/nvidia/nemotron-3-nano-omni-30b-a3b-reasoning"
---

# Model Overview

### Description:
NVIDIA Nemotron 3 Nano Omni is a multimodal large language model that unifies video, audio, image, and text understanding to support enterprise-grade Q&A, summarization, transcription, and document intelligence workflows. It extends the Nemotron Nano family with integrated video+speech comprehension, Graphical User Interface (GUI), Optical Character Recognition (OCR), and speech transcription capabilities, enabling end-to-end processing of rich enterprise content such as meeting recordings, M&E assets, training videos, and complex business documents. NVIDIA Nemotron 3 Nano Omni was developed by NVIDIA as part of the Nemotron model family. <br>

This model is available for commercial use. <br>

This model was improved using Qwen3-VL-30B-A3B-Instruct, Qwen3.5-122B-A10B, Qwen3.5-397B-A17B, Qwen2.5-VL-72B-Instruct, and gpt-oss-120b. For more information, please see the Training Dataset section below. <br>

### License/Terms of Use

Governing Terms: This trial service is governed by the [NVIDIA API Trial Terms of Service](https://assets.ngc.nvidia.com/products/api-catalog/legal/NVIDIA%20API%20Trial%20Terms%20of%20Service.pdf). Use of this model is governed by the [NVIDIA Open Model Agreement](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-agreement/).<br>

### Deployment Geography:
Global <br>

### Use Case: <br>
This model is designed for enterprise customers requiring multimodal understanding capabilities. Expected users include:
- Customer service applications (e.g., Doordash video of drop-off at a given address via OCR, drive-thru order verification)
- Media and Entertainment (M&E) — video and speech analysis, dense captions, video search and summarization
- Document intelligence for AI assistants (contracts, SOW/MSA, scientific discovery, financial documents)
- GUI automation for AI agentic applications (incident management, agentic search, browser agents, email agents)

### Release Date: <br>
Build.Nvidia.com 04/28/2026 via [URL](https://build.nvidia.com/nvidia/nemotron-3-nano-omni-30b-a3b-reasoning) <br>
Hugging Face 04/28/2026 via:
- [BF16](https://huggingface.co/nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-BF16) <br>
- [FP8](https://huggingface.co/nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-FP8) <br>
- [NVFP4](https://huggingface.co/nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-NVFP4) <br>

NGC 04/28/2026  via [URL](https://catalog.ngc.nvidia.com/orgs/nim/teams/nvidia/containers/nemotron-3-nano-omni-30b-a3b-reasoning) <br>

## Model Architecture:
**Architecture Type:** Mamba2-Transformer Hybrid Mixture of Experts (MoE) <br>

**Network Architecture:**
- [Nemotron 3 Nano LLM (30B A3B)](https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16)
- CRADIO v4-H vision encoder
- Parakeet speech encoder

**Number of model parameters:** 3.1 x 10^10 (31B A3B) <br>

## Input(s): <br>
**Input Type(s):** Video, Audio, Image, Text <br>

**Input Format(s):** <br>
- Video: mp4, up to 2 minutes. For 1080p videos, sample up to 1 FPS / 128 frames. For lower-resolution videos such as 720p, higher temporal sampling such as 2 FPS / 256 frames may be used.
- Audio: wav, mp3 files (up to 1 hour), 8kHz and higher sampling rates
- Image: Red, Green, Blue (RGB) (jpeg, png)
- Text: String <br>

**Input Parameters:** <br>
- Video: Three-Dimensional (3D)
- Audio: One-Dimensional (1D)
- Image: Two-Dimensional (2D)
- Text: One-Dimensional (1D) <br>

**Other Properties Related to Input:** <br>
- Maximum context length up to 256k tokens
- Language support: English only  <br>

## Output(s)

**Output Type(s):** Text <br>

**Output Format(s):** <br>
- Text: String <br>

**Output Parameters:** <br>
- Text: One-Dimensional (1D) <br>

**Other Properties Related to Output:** <br>
- Maximum context length up to 256k tokens.
- Supports JSON output format
- Supports reasoning output with chain-of-thought
- Supports tool calling
- Supports word-level timestamps for transcription <br>

Our AI models are designed and/or optimized to run on NVIDIA GPU-accelerated systems. By leveraging NVIDIA's hardware (e.g. GPU cores) and software frameworks (e.g., CUDA libraries), the model achieves faster training and inference times compared to CPU-only solutions. <br>

## Software Integration:
**Runtime Engine(s):**
* vLLM <br>
* NeMo <br>
* Megatron <br>
* NeMo-RL <br>

**Supported Hardware Microarchitecture Compatibility:** <br>
* NVIDIA Ampere (A100 80GB SXM/NVLink) <br>
* NVIDIA Blackwell (B200 SXM/NVLink, RTX Pro 6000 SE, DGX Spark, Jetson Thor, RTX 5090) <br>
* NVIDIA Hopper (H100 SXM/NVLink, H200 SXM/NVLink) <br>
* NVIDIA Lovelace (L40S) <br>

**Preferred/Supported Operating System(s):**
* Linux <br>

**Inference Runtimes:** <br>
* vLLM <br>
* TensorRT LLM <br>
* TensorRT Edge-LLM <br>
* llama.cpp <br>
* Ollama <br>
* SGLang <br>

The integration of foundation and fine-tuned models into AI systems requires additional testing using use-case-specific data to ensure safe and effective deployment. Following the V-model methodology, iterative testing and validation at both unit and system levels are essential to mitigate risks, meet technical and functional requirements, and ensure compliance with safety and ethical standards before deployment. <br>

This AI model can be embedded as an Application Programming Interface (API) call into the software environment described above. <br>

## Model Version(s):
Nemotron-3-Nano-Omni-30B-A3B-Reasoning <br>

---

## Quick Start Guide

### Model Parameters

| Mode | temperature | top_p | top_k | max_tokens | reasoning_budget | grace_period |
|------|-------------|-------|-------|------------|------------------|--------------|
| **Thinking mode** | 0.6 | 0.95 | — | 20480 | 16384 | 1024 |
| **Instruct mode** | 0.2 | — | 1 | 1024 | — | — |

### Download Model Weights

| Precision | Technical Name | HuggingFace URL |
|-----------|---------------|-----------------|
| BF16 | `Nemotron-3-Nano-Omni-30B-A3B-Reasoning-BF16` | https://huggingface.co/nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-BF16 |
| FP8 | `Nemotron-3-Nano-Omni-30B-A3B-Reasoning-FP8` | https://huggingface.co/nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-FP8 |
| NVFP4 | `Nemotron-3-Nano-Omni-30B-A3B-Reasoning-NVFP4` | https://huggingface.co/nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-NVFP4 |

#### Install the HuggingFace CLI

```bash
pip install -U "huggingface_hub[hf_xet]"

# Log in once; the token is cached at ~/.cache/huggingface/token
hf auth login

# Sanity check: should print your username and orgs
hf auth whoami
```

#### Download the weights

Pick a target directory on a volume with ≥70 GB free (the model is ~62 GB).

```bash
WEIGHTS=/path/to/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-BF16

hf download nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-BF16 \
--local-dir "$WEIGHTS" \
--max-workers 8
```

> **Notes:**
> - `hf download` is **resumable** — re-run the same command if the connection drops.
> - `--max-workers 8` parallelizes downloads; tune up on fast networks.
> - The `hf_xet` extra enables native Xet-protocol transfers for Xet-backed repos; no need for `git-xet` or `git-lfs` when using `hf download`.

#### Verify the download

```bash
ls "$WEIGHTS" | head
du -sh "$WEIGHTS"  # expect ~62 GB
test -f "$WEIGHTS/config.json" && echo OK
```

---

### vLLM

> **Required version:** vLLM **0.20.0** is needed. This means one of these containers:
>
> - **CUDA 13.0:** ['vllm/vllm-openai:v0.20.0'](https://hub.docker.com/layers/vllm/vllm-openai/v0.20.0/images/sha256-328268a8e0ceb9fccd301cca6599654908c3cac0e328ddce953c933b432924ef)
> - **CUDA 12.9:** ['vllm/vllm-openai:v0.20.0-cu129'](https://hub.docker.com/layers/vllm/vllm-openai/v0.20.0-cu129/images/sha256-f4ace3494896eeda800dee284d1fc42ca7f5626f31ceae8e24d1383d770567c2)
>

#### Container

```bash
docker pull vllm/vllm-openai:v0.20.0
```

> **Audio support:** Within the vLLM container, before running `vllm serve`, if *any* audio will be used (including passing `use_audio_in_video: true`):
> ```bash
> python3 -m pip install "vllm[audio]"
> ```

#### General Invocation (1×GPU, e.g. 1×B200)

```bash
# vllm serve nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-BF16 \
# vllm serve nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-FP8 \
vllm serve nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-NVFP4 \
--host 0.0.0.0 \
--max-model-len 131072 \
--tensor-parallel-size 1 \
--trust-remote-code \
--video-pruning-rate 0.5 \
--max-num-seqs 384 \
--allowed-local-media-path / \
--media-io-kwargs '{"video": {"fps": 2, "num_frames": 256}}' \
--reasoning-parser nemotron_v3 \
--enable-auto-tool-choice \
--tool-call-parser qwen3_coder \
--kv-cache-dtype fp8 # Omit this for BF16
```

#### Platform-Specific Notes

> **RTX Pro:** Due to a current bug with FlashInfer + RTX Pro, append: `--moe-backend triton`

> **NVFP4 + TP>1:** Due to a current bug with the TRTLLM_GEN MoE backend kernels on vLLM, when running with TP>1 on NVFP4, append: `--moe-backend flashinfer_cutlass`

##### vLLM on DGX Spark (aarch64 / ARM64)

For everything not covered here (API examples, reasoning mode, video tuning), follow the general instructions.

###### 1. Pull the container image

Use the upstream multi-arch **vLLM v0.20.0** docker image. Docker will automatically pull the `arm64` variant.

```bash
docker pull vllm/vllm-openai:v0.20.0
```

###### 2. Launch the vLLM server on Spark

```bash
WEIGHTS=/path/to/nemotron-3-nano-omni-weights

# The image does not include audio packages so we need to install them with "pip install vllm[audio]" as done in the command below
docker run --rm -it \
--gpus all \
--ipc=host -p 8000:8000 \
--shm-size=16g \
--name vllm-nemotron-omni \
-v "${WEIGHTS}:/model:ro" \
--entrypoint /bin/bash \
vllm/vllm-openai:v0.20.0 -c  \
"pip install vllm[audio] && vllm serve /model \
--served-model-name=nemotron_3_nano_omni \
--max-num-seqs 8 \
--max-model-len 131072 \
--port 8000 \
--trust-remote-code \
--gpu-memory-utilization 0.8 \
--limit-mm-per-prompt '{\"video\": 1, \"image\": 1, \"audio\": 1}' \
--media-io-kwargs '{\"video\": {\"fps\": 2,  \"num_frames\": 256}}' \
--allowed-local-media-path=/ \
--enable-prefix-caching \
--max-num-batched-tokens 32768 \
--reasoning-parser nemotron_v3 \
--enable-auto-tool-choice \
--tool-call-parser qwen3_coder"
```

In another terminal, verify the server is ready:

```bash
curl -sS http://localhost:8000/v1/models | python3 -m json.tool
```

###### Key Spark-Specific Flags

| Flag | Purpose | Spark Guidance |
|------|---------|----------------|
| `--gpus all` | Select GPU | Spark has one GB10 GPU; `all` is equivalent to `device=0` |
| `--max-model-len` | Max context window | Start at 131072; reduce if you hit OOM (see Memory Tuning below) |

###### Memory Tuning on Spark

Spark uses **unified LPDDR5X memory** (~128 GB shared between CPU and GPU), not separate system + VRAM pools. Two levers, in order of impact:

1. **Lower `--gpu-memory-utilization`** from 0.85 → 0.70 to free ~19 GB back to the OS and re-enable weight prefetch. Cost: smaller KV cache budget.
2. **Lower `--max-model-len`** to reduce KV cache allocation (e.g. halving context window halves KV cache at `--max-num-seqs=1`).
Combined override:

```bash
--gpu-memory-utilization=0.70 \
--max-model-len=32768 \
```

---

### TensorRT-LLM

This model can also be deployed with TensorRT-LLM - see relevant [instructions here](https://github.com/NVIDIA-NeMo/Nemotron/blob/main/usage-cookbook/Nemotron-3-Nano-Omni/trtllm_cookbook.ipynb).

#### Platform-Specific Notes

##### TensorRT Edge-LLM

This model can also be deployed with TensorRT Edge-LLM on NVIDIA Jetson Thor - see the [Jetson AI Lab model page](https://www.jetson-ai-lab.com/models/nemotron-3-nano-omni/) and the [TensorRT Edge-LLM Quick Start Guide](https://nvidia.github.io/TensorRT-Edge-LLM/latest/user_guide/getting_started/quick-start-guide.html).

---

### SGLang

The BF16 variant of this model is supported on SGLang, with the following images:

* **CUDA 13.0:** [`lmsysorg/sglang:dev-cu13-nemotronh-nano-omni-reasoning-v3`](https://hub.docker.com/layers/lmsysorg/sglang/dev-cu13-nemotronh-nano-omni-reasoning-v3/images/sha256-302533fef545bbc5efdd2774556a1492034c797bf2978a9dc63ada55e4cf5703)
* **CUDA 12.9:** [`lmsysorg/sglang:dev-nemotronh-nano-omni-reasoning-v3`](https://hub.docker.com/layers/lmsysorg/sglang/dev-nemotronh-nano-omni-reasoning-v3/images/sha256-23bda4117a86744d9fa08861417869dbd6fb31d5a68b5efba741aca6185f285b)

`librosa` must be installed first:
`pip install librosa --break-system-packages`

To serve:
`sglang serve --model-path nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-BF16 --trust-remote-code`

> [!NOTE]
> NVFP4 and FP8 support to come.

#### Platform-Specific Notes

##### SGLang on DGX Spark (aarch64 / ARM64)

For everything not covered here (API examples, reasoning mode, video tuning), follow the general instructions.

###### 1. Pull the container image

Use the upstream multi-arch **CUDA 13.0** docker image linked above. Docker will automatically pull the `arm64` variant.

```bash
docker pull lmsysorg/sglang:dev-cu13-nemotronh-nano-omni-reasoning-v3
```

###### 2. Launch the SGLang server on Spark

```bash
WEIGHTS=/path/to/nemotron-3-nano-omni-weights

# The image does not include audio packages so we need to install them with "pip install librosa" as done in the command below
docker run --gpus all -it --rm \
-p 30000:30000 \
-v "${WEIGHTS}:/model:ro" \
--shm-size 16g \
lmsysorg/sglang:dev-cu13-nemotronh-nano-omni-reasoning-v3 \
bash -c "pip install librosa && python3 -m sglang.launch_server --model-path /model \
--host 0.0.0.0 \
--port 30000 \
--trust-remote-code \
--mem-fraction-static 0.8 \
--max-running-requests 8 \
--tool-call-parser qwen3_coder \
--reasoning-parser nemotron_3"
```

In another terminal, verify the server is ready:

```bash
curl -sS http://localhost:30000/v1/models | python3 -m json.tool
```

###### Key Spark-Specific Flags

| Flag | Purpose | Spark Guidance |
|------|---------|----------------|
| `--gpus all` | Select GPU | Spark has one GB10 GPU; `all` is equivalent to `device=0` |
| `--context-length` | Max context window | Start with default; reduce if you hit OOM (see Memory Tuning below) |

###### Memory Tuning on Spark

Spark uses **unified LPDDR5X memory** (~128 GB shared between CPU and GPU), not separate system + VRAM pools. Two levers, in order of impact:

1. **Lower `--mem-fraction-static`** from 0.80 → 0.70 to free ~13 GB back to the OS and re-enable weight prefetch. Cost: smaller KV cache budget.
2. **Lower `--context-length`** to reduce KV cache allocation (e.g. halving context window halves KV cache at `--max-running-requests=1`).
Combined override:

```bash
--mem-fraction-static=0.70 \
--context-length=32768 \
```

---
### API Client (OpenAI-compatible)

```python
from openai import OpenAI
client = OpenAI(base_url="http://localhost:8000/v1", api_key="")
MODEL = "nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-NVFP4"
```
**Image Example**

```python
import base64

def image_to_data_url(path: str) -> str:
with open(path, "rb") as f:
b64 = base64.b64encode(f.read()).decode("utf-8")
return f"data:image/jpeg;base64,{b64}"

image_url = image_to_data_url("media/example1a.jpeg")

response = client.chat.completions.create(
model=MODEL,
messages=[
{
"role": "user",
"content": [
{"type": "text", "text": "Describe this image in detail."},
{"type": "image_url", "image_url": {"url": image_url}},
],
}
],
max_tokens=1024,
temperature=1.0,
extra_body={"top_k": 1, "chat_template_kwargs": {"enable_thinking": False}},
)
print(response.choices[0].message.content)
```

**Audio Example**

```python
from pathlib import Path

audio_url = Path("media/2414-165385-0000.wav").resolve().as_uri()

response = client.chat.completions.create(
model=MODEL,
messages=[
{
"role": "user",
"content": [
{"type": "audio_url", "audio_url": {"url": audio_url}},
{"type": "text", "text": "Transcribe this audio."},
],
}
],
max_tokens=1024,
temperature=1.0,
extra_body={"top_k": 1, "chat_template_kwargs": {"enable_thinking": False}},
)
print(response.choices[0].message.content)
```

**Video Example**

```python
from pathlib import Path

video_url = Path("media/demo.mp4").resolve().as_uri()
reasoning_budget = 16384
grace_period = 1024

response = client.chat.completions.create(
model=MODEL,
messages=[
{
"role": "user",
"content": [
{"type": "video_url", "video_url": {"url": video_url}},
{"type": "text", "text": "Describe this video."},
],
}
],
max_tokens=20480,
temperature=0.6,
top_p=0.95,
extra_body={
"thinking_token_budget": reasoning_budget + grace_period,
"chat_template_kwargs": {
"enable_thinking": True,
"reasoning_budget": reasoning_budget,
},
"mm_processor_kwargs": {"use_audio_in_video": False},
},
)
print(response.choices[0].message.content)
```

**Text Example (curl)**

```bash
curl -sS http://localhost:8000/v1/chat/completions \
-H "Content-Type: application/json" \
-d '{"model":"nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-NVFP4","messages":[{"role":"user","content":"Hello, what can you do?"}],"temperature":1.0,"top_k":1}' \
| python3 -c "import sys,json; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

**PDF Example (page-by-page via Python)**

The API accepts **images**, not raw PDF files. The script below renders each page to PNG and sends it as base64. Save as **`pdf_vlm_chat.py`** and install dependencies: `pip install pymupdf pillow requests`.

<details>
<summary>pdf_vlm_chat.py (click to expand)</summary>

```python
#!/usr/bin/env python3
"""Send PDF page(s) as images to a vLLM /v1/chat/completions endpoint."""
from __future__ import annotations

import argparse, base64, sys
from io import BytesIO
from pathlib import Path

import requests

try:
import fitz
from PIL import Image
except ImportError:
print("Install: pip install pymupdf pillow requests", file=sys.stderr)
sys.exit(1)

USER_PROMPT = (
"Summarize this PDF page: main topic, section headings, important facts "
"or bullets, and a brief note on each figure or table. "
"Do not invent text you cannot read."
)
API_URL = "http://localhost:8000/v1/chat/completions"
MODEL = "nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-NVFP4"
MAX_TOKENS = 32000
DPI = 150

def page_to_b64(pdf_path: str, idx: int) -> str:
doc = fitz.open(pdf_path)
z = DPI / 72.0
pix = doc.load_page(idx).get_pixmap(matrix=fitz.Matrix(z, z))
img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
doc.close()
buf = BytesIO()
img.save(buf, format="PNG")
return base64.b64encode(buf.getvalue()).decode("ascii")

def chat(url, model, b64, text, max_tokens):
r = requests.post(url, json={
"model": model,
"messages": [{"role": "user", "content": [
{"type": "text", "text": text},
{"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
]}],
"max_tokens": max_tokens,
"stream": False,
"temperature": 1.0,
"chat_template_kwargs": {"enable_thinking": False},
}, timeout=120)
r.raise_for_status()
return r.json()["choices"][0]["message"]["content"]

def main():
p = argparse.ArgumentParser()
p.add_argument("pdf")
p.add_argument("--page", type=int, default=0)
p.add_argument("--all-pages", action="store_true")
p.add_argument("-o", "--output")
p.add_argument("--url", default=API_URL)
p.add_argument("--model", default=MODEL)
p.add_argument("--max-tokens", type=int, default=MAX_TOKENS)
a = p.parse_args()

doc = fitz.open(a.pdf); n = len(doc); doc.close()
pages = range(n) if a.all_pages else [a.page]
parts = [f"# Extracted: {Path(a.pdf).name}\n\n*Pages: {n}*\n"] if a.all_pages else []

for i in pages:
print(f"Page {i+1}/{n} ...", file=sys.stderr)
b64 = page_to_b64(a.pdf, i)
text = chat(a.url, a.model, b64, f"Page {i+1}.\n\n{USER_PROMPT}", a.max_tokens)
parts.append(f"\n---\n\n## Page {i+1}\n\n{text.strip()}\n" if a.all_pages else text.strip())

out = "\n".join(parts)
if a.output:
Path(a.output).write_text(out + "\n", encoding="utf-8")
else:
print(out)

if __name__ == "__main__":
main()
```

</details>

**Single page:**

```bash
python3 pdf_vlm_chat.py /path/to/your_document.pdf --page 0
```

**All pages to markdown:**

```bash
python3 pdf_vlm_chat.py /path/to/your_document.pdf --all-pages -o extracted.md
```

Edit `USER_PROMPT` in the script for different tasks (detailed extraction, table parsing, etc.).

---

### Reasoning Mode (`enable_thinking`)

| Setting | Behavior |
|---------|----------|
| **Default (omitted)** | Reasoning is **on**. The model emits chain-of-thought before the final answer, visible in `content`. |
| `"chat_template_kwargs": {"enable_thinking": false}` | Reasoning is **off**. Only the final answer appears in `content`. |

To disable reasoning on a request, add to the JSON body:

```json
"chat_template_kwargs": {"enable_thinking": false}
```

In the Python heredoc pattern, use `False` (Python boolean), not `false` (invalid Python).

We recommend thinking mode for tasks that involve reasoning and complex understanding. For video, audio, and omni use cases, try both enabling and disabling thinking for best results.

---

<details>
<summary><strong>Advanced: Budget-Controlled Reasoning</strong></summary>

```python
from typing import Any, Dict, List

from openai import OpenAI
from transformers import AutoTokenizer

class ThinkingBudgetClient:
def __init__(self, base_url: str, api_key: str, tokenizer_name_or_path: str):
self.tokenizer = AutoTokenizer.from_pretrained(
tokenizer_name_or_path, trust_remote_code=True
)
self.client = OpenAI(base_url=base_url, api_key=api_key)

def chat_completion(
self,
model: str,
messages: List[Dict[str, Any]],
reasoning_budget: int = 512,
max_tokens: int = 1024,
**kwargs,
) -> Dict[str, Any]:
assert max_tokens > reasoning_budget, (
f"reasoning_budget must be less than max_tokens. "
f"Got {max_tokens=} and {reasoning_budget=}"
)

# Step 1: generate only the reasoning trace up to the requested budget.
response = self.client.chat.completions.create(
model=model,
messages=messages,
max_tokens=reasoning_budget,
extra_body={
"top_k": 1,
"chat_template_kwargs": {
"enable_thinking": True,
},
},
**kwargs,
)
reasoning_content = response.choices[0].message.content or ""
if "</think>" not in reasoning_content:
print("No </think> found in reasoning content")
reasoning_content = f"{reasoning_content}</think>\n\n"

reasoning_tokens_len = len(
self.tokenizer.encode(reasoning_content, add_special_tokens=False)
)
remaining_tokens = max_tokens - reasoning_tokens_len
assert remaining_tokens > 0, (
f"No tokens remaining for response ({remaining_tokens=}). "
"Increase max_tokens or lower reasoning_budget."
)

# Step 2: continue from the closed reasoning trace and ask for the final answer.
continued_messages = messages + [
{"role": "assistant", "content": reasoning_content}
]
prompt = self.tokenizer.apply_chat_template(
continued_messages,
tokenize=False,
continue_final_message=True,
)
response = self.client.completions.create(
model=model,
prompt=prompt,
max_tokens=remaining_tokens,
extra_body={"top_k": 1},
**kwargs,
)

return {
"reasoning_content": reasoning_content.strip(),
"content": response.choices[0].text,
"finish_reason": response.choices[0].finish_reason,
}
```

</details>

### Video Tuning

#### Frame sampling (`--media-io-kwargs`)

Without explicit settings, vLLM may default to ~32 frames per video regardless of length. Always set `--media-io-kwargs` at server launch (already included in the General Invocation above):

```text
--media-io-kwargs '{"video": {"fps": 2, "num_frames": 256}}'
```

Recommended `num_frames` ranges (at `fps=2`):

| GPU memory | Recommended `num_frames` range |
|------------|--------------------------------|
| **80 GB** (A100/H100) | 128–512 |
| **≤40 GB** | 64–256 |

Higher values improve temporal coverage but increase VRAM and prefill time. Start at the low end of the range and increase as your workload and latency budget allow.

---

### Notes

1. **Reasoning default:** Reasoning is on by default. If you omit `chat_template_kwargs`, the model will produce chain-of-thought traces in `content`. This is appropriate for text and image inputs.
2. **Video frame sampling:** The default (~32 frames) is too conservative for most real videos. Set `--media-io-kwargs` at server launch.
3. **PDF input format:** The API does not accept raw PDF uploads. Render pages to PNG and send as base64 (see PDF Example above).
4. **`max_tokens` vs `--max-model-len`:** `max_tokens` in the request caps only the completion (generated output). It cannot exceed the server's `--max-model-len`, which is the hard ceiling for prompt + completion combined. Increase the server flag if you need longer outputs.
---

### Jetson Deployment

For Jetson deployments, vLLM, SGLang, Ollama, llama.cpp, and TensorRT Edge-LLM are supported inference frameworks; see the [Jetson AI Lab model page](https://www.jetson-ai-lab.com/models/nemotron-3-nano-omni/) for more details.

TensorRT Edge-LLM support is only for Jetson Thor; TensorRT-LLM is not supported on Jetson.

---

## Training, Testing, and Evaluation Datasets:

### Dataset Overview
**Total Size:** 354,587,705 data points (~717.0B tokens) <br>
**Total Number of Datasets:** 1395 dataset entries <br>

**Dataset partition:** Training [100%], Testing [N/A — evaluation benchmarks used separately], Validation [N/A — evaluation benchmarks used separately] <br>
**Time period for training data collection:** 2019–2025 <br>
**Time period for testing data collection:** N/A (standard public benchmarks) <br>
**Time period for validation data collection:** N/A (standard public benchmarks) <br>

### Dataset Description
Nemotron-Omni extends our commitment from text to multimodal, delivering the same level of openness across text, audio, image, and video.

**Adapter and encoder training scale:** ~127B tokens across mixed modalities spanning text+image, text+video, text+audio, and text+video+audio—reflecting real-world, contextualized interactions versus single-modality data.

**Post-training for real-world tasks:** ~124M curated examples across multimodal combinations (text+audio, text+image, text+video, and text+video+audio), structured to support document reasoning, computer use, and long-horizon workflows.

**RL environments for agent training:** 20 RL datasets across 25 environments covering 5 new multimodal tasks—visual grounding, chart and document understanding, vision-critical STEM problems, video understanding, and automatic speech recognition—extending Nemotron's RL pipeline beyond text into vision and audio.

**Modality Breakdown:**

| Modality | Dataset Entries | Samples | Est. Tokens (M) |
|---|---|---|---|
| text+audio | 220 | 259,178,821 | 143,533.1 |
| text+image | 750 | 70,143,901 | 180,347.1 |
| text+video | 241 | 15,837,673 | 239,631.5 |
| text+video+audio | 155 | 8,720,044 | 152,499.2 |
| text | 12 | 707,187 | 958.4 |
| **Total** | **1395** | **354,587,705** | **716,969.2** |

Training data for Nemotron-Omni was assembled from a diverse collection of audio, image, video, and text datasets. Raw datasets were first converted into a standardized JSONL format with unified conversation-turn structure. Audio data was resampled to 16 kHz where needed. Image and video datasets were paired with question-answer annotations, often regenerated or refined using large vision-language models to improve quality and consistency. Quality filtering was applied using model-based judges to remove low-quality, unsafe, or off-topic samples. Deduplication and CSAM scanning were performed across all image datasets. Data was then packed into fixed-length sequences (32k, 128k, or 256k tokens) for efficient training. <br>

Multiple safety measures were implemented throughout the data pipeline. All image/text datasets underwent CSAM (Child Sexual Abuse Material) scanning, with results tracked per dataset. Content safety filtering was applied using two independent safety judge models to flag and remove samples containing harmful content including weapons references, criminal planning, sexual content involving minors, harassment, hate speech, profanity, threats, violence, or suicide-related content. Synthetic data generation pipelines included explicit quality and safety filtering stages. Identity-fix processing was applied to correct potential biases in generated responses. The multi-stage pipeline (original → cleaned → clean+safe → clean+safe+holdout) ensured progressive refinement, with each stage removing additional problematic content. <br>

We built on the base model, applying additional training, enhancements, and optimizations on top of it.

# Public Datasets
| Dataset | Samples | % of Public | Tokens (M) | Modality |
|---|---|---|---|---|
| MiraData | 28,252,307 | 55.53% | 14,181.3 | text+audio+video | https://github.com/mira-space/MiraData
| laion-disco-12M | 7,507,574 | 14.7% | 22,691.0 | text+audio | https://laion.ai/blog/laion-disco-12m/
| YouTube Video | 2,057,000 | 4.0% | 15,390 | text+video |
| YouTube Video and Audio | 1,164,000 | 2.2% | 18,730 | text+video+audio |

# Private Datasets
| Dataset | Samples | % of Private | Tokens (M) | Modality |
|---|---|---|---|---|
| Granary | 23,370,274 | 8.0% | 1,471.7 | text+audio |
| SIFT-50M | 22,837,500 | 7.8% | 5,241.7 | text+audio |

# Self-Sourced Synthetic Data

* Overall Size: 41,502,625 samples across modalities: text+audio, text+image, text+video <br>

* Description of synthetic data generation methods: <br>

Synthetic data generation (SDG) was used to improve data quality, generate reasoning traces, re-label annotations, and augment existing datasets. Methods include: re-captioning images and audio using vision-language models, generating question-answer pairs from existing media, producing thinking/reasoning chains for complex tasks, paraphrasing prompts for diversity, and applying model-based quality filtering. <br>

## NVIDIA-Sourced Synthetic Datasets
| Dataset | Modality | Count | Models Used |
| --- | --- | --- | --- |
| GroundCUA | text+image | 2,797,851 | gpt-oss-120b, Qwen3-VL-30B-A3B-Instruct |
| OpenImages | text+image | 2,556,412 | Qwen3-VL-30B-A3B-Instruct |
| MMTrail | text+audio | 1,620,533 | Qwen3-omni-captioner, gpt-oss-120B |
| Localized Narratives | text+image | 1,511,812 | Qwen3-VL-30B-A3B-Instruct |
| ALLaVA | text+image | 1,414,130 | Qwen3-VL-30B-A3B-Instruct |
| VGG-Sound | text+audio | 1,371,167 | Qwen3-omni-captioner, gpt-oss-120B |
| PIXMO-CAP | text+image | 1,308,838 | Qwen3-VL-30B-A3B-Instruct |
| TTS-Synthesized Nemotron-Nano-3 SFT Data | text+audio | 1,226,784 | NVIDIA Magpie TTS |
| MINT-1T | text+image | 904,035 | Qwen3-VL-32B-Instruct, Gemini 3 Pro for filtering, Scene Text models (RTX) translate |
| ScaleCUA | text+image | 889,010 | Qwen3-VL-30B-A3B-Instruct |
| AgentNet | text+image | 878,986 | Kimi-K2.5 |
| Conceptual Captions 3M-30b | text+image | 867,065 | Qwen3-VL-30B-A3B-Thinking-FP8 |
| MetaMathQA | text+image | 860,656 | Qwen3.5-122B-A10B, Gemini 3 Flash Preview for filtering |
| Mulberry-SFT COT | text+image | 566,982 | GLM-4.1V-9B-Thinking, Qwen3.5-122B-A10B, Gemini 3 Flash Preview for filtering |
| CC for OCR | text+image | 522,595 | SwinDocSegmenter, DeepSeek OCR, Qwen3.5-122B-A10B, Qwen3-32B, Gemini 3 Flash Preview for filtering, GPT-4o mini for filtering & quality checks, Qwen3-VL-30B-A3B-Thinking-FP8, gpt-oss-120b |
| Charxiv-100K | text+image | 272,104 | Qwen3-VL-235B-A22B-Instruct, Qwen3-VL-235B-A22B-Thinking, GPT-4o for filtering, Qwen3.5-122B-A10B |
| SwinDocSegmenter | text+image | 207,200 | SwinDocSegmenter, DeepSeek OCR |
| CLEVR | text+image, text+video | 197,027 | Qwen3.5-122B-A10B, Gemini 3 Flash Preview for filtering |
| InternVL-Data | text+image | 185,395 | Qwen3.5-122B-A10B, Gemini 3 Flash Preview for filtering |
| Flickr30k Entities | text+image | 154,760 | Qwen3.5-122B-A10B, Gemini 3 Flash Preview for filtering |
| Metropolis and Lita | text+video | 150,434 | Qwen3.5-122B-A10B |
| TextCaps | text+image | 136,911 | Commercial VILA model, Qwen3-VL-30B-A3B-Instruct |
| Vision R1 Llava CoT | text+image | 126,024 | GLM-4.1V-9B-Thinking |
| HC-STVG | text+video | 124,902 | NVIDIA relabeled using Qwen model (Qwen2.5-VL-72B-Instruct) |
| nvPDFtex | text+image | 118,351 | gpt-oss-120b, Qwen3.5-122B-A10B |
| ChartQA | text+image | 111,602 | Qwen3.5-122B-A10B, Gemini 3 Flash Preview for filtering, Qwen2-VL-72B (NV) |
| ECD-10k-Images | text+image | 110,697 | Qwen3.5-122B-A10B |
| SAMA-COCO | text+image | 102,965 | gpt-oss-120B |
| VisualWebInstruct | text+image | 97,746 | Earlier SDG, GLM-4.1V-9B-Thinking |
| Spatial | text+image | 95,532 | Microsoft Florence-2-large |
| DoubtNut | text+image | 94,919 | Qwen3.5-122B-A10B, Gemini 3 Flash Preview for filtering |
| Cosmos Nemotron SFTv13.9 | text+image | 92,128 | Qwen3-VL-30B-A3B-Instruct, Qwen3.5-122B-A10B, Gemini 3 Flash Preview for filtering |
| CrossTask | text+video | 76,495 | NVIDIA relabeled using Qwen model (Qwen2.5-VL-72B-Instruct) |
| RefCOCO | text+image | 69,850 | Qwen3.5-122B-A10B, Gemini 3 Flash Preview for filtering |
| Mantis Instruct | text+image | 66,975 | Qwen3.5-122B-A10B, Gemini 3 Flash Preview for filtering |
| Visual7W | text+image | 62,589 | Qwen3.5-122B-A10B |
| ScreenQA | text+image | 62,186 | Qwen3.5-122B-A10B |
| VQAV2 | text+image | 54,899 | Qwen3.5-122B-A10B |
| TallyQA | text+image | 50,073 | Qwen3.5-122B-A10B, Gemini 3 Flash Preview for filtering |
| KeenSight | text+image | 49,849 | Qwen3.5-122B-A10B, Gemini 3 Flash Preview for filtering |
| GQA | text+image | 42,182 | Qwen3.5-122B-A10B, Gemini 3 Flash Preview for filtering |
| AskFilo | text+image | 41,807 | Qwen3.5-122B-A10B, Gemini 3 Flash Preview for filtering |
| Raven | text+image | 41,996 | gpt-oss-120b |
| DocVQA | text+image | 35,759 | Qwen3.5-122B-A10B |
| TextVQA | text+image | 34,602 | Commercial VILA model, Qwen3-VL-30B-A3B-Instruct |
| COCO | text+image | 32,111 | Qwen3.5-122B-A10B, Gemini 3 Flash Preview for filtering |
| PlotQA | text+image | 30,665 | Qwen3.5-122B-A10B, Gemini 3 Flash Preview for filtering |
| Llava | text+video | 30,250 | Qwen3-Omni-30B-A3B-Instruct, Qwen3-VL-32B-Instruct |
| NVCLIP | text+image | 29,680 | Qwen2.5-72B-Instruct |
| Tapos | text+video | 29,250 | Qwen2.5-VL-72B-Instruct |
| Vedantu Chemistry | text+audio | 26,338 | NVIDIA Magpie TTS |
| NV-CC-Img-Text-Dataset | text+image | 24,998 | Qwen3-VL-30B-A3B-Instruct |
| DocLayNet | text+image | 22,709 | Qwen3.5-122B-A10B, Gemini 3 Flash Preview for filtering, gpt-oss-120b |
| Taloka Grounding | text+image | 22,218 | Qwen3.5-122B-A10B, Gemini 3 Flash Preview for filtering |
| Wikipedia OCR | text+image | 21,440 | Qwen3.5-122B-A10B, Gemini 3 Flash Preview for filtering |
| InternVL2.5 | text+image | 20,770 | Qwen3-VL-235B-A22B-Instruct, Qwen3-VL-235B-A22B-Thinking, GPT-4o for filtering, Qwen3.5-122B-A10B |
| PromptPG | text+image | 20,305 | Qwen2-VL-72B |
| PubTables | text+image | 20,174 | gpt-oss-120b |
| InfoVQA | text+image | 18,679 | Qwen3.5-122B-A10B, Gemini 3 Flash Preview for filtering |
| Azure Tables | text+image | 18,188 | gpt-oss-120b, Qwen3.5-122B-A10B |
| TabRecSet | text+image | 17,437 | GPT-4o mini, Qwen3-VL-30B-A3B-Thinking-FP8, gpt-oss-120b, Qwen3.5-122B-A10B |
| CD Questions | text+audio, text+image | 16,335 | NVIDIA Magpie TTS, Qwen3.5-122B-A10B, Gemini 3 Flash Preview for filtering |
| Linguistic Data Consortium | text+image | 15,499 | Qwen3.5-122B-A10B, GPT-4o mini, Qwen3-VL-30B-A3B-Thinking-FP8, gpt-oss-120b, Ask Kateryna |
| MapQA | text+image | 12,480 | Qwen3.5-122B-A10B, Gemini 3 Flash Preview for filtering |
| SlideVQA | text+image | 11,199 | Qwen3.5-122B-A10B |
| OCR Reason Finance | text+image | 9,389 | Qwen3.5-122B-A10B, Gemini 3 Flash Preview for filtering |
| GeomVerse | text+image | 9,298 | GLM-4.1V-9B-Thinking |
| NextQA | text+video | 8,903 | Qwen3.5-122B-A10B, Gemini 3 Flash Preview for filtering |
| UniGeo | text+image | 8,822 | Qwen3.5-122B-A10B, Gemini 3 Flash Preview for filtering |
| Vedantu | text+audio, text+image | 8,750 | NVIDIA Magpie TTS, Qwen3.5-122B-A10B, Gemini 3 Flash Preview for filtering |
| GPQA | text+audio | 7,657 | NVIDIA Magpie TTS |
| SLAKE | text+image | 7,294 | Qwen3.5-122B-A10B, Gemini 3 Flash Preview for filtering |
| OpenGVLab | text+image | 7,269 | Qwen3.5-122B-A10B, Gemini 3 Flash Preview for filtering, Qwen3-VL-235B-A22B-Instruct, Qwen3-VL-235B-A22B-Thinking, GPT-4o for filtering |
| PerceptionTest | text+video | 5,192 | Qwen3.5-122B-A10B, Gemini 3 Flash Preview for filtering |
| InvoicesQA | text+image | 4,817 | Qwen3.5-122B-A10B |
| EgoProcel | text+video | 4,660 | Qwen2.5-VL-72B-Instruct |
| SynthTabNet | text+image | 4,364 | gpt-oss-120b |
| SerpAPI | text+image | 3,784 | Qwen3.5-122B-A10B, Gemini 3 Flash Preview for filtering |
| FinTabNet | text+image | 3,852 | gpt-oss-120b |
| FastMath | text+image | 3,718 | Qwen3-VL-235B-A22B-Instruct-FP8 |
| ASR Data Derived Speech-to-Text Chat Data | text+audio | 3,608 | GPT-OSS 120B |
| Geometry3k | text+image | 2,078 | Qwen3-VL-235B-A22B-Thinking-FP8 |
| VQA-RAD | text+image | 1,270 | Qwen3.5-122B-A10B |
| RQA | text+audio | 959 | NVIDIA Magpie TTS |
| HierText OCRQA Qwen | text+image | 514 | Qwen2.5-VL-32B-Instruct |
<br>

## Training Dataset:

**Data Modality** <br>
* Audio <br>
* Image <br>
* Text <br>
* Video <br>

**Audio Training Data Size** <br>
* 10,000 to 1 Million Hours <br>
(267,898,865 audio-containing samples) <br>

**Image Training Data Size** <br>
* 1 Million to 1 Billion Images <br>
(70,143,901 image-containing samples) <br>

**Text Training Data Size** <br>
* 1 Billion to 10 Trillion Tokens <br>
(~717.0B tokens total across all modalities) <br>

**Video Training Data Size** <br>
* 10,000 to 1 Million Hours <br>
(24,557,717 video-containing samples) <br>

**Data Collection Method by dataset** <br>
* Hybrid: Human, Automated, Synthetic <br>

**Labeling Method by dataset** <br>
* Hybrid: Human, Automated, Synthetic <br>

**Properties (Quantity, Dataset Descriptions, Sensor(s)):** 354,587,705 total data items across 1395 datasets. The training data spans five modality combinations: text+audio (259,178,821 samples), text+image (70,143,901 samples), text+video (15,837,673 samples), text+video+audio (8,720,044 samples), and text-only (707,187 samples). Content includes publicly available academic datasets, licensed third-party data, NVIDIA-internal collections, and synthetically generated annotations. The data is primarily in English. No sensor-derived data was used. <br>

For more information about the datasets used to train this model, please see the [Public Summary of Training Content](https://developer.download.nvidia.com/assets/nemo/docs/public-summary-of-training-content-for-nvidia-nemotron.pdf) <br>

### Evaluation Dataset:

**Benchmark Scores:** <br>

| Task | Multimodal Benchmarks | Nemotron 3 Nano Omni | Nemotron Nano VL V2 | % Improvement |
|---|---|---|---|---|
| Grounding | CVBench2D | 83.95 | 78.3 | 6.73 |
| Document | OCRBenchV2 (EN) | 67.04 | 54.8 | 18.26 |
| Computer Use | OSWorld | 47.4 | 11.1 | 76.58 |
| Chart Reasoning | Charxiv Reasoning | 63.6 | 41.3 | 35.06 |
| Multi-Image Reasoning | MMlongBench Doc | 57.5 | 38 | 33.91 |
| Math Reasoning | MathVista_MINI | 82.8 | 75.5 | 8.82 |
| OCR Reasoning | OCR_Reasoning | 54.14 | 33.9 | 33.87 |
| Video Q/A | Video MME | 72.2 | - | - |
| Video + Audio Q/A | World Sense | 55.4 | - | - |
| Video + Audio Q/A | Daily Omni | 74.52 | - | - |
| Speech Instruction Following | Voice interaction | 89.39 | - | - |

**Quantization Benchmark Scores:** <br>

We release FP8 and NVFP4 quantized variants alongside the BF16 model. The FP8 variant quantizes every linear layer in the language model to per-tensor E4M3 (with the exception of the MoE router and `lm_head`) and pairs it with an FP8 KV cache, yielding 8.5 effective bits per weight (32.8 GB). The NVFP4 variant uses a mixed-precision recipe inspired by Nemotron 3 Super: routed MoE experts are quantized to NVFP4 (FP4 E2M1 values with per-block FP8 E4M3 scales over groups of 16 elements and an additional per-tensor FP32 global scale), while the Mamba `in_proj` / `out_proj`, shared experts, and attention `o_proj` are quantized to FP8, yielding 4.98 effective bits per weight (20.9 GB). In both variants the vision and audio encoders and their MLP projectors are kept in BF16. <br>

The table below reports FP8 & NVFP4 accuracy against a BF16 baseline using non-reasoning mode. Across 9 multimodal benchmarks, both quantized variants stay within 1 point of BF16 on average.

| Footprint | BF16 | FP8 | NVFP4 |
|---|---|---|---|
| Size (GB) | 61.5 | 32.8 | 20.9 |
| Effective bpw | 16.00 | 8.5 | 4.98 |

| Benchmark | BF16 | FP8 | NVFP4 |
|---|---|---|---|
| MathVista_MINI | 71.90 | 71.05 | 71.30 |
| Charxiv Reasoning | 49.10 | 48.05 | 47.95 |
| MMlongBench Doc | 46.10 | 45.84 | 45.78 |
| OCRBenchV2 (EN) | 65.80 | 65.63 | 65.77 |
| CVBench2D | 84.20 | 85.62 | 85.27 |
| Video MME | 70.80 | 69.40 | 69.60 |
| Daily Omni | 74.50 | 74.06 | 74.23 |
| World Sense | 55.20 | 54.40 | 54.60 |
| MMAU | 74.62 | 74.56 | 74.34 |
| Tedium Long (WER↓) | 3.11 | 3.12 | 3.04 |
| HF-ASR (WER↓) | 5.95 | 5.97 | 5.95 |
| **Mean (9 non-ASR)** | **65.80** | **65.40** | **65.43** |
| **Median (9 non-ASR)** | **70.80** | **69.40** | **69.60** |
| **Δ vs BF16 (mean)** | --- | −0.40 | −0.38 |

Data Collection Method by dataset: <br>
* Hybrid: Human, Automated — Evaluation benchmarks are primarily human-curated public academic datasets with automated scoring. <br>

Labeling Method by dataset: <br>
* Human <br>

**Properties (Quantity, Dataset Descriptions, Sensor(s)):** 14 evaluation benchmarks spanning image understanding (MathVistaMini, Charxiv Reasoning, MMLongBench-Doc, OCR Reasoning, OCRBenchV2 English, CVBench2D, OSWorld), video understanding (Video MME), audio/speech understanding (VoiceBench, Tedium Long, HF-ASR, MMAU, World Sense), and multimodal omni-understanding (Daily Omni). All benchmarks are publicly available academic datasets in English. <br>

Prior to training this model, NVIDIA implemented measures to respect EU text and data mining opt-outs by (1) respecting robots.txt instructions to the extent such signals reflect valid rights reservations, and (2) filtering datasets on any actionable metadata identifiers provided by rightsholders.

# Inference:
**Acceleration Engine:** vLLM <br>
**Test Software:** vLLM <br>
**Test Hardware:** <br>
* NVIDIA H100 x2 <br>

# Best Practices

We recommend following settings for reaching the optimal performance.

### Sampling Parameters
We suggest the following sampling parameters based on the mode and tasks.
* Thinking mode for long document analysis and multimodal reasoning tasks: <br>
`temperature=0.5-0.7`, `top_p=0.95`, `grace_period=1024`, `reasoning_budget=16384`, `max_token=20480`, and `max_model_len=210000`<br>
* Instruct mode (non-thinking) for general tasks:<br>
`temperature=0.2`, `top_k=1`<br>
* For ASR tasks, we recommend non-thinking mode with
`temperature=0.2`, `top_k=1`<br>

### Model output length
For most multimodel reasoning tasks, we recommend using output length of at least 20480. For complex reasoning questions especially in math and programing increasing the maximum output length to 131072 tokens can give the model enough room to produce more detailed and correct answers. We also found the proposed Budget-Controlled Reasoning effectiveness in answering complex reasoning questions.

## Ethical Considerations:
NVIDIA believes Trustworthy AI is a shared responsibility and we have established policies and practices to enable development for a wide array of AI applications. When downloaded or used in accordance with our terms of service, developers should work with their internal model team to ensure this model meets requirements for the relevant industry and use case and addresses unforeseen product misuse. <br>

Please make sure you have proper rights and permissions for all input image and video content; if image or video includes people, personal health information, or intellectual property, the image or video generated will not blur or maintain proportions of image subjects included. <br>

For more detailed information on ethical considerations for this model, please see the Model Card++ Bias, Explainability, Safety & Security, and Privacy Subcards. <br>

Please report model quality, risk, security vulnerabilities or NVIDIA AI Concerns [here](https://www.nvidia.com/en-us/support/submit-security-vulnerability/). <br>

## Specifications

- **Context Length:** 262,144 tokens
- **Parameters:** 33,015,632,214
- **Input:** Video, Audio, Image, Text
- **Output:** Text

## Capabilities

- **Function Calling:** Supported
- **Structured Output:** Not supported
- **Reasoning:** Supported

## Bias

Field                                                                                               |  Response
:---------------------------------------------------------------------------------------------------|:---------------
Participation considerations from adversely impacted groups [protected classes](https://calcivilrights.ca.gov/disputeresolution/protected-characteristics/) in model design and testing:  |  None
Bias Metric (If Measured):                                                   |  [BBQ Accuracy Scores in Ambiguous Contexts](https://github.com/nyu-mll/BBQ/). The model may have some quality concerns for English spoken by a few non-native English speakers.
Which characteristic (feature) show(s) the greatest difference in performance?: |  The model has been evaluated across multiple benchmarks spanning STEM reasoning, video understanding, document intelligence, GUI tasks, and audio transcription. Performance differences may appear across input modalities (e.g., audio vs. video) and across benchmark complexity levels. Specific per-characteristic bias metrics have not been separately measured for this release.
Which feature(s) have have the worst performance overall? | Audio-related tasks such as speaker diarization and multi-lingual speech are out of scope for V3. Audio event detection and speech instruction following are P1 priorities. Performance on far-field microphone audio and noisy environments (SNR below 10 dB) may be limited.
Measures taken to mitigate against unwanted bias:                                                   |  Training data includes a blend of diverse, curated datasets across modalities (text, image, video, audio). Data integrity filters are applied to chat, social sciences, and safety domains. VLM dehumanization safety benchmarks are part of the evaluation pipeline. RL recipes for security improvements are applied during post-training.
If using internal data, description of methods implemented in data acquisition or processing, if any, to address the prevalence of identifiable biases in the training, testing, and validation data: | Synthetic data generation pipelines use approved seed data and approved models. Data processing includes deduplication, filtering, and quality assessment (low, medium, high). Distribution analysis is performed across domains (math, code, etc.), languages, data types, and token lengths. Safety evaluations are conducted to identify and mitigate biases.
Tools used to assess statistical imbalances and highlight patterns that may introduce bias into AI models: | AEGIS 1.0, Garak, RTVLM, VLGuard, internal competitive evaluation (VPR) tool, and NVIDIA Custom Datasets focused on child safety and dehumanization risks.

## Explainability

Field                                                                                                  |  Response
:------------------------------------------------------------------------------------------------------|:---------------------------------------------------------------------------------
Intended Task/Domain:                                                                   |  Multi-modal understanding and generation: Video+Audio understanding, Document Intelligence (OCR, chart reasoning, long-document comprehension), GUI/Agentic tasks (computer use agents), Speech Transcription (ASR), and Visual Question Answering.
Model Type:                                                                                            |  Transformer
Intended Users:                                                                                        |  Enterprise developers and AI practitioners building multi-modal AI applications, including conversational AI, video and audio analysis, document processing, and agentic workflows.
Output:                                                                                                |  Text (responds to posed questions across text, image, video, and audio inputs; supports reasoning with chain-of-thought, tool calling, JSON output, and word-level timestamps for transcription).
Tools used to evaluate datasets to identify synthetic data and ensure data authenticity. | Synthetic data generation pipelines use approved seed data and approved generation models. The pipeline is tracked by domain, generating model, data type, token length, and quality level. Distribution analytics are produced for both pre-training and post-training datasets.
Describe how the model works:                                                                          |  The model combines three encoders: a Nemotron Nano V3 LLM backbone (31B MoE, ~3B active), a CRADIO v4-H vision encoder, and a Parakeet speech encoder. Image and video inputs are encoded into visual tokens via the Eagle vision architecture, audio inputs are encoded via the Parakeet encoder, and all modality tokens are concatenated with text tokens before being processed by the transformer-based language model to produce text outputs.
Name the adversely impacted groups this has been tested to deliver comparable outcomes regardless of:  |  Age, Disability Status, Gender Identity, Nationality, Physical Appearance, Ethnicity, Socioeconomic Status, Sexual Orientation, Religion
Technical Limitations & Mitigation:                                                                    |  This model supports English only for speech inputs. Audio other than speech is out of scope. Speaker diarization, translation, temporal understanding (timestamps correlating audio and video), multi-lingual capability, and streaming audio/video are not supported in V3. Video input is limited to under 2 minutes at 1 FPS (max 128 frames). Performance may vary across different GPU configurations and precision formats.
Verified to have met prescribed NVIDIA quality standards:  |  Yes
Performance Metrics:                                                                                   |  Accuracy (MMMU, MathVista, Video-MME, OCRBench V2, Charxiv, MMLongBench-Doc, ScreenSpot Pro, WorldSense, HF OpenASR WER, Librispeech, GPQA Diamond, SWE-bench Verified, IF Bench, Tau2 Bench), Latency (TTFT), Throughput (tokens per second)
Potential Known Risks:                                                                                 |  The model may produce inaccurate transcriptions in noisy environments or with non-English audio. OCR accuracy may be impacted by low-resolution inputs.<br> The model may generate incorrect or hallucinated content when processing ambiguous multi-modal inputs. The model may exhibit self-anthropomorphism (e.g., displaying human-like characteristics in dialogue, such as expressing preferences and emotions).<br>  The model was trained on data that contains toxic language and societal biases originally crawled from the internet. Therefore, the model may generate and amplify harmful, biased, or otherwise unsafe content reinforcing these biases and return toxic responses especially when prompted with toxic prompts. <br> The model may also generate answers that may be inaccurate, omit key information, or include irrelevant or redundant text producing socially unacceptable or undesirable text, even if the prompt itself does not include anything explicitly offensive. 
Licensing:                                                                                             | Governing Terms: This trial service is governed by the [NVIDIA API Trial Terms of Service](https://assets.ngc.nvidia.com/products/api-catalog/legal/NVIDIA%20API%20Trial%20Terms%20of%20Service.pdf). Use of this model is governed by the [NVIDIA Open Model Agreement](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-agreement/).

<br>

## Privacy

| Privacy Information |
| --- |
| NVIDIA Nemotron Omni was trained on large-scale publicly available data that may contain images, audio-video, and text relating to people. NVIDIA collected and used this data in compliance with applicable data protection and privacy laws. This model was not designed to specifically derive insights or otherwise learn from any personal data contained in the datasets. |
| NVIDIA uses a combination of filters, data minimization techniques, and other guardrails to help prevent personal data from being recited by our models. We employ automated tools and data processing techniques during pre-training or training to identify and filter certain categories of personal data. |
| Please review NVIDIA's Applicable [Privacy Policy](https://www.nvidia.com/en-us/about-nvidia/privacy-policy/) for more information. |

## Safety & Security

Field                                               |  Response
:---------------------------------------------------|:----------------------------------
Model Application Field(s):                               |  Customer Service, Media & Entertainment, Healthcare (Document Intelligence), Financial Services (Document Intelligence)<br> |
Describe the life critical impact (if present) |  Not Applicable
Description of methods implemented in data acquisition or processing, if any, to address other types of potentially harmful data in the training, testing, and validation data: | Training data undergoes multi-stage processing including deduplication, filtering, and quality assessment. Data integrity filters are applied to chat, social sciences, and safety domains. Safety evaluations were conducted using AEGIS v2, Garak, RTVLM, and VLGuard, as well as NVIDIA Custom Datasets focused on child safety and dehumanization risks. RL recipes for security improvements are applied during post-training. Ablation studies for safety were conducted, and video safety and omni-specific benchmarks are investigated. An over-refusal evaluation is also performed to balance safety with model utility.
Description of any methods implemented in data acquisition or processing, if any, to address illegal or harmful content in the training data, including, but not limited to, child sexual abuse material (CSAM) and non-consensual intimate imagery (NCII) | Content safety is evaluated using NVIDIA Custom Datasets focused on child safety and dehumanization risks. AEGIS 1.0 evaluation covers 13 content safety categories with a required >=95% overall score AND 0 items under the sexual (minor) category. Qualitative review is conducted for every prompt/response under the suicide and self-harm category. Safety evaluations are run with both Reasoning ON and OFF modes.
Use Case Restrictions:                              |  Governing Terms: This trial service is governed by the [NVIDIA API Trial Terms of Service](https://assets.ngc.nvidia.com/products/api-catalog/legal/NVIDIA%20API%20Trial%20Terms%20of%20Service.pdf). Use of this model is governed by the [NVIDIA Open Model Agreement](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-agreement/).<br>|
Model and dataset restrictions:            |  The Principle of least privilege (PoLP) is applied limiting access for dataset generation and model development. Restrictions enforce dataset access during training, and dataset license constraints adhered to. <br> |
Responsible data handling:  | This AI model was developed based on our policies to ensure responsible data handling and risk mitigation. The datasets used for training have been scanned for harmful content and illegal content, consistent with our policies including scanning for Child Sexual Abuse Material (CSAM). Ongoing review and monitoring mechanisms are in place based on our policies and to maintain data integrity.

## Prototype

```python
import requests

invoke_url = "https://integrate.api.nvidia.com/v1/chat/completions"
stream = False

headers = {
"Authorization": "Bearer $NVIDIA_API_KEY",
"Accept": "text/event-stream" if stream else "application/json",
}

payload = {
"messages": [
{
"role": "user",
"content": ""
}
]
}

response = requests.post(invoke_url, headers=headers, json=payload, stream=stream)
if stream:
for line in response.iter_lines():
if line:
print(line.decode("utf-8"))
else:
print(response.json())
```

```python
from langchain_nvidia_ai_endpoints import ChatNVIDIA

client = ChatNVIDIA(
model="",
api_key="$NVIDIA_API_KEY",
temperature=,

max_completion_tokens=,
)

lc_messages = [
{
"role": "user",
"content": "",
},
]

response = client.invoke(lc_messages)
if response.additional_kwargs and "reasoning_content" in response.additional_kwargs:
print(response.additional_kwargs["reasoning_content"])
print(response.content)
```

```javascript
import axios from 'axios';

const invokeUrl = "https://integrate.api.nvidia.com/v1/chat/completions";
const stream = ;

const headers = {
"Authorization": "Bearer $NVIDIA_API_KEY",
"Accept": stream ? "text/event-stream" : "application/json"
};

async function main() {
const payload = {"messages":[{"role":"user","content":""}]};

const response = await axios.post(invokeUrl, payload, {
headers: headers,
responseType: stream ? 'stream' : 'json'
});

if (stream) {
response.data.on('data', (chunk) => {
console.log(chunk.toString());
});
} else {
console.log(JSON.stringify(response.data));
}
}

main().catch(error => {
if (error.response) {
console.error(`HTTP ${error.response.status}`);
if (error.response.data?.on) {
error.response.data.on('data', (chunk) => console.error(chunk.toString()));
} else {
console.error(error.response.data);
}
} else {
console.error(error);
}
});
```

```bash
stream=
if [ "$stream" = true ]; then
accept_header='Accept: text/event-stream'
else
accept_header='Accept: application/json'
fi

cat > payload.json <<JSON
{"messages":[{"role":"user","content":""}]}
JSON

curl https://integrate.api.nvidia.com/v1/chat/completions \
-H "Authorization: Bearer $NVIDIA_API_KEY" \
-H "Content-Type: application/json" \
-H "$accept_header" \
-d @payload.json
```