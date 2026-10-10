---
title: "gpt-oss-20b"
publisher: "openai"
type: "endpoint"
updated: "2025-08-05T16:46:10.339Z"
description: "Smaller Mixture of Experts (MoE) text-only LLM for efficient AI reasoning and math"
canonical: "https://build.nvidia.com/openai/gpt-oss-20b"
---

# GPT OSS 20B Overview

## Description: <br>
OpenAI releases the gpt-oss family of open-weight models designed for powerful reasoning, agentic tasks, and versatile developer use cases. The family consists of the:
- `gpt-oss-120b` — for production, general purpose, high reasoning use-cases that fits into a single H100 GPU (117B parameters with 5.1B active parameters)
- `gpt-oss-20b` — for lower latency, and local or specialized use-cases (21B parameters with 3.6B active parameters).

The `gpt-oss-20b` is designed as a Mixture-of-Experts (MoE) model, structurally identical to the larger 117B variant, albeit with different hyperparameters. This model leverages SwiGLU activations and incorporates learned attention sinks within its architecture. Functionally, it serves as a robust reasoning model, supporting advanced capabilities such as chain-of-thought processing, adjustable reasoning effort levels, instruction following, and tool use. It operates strictly with text-only modalities for both input and output. A key strategic benefit is its suitability for enterprises and governments, facilitating on-premises or private cloud deployment to ensure enhanced data security and privacy.

Model Highlights:  
- **Permissive Apache 2.0 license:** Build freely without copyleft restrictions or patent risk—ideal for experimentation, customization, and commercial deployment.
- **Configurable reasoning effort:** Easily adjust the reasoning effort (low, medium, high) based on your specific use case and latency needs.
- **Full chain-of-thought:** Gain complete access to the model's reasoning process, facilitating easier debugging and increased trust in outputs. It's not intended to be shown to end users.
- **Fine-tunable:** Fully customize models to your specific use case through parameter fine-tuning.
- **Agentic capabilities:** Use the models' native capabilities for function calling, web browsing, python code execution, and structured outputs.

This model is ready for commercial/non-commercial use.

