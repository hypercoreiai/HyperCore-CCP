---
title: "nemotron-3-embed-1b"
publisher: "nvidia"
type: "endpoint"
updated: "2026-07-16T19:07:19.287Z"
description: "1B embedding model for semantic search, retrieval, and RAG applications."
canonical: "https://build.nvidia.com/nvidia/nemotron-3-embed-1b"
---

# Model Overview

### Description:

**Nemotron-3-Embed-1B** is a versatile text embedding model developed by NVIDIA and optimized for retrieval and semantic similarity tasks. It provides strong multilingual and cross-lingual retrieval capabilities and is designed to serve as a foundational component in text-based Retrieval-Augmented Generation (RAG) systems.

The model is available in two versions:

- **Nemotron-3-Embed-1B-BF16:** The reference BF16 model.
- **Nemotron-3-Embed-1B-NVFP4:** A post-training-quantized derivative of the BF16 model, with Quantization-Aware Distillation (QAD) applied to recover retrieval accuracy, particularly for long input sequences.

Both versions were evaluated across 34 languages: English, Arabic, Assamese, Bengali, Bulgarian, Chinese, Danish, Dutch, Finnish, French, German, Hindi, Hinglish, Indonesian, Italian, Japanese, Korean, Malay, Marathi, Nepali, Norwegian, Persian, Portuguese, Romanian, Russian, Spanish, Swahili, Swedish, Tamil, Telugu, Thai, Ukrainian, Urdu, and Vietnamese.

The model generates dense vector embeddings from multilingual text inputs, enabling retrieval, semantic search, code retrieval, and agentic or conventional RAG workflows. As a core component of text retrieval systems, an embedding model transforms text, such as questions or passages, into dense vector representations suitable for efficient similarity matching.

Among models of comparable size, **Nemotron-3-Embed-1B-BF16** achieves state-of-the-art performance across multiple multilingual retrieval benchmarks. **Nemotron-3-Embed-1B-NVFP4** retains approximately 99.5% of the BF16 version's reported RTEB score.

The BF16 and NVFP4 versions generally share the same embedding space and can be used interchangeably, but retrieval quality should be validated on a representative sample before switching versions in a production system.

*This model is ready for commercial use.*

### License/Terms of Use:

