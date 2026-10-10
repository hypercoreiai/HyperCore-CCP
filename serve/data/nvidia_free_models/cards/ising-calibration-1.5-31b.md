---
title: "ising-calibration-1.5-31b"
publisher: "nvidia"
type: "endpoint"
updated: "2026-07-23T15:28:05.216Z"
description: "NVIDIA-Ising-Calibration-1.5 is a dense multimodal vision-language model built on Gemma 4 31B. It analyzes quantum computing calibration experiment plots and generates structured technical text."
canonical: "https://build.nvidia.com/nvidia/ising-calibration-1.5-31b"
---

# NVIDIA-Ising-Calibration-1.5-31B-BF16 Overview

## Description:  
NVIDIA-Ising-Calibration-1.5-31B-BF16 is a dense multimodal vision-language model built on Gemma 4 31B. It analyzes quantum computing calibration experiment plots and generates structured technical text across six analysis categories: technical description, experimental conclusion, experimental significance, fit quality assessment, parameter extraction, and experiment success classification.  
NVIDIA-Ising-Calibration-1.5-31B-BF16 was developed by NVIDIA for quantum calibration plot understanding. 

_This model is ready for commercial use._

### License/Terms of Use:
**GOVERNING TERMS:** Use of this trial service is governed by the [NVIDIA API Trial Terms of Service](https://assets.ngc.nvidia.com/products/api-catalog/legal/NVIDIA%20API%20Trial%20Terms%20of%20Service.pdf). Use of this model is governed by the [OpenMDW License Agreement, version 1.1](https://github.com/OpenMDW/OpenMDW/blob/main/1.1/LICENSE.OpenMDW-1.1). ADDITIONAL INFORMATION: [Apache License, Version 2.0](https://www.apache.org/licenses/LICENSE-2.0).

### Deployment Geography:  
Global

### Use Case:  
Quantum computing researchers, calibration engineers, and developers can use this model to analyze experiment plot images and generate technical descriptions, experimental conclusions, significance assessments, fit quality evaluations, parameter extractions, and experiment success classifications. The model assists automated or assisted calibration workflows, and outputs should be validated by domain experts before acting on experimental conclusions.  

### Release Date:
**Preview API:** 07/20/2026 via [link](https://build.nvidia.com/nvidia/ising-calibration-1.5-31b)   
**NVIDIA NGC:** 07/20/2026 via [link](https://catalog.ngc.nvidia.com/orgs/nim/teams/nvidia/models/nvidia-ising-calibration-1-5-31b)

## Reference(s):
[Gemma](https://ai.google.dev/gemma)  
[QCalEval Benchmark](https://huggingface.co/datasets/nvidia/QCalEval)  
[QCalEval: Benchmarking Vision-Language Models for Quantum Calibration Plot Understanding](https://arxiv.org/abs/2604.25884)  

## Model Architecture:   
**Architecture Type:** Dense multimodal vision-language model   
**Network Architecture:** Integrated vision processing for experiment plot images combined with a Gemma 4 31B dense language model for autoregressive text generation.  
**This model was developed based on google/gemma-4-31b.**  
**Number of model parameters:** Approximately 31B  

## Input:  
**Input Type(s):** Text, Image  
**Input Format(s):** String, Other: RGB (.png, .jpeg, .jpg)  
**Input Parameters:** One-Dimensional (1D), Two-Dimensional (2D)  
**Other Properties Related to Input:** Single-image or multi-image quantum calibration experiment plots with text prompts delivered through an OpenAI-compatible API. Suggested inference settings use temperature=0.2, zero-shot max_tokens=8192, and ICL max_tokens=32767.  

## Output:  
**Output Type(s):** Text  
**Output Format:** String  
**Output Parameters:** One-Dimensional (1D)  
**Other Properties Related to Output:** Natural language technical analysis, experimental conclusions, significance assessments, fit quality evaluations, parameter extractions, and experiment success classifications. Output length is controlled by max_tokens, and output is delivered through the hosted OpenAI-compatible Preview API with a vLLM backend.  

Our AI models are designed and/or optimized to run on NVIDIA GPU-accelerated systems. By leveraging NVIDIA's hardware (e.g. GPU cores) and software frameworks (e.g., CUDA libraries), the model achieves faster training and inference times compared to CPU-only solutions.

## Software Integration:
**Runtime Engine(s):** vLLM, BF16 serving precision    
**Supported Hardware Microarchitecture Compatibility:**
* NVIDIA Blackwell
* NVIDIA Hopper

**Supported Operating System(s):** Linux  

The integration of foundation and fine-tuned models into AI systems requires additional testing using use-case-specific data to ensure safe and effective deployment. Following the V-model methodology, iterative testing and validation at both unit and system levels are essential to mitigate risks, meet technical and functional requirements, and ensure compliance with safety and ethical standards before deployment.  

This AI model can be embedded as an Application Programming Interface (API) call into the software environment described above.

## Model Version(s): 
NVIDIA-Ising-Calibration-1.5-31B-BF16 v1.5.0  

## Training, Testing, and Evaluation Datasets:  

## Training Dataset:

**Data Modality:**
* Image  
* Text  

**Image Training Data Size:** Less than a Million Images  
**Text Training Data Size:** Less than a Billion Tokens  
**Data Collection Method by dataset:** Synthetic
**Labeling Method by dataset:** Synthetic  
**Properties (Quantity, Dataset Descriptions, Sensor(s)):** The training corpus contains 72.5K total supervised entries: 23.8K ICL-formatted entries for multi-image demonstrations and 48.7K zero-shot entries augmented using Qwen3.5-397B-A17B. The data comes from NVIDIA quantum-calibration/QCal-style synthetic data generation and focuses on calibration plot interpretation. The dataset was assembled for the 2026 Ising Calibration 1.5 release cycle.

### Testing Dataset:

**Data Collection Method by dataset:** Synthetic
**Labeling Method by dataset:** Synthetic
**Properties (Quantity, Dataset Descriptions, Sensor(s)):** QCalEval was used as the primary external release validation benchmark for Ising Calibration 1.5. It is a quantum-calibration evaluation suite with multimodal plot-plus-text tasks covering zero-shot and ICL/few-shot settings across calibration interpretation, parameter extraction, diagnostic reasoning, and calibration-status classification. The release candidate was evaluated on 243 zero-shot examples with 1,458 response slots and 236 ICL examples with 708 response slots; raw outputs were checked for completeness and server errors, then judged with both GPT and Gemini judges to produce aggregate scores. The benchmark uses curated quantum-calibration plot tasks rather than raw sensor telemetry, and should be interpreted as domain validation rather than a broad general-purpose capability benchmark.

### Evaluation Dataset:
**Benchmark Score:** QCalEval benchmark scores. Scores are the simple average of GPT-5.4 and Gemini-3.1-Pro judges.  

Zero-shot scores:  

| Model | Mean | Q1 | Q2 | Q3 | Q4 | Q5 | Q6 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| NVIDIA-Ising-Calibration-1.5-31B-BF16 | 74.5 | 86.2 | 66.3 | 63.5 | 86.4 | 68.4 | 76.5 |
| Gemma-4-31B-IT | 68.8 | 85.6 | 54.3 | 59.8 | 82.7 | 68.3 | 62.1 |

MM-ICL scores:  

| Model | Mean | Q3 | Q5 | Q6 |
| --- | ---: | ---: | ---: | ---: |
| NVIDIA-Ising-Calibration-1.5-31B-BF16 | 81.2 | 71.7 | 85.0 | 86.9 |
| Gemma-4-31B-IT | 81.2 | 80.6 | 76.9 | 86.0 |

**Data Collection Method by dataset:** Synthetic  
**Labeling Method by dataset:** Synthetic  
**Properties (Quantity, Dataset Descriptions, Sensor(s)):** The evaluation dataset is QCalEval, a synthetic vision-language benchmark for quantum calibration plots containing 243 entries across 87 scenario types from 22 experiment families, covering superconducting qubits and neutral atoms. It assesses six question types: technical description, experimental conclusion, experimental significance, fit quality assessment, parameter extraction, and experiment success classification. Ground-truth labels are derived from simulation parameters, providing curated quantum calibration experiments.

## Inference:
**Acceleration Engine:** vLLM   
**Test Hardware:** NVIDIA Hopper (H100x2, TP2)

## Ethical Considerations:
NVIDIA believes Trustworthy AI is a shared responsibility and we have established policies and practices to enable development for a wide array of AI applications. Developers should work with their internal model team to ensure this model meets requirements for the relevant industry and use case and addresses unforeseen product misuse.

Please make sure you have proper rights and permissions for all input image content; if image inputs include people, personal health information, or intellectual property, developers are responsible for appropriate handling.  

For more detailed information on ethical considerations for this model, please see the Model Card++ Explainability, Bias, Safety & Security, and Privacy Subcards.  

Please report model quality, risk, security vulnerabilities or NVIDIA AI Concerns [here](https://www.nvidia.com/en-us/support/submit-security-vulnerability/).

## Specifications

- **Context Length:** 262,144 tokens
- **Parameters:** 31,273,088,876
- **Input:** Image, Text
- **Output:** Text

## Capabilities

- **Function Calling:** Not supported
- **Structured Output:** Not supported
- **Reasoning:** Not supported

## Bias

# Bias Subcard

## Participation considerations from adversely impacted groups [protected classes](https://www.senate.ca.gov/content/protected-classes) in model design and testing:

Not Applicable. Fine-tuning data consists of synthetically generated quantum calibration experiment plots with no human subjects.

## Measures taken to mitigate against unwanted bias:

Not Applicable. Fine-tuning data is synthetically generated scientific content with no human-generated or crowdsourced annotations.

## Bias Metric (If Measured):

Not Applicable.

## Explainability

# Explainability Subcard

## Intended Task/Domain:

Scientific research and quantum computing calibration experiment analysis

## Model Type:

Dense multimodal vision-language model based on Gemma 4 31B

## Intended Users:

Quantum computing researchers, calibration engineers, and developers analyzing experiment results in automated or assisted calibration workflows.

## Output:

Types: Text. Formats: String

## Describe how the model works:

Experiment plot images are encoded into visual tokens and combined with prompt text tokens before being processed by the Gemma 4 31B dense language model. The model generates analytical text autoregressively through the hosted OpenAI-compatible Preview API with a vLLM backend.

## Name the adversely impacted groups this has been tested to deliver comparable outcomes regardless of:

Not Applicable

## Technical Limitations and Mitigation:

The model is domain-specific to quantum calibration experiments and may not generalize to broader VLM tasks. Performance varies by question type, with weaker results on experimental significance and parameter extraction than on fit quality assessment. Outputs should be validated by domain experts before being used in experimental workflows.

## Verified to have met prescribed NVIDIA quality standards:

Yes

## Performance Metrics:

QCalEval zero-shot overall 74.5; QCalEval MM-ICL overall 81.2; throughput and latency were measured for the BF16 model release candidate on NVIDIA GPU-accelerated systems.

## Potential Known Risks:

The model may misclassify rare or ambiguous experiment outcomes, may hallucinate details outside the quantum calibration domain, and does not have access to raw numerical traces or experiment metadata beyond what is visible in the input plots.

## Terms of Use/Licensing:

OpenMDW License Agreement, version 1.1 (OpenMDW-1.1). Additional information: Gemma 4 31B is provided under Apache License, Version 2.0.

## Privacy

# Privacy Subcard

## Generatable or reverse engineerable personal data?

No

## Personal data used to create this model?

No

## Was consent obtained for any personal data used?

Not Applicable

## How often is dataset reviewed?

Before Every Release

## Was data from user interactions with the AI model (e.g. user input and prompts) used to train the model?

No

## Is there provenance for all datasets used in training?

Yes

## Does data labeling (annotation, metadata) comply with privacy laws?

Yes

## Is data compliant with data subject requests for data correction or removal, if such a request was made?

Not Applicable

## Applicable Privacy Policy

https://www.nvidia.com/en-us/about-nvidia/privacy-policy/

## Safety & Security

# Safety & Security Subcard

## Model Application Field(s):

Scientific research, quantum calibration plot understanding, and experiment workflow assistance

## Describe the life critical impact (if present).

Not Applicable. The model provides analysis assistance for quantum calibration experiments and does not directly control quantum hardware or make safety-critical decisions.

## Use Case Restrictions:

Abide by the OpenMDW License Agreement, version 1.1 (OpenMDW-1.1). Outputs should be reviewed by qualified domain experts before they are used to guide experiment decisions.

## Model and dataset restrictions:

The Principle of least privilege (PoLP) is applied to limit access for dataset generation and model development. Restrictions enforce dataset access during training, and dataset license constraints are adhered to.

## Prototype

```python
import requests

invoke_url = "https://integrate.api.nvidia.com/v1/chat/completions"

headers = {
"Authorization": "Bearer ",
"Accept": "application/json",
}

payload = {
"messages": [
{
"role": "user",
"content": ""
}
]
}

# re-use connections
session = requests.Session()

response = session.post(invoke_url, headers=headers, json=payload)

response.raise_for_status()
response_body = response.json()
print(response_body)
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

lc_messages = [{"role":"user","content":""}]

response = client.invoke(lc_messages)
print(response.content)
```

```javascript
import fetch from "node-fetch";

const invokeUrl = "https://integrate.api.nvidia.com/v1/chat/completions"

const headers = {
"Authorization": "Bearer ",
"Accept": "application/json",
}

const payload = {
"messages": [
{
"role": "user",
"content": ""
}
]
}

let response = await fetch(invokeUrl, {
method: "post",
body: JSON.stringify(payload),
headers: { "Content-Type": "application/json", ...headers }
});

let response_body = await response.json()

console.log(JSON.stringify(response_body))
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