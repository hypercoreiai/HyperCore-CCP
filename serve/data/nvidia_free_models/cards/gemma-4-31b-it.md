---
title: "gemma-4-31b-it"
publisher: "google"
type: "endpoint"
updated: "2026-04-02T16:23:29.660Z"
description: "Dense 31B model delivering frontier reasoning for coding, agentic workflows, and fine-tuning."
canonical: "https://build.nvidia.com/google/gemma-4-31b-it"
---

# Gemma 4 31B IT

## Description
Gemma 4 31B IT is an open multimodal model built by Google DeepMind that handles text and image inputs, can process video as sequences of frames, and generates text output. It is designed to deliver frontier-level performance for reasoning, agentic workflows, coding, and multimodal understanding on consumer GPUs and workstations, with a 256K-token context window and support for over 140 languages. The model uses a hybrid attention mechanism that interleaves local sliding-window and full global attention, with unified Keys and Values in global layers and Proportional RoPE (p-RoPE) to support long-context performance.

*This model is ready for commercial/non-commercial use.*

## Third-Party Community Consideration:
This model is not owned or developed by NVIDIA. This model has been developed and built to a third-party's requirements for this application and use case; see link to Non-NVIDIA [Gemma 4 31B IT Model Card](https://huggingface.co/google/gemma-4-31B-it)

