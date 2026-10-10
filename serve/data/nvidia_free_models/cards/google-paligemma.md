---
title: "paligemma"
publisher: "google"
type: "endpoint"
updated: "2024-08-26T16:47:12.134Z"
description: "Vision language model adept at comprehending text and visual inputs to produce informative responses"
canonical: "https://build.nvidia.com/google/google-paligemma"
---

# Model Overview

## Description:

The Google PaLIGemma-3B-mix model is a one-shot visual language understanding solution for image-to-text generation.  This model is ready for commercial use.

## Third-Party Community Consideration
This model is not owned or developed by NVIDIA. This model has been developed and built to a third-party’s requirements for this application and use case; see link to Google's [(PaliGemma Model Card](https://ai.google.dev/gemma/docs/paligemma/model-card).

## License, Acceptable Use, and Research Privacy Policy

By using this model, you are agreeing to the terms and conditions of the 
[License](https://github.com/google-research/google-research/blob/master/LICENSE), 
[Acceptable Use Policy](https://policies.google.com/terms) and 
[Google Research Privacy Policy](https://policies.google.com/privacy).

## References(s):

* [SigLIP paper](https://arxiv.org/pdf/2303.15343)
* [Gemma paper](https://arxiv.org/pdf/2403.08295)
* [PaLIGemma on HuggingFace](https://huggingface.co/google/paligemma-3b-mix-224-jax)

## Model Architecture:
**Architecture Type:** Transformer <br>
**Network Architecture:** SigLIP + Gemma <br>

## Input:
**Input Format:** Image + Text <br>
**Input Parameters:** Image: Red, Green, and Blue (RGB); Text: String <br>
**Other Properties Related to Input:** Prompt to caption the image or a question. <br>

## Output: <br>
**Output Format:** Text <br>
**Output Parameters:** temperature, top_p, max_tokens <br>
**Other Properties Related to Output:** Stream <br>

## Supported Operating System(s):
* Linux

# Inference:
**Engine:** [Triton](https://developer.nvidia.com/triton-inference-server) <br>
**Test Hardware:** Other <br>

## Specifications

- **Context Length:** 8,192 tokens
- **Parameters:** 2,923,466,480
- **Input:** Text, Image
- **Output:** Text

## Capabilities

- **Function Calling:** Not supported
- **Structured Output:** Not supported
- **Reasoning:** Not supported

## Prototype

```python
import requests

invoke_url = "https://ai.api.nvidia.com/v1/vlm/google/paligemma"

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

```javascript
import fetch from "node-fetch";

const invokeUrl = "https://ai.api.nvidia.com/v1/vlm/google/paligemma"

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
invoke_url='https://ai.api.nvidia.com/v1/vlm/google/paligemma'

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