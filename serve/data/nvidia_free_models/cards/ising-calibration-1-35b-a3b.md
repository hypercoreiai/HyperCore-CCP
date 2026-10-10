---
title: "ising-calibration-1-35b-a3b"
publisher: "nvidia"
type: "endpoint"
updated: "2026-04-14T19:24:38.061Z"
description: "Open VLM for quantum computer calibration chart understanding across a range of qubit modalities."
canonical: "https://build.nvidia.com/nvidia/ising-calibration-1-35b-a3b"
---

# Model Overview

### Description:
`Ising-Calibration-1-35B-A3B` analyzes quantum computing calibration experiment plots and generates structured technical text across six analysis question categories. `Ising-Calibration-1-35B-A3B` was developed by NVIDIA as a quantum calibration vision-language model built on `Qwen3.5-35B-A3B`. This model is ready for commercial/non-commercial use. <br>

### License/Terms of Use:
**GOVERNING HOSTING TERMS**
The Ising-Calibration-1-35B-A3B is governed by the [NVIDIA Open Model License Agreement](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license/).
By continuing you consent to processing and agree to the [NVIDIA API Trial Terms of Service](https://assets.ngc.nvidia.com/products/api-catalog/legal/NVIDIA%20API%20Trial%20Terms%20of%20Service.pdf). **ADDITIONAL INFORMATION**: For Qwen3.5-35B-A3B [Apache License, Version 2.0](https://huggingface.co/Qwen/Qwen3.5-35B-A3B/blob/main/LICENSE). <br>

### Deployment Geography:
Global <br>

### Use Case: <br>
Quantum computing researchers, calibration engineers, and developers can use this model to analyze experiment plot images and generate technical descriptions, experimental conclusions, significance assessments, fit quality evaluations, parameter extractions, and experiment success classifications. Model outputs should be validated by domain experts before acting on experimental conclusions. <br>

### Release Date: <br>
**Hugging Face:** 04/14/2026 via https://huggingface.co/nvidia/Ising-Calibration-1-35B-A3B <br>
**Build.NVIDIA.com:** 04/14/2026 via https://build.nvidia.com/nvidia/ising-calibration-1-35b-a3b <br>

## References(s):
- [Qwen3.5](https://huggingface.co/Qwen/)
- [QCalEval Benchmark](https://huggingface.co/datasets/nvidia/QCalEval) <br>

## Model Architecture:
**Architecture Type:** Mixture-of-Experts Vision-Language Model (MoE VLM) <br>

**Network Architecture:** Integrated vision encoder for experiment plot images combined with the `Qwen3.5-35B-A3B` MoE language model for autoregressive text generation. <br>

**This model was developed based on:** `Qwen3.5-35B-A3B` <br>

**Number of model parameters:** ~35B total parameters, ~3B active per token (256 experts, 8 active) <br>

## Input(s): <br>
**Input Type(s):** Image, Text <br>

**Input Format(s):**
- Image: PNG, JPEG <br>
- Text: String <br>

**Input Parameters:**
- Image: Two-Dimensional (2D) <br>
- Text: One-Dimensional (1D) <br>

**Other Properties Related to Input:** Single-image or multi-image quantum calibration experiment plots with text prompts delivered through an OpenAI-compatible API. Default inference settings use `temperature=0` and `max_tokens=16384`. <br>

## Output(s)

**Output Type(s):** Text <br>

**Output Format(s):**
- Text: String <br>

**Output Parameters:**
- Text: One-Dimensional (1D) <br>

**Other Properties Related to Output:** Natural language technical analysis, experimental conclusions, significance assessments, fit quality evaluations, parameter extractions, and experiment success classifications. <br>

Our AI models are designed and/or optimized to run on NVIDIA GPU-accelerated systems. By leveraging NVIDIA hardware and software frameworks, the model achieves faster inference times compared to CPU-only solutions. <br>

## Software Integration:
**Runtime Engine(s):** <br>
* vLLM <br>

**Supported Hardware Microarchitecture Compatibility:** <br>
* NVIDIA Ada Lovelace <br>
* NVIDIA Blackwell <br>
* NVIDIA Hopper <br>

**Supported Operating System(s):**
* Linux (`Ubuntu 22.04+`) <br>

The integration of foundation and fine-tuned models into AI systems requires additional testing using use-case-specific data to ensure safe and effective deployment. Following the V-model methodology, iterative testing and validation at both unit and system levels are essential to mitigate risks before deployment. <br>

## Model Version(s):
`v1.0.0` <br>

## Training, Testing, and Evaluation Datasets:

## Training Dataset:

### Data Modality:
* Image <br>
* Text <br>

### Training Data Size:
72.5K total entries (Phase 1: 23.8K ICL-formatted entries; Phase 2: 48.7K zero-shot entries). <br>

**Data Collection Method by dataset**
* Synthetic (LLM-augmented via Qwen3.5-397B-A17B) <br>

**Labeling Method by dataset**
* Synthetic <br>

**Properties:** Synthetically generated quantum calibration experiment plots with paired analytical text. <br>

## Testing and Evaluation Dataset:

**Benchmark Score:** [QCalEval](https://huggingface.co/datasets/nvidia/QCalEval) Benchmark zero-shot scores. <br>

**Description:** QCalEval is a VLM benchmark for quantum calibration plots: 243 entries across 87 scenario types from 22 experiment families, spanning superconducting qubits and neutral atoms. It evaluates six question types: technical description (Q1), experimental conclusion (Q2), experimental significance (Q3), fit quality assessment (Q4), parameter extraction (Q5), and experiment success classification (Q6). <br>

Data Collection Method by dataset:
* Synthetic <br>

Labeling Method by dataset:
* Synthetic <br>

**Properties:** Curated quantum calibration experiments with ground-truth labels derived from simulation parameters. <br>

## Inference:
**Acceleration Engine:** vLLM <br>
**Test Hardware:** <br>
* 2x NVIDIA L40S (48GB) <br>

## Ethical Considerations:
NVIDIA believes Trustworthy AI is a shared responsibility and developers should ensure this model meets the requirements of their use case and addresses foreseeable misuse before deployment. <br>

For more detailed information on ethical considerations for this model, please see the Model Card++ Bias, Explainability, Safety & Security, and Privacy Subcards. <br>

Please report model quality, risk, security vulnerabilities or NVIDIA AI Concerns [here](https://www.nvidia.com/en-us/support/submit-security-vulnerability/). <br>

## Specifications

- **Context Length:** 262,144 tokens
- **Parameters:** 35,107,181,936
- **Input:** Image, Text
- **Output:** Text

## Capabilities

- **Function Calling:** Not supported
- **Structured Output:** Not supported
- **Reasoning:** Supported

## Bias

Field | Response
:---|:---
Participation considerations from adversely impacted groups [protected classes](https://calcivilrights.ca.gov/disputeresolution/protected-characteristics/) in model design and testing: | Not Applicable. Fine-tuning data consists of synthetically generated quantum calibration experiment plots with no human subjects.
Measures taken to mitigate against unwanted bias: | Not Applicable. Fine-tuning data is synthetically generated scientific content with no human-generated or crowdsourced annotations.

## Explainability

Field | Response
:---|:---
Intended Task/Domain: | Scientific research and quantum computing calibration experiment analysis
Model Type: | Mixture-of-Experts Vision-Language Model (MoE VLM) based on `Qwen3.5-35B-A3B`
Intended Users: | Quantum computing researchers, calibration engineers, and developers analyzing experiment results in automated or assisted calibration workflows.
Output: | Text responses covering technical descriptions, experimental conclusions, significance assessments, fit quality evaluations, parameter extraction, and experiment success classifications.
Describe how the model works: | Experiment plot images are encoded into visual tokens and combined with prompt text tokens before being processed by the `Qwen3.5-35B-A3B` MoE language model. The model activates 8 of 256 experts per token, corresponding to about 3B active parameters out of roughly 35B total parameters, and generates analytical text autoregressively through a vLLM-served OpenAI-compatible API.
Name the adversely impacted groups this has been tested to deliver comparable outcomes regardless of: | Not Applicable
Technical Limitations & Mitigation: | The model is domain-specific to quantum calibration experiments and may not generalize to broader VLM tasks. Performance varies by question type, with weaker results on experimental significance and parameter extraction than on fit quality assessment. Outputs should be validated by domain experts before being used in experimental workflows.
Performance Metrics: | QCalEval zero-shot scores (averaged): Q1 Technical Description `87.8`, Q2 Experimental Conclusion `67.1`, Q3 Experimental Significance `64.7`, Q4 Fit Quality Assessment `90.5`, Q5 Parameter Extraction `62.5`, Q6 Experiment Success `75.3`, Overall `74.7`.
Verified to have met prescribed NVIDIA quality standards: | Yes
Potential Known Risks: | The model may misclassify rare or ambiguous experiment outcomes, may hallucinate details outside the quantum calibration domain, and does not have access to raw numerical traces or experiment metadata beyond what is visible in the input plots.
Licensing: | **GOVERNING HOSTING TERMS**<br>The Ising-Calibration-1-35B-A3B is governed by the [NVIDIA Open Model License Agreement](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license/).<br>By continuing you consent to processing and agree to the [NVIDIA API Trial Terms of Service](https://assets.ngc.nvidia.com/products/api-catalog/legal/NVIDIA%20API%20Trial%20Terms%20of%20Service.pdf).<br><br>**ADDITIONAL INFORMATION**: For Qwen3.5-35B-A3B [Apache License, Version 2.0](https://huggingface.co/Qwen/Qwen3.5-35B-A3B/blob/main/LICENSE).

## Privacy

Field | Response
:---|:---
Generatable or reverse engineerable personal data? | No
Personal data used to create this model? | No
Was consent obtained for any personal data used? | Not Applicable
How often is dataset reviewed? | Before Every Release
Was data from user interactions with the AI model (e.g. user input and prompts) used to train the model? | No
Is there provenance for all datasets used in training? | Yes
Does data labeling (annotation, metadata) comply with privacy laws? | Yes
Is data compliant with data subject requests for data correction or removal, if such a request was made? | Not Applicable
Applicable Privacy Policy | https://www.nvidia.com/en-us/about-nvidia/privacy-policy/

## Safety & Security

Field | Response
:---|:---
Model Application Field(s): | Scientific research, quantum calibration analysis, and experiment workflow assistance
Describe the life critical impact (if present). | Not Applicable. The model provides analysis assistance for quantum calibration experiments and does not directly control quantum hardware or make safety-critical decisions.
Use Case Restrictions: | **GOVERNING HOSTING TERMS**<br>The Ising-Calibration-1-35B-A3B is governed by the [NVIDIA Open Model License Agreement](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license/).<br>By continuing you consent to processing and agree to the [NVIDIA API Trial Terms of Service](https://assets.ngc.nvidia.com/products/api-catalog/legal/NVIDIA%20API%20Trial%20Terms%20of%20Service.pdf).<br><br>**ADDITIONAL INFORMATION**: For Qwen3.5-35B-A3B [Apache License, Version 2.0](https://huggingface.co/Qwen/Qwen3.5-35B-A3B/blob/main/LICENSE).
Model and dataset restrictions: | The Principle of least privilege (PoLP) is applied limiting access for dataset generation and model development. Restrictions enforce dataset access during training, and dataset license constraints adhered to.

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