## License and Terms of Use:
**GOVERNING TERMS:** This trial service is governed by the [NVIDIA API Trial Terms of Service](https://assets.ngc.nvidia.com/products/api-catalog/legal/NVIDIA%20API%20Trial%20Terms%20of%20Service.pdf). Use of this model is governed by the [NVIDIA Open Model License Agreement](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license/). Additional Information:[Apache License, Version 2.0](https://ai.google.dev/gemma/docs/gemma_4_license).

## Deployment Geography:
Global

## Use Case:
**Use Case:** Designed for text generation, chatbots and conversational AI, text summarization, image data extraction, reasoning, coding, multimodal understanding, function calling, and research or educational use.

## Release Date:
**Build.NVIDIA.com:** 04/02/2026 via [link](https://build.nvidia.com/google/gemma-4-31b-it)  
**Huggingface:** 04/02/2026 via [link](https://huggingface.co/google/gemma-4-31B-it)

## Model Architecture:
**Architecture Type:** Transformer  
**Network Architecture:** Gemma 4  
**Total Parameters:** 30.7B  
**Vocabulary Size:** 262,144

### Input:
**Input Types:** Text, Image, Video  
**Input Formats:** String, Red, Green, Blue (RGB), Video (MP4/WebM)  
**Input Parameters:** One-Dimensional (1D), Two-Dimensional (2D), Three-Dimensional (3D)  
**Other Input Properties:** Supports variable image aspect ratios and resolutions, configurable visual token budgets of 70, 140, 280, 560, and 1120, and video inputs up to 60 seconds at one frame per second.  
**Input Context Length (ISL):** 256K

### Output:
**Output Types:** Text  
**Output Format:** String  
**Output Parameters:** One-Dimensional (1D)  
**Other Output Properties:** Generates text responses for chat, reasoning, coding, multimodal understanding, and function-calling workflows.

__Our AI models are designed and/or optimized to run on NVIDIA GPU-accelerated systems. By leveraging NVIDIA's hardware (e.g. GPU cores) and software frameworks (e.g., CUDA libraries), the model achieves faster training and inference times compared to CPU-only solutions.__

## Software Integration:
**Runtime Engines:**
- **vLLM**
- **SGLang**

**Supported Hardware:**
- **NVIDIA Ampere:** A100
- **NVIDIA Blackwell:** B100, B200, GB200
- **NVIDIA Hopper:** H100, H200

**Preferred Operating Systems:** Linux

__The integration of foundation and fine-tuned models into AI systems requires additional testing using use-case-specific data to ensure safe and effective deployment. Following the V-model methodology, iterative testing and validation at both unit and system levels are essential to mitigate risks, meet technical and functional requirements, and ensure compliance with safety and ethical standards before deployment.__

## Model Version(s)
Gemma 4 31B IT v1.0

## Training, Testing, and Evaluation Datasets:

### Training Dataset
**Data Modality:** Text, Image, Audio, Other (Code)  
**Training Data Collection:** Automated  
**Training Labeling:** Undisclosed  
**Training Properties:** Large-scale multimodal pre-training data spanning web documents, code, images, and audio, with a cutoff date of January 2025 and coverage in over 140 languages. Data was filtered for CSAM, sensitive data, quality, and safety.

### Testing Dataset
**Testing Data Collection:** Undisclosed  
**Testing Labeling:** Undisclosed  
**Testing Properties:** Undisclosed

### Evaluation Dataset
**Evaluation Benchmark Score:** Benchmark results are provided in the [Gemma 4 31B IT Model Card](https://huggingface.co/google/gemma-4-31B-it) comparing Gemma 4 31B IT to similar sized models across text and vision tasks. Specific scores vary by benchmark.  
**Evaluation Data Collection:** Hybrid: Automated, Human  
**Evaluation Labeling:** Hybrid: Automated, Human  
**Evaluation Properties:** Gemma 4 models were evaluated across reasoning, coding, vision, long-context, and safety tasks, with benchmark table results reported for instruction-tuned models. Evaluation Methodology Notes:
- `Tau2` is reported as an average over 3 runs.
- `HLE` is reported with and without search.
- `OmniDocBench 1.5` uses average edit distance, where lower is better.
- `MRCR v2 8 needle 128k` is reported as an average.
- Safety evaluations included both automated and human assessments, and all safety testing was conducted without safety filters for both text-to-text and image-to-text settings.

<details>
<summary><strong>Detailed Benchmark Comparison Table</strong></summary>

| Benchmark | Gemma 4 31B | Gemma 4 26B A4B | Gemma 4 E4B | Gemma 4 E2B | Gemma 3 27B (no think) |
|-----------|-------------|-----------------|-------------|-------------|------------------------|
| MMLU Pro | 85.2% | 82.6% | 69.4% | 60.0% | 67.6% |
| AIME 2026 no tools | 89.2% | 88.3% | 42.5% | 37.5% | 20.8% |
| LiveCodeBench v6 | 80.0% | 77.1% | 52.0% | 44.0% | 29.1% |
| Codeforces ELO | 2150 | 1718 | 940 | 633 | 110 |
| GPQA Diamond | 84.3% | 82.3% | 58.6% | 43.4% | 42.4% |
| Tau2 (average over 3) | 76.9% | 68.2% | 42.2% | 24.5% | 16.2% |
| HLE no tools | 19.5% | 8.7% | - | - | - |
| HLE with search | 26.5% | 17.2% | - | - | - |
| BigBench Extra Hard | 74.4% | 64.8% | 33.1% | 21.9% | 19.3% |
| MMMLU | 88.4% | 86.3% | 76.6% | 67.4% | 70.7% |
| **Vision** |  |  |  |  |  |
| MMMU Pro | 76.9% | 73.8% | 52.6% | 44.2% | 49.7% |
| OmniDocBench 1.5 (average edit distance, lower is better) | 0.131 | 0.149 | 0.181 | 0.290 | 0.365 |
| MATH-Vision | 85.6% | 82.4% | 59.5% | 52.4% | 46.0% |
| MedXPertQA MM | 61.3% | 58.1% | 28.7% | 23.5% | - |
| **Audio** |  |  |  |  |  |
| CoVoST | - | - | 35.54 | 33.47 | - |
| FLEURS (lower is better) | - | - | 0.08 | 0.09 | - |
| **Long Context** |  |  |  |  |  |
| MRCR v2 8 needle 128k (average) | 66.4% | 44.1% | 25.4% | 19.1% | 13.5% |

</details>

## Inference
**Acceleration Engine:** vLLM   
**Test Hardware:** NVIDIA Hopper H100

## Additional Details
### Best Practices
For best performance, use the partner-recommended sampling configuration of `temperature=1.0`, `top_p=0.95`, and `top_k=64` across use cases.

### Thinking Mode Configuration
Compared to Gemma 3, Gemma 4 uses standard system, assistant, and user roles. Thinking is enabled by including the `<|think|>` token at the start of the system prompt and disabled by removing it. When thinking is enabled, the model outputs its internal reasoning followed by the final answer using the structure `<|channel>thought\n[Internal reasoning]<channel|>`. For models other than `E2B` and `E4B`, including `31B`, disabling thinking still produces the tags with an empty thought block before the final answer: `<|channel>thought\n<channel|>[Final answer]`. Libraries such as Transformers and `llama.cpp` may handle chat-template details automatically.

### Multi-Turn Conversations
In multi-turn conversations, historical model output should include only the final response. Thought content from previous turns should not be included before the next user turn begins.

### Multimodal Input Guidance
For optimal multimodal performance, place image content before text in the prompt. For variable image resolution, Gemma 4 uses a configurable visual token budget with supported values of `70`, `140`, `280`, `560`, and `1120`. Lower budgets are better suited to classification, captioning, or video understanding where faster inference and processing many frames are preferred, while higher budgets are better suited to OCR, document parsing, or reading small text.

### Video Length
The `31B` model can process video as frames and supports video inputs up to `60` seconds when frames are processed at one frame per second.

### Usage and Limitations
These models have certain limitations that users should be aware of.

#### Intended Usage
The Gemma 4 model card describes a broad intended-usage set for the Gemma 4 family across content creation, communication, research, and education. Example uses include text generation for creative and practical formats such as poems, scripts, code, marketing copy, and email drafts; chatbots and conversational AI for customer service, virtual assistants, or interactive applications; text summarization for corpora, research papers, or reports; image data extraction for interpreting and summarizing visual data into text communications; natural language processing and VLM research; language learning tools; and knowledge exploration over large bodies of text. It also notes audio processing and interaction for the smaller `E2B` and `E4B` models only.

#### Limitations
- Training data quality and diversity significantly influence model capabilities, and biases or gaps in the training data can lead to limitations in model responses.
- The scope of the training dataset affects which subject areas the model can handle effectively.
- Models perform best on tasks framed with clear prompts and instructions; open-ended or highly complex tasks may be challenging.
- Performance can be influenced by the amount of context provided, with longer context often helping only up to a point.
- Natural language ambiguity and nuance, including sarcasm and figurative language, may still be difficult for the model to handle reliably.
- The model generates responses from learned training patterns rather than from a live knowledge base, so outputs can contain incorrect or outdated factual statements.
- The model may lack the ability to apply common-sense reasoning in some situations.

## Ethical Considerations
NVIDIA believes Trustworthy AI is a shared responsibility and we have established policies and practices to enable development for a wide array of AI applications. When downloaded or used in accordance with our terms of service, developers should work with their internal model team to ensure this model meets requirements for the relevant industry and use case and addresses unforeseen product misuse.

Please make sure you have proper rights and permissions for all input image and video content; if image or video includes people, personal health information, or intellectual property, the image or video generated will not blur or maintain proportions of image subjects included.

Please report model quality, risk, security vulnerabilities or NVIDIA AI Concerns [here](https://www.nvidia.com/en-us/support/submit-security-vulnerability/).

## Specifications

- **Context Length:** 262,144 tokens
- **Parameters:** 32,682,372,656
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