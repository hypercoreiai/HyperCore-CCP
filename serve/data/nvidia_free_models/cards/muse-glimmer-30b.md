---
title: "muse-glimmer-30b"
publisher: "meta"
type: "endpoint"
updated: "2026-08-10T12:58:58.470Z"
description: "Muse Glimmer 30B is a multimodal reasoning model accepting text and images, with native tool-calling and separate reasoning output."
canonical: "https://build.nvidia.com/meta/muse-glimmer-30b"
---

# Muse Glimmer

## Description

Muse Glimmer is an approximately 29.6B-parameter dense multimodal causal language model with a dedicated perception encoder, distilled from Muse Spark and purpose-built for autonomous agentic tasks on consumer hardware. It accepts interleaved text and image inputs to produce text output and supports local operation without requiring cloud infrastructure or network access.

*This model is ready for commercial or non-commercial use.*

## Third-Party Community Consideration:

This model is not owned or developed by NVIDIA. This model has been developed and built to a third-party's requirements for this application and use case; see link to Non-NVIDIA [Muse Glimmer Model Card](https://huggingface.co/meta-models/Muse-Glimmer-30B)

## License and Terms of Use:

**GOVERNING TERMS:** Use of this trial service is governed by the [NVIDIA API Trial Terms of Service](https://assets.ngc.nvidia.com/products/api-catalog/legal/NVIDIA%20API%20Trial%20Terms%20of%20Service.pdf) and use of the model is governed by the [NVIDIA Open Model Agreement](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-agreement/).
ADDITIONAL INFORMATION: The base model is governed by [Apache License, Version 2.0](https://www.apache.org/licenses/LICENSE-2.0).

## Deployment Geography:

Global

## Use Case:

**Use Case:** Muse Glimmer is intended for commercial and research use in local AI agents, coding agents, multi-step planning, tool and function calling, failure recovery, and multimodal reasoning over screenshots, charts, documents, and images. It can also support synthetic data generation and evaluation of other models' outputs.

## Release Date:

**Build.NVIDIA.com:** 08/10/2026 via [link](https://build.nvidia.com/meta/muse-glimmer-30b)<br>
**Huggingface:** 08/10/2026 via [link](https://huggingface.co/meta-models/Muse-Glimmer-30B)

## Reference(s):
**References:**
* [Muse Glimmer Model Page](https://huggingface.co/meta-models/Muse-Glimmer-30B)

## Model Architecture:

**Architecture Type:** Transformer  
**Network Architecture:** Dense causal Transformer + ViT-G/14 perception encoder  
**Total Parameters:** 29.6B  
**Vocabulary Size:** 202,048

### Input:

**Input Types:** Text, Image  
**Input Formats:** String, Red, Green, Blue (RGB)  
**Input Parameters:** One-Dimensional (1D), Two-Dimensional (2D)  
**Other Input Properties:** Supports interleaved text and images, with up to 4,096 visual tokens per image.

### Output:

**Output Types:** Text  
**Output Format:** String  
**Output Parameters:** One-Dimensional (1D)  
**Other Output Properties:** Combined input and output context length is 131,072+ tokens.

__Our AI models are designed and/or optimized to run on NVIDIA GPU-accelerated systems. By leveraging NVIDIA's hardware (e.g. GPU cores) and software frameworks (e.g., CUDA libraries), the model achieves faster training and inference times compared to CPU-only solutions.__

## Software Integration:

**Runtime Engines:**
- **vLLM**

**Supported Hardware:**

- **NVIDIA Blackwell:** B100, B200, GB200, DGX Spark (GB10), GeForce RTX 5090, RTX PRO 6000 Blackwell
- **NVIDIA Hopper:** H100, H200

**Preferred Operating Systems:** Linux

__The integration of foundation and fine-tuned models into AI systems requires additional testing using use-case-specific data to ensure safe and effective deployment. Following the V-model methodology, iterative testing and validation at both unit and system levels are essential to mitigate risks, meet technical and functional requirements, and ensure compliance with safety and ethical standards before deployment.__

## Model Version(s)

Muse Glimmer v1.0

## Training, Testing, and Evaluation Datasets:

### Training Dataset

**Data Modality:** Text, Image  
**Image Training Data Size:** Undisclosed  
**Text Training Data Size:** Undisclosed  
**Training Data Collection:** Undisclosed  
**Training Labeling:** Undisclosed  
**Training Properties:** Multimodal content sourced from publicly available data, data provided by third parties, and information from the model developer's products and services. Muse Glimmer is trained on data from more than 100 languages; specific dataset names and sizes are undisclosed.

### Testing Dataset

**Testing Data Collection:** Undisclosed  
**Testing Labeling:** Undisclosed  
**Testing Properties:** Undisclosed

### Evaluation Dataset

**Evaluation Benchmark Score:** Muse Glimmer reports results across agentic, coding, multimodal, safety, general reasoning, and chem/bio benchmarks. Selected results include 75.5 on MCP Atlas (Public), 74.6 on DeepSearch QA, 76.0 on SWE-Bench Verified, and 94.7 on AIME 2026.

<details>
<summary><strong>Primary Benchmark Comparison Table</strong></summary>

<table>
<thead>
<tr><th>Category</th><th>Benchmark</th><th>Muse Glimmer (High Reasoning)</th><th>Gemma4-31B (Thinking Mode)</th><th>Qwen3.6-27B (Thinking Mode)</th></tr>
</thead>
<tbody>
<tr><td>General Agentic</td><td>MCP Atlas (Public)</td><td>75.5</td><td>54.2</td><td>62.5</td></tr>
<tr><td>General Agentic</td><td>DeepSearch QA</td><td>74.6</td><td>61.7</td><td>71.1</td></tr>
<tr><td>General Agentic</td><td>τ3-Banking</td><td>23.5</td><td>15.1</td><td>16.7</td></tr>
<tr><td>General Agentic</td><td>WildClawBench</td><td>47.6</td><td>37.6</td><td>43.2</td></tr>
<tr><td>General Agentic</td><td>GDPVal-AA v2</td><td>953</td><td>811</td><td>1141</td></tr>
<tr><td>General Agentic</td><td>Gaia2</td><td>43.3</td><td>36.4</td><td>40.0</td></tr>
<tr><td>General Agentic</td><td>SkillsBench (with skills)</td><td>44.3</td><td>32.4</td><td>46.6</td></tr>
<tr><td>General Agentic</td><td>OSWorld-Verified</td><td>65.9</td><td>58.5</td><td>75.6</td></tr>
<tr><td>Agentic Coding</td><td>SWE-Bench Pro</td><td>51.2</td><td>36.9</td><td>50.2</td></tr>
<tr><td>Agentic Coding</td><td>SWE-Bench Verified</td><td>76.0</td><td>66.6</td><td>77.2</td></tr>
<tr><td>Agentic Coding</td><td>TerminalBench 2.1 (with terminus2)</td><td>51.7</td><td>43.4</td><td>60.7</td></tr>
<tr><td>Agentic Coding</td><td>SciCode</td><td>43.6</td><td>43.4</td><td>39.8</td></tr>
<tr><td>Multimodal</td><td>Charxiv Reasoning</td><td>78.8</td><td>77.7</td><td>78.4</td></tr>
<tr><td>Multimodal</td><td>ScreenSpot Pro</td><td>75.4</td><td>75.9</td><td>76.1</td></tr>
<tr><td>Multimodal</td><td>OmniDocBench v1.5</td><td>75.8</td><td>72.5</td><td>77.8</td></tr>
<tr><td>Multimodal</td><td>MMMU Pro</td><td>74</td><td>73</td><td>75</td></tr>
<tr><td>Safety</td><td>CI Memories</td><td>Violation (↓): 26.4<br>Coverage: 64.8</td><td>Violation (↓): 12.1<br>Coverage: 53.0</td><td>Violation (↓): 53.4<br>Coverage: 66.9</td></tr>
<tr><td>Safety</td><td>Siren AgentDojo</td><td>Attack Success Rate (↓): 28.4<br>Utility: 94.2</td><td>Attack Success Rate (↓): 25.6<br>Utility: 90.8</td><td>Attack Success Rate (↓): 40.3<br>Utility: 92.7</td></tr>
<tr><td>General Capabilities and Reasoning</td><td>IFBench</td><td>77.0</td><td>76.0</td><td>70.8</td></tr>
<tr><td>General Capabilities and Reasoning</td><td>AIME 2026</td><td>94.7</td><td>89.2</td><td>94.1</td></tr>
<tr><td>General Capabilities and Reasoning</td><td>GPQA Diamond (AA)</td><td>83.5</td><td>85.7</td><td>84.2</td></tr>
<tr><td>General Capabilities and Reasoning</td><td>HLE Text (AA)</td><td>22.0</td><td>23.6</td><td>23.1</td></tr>
<tr><td>General Capabilities and Reasoning</td><td>AA-LCR</td><td>80.0</td><td>68.3</td><td>73.3</td></tr>
<tr><td>General Capabilities and Reasoning</td><td>Beam128K</td><td>65.1</td><td>58.2</td><td>63.0</td></tr>
</tbody>
</table>

</details>

<details>
<summary><strong>Chem/Bio Benchmark Comparison Table</strong></summary>

<table>
<thead>
<tr><th>Benchmark</th><th>Muse Glimmer</th><th>Gemma4-31B</th><th>Qwen3.6-27B</th><th>Kimi K3</th></tr>
</thead>
<tbody>
<tr><td>MBCT</td><td>41.5%</td><td>50.6%</td><td>45.9%</td><td>58.9%</td></tr>
<tr><td>HPCT</td><td>52.3%</td><td>54.0%</td><td>48.7%</td><td>59.6%</td></tr>
<tr><td>VCT</td><td>37.0%</td><td>43.5%</td><td>33.7%</td><td>48.0%</td></tr>
<tr><td>WMDP (Bio)</td><td>86.5%</td><td>85.9%</td><td>84.8%</td><td>89.1%</td></tr>
<tr><td>WMDP (Chem)</td><td>75.2%</td><td>80.5%</td><td>74.8%</td><td>84.2%</td></tr>
<tr><td>Lab Bench (ProtocolQA)</td><td>80.2%</td><td>75.8%</td><td>69.1%</td><td>81.9%</td></tr>
</tbody>
</table>

</details>

**Evaluation Data Collection:** Hybrid: Automated, Manually-Collected  
**Evaluation Labeling:** Hybrid: Automated, Manually-Labeled  
**Evaluation Properties:** Evaluation covers agentic task completion, coding, multimodal reasoning, safety, general capabilities, and reasoning using standard benchmarks and dedicated adversarial evaluation datasets. Safety evaluations assess content safety, agentic risk, appropriate information flows, and catastrophic risk; application-specific evaluation is recommended because testing cannot cover all deployment scenarios.

## Inference

**Acceleration Engine:** vLLM  
**Test Hardware:** NVIDIA Hopper (H100)

## Additional Details

### Deployment and Generation

Muse Glimmer has a knowledge cutoff of January 4, 2026. Released artifacts include BF16 full-precision weights, two approximately 4-bit quantized variants for 24 GB and 32 GB consumer hardware, a DFlash speculative-decoding drafter, and a frozen ViT-G/14 perception encoder. Recommended sampling parameters are temperature 1.0, top-p 0.95, and top-k 64; supported reasoning-strength settings are low, medium, high, and xhigh.

### Known Limitations

Muse Glimmer may produce inaccurate, biased, or objectionable responses and may make errors in multi-step reasoning, particularly in novel scenarios not well represented in its training data. It has not been evaluated on every language represented in its training data, and quantized inference may show minor quality differences in edge cases compared with full-precision inference. Deployers should perform use-case-specific safety evaluation and add appropriate guardrails.

## Ethical Considerations

NVIDIA believes Trustworthy AI is a shared responsibility and we have established policies and practices to enable development for a wide array of AI applications. Developers should work with their internal model team to ensure this model meets requirements for the relevant industry and use case and addresses unforeseen product misuse.

Please make sure you have proper rights and permissions for all input image content; if image includes people, personal health information, or intellectual property, the image generated will not blur or maintain proportions of image subjects included.

Users are responsible for model inputs and outputs. Users are responsible for ensuring safe integration of this model, including implementing guardrails as well as other safety mechanisms, prior to deployment.

Please report model quality, risk, security vulnerabilities or NVIDIA AI Concerns [here](https://www.nvidia.com/en-us/support/submit-security-vulnerability/).

## Specifications

- **Context Length:** 131,072 tokens
- **Parameters:** 29,776,626,688
- **Input:** Text, Image
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