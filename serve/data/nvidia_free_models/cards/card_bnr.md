:false}]
4f:T254d,# Model Overview

### Description:

Background Noise Removal (BNR) is an audio background noise removal model 
from NVIDIA. BNR removes unwanted noises from audio, which improves speech 
intelligibility and also improves the speech recognition accuracy of 
various ASR systems under noisy environments.  

This model is ready for commercial use.  


### License/Terms of Use:

Use of this model is governed by the [NVIDIA Open Model License](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license/).  


### Deployment Geography:

Global  


## Model Architecture

**Architecture Type:** Residual Convolutional Recurrent Neural Network (CRNN)  
**Network Architecture:** SEASR  
**Number of model parameters:** ~60M  


## Input(s):

**Input Type(s):** Audio  
**Input Format(s):** PCM F32  
**Input Parameters:** One-Dimensional (1D)  
**Other Properties Related to Input:** Pulse Code Modulation (PCM) audio samples
with no encoding or pre-processing; 16kHz or 48kHz sampling rate required.  

## Output(s):

**Output Type(s):** Audio  
**Output Format:** PCM F32  
**Output Parameters:** One-Dimensional (1D)  
**Other Properties Related to Output:** PCM audio samples at input sampling rate
with no encoding or post-processing.  

Our AI models are designed and/or optimized to run on NVIDIA GPU-accelerated 
systems. By leveraging NVIDIA’s hardware (e.g. GPU cores) and software 
frameworks (e.g., CUDA libraries), the model achieves faster training and 
inference times compared to CPU-only solutions.   


## Software Integration

**Runtime Engine(s):**  
* Audio Effects 2.1.0

**Supported Hardware Microarchitecture Compatibility:**  
* NVIDIA Ampere  
* NVIDIA Blackwell  
* NVIDIA Hopper
* NVIDIA Lovelace  
* NVIDIA Turing  

**Preferred/Supported Operating System(s):**  
* Linux  
* Windows  

The integration of foundation and fine-tuned models into AI systems requires 
additional testing using use-case-specific data to ensure safe and effective 
deployment. Following the V-model methodology, iterative testing and validation
at both unit and system levels are essential to mitigate risks, meet technical 
and functional requirements, and ensure compliance with safety and ethical 
standards before deployment.  

This AI model can be embedded as an Application Programming Interface (API) call
into the software environment described above.

## Model Version(s)

BNR v2.1  


# Training, Testing, and Evaluation Datasets

**Data Modality:**
* Audio

**Audio Training Data Size:**
* Less than 10,000 Hours


NVIDIA models are trained on a diverse set of public and proprietary datasets.
The BNR 2.0 model is trained on a wide range of English language accents, 
some European and Asian languages, and 29 different noise profiles that are 
commonly audible in the real world. 

**Data Collection Method by dataset:** [Hybrid: Human, Synthetic]  

**Labeling Method by dataset:** [Hybrid: Human, Synthetic]  

