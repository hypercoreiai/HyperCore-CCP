---
title: "glm-5-3"
publisher: "z-ai"
type: "endpoint"
updated: "2026-09-15T19:47:58.961Z"
description: "753B-parameter text MoE with DeepSeek-style sparse attention, native FP8 weights, reasoning and tool calling."
canonical: "https://build.nvidia.com/z-ai/glm-5-3"
---

# GLM-5.3

## Description

GLM-5.3 is a 753B-parameter text Mixture-of-Experts model from Z.ai, built on the same base model
as GLM-5.2 with every gain coming from post-training. It is aimed at complex coding and
long-horizon agentic work, and reports a 50% improvement over GLM-5.2 on Z.ai's in-house Code
Bench along with open-weights state of the art on Terminal Bench 3.0 and Agents' Last Exam.
Post-training also produced a marked jump in cyber capability, where the model leads CyberGym for
vulnerability discovery.

The model uses DeepSeek-style sparse attention (DSA) over a 1,048,576-token context, and supports
reasoning, function/tool calling, and a multi-token-prediction (MTP) draft layer for speculative
decoding.

This model is ready for commercial use.

## Third-Party Community Consideration:

This model is not owned or developed by NVIDIA. This model has been developed and built to a
third-party's requirements for this application and use case; see link to Non-NVIDIA
[GLM-5.3 Model Card](https://huggingface.co/zai-org/GLM-5.3)

## License and Terms of Use:

**GOVERNING TERMS:** Use of this trial service is governed by the [NVIDIA API Trial Terms of Service](https://assets.ngc.nvidia.com/products/api-catalog/legal/NVIDIA%20API%20Trial%20Terms%20of%20Service.pdf).
ADDITIONAL INFORMATION: Use of the model is governed by the [GLM-5.3 License](https://huggingface.co/zai-org/GLM-5.3/blob/main/LICENSE).
The licence is MIT-like, with the addition that a Model-as-a-Service operator whose aggregate
revenue exceeds 10 billion US dollars over any consecutive 12 months must pass a Z.ai security
review before commercial use.

## Deployment Geography:

Global

## Use Case:

**Use Case:** Agentic software engineering: repository-scale code generation and refactoring,
terminal and tool-driven agents, long-horizon multi-step planning with failure recovery, and
security research including vulnerability discovery. The 1M-token context also suits long-document
and whole-codebase analysis.

## Release Date:

**Huggingface:** 08/27/2026 via [link](https://huggingface.co/zai-org/GLM-5.3)

## Reference(s):

**References:**
* [GLM-5.3 Model Page](https://huggingface.co/zai-org/GLM-5.3)
* [GLM-5 Technical Report](https://arxiv.org/abs/2602.15763)
* [vLLM recipe](https://recipes.vllm.ai/zai-org/GLM-5.3)

## Model Architecture:

**Architecture Type:** Transformer (sparse Mixture-of-Experts with sparse attention)<br>
**Network Architecture:** GLM-5.3 (`GlmMoeDsaForCausalLM`) — 78 decoder layers (3 dense MLP + 75
MoE), 256 routed experts per MoE layer with top-8 routing plus 1 shared expert, DeepSeek Sparse
Attention with an indexer selecting 2,048 tokens per query, and 1 MTP layer.<br>
**Number of Model Parameters:** 753B total, ~40B activated per token

### Input:

**Input Type(s):** Text<br>
**Input Format(s):** String<br>
**Input Parameters:** One-Dimensional (1D)<br>
**Other Properties Related to Input:** Context length up to 1,048,576 tokens. Thinking budget is
controlled by `reasoning_effort`, which accepts `low`, `high`, or `max` and defaults to `max`. In
the chat template `clear_thinking` defaults to `false`; chat scenarios should pass
`clear_thinking=true` explicitly.

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
- **NVIDIA Blackwell:** GB300

**Preferred Operating Systems:** Linux

__The integration of foundation and fine-tuned models into AI systems requires additional testing using use-case-specific data to ensure safe and effective deployment. Following the V-model methodology, iterative testing and validation at both unit and system levels are essential to mitigate risks, meet technical and functional requirements, and ensure compliance with safety and ethical standards before deployment.__

## Model Version(s)

GLM-5.3

## Inference

**Acceleration Engine:** vLLM on NVIDIA Dynamo<br>
**Test Hardware:** NVIDIA Blackwell (GB300)

This endpoint serves an NVFP4-quantized checkpoint on two-node GB300 workers (8 GPUs per worker),
using data parallelism with expert parallelism across the 8 GPUs, an FP8 KV cache, CPU KV-cache
offloading, and MTP speculative decoding.

## Additional Details

### Known Limitations

GLM-5.3 may produce inaccurate, biased, or objectionable responses, and may err in multi-step
reasoning, particularly in scenarios not well represented in its training data. This endpoint
serves a 4-bit (NVFP4) quantized checkpoint, so outputs may differ from the full-precision model in
edge cases. The model's cyber capabilities are a stated strength and warrant particular care:
deployers should apply use-case-specific safety evaluation and appropriate guardrails.

## Ethical Considerations

NVIDIA believes Trustworthy AI is a shared responsibility and we have established policies and practices to enable development for a wide array of AI applications. Developers should work with their internal model team to ensure this model meets requirements for the relevant industry and use case and addresses unforeseen product misuse.

## Specifications

- **Context Length:** 1,048,576 tokens
- **Parameters:** 753B
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
"model": "z-ai/glm-5.3",
"messages": [{"role":"user","content":""}],
"temperature": ,   
"top_p": ,
"max_tokens": ,
"stream":                 
}'
```