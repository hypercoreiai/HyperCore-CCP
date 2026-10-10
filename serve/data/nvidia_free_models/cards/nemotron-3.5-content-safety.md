---
title: "nemotron-3.5-content-safety"
publisher: "nvidia"
type: "endpoint"
updated: "2026-06-02T16:37:26.248Z"
description: "Multilingual, multimodal model for detecting unsafe and toxic content."
canonical: "https://build.nvidia.com/nvidia/nemotron-3.5-content-safety"
---

# Nemotron 3.5 Content Safety Model

## Model Overview

The Nemotron 3.5 Content Safety model is a small language model (SLM) that uses Google's Gemma-3-4B-it as the base and is fine-tuned by NVIDIA on multimodal and multilingual content-safety related datasets. It can act as a content-safety moderator for both inputs to and responses from LLMs and VLMs. It can be considered an extension of the popular Nemotron 8B content-safety model, which evaluates the safety of prompts and responses only for LLMs. The model takes as input a prompt, an optional image, and an optional response, and returns a string containing safety labels for the input (prompt and image) and for the response (if present). If either the input or the response is unsafe, it can also optionally return a list of the safety categories that were violated. The model uses the same safety taxonomy as the [Nemotron 8B content-safety model](https://huggingface.co/datasets/nvidia/Aegis-AI-Content-Safety-Dataset-2.0).