**GOVERNING TERMS:** Use of this trial service is governed by the [NVIDIA API Trial Terms of Service](https://assets.ngc.nvidia.com/products/api-catalog/legal/NVIDIA%20API%20Trial%20Terms%20of%20Service.pdf). Use of the model and associated software are governed by the [OpenMDW License Agreement, version 1.1](https://github.com/OpenMDW/OpenMDW/blob/main/1.1/LICENSE.OpenMDW-1.1). ADDITIONAL INFORMATION: [Apache License, Version 2.0](https://www.apache.org/licenses/LICENSE-2.0).

**You are responsible for ensuring that your use of NVIDIA provided models complies with all applicable laws.**

**Model Developer:** NVIDIA

### Deployment Geography:

**Global**

### Use Case:

Nemotron-3-Embed-1B is most suitable for users who want to build a multilingual question-and-answer application over a large text corpus, leveraging the latest dense retrieval technologies, including RAG pipelines.

The BF16 version is intended for applications prioritizing the highest reported retrieval quality. The NVFP4 version is intended for efficient quantized inference while retaining closely comparable retrieval quality. Validate retrieval quality on representative application data before switching versions.

### Release Date:

**Build.NVIDIA.com:** 07/16/2026 via [link](https://build.nvidia.com/nvidia/nemotron-3-embed-1b/)

**Hugging Face:** 07/16/2026 via [Nemotron-3-Embed-1B-BF16](https://huggingface.co/nvidia/Nemotron-3-Embed-1B-BF16) and [Nemotron-3-Embed-1B-NVFP4](https://huggingface.co/nvidia/Nemotron-3-Embed-1B-NVFP4)

## Model Architecture:

**Architecture Type:** Transformer <br>
**Network Architecture:** [Ministral-3-3B-Instruct-2512](https://huggingface.co/mistralai/Ministral-3-3B-Instruct-2512) based pruned model <br>
**Embedding Dimension:** 2048 <br>
**Max Sequence Length:** 32768 <br>
**Number of Model Parameters:** ~1.14B <br>
**Precision:** BF16 and NVFP4

The **Nemotron-3-Embed-1B-BF16** model is a transformer-based text embedding model trained with bidirectional attention masking, where the final embedding vector is obtained by applying average pooling to the transformer's token-level representations. It encodes each input text into a dense embedding vector of dimension 2048.

The **Nemotron-3-Embed-1B-BF16** was derived from the **nemotron-3-embed-3b** text-embedding model through two iterative rounds of structured pruning and distillation. First, the 3B parent model was pruned to 2B using NVIDIA ModelOpt mcore_minitron Neural Architecture Search (NAS) [[NVIDIA/Model-Optimizer](https://github.com/NVIDIA/Model-Optimizer), [paper](https://arxiv.org/pdf/2407.14679)]. This process searches across hidden width, FFN size, attention heads, and depth, then selects the best candidate from the top-10 Pareto front. Candidates were evaluated against the parent model's representations using a 50k in-domain calibration corpus, which was also used to estimate importance scores.

The resulting 2B model was then distilled from the fine-tuned **Nemotron-3-Embed-8B-BF16** embedding teacher model to recover accuracy. Distillation used combined cosine distance loss (COS) and mean squared error (MSE) loss on a multilingual, in-domain retrieval data blend. The same pruning-and-distillation procedure, using the same dataset blend, was then repeated to produce the final 1.14B embedding model.

**Nemotron-3-Embed-1B-NVFP4** is a post-training-quantized derivative of Nemotron-3-Embed-1B-BF16. NVIDIA Model Optimizer version 0.45.0 was used to quantize the weights and activations of linear layers only, targeting the NVFP4 data type for efficient inference. QAD was applied primarily to recover accuracy for long input sequences.

## Input(s):

**Input Type(s):** Text <br>
**Input Format(s):** List of strings <br>
**Input Parameters:** One Dimensional (1D) <br>
**Other Properties Related to Input:** Text inputs should be tokenized by the model tokenizer. The model's max sequence length is 32768. Longer inputs should be chunked or truncated.

## Output(s):

**Output Type(s):** Floats <br>
**Output Format(s):** List of float arrays <br>
**Output Parameters:** One-Dimensional (1D) embedding vector per input text string <br>
**Other Properties Related to Output:** The model outputs a 2048-dimensional embedding vector for each input text string. It also supports retaining the first 1024 or 512 dimensions; sliced vectors must be L2-normalized again before similarity scoring.

__Our AI models are designed and/or optimized to run on NVIDIA GPU-accelerated systems. By leveraging NVIDIA's hardware (e.g. GPU cores) and software frameworks (e.g., CUDA libraries), the model achieves faster training and inference times compared to CPU-only solutions.__

## Software Integration:

**Runtime Engine(s):** Rust

**Supported Hardware Microarchitecture Compatibility:**

- NVIDIA Ampere (A100 SXM 40GB, A10G)
- NVIDIA Blackwell (GB200, RTX PRO 6000 Blackwell Server Edition)
- NVIDIA Hopper (H100 80GB HBM3)
- NVIDIA Lovelace (L40S)

**Preferred/Supported Operating System(s):** Linux

The integration of foundation and fine-tuned models into AI systems requires additional testing using use-case-specific data to ensure safe and effective deployment. Following the V-model methodology, iterative testing and validation at both unit and system levels are essential to mitigate risks, meet technical and functional requirements, and ensure compliance with safety and ethical standards before deployment.

## Performance:

| Model Name | RTEB 16 | ViDoRE-V3 text | MMTEB (Retrieval) |
| --- | ---: | ---: | ---: |
| llama-nemotron-embed-1b-v2 | 60.47 | 52.10 | 59.58 |
| llama-nemotron-embed-vl-1b-v2 | 61.98 | 52.54 | 59.71 |
| **Nemotron-3-Embed-1B-BF16** | **72.38** | **57.76** | **71.05** |
| **Nemotron-3-Embed-1B-NVFP4** | **72.00** | **57.50** | **70.59** |

*Avg. NDCG@10 on text retrieval benchmarks (chunk retrieval), evaluated at sequence length 4096. The NVFP4 RTEB result was evaluated on an NVIDIA GB200 GPU.*

## Model Version(s):

**Nemotron-3-Embed-1B-BF16**

**Nemotron-3-Embed-1B-NVFP4**

**Short Name:** `nemotron-3-embed-1b`

## Training, Testing, and Evaluation Datasets:

### Dataset Overview:
**Total Size:** 8.5M+ data samples <br>
**Total Number of Datasets:** 161 dataset files <br>
**Dataset Partition:** Training [100%], Testing [N/A — evaluation benchmarks used separately], Validation [N/A — evaluation benchmarks used separately].

Model distillation training was conducted using publicly available, commercially permissible datasets and synthetically generated datasets. Synthetic data was created either by generating queries from seed documents or by generating complete question–answer pairs through LLM-based prompting using the models listed below.

Nemotron-3-Embed-1B-NVFP4 is a post-training-quantized derivative of Nemotron-3-Embed-1B-BF16. Its quantization calibration used 512 samples consisting of 256 queries and 256 passages. Its QAD stage used 20,000 samples across five dataset files.

### Public Datasets:

| Dataset name | Reference |
| --- | --- |
| MIRACL | [https://huggingface.co/datasets/miracl/miracl](https://huggingface.co/datasets/miracl/miracl) |
| MLDR | [https://huggingface.co/datasets/Shitao/MLDR](https://huggingface.co/datasets/Shitao/MLDR) |
| HotpotQA | [https://hotpotqa.github.io/](https://hotpotqa.github.io/) |
| NQ | [https://huggingface.co/datasets/sentence-transformers/embedding-training-data](https://huggingface.co/datasets/sentence-transformers/embedding-training-data) |
| Squad | [https://rajpurkar.github.io/SQuAD-explorer/](https://rajpurkar.github.io/SQuAD-explorer/) |
| Stack Exchange | [https://archive.org/details/stackexchange](https://archive.org/details/stackexchange) |
| Hover | [https://hover-nlp.github.io/](https://hover-nlp.github.io/) |
| TAT-QA | [https://huggingface.co/datasets/next-tat/TAT-QA](https://huggingface.co/datasets/next-tat/TAT-QA) |
| FinQA | [https://github.com/czyssrs/FinQA/tree/main](https://github.com/czyssrs/FinQA/tree/main) |
| PubMedQA | [https://huggingface.co/datasets/qiaojin/PubMedQA/viewer/pqa_labeled](https://huggingface.co/datasets/qiaojin/PubMedQA/viewer/pqa_labeled) |
| MedQuAD | [https://github.com/abachaa/MedQuAD](https://github.com/abachaa/MedQuAD) |
| JaQuAD | [https://huggingface.co/datasets/SkelterLabsInc/JaQuAD](https://huggingface.co/datasets/SkelterLabsInc/JaQuAD) |
| coir_apps | [https://huggingface.co/datasets/CoIR-Retrieval/apps](https://huggingface.co/datasets/CoIR-Retrieval/apps) |
| coir_cosqa | [https://huggingface.co/datasets/CoIR-Retrieval/cosqa](https://huggingface.co/datasets/CoIR-Retrieval/cosqa) |
| coir_stackoverflow_qa | [https://huggingface.co/datasets/CoIR-Retrieval/stackoverflow-qa](https://huggingface.co/datasets/CoIR-Retrieval/stackoverflow-qa) |
| coir_codetrans_dl | [https://huggingface.co/datasets/CoIR-Retrieval/codetrans-dl](https://huggingface.co/datasets/CoIR-Retrieval/codetrans-dl) |
| coir_codetrans_contest | [https://huggingface.co/datasets/CoIR-Retrieval/codetrans-contest](https://huggingface.co/datasets/CoIR-Retrieval/codetrans-contest) |
| synthetic_text2sql | [https://huggingface.co/datasets/CoIR-Retrieval/synthetic-text2sql](https://huggingface.co/datasets/CoIR-Retrieval/synthetic-text2sql) |
| SWE-bench | [https://huggingface.co/datasets/princeton-nlp/SWE-bench/viewer/default/train](https://huggingface.co/datasets/princeton-nlp/SWE-bench/viewer/default/train) |
| MLQA | [https://github.com/facebookresearch/MLQA](https://github.com/facebookresearch/MLQA) |
| SpartQA | [https://github.com/HLR/SpartQA_generation](https://github.com/HLR/SpartQA_generation) |
| Winogrande | [https://github.com/allenai/winogrande](https://github.com/allenai/winogrande) |
| TempReason | [https://huggingface.co/datasets/tonytan48/TempReason](https://huggingface.co/datasets/tonytan48/TempReason) |

### Synthetic Datasets:

Synthetic query-document pairs were generated either from scratch or by using seed datasets to generate queries with the models listed below.

<table>
<tr>
<th>LLMs used to generate synthetic datasets</th>
</tr>
<tr>
<td>Qwen/Qwen3-Next-80B-A3B-Instruct<br>Qwen/Qwen3-235B-A22B<br>Qwen/Qwen3.5-397B-A17B<br>Qwen/Qwen3.6-27B<br>Qwen/Qwen3.6-35B-A3B</td>
</tr>
<tr>
<td>google/gemma-4-31B-it</td>
</tr>
<tr>
<td>openai/gpt-oss-120b<br>openai/gpt-oss-20b</td>
</tr>
<tr>
<td>nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-BF16<br>nvidia/NVIDIA-Nemotron-3-Ultra-550B-A55B-NVFP4</td>
</tr>
</table>

<table>
<tr>
<th colspan="2">Seed Datasets</th>
</tr>
<tr>
<th>Dataset</th>
<th>Reference</th>
</tr>
<tr>
<td>FinePdfs</td>
<td><a href="https://huggingface.co/datasets/HuggingFaceFW/finepdfs">https://huggingface.co/datasets/HuggingFaceFW/finepdfs</a></td>
</tr>
<tr>
<td>CentralActs</td>
<td><a href="https://zenodo.org/records/5088102">https://zenodo.org/records/5088102</a></td>
</tr>
<tr>
<td>BRIGHT</td>
<td><a href="https://huggingface.co/datasets/xlangai/BRIGHT">https://huggingface.co/datasets/xlangai/BRIGHT</a></td>
</tr>
<tr>
<td>MultiHiertt</td>
<td><a href="https://github.com/psunlpgroup/MultiHiertt">https://github.com/psunlpgroup/MultiHiertt</a></td>
</tr>
</table>

### Training Dataset:

**Data Modality:** Text <br>
**Training Data Size:** 8.5M+ <br>
**Data Collection Method by dataset:** Hybrid: Manually-Collected, Automated, Synthetic <br>
**Labeling Method by dataset:** Hybrid: Manually-Collected, Automated, Synthetic <br>
**Properties:** Model training was conducted on text datasets using question–passage pairs from publicly available, commercially permissible datasets and synthetically generated datasets. The NVFP4 version additionally used a 512-sample calibration set and a 20,000-sample QAD training set derived from the BF16 data mixture.

### Testing Dataset:

**Data Collection Method by dataset:** Not Applicable <br>
**Labeling Method by dataset:** Not Applicable <br>
**Properties:** Not Applicable. Model quality was assessed using the evaluation benchmark datasets described in the Evaluation Dataset subsection.

### Evaluation Dataset:

**Data Collection Method by dataset:** Hybrid: Manually-Collected, Automated, Synthetic <br>
**Labeling Method by dataset:** Hybrid: Manually-Collected, Automated, Synthetic <br>
**Properties:** The model was evaluated on 16 public tasks on the [Retrieval Embedding Benchmark (RTEB)](https://huggingface.co/blog/rteb), a benchmark designed to evaluate the retrieval accuracy of embedding models for real-world applications. More details on RTEB can be found on its [leaderboard](https://huggingface.co/spaces/mteb/leaderboard?benchmark_name=RTEB%28beta%29).

The BF16 version was also evaluated on [MMTEB Retrieval benchmark datasets](https://huggingface.co/spaces/mteb/leaderboard) ([paper](https://arxiv.org/pdf/2502.13595)) and on eight text datasets extracted through OCR from the [ViDoRe-V3 benchmark](https://mteb-leaderboard.hf.space/benchmark/ViDoRe(v3)). The NVFP4 version was compared directly with the BF16 version on RTEB.

## Inference:

**Acceleration Engine:** Rust <br>
**Test Hardware:** NVIDIA Lovelace (L40S)

## Ethical Considerations:

NVIDIA believes Trustworthy AI is a shared responsibility and we have established policies and practices to enable development for a wide array of AI applications. Developers should work with their internal model team to ensure this model meets requirements for the relevant industry and use case and addresses unforeseen product misuse.

For more detailed information on ethical considerations for this model, please see the Model Card++ Bias, Explainability, Safety & Security, and Privacy Subcards.

Please report model quality, risk, security vulnerabilities or NVIDIA AI Concerns [here](https://www.nvidia.com/en-us/support/submit-security-vulnerability/).

## Specifications

- **Context Length:** 32,768 tokens
- **Parameters:** 1,140,918,272

## Capabilities

- **Function Calling:** Not supported

## Bias

| Field | Response |
| ----- | ----- |
| Participation considerations from adversely impacted groups [protected classes](https://www.senate.ca.gov/content/protected-classes) in model design and testing | None |
| Measures taken to mitigate against unwanted bias | None |
| Bias Metric (If Measured): | None |

## Explainability

| Field | Response |
| ----- | ----- |
| Intended Task/Domain: | Passage and query embedding for question and answer retrieval |
| Model Type: | Transformer encoder |
| Intended Users: | Generative AI creators working with conversational AI models - users who want to build a multilingual question and answer application over a large text corpus, leveraging the latest dense retrieval technologies. |
| Output: | Array of float numbers (Dense Vector Representation for the input text) |
| Describe how the model works: | Model transforms the tokenized input text into a dense vector representation. |
| Name the adversely impacted groups this has been tested to deliver comparable outcomes regardless of: | Not Applicable |
| Technical Limitations & Mitigation: | The model's max sequence length is 32768. Therefore, the longer text inputs should be truncated. |
| Verified to have met prescribed NVIDIA quality standards: | Yes |
| Performance Metrics: | Accuracy, Throughput, and Latency |
| Potential Known Risks: | This model does not always guarantee to retrieve the correct passage(s) for a given query. |
| Licensing: | This model and its associated configuration files are licensed under the [OpenMDW License Agreement, version 1.1 (OpenMDW-1.1)](https://openmdw.ai/license/1-1/). Additional Information: Built with [Ministral-3-3B-Instruct-2512](https://huggingface.co/mistralai/Ministral-3-3B-Instruct-2512) which is released under Apache 2.0. |

## Privacy

| Field | Response |
| ----- | ----- |
| Generatable or reverse engineerable personal data? | None |
| Was consent obtained for any personal data used? | Not Applicable |
| Personal data used to create this model? | None Known |
| How often is the dataset reviewed? | Before Every Release |
| Is there provenance for all datasets used in training? | Yes |
| Does data labeling (annotation, metadata) comply with privacy laws? | Yes |
| Was data from user interactions with the AI model (e.g. user input and prompts) used to train the model? | Yes |
| Is data compliant with data subject requests for data correction or removal, if such a request was made? | No, not possible with externally-sourced data. |
| Applicable Privacy Policy | https://www.nvidia.com/en-us/about-nvidia/privacy-policy/ |

## Safety & Security

| Field | Response |
| ----- | ----- |
| Model Application(s): | Text Embedding for Retrieval |
| Describe the life critical impact (if present). | Not Applicable |
| Use Case Restrictions: | This model and its associated configuration files are licensed under the [OpenMDW License Agreement, version 1.1 (OpenMDW-1.1)](https://openmdw.ai/license/1-1/). Additional Information: Built with [Ministral-3-3B-Instruct-2512](https://huggingface.co/mistralai/Ministral-3-3B-Instruct-2512) which is released under Apache 2.0. |
| Model and dataset restrictions: | The Principle of least privilege (PoLP) is applied limiting access for dataset generation and model development. Restrictions enforce dataset access during training, and dataset license constraints adhered to. |