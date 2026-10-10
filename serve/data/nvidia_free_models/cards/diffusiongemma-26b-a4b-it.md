---
title: "diffusiongemma-26b-a4b-it"
publisher: "google"
type: "endpoint"
updated: "2026-06-10T18:07:50.386Z"
description: "Diffusion-based 26B parameter LLM enabling parallel token generation for real-time text apps"
canonical: "https://build.nvidia.com/google/diffusiongemma-26b-a4b-it"
---

# DiffusionGemma 26B A4B IT

## Description:
DiffusionGemma 26B A4B IT is an open-weights multimodal generative model developed by Google DeepMind that processes text, image, and video inputs to produce text output via discrete diffusion. Built on the Gemma 4 26B A4B Mixture-of-Experts (MoE) architecture with 25.2B total parameters and 3.8B active parameters, the model employs an encoder-decoder design with bidirectional attention that generates tokens in parallel 256-token blocks, enabling high-speed generation exceeding 1,100 tokens per second at low batch sizes on NVIDIA Hopper H100 (FP8). DiffusionGemma 26B A4B IT supports a 256K token context window, configurable thinking (reasoning) mode, native function calling, and multilingual inference across 35+ languages.

*This model is ready for commercial or non-commercial use.*

## Third-Party Community Consideration:
This model is not owned or developed by NVIDIA. This model has been developed and built to a third-party's requirements for this application and use case; see link to Non-NVIDIA [DiffusionGemma 26B A4B IT Model Card](https://huggingface.co/google/diffusiongemma-26B-A4B-it)

