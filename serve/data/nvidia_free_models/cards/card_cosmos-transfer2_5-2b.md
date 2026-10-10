:false}]
50:T28ad,# Model Overview

## Description
**Cosmos-Transfer2.5**: A family of highly performant pre-trained world foundation models purpose-built for generating physics-aware images, videos and world states aligned with the input control conditions.

Cosmos-Transfer2.5 diffusion models are a collection of diffusion based world foundation models that generate dynamic, high quality images and videos from text, image, or control video inputs. It can serve as the building block for various applications or research that are related to world generation. This model is ready for commercial/non-commercial use.

**Model Developer**: NVIDIA

## Model Versions

The Cosmos-Transfer2.5 diffusion-based model family includes the following models:

- [Cosmos-Transfer2.5-2B](https://huggingface.co/nvidia/Cosmos-Transfer2.5-2B)
  - Given a text prompt and one or multiple (up to four) control input videos -- Canny edge, blurred RGB, segmentation mask, and depth map  -- predict a photorealistic output video by leveraging guidance in the control input videos. Automatic extraction is available for edge and blur controls when only an RGB video is provided.

The model produces 720P video with 16FPS

- [Cosmos-Transfer2.5-2B/ Auto / Multiview](https://huggingface.co/nvidia/Cosmos-Transfer2.5-2B)
  - Given a text prompt and 7 "world scenario" control input videos (from front center, front left, front right, rear left, rear right, rear tele, front tele cameras on an autonomous vehicle), generate 29 view-consistent frames for each of the 7 cameras at resolution of 1280×720 (text-to-world). The model can additionally be conditioned by 1 or 2 initial latent frames using reference videos of the 7 cameras (image-to-world, video-to-world).

The model has been trained on 720p video at 10FPS.
 
### License
The trial service is governed by the [NVIDIA API Trial Terms of Service](https://assets.ngc.nvidia.com/products/api-catalog/legal/NVIDIA%20API%20Trial%20Terms%20of%20Service.pdf); and use of the model is governed by the  [NVIDIA Open Model License](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license). Additional Information: [Apache License 2.0](https://huggingface.co/Qwen/Qwen3Guard-Gen-0.6B/blob/main/LICENSE). 


### Deployment Geography:

Global

### Use Case:

Physical AI: encompassing robotics, autonomous vehicles (AV), and more.

### Release Date:

Github [10/06/2025] via https://github.com/nvidia-cosmos/cosmos-transfer2.5

HuggingFace [10/06/2025] via https://huggingface.co/collections/nvidia/cosmos-transfer25-6864569b8acaf966a107bfe3

## Model Architecture
Cosmos-Transfer2.5-2B is a diffusion transformer model designed for video denoising in the latent space, modulated by multiple control branches. 

The diffusion transformer network (“the base model”) is composed of interleaved self-attention, cross-attention and feedforward layers as its building blocks. The cross-attention layers allow the model to condition on input text throughout the denoising process. Before each layer, adaptive layer normalization is applied to embed the time information for denoising. When image or video is provided as input, their latent frames are concatenated with the generated frames along the temporal dimension. Augment noise is added to conditional latent frames to bridge the training and inference gap.

The control branch is formed by replicating a few transformer blocks of the base model. It processes the control input video to extract control signals, which are then injected into the corresponding transformer blocks of the base model, guiding the denoising process with structured control. When multiple control input videos are provided, each is processed by a dedicated control branch to extract modality-specific control signals. These control signals are then combined with spatial-temporal weight maps, and injected into the corresponding transformer blocks in the base model.

**This model was developed based on:**  [Cosmos-Predict2.5](https://huggingface.co/nvidia/Cosmos-Predict2.5-2B)

**Number of model parameters:** 2,358,047,744 

## Input/Output Specifications

* **Input**

  * **Input Type(s)**:  Text+Video
  * **Input Format(s)**:
    * Text: String
    * Control Input Video: mp4
  * **Input Parameters**:
    * Text: One-dimensional (1D)
    * Control Input Video: Three-dimensional (3D)
  * **Other Properties Related to Input**:
    * The input text string should contain fewer than 300 words and should provide descriptive content for world generation, such as a scene description, key objects or characters, background, and any specific actions or motions to be depicted within the 5-second duration.
    * The model supports control input videos of varying lengths, but a length which is multiples of 93 frames (e.g., 93, 186, or 279 frames) performs the best.
    * The model supports four types of control input videos: blurred video, Canny edge video, depth map video, and segmentation mask video. When multiple control inputs are provided, they must be derived from the same source video, representing different modalities of the same content while maintaining identical spatio-temporal dimensions.
    * The control input video should have a spatial resolution of 1280×720 for the 720P model. 

* **Output**
  * **Output Type(s)**: Video
  * **Output Format(s)**: mp4
  * **Output Parameters**: Three-dimensional (3D)
  * **Other Properties Related to Output**: The output video is of the same temporal length and spatial resolution of the control input video. The frame rate of the output video is determined by the model variant (i.e., 16 FPS)

The video content visualizes the input text description as a short animated scene, capturing key elements within the specified time constraints.

Our AI models are designed and/or optimized to run on NVIDIA GPU-accelerated systems. By leveraging NVIDIA's hardware (e.g. GPU cores) and software frameworks (e.g., CUDA libraries), the model achieves faster training and inference times compared to CPU-only solutions.

## Software Integration
**Runtime Engine(s):**
* [Cosmos-Transfer2.5](https://github.com/nvidia-cosmos/cosmos-transfer2.5)

**Supported Hardware Microarchitecture Compatibility:**

* NVIDIA Ampere
* NVIDIA Blackwell
* NVIDIA Hopper

**Note**: Only BF16 precision is tested. Other precisions like FP16 or FP32 are not officially supported.

The integration of foundation and fine-tuned models into AI systems requires additional testing using use-case-specific data to ensure safe and effective deployment. Following the V-model methodology, iterative testing and validation at both unit and system levels are essential to mitigate risks, meet technical and functional requirements, and ensure compliance with safety and ethical standards before deployment.

## Training Dataset:

**Data Modality** <br>
* [Image] <br>
* [Text] <br>
* [Video] <br>

**Data Collection Method by dataset** <br>
* [Automated] <br>

**Labeling Method by dataset** <br>
* [Hybrid: Human, Automated] <br>

### Testing Dataset:

**Data Collection Method by dataset** <br>
* [Automated] <br>

**Labeling Method by dataset** <br>
* [Hybrid: Human, Automated] <br>

# Evaluation

Please see our [technical paper](https://research.nvidia.com/publication/2025-09_world-simulation-video-foundation-models-physical-ai) for detailed evaluations of the base model. The control models are built upon the base foundation model.

**Data Collection Method**:
* Automated

**Labeling Method**:
* Hybrid:  Human,Automated

**System Requirements and Performance:**
This model requires 65.4 GB of GPU VRAM.

The following table shows generation times across different NVIDIA GPU hardware for single-GPU inference:

| GPU Hardware | Cosmos-Transfer2-2B (Segmentation) |
|--------------|---------------|
| NVIDIA B200 | 285.83 sec |
| NVIDIA H100 NVL | 719.4 sec |
| NVIDIA H100 PCIe | 870.3 sec |
| NVIDIA H20 | 2326.6 sec |

**Operating System(s):**
* Linux (We have not tested on other operating systems.)

**Note**: Only BF16 precision is tested. Other precisions like FP16 or FP32 are not officially supported.

# Usage

* See [Cosmos-Transfer2.5](https://github.com/nvidia-cosmos/cosmos-transfer2.5) for details.

## Limitations
Despite various improvements in world generation for Physical AI, Cosmos-Transfer2.5 models still face technical and application limitations for world-to-world generation. In particular, they struggle to generate long, high-resolution videos without artifacts. Common issues include temporal inconsistency, camera and object motion instability, and imprecise interactions. The models may inaccurately represent 3D space, 4D space-time, or physical laws in the generated videos, leading to artifacts such as disappearing or morphing objects, unrealistic interactions, and implausible motions. As a result, applying these models for applications that require simulating physical law-grounded environments or complex multi-agent dynamics remains challenging.

## Inference:
**Acceleration Engine**: [PyTorch](https://pytorch.org/), [Transformer Engine](https://github.com/NVIDIA/TransformerEngine)

**Test Hardware:** H100, A100, GB200

## Ethical Considerations
NVIDIA believes Trustworthy AI is a shared responsibility and we have established policies and practices to enable development for a wide array of AI applications.  When downloaded or used in accordance with our terms of service, developers should work with their internal model team to ensure this model meets requirements for the relevant industry and use case and addresses unforeseen product misuse. Please make sure you have proper rights and permissions for all input image and video content; if image or video includes people, personal health information, or intellectual property, the image or video generated will not blur or maintain proportions of image subjects included.

Users are responsible for model inputs and outputs. Users are responsible for ensuring safe integration of this model, including implementing guardrails as well as other safety mechanisms, prior to deployment.

For more detailed information on ethical considerations for this model, please see the subcards of Explainability, Bias, Safety & Security, and Privacy below. Please report model quality, risk, security vulnerabilities or NVIDIA AI Concerns [here](https://www.nvidia.com/en-us/support/submit-security-vulnerability/).51:T986,### Explainability

Field                                                                                                  |  Response
:------------------------------------------------------------------------------------------------------|:---------------------------------------------------------------------------------
Intended Application & Domain:                                                                   |  World Generation
Model Type:                                                                                            |  Transformer
Intended Users:                                                                                        |  Physical AI developers
Output:                                                                                                |  Videos
Describe how the model works:                                                                          |  Generates videos based on text and video inputs
Technical Limitations:                                                                                 |  The model may not follow the video input accurately.
Verified to have met prescribed NVIDIA quality standards:  |  Yes
Performance Metrics:                                                                                   |  Quantitative and Qualitative Evaluation. We use PAIBench-Transfer, a benchmark dataset containing 600 videos spanning diverse domains such as driving and robotics. The evaluation is structured around two key dimensions: adherence to control inputs (how well the generated video follows the provided conditions) and overall video quality (measuring realism and consistency).
Potential Known Risks:                                                                                 |  The model's output can generate all forms of videos, including what may be considered toxic, offensive, or indecent.
Licensing:                                                                                             |  * The trial service is governed by the [NVIDIA API Trial Terms of Service](https://assets.ngc.nvidia.com/products/api-catalog/legal/NVIDIA%20API%20Trial%20Terms%20of%20Service.pdf); and use of the model is governed by the  [NVIDIA Open Model License](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license). Additional Information: [Apache License 2.0](https://huggingface.co/Qwen/Qwen3Guard-Gen-0.6B/blob/main/LICENSE).52:T57c,### Privacy

Field                                                                                                                              |  Response
:----------------------------------------------------------------------------------------------------------------------------------|:-----------------------------------------------
Generatable or reverse engineerable personal data?                                                |  No
Personal data used to create this model?                                                     |  None Known
Was consent obtained for any personal data used?                                                                                             |  None Known
How often is dataset reviewed?                                                                                                     |  Before Release
Is there provenance for all datasets used in training?                                                                                |  Yes
Does data labeling (annotation, metadata) comply with privacy laws?                                                                |  Yes
Is data compliant with data subject requests for data correction or removal, if such a request was made?                           |  No, not possible with externally-sourced data.
Applicable Privacy Policy        | https://www.nvidia.com/en-us/about-nvidia/privacy-policy/53:T490,### Safety And Security

Field                                               |  Response
:---------------------------------------------------|:----------------------------------
Model Application(s):                               |  World Generation
Describe the life critical impact (if present).   |  None Known
Use Case Restrictions:                              |  * Abide by the [NVIDIA API Trial Terms of Service](https://assets.ngc.nvidia.com/products/api-catalog/legal/NVIDIA%20API%20Trial%20Terms%20of%20Service.pdf); and use of the model is governed by the [NVIDIA Open Model License](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license). Additional Information: [Apache License 2.0](https://huggingface.co/Qwen/Qwen3Guard-Gen-0.6B/blob/main/LICENSE).. 
Model and dataset restrictions:            |  The Principle of least privilege (PoLP) is applied limiting access for dataset generation and model development.  Restrictions enforce dataset access during training, and dataset license constraints adhered to. Model checkpoints are made available on Hugging Face, and may become available on cloud providers' model catalog.4a:[["$","div",".3",{"className":"relative","children":[["$","div",null,{"className":"relative flex min-h-[194px] w-full flex-col overflow-hidden p-md sm:p-ml bg-manitoulinLightBlack","children":[["$","$L4d",null,{"alt":"","className":"object-cover object-center !left-1/2 z-10 !w-1/2 brightness-20 lg:brightness-75","fill":true,"priority":true,"src":"https://assets.ngc.nvidia.com/products/api-catalog/images/cosmos-transfer2_5-2b.jpg","style":{"maskImage":"linear-gradient(to left, rgba(0,0,0,1), rgba(0,0,0,0))"}}],["$","div",null,{"className":"z-30 mx-auto flex w-full max-w-screen-xl min-w-0 flex-1 flex-col items-start justify-between gap-md lg:flex-row lg:gap-ml","children":["$","section",null,{"aria-describedby":"resource-description","aria-labelledby":"resource-name","className":"flex w-full min-w-0 flex-col lg:flex-1","children":["$","div",null,{"className":"flex flex-col gap-1.5 whitespace-pre-wrap","children":[["$","$L4e",null,{"className":"w-fit text-ml text-n300 lowercase hover:text-n050","href":"/nvidia","children":"NVIDIA"}],["$","div",null,{"className":"flex flex-col items-start gap-3 lg:flex-row lg:items-center","children":[["$","h1",null,{"className":"max-w-full text-lg leading-heading font-medium break-words text-primary","data-testid":"resource-name","id":"resource-name","children":"cosmos-transfer2.5-2b"}],["$","$L4f",null,{"artifact":{"artifactType":"ENDPOINT","name":"cosmos-transfer2_5-2b","displayName":"cosmos-transfer2.5-2b","publisher":"nvidia","shortDescription":"Generates physics-aware video world states for physical AI development using text prompts and multiple spatial control inputs derived from real-world data or simulation.","logo":"https://assets.ngc.nvidia.com/products/api-catalog/images/cosmos-transfer2_5-2b.jpg","labels":["Autonomous Vehicles","Physical AI","nimType:endpoint:nim_type_preview","robotics","usecase:endpoint:usecase_sdg","video-to-world"],"attributes":[{"key":"AVAILABLE","value":"false"},{"key":"PREVIEW","value":"true"},{"key":"last_month_api_invocation_count","value":"0"},{"key":"last_month_download_count","value":"0"}],"updatedDate":"2026-02-26T00:09:28.953Z","bias":"### Bias\n\nField                                                                                               |  Response\n:---------------------------------------------------------------------------------------------------|:---------------\nParticipation considerations from adversely impacted groups [protected classes](https://calcivilrights.ca.gov/disputeresolution/protected-characteristics/) in model design and testing:  |  None\nMeasures taken to mitigate against unwanted bias:                                                   |  None","canGuestDownload":true,"createdDate":"2026-02-26T00:09:28.953Z","description":"$50","explainability":"$51","isPublic":true,"isReadOnly":true,"orgName":"qc69jvmznzxy","privacy":"$52","safetyAndSecurity":"$53"}}],"$undefined"]}],"$L54","$L55"]}]}]}],"$L56"]}],"$L57"]}]]
59:T3958,# NVIDIA Cosmos

Cosmos is NVIDIA’s World Foundation Model Development Platform that provides the tools to either finetune existing models or train new models from scratch.

## Cosmos Model Family

Cosmos World Foundation Models (WFM) are a family of highly-performant pre-trained models purpose-built for generating physics-aware videos used for training robots. With Cosmos, developers can simulate a world in which robots function and train them to act and react responsibly in the real world before actual deployment.

Cosmos WFMs currently contain four main types of models: NeMo Curator, Cosmos Tokenizer, Cosmos Guardrail, and Cosmos World Foundation Model. NeMo Curator is a video curation pipeline that takes raw video frames, splits them into meaningful segments, and annotates them with semantic tags, object labels, and scene descriptions. The annotated images are then fed into the Cosmos Tokenizer, which produces a sequence of tokens. This step reduces data dimensionality enabling Cosmos World Foundation Model to effectively handle large or complex inputs for training. Cosmos WFM then consumes the curated/annotated video segments and learns the underlying physics and visual dynamics from real world data. When queried, Cosmos WFM outputs new token sequences that are then decoded back into high-resolution and physically realistic synthetic videos. Cosmos WFMs are pretrained on large-scale video datasets to expose them to a broad range of visual experiences, enabling them to serve as generalists. To construct a specialized WFM developers are expected to fine-tune Cosmos WFM using additional data collected from a specific use case. This additional data will help adapt Cosmos WFM to this intended use case, ensuring it can perform optimally under real-world conditions.

## Governing Terms/Terms of Use

All Cosmos WFMs are deployed globally and are covered under NVIDIA’s [Open Model License Agreement](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license/). This license agreement confirms that:

* Models are commercially usable.
* You are free to create and distribute derivative models.
* NVIDIA does not claim ownership of any outputs generated using the models or derivative models.

If users bypass, disable, reduce the efficacy of, or circumvent any technical limitation, safety guardrail or associated safety guardrail hyperparameter, encryption, security, digital rights management, or authentication mechanism contained in the Model, the user’s rights under the NVIDIA Open Model License Agreement will automatically terminate. If users are interested in a custom license, they may contact cosmos-license@nvidia.com.

## Specific Risk Areas and Mitigations

WFMs can produce unrealistic outputs, generate unsafe content or may inadvertently amplify societal biases reflected in their training data. Collectively, these risks underscore the need for technical measures to mitigate risk and careful evaluation before leveraging Cosmos WFM in real-world applications.

### **Cosmos Guardrail**


For the safe use of our world foundation models, we develop a comprehensive guardrail system. Cosmos Guardrail consists of two stages: the pre-Guard and the post-Guard stage. The pre-Guard stage leverages [Aegis-AI-Content-Safety-LlamaGuard-LLM-Defensive-1.0](https://huggingface.co/nvidia/Aegis-AI-Content-Safety-LlamaGuard-Defensive-1.0), which is a fine-tuned version of [Llama-Guard](https://ai.meta.com/research/publications/llama-guard-llm-based-input-output-safeguard-for-human-ai-conversations/) trained on [NVIDIA’s Aegis Content Safety Dataset](https://huggingface.co/datasets/nvidia/Aegis-AI-Content-Safety-Dataset-1.0) and a blocklist filter that performs a lemmatized and whole-word keyword search to block harmful prompts. It then further sanitizes the user prompt by processing it through the Cosmos  Text2World Prompt Upsampler. The post-Guard stage blocks harmful visual outputs using a video content safety classifier and a face blur filter.
![](https://assets.ngc.nvidia.com/products/api-catalog/cosmos/system-card-diagram.jpg)


Cosmos pre-Guard first uses a simple blocklist-based checker for unsafe keyword detection. This is designed to block explicitly harmful generations by doing a keyword search on the prompt against a hard-coded blocklist of a large corpus of explicit and objectionable words. Input words are lemmatized using [WordNetLemmatizer](https://www.nltk.org/api/nltk.stem.WordNetLemmatizer.html?highlight=wordnet), a tool that uses a lexical database of the English language to extract the root word from its variants. These lemmatized words are then compared to the words in the hard-coded blocklist, and the entire prompt is rejected if any profanity is found.

As the second line of defense, Cosmos pre-Guard uses [Aegis-AI-Content-Safety-LlamaGuard-LLM-Defensive-1.0](https://huggingface.co/nvidia/Aegis-AI-Content-Safety-LlamaGuard-Defensive-1.0) to detect unsafe content in semantically-complex prompts. Aegis is able to classify prompts into13 critical safety risk categories: violence, sexual, criminal planning, weapons, substance abuse, suicide, child sexual abuse material, hatred, harassment, threat, and profanity. If the input prompt is categorized as unsafe by this prompt filter, the video is not generated, and an error message is displayed. Any prompt that does not fall into the above categories is considered safe from the prompt-filtering standpoint.

Prior to passing the prompt to the world generation models, the prompt is further augmented and indirectly sanitized via the Cosmos Text2World Prompt Upsampler. This is a bespoke model that not only compensates for the lack of specificity in the prompt but also steers clear of objectionable denotations or connotations.

Cosmos post-Guard is a vision-domain guardrail that is activated after the world content has been generated and comprises a video content safety filter and a face blur filter. Our video content safety filter used in the post-Guard stage has been trained on carefully-curated datasets and evaluated on human\- annotated datasets created by Cosmos Red Team. To calibrate model outputs for the intended use case in the robotics and autonomous vehicle domains, we also automatically detect and blur all faces. We use RetinaFace, a state-of-the-art face detection model, to identify facial regions with high confidence scores. For any generated face region larger than 20 × 20 pixels, we apply pixelation to obscure features while preserving the overall scene composition.  Note that by blurring all generated human faces in the video, potential biases based on age, gender, race and ethnicity in the output video are reduced.

### **Balanced Datasets**


Cosmos WFM is trained using both proprietary and publicly available video datasets. We curated about 100M clips of videos ranging from 2 to 60 seconds from a 20M hour-long video collection. For each clip, we use a VLM ([13B-parameter VILA model](https://huggingface.co/Efficient-Large-Model/VILA-13b)) to provide a video caption per 256 frames. As our goal is to create a VLM that is able to generate physically realistic videos, we use the video captions to curate the training dataset to cover various physical applications:

* Driving (11%),
* Hand motion and object manipulation (16%),
* Human motion and activity (10%),
* Spatial awareness and navigation (16%),
* First person point-of-view (8%),
* Nature dynamics (20%),
* Dynamic camera movements (8%),
* Synthetically rendered (4%)
* Others (7%)

To ensure effective distribution of the dataset we employ a taxonomy-based classifier to label video types and prune those that introduce unrealistic behaviors, such as purely animated or abstract patterns. Certain categories relevant to world foundation models (like human actions and interactions) are upsampled, while less critical ones (such as landscapes) are downsampled.

A significant amount of the initial video data is either semantically redundant or contains different visual effects, which may induce unwanted artifacts in the generated videos if not appropriately handled. We therefore designed a sequence of data processing steps to find the most valuable parts of the raw videos for training. Shot boundary detection identifies where one shot ends and another begins, after which all footage is re-encoded into a uniform, high-quality MP4 format to ensure consistent loading and reduce codec discrepancies. The resulting video segments undergo several filtering processes. Motion filtering removes clips that are static or excessively shaky, and tags the remaining clips with camera motion types to enhance training signals. Visual quality filtering uses a video assessment model trained on [DOVER](https://github.com/VQAssessment/DOVER) to discard the bottom 15% in perceptual quality and applies an image aesthetic model exclude footage that is aesthetically poor. A deduplication step uses [InternVideo2](https://arxiv.org/abs/2403.15377) embeddings to identify near-duplicate content and preserves the highest-resolution version for minimal quality loss.

## **Evaluation Methods**

We employ a dedicated red team to actively probe the system using both standard and adversarial examples that are collected in an internal attack prompt dataset. These video outputs are annotated by a team of expert annotators, who were specially trained for our task, to classify the generated video on a scale of 1-5 on multiple categories of harm related to the safety taxonomy. These annotations also specify the start and end-frames where the unsafe content is detected, thereby generating high-quality annotations. The red team also probed each guardrail component independently with targeted examples to identify weaknesses and improve performance in edge cases. As of the date of publication, the red team has tested and annotated over10, 000 distinct prompt-video pairs that were carefully crafted to cover a broad range of unsafe content. We separate out our safety testing into 4 categories:

**Targeted unsafe testing**

Targeted unsafe testing involves generating a corpus of manually curated unsafe prompts. These are intended to emulate common unsafe interactions that are performed by non-technical users of the system with basic or limited knowledge of multimodal AI attack vectors. These have a high likelihood of being caught by prompt filters, e.g. “Video of a naked person”.

**Adversarial Attack Testing**

Adversarial attack testing involves generating a corpus of unsafe prompts following the styles of AI attack published in literature. This type of testing will also leverage some (not all) of the prompts from content safety datasets like Aegis and automation tooling like [Garak](https://github.com/NVIDIA/garak).

**Prompt Upsampler Toxicity**

Prompt Upsampler Toxicity refers to a phenomenon where automated methods are used to “upsample” or expand a prompt by adding detail or context and inadvertently introduce unsafe content. Monitoring and mitigating Prompt Upsampler Toxicity ensures that content moderation systems remain effective throughout the entire generation pipeline, preserving user trust and upholding ethical standards.

**Accidental Mishap Testing**

Accidental mishap testing involves emulating the experience of a user prompting the model with a benign prompt, and getting unsafe content in return. This is the hardest category to test, since it does not have a fixed method or protocol for generation.

## Deployment

Cosmos WFM is released under an open, permissive NVIDIA license, allowing users to download the model weights and run it on their own hardware. This means that developers can integrate the WFM into their existing workflows without dependency on external APIs. They can also tailor the model to specific domain needs, retrain or fine-tune the model with their private data. This approach fosters innovation especially for under-resourced stakeholders that cannot rely on paid services.

Once downloaded, NVIDIA has less visibility into how or where Cosmos is deployed, reducing opportunities to enforce content policies or guardrails. Downloadable models grant complete control to users, but also transfer responsibility to the users for preventing misuse, and implementing safety mechanisms, such as watermarking and content moderation. Watermarking in the context of WFMs is crucial to ensure traceability, and user awareness that generated content might not be authentic. Watermarks allow viewers and downstream users to identify AI-generated or AI-manipulated videos, helping prevent misinformation and misuse. Even though watermarking is typically the responsibility of the user, we still encourage the use of open-source libraries for watermarking by downstream users of Cosmos WFM. NVIDIA has actively promoted watermarking and has worked in consortiums and standards bodies to define common protocols for watermarking synthetic media.

Cosmos WFM is also hosted by NVIDIA at the NVIDIA API Catalog (build.nvidia.com) and accessible via a web-based user interface. In this case, NVIDIA manages infrastructure, updates, and safety features. End users with minimal machine learning expertise can harness powerful WFMs without worrying about infrastructure or setup. Hosted models give NVIDIA more oversight and moderation capabilities, for example:

* Know Your Customer (KYC) and account verification ensures that users are who they claim to be, discouraging malicious actors and fostering accountability.
* Usage monitoring securely records user activity and flags suspicious patterns, enabling traceability and compliance checks while helping identify harmful behavior.
* Rate limiting prevents spamming and large-scale misuse, balancing computational resources and protecting against abuse or overwhelming the system.
* Human review protocols provide an escalation path for questionable outputs or flagged user accounts. This is a dedicated moderation team for final decisions on content removals, user bans, or investigations.

## Ethical Considerations

NVIDIA believes Trustworthy AI is a shared responsibility and we have established policies and practices to enable development for a wide array of AI applications. When downloaded or used in accordance with our terms of service, developers should work with their internal supporting team to ensure this system meets requirements for the relevant industry and use case and addresses unforeseen product misuse.

## Getting Help/Support

Please report security vulnerabilities or NVIDIA AI Concerns [here](https://www.nvidia.com/en-us/support/submit-security-vulnerability/).
4b:["$","$L58",null,{"spec":{"openAPISpec":{"openapi":"3.1.0","info":{"contact":{"name":"NVIDIA Support","url":"https://help.nvidia.com/"},"description":"The NVIDIA NIM REST API. Please see https://docs.api.nvidia.com/nim for more details.","termsOfService":"https://nvidia.com/legal/terms-of-use","license":{"name":"TODO","url":"https://todo"},"title":"NVIDIA NIM API for nvidia/cosmos-transfer1-7b","version":"1.0.0"},"servers":[{"url":"https://ai.api.nvidia.com/v1/"}],"paths":{"/cosmos/nvidia/cosmos-transfer1-7b":{"post":{"summary":" Infer","operationId":"_infer_v1_infer_post","requestBody":{"content":{"application/json":{"schema":{"$ref":"#/components/schemas/Transfer1Request"}}},"required":true},"responses":{"200":{"description":"Successful Response","content":{"application/json":{"schema":{"$ref":"#/components/schemas/Transfer1Response"}}}},"422":{"description":"Validation Error","content":{"application/json":{"schema":{"$ref":"#/components/schemas/HTTPValidationError"}}}}}}}},"components":{"schemas":{"ControlInput":{"properties":{"control_weight":{"type":"number","maximum":1,"minimum":0,"title":"Control Weight","description":"Weight for the control input","default":0.5},"control_weight_prompt":{"anyOf":[{"type":"string"},{"type":"null"}],"title":"Control Weight Prompt","description":"Optional prompt to guide the control input"},"input_control":{"anyOf":[{"type":"string"},{"type":"null"}],"title":"Input Control","description":"Optional video input for control, public URL or base64 encoded video"},"input_control_prompt":{"anyOf":[{"type":"string"},{"type":"null"}],"title":"Input Control Prompt","description":"Optional prompt to guide the input control generation, only used for 'seg' control input"}},"additionalProperties":false,"type":"object","title":"ControlInput"},"HTTPValidationError":{"properties":{"detail":{"items":{"$ref":"#/components/schemas/ValidationError"},"type":"array","title":"Detail"}},"type":"object","title":"HTTPValidationError"},"LicenseEndpointModel":{"properties":{"name":{"type":"string","title":"Name","description":"The name of the license for the NIM container."},"path":{"type":"string","title":"Path","description":"The filepath within the container containing the license content."},"sha":{"type":"string","title":"Sha","description":"A SHA1 hash of the license contents."},"size":{"type":"integer","title":"Size","description":"The number of characters in the license content."},"url":{"type":"string","title":"Url","description":"The url where this license is hosted externally."},"type":{"type":"string","const":"file","title":"Type","description":"The format of the license content."},"content":{"type":"string","title":"Content","description":"The license text."}},"type":"object","required":["name","path","sha","size","url","type","content"],"title":"LicenseEndpointModel","description":"A model representing the license response."},"ManifestEndpointModel":{"properties":{"manifest_file":{"type":"string","title":"Manifest File","description":"The content of the manifest file describing the required model artifacts."},"repository_override":{"type":"string","title":"Repository Override","description":"Alternate location used to retrieve artifacts from manifest file."}},"type":"object","required":["manifest_file","repository_override"],"title":"ManifestEndpointModel","description":"A model representing the manifest response."},"MetadataEndpointModel":{"properties":{"assetInfo":{"items":{"type":"string"},"type":"array","title":"Assetinfo","description":"A list of required container assets excluding model artifacts"},"licenseInfo":{"$ref":"#/components/schemas/LicenseEndpointModel","description":"The license info."},"modelInfo":{"items":{"$ref":"#/components/schemas/ModelInfo"},"type":"array","title":"Modelinfo","description":"A list of models being served by the NIM."},"repository_override":{"type":"string","title":"Repository Override","description":"Alternate location used to retrieve artifacts from manifest file."},"version":{"type":"string","title":"Version","description":"The version of the NIM service."}},"type":"object","required":["assetInfo","licenseInfo","modelInfo","repository_override","version"],"title":"MetadataEndpointModel","description":"A model representing the metadata response."},"ModelInfo":{"properties":{"modelUrl":{"type":"string","title":"Modelurl"},"shortName":{"type":"string","title":"Shortname"}},"type":"object","required":["modelUrl","shortName"],"title":"ModelInfo","description":"A model representing the model response."},"Transfer1Request":{"properties":{"prompt":{"type":"string","title":"Prompt","description":"Prompt which the sampled video conditions on"},"negative_prompt":{"anyOf":[{"type":"string"},{"type":"null"}],"title":"Negative Prompt","description":"Negative prompt which the sampled video conditions on","default":"The video captures a series of frames showing ugly scenes, static with no motion, motion blur, over-saturation, shaky footage, low resolution, grainy texture, pixelated images, poorly lit areas, underexposed and overexposed scenes, poor color balance, washed out colors, choppy sequences, jerky movements, low frame rate, artifacting, color banding, unnatural transitions, outdated special effects, fake elements, unconvincing visuals, poorly edited content, jump cuts, visual noise, and flickering. Overall, the video is of poor quality."},"prompt_upsampling":{"type":"boolean","title":"Prompt Upsampling","description":"Whether to use prompt upsampling before generation","default":false},"video":{"type":"string","title":"Video","description":"Video to condition on, public URL or base64 encoded video. Codecs: h264 or vp9. Number of frames >= 9."},"seed":{"anyOf":[{"type":"integer"},{"type":"null"}],"title":"Seed","description":"Random seed"},"guidance_scale":{"type":"number","maximum":20,"minimum":1,"title":"Guidance Scale","description":"Classifier-free guidance scale","default":7},"steps":{"type":"integer","maximum":50,"minimum":1,"title":"Steps","description":"Number of diffusion sampling steps","default":35},"video_params":{"$ref":"#/components/schemas/VideoParams","description":"Parameters of the requested video","default":{"frames_count":121,"frames_per_sec":24}},"vis":{"anyOf":[{"$ref":"#/components/schemas/ControlInput"},{"type":"null"}],"description":"Visual control input parameters"},"edge":{"anyOf":[{"$ref":"#/components/schemas/ControlInput"},{"type":"null"}],"description":"Edge control input parameters"},"depth":{"anyOf":[{"$ref":"#/components/schemas/ControlInput"},{"type":"null"}],"description":"Depth control input parameters"},"seg":{"anyOf":[{"$ref":"#/components/schemas/ControlInput"},{"type":"null"}],"description":"Segmentation control input parameters"},"keypoint":{"anyOf":[{"$ref":"#/components/schemas/ControlInput"},{"type":"null"}],"description":"Keypoint control input parameters"}},"additionalProperties":false,"type":"object","required":["prompt","video"],"title":"Transfer1Request"},"Transfer1Response":{"properties":{"b64_video":{"type":"string","title":"B64 Video","description":"The generated video as mp4, encoded in base64"},"upsampled_prompt":{"anyOf":[{"type":"string"},{"type":"null"}],"title":"Upsampled Prompt","description":"If prompt upsampling was enabled, the upsampled prompt"},"seed":{"type":"integer","title":"Seed","description":"Seed used for generation"}},"additionalProperties":false,"type":"object","required":["b64_video","seed"],"title":"Transfer1Response"},"ValidationError":{"properties":{"loc":{"items":{"anyOf":[{"type":"string"},{"type":"integer"}]},"type":"array","title":"Location"},"msg":{"type":"string","title":"Message"},"type":{"type":"string","title":"Error Type"}},"type":"object","required":["loc","msg","type"],"title":"ValidationError"},"VideoParams":{"properties":{"frames_count":{"type":"integer","const":121,"title":"Frames Count","description":"Number of frames of the output video","default":121},"frames_per_sec":{"type":"integer","maximum":40,"minimum":12,"title":"Frames Per Sec","description":"Number of FPS (frames per seconds) of the output video","default":24}},"additionalProperties":false,"type":"object","title":"VideoParams"}}}},"namespace":"qc69jvmznzxy","updatedDate":"2026-08-20T22:23:28.919Z","nvcfFunctionId":"a87ff22e-a2d0-496f-acb0-91df59a88f64","createdDate":"2026-02-26T00:09:29.262Z","attributes":{"apiDocsUrl":null,"termsOfUse":"<b>GOVERNING TERMS:</b> The trial service is governed by the <a href=\"https://assets.ngc.nvidia.com/products/api-catalog/legal/NVIDIA%20API%20Trial%20Terms%20of%20Service.pdf\" rel=\"noreferrer\" target=\"_blank\"><u>NVIDIA API Trial Terms of Service</u></a>; and use of the model is governed by the <a href=\"https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license/\" rel=\"noreferrer\" target=\"_blank\"><u>NVIDIA Open Model License</u></a>. Additional Information: <a href=\"https://huggingface.co/Qwen/Qwen3Guard-Gen-0.6B/blob/main/LICENSE\" rel=\"noreferrer\" target=\"_blank\"><u>Apache License 2.0</u></a>.\n  \n","showUnavailableBanner":false,"cta":{"text":"Download and Post-Train","nim_available_override_url":"https://catalog.ngc.nvidia.com/orgs/nim/teams/nvidia/containers/cosmos-predict1-7b-text2world"},"fineTuneModal":{"ngc":"https://catalog.ngc.nvidia.com/orgs/nvidia/teams/cosmos/collections/cosmos","huggingFace":"https://huggingface.co/nvidia/Cosmos-Transfer2.5-2B","nemo":"https://github.com/nvidia-cosmos/cosmos-transfer2.5"},"maxRequests":20,"systemCard":"$59","modelCapability":{"functionCalling":false}},"artifactName":"cosmos-transfer2_5-2b"}}]
5a:I[299632,["/_next/static/chunks/04d712ydf7vwt.js","/_next/static/chunks/3ibd-wdn1muo9.js","/_next/static/chunks/1q5xb__jylra0.js","/_next/static/chunks/1z_-bqrzptsiz.js","/_next/static/chunks/1la1pzs9j8idc.js","/_next/static/chunks/00eq9bqnkbpfo.js","/_next/static/chunks/1tjzqakl0-ac_.js","/_next/static/chunks/3r5yd4k4rms8-.js","/_next/static/chunks/1qasf48lwbczr.js","/_next/static/chunks/0iqwvdhi-o1pr.js","/_next/static/chunks/3-dupjzg004ft.js","/_next/static/chunks/1p8p6uesfmfc2.js","/_next/static/chunks/3c_tmnbt9nfb3.js","/_next/static/chunks/2lofudtwqsrwt.js","/_next/static/chunks/36qm3961yv116.js","/_next/static/chunks/342zpu2i9tat1.js","/_next/static/chunks/2tmwf_2axyd0y.js","/_next/static/chunks/3v9fr1qimf7lj.js","/_next/static/chunks/364lrnu5opng7.js","/_next/static/chunks/3kdaun3epyv7g.js","/_next/static/chunks/13fah1s8gxrn0.js","/_next/static/chunks/2tkz_ff5gjl4a.js","/_next/static/chunks/2_n0f-hh3ea4l.js","/_next/static/chunks/0czpc-f8wjri8.js","/_next/static/chunks/3761ezb6xysq0.js","/_next/static/chunks/24_gg9g_4g22i.js","/_next/static/chunks/1_3y3ily4zuo1.js","/_next/static/chunks/1a2o19d1j4nvx.js","/_next/static/chunks/1kci6kpi29km9.js","/_next/static/chunks/1hhq3s9jcti5r.js","/_next/static/chunks/2mr_uzqfq-mid.js","/_next/static/chunks/3o73dbhryidg8.js","/_next/static/chunks/278imbrkq3abd.js","/_next/static/chunks/3zvavojkcitpd.js","/_next/static/chunks/1q5ewy8bee9p6.js","/_next/static/chunks/2pqhypz2vo8mu.js","/_next/static/chunks/1faamicx17qlr.js","/_next/static/chunks/00jw9q5dp3jlz.js","/_next/static/chunks/2960tspz292yr.js","/_next/static/chunks/0tqq_6ft6mlt2.js"],"default"]
5b:I[306012,["/_next/static/chunks/04d712ydf7vwt.js","/_next/static/chunks/3ibd-wdn1muo9.js","/_next/static/chunks/1q5xb__jylra0.js","/_next/static/chunks/1z_-bqrzptsiz.js","/_next/static/chunks/1la1pzs9j8idc.js","/_next/static/chunks/00eq9bqnkbpfo.js","/_next/static/chunks/1tjzqakl0-ac_.js","/_next/static/chunks/3r5yd4k4rms8-.js","/_next/static/chunks/1qasf48lwbczr.js","/_next/static/chunks/0iqwvdhi-o1pr.js","/_next/static/chunks/3-dupjzg004ft.js","/_next/static/chunks/1p8p6uesfmfc2.js","/_next/static/chunks/3c_tmnbt9nfb3.js","/_next/static/chunks/2lofudtwqsrwt.js","/_next/static/chunks/36qm3961yv116.js","/_next/static/chunks/342zpu2i9tat1.js","/_next/static/chunks/2tmwf_2axyd0y.js","/_next/static/chunks/3v9fr1qimf7lj.js","/_next/static/chunks/364lrnu5opng7.js","/_next/static/chunks/3kdaun3epyv7g.js","/_next/static/chunks/13fah1s8gxrn0.js","/_next/static/chunks/2tkz_ff5gjl4a.js","/_next/static/chunks/2_n0f-hh3ea4l.js","/_next/static/chunks/0czpc-f8wjri8.js","/_next/static/chunks/3761ezb6xysq0.js","/_next/static/chunks/24_gg9g_4g22i.js","/_next/static/chunks/1_3y3ily4zuo1.js","/_next/static/chunks/1a2o19d1j4nvx.js","/_next/static/chunks/1kci6kpi29km9.js","/_next/static/chunks/1hhq3s9jcti5r.js","/_next/static/chunks/2mr_uzqfq-mid.js","/_next/static/chunks/3o73dbhryidg8.js","/_next/static/chunks/278imbrkq3abd.js","/_next/static/chunks/3zvavojkcitpd.js","/_next/static/chunks/1q5ewy8bee9p6.js","/_next/static/chunks/2pqhypz2vo8mu.js","/_next/static/chunks/1faamicx17qlr.js","/_next/static/chunks/00jw9q5dp3jlz.js","/_next/static/chunks/2960tspz292yr.js","/_next/static/chunks/0tqq_6ft6mlt2.js"],"ButtonCTA"]
5c:I[331699,["/_next/static/chunks/04d712ydf7vwt.js","/_next/static/chunks/3ibd-wdn1muo9.js","/_next/static/chunks/1q5xb__jylra0.js","/_next/static/chunks/1z_-bqrzptsiz.js","/_next/static/chunks/1la1pzs9j8idc.js","/_next/static/chunks/00eq9bqnkbpfo.js","/_next/static/chunks/1tjzqakl0-ac_.js","/_next/static/chunks/3r5yd4k4rms8-.js","/_next/static/chunks/1qasf48lwbczr.js","/_next/static/chunks/0iqwvdhi-o1pr.js","/_next/static/chunks/3-dupjzg004ft.js","/_next/static/chunks/1p8p6uesfmfc2.js","/_next/static/chunks/3c_tmnbt9nfb3.js","/_next/static/chunks/2lofudtwqsrwt.js","/_next/static/chunks/36qm3961yv116.js","/_next/static/chunks/342zpu2i9tat1.js","/_next/static/chunks/2tmwf_2axyd0y.js","/_next/static/chunks/3v9fr1qimf7lj.js","/_next/static/chunks/364lrnu5opng7.js","/_next/static/chunks/3kdaun3epyv7g.js","/_next/static/chunks/13fah1s8gxrn0.js","/_next/static/chunks/2tkz_ff5gjl4a.js","/_next/static/chunks/2_n0f-hh3ea4l.js","/_next/static/chunks/0czpc-f8wjri8.js","/_next/static/chunks/3761ezb6xysq0.js","/_next/static/chunks/24_gg9g_4g22i.js","/_next/static/chunks/1_3y3ily4zuo1.js","/_next/static/chunks/1a2o19d1j4nvx.js","/_next/static/chunks/1kci6kpi29km9.js","/_next/static/chunks/1hhq3s9jcti5r.js","/_next/static/chunks/2mr_uzqfq-mid.js","/_next/static/chunks/3o73dbhryidg8.js","/_next/static/chunks/278imbrkq3abd.js","/_next/static/chunks/3zvavojkcitpd.js","/_next/static/chunks/1q5ewy8bee9p6.js","/_next/static/chunks/2pqhypz2vo8mu.js","/_next/static/chunks/1faamicx17qlr.js","/_next/static/chunks/00jw9q5dp3jlz.js","/_next/static/chunks/2960tspz292yr.js","/_next/static/chunks/0tqq_6ft6mlt2.js"],"ModelContent"]
5d:I[460285,["/_next/static/chunks/04d712ydf7vwt.js","/_next/static/chunks/3ibd-wdn1muo9.js","/_next/static/chunks/1q5xb__jylra0.js","/_next/static/chunks/1z_-bqrzptsiz.js","/_next/static/chunks/1la1pzs9j8idc.js","/_next/static/chunks/00eq9bqnkbpfo.js","/_next/static/chunks/1tjzqakl0-ac_.js","/_next/static/chunks/3r5yd4k4rms8-.js","/_next/static/chunks/1qasf48lwbczr.js","/_next/static/chunks/0iqwvdhi-o1pr.js","/_next/static/chunks/3-dupjzg004ft.js","/_next/static/chunks/1p8p6uesfmfc2.js","/_next/static/chunks/3c_tmnbt9nfb3.js","/_next/static/chunks/2lofudtwqsrwt.js","/_next/static/chunks/36qm3961yv116.js","/_next/static/chunks/342zpu2i9tat1.js","/_next/static/chunks/2tmwf_2axyd0y.js","/_next/static/chunks/3v9fr1qimf7lj.js","/_next/static/chunks/364lrnu5opng7.js","/_next/static/chunks/3kdaun3epyv7g.js","/_next/static/chunks/13fah1s8gxrn0.js","/_next/static/chunks/2tkz_ff5gjl4a.js","/_next/static/chunks/2_n0f-hh3ea4l.js","/_next/static/chunks/0czpc-f8wjri8.js","/_next/static/chunks/3761ezb6xysq0.js","/_next/static/chunks/24_gg9g_4g22i.js","/_next/static/chunks/1_3y3ily4zuo1.js","/_next/static/chunks/1a2o19d1j4nvx.js","/_next/static/chunks/1kci6kpi29km9.js","/_next/static/chunks/1hhq3s9jcti5r.js","/_next/static/chunks/2mr_uzqfq-mid.js","/_next/static/chunks/3o73dbhryidg8.js","/_next/static/chunks/278imbrkq3abd.js","/_next/static/chunks/3zvavojkcitpd.js","/_next/static/chunks/1q5ewy8bee9p6.js","/_next/static/chunks/2pqhypz2vo8mu.js","/_next/static/chunks/1faamicx17qlr.js","/_next/static/chunks/00jw9q5dp3jlz.js","/_next/static/chunks/2960tspz292yr.js","/_next/static/chunks/0tqq_6ft6mlt2.js"],"default"]
54:["$","p",null,{"className":"max-w-[85ch] text-ms text-primary","id":"resource-description","children":"Generates physics-aware video world states for physical AI development using text prompts and multiple spatial control inputs derived from real-world data or simulation."}]
55:["$","div",null,{"className":"flex w-full flex-col items-start gap-md lg:flex-row lg:items-end lg:justify-between","children":[["$","div",null,{"className":"flex w-full min-w-0 flex-wrap gap-sm lg:flex-1","children":["$","$L5a",null,{"artifactType":"ENDPOINT","density":"standard","labels":"$4a:0:props:children:0:props:children:1:props:children:props:children:props:children:1:props:children:1:props:artifact:labels","searchRoutePath":"/models"}]}],["$","div",null,{"className":"z-30 flex w-full flex-row justify-start gap-ms sm:justify-end lg:w-auto lg:shrink-0","children":["$undefined",["$","$L5b",null,{"cta":{"text":"Download and Post-Train","url":"?modal=fine-tune"}}]]}]]}]
56:["$","div",null,{"className":"pointer-events-none absolute right-0 bottom-0 left-0 z-20 h-30 bg-gradient-to-t to-transparent from-manitoulinLightBlack via-manitoulinLightBlack/70"}]
57:["$","div",null,{"className":"px-4 mx-auto flex max-w-screen-xl flex-col pt-0 lg:px-0","data-body-background":"light-black","children":["$","section",null,{"className":"flex w-full flex-col justify-between rounded-4 border-manitoulinBorderColor bg-manitoulinDarkBlack sm:rounded-6 lg:rounded-8 p-ms lg:p-lg","children":["$","$L5c",null,{"apiReferenceEnabled":false,"artifact":"$4a:0:props:children:0:props:children:1:props:children:props:children:props:children:1:props:children:1:props:artifact","endpointName":"cosmos-transfer2_5-2b","endpointSpec":"$4b:props:spec","isLoginRequired":true,"playgroundElement":"$5d","publisherName":"nvidia","searchParams":{"model":"cosmos-transfer2_5-2b"},"tabs":[{"label":"Experience","bare":true,"icon":"play","kind":"default","id":"experience","href":"/nvidia/cosmos-transfer2_5-2b","aliases":["/nvidia/cosmos-transfer2_5-2b/experience"]},{"label":"Model Card","icon":"book","kind":"default","id":"modelcard","href":"/nvidia/cosmos-transfer2_5-2b/modelcard","aliases":"$undefined"},{"label":"System Card","icon":"gpu","kind":"default","id":"systemcard","href":"/nvidia/cosmos-transfer2_5-2b/systemcard","aliases":"$undefined"}]}]}]}]