**Link:** [AudioSet](https://research.google.com/audioset/)  
**Properties (Quantity, Dataset Descriptions, Sensor(s)):**  
AudioSet consists of an expanding ontology of 632 audio event classes and 
a collection of 2,084,320 human-labeled 10-second sound clips drawn from 
publicly available internet scale data.  

**Link:** [CREMA-D](https://www.kaggle.com/ejlok1/cremad)  
**Properties (Quantity, Dataset Descriptions, Sensor(s)):**  
CREMA-D is a data set of 7,442 original clips from 91 actors. These clips were 
from 48 male and 43 female actors between the ages of 20 and 74 coming from a 
variety of races and ethnicities (African American, Asian, Caucasian, Hispanic, 
and Unspecified). Actors spoke from a selection of 12 sentences. The sentences 
were presented using one of six different emotions (Anger, Disgust, Fear, Happy,
Neutral, and Sad) and four different emotion levels (Low, Medium, High, and 
Unspecified).  

**Link:** [Crowdsourced high-quality UK and Ireland English Dialect speech data set](https://www.openslr.org/83/)  
**Properties (Quantity, Dataset Descriptions, Sensor(s)):**  
The dataset contains male and female high quality recordings of English from
various dialects of the UK and Ireland for a total of 17,877 lines.  

**Link:** [CSR-I WSJ0](https://catalog.ldc.upenn.edu/LDC93S6A)  
**Properties (Quantity, Dataset Descriptions, Sensor(s)):**  
Corpus by the DARPA Spoken Language Program to support research on large-
vocabulary Continuous Speech Recognition (CSR) systems. The first two CSR 
Corpora consist primarily of read speech with texts drawn from a machine-
readable corpus of Wall Street Journal news text and are thus often known as 
WSJ0 and WSJ1. WSJ0 consists of 123 speakers.  

**Link:** [CSTR VCTK](https://datashare.ed.ac.uk/handle/10283/3443)  
**Properties (Quantity, Dataset Descriptions, Sensor(s)):**  
This CSTR VCTK Corpus includes speech data uttered by 110 English speakers with
various accents. Each speaker reads out about 400 sentences, which were selected
from a newspaper, the rainbow passage and an elicitation paragraph used for the
speech accent archive.  

**Link:** [DAPS](https://ccrma.stanford.edu/~gautham/Site/daps.html)  
**Properties (Quantity, Dataset Descriptions, Sensor(s)):**  
The DAPS dataset has 15 versions of audio (3 professional versions and
12 consumer device/real-world environment combinations). Each version consists
of about 4.5 hours of data (about 14 minutes from each of 20 speakers).  

**Link:** [DEMAND](https://zenodo.org/records/1227121)  
**Properties (Quantity, Dataset Descriptions, Sensor(s)):**  
The DEMAND (Diverse Environments Multichannel Acoustic Noise Database) 
contains a set of recordings that allow testing of algorithms using 
real-world noise in a variety of settings. This version provides 15 recordings. 
All recordings are made with a 16-channel array, with the smallest distance 
between microphones being 5 cm and the largest being 21.8 cm. It is a collection 
of multichannel recordings of accoustic noise in diverse environments.  

**Link:** [Edinburgh 56 speaker dataset](https://datashare.ed.ac.uk/handle/10283/2791)  
**Properties (Quantity, Dataset Descriptions, Sensor(s)):**  
Clean and noisy parallel speech database from 56 speakers designed to train and 
test speech enhancement methods that operate at 48kHz.  

**Link:** [FreeField](https://archive.org/details/freefield1010)  
**Properties (Quantity, Dataset Descriptions, Sensor(s)):**  
A dataset of standardised 7690 10-second excerpts from Freesound field recordings.  

**Link:** [Freesound](https://freesound.org/)  
**Properties (Quantity, Dataset Descriptions, Sensor(s)):**  
Freesound is a collaborative collection of 620,291 free sounds which contains 
speakers speaking in different emotions as well as female speakers speaking in 
high pitched voices. The audio data also contains few noise profiles too.  

**Link:** GTC Dataset  
**Properties (Quantity, Dataset Descriptions, Sensor(s)):**  
A collection of talks from NVIDIA GTC Conferences with a total of 103 speakers.  

**Link:** [HiFi-TTS](https://www.openslr.org/109/)  
**Properties (Quantity, Dataset Descriptions, Sensor(s)):**  
A multi-speaker English dataset for training text-to-speech models. 
The HiFi-TTS dataset contains about 291.6 hours of speech from 10 speakers 
with at least 17 hours per speaker sampled at 44.1 kHz.  

**Link:** [LibriTTS](https://www.openslr.org/60/)  
**Properties (Quantity, Dataset Descriptions, Sensor(s)):**  
LibriTTS is a multi-speaker English corpus of approximately 585 hours of read
English speech by 200 speakers, which is resampled at 16kHZ.  

**Link:** [Vocal set dataset](https://zenodo.org/record/1193957#.Xt9uVUUzaUl)  
**Properties (Quantity, Dataset Descriptions, Sensor(s)):**  
VocalSet is a singing voice dataset consisting of 10.1 hours of monophonic 
recorded audio of professional singers demonstrating both standard and extended 
vocal techniques on all 5 vowels. Existing singing voice datasets aim to capture
a focused subset of singing voice characteristics, and generally consist of just
a few singers. VocalSet contains recordings from 20 different singers (9 male, 
11 female) and a range of voice types.  VocalSet aims to improve the state of 
existing singing voice datasets and singing voice research by capturing not only
a range of vowels, but also a diverse set of voices on many different vocal 
techniques, sung in contexts of scales, arpeggios, long tones, and excerpts.  


# Inference

**Acceleration Engine:** Tensor(RT), [Triton](https://developer.nvidia.com/triton-inference-server)  
**Test Hardware:** 
* T4, T10, A30, A100, A2, A10, A16, A40, L4, L40, H100, B40  
* RTX 4080, RTX 4090, RTX 5070, RTX 5080, RTX 5090  


## Ethical Considerations

NVIDIA believes Trustworthy AI is a shared responsibility and we have established
policies and practices to enable development for a wide array of AI applications.
When downloaded or used in accordance with our terms of service, developers
should work with their internal model team to ensure this model meets
requirements for the relevant industry and use case and addresses unforeseen
product misuse.  

For more detailed information on ethical considerations for this
model, please see the Model Card++ [Bias](bias), [Explainability](explainability),
[Safety & Security](safety-and-security), and [Privacy](privacy) Subcards.  

Please report model quality, risk, security vulnerabilities or NVIDIA AI Concerns
[here](https://www.nvidia.com/en-us/support/submit-security-vulnerability/).50:T541,| Field | Response |
|-------|----------|
| Intended Task/Domain: | Speech Enhancement |
| Model Type:                    | Background Noise Removal |
| Intended Users:                | Automatic Speech Recognition and Video Conference System Developers |
| Output:                        | Audio |
| Describe how the model works:  | This model segments out the background noises from the input noisy audio, retaining only speech for better intelligibility and improved ASR accuracy. |
| Name the adversely impacted groups this has been tested to deliver comparable outcomes regardless of: | Age (18+), Gender |
| Verified to have met prescribed NVIDIA quality standards: | Yes |
| Performance Metrics:                | Scale Invariant Signal-to-Noise Ratio Improvement (SI-SNRi), Virtual Speech Quality Objective Listener (VISQOL), Perceptual Evaluation of Speech Quality (PESQ), Latency, Throughput. |
| Technical Limitations & Mitigation: | The model may not handle noises below 5dB or lower SNR. While the model can also work for other types of noises and at lower SNRs, the output speech quality could vary. |
| Potential Known Risks: | The model may not detect and filter out all audio background noises. |
| Licensing: | [NVIDIA Open Model License](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license/) |51:T570,| Field | Response |
|-------|----------|
| Generatable or reverse engineerable personal data? | No             |
| Personal data used to create this model?           | Yes            |
| Was consent obtained for any personal data used?   | Yes            |
| How often is dataset reviewed?                     | Before Release |
| Is a mechanism in place to honor data subject right of access or deletion of personal data?       | Yes |
| If personal data collected for the development of the model, was it collected directly by NVIDIA? | Yes, for some training data |
| If personal data collected for the development of the model by NVIDIA, do you maintain or have access to disclosures made to data subjects? | Yes |
| If personal data collected for the development of this AI model, was it minimized to only what was required? | Yes |
| Was data from user interactions with the AI model (e.g. user input and prompts) used to train the model?     | No |
| Is there provenance for all datasets used in training?              | Yes |
| Does data labeling (annotation, metadata) comply with privacy laws? | Yes |
| Is data compliant with data subject requests for data correction or removal, if such a request was made? | No, not possible with externally-sourced data. Yes, for Nvidia collected data. |
| Applicable Privacy Policy | https://www.nvidia.com/en-us/about-nvidia/privacy-policy/ |49:[["$","div",".3",{"className":"relative","children":[["$","div",null,{"className":"relative flex min-h-[194px] w-full flex-col overflow-hidden p-md sm:p-ml bg-manitoulinLightBlack","children":[["$","$L4c",null,{"alt":"","className":"object-cover object-center !left-1/2 z-10 !w-1/2 brightness-20 lg:brightness-75","fill":true,"priority":true,"src":"https://assets.ngc.nvidia.com/products/api-catalog/images/bnr.jpg","style":{"maskImage":"linear-gradient(to left, rgba(0,0,0,1), rgba(0,0,0,0))"}}],["$","div",null,{"className":"z-30 mx-auto flex w-full max-w-screen-xl min-w-0 flex-1 flex-col items-start justify-between gap-md lg:flex-row lg:gap-ml","children":["$","section",null,{"aria-describedby":"resource-description","aria-labelledby":"resource-name","className":"flex w-full min-w-0 flex-col lg:flex-1","children":["$","div",null,{"className":"flex flex-col gap-1.5 whitespace-pre-wrap","children":[["$","$L4d",null,{"className":"w-fit text-ml text-n300 lowercase hover:text-n050","href":"/nvidia","children":"NVIDIA"}],["$","div",null,{"className":"flex flex-col items-start gap-3 lg:flex-row lg:items-center","children":[["$","h1",null,{"className":"max-w-full text-lg leading-heading font-medium break-words text-primary","data-testid":"resource-name","id":"resource-name","children":"Background Noise Removal"}],["$","$L4e",null,{"artifact":{"artifactType":"ENDPOINT","name":"bnr","displayName":"Background Noise Removal","publisher":"nvidia","shortDescription":"Removes unwanted noises from audio improving speech intelligibility.","logo":"https://assets.ngc.nvidia.com/products/api-catalog/images/bnr.jpg","labels":["communications","denoising","nimType:endpoint:nim_type_preview","nimType:endpoint:nim_type_run_anywhere","nvidia ai for media","speech enhancement"],"attributes":[{"key":"AVAILABLE","value":"true"},{"key":"PREVIEW","value":"true"},{"key":"last_month_api_invocation_count","value":"1240"},{"key":"last_month_download_count","value":"0"}],"updatedDate":"2025-06-13T17:42:41.479Z","bias":"Field                                                                                               |  Response\n:---------------------------------------------------------------------------------------------------|:---------------\nParticipation considerations from adversely impacted groups [protected classes](https://calcivilrights.ca.gov/disputeresolution/protected-characteristics/) in model design and testing:  |  Age (18+), Gender\nMeasures taken to mitigate against unwanted bias:                                                   |  Evaluated using internal, proprietary data mix to achieve similar key performance indicators.","canGuestDownload":true,"createdDate":"2025-06-12T23:23:23.819Z","description":"$4f","explainability":"$50","isPublic":true,"isReadOnly":true,"orgName":"qc69jvmznzxy","privacy":"$51","safetyAndSecurity":"| Field | Response |\n|-------|----------|\n| Model Application(s):                             | Audio Denoising |\n| Describe the life critical impact (if present):   | Not Applicable |\n| Use Case Restrictions:                            | Abide by [NVIDIA Open Model License](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license/). |\n| Model and dataset restrictions:                   | The Principle of Least Privilege (PoLP) is applied limiting access for dataset generation and model development. Restrictions enforce dataset access during training, and dataset license constraints adhered to. |"}}],"$undefined"]}],"$L52","$L53"]}]}]}],"$L54"]}],"$L55"]}]]
57:T989,## Getting Started

NVIDIA Background Noise Removal NIM uses gRPC APIs for inferencing requests. Following instructions demonstrate the usage of BNR NIM model using Python client.

### Prerequisites

You will need a system with `git` and `Python 3.10+` installed.

### Setup NVIDIA BNR Python client

Download the BNR Python client code by cloning the [NIM gRPC Client Repository](https://github.com/NVIDIA-Maxine/nim-clients):

```bash
git clone https://github.com/NVIDIA-Maxine/nim-clients.git
cd nim-clients/bnr
```

Install the dependencies for the NVIDIA BNR Python client:

```bash
sudo apt-get install python3-pip
pip install -r requirements.txt
```

### Run Python Client

Navigate to the scripts directory.

```bash
cd scripts
```

Send the gRPC requests

```bash
python bnr.py --preview-mode \
    --ssl-mode TLS \
    --target grpc.nvcf.nvidia.com:443 \
    --function-id <%- nvcfFunctionId %> \
    --api-key <%- apiKey %> \
    --input <input_file_path> \
    --output <output_file_path> \
    --streaming False
```

Note the requirements for input file:

- The supported format is 16-bit mono channel wav file.
- The size limit for input file is 35 MB.
- The duration limit for input file is 6 min.

Command line arguments:

- `--preview-mode`     - Flag to send request to preview NVCF server on https://build.nvidia.com/nvidia/bnr/api.
- `--ssl-mode`         - Set the SSL mode to TLS or MTLS. Defaults to no SSL. When running preview, TLS mode must be used with default root certificate.
- `--target <ip:port>` - URI of NIM's gRPC service. Use grpc.nvcf.nvidia.com:443 when hosted on NVCF. (Default: `127.0.0.1:8001`)
- `--api-key <%- apiKey %>` - NGC API key required for authentication. Utilized when using `TRY API` ignored otherwise.
- `--function-id <function_id>` - Function ID for the feature.
- `--input <input_file_path>` - The path to the input audio file. (Default: `../assets/bnr_48k_input.wav`)
- `--output <output_file_path>` - The path to the output audio file. (Default: `./bnr_48k_output.wav`)
- `--streaming` - Flag to control if streaming or transactional mode should be used. Streaming mode will be used by default, set to False to enable transactional mode.
- `--intensity-ratio` - Intensity ratio value between 0 and 1 to control denoising intensity. Default is 1.0 (maximum denoising).

Refer the [BNR NIM documentation](https://docs.nvidia.com/nim/maxine/bnr/latest/index.html) for more information.
58:T1654,## Step 1. Generate API Key

::generate-api-key

## Step 2. Pull and Run the NIM

```bash
$ docker login nvcr.io
Username: $oauthtoken
Password: <PASTE_API_KEY_HERE>
```

NVIDIA BNR NIM uses gRPC APIs for inferencing requests.

A NGC API KEY is required to download the appropriate models and resources when starting the NIM.

If you are not familiar with how to create the `NGC_API_KEY` environment variable, the simplest way is to export it in your terminal:

```bash
export NGC_API_KEY=<PASTE_API_KEY_HERE>
```

Run one of the following commands to make the key available at startup:

```bash
# If using bash
echo "export NGC_API_KEY=<value>" >> ~/.bashrc

# If using zsh
echo "export NGC_API_KEY=<value>" >> ~/.zshrc
```

Other, more secure options include saving the value in a file, so that you can retrieve with `cat $NGC_API_KEY_FILE`, or using a [password manager](https://www.passwordstore.org/).

The following command launches the BNR NIM container with the gRPC service. Find reference to runtime parameters for the container [here](https://docs.nvidia.com/nim/maxine/bnr/latest/getting-started.html#runtime-parameters-for-the-container).

```bash
docker run -it --rm --name=bnr \
  --runtime=nvidia \
  --gpus all \
  --shm-size=8GB \
  -e NGC_API_KEY=$NGC_API_KEY \
  -e NIM_MAX_CONCURRENCY_PER_GPU=8 \
  -e NIM_MODEL_PROFILE=<nim_model_profile> \
  -e FILE_SIZE_LIMIT=36700160 \
  -p 8000:8000 \
  -p 8001:8001 \
  nvcr.io/nim/nvidia/bnr:latest
```

Ensure you use the appropriate `NIM_MODEL_PROFILE` for your GPU. For more information about `NIM_MODEL_PROFILE`, refer to the the [NIM Model Profile Table](https://docs.nvidia.com/nim/maxine/bnr/latest/model-profile-table.html).

Please note, the flag --gpus all is used to assign all available GPUs to the docker container. This fails on multiple GPU unless all GPUs are same. To assign specific GPU to the docker container (in case of different multiple GPUs available in your machine) use --gpus '"device=0,1,2..."'

If the command runs successfully, you will get an output ending similar to the following:

```bash
I0415 05:25:07.343449 100 grpc_server.cc:2560] "Started GRPCInferenceService at 127.0.0.1:9001"
I0415 05:25:07.343632 100 http_server.cc:4822] "Started HTTPService at 127.0.0.1:9000"
I0415 05:25:07.384715 100 http_server.cc:358] "Started Metrics Service at 127.0.0.1:9002"
[INFO AI4M BASE LOGGER 2026-04-15 05:25:09.012 PID:176] Listening to 0.0.0.0:8001
```

By default BNR gRPC service is hosted on port `8001`. You will have to use this port for inferencing requests.

## Step 3. Test the NIM

We have provided a sample client script file in our GitHub repo.
The script could be used to invoke the Docker container using the following instructions.

Download the BNR Python client code by cloning the [NIM gRPC client Repository](https://github.com/NVIDIA-Maxine/nim-clients):

```bash
git clone https://github.com/NVIDIA-Maxine/nim-clients
cd nim-clients/bnr
```

Install the dependencies for the NVIDIA BNR Python client:

```bash
sudo apt-get install python3-pip
pip install -r requirements.txt
```

Go to scripts directory

```bash
cd scripts
```

Run the command to send a gRPC request (By Default streaming mode):

```bash
python bnr.py --target <target_ip:port> --input <input_file_path> --output <output_file_path>
```

For transactional mode:

```bash
python bnr.py --target <target_ip:port> --input <input_file_path> --output <output_file_path> --streaming False --sample-rate 48000
```

Ensure that the selected `--sample-rate` (48000, 16000) aligns with the `NIM_MODEL_PROFILE` model type configuration to maintain compatibility.
eg: if `--sample-rate` is 48000, then `NIM_MODEL_PROFILE` with model type v1-48k, v2-48k needs to be selected.

To view details of command line arguments run this command

```bash
python bnr.py -h
```

You will get a response similar to the following.

```bash
usage: bnr.py [-h] [--ssl-mode {MTLS,TLS}] [--ssl-key SSL_KEY] [--ssl-cert SSL_CERT] [--ssl-root-cert SSL_ROOT_CERT] [--target TARGET]
                       [--input INPUT] [--output OUTPUT] [--api-key API_KEY] [--function-id FUNCTION_ID] [--streaming] [--sample-rate {48000, 16000}]

Process wav audio files using gRPC and apply bnr.

options:
  -h, --help            show this help message and exit
  --preview-mode        Flag to send request to preview NVCF server on https://build.nvidia.com/nvidia/bnr/api.
  --ssl-mode {MTLS,TLS}
                        Flag to set SSL mode, default is None
  --ssl-key SSL_KEY     The path to ssl private key.
  --ssl-cert SSL_CERT   The path to ssl certificate chain.
  --ssl-root-cert SSL_ROOT_CERT
                        The path to ssl root certificate.
  --target TARGET       IP:port of gRPC service, when hosted locally. Use grpc.nvcf.nvidia.com:443 when hosted on NVCF.
  --input INPUT         The path to the input audio file.
  --output OUTPUT       The path for the output audio file.
  --api-key API_KEY     NGC API key required for authentication, utilized when using TRY API ignored otherwise
  --function-id FUNCTION_ID
                        NVCF function ID for the service, utilized when using TRY API ignored otherwise
  --streaming           Streaming mode is enabled by default. Set --streaming False to enable transactional mode.
  --sample-rate {48000, 16000}
                        Sample rate of input audio file in Hz, default is 48000.
  --intensity-ratio     Intensity ratio value between 0 and 1 to control denoising intensity. Default is 1.0 (maximum denoising).
```

For more details on getting started with this NIM including configuring using parameters, visit the [NVIDIA BNR NIM Docs](https://docs.nvidia.com/nim/maxine/bnr/latest/index.html).
4a:["$","$L56",null,{"spec":{"namespace":"qc69jvmznzxy","updatedDate":"2026-08-05T18:59:17.326Z","nvcfFunctionId":"c95bfe76-c553-4975-bc18-8ef9d6e2666b","createdDate":"2025-06-12T23:23:24.030Z","attributes":{"apiDocsUrl":"https://docs.nvidia.com/nim/maxine/bnr/latest/overview.html","termsOfUse":"<b>GOVERNING TERMS</b>: This trial service is governed by the <a href=\"https://assets.ngc.nvidia.com/products/api-catalog/legal/NVIDIA%20API%20Trial%20Terms%20of%20Service.pdf\" rel=\"noreferrer\" target=\"_blank\">NVIDIA API Trial Terms of Service</a>. Use of this model is governed by the <a href=\"https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license/\" rel=\"noreferrer\" target=\"_blank\">NVIDIA Open Model License Agreement</a>.\n","showUnavailableBanner":false,"cta":{"text":"Apply to Self-Host","url":"https://www.nvidia.com/en-us/ai/nim-notifyme/","nim_available_override_url":"https://catalog.ngc.nvidia.com/orgs/nim/teams/nvidia/containers/bnr"},"usage":"$57","deploy":[{"label":"Linux with Docker","filename":"linux.md","contents":"$58"}],"modelCapability":{"functionCalling":false}},"artifactName":"bnr"}}]
59:I[299632,["/_next/static/chunks/04d712ydf7vwt.js","/_next/static/chunks/3ibd-wdn1muo9.js","/_next/static/chunks/1q5xb__jylra0.js","/_next/static/chunks/1z_-bqrzptsiz.js","/_next/static/chunks/1la1pzs9j8idc.js","/_next/static/chunks/00eq9bqnkbpfo.js","/_next/static/chunks/1tjzqakl0-ac_.js","/_next/static/chunks/3r5yd4k4rms8-.js","/_next/static/chunks/1qasf48lwbczr.js","/_next/static/chunks/0iqwvdhi-o1pr.js","/_next/static/chunks/3-dupjzg004ft.js","/_next/static/chunks/1p8p6uesfmfc2.js","/_next/static/chunks/3c_tmnbt9nfb3.js","/_next/static/chunks/2lofudtwqsrwt.js","/_next/static/chunks/36qm3961yv116.js","/_next/static/chunks/342zpu2i9tat1.js","/_next/static/chunks/2tmwf_2axyd0y.js","/_next/static/chunks/3v9fr1qimf7lj.js","/_next/static/chunks/364lrnu5opng7.js","/_next/static/chunks/3kdaun3epyv7g.js","/_next/static/chunks/13fah1s8gxrn0.js","/_next/static/chunks/2tkz_ff5gjl4a.js","/_next/static/chunks/2_n0f-hh3ea4l.js","/_next/static/chunks/0czpc-f8wjri8.js","/_next/static/chunks/3761ezb6xysq0.js","/_next/static/chunks/24_gg9g_4g22i.js","/_next/static/chunks/1_3y3ily4zuo1.js","/_next/static/chunks/1a2o19d1j4nvx.js","/_next/static/chunks/1kci6kpi29km9.js","/_next/static/chunks/1hhq3s9jcti5r.js","/_next/static/chunks/2mr_uzqfq-mid.js","/_next/static/chunks/3o73dbhryidg8.js","/_next/static/chunks/278imbrkq3abd.js","/_next/static/chunks/2xuup_ncbht_q.js","/_next/static/chunks/1q5ewy8bee9p6.js","/_next/static/chunks/2pqhypz2vo8mu.js","/_next/static/chunks/2960tspz292yr.js","/_next/static/chunks/00jw9q5dp3jlz.js","/_next/static/chunks/3eoelf0hi5x-3.js","/_next/static/chunks/0tqq_6ft6mlt2.js"],"default"]
5a:I[400402,["/_next/static/chunks/04d712ydf7vwt.js","/_next/static/chunks/3ibd-wdn1muo9.js","/_next/static/chunks/1q5xb__jylra0.js","/_next/static/chunks/1z_-bqrzptsiz.js","/_next/static/chunks/1la1pzs9j8idc.js","/_next/static/chunks/00eq9bqnkbpfo.js","/_next/static/chunks/1tjzqakl0-ac_.js","/_next/static/chunks/3r5yd4k4rms8-.js","/_next/static/chunks/1qasf48lwbczr.js","/_next/static/chunks/0iqwvdhi-o1pr.js","/_next/static/chunks/3-dupjzg004ft.js","/_next/static/chunks/1p8p6uesfmfc2.js","/_next/static/chunks/3c_tmnbt9nfb3.js","/_next/static/chunks/2lofudtwqsrwt.js","/_next/static/chunks/36qm3961yv116.js","/_next/static/chunks/342zpu2i9tat1.js","/_next/static/chunks/2tmwf_2axyd0y.js","/_next/static/chunks/3v9fr1qimf7lj.js","/_next/static/chunks/364lrnu5opng7.js","/_next/static/chunks/3kdaun3epyv7g.js","/_next/static/chunks/13fah1s8gxrn0.js","/_next/static/chunks/2tkz_ff5gjl4a.js","/_next/static/chunks/2_n0f-hh3ea4l.js","/_next/static/chunks/0czpc-f8wjri8.js","/_next/static/chunks/3761ezb6xysq0.js","/_next/static/chunks/24_gg9g_4g22i.js","/_next/static/chunks/1_3y3ily4zuo1.js","/_next/static/chunks/1a2o19d1j4nvx.js","/_next/static/chunks/1kci6kpi29km9.js","/_next/static/chunks/1hhq3s9jcti5r.js","/_next/static/chunks/2mr_uzqfq-mid.js","/_next/static/chunks/3o73dbhryidg8.js","/_next/static/chunks/278imbrkq3abd.js","/_next/static/chunks/2xuup_ncbht_q.js","/_next/static/chunks/1q5ewy8bee9p6.js","/_next/static/chunks/2pqhypz2vo8mu.js","/_next/static/chunks/2960tspz292yr.js","/_next/static/chunks/00jw9q5dp3jlz.js","/_next/static/chunks/3eoelf0hi5x-3.js","/_next/static/chunks/0tqq_6ft6mlt2.js"],"EndpointCTA"]
5b:I[331699,["/_next/static/chunks/04d712ydf7vwt.js","/_next/static/chunks/3ibd-wdn1muo9.js","/_next/static/chunks/1q5xb__jylra0.js","/_next/static/chunks/1z_-bqrzptsiz.js","/_next/static/chunks/1la1pzs9j8idc.js","/_next/static/chunks/00eq9bqnkbpfo.js","/_next/static/chunks/1tjzqakl0-ac_.js","/_next/static/chunks/3r5yd4k4rms8-.js","/_next/static/chunks/1qasf48lwbczr.js","/_next/static/chunks/0iqwvdhi-o1pr.js","/_next/static/chunks/3-dupjzg004ft.js","/_next/static/chunks/1p8p6uesfmfc2.js","/_next/static/chunks/3c_tmnbt9nfb3.js","/_next/static/chunks/2lofudtwqsrwt.js","/_next/static/chunks/36qm3961yv116.js","/_next/static/chunks/342zpu2i9tat1.js","/_next/static/chunks/2tmwf_2axyd0y.js","/_next/static/chunks/3v9fr1qimf7lj.js","/_next/static/chunks/364lrnu5opng7.js","/_next/static/chunks/3kdaun3epyv7g.js","/_next/static/chunks/13fah1s8gxrn0.js","/_next/static/chunks/2tkz_ff5gjl4a.js","/_next/static/chunks/2_n0f-hh3ea4l.js","/_next/static/chunks/0czpc-f8wjri8.js","/_next/static/chunks/3761ezb6xysq0.js","/_next/static/chunks/24_gg9g_4g22i.js","/_next/static/chunks/1_3y3ily4zuo1.js","/_next/static/chunks/1a2o19d1j4nvx.js","/_next/static/chunks/1kci6kpi29km9.js","/_next/static/chunks/1hhq3s9jcti5r.js","/_next/static/chunks/2mr_uzqfq-mid.js","/_next/static/chunks/3o73dbhryidg8.js","/_next/static/chunks/278imbrkq3abd.js","/_next/static/chunks/2xuup_ncbht_q.js","/_next/static/chunks/1q5ewy8bee9p6.js","/_next/static/chunks/2pqhypz2vo8mu.js","/_next/static/chunks/2960tspz292yr.js","/_next/static/chunks/00jw9q5dp3jlz.js","/_next/static/chunks/3eoelf0hi5x-3.js","/_next/static/chunks/0tqq_6ft6mlt2.js"],"ModelContent"]
5c:I[122761,["/_next/static/chunks/04d712ydf7vwt.js","/_next/static/chunks/3ibd-wdn1muo9.js","/_next/static/chunks/1q5xb__jylra0.js","/_next/static/chunks/1z_-bqrzptsiz.js","/_next/static/chunks/1la1pzs9j8idc.js","/_next/static/chunks/00eq9bqnkbpfo.js","/_next/static/chunks/1tjzqakl0-ac_.js","/_next/static/chunks/3r5yd4k4rms8-.js","/_next/static/chunks/1qasf48lwbczr.js","/_next/static/chunks/0iqwvdhi-o1pr.js","/_next/static/chunks/3-dupjzg004ft.js","/_next/static/chunks/1p8p6uesfmfc2.js","/_next/static/chunks/3c_tmnbt9nfb3.js","/_next/static/chunks/2lofudtwqsrwt.js","/_next/static/chunks/36qm3961yv116.js","/_next/static/chunks/342zpu2i9tat1.js","/_next/static/chunks/2tmwf_2axyd0y.js","/_next/static/chunks/3v9fr1qimf7lj.js","/_next/static/chunks/364lrnu5opng7.js","/_next/static/chunks/3kdaun3epyv7g.js","/_next/static/chunks/13fah1s8gxrn0.js","/_next/static/chunks/2tkz_ff5gjl4a.js","/_next/static/chunks/2_n0f-hh3ea4l.js","/_next/static/chunks/0czpc-f8wjri8.js","/_next/static/chunks/3761ezb6xysq0.js","/_next/static/chunks/24_gg9g_4g22i.js","/_next/static/chunks/1_3y3ily4zuo1.js","/_next/static/chunks/1a2o19d1j4nvx.js","/_next/static/chunks/1kci6kpi29km9.js","/_next/static/chunks/1hhq3s9jcti5r.js","/_next/static/chunks/2mr_uzqfq-mid.js","/_next/static/chunks/3o73dbhryidg8.js","/_next/static/chunks/278imbrkq3abd.js","/_next/static/chunks/2xuup_ncbht_q.js","/_next/static/chunks/1q5ewy8bee9p6.js","/_next/static/chunks/2pqhypz2vo8mu.js","/_next/static/chunks/2960tspz292yr.js","/_next/static/chunks/00jw9q5dp3jlz.js","/_next/static/chunks/3eoelf0hi5x-3.js","/_next/static/chunks/0tqq_6ft6mlt2.js"],"default"]
52:["$","p",null,{"className":"max-w-[85ch] text-ms text-primary","id":"resource-description","children":"Removes unwanted noises from audio improving speech intelligibility."}]
53:["$","div",null,{"className":"flex w-full flex-col items-start gap-md lg:flex-row lg:items-end lg:justify-between","children":[["$","div",null,{"className":"flex w-full min-w-0 flex-wrap gap-sm lg:flex-1","children":["$","$L59",null,{"artifactType":"ENDPOINT","density":"standard","labels":"$49:0:props:children:0:props:children:1:props:children:props:children:props:children:1:props:children:1:props:artifact:labels","searchRoutePath":"/models"}]}],["$","div",null,{"className":"z-30 flex w-full flex-row justify-start gap-ms sm:justify-end lg:w-auto lg:shrink-0","children":["$undefined",["$","$L5a",null,{"cta":"$4a:props:spec:attributes:cta","isNIMAccessRestricted":"$undefined","isNIMAvailable":true}]]}]]}]
54:["$","div",null,{"className":"pointer-events-none absolute right-0 bottom-0 left-0 z-20 h-30 bg-gradient-to-t to-transparent from-manitoulinLightBlack via-manitoulinLightBlack/70"}]
55:["$","div",null,{"className":"px-4 mx-auto flex max-w-screen-xl flex-col pt-0 lg:px-0","data-body-background":"light-black","children":["$","section",null,{"className":"flex w-full flex-col justify-between rounded-4 border-manitoulinBorderColor bg-manitoulinDarkBlack sm:rounded-6 lg:rounded-8 p-ms lg:p-lg","children":["$","$L5b",null,{"apiReferenceEnabled":false,"artifact":"$49:0:props:children:0:props:children:1:props:children:props:children:props:children:1:props:children:1:props:artifact","endpointName":"bnr","endpointSpec":"$4a:props:spec","isLoginRequired":true,"playgroundElement":"$5c","publisherName":"nvidia","searchParams":{"model":"bnr"},"tabs":[{"label":"Experience","bare":true,"icon":"play","kind":"default","id":"experience","href":"/nvidia/bnr","aliases":["/nvidia/bnr/experience"]},{"label":"Model Card","icon":"book","kind":"default","id":"modelcard","href":"/nvidia/bnr/modelcard","aliases":"$undefined"},{"label":"Try API","kind":"default","id":"api","href":"/nvidia/bnr/api","aliases":"$undefined"},{"label":"Deploy","kind":"default","id":"deploy","href":"/nvidia/bnr/deploy","aliases":"$undefined"}]}]}]}]