## License and Terms of Use:
**GOVERNING TERMS:** The trial service is governed by the [NVIDIA API Trial Terms of Service](https://assets.ngc.nvidia.com/products/api-catalog/legal/NVIDIA%20API%20Trial%20Terms%20of%20Service.pdf). Use of the model is governed by the [NVIDIA Open Model Agreement](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-agreement/). Additional Information: [Apache 2.0](https://ai.google.dev/gemma/apache_2). [Gemma Terms of Use](https://ai.google.dev/gemma/terms) and [Gemma Prohibited Use Policy](https://ai.google.dev/gemma/prohibited_use_policy).

## Deployment Geography:
Global

## Use Case:
**Use Case:** DiffusionGemma 26B A4B IT is designed for developers, researchers, and enterprises requiring high-speed multimodal text generation. Supported use cases include conversational AI and chatbots, text summarization, code generation and step-by-step reasoning, image and document understanding (OCR, chart comprehension, PDF parsing, screen and UI parsing), video content analysis, agentic workflows with native function calling, and multilingual NLP tasks across 35+ languages.

## Release Date:
**Build.NVIDIA.com:** 06/2026 via [link](https://build.nvidia.com/google/diffusiongemma-26b-a4b-it)  
**Huggingface:** 06/10/2026 via [link](https://huggingface.co/google/diffusiongemma-26B-A4B-it)

## Reference(s):
**References:**
- [Google AI Principles](https://ai.google/principles/)
- [Responsible Generative AI Toolkit](https://ai.google.dev/responsible)
- [Google AI Responsibility Update (February 2025)](https://ai.google/static/documents/ai-responsibility-update-published-february-2025.pdf)
- [DiffusionGemma 26B A4B IT on Hugging Face](https://huggingface.co/google/diffusiongemma-26B-A4B-it)

## Model Architecture:
**Architecture Type:** Transformer  
**Network Architecture:** Mixture-of-Experts  
**Total Parameters:** 25.2B  
**Active Parameters:** 3.8B  
**Vocabulary Size:** 262,144  
**Base Model:** Gemma 4 26B A4B

### Input:
**Input Types:** Text, Image, Video  
**Input Formats:** String, Red, Green, Blue (RGB), Video (MP4)
**Input Parameters:** One-Dimensional (1D), Two-Dimensional (2D), Three-Dimensional (3D)  
**Other Input Properties:** Images support variable aspect ratios and resolutions via a configurable visual token budget (70, 140, 280, 560, or 1120 tokens per image); place image content before text for optimal multimodal performance. Videos are processed as frame sequences up to 60 seconds at 1 frame per second.  
**Input Context Length (ISL):** 262,144

### Output:
**Output Types:** Text  
**Output Format:** String  
**Output Parameters:** One-Dimensional (1D)  
**Other Output Properties:** Text is generated in parallel 256-token canvas blocks via diffusion sampling with adaptive stopping; supports native function calling and structured JSON output formatting.

__Our AI models are designed and/or optimized to run on NVIDIA GPU-accelerated systems. By leveraging NVIDIA's hardware (e.g. GPU cores) and software frameworks (e.g., CUDA libraries), the model achieves faster training and inference times compared to CPU-only solutions.__

## Software Integration:
**Runtime Engines:**
- **Hugging Face Transformers**
- **vLLM**
- **Unsloth**

**Supported Hardware:**
- **NVIDIA Ampere:** A100 (80GB)
- **NVIDIA Blackwell:** B200, B100, GB200, GeForce RTX 5090
- **NVIDIA Hopper:** H100, H200

**Operating Systems:** Linux

__The integration of foundation and fine-tuned models into AI systems requires additional testing using use-case-specific data to ensure safe and effective deployment. Following the V-model methodology, iterative testing and validation at both unit and system levels are essential to mitigate risks, meet technical and functional requirements, and ensure compliance with safety and ethical standards before deployment.__

## Model Version(s)
DiffusionGemma 26B A4B IT v1.0 (June 2026)

## Training, Testing, and Evaluation Datasets:

### Training Dataset
**Data Modality:** Text, Image  
**Text Training Data Size:** Undisclosed  
**Image Training Data Size:** Undisclosed  
**Training Data Collection:** Hybrid: Automated, Human  
**Training Labeling:** Hybrid: Automated, Human  
**Training Properties:** Large-scale, diverse pre-training corpus spanning web documents, code, mathematics, and images across 140+ languages with a data collection cutoff of January 2025. Preprocessing includes CSAM filtering, sensitive personal information removal, and content quality filtering aligned with Google's AI policies.

### Testing Dataset
**Testing Data Collection:** Undisclosed  
**Testing Labeling:** Undisclosed  
**Testing Properties:** Undisclosed

### Evaluation Dataset
**Evaluation Benchmark Score:** DiffusionGemma 26B A4B IT achieves strong performance across text reasoning, code, vision, and long-context benchmarks, including 77.6% on MMLU Pro, 73.2% on GPQA Diamond, and 70.5% on MATH-Vision. All results are for instruction-tuned model variants evaluated with the recommended Entropy Bound (EB) sampler.

<details>
<summary><strong>Detailed Benchmark Comparison Table</strong></summary>

| Benchmark                                             | DiffusionGemma 26B A4B | Gemma 4 26B A4B |
|:------------------------------------------------------|:----------------------:|:---------------:|
| **Text & Reasoning**                                  |                        |                 |
| MMLU Pro                                              |         77.6%          |      82.6%      |
| AIME 2026 (no tools)                                  |         69.1%          |      88.3%      |
| LiveCodeBench v6                                      |         69.1%          |      77.1%      |
| Codeforces ELO                                        |          1429          |      1718       |
| GPQA Diamond                                          |         73.2%          |      82.3%      |
| Tau2 (average over 3)                                 |         56.2%          |      68.2%      |
| HLE (no tools)                                        |         11.0%          |      8.7%       |
| HLE (with search)                                     |         11.9%          |      17.2%      |
| BigBench Extra Hard                                   |         47.6%          |      64.8%      |
| MMMLU                                                 |         81.5%          |      86.3%      |
| **Vision**                                            |                        |                 |
| MMMU Pro                                              |         54.3%          |      73.8%      |
| OmniDocBench 1.5 (avg edit distance, lower is better) |         0.319          |      0.149      |
| MATH-Vision                                           |         70.5%          |      82.4%      |
| MedXPertQA MM                                         |         49.0%          |      58.1%      |
| **Long Context**                                      |                        |                 |
| MRCR v2 8 needle 128k (average)                       |         32.0%          |      44.1%      |

*Evaluations conducted on instruction-tuned variants using the recommended Entropy-Bounded Denoising with Adaptive Stopping (EB) sampler.*

</details>

**Evaluation Data Collection:** Automated  
**Evaluation Labeling:** Automated  
**Evaluation Properties:** Standard benchmark evaluation across 15 tasks covering text reasoning, code generation, multilingual understanding, vision, and long-context retrieval. All evaluations were performed on instruction-tuned model variants using the Entropy-Bounded Denoising with Adaptive Stopping (EB) sampler (max 48 denoising steps, temperature linear decay 0.8 → 0.4, entropy bound 0.1, adaptive stopping entropy threshold 0.005). All testing was intentionally conducted without safety filters to evaluate the model's raw capabilities and baseline behaviors.

## Inference
**Acceleration Engine:** vLLM  
**Test Hardware:** H100

## Additional Details

### Diffusion Sampling Configuration
DiffusionGemma 26B A4B IT generates text via block-autoregressive discrete diffusion. An autoregressive encoder processes the input prompt and caches it via KV cache; a decoder then applies bidirectional attention over a 256-token generation canvas, iteratively denoising the full block in parallel. Recommended sampling settings:
- **Sampler:** Entropy-Bounded Denoising with Adaptive Stopping (EB)
- **Maximum denoising steps:** 48
- **Temperature schedule:** Linear decay 0.8 → 0.4
- **Entropy bound:** 0.1 (token selection threshold)
- **Adaptive stopping:** Halts when average canvas entropy < 0.005 and highest-probability token predictions are stable across two consecutive denoising steps

Simpler tasks (e.g., structured code output) require fewer denoising steps, enabling dynamic throughput scaling by task complexity.

### Thinking Mode
Enable step-by-step reasoning by including `<|think|>` at the start of the system prompt. Reasoning output is wrapped in `<|channel>thought\n[reasoning]<channel|>` before the final answer. If thinking is disabled, empty thought tags are still emitted. In multi-turn conversations, do not include prior thinking content in conversation history — include only the final response.

### Known Limitations
- Performance may reflect socio-cultural biases present in training data.
- The model may generate factually incorrect or outdated information; it is not a knowledge base.
- Complex, highly open-ended, or nuanced tasks (sarcasm, figurative language) may yield degraded outputs.
- Common-sense reasoning may be limited in certain situations due to reliance on statistical language patterns.

## Ethical Considerations
NVIDIA believes Trustworthy AI is a shared responsibility and we have established policies and practices to enable development for a wide array of AI applications. Developers should work with their internal model team to ensure this model meets requirements for the relevant industry and use case and addresses unforeseen product misuse.

Please make sure you have proper rights and permissions for all input image and video content; if image or video includes people, personal health information, or intellectual property, the image or video generated will not blur or maintain proportions of image subjects included.

Please report model quality, risk, security vulnerabilities or NVIDIA AI Concerns [here](https://www.nvidia.com/en-us/support/submit-security-vulnerability/)

## Specifications

- **Context Length:** 262,144 tokens
- **Parameters:** 25,823,778,864
- **Input:** Text, Image, Video
- **Output:** Text

## Capabilities

- **Function Calling:** Supported
- **Structured Output:** Not supported
- **Reasoning:** Supported

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
top_p=,
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