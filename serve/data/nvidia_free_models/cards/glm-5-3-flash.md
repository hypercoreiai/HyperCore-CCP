---
title: "glm-5-3-flash"
publisher: "z-ai"
type: "endpoint"
updated: "2026-09-15T19:46:42.256Z"
description: "Multimodal 320B-total / 18B-active MoE with hybrid KDA and sparse MLA attention, native FP8 weights, reasoning and tool calling."
canonical: "https://build.nvidia.com/z-ai/glm-5-3-flash"
---

# GLM-5.3-Flash

## Description

GLM-5.3-Flash is the first natively multimodal model in Z.ai's GLM-5 series. With 320B total
parameters and 18B active per token, it outperforms GLM-5.2 across benchmarks and real-world
workloads at roughly one-tenth the price, approaching Claude Opus 4.8 on coding and agentic
benchmarks.

It starts from a newly trained base model whose architecture and training recipe were redesigned
around capability and efficiency. For the first time in the GLM series it uses a hybrid attention
stack combining sparse and linear attention, sharply reducing long-context serving cost while
preserving precise long-context behaviour, and adopts Manifold-Constrained Hyper-Connections (mHC)
to improve scaling efficiency. It was pre-trained on a 30T-token multimodal corpus.

The model understands **text and images**, and supports reasoning, function/tool calling, and a
multi-token-prediction (MTP) draft layer for speculative decoding.

This model is ready for commercial use.

## Third-Party Community Consideration:

This model is not owned or developed by NVIDIA. This model has been developed and built to a
third-party's requirements for this application and use case; see link to Non-NVIDIA
[GLM-5.3-Flash Model Card](https://huggingface.co/zai-org/GLM-5.3-Flash)

## License and Terms of Use:

**GOVERNING TERMS:** Use of this trial service is governed by the [NVIDIA API Trial Terms of Service](https://assets.ngc.nvidia.com/products/api-catalog/legal/NVIDIA%20API%20Trial%20Terms%20of%20Service.pdf).
ADDITIONAL INFORMATION: Use of the model is governed by the [MIT License](https://huggingface.co/datasets/choosealicense/licenses/blob/main/markdown/mit.md).

## Deployment Geography:

Global

## Use Case:

**Use Case:** Multimodal assistants and agents: visual question answering and multi-image
reasoning, document and screenshot understanding, coding and tool-using agents, and long-context
document intelligence. The low active-parameter count makes it suited to high-throughput,
cost-sensitive serving.

## Release Date:

**Huggingface:** 08/25/2026 via [link](https://huggingface.co/zai-org/GLM-5.3-Flash)

## Reference(s):

**References:**
* [GLM-5.3-Flash Model Page](https://huggingface.co/zai-org/GLM-5.3-Flash)
* [GLM-5.3-Flash blog](https://z.ai/blog/glm-5.3-flash)
* [GLM-5 Technical Report](https://arxiv.org/abs/2602.15763)
* [vLLM recipe](https://recipes.vllm.ai/zai-org/GLM-5.3-Flash)

## Model Architecture:

**Architecture Type:** Transformer (sparse Mixture-of-Experts, hybrid sparse + linear attention)<br>
**Network Architecture:** GLM-5.3-Flash (`Glm5NextForConditionalGeneration`) — 45 decoder layers
in a hybrid attention stack: 34 KDA linear-attention layers interleaved with 11 DeepSeek sparse
attention layers (every fourth layer), plus Manifold-Constrained Hyper-Connections (mHC), 288
routed experts per MoE layer with top-8 routing, a vision encoder for native image input, and 1 MTP
layer.<br>
**Number of Model Parameters:** 320B total, 18B activated per token

### Input:

**Input Type(s):** Text, Image<br>
**Input Format(s):** String; Image (png, jpg, jpeg, webp)<br>
**Input Parameters:** Text: One-Dimensional (1D); Image: Two-Dimensional (2D)<br>
**Other Properties Related to Input:** Context length up to 1,048,576 tokens. Up to 8 images per
request on this endpoint. Thinking budget is controlled by `reasoning_effort`, which accepts `low`,
`high`, or `max` and defaults to `max`. In the chat template `clear_thinking` defaults to `false`;
chat scenarios should pass `clear_thinking=true` explicitly.

### Output:

**Output Type(s):** Text<br>
**Output Format:** String<br>
**Output Parameters:** One-Dimensional (1D)<br>
**Other Properties Related to Output:** Reasoning content is returned separately from the answer.
Tool calls are emitted in OpenAI-compatible form.

## Software Integration:

**Runtime Engines:**
- **vLLM** (via NVIDIA Dynamo)

**Supported Hardware:**
- **NVIDIA Hopper:** H100

**Preferred Operating Systems:** Linux

__The integration of foundation and fine-tuned models into AI systems requires additional testing using use-case-specific data to ensure safe and effective deployment. Following the V-model methodology, iterative testing and validation at both unit and system levels are essential to mitigate risks, meet technical and functional requirements, and ensure compliance with safety and ethical standards before deployment.__

## Model Version(s)

GLM-5.3-Flash

## Inference

**Acceleration Engine:** vLLM on NVIDIA Dynamo<br>
**Test Hardware:** NVIDIA Hopper (H100)

This endpoint serves the native FP8 checkpoint tensor-parallel across 8 H100 GPUs, with MTP
speculative decoding enabled.

## Additional Details

### Known Limitations

GLM-5.3-Flash may produce inaccurate, biased, or objectionable responses, and may err in multi-step
reasoning, particularly in scenarios not well represented in its training data. Image understanding
quality varies with resolution and image quality. Deployers should perform use-case-specific safety
evaluation and add appropriate guardrails.

## Ethical Considerations

NVIDIA believes Trustworthy AI is a shared responsibility and we have established policies and practices to enable development for a wide array of AI applications. Developers should work with their internal model team to ensure this model meets requirements for the relevant industry and use case and addresses unforeseen product misuse.

## Specifications

- **Context Length:** 1,048,576 tokens
- **Parameters:** 320B
- **Input:** Text, Image
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

print(completion.choices[0].message)
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
stream: ,
})

process.stdout.write(completion.choices[0]?.message?.content);

}

main();
```

```bash
curl https://integrate.api.nvidia.com/v1/chat/completions \
-H "Content-Type: application/json" \
-H "Authorization: Bearer $NVIDIA_API_KEY" \
-d '{
"model": "z-ai/glm-5.3-flash",
"messages": [{"role":"user","content":""}],
"temperature": ,   
"top_p": ,
"max_tokens": ,
"stream":                 
}'
```