## Third-Party Community Consideration <br>
This model is not owned or developed by NVIDIA. This model has been developed and built to a third-party’s requirements for this application and use case; see link to Non-NVIDIA [gpt-oss-20b model card](https://huggingface.co/openai/gpt-oss-20b).

### License and Terms of Use: <br> 
GOVERNING TERMS: This trial service is governed by the [NVIDIA API Trial Terms of Service](https://assets.ngc.nvidia.com/products/api-catalog/legal/NVIDIA%20API%20Trial%20Terms%20of%20Service.pdf). Use of this model is governed by the [NVIDIA Community Model License](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-community-models-license/). Additional Information: [Apache License Version 2.0](https://www.apache.org/licenses/LICENSE-2.0).

### Deployment Geography:
Global

### Use Case: <br>
Intended for use as a reasoning model, offering features like chain-of-thought and adjustable reasoning effort levels. It provides comprehensive support for instruction following and tool use, fostering transparency, customization, and deployment flexibility for developers, researchers, and startups. Crucially, it enables enterprises and governments to deploy on-premises or in private clouds, ensuring stringent data security and privacy requirements are met.

### Release Date:  <br>
Build.NVIDIA.com - 08/05/2025 via [link](https://build.nvidia.com/openai/gpt-oss-20b) <br> 
Hugging Face - 08/05/2025 via [link](https://huggingface.co/openai/gpt-oss-20b) <br>

## Reference(s):
- [OpenAI Cookbook](https://cookbook.openai.com/)
- [Optimizing OpenAI GPT-OSS Models with NVIDIA TensorRT-LLM](https://github.com/openai/openai-cookbook/blob/main/articles/run-nvidia.ipynb)
- [Running a High Performance GPT-OSS-120B Inference Server with TensorRT-LLM](https://github.com/NVIDIA/TensorRT-LLM/blob/main/docs/source/blogs/tech_blog/blog9_Deploying_GPT_OSS_on_TRTLLM.md)

## Model Architecture: <br> 
**Architecture Type:** Transformer <br>
**Network Architecture:** Mixture-of-Experts (MoE) <br>
**Total Parameters:** 20B <br>
**Active Parameters:** 4B <br>
**Vocabulary Size:** 201,088 (Utilizes the standard tokenizer used by GPT-4o) <br>

## Input: <br>
**Input Type(s):** Text <br>
**Input Format(s):** String <br>
**Input Parameters:** One Dimensional (1D) <br>
**Other Properties Related to Input:** Uses RoPE with a 128k context length, with attention layers alternating between full context and a sliding 128-token window. Includes a learned attention sink per-head. Employs SwiGLU activations in the MoE layers, and the router performs a Top-K operation (K=4) followed by a Sigmoid function. GEMMs in the MoE include a per-expert bias. Utilizes tiktoken for tokenization. Input Context Length (ISL): 128000 <br>

## Output: <br>
**Output Type(s):** Text <br>
**Output Format:** String <br>
**Output Parameters:** One Dimensional (1D) <br>
**Other Properties Related to Output:** The model is architected to be compatible with the OpenAI Responses API and supports Structured Output, aligning with key partner expectations for advanced response formatting. <br> 

Our AI models are designed and/or optimized to run on NVIDIA GPU-accelerated systems [or name equivalent hardware preference]. By leveraging NVIDIA’s hardware (e.g. GPU cores) and software frameworks (e.g., CUDA libraries), the model achieves faster training and inference times compared to CPU-only solutions. <br>   

## Software Integration: <br>
**Runtime Engine(s):** <br>
* NeMo Framework (based on 25.07)<br>

**Supported Hardware Microarchitecture Compatibility:** <br>
* NVIDIA Blackwell: B200, GB200 <br>
* NVIDIA Hopper: H200

**Operating System(s):** Linux 

## Model Version(s): 
`gpt-oss-20b` v1.0 (August 5, 2025)

## Training, Testing, and Evaluation Datasets: <br>   
### Training Dataset:

* **Training Data Collection:** Undisclosed <br>
* **Training Labeling:** Undisclosed <br>
* **Training Properties:** The gpt-oss-20b model has approximately 20 billion total parameters, with approximately 4 billion active parameters per inference. The weights for all layers are in BF16, except for the MoE projection weights, which are in MXFP4. The reference implementation, for initial accuracy validation, currently upcasts all weights to BF16. Activations are expected to be in BF16 or FP8.

### Testing Dataset:
* **Testing Data Collection:** Undisclosed <br>
* **Testing Labeling:** Undisclosed <br>
* **Testing Properties:** The model's performance is tested against recognized benchmarks such as MMLU (Massive Multitask Language Understanding) and GPQA (General Purpose Question Answering), alongside other benchmarks including LiveCodeBench, AIME 2024, and MATH-500 

### Evaluation Dataset:

* **Evaluation Data Collection:** Undisclosed <br>
* **Evaluation Labeling:** Undisclosed <br>
* **Evaluation Benchmark Score:** 

| Benchmark  | gpt-oss-120b | gpt-oss-20b |
|----------|-----------| -----------|
| AIME 2024 (no tools) | 95.8   | 92.1 |
| AIME 2024 (with tools) | 96.6 | 96.0 |
| AIME 2025 (no tools) | 92.5  | 91.7 |
| AIME 2025 (with tools) | 97.9 | 98.7 |
| GPQA Diamond (no tools) | 80.1 | 71.5 |
| GPQA Diamond (with tools) | 80.9 | 74.2 |
| HLE (no tools) | 14.9 | 10.9 |
| HLE (with tools) | 19.0 | 17.3 |
| MMLU | 90.0 | 85.3 |
| SWE-Bench Verified | 62.4 | 60.7 |
| Tau-Bench Retail | 67.8 | 54.4 |
| Tau-Bench Airline | 49.2 | 38.0 |
| Aider Polyglot | 44.4 | 34.2 |
| MMMLU (Average) | 81.3 | 75.6 |
| HealthBench | 57.6 | 42.5 |
| HealthBench Hard | 30.0 | 10.8 |
| HealthBench Consensus | 89.9 | 82.6 |
| Codeforces (no tools) [elo] | 2463 | 2230 |
| Codeforces (with tools) [elo] | 2622 | 2516 |

Above scores were measured for the high reasoning level.

### Safety Results:

The following evaluations check that the model does not comply with requests for content that is
disallowed under OpenAI’s safety policies, including hateful content or illicit advice.

| Category  | gpt-oss-120b | gpt-oss-20b |
|----------|-----------| -----------|
| hate (aggregate) | 0.996   | 0.996 |
| self-harm/intent and selfharm/instructions | 0.995 | 0.984 |
| personal data/semi restrictive | 0.967  | 0.947 |
| sexual/exploitative | 1.000 | 0.980 |
| sexual/minors | 1.000 | 0.971 |
| illicit/non-violent | 1.000 | 0.983 |
| illicit/violent | 1.000 | 1.000 |
| personal data/restricted | 0.996 | 0.978 |

## Inference:
**Acceleration Engine:** vLLM <br>
**Test Hardware:** NVIDIA Hopper (H200) <br>

## Additional Details
The model is released with the native quantization support. Specifically, [MXFP4](https://www.opencompute.org/documents/ocp-microscaling-formats-mx-v1-0-spec-final-pdf) is used for the linear projection weights in the MoE layer. It is stored the MoE tensor in two parts:

- `tensor.blocks` stores the actual fp4 values. Every two values are packed in one `uint8` value.
- `tensor.scales` stores the block scale. The block scaling is done among the last dimension for all MXFP4 tensors.

All other tensors are stored in BF16. It is recommended to use BF16 as the activation precision for the model.

## Ethical Considerations:
NVIDIA believes Trustworthy AI is a shared responsibility and we have established policies and practices to enable development for a wide array of AI applications.  When downloaded or used in accordance with our terms of service, developers should work with their internal model team to ensure this model meets requirements for the relevant industry and use case and addresses unforeseen product misuse.  

Please report security vulnerabilities or NVIDIA AI Concerns [here](https://www.nvidia.com/en-us/support/submit-security-vulnerability/).

## Specifications

- **Context Length:** 131,072 tokens
- **Parameters:** 21,000,000,000
- **Input:** Text
- **Output:** Text

## Capabilities

- **Function Calling:** Supported
- **Structured Output:** Supported
- **Reasoning:** Supported

## Prototype

```python
from openai import OpenAI

client = OpenAI(
base_url = "https://integrate.api.nvidia.com/v1",
api_key = "$NVIDIA_API_KEY"
)

completion = client.chat.completions.create(
model="",
messages=[{"role":"user","content":""}],
temperature=,
top_p=,
max_tokens=,
stream=NaN
)

reasoning = getattr(completion.choices[0].message, "reasoning_content", None)
if reasoning:
print(reasoning)
print(completion.choices[0].message.content)
```

```python
from langchain_nvidia_ai_endpoints import ChatNVIDIA

client = ChatNVIDIA(
model="",
api_key="$NVIDIA_API_KEY", 
temperature=,
top_p=,
max_tokens=,
)

response = client.invoke([{"role":"user","content":""}])
if response.additional_kwargs and "reasoning_content" in response.additional_kwargs:
print(response.additional_kwargs["reasoning_content"])
print(response.content)
```

```javascript
import OpenAI from 'openai';

const openai = new OpenAI({
apiKey: '$NVIDIA_API_KEY',
baseURL: 'https://integrate.api.nvidia.com/v1',
})

async function main() {
const completion = await openai.chat.completions.create({
model: "",
messages: [{"role":"user","content":""}],
temperature: ,
top_p: ,
max_tokens: ,
stream: 
})

const reasoning = completion.choices[0]?.message?.reasoning_content;
if (reasoning) process.stdout.write(reasoning + "\n");
process.stdout.write(completion.choices[0]?.message?.content);

}

main();
```

```bash
invoke_url='https://integrate.api.nvidia.com/v1/chat/completions'

authorization_header='Authorization: Bearer '
accept_header='Accept: application/json'
content_type_header='Content-Type: application/json'

data=$'{
"messages": [
{
"role": "user",
"content": ""
}
]
}'

response=$(curl --silent -i -w "\n%{http_code}" --request POST \
--url "$invoke_url" \
--header "$authorization_header" \
--header "$accept_header" \
--header "$content_type_header" \
--data "$data"
)

echo "$response"
```