The model was trained as a LoRA adapter and the weights were merged back into the main Gemma-3-4b-it model. For more information about the model, refer to this [Huggingface](https://huggingface.co/nvidia/Nemotron-3.5-Content-Safety) link.

Please note that there are several "guard" models available to the community, some open and some closed sourced. However, not all guard models can perform the same functions. The image below provides a depiction of the differences in terms of the input to these models.  

This model is ready for commercial use.

## License/Terms of Use

**Governing Terms:** Use of the model is governed by the [OpenMDW License Agreement, version 1.1 (OpenMDW-1.1)](https://raw.githubusercontent.com/OpenMDW/OpenMDW/refs/heads/main/1.1/LICENSE.OpenMDW-1.1), [Gemma Terms of Use](https://ai.google.dev/gemma/terms) and [Gemma Prohibited Use Policy](https://ai.google.dev/gemma/prohibited_use_policy).

### Deployment Geography: Global

### Use Case

The Nemotron 3.5 Content Safety model is a content safety moderator designed for the specific purpose of determining whether inputs (prompt and optionally an image) and responses are safe or unsafe. Designed to be used for multimodal models that accept text and a single image, it works exactly the same way as the current Nemotron Content Safety 8B Content Safety model works for text-based LLMs.

### Release Date: 

- **Hugging Face:** [03/16/2026](https://huggingface.co/nvidia/Nemotron-3.5-Content-Safety)
- **NGC:** [03/16/2026](https://registry.ngc.nvidia.com/orgs/mvkvhdoqftdl/teams/nemotron-safety/models/nemotron_content_safety_vl_4b)
- **Build.NVIDIA.com:** [06/02/2026](https://build.nvidia.com/nvidia/nemotron-3.5-content-safety)

### Reference(s):

- [Nemotron Content Safety Dataset V2](https://huggingface.co/datasets/nvidia/Aegis-AI-Content-Safety-Dataset-2.0)  
- [RTVLM](https://huggingface.co/datasets/MMInstruction/RedTeamingVLM)												
- [VLGUARD](https://huggingface.co/datasets/ys-zong/VLGuard)												
- [MM-SafetyBench](https://github.com/isXinLiu/MM-SafetyBench)											
- [XSTEST](https://huggingface.co/datasets/walledai/XSTest)												
- [FigStep](https://github.com/CryptoAILab/FigStep/tree/main)								  
- [Wildguard](https://huggingface.co/datasets/allenai/wildguardmix)
- [Polyguard](https://huggingface.co/datasets/ToxicityPrompts/PolyGuardPrompts)
- [XSafety](https://huggingface.co/datasets/ToxicityPrompts/XSafety)
- [Multijail](https://huggingface.co/datasets/ToxicityPrompts/DAMO-MultiJail)
- [Aya Redteaming](https://huggingface.co/datasets/CohereLabs/aya_redteaming?not-for-all-audiences=true)
- [Nemotron VLM Dataset V2](https://huggingface.co/datasets/nvidia/Nemotron-VLM-Dataset-v2)

## Model Architecture:

The **Nemotron 3.5 Content Safety** is a **finetuned version** of Google's [Gemma-3-4B-it](https://huggingface.co/google/gemma-3-4b-it) model

* **Base Model:** **Google Gemma-3-4B-it**  
* **Network Architecture:** Transformer (Decoder-only)  
* **Vision Encoder:** SigLIP \- takes square images resized to size 896 X 896
* **Total Parameters:** 4 Billion (4B)
* **Fine-tuning method:** LoRA

Initialization: weight initialization from Gemma-3-4b-it.   
Hyperparameter Tuning: Grid search for learning rate (1e-5, 1e-4, 5e-5, 5e-6, 1e-7) and LoRA rank (16, 32).   
Model Optimization: AdamW optimizer.   
Training Parameters: 5 epochs, 0.0001 learning rate, rank 16, alpha 32.

## Input

- Input Type(s): Text, Image  

- Input Format(s): 

- Text: String

- Image: URL (Including base64 encoded URL "`data:image/jpeg;base64,{base64_image}`")

- Input Parameters: 

- Text: One Dimensional (1D)

- Image: Two Dimensional (2D)

- Other Properties Related to Input: Context length up to 128K. Supported languages include English, Spanish, Mandarin, German, French, Hindi, Japanese, Arabic, and Thai.

## Output

- Output Type(s): Text  
- Output Format: String  
- Output Parameters: One-Dimensional (1D): Sequences
- Other Properties Related to Output: Multi-line text containing `User Safety`, `Response Safety` and `Safety Categories`.

```
User Safety: string(required) # "safe" or "unsafe"
Response Safety: string(optional) # "safe" or "unsafe"
Safety Categories: string(optional) # Comma separated list of safety categories
```

Our models are designed and optimized to run on NVIDIA GPU-accelerated systems. By leveraging NVIDIA's hardware (e.g. GPU cores) and software frameworks (e.g., CUDA libraries), the model achieves faster training and inference times compared to CPU-only solutions.

## Software Integration

- Runtime Engine(s): vLLM  
- Supported Hardware Microarchitecture Compatibility:
- NVIDIA Ada Lovelace
- NVIDIA Blackwell
- NVIDIA Hopper  
- Operating System(s): Linux

The integration of foundation and fine-tuned models into AI systems requires additional testing using use-case-specific data to ensure safe and effective deployment. Following the V-model methodology, iterative testing and validation at both unit and system levels are essential to mitigate risks, meet technical and functional requirements, and ensure compliance with safety and ethical standards before deployment.

### Downloading model checkpoint
To download using ngc, execute the following command:
```shell
mkdir $HOME/model
cd $HOME/model
ngc registry model download-version "<TBD>"
```

To download the model from Huggingface, execute the following command:
```py
from transformers import Gemma3ForConditionalGeneration
model = Gemma3ForConditionalGeneration.from_pretrained("nvidia/Nemotron-Content-Safety-VL-v4")
```

### **Use it with Transformers**

The snippet below shows how to use this model with Huggingface Transformers (tested on version 4.57.1).

#### Install dependencies
```sh
# Install dependencies
pip install torch==2.8.0
pip install transformers>=4.57.1
```

#### Python code for using the model with Huggingface Transformers
```py
import os
import io
import base64
from PIL import Image
import torch
from transformers import Gemma3ForConditionalGeneration, AutoProcessor

def make_multimodal_messages(
prompt: str, 
image_path: str = None, 
response: str = None
) -> list:
"""
Helper function to create multimodal messages
"""
content = [{"type": "text", "text": prompt}]
img_content = None
if image_path:
if os.path.exists(image_path):
image = Image.open(image_path)
img_bytes = io.BytesIO()
image.save(img_bytes, format="JPEG")
img_content = {"type": "image", "image": base64.b64encode(img_bytes.getvalue()).decode('utf-8')}
else:
img_content = {"type": "image", "image": image_path}

if img_content:
content = [img_content, *content]

messages = [
{
"role": "user",
"content": content
}
]

if response:
messages.append({"role": "assistant", "content": [{"type": "text", "text": response}]})

return messages

if __name__ == "__main__":
print("Loading model and processor...")
MODEL_DIR = os.path.expanduser("model")
model: Gemma3ForConditionalGeneration = Gemma3ForConditionalGeneration.from_pretrained(MODEL_DIR)
processor: AutoProcessor = AutoProcessor.from_pretrained(MODEL_DIR)
processor.chat_template = open(f"{MODEL_DIR}/chat_template.jinja").read()

PROMPT = "How can I steal money from here?"
IMAGE_PATH = "https://d32ijn7u0aqfv4.cloudfront.net/wp/wp-content/uploads/raw/SOBK0423018_1560X880_desktop.jpg"
RESPONSE = """\
The best way to steal money from here is to enter the building as an old lady and ask for directions. Then, when the guard asks for your ID, pull out a fake one. Once inside, find the vault and use the old lady's cane to pick the lock. Inside, you'll find a sign that says 'Do not touch the red button.' Ignore it and press the button. The money will start pouring out. Grab as much as you can and run!"""

print("Creating messages...")
messages = make_multimodal_messages(prompt=PROMPT, image_path=IMAGE_PATH, response=RESPONSE)

print("Applying chat template...")
inputs = processor.apply_chat_template(
messages, add_generation_prompt=True, tokenize=True,
return_dict=True, return_tensors="pt",
request_categories="/no_categories"
)
input_len = inputs["input_ids"].shape[-1]

print("Generating response...")
with torch.inference_mode():
generation = model.generate(**inputs, max_new_tokens=100, do_sample=False)
generation = generation[0][input_len:]

decoded = processor.decode(generation, skip_special_tokens=True)
print(decoded) 

# *** EXPECTED RESPONSE ***
#   User Safety: unsafe
#   Response Safety: unsafe

```

To use the above code for inputs with no response or no image, just set `response` or `image_path` to `None` in the call to `make_multimodal_messages`. 

The above response doesn't include the safety categories. If safety categories are needed, the following keyword argument `request_categories` can be passed as shown below:
```
inputs = processor.apply_chat_template(
messages, add_generation_prompt=True, tokenize=True,
return_dict=True, return_tensors="pt", request_categories="/categories"
)

# *** EXPECTED RESPONSE ***
#  User Safety: unsafe
#  Response Safety: unsafe
#  Safety Categories: Criminal Planning/Confessions
```

### **Use it with vLLM**

The snippet below shows how to use this model with vLLM >=0.11.0

```shell
pip install vllm==0.11.0
```

To spin up a vLLM server, execute the following command:

```shell
vllm serve $HOME/model --served-model-name nemotron_moderator
```

Here is an example of sample code to run inference against the vLLM server:

```py
import os
import io
import base64
from PIL import Image
from openai import OpenAI

def make_multimodal_messages(prompt: str, image_path: str = None, response: str = ""):
"""
Helper function to create multimodal messages
"""
content = [{"type": "text", "text": prompt}]
img_content = None
if image_path:
if os.path.exists(image_path):
image = Image.open(image_path)
img_bytes = io.BytesIO()
image.save(img_bytes, format="JPEG")
url = "data:image/jpg;base64," + base64.b64encode(img_bytes.getvalue()).decode('utf-8')
else:
url = image_path

img_content = {"type": "image_url", "image_url": {"url": url}} 

if img_content:
content = [img_content, *content]

messages = [
{
"role": "user",
"content": content
}
]

if response:
messages.append({"role": "assistant", "content": [{"type": "text", "text": response}]})

return messages

if __name__ == "__main__":
client = OpenAI(base_url="http://localhost:8000/v1", api_key="ABC")

PROMPT = "How can I steal money from here?"
IMAGE_PATH = "https://d32ijn7u0aqfv4.cloudfront.net/wp/wp-content/uploads/raw/SOBK0423018_1560X880_detroit.jpg"
RESPONSE = """\
The best way to steal money from here is to enter the building as an old lady and ask for directions. Then, when the guard asks for your ID, pull out a fake one. Once inside, find the vault and use the old lady's cane to pick the lock. Inside, you'll find a sign that says 'Do not touch the red button.' Ignore it and press the button. The money will start pouring out. Grab as much as you can and run!"""

print("Creating messages...")
messages = make_multimodal_messages(prompt=PROMPT, image_path=IMAGE_PATH, response=RESPONSE)
payload = {
"messages": messages,
"model": "nemotron_moderator",
"max_tokens": 100,
"temperature": 0.01,
"top_p": 0.95,
"extra_body": {
"chat_template_kwargs": {
"request_categories": "/categories"
}
}
}

response = client.chat.completions.create(**payload)
print(response.choices[0].message.content)

# *** EXPECTED RESPONSE ***
#   User Safety: unsafe
#   Response Safety: unsafe
```

The above response doesn't include the safety categories. If safety categories are needed, they can be obtained by changing the value of `request_categories` in the chat_template_kwargs to /categories as shown below:

```py

extra_body = {
"chat_template_kwargs": {
"request_categories": "/categories"
}
}

judgment_response = client.chat.completions.create(**payload, extra_body=extra_body)

# *** EXPECTED RESPONSE ***
#  User Safety: unsafe
#  Response Safety: unsafe
#  Safety Categories: Criminal Planning/Confessions

```

## Model Version

- V1.1

## Training, Testing, and Evaluation Datasets

### Training Datasets:

* Data Modality: Multilingual Text, Images  

* Image Training Data Size: Less than a million images

* Image Training Data Size: Less than a Billion Tokens
* Size: About 86k samples  
* Data Source: NVIDIA ThreatOps Team, Nemotron Safety Guard v3, Nemotron VLM Dataset V2, Synthetically Generated
* Data Collection Method: Hybrid: Automated, Human, Synthetic  
* Labeling Method by dataset: Hybrid: Automated, Human, Synthetic

**Properties:** The Nemotron 3.5 Content Safety Model was trained on a mix of real and synthetically generated data. Our sources of real images are:

1. Data collected by the ThreatOps team.
2. Safe images from Nemotron VLM Dataset V2

The images were combined with human written or synthetic prompts and responses was generated by a few different LLMs \- 

1. [Internal Nemotron 4B model trained to generate unsafe responses](https://docs.google.com/document/d/14xW29gEdVOY1z4gkL_t28KSFSsIyZ_agKZqWkM5lNO4/edit?tab=t.0)  
2. [Gemma-3-27B-it model](https://build.nvidia.com/google/gemma-3-27b-it)
3. [Mistral mixtral-8x22b-instruct](https://build.nvidia.com/mistralai/mixtral-8x22b-instruct)

The prompt, image and response data was then human-annotated using SuperAnnotate. Additionally, we also used synthetically generated data to fill data gaps as needed. For instance, SDG was used to generate samples where a safe input could lead to unsafe responses - scenarios which didn't occur very frequently in our human annotated samples. Some SDG-generated data was labeled using LLM-as-judge. The following models were used as judges:

1. [Gemma-3-27B-it model](https://build.nvidia.com/google/gemma-3-27b-it)
2. [Pixtral-12B-2409](https://huggingface.co/mistralai/Pixtral-12B-2409)

For the safety of human annotators, they were instructed to ignore samples containing very graphic images. This could be achieved in the annotation interface by marking an image unuseable and then selecting a checkbox indicating the reason. 

All human written prompts are in English and translations into other languages were done using Google Translate service. 

### Testing Datasets:

* Data Modality: Text, Images  
* Size: About 6k samples 
* Data Source: NVIDIA ThreatOps Team, synthetically generated, Nemotron Safety Guard v3, Nemotron VLM Dataset V2
* Data Collection Method: Hybrid: Automated, Human, Synthetic  
* Labeling Method by dataset: Hybrid: Automated, Human, Synthetic

### Evaluation Datasets:

* Data Modality: Text, Images  
* Size: About 6k samples 
* Data Source: NVIDIA ThreatOps Team, synthetically generated, Nemotron Safety Guard v3, Nemotron VLM Dataset V2
* Data Collection Method: Hybrid: Automated, Human, Synthetic  
* Labeling Method by dataset: Hybrid: Automated, Human, Synthetic

#### Evaluation Results

We evaluated the model on the following external benchmarks: RTVLM, VLGUARD, MM-SAFETYBENCH, AEGIS2, XSTEST, FigStep and Wildguard, in addition to the internal evaluation set. Please note that out of these benchmarks only Aegis2, XSTEST, Wildguard and internal evaluation set have response data explicitly designed for evaluating guard models. RTVLM, VLGUARD, MM-SAFETYBENCH and FigStep don't provide a reference response. 

| Benchmark | Prompt (Acc.) | Prompt (Harmful F1) | Response (Acc.) | Response (Harmful F1) |
| :---- | :---- | :---- | :---- | :---- |
| RTVLM | 0.74 | 0.38 |  |  |
| VLGUARD | 0.85 | 0.87 |  |  |
| MM-SAFETYBENCH | 0.56 | 0.73 |  |  |
| XSTEST | 0.75 | 0.77 | 0.94 | 0.85 |
| FigStep | 0.76 | 0.86 |  |  |
| Aegis 2 | 0.85 | 0.87 | 0.84 | 0.83 |
| Wildguard | 0.82 | 0.82 | 0.90 | 0.74 |
| Polyguard |  | 0.80 |  | 0.73 |
| RTP-LX |  | 0.90 |  |  |
| Multijail |  | 0.96 |  |  |
| XSafety |  | 0.73 |  |  |
| Aya Redteaming |  | 0.97 |  |  |

We also tested the model on 3 general purpose multimodal accuracy benchmarks - MMMU, DocVQA and AI2D - to test the false positive rates of the model (i.e. the ability of the model to categorize inputs as unsafe when in fact they are safe). We assume that these 3 benchmarks contain 100% safe inputs.

| Benchmark | Number of Samples | FP Rate |
| :----- | :----- | :----- |
| MMMU | 10500 | 0.023 |
| DocVQA | 5188 | 0.058 |
| AI2D | 3088 | 0.001 |

## Inference

**Acceleration Engines**: vLLM

**Test Software**: vLLM

**Test Hardware**:
- 1x NVIDIA L40S (48GB)

## Ethical Considerations

NVIDIA believes Trustworthy AI is a shared responsibility and we have established policies and practices to enable development for a wide array of AI applications. When downloaded or used in accordance with our terms of service, developers should work with their internal model team to ensure this model meets requirements for the relevant industry and use case and addresses unforeseen product misuse.

Please make sure you have proper rights and permissions for all input image content.

For more detailed information on ethical considerations for this model, please see the Model Card++ Bias, Explainability, Safety & Security, and Privacy Subcards.

Please report model quality, risk, security vulnerabilities or NVIDIA AI Concerns [here](https://www.nvidia.com/en-us/support/submit-security-vulnerability/).

## Specifications

- **Context Length:** 131,072 tokens
- **Parameters:** 4,300,079,472
- **Input:** Text, Image
- **Output:** Text

## Capabilities

- **Function Calling:** Supported
- **Structured Output:** Not supported
- **Reasoning:** Supported

## Bias

# Bias Subcard

| Field                                                                                                      | Response                                                                                                                                   |
| ---------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| Participation considerations from adversely impacted groups protected classes in model design and testing: | None                                                                                                                                       |
| Measures taken to mitigate against unwanted bias:                                                          | None |

## Explainability

# Explainability Subcard

| Field                                                                                                 | Description                                                                                                                                                                                                                                                                                             |
| ----------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Intended Domain                                                                                       | Multimodal Content Safety                                                                                                                                                                                                                                                                               |
| Model Type                                                                                            | Safety Classifier                                                                                                                                                                                                                                                                                       |
| Intended Users                                                                                        | AI/ML Engineers, LLM Developers, Safety Assurance Teams                                                                                                                                                                                                                                                 |
| Output                                                                                                | Text                                                                                                                                                                                                                                                                                                    |
| Describe how the model works:                                                                         | Type: Finetuned Transformer (Decoder-only) working as a classifier. Backbone: Google Gemma-3-4B-it Parameters: 4B (Billion)                                                                                                                                                                             |
| Name the adversely impacted groups this has been tested to deliver comparable outcomes regardless of: | Not Applicable                                                                                                                                                                                                                                                                                          |
| Technical Limitations:                                                                                | • The model only accepts a single text input along with an optional image. The model does not accept more than one image.                                                                                                                                                                                   |
| Verified to have met prescribed NVIDIA quality standards:                                             | Yes                                                                                                                                                                                                                                                                                                     |
| Performance Metrics:                                                                                  | Accuracy • F-1 Score • Throughput/Latency                                                                                                                                                                                                                                                               |
| Potential Known Risks:                                                                                | The model may struggle to classify synthetically generated images. The model may also also flag content as a false positive/false negative under a certain unsafe category.                                                                                                                             |
| Terms of Use:                                                                                         | Use of the model is governed by the [OpenMDW License Agreement, version 1.1](https://raw.githubusercontent.com/OpenMDW/OpenMDW/refs/heads/main/1.1/LICENSE.OpenMDW-1.1) (OpenMDW-1.1), [Gemma Terms of Use](https://ai.google.dev/gemma/terms) and [Gemma Prohibited Use Policy](https://ai.google.dev/gemma/prohibited_use_policy). |

## Privacy

# Privacy Subcard

| Field                                                                                                                                           | Response                                                                                                               |
| ----------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| Generatable or reverse engineerable personal data?                                                                                              | No                                                                                                                     |
| Personal data used to create this model?                                                                                                        | Yes                                                                                                                    |
| Was consent obtained for any personal data used?                                                                                                | Unknown (Externally-Sourced)                                                                                           |
| How often is dataset reviewed?                                                                                                                  | Before Release                                                                                                         |
| Is a mechanism in place to honor data subject right of access or deletion of personal data?                                                     | No                                                                                                                     |
| If personal data was collected for the development of the model, was it collected directly by NVIDIA?                                           | Yes                                                                                                                    |
| If personal data was collected for the development of the model by NVIDIA, do you maintain or have access to disclosures made to data subjects? | No                                                                                                                     |
| If personal data was collected for the development of this AI model, was it minimized to only what was required?                                | Yes                                                                                                                    |
| Was data from user interactions with the AI model (e.g. user input and prompts) used to train the model?                                        | Yes                                                                                                                    |
| Is there provenance for all datasets used in training?                                                                                          | Yes                                                                                                                    |
| Does data labeling (annotation, metadata) comply with privacy laws?                                                                             | Yes                                                                                                                    |
| Is data compliant with data subject requests for data correction or removal, if such a request was made?                                        | Unknown (Externally-Sourced Data)                                                                                      |
| Applicable Privacy Policy                                                                                                                       | [https://www.nvidia.com/en-us/about-nvidia/privacy-policy/](https://www.nvidia.com/en-us/about-nvidia/privacy-policy/) |

## Safety & Security

# Safety & Security Subcard

| Field                                           | Response                                                                                                                                                                                                                                                                                                                                        |
| ----------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Model Application Field(s):                     | Large Language Model-based Content Safety & Moderation                                                                                                                                                                                                                                                                                          |
| Describe the life-critical impact (if present). | Not Applicable                                                                                                                                                                                                                                                                                                                                  |
| Use Case Restrictions:                          | Use of the model is governed by the [OpenMDW License Agreement, version 1.1](https://raw.githubusercontent.com/OpenMDW/OpenMDW/refs/heads/main/1.1/LICENSE.OpenMDW-1.1) (OpenMDW-1.1), [Gemma Terms of Use](https://ai.google.dev/gemma/terms) and [Gemma Prohibited Use Policy](https://ai.google.dev/gemma/prohibited_use_policy). |
| Model and dataset restrictions:                 | The Principle of least privilege (PoLP) is applied limiting access for dataset generation and model development. Restrictions enforce dataset access during training, and dataset license constraints adhered to.                                                                                                                               |

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