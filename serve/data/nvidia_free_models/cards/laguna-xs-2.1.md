---
title: "laguna-xs-2.1"
publisher: "poolside"
type: "endpoint"
updated: "2026-07-15T23:10:20.283Z"
description: "Efficient 33B MoE for local, long-horizon agentic coding and terminal tasks"
canonical: "https://build.nvidia.com/poolside/laguna-xs-2.1"
---

# Laguna XS 2.1

## Description
Laguna XS 2.1 is a Poolside 33B total parameter Mixture-of-Experts text generation model with 3B activated parameters per token, designed for agentic coding and long-horizon software engineering work on local machines.

*This model is ready for commercial or non-commercial use.*

## Third-Party Community Consideration:
This model is not owned or developed by NVIDIA. This model has been developed and built to a third-party's requirements for this application and use case; see link to Non-NVIDIA [Laguna XS 2.1 Model Card](https://huggingface.co/poolside/Laguna-XS-2.1)

## License and Terms of Use:
**GOVERNING TERMS:** The trial service is governed by the [NVIDIA API Trial Terms of Service](https://assets.ngc.nvidia.com/products/api-catalog/legal/NVIDIA%20API%20Trial%20Terms%20of%20Service.pdf). Use of the model is governed by the [OpenMDW License Agreement, version 1.1](https://openmdw.ai/license/1-1/).

## Deployment Geography:
Global

## Use Case:
**Use Case:** Laguna XS 2.1 is intended for software engineering, agentic coding, terminal-style tasks, tool-use workflows, long-horizon coding work, and local text generation.

## Release Date:
**Build.NVIDIA.com:** 07/15/2026 via [link](https://build.nvidia.com/poolside/laguna-xs-2.1)  
**Huggingface:** 07/02/2026 via [link](https://huggingface.co/poolside/Laguna-XS-2.1)

## Reference(s):
**References:** 
- [Laguna XS 2.1 Model Page](https://huggingface.co/poolside/Laguna-XS-2.1)

## Model Architecture:
**Architecture Type:** Transformer  
**Network Architecture:** Mixture-of-Experts  
**Total Parameters:** 33B  
**Active Parameters:** 3B  
**Vocabulary Size:** 100,352

### Input:
**Input Types:** Text  
**Input Formats:** String  
**Input Parameters:** One-Dimensional (1D)  
**Other Input Properties:** Laguna XS 2.1 uses a chat template that supports optional thinking, tool calls, and preserved reasoning content.  
**Input Context Length (ISL):** 262,144

### Output:
**Output Types:** Text  
**Output Format:** String  
**Output Parameters:** One-Dimensional (1D)  
**Other Output Properties:** The model can generate text with interleaved reasoning and tool-call content when supported by the serving stack.

__Our AI models are designed and/or optimized to run on NVIDIA GPU-accelerated systems. By leveraging NVIDIA's hardware (e.g. GPU cores) and software frameworks (e.g., CUDA libraries), the model achieves faster training and inference times compared to CPU-only solutions.__

## Software Integration:
**Runtime Engines:**
- **llama.cpp**
- **Ollama**
- **SGLang**
- **TensorRT-LLM**
- **Transformers**
- **vLLM**

**Supported Hardware:**
- **NVIDIA Blackwell:** GB300, GB200, B300, B200, RTX 6000 PRO
- **NVIDIA Hopper:** H100, H200

**Preferred Operating Systems:** Linux

__The integration of foundation and fine-tuned models into AI systems requires additional testing using use-case-specific data to ensure safe and effective deployment. Following the V-model methodology, iterative testing and validation at both unit and system levels are essential to mitigate risks, meet technical and functional requirements, and ensure compliance with safety and ethical standards before deployment.__

## Model Version(s)
Laguna XS 2.1 v2.1

## Training, Testing, and Evaluation Datasets:

### Training Dataset
**Data Modality:** Text  
**Text Training Data Size:** Undisclosed  
**Training Data Collection:** Automated  
**Training Labeling:** Automated  
**Training Properties:** Laguna XS 2.1 was developed through pre-training, post-training, and reinforcement learning stages. Specific training datasets are Undisclosed.

### Testing Dataset
**Testing Data Collection:** Undisclosed  
**Testing Labeling:** Undisclosed  
**Testing Properties:** Undisclosed

### Evaluation Dataset
**Evaluation Benchmark Score:** Laguna XS 2.1 reports 70.9% on SWE-bench Verified, 63.1% on SWE-bench Multilingual, 47.6% on SWE-Bench Pro, and 37.5% on Terminal-Bench 2.0.

<details>
<summary><strong>Detailed Benchmark Comparison Table</strong></summary>

| Model | Size (total params.) | SWE-bench Verified | SWE-bench Multilingual | SWE-Bench Pro (Public Dataset) | Terminal-Bench 2.0 |
|---|---:|---:|---:|---:|---:|
| Laguna XS 2.1 | 33B | 70.9% | 63.1% | 47.6% | 37.5% |
| Laguna XS.2 | 33B | 69.9% | 57.7% | 46.3% | 35.7% |
| Qwen3.6-35B-A3B | 35B | 73.4% | 67.2% | 49.5% | 51.5% |
| North Mini Code | 30B | 67.6% | - | 40.2% | 36.0% |
| MAI-Code-1-Flash | 137B | 71.6% | 65.5% | 51.2% | 54.8% |
| gpt-oss-120B | 120B | - | - | 16.2% | 18.7% |
| Claude Haiku 4.5 | - | 73.3% | - | 39.5% | 29.8% |
| GPT-5.4 Nano | - | - | - | 52.4% | 46.3% |

</details>

**Evaluation Data Collection:** Hybrid: Automated, Manually-Collected  
**Evaluation Labeling:** Hybrid: Automated, Manually-Labeled  
**Evaluation Properties:** Evaluation benchmarks include SWE-bench Verified, SWE-bench Multilingual, SWE-Bench Pro, and Terminal-Bench 2.0. Evaluation Methodology Notes:
- All Laguna XS 2.1 benchmarking used Laude Institute's Harbor Framework with Poolside's agent harness, a maximum of 500 steps, sandboxed execution, temperature=1.0, top_k=20, top_p=1, thinking mode enabled, and a 256K-token context length.
- SWE-bench Verified and SWE-bench Multilingual report mean pass@1 averaged over 4 attempts per task.
- SWE-Bench Pro reports mean pass@1 averaged over 2 attempts per task.
- Terminal-Bench 2.0 reports mean pass@1 averaged over 5 attempts per task using 48 GB RAM and 32 CPUs; other tasks used 8 GB RAM and 2 CPUs.
- Base task images and verifiers were patched for infrastructure reliability issues, and a reward-hack judge review did not find significant reward hacking after joint judge review and manual review.

## Inference
**Acceleration Engine:** vLLM  
**Test Hardware:** NVIDIA Hopper (H100)

## Ethical Considerations
NVIDIA believes Trustworthy AI is a shared responsibility and we have established policies and practices to enable development for a wide array of AI applications. Developers should work with their internal model team to ensure this model meets requirements for the relevant industry and use case and addresses unforeseen product misuse.

Please report model quality, risk, security vulnerabilities or NVIDIA AI Concerns [here](https://www.nvidia.com/en-us/support/submit-security-vulnerability/).

## Specifications

- **Context Length:** 262,144 tokens
- **Parameters:** 33,000,000,000
- **Input:** Text
- **Output:** Text

## Capabilities

- **Function Calling:** Supported
- **Structured Output:** Not supported
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