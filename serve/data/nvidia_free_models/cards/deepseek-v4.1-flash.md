---
title: "deepseek-v4.1-flash"
publisher: "deepseek-ai"
type: "endpoint"
updated: "2026-09-18T18:55:17.986Z"
description: "552B MoE, 8B active params with native multimodal support and lower API cost using smaller KV cache"
canonical: "https://build.nvidia.com/deepseek-ai/deepseek-v4.1-flash"
---

# DeepSeek-V4.1-Flash

## Description
DeepSeek-V4.1-Flash is a multimodal mixture-of-experts model from DeepSeek-AI that accepts text and images, generates text autoregressively, supports a combined context of up to one million tokens, and provides continuously controllable reasoning effort.

*This model is ready for commercial or non-commercial use.*

## Third-Party Community Consideration:
This model is not owned or developed by NVIDIA. This model has been developed and built to a third-party's requirements for this application and use case; see link to Non-NVIDIA [DeepSeek-V4.1-Flash Model Card](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash)

## License and Terms of Use:
**GOVERNING TERMS**: This trial service is governed by the [NVIDIA API Trial Terms of Service](https://assets.ngc.nvidia.com/products/api-catalog/legal/NVIDIA%20API%20Trial%20Terms%20of%20Service.pdf); and the use of this model is governed by the [NVIDIA Open Model Agreement](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-agreement/). ADDITIONAL INFORMATION: The base model DeepSeek V4.1 Flash is governed by the [MIT License](https://huggingface.co/datasets/choosealicense/licenses/blob/main/markdown/mit.md).

## Deployment Geography:
Global

## Use Case:
**Use Case:** DeepSeek-V4.1-Flash is intended for long-context multimodal reasoning, coding, document understanding, and tool-using agentic applications that consume text and images and generate text.

## Release Date:
**Build.NVIDIA.com:** 09/18/2026 via [link](https://build.nvidia.com/deepseek-ai/deepseek-v4.1-flash)  
**Huggingface:** 09/10/2026 via [link](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash)

## Reference(s):
**References:**
- [DeepSeek-V4.1-Flash Technical Report](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash/blob/main/DeepSeek_V41_Tech_Report.pdf)
- [DeepSeek Recipe](https://github.com/deepseek-ai/deepseek-recipe)
- [DeepSeek Homepage](https://www.deepseek.com/)

## Model Architecture:
**Architecture Type:** Transformer  
**Network Architecture:** Mixture-of-Experts  
**Total Parameters:** 552B  
**Active Parameters:** 8B (prefill), 16B (decode)  
**Vocabulary Size:** 129,280

### Input:
**Input Types:** Image, Text  
**Input Formats:** Red, Green, Blue (RGB), String  
**Input Parameters:** Two-Dimensional (2D), One-Dimensional (1D)  
**Other Input Properties:** The vision configuration supports up to 1,024 image tokens and specifies a minimum image area of 295,936 pixels; the reference encoder supports interleaved image and text content.

### Output:
**Output Types:** Text  
**Output Format:** String  
**Output Parameters:** One-Dimensional (1D)  
**Other Output Properties:** Combined input and output context length is 1,048,576 tokens; the prompt protocol supports thinking content, tool calls, and structured API responses.

__Our AI models are designed and/or optimized to run on NVIDIA GPU-accelerated systems. By leveraging NVIDIA's hardware (e.g. GPU cores) and software frameworks (e.g., CUDA libraries), the model achieves faster training and inference times compared to CPU-only solutions.__

## Software Integration:
**Runtime Engines:**
- **Transformers:** 5.6.0
- **vLLM**

**Supported Hardware:**
- **NVIDIA Blackwell:** B100, B200, GB200
- **NVIDIA Hopper:** H200

**Preferred Operating Systems:** Linux

__The integration of foundation and fine-tuned models into AI systems requires additional testing using use-case-specific data to ensure safe and effective deployment. Following the V-model methodology, iterative testing and validation at both unit and system levels are essential to mitigate risks, meet technical and functional requirements, and ensure compliance with safety and ethical standards before deployment.__

## Model Version(s)
DeepSeek-V4.1-Flash v4.1

## Training, Testing, and Evaluation Datasets:

### Training Dataset
**Data Modality:** Image, Text  
**Image Training Data Size:** Undisclosed  
**Text Training Data Size:** Undisclosed  
**Training Data Collection:** Undisclosed  
**Training Labeling:** Undisclosed  
**Training Properties:** The model was trained from scratch on a multimodal corpus comprising 45T tokens, with sparse attention trained at a 64K-token sequence length and context extended to 1M tokens at 34T tokens. Post-training used supervised fine-tuning, reinforcement learning, and on-policy distillation with large-scale automated synthesis of agent tasks and environments; the source does not disclose corpus names, licenses, or collection and labeling procedures.

### Testing Dataset
**Testing Data Collection:** Undisclosed  
**Testing Labeling:** Undisclosed  
**Testing Properties:** Undisclosed

### Evaluation Dataset
**Evaluation Data Collection:** Hybrid: Automated, Manually-Collected  
**Evaluation Labeling:** Hybrid: Automated, Manually-Labeled  
**Evaluation Properties:** Base models were evaluated in DeepSeek's internal framework under the same settings, and scores within 0.3 were considered equivalent. Instruct evaluations used `reasoning_effort=100`, `temperature=1.0`, and `top_p=0.95`; the benchmark results and methodology below are reported by DeepSeek-AI and do not represent independent NVIDIA verification.  
**Evaluation Benchmark Score:** DeepSeek-V4.1-Flash-Base reported scores across knowledge, reasoning, coding, mathematics, long-context, and multimodal benchmarks; the instruct model reported 90.9 GPQA Diamond Pass@1, 90.6 Terminal-Bench 2.1 Pass@1, 74.2 DeepSWE v1.1 resolved, 88.1 CyberGym Pass@1, 54.8 AutomationBench Pass@1, and 31.8 Agent's Last Exam Pass@1.  

<details>
<summary><strong>Base Model Benchmark Results</strong></summary>

| Benchmark (Metric) | Shots | DeepSeek-V4.1-Flash-Base |
| --- | ---: | ---: |
| AGIEval (EM) | 3–5-shot | 83.4 |
| MMLU-Pro (EM) | 5-shot | 74.1 |
| C-Eval (EM) | 5-shot | 92.1 |
| MultiLoKo (LLM-Judge) | 5-shot | 45.5 |
| SimpleQA-Verified (EM) | 25-shot | 42.3 |
| SuperGPQA (EM) | 5-shot | 53.1 |
| BBH (EM) | 3-shot | 86.1 |
| BBEH (EM) | 1-shot | 27.2 |
| DROP (F1) | 1-shot | 87.9 |
| HellaSwag (EM) | 0-shot | 87.2 |
| BigCodeBench (Pass@1) | 3-shot | 60.6 |
| HumanEval (Pass@1) | 0-shot | 79.4 |
| GSM8K (EM) | 8-shot | 93.0 |
| MATH (EM) | 4-shot | 61.1 |
| MGSM (EM) | 8-shot | 80.2 |
| LongBench-V2 (EM) | 1-shot | 45.2 |
| MMMU-Pro (EM) | 4-shot | 56.5 |
| CVBench (EM) | 4-shot | 77.9 |
| DocVQA (LLM-Judge) | 4-shot | 95.6 |
| RefCOCO-avg (Acc@0.5) | 0-shot | 86.0 |

</details>

<details>
<summary><strong>Instruct Model Benchmark Results</strong></summary>

| Benchmark (Metric) | DeepSeek-V4.1-Flash |
| --- | ---: |
| GPQA Diamond (Pass@1) | 90.9 |
| HLE (Pass@1) | 36.8 (39.1†) |
| Codeforces (Rating) | 3471 |
| MathArena Apex (Pass@1) | 65.6 |
| Terminal-Bench 2.1 (Pass@1) | 90.6 |
| Terminal-Bench 3.0 (Pass@1) | 30.0 |
| Terminal-Bench 4.0 (Pass@1) | 31.2 |
| DeepSWE v1.1 (Resolved) | 74.2 |
| ProgramBench (Almost@1) | 20.3 |
| NL2Repo-Bench (Score) | 64.0 |
| CyberGym (Pass@1) | 88.1 |
| SEC-Bench Pro (Pass@1) | 62.8 |
| ExploitGym (Pass@1) | 15.3 |
| HLE with tools (Pass@1) | 63.9 |
| AutomationBench (Pass@1) | 54.8 |
| Agent's Last Exam (Pass@1) | 31.8 |
| Chartography with tools (Pass@1) | 78.9 |
| BabyVision with tools (Pass@1) | 89.6 |
| ZeroBench-main with tools (Pass@5) | 49.0 |

† Text-only subset of HLE.

</details>

<details>
<summary><strong>Evaluation Methodology and Agent Scaffold Results</strong></summary>

- Code-agent benchmarks used the Minimal mode of DeepSeek Harness and a 1M-token context window. DeepSWE v1.1 used the mini-SWE harness, SEC-Bench Pro used Claude Code, and visual-agent benchmarks used Claude Code with a 512K-token context window. Agent's Last Exam and AutomationBench used their official scaffolds.
- Scaffold comparisons used eight samples per task for DeepSWE v1.1 and three samples per task for Terminal-Bench 2.1, Linux containers, `temperature=1.0`, `top_p=0.95`, a 1M-token context limit, and `max_steps=500`. Terminal-Bench 2.1 ran without network access.

| Benchmark (Metric) | Claude Code | Codex | OpenCode | Pi | mini-SWE | DSH Minimal | DSH Standard | DSH PTC |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DeepSWE v1.1 (Resolved) | 69.8 | 65.6 | 65.5 | 66.2 | 74.2 | 72.6 | 70.5 | 67.6 |
| Terminal-Bench 2.1 (Pass@1) | 88.0 | 84.1 | 85.0 | 86.1 | 90.3 | 90.6 | 85.8 | 85.8 |

</details>

## Inference
**Acceleration Engine:** vLLM  
**Test Hardware:** NVIDIA Hopper (H200)

## Additional Details
### Architecture and KV Cache
DeepSeek-V4.1-Flash uses a 40-layer Causal Encoder-Decoder Transformer with a 20-layer causal encoder and a 20-layer decoder. It combines Compressed Sparse Attention 2, SWA Bounded Replay, FP4 main KV caching, Single-Pass mHC, a 196B-parameter Engram conditional memory, and DSpark speculative decoding; the source reports a persistent global KV cache footprint of 890 bytes per token.

Each mixture-of-experts layer has one shared expert and 384 routed experts, with six routed experts activated per token. DeepSeek-ViT, trained from scratch with two-dimensional rotary position embeddings and 3×3 pixel-unshuffle downsampling, feeds visual embeddings through a two-layer MLP projector for joint image-and-text processing.

### Prompt Encoding and Deployment
This release does not include a Jinja-format chat template. Its reference encoding supports multi-turn conversations, tool calling, thinking mode, numeric reasoning effort from 1 to 100, mid-conversation system messages, and interleaved image content; model inference, tool execution, and HTTP transport remain the caller's responsibility.

The source recommends `temperature=1.0`, `top_p=0.95` or `1.0`, a 1M-token context window, and `max_tokens` of at least 256K.

## Ethical Considerations
NVIDIA believes Trustworthy AI is a shared responsibility and we have established policies and practices to enable development for a wide array of AI applications. Developers should work with their internal model team to ensure this model meets requirements for the relevant industry and use case and addresses unforeseen product misuse.

Please make sure you have proper rights and permissions for all input image content; if image includes people, personal health information, or intellectual property, the image generated will not blur or maintain proportions of image subjects included.

Users are responsible for model inputs and outputs. Users are responsible for ensuring safe integration of this model, including implementing guardrails as well as other safety mechanisms, prior to deployment.

Please report model quality, risk, security vulnerabilities or NVIDIA AI Concerns [here](https://www.nvidia.com/en-us/support/submit-security-vulnerability/)

## Specifications

- **Context Length:** 1,048,576 tokens
- **Parameters:** 552B
- **Input:** Text, Image
- **Output:** Text

## Capabilities

- **Function Calling:** Supported
- **Reasoning:** Supported

## Prototype

```python
import json
import os
from openai import OpenAI

client = OpenAI(
base_url = "https://integrate.api.nvidia.com/v1",
api_key = os.environ["NVIDIA_API_KEY"]
)

completion = client.chat.completions.create(
model="deepseek-ai/deepseek-v4.1-flash",
messages=json.loads("[{\"role\":\"user\",\"content\":\"\"}]"),
temperature=,
top_p=,
max_tokens=,
stream=NaN
)

print(completion.choices[0].message)
```

```javascript
import OpenAI from 'openai';

const openai = new OpenAI({
apiKey: process.env.NVIDIA_API_KEY,
baseURL: 'https://integrate.api.nvidia.com/v1',
})

async function main() {
const completion = await openai.chat.completions.create({
model: "deepseek-ai/deepseek-v4.1-flash",
messages: [{"role":"user","content":""}],
temperature: ,
top_p: ,
max_tokens: ,
stream: ,
})

console.log(completion.choices[0]?.message);

}

main();
```

```bash
curl --fail --show-error --no-buffer https://integrate.api.nvidia.com/v1/chat/completions \
-H "Content-Type: application/json" \
-H "Authorization: Bearer $NVIDIA_API_KEY" \
--data-binary @- <<'JSON'
{
"model": "deepseek-ai/deepseek-v4.1-flash",
"messages": [{"role":"user","content":""}],
"temperature": ,
"top_p": ,
"max_tokens": ,
"stream": 
}
JSON
```