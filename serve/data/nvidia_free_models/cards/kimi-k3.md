---
title: "kimi-k3"
publisher: "moonshotai"
type: "endpoint"
updated: "2026-08-27T20:40:37.796Z"
description: "~2.8T hybrid KDA+MLA multimodal MoE for long-horizon coding, agentic tool use, and image understanding."
canonical: "https://build.nvidia.com/moonshotai/kimi-k3"
---

# Kimi-K3

## Description
Kimi-K3 is an open-weight, native multimodal agentic model developed by Moonshot AI for long-horizon coding, knowledge work, visual understanding, and reasoning. It is a 2.8T-parameter Mixture-of-Experts model built with Kimi Delta Attention, Attention Residuals, and Stable LatentMoE, with 104B activated parameters and a 1M-token context window.

*This model is ready for commercial or non-commercial use.*

## Third-Party Community Consideration:
This model is not owned or developed by NVIDIA. This model has been developed and built to a third-party's requirements for this application and use case; see link to Non-NVIDIA [Kimi-K3 Model Card](https://huggingface.co/moonshotai/Kimi-K3).

## License and Terms of Use:
**GOVERNING TERMS:** This trial service is governed by the [NVIDIA API Trial Terms of Service](https://assets.ngc.nvidia.com/products/api-catalog/legal/NVIDIA%20API%20Trial%20Terms%20of%20Service.pdf). Use of this model is governed by the [NVIDIA Open Model Agreement](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-agreement/). Additional Information: [Modified MIT License](https://huggingface.co/moonshotai/Kimi-K3/blob/main/LICENSE). Kimi K3.

## Deployment Geography:
Global

## Use Case:
**Use Case:** Developers and researchers can use Kimi-K3 for long-horizon software engineering, agentic knowledge work, multimodal document understanding, reasoning, tool use, visual content analysis, and interactive application development.

## Release Date:
**Build.NVIDIA.com:** 08/20/2026 via [link](https://build.nvidia.com/moonshotai/kimi-k3)  
**Huggingface:** 07/16/2026 via [link](https://huggingface.co/moonshotai/Kimi-K3)

## Reference(s):
**References:**  
- [Kimi-K3 on Hugging Face](https://huggingface.co/moonshotai/Kimi-K3)
- [Kimi-K3 Technical Blog](https://www.kimi.com/blog/kimi-k3)
- [Kimi-K3 Technical Report](https://github.com/MoonshotAI/Kimi-K3/blob/main/k3_tech_report.pdf)
- [Kimi-K3 Quickstart](https://platform.kimi.ai/docs/guide/kimi-k3-quickstart)
- [Thinking Effort Guide](https://platform.kimi.ai/docs/guide/use-thinking-effort)

## Model Architecture:
**Architecture Type:** Transformer  
**Network Architecture:** Mixture-of-Experts  
**Total Parameters:** 2.8T  
**Active Parameters:** 104B  
**Vocabulary Size:** 160K  
**Input Context Length (ISL):** 1,048,576 tokens  
**Base Model:** Kimi-K3

### Input:
**Input Types:** Text, Image  
**Input Formats:** String, Red, Green, Blue (RGB)  
**Input Parameters:** One-Dimensional (1D), Two-Dimensional (2D)  
**Other Input Properties:** Supports multimodal conversations, system prompts, tool definitions, and preserved reasoning history. For multi-turn conversations and tool calls, clients must pass back the complete assistant message, including `reasoning_content` and `tool_calls`.

### Output:
**Output Types:** Text  
**Output Format:** String  
**Output Parameters:** One-Dimensional (1D)  
**Other Output Properties:** Supports reasoning content, structured output, function and tool calls, and configurable low, high, or max reasoning effort. Thinking is always enabled.

__Our AI models are designed and/or optimized to run on NVIDIA GPU-accelerated systems. By leveraging NVIDIA's hardware (e.g. GPU cores) and software frameworks (e.g., CUDA libraries), the model achieves faster training and inference times compared to CPU-only solutions.__

## Software Integration:
**Runtime Engines:**  
- **vLLM:** Supported; see the [Kimi-K3 vLLM recipes](https://recipes.vllm.ai/moonshotai/Kimi-K3)
- **SGLang:** Supported; see the [Kimi-K3 SGLang cookbook](https://docs.sglang.io/cookbook/autoregressive/Moonshotai/Kimi-K3)
- **TokenSpeed:** Supported; see the [TokenSpeed recipes](https://lightseek.org/tokenspeed/recipes/models#kimi-k3)

**Supported Hardware:** NVIDIA Blackwell

**Operating Systems:** Linux

__The integration of foundation and fine-tuned models into AI systems requires additional testing using use-case-specific data to ensure safe and effective deployment. Following the V-model methodology, iterative testing and validation at both unit and system levels are essential to mitigate risks, meet technical and functional requirements, and ensure compliance with safety and ethical standards before deployment.__

## Model Version(s)
Kimi-K3

## Training, Testing, and Evaluation Datasets:

### Training Dataset
**Data Modality:** Text, Image  
**Image Training Data Size:** Undisclosed  
**Text Training Data Size:** Undisclosed  
**Training Data Collection:** Undisclosed  
**Training Labeling:** Undisclosed  
**Training Properties:** Kimi-K3 uses quantization-aware training from the supervised fine-tuning stage onward with MXFP4 weights and MXFP8 activations. Specific pretraining datasets, collection methods, and labeling methods are not disclosed in the source Model Card.

### Testing Dataset
**Testing Data Collection:** Undisclosed  
**Testing Labeling:** Undisclosed  
**Testing Properties:** Undisclosed

### Evaluation Dataset
**Evaluation Benchmark Score:** Kimi-K3 was evaluated across reasoning and knowledge, coding, agentic, and multimodal benchmarks. Selected partner-reported results are shown below.

<details>
<summary><strong>Selected Benchmark Results</strong></summary>

| Category | Benchmark | Kimi-K3 Result |
|---|---|---:|
| Reasoning and Knowledge | GPQA Diamond | 93.5 |
| Reasoning and Knowledge | AA-LCR | 74.7 |
| Coding | DeepSWE | 67.5 |
| Coding | ProgramBench | 77.8 |
| Coding | Terminal-Bench 2.1 | 88.3 |
| Coding | FrontierSWE | 81.2 |
| Multimodal | MMVU | 82.1 |
| Multimodal | BabyVision with Python | 85.7 |
| Multimodal | MMMU-Pro, without/with tools | 81.6 / 83.4 |
| Multimodal | MathVision, without/with tools | 94.3 / 97.8 |

</details>

**Evaluation Data Collection:** Hybrid: Automated, Manually-Collected  
**Evaluation Labeling:** Hybrid: Automated, Manually-Labeled  
**Evaluation Properties:** Partner-reported Kimi-K3 results use max reasoning effort and temperature 1.0. Single-step tasks use top-p 0.95, while agentic tasks use top-p 1.0. Tool-augmented benchmark cells report scores without and with tool augmentation in that order. Coding benchmarks use benchmark-specific Kimi Code, Claude Code, Codex, or official harnesses; multimodal results other than ZeroBench are averaged over three runs.

## Inference
**Acceleration Engine(s):** vLLM; Dynamo  
**Test Hardware:** NVIDIA Grace Blackwell GB300x8  
**Precision Formats:** MXFP4 weights with MXFP8 activations

## Additional Details

### Key Architecture Features
- **Kimi Delta Attention and Attention Residuals:** The model combines 69 KDA layers with 24 gated multi-head latent-attention layers.
- **Stable LatentMoE:** The model contains 896 experts and selects 16 experts per token, with two shared experts.
- **Native multimodality:** A 401M-parameter MoonViT-V2 vision encoder supports text and image understanding.
- **Long context:** The model supports a context length of 1,048,576 tokens.

### Usage Considerations
Kimi-K3 was trained with preserved thinking history. Applications using multi-turn conversations or tool calls must return the complete prior assistant message to the model, including reasoning content and tool calls. Refer to the [Kimi-K3 Quickstart](https://platform.kimi.ai/docs/guide/kimi-k3-quickstart) for current API guidance.

## Ethical Considerations
NVIDIA believes Trustworthy AI is a shared responsibility and we have established policies and practices to enable development for a wide array of AI applications. When downloaded or used in accordance with our terms of service, developers should work with their internal model team to ensure this model meets requirements for the relevant industry and use case and addresses unforeseen product misuse.

Users are responsible for model inputs and outputs. Users are responsible for ensuring safe integration of this model, including implementing guardrails as well as other safety mechanisms, prior to deployment.

Please make sure you have proper rights and permissions for all input image content; if the image includes people, personal health information, or intellectual property, the image generated will not blur or maintain proportions of image subjects included.

Please report model quality, risk, security vulnerabilities or NVIDIA AI Concerns [here](https://www.nvidia.com/en-us/support/submit-security-vulnerability/)

## Specifications

- **Context Length:** 1,048,576 tokens
- **Parameters:** 2.8T
- **Input:** Text, Image
- **Output:** Text

## Capabilities

- **Function Calling:** Supported
- **Structured Output:** Supported
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