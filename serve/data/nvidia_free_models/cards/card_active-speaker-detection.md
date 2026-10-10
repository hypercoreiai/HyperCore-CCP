:false}]
4f:T711,# Face and Landmark Detector:
Field                                                                                               |  Response
:---------------------------------------------------------------------------------------------------|:---------------
Participation considerations from adversely impacted groups [protected classes](https://www.senate.ca.gov/content/protected-classes) in model design and testing:  |  None
Measures taken to mitigate against unwanted bias:                                                   |  Dataset rebalancing for fair representation of age, gender, race/skin tones

# SyncDiscriminator:
Field                                                                                               |  Response
:---------------------------------------------------------------------------------------------------|:---------------
| Participation considerations from adversely impacted groups [protected classes](https://www.senate.ca.gov/content/protected-classes) in model design and testing: | Age, Gender, Race, Skin color                                                                                                                                                                                                                                                                                     |
| Measures taken to mitigate against unwanted bias:                                                                                                                 | Trained on AVA-ActiveSpeaker dataset which contains diverse demographics from Hollywood movie clips spanning a wide range of ages, genders, races, and skin colors. Evaluated on Columbia ASD dataset with multiple speakers of different backgrounds to verify consistent performance across demographic groups. |50:T6a6f,# Active Speaker Detection

Active Speaker Detection is in fact a combination of multiple models that are used to perform the Active Speaker Detection effect, which processes video and multiple audio track inputs to detect, identify and track speaker identities across video frames. These include the Adaface model, Face and landmark Detector models and the SyncDiscriminator model

This feature and all associated models are available for commercial/non-commercial use.

### Using these models

To download the models, use the feature installation script bundled with the NVIDIA AR SDK (`features/install_feature.[ps1|sh]`). Please refer to the Active Speaker Detection Collection page or the AR SDK Documentation for more details. You can navigate to the collection page by click on the **Related Collections** tab at the top of this page.

### License/Terms of use:

The use of NVIDIA Active Speaker Detection is governed by the [NVIDIA SOFTWARE LICENSE AGREEMENT](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-software-license-agreement/) and [Product-Specific Terms for NVIDIA AI Products](https://www.nvidia.com/en-us/agreements/enterprise-software/product-specific-terms-for-ai-products/).

Please see the additional sections below for each model for the governing terms of their use.

---

## Adaface

### Model Overview
Adaface generates embeddings for identifying people captured in different scenes. This model does not include biometric data.

### License/Terms of use
Use of the Adaface model is governed by the [NVIDIA Open Model License]( https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license/).  Additional Information: [MIT](https://github.com/mk-minchul/AdaFace/blob/master/LICENSE).

### Third-Party Community Consideration:
This model is not owned or developed by NVIDIA. This model has been developed and built to a third-party's requirements for this application and use case; see link to Non-NVIDIA model card here: [CVLFace Adaface IR101 WebFace12M](https://huggingface.co/minchul/cvlface_adaface_ir101_webface12m).

### Deployment Geography:

Global

### Use Case:

- Generates embeddings for identifying people captured in different scenes for video dubbing
- Based on ResNet101 architecture with Additive Angular Margin Loss
- Optimized for minimal computational overhead
- Supports various demographics, lighting conditions, and image qualities
- Produces 512-dimensional face embeddings for identification tasks
- Compatible with InsightFace framework, replaces ArcFace/AuraFace model

### Release Date:
HuggingFace [repo](https://huggingface.co/minchul/cvlface_adaface_ir101_webface12m) June 5, 2024

NGC: 03/12/2026 - TensorRT optimized

### References

- **Paper:** [AdaFace: Quality Adaptive Margin for Face Recognition](https://arxiv.org/abs/2204.00964)
- **HuggingFace:** [Adaface IR101 WebFace12M](https://huggingface.co/minchul/cvlface_adaface_ir101_webface12m)

## Model Architecture

### Architecture Type
**Convolutional Neural Network (CNN)**

### Network Architecture
- **Backbone:** IResNet101
- **Loss Function:** Additive Angular Margin Loss (ArcFace)
- **Embedding Dimension:** 512-dimensional face embeddings
- **Framework:** ONNX format compatible with InsightFace ArcFace, TensorRT optimized
- **Number of model parameters:** 65.2M

## Input

### Input Type
Image

### Input Format
- **Color Space:** RGB (Red, Green, Blue)
- **Image Dimensions:** 112x112 pixels
- **Data Type:** float32 (normalized)

### Input Parameters
- **Batch Size:** Configurable (1 or more)
- **Image:** Two-Dimensional (2D)
- **Channels:** 3 (BGR)
- **layout:** NHWC

### Preprocessing Requirements
1. Face detection and alignment
2. Cropping to standard size (112x112)
3. Normalization to [0, 1] range

### Other Properties Related to Input
- Input images should contain a single face, properly aligned
- Images with multiple faces should be preprocessed to identify individual faces
- Optimal performance with well-lit, frontal face images
- Model can handle various lighting conditions and poses due to training data diversity

## Output

### Output Type
Embedding Vector

### Output Format
- **Embedding Dimension:** 512-dimensional normalized feature vector
- **Data Type:** float32
- **Normalization:** L2-normalized (unit vector)

### Output Parameters
- **Shape:** [batch_size, 512]

### Other Properties Related to Output
- Output embeddings can be compared using cosine similarity or Euclidean distance
- Typical similarity threshold for same person: >0.5 (cosine similarity)
- Embeddings are designed to cluster faces of the same identity closely in feature space
- Can be used for face verification, identification, and clustering tasks

## Training & Evaluation Data

### Training Dataset

#### Dataset Sources
The model was trained on a commercial dataset comprising face images from various publicly available and licensed sources:
- Commercially licensed face datasets
- Publicly available face identification benchmarks

#### Dataset Characteristics
AdaFace was trained on a commercial dataset comprising face images from various sources, including synthetic images. The dataset includes a wide range of demographics, lighting conditions, and image qualities to ensure robust performance across different scenarios.

- Data Collection Method:
  - Hybrid: Synthetic, Undisclosed
- Labeling Method: Undisclosed

#### Data Preprocessing
- **Normalization:** All images were normalized to standard size and format
- **Augmentation:** Rotation, flipping, and scaling were used to improve generalization
- **Face Alignment:** All training faces were detected and aligned using standard landmarks

#### Dataset Limitations
Due to commercial licensing requirements, the training dataset may not extensively cover all global ethnicities and demographic groups. Users should conduct their own assessments to confirm the model's performance in their specific application context.

### Evaluation Benchmarks

AdaFace has been tested on multiple face recognition benchmarks:

- LFW: 0.99650
- CFP-FP: 0.95186
- AGEDB: 0.96100
- CALFW: 0.94700
- CPLFW: 0.90933

## Intended Use

### Primary Use Cases

**Media and Entertainment**
   - Face-based search in media libraries
   - Content personalization

### Bias and Fairness

#### Known Limitations
- **Demographic Representation:** The training dataset attempts to include diverse demographics, but may have limited representation of certain ethnicities due to dataset availability and commercial licensing constraints
- **Performance Variation:** Model efficacy in identity preservation may vary based on ethnicity, age, gender, and other demographic factors
- **Lighting Sensitivity:** Performance may degrade in extreme lighting conditions not well-represented in training data

#### Mitigation Efforts
- Training data included diverse demographics, lighting conditions, and image qualities
- Continuous monitoring and evaluation across demographic groups
- Open-source release to enable community testing and feedback
- Commercial licensing ensures proper data usage rights

#### Fairness Considerations
Efforts have been made to ensure that AdaFace performs equitably across different demographic groups. However, users should:
- Conduct their own fairness assessments in their specific application context
- Test model performance across relevant demographic groups for their use case
- Implement appropriate thresholds and decision-making processes
- Monitor for bias in production deployments

### Privacy Considerations

#### Data Privacy
- AdaFace characterizes faces, which is considered sensitive personal information in many jurisdictions
- Users must ensure compliance with relevant privacy laws (GDPR, CCPA, BIPA, etc.)
- Implement appropriate data protection measures (encryption, access controls)
- Obtain necessary consent from individuals whose faces are processed

#### Recommendations
- Store face embeddings rather than raw images when possible
- Provide transparency to users about face identification usage
- Enable user consent and opt-out mechanisms
- Conduct Privacy Impact Assessments (PIA) for your application

### Security Considerations

#### Potential Vulnerabilities
- **Presentation Attacks:** The model may be vulnerable to spoofing attacks using photos, videos, or masks (requires additional liveness detection)
- **Adversarial Attacks:** Like all neural networks, the model may be susceptible to adversarial perturbations
- **Model Extraction:** Publicly available model weights could be subject to model stealing attacks

#### Security Best Practices
- Implement liveness detection for security-critical applications
- Use multi-factor authentication rather than face identication alone for high-security scenarios
- Monitor for unusual patterns or potential attacks
- Keep model and dependencies updated
- Implement proper access controls for model deployment

## Limitations and Recommendations

### Known Limitations

1. **Generalization:** The model's generalization is limited by the scope of the training data
2. **Perfect Accuracy:** The model does not achieve perfect photorealism and identity consistency in all cases
3. **Demographic Variance:** Performance may vary across different demographic groups
4. **Environmental Conditions:** Extreme lighting, poses, or occlusions may reduce accuracy
5. **Performance Gap:** Does not match the performance of the original ArcFace due to smaller commercial training dataset
6. **Real-time Requirements:** May require GPU acceleration for real-time applications with high throughput

### Recommendations for Users

1. **Validation:** Conduct thorough testing in your specific deployment environment
2. **Threshold Tuning:** Adjust similarity thresholds based on your use case
3. **Demographic Testing:** Test across relevant demographic groups for your application
4. **Liveness Detection:** Implement additional liveness detection for security applications
5. **Monitoring:** Continuously monitor model performance in production
6. **Legal Compliance:** Ensure compliance with all relevant regulations (GDPR, CCPA, BIPA, etc.)
7. **Human Oversight:** Implement human review for high-stakes decisions
8. **Feedback Loop:** Establish mechanisms to collect and address user feedback

### Performance Optimization Tips

- Use GPU inference for batch processing and real-time applications
- Implement face detection caching for video streams
- Optimize image preprocessing pipeline
- Use TensorRT for additional performance gains on NVIDIA hardware
- Consider model quantization (FP16, INT8) for edge deployment

## Model Governance

### Model Maintenance
- **Updates:** The model is currently at version 1.0, with community feedback guiding future improvements
- **Issue Reporting:** Users can report issues on the HuggingFace model page or GitHub repository
- **Community Contributions:** The open-source nature enables community improvements and extensions

### Compliance and Regulations
Users are responsible for ensuring their use of AdaFace complies with:
- Local and international privacy laws (GDPR, CCPA, BIPA, etc.)
- Biometric data regulations
- Industry-specific requirements
- Ethical AI guidelines

## Changelog and Versioning

### Version 1.0 (Initial Release)
- ResNet101 architecture with Additive Angular Margin Loss
- Trained on commercially available face datasets
- ONNX format for broad framework compatibility
- Compatible with InsightFace framework, replaces ArcFace

## Contact and Support

### Model Developers
- **Organization:** Minchul Kim
- **Contributors:** @minchul
- **HuggingFace:** [minchul/cvlface_adaface_ir101_webface12m](https://huggingface.co/minchul/cvlface_adaface_ir101_webface12m)

## Additional Resources

### Documentation
- [AdaFace Paper](https://arxiv.org/abs/2204.00964)
- [Model Weights on HuggingFace](https://huggingface.co/minchul/cvlface_adaface_ir101_webface12m)

### Citations
If you use AdaFace in your research or applications, please cite:

```bibtex
@misc{adaface2022,
  title={AdaFace: Quality Adaptive Margin for Face Recognition},
  author={Minchul Kim, Anil K. Jain, Xiaoming Liu},
  year={2022},
  howpublished={\url{https://arxiv.org/abs/2204.00964}}
}

@inproceedings{deng2019arcface,
  title={Arcface: Additive angular margin loss for deep face recognition},
  author={Deng, Jiankang and Guo, Jia and Xue, Niannan and Zafeiriou, Stefanos},
  booktitle={Proceedings of the IEEE/CVF conference on computer vision and pattern recognition},
  pages={4690--4699},
  year={2019}
}
```

---

## Face and Landmarks Detector (FLD)

### Model Overview

The Face and Landmarks Detector (FLD) is a high-performance face detection and facial landmark localization model based on the SCRFD (Sample and Computation Redistribution for Face Detection) architecture. SCRFD is an efficient face detector with landmark localization capabilities, designed for real-time performance while maintaining high accuracy. The model simultaneously detects faces and predicts facial keypoints, making it ideal for comprehensive facial analysis pipelines.

### License/Terms of Use:

GOVERNING TERMS: Use of this model is governed by the [NVIDIA Open Model License](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license/).

### Deployment Geography:

Global

### Use Case:
### Primary Applications

- **Facial Recognition Pipelines:** Face detection and landmark extraction as preprocessing for recognition/verification
- **Face Alignment:** Landmark-based face normalization for downstream tasks
- **Facial Expression Analysis:** Face detection with keypoints for emotion recognition
- **Video Analytics:** Real-time face and landmark detection in video streams
- **Media Organization:** Automated face detection with alignment for media libraries

### Supported Domains

- Broadcasting and media production
- Entertainment
- Human-Computer Interaction

## Release Date:
03/12/2026

## Model Architecture

### Architecture Details

- **Backbone:** ResNet-inspired efficient backbone
- **Detection Framework:** SCRFD (Sample and Computation Redistribution for Face Detection)
- **Detection Method:** Anchor-free detection with stride-based feature pyramids
- **Feature Pyramid Network:** Multi-scale feature extraction
- **Landmark Prediction:** 5-point facial landmarks (two eyes, nose, two mouth corners)
- **Number of model parameters:** 3.9 million (10 GFLOPS variant)

### SCRFD Architecture Highlights

- **Sample Redistribution:** Efficient positive/negative sample assignment strategy
- **Computation Redistribution:** Optimized computation allocation across detection heads
- **Anchor-Free Design:** Direct prediction without predefined anchors
- **Multi-Task Learning:** Simultaneous face detection and landmark localization

## Input(s):
**Input Type:** Image

**Input Format:**
- Input name: `input_image`
- Color format: Red, Green, Blue (RGB)
- Data type: fp32, fp16
- Shape: [1, 3, 640, 640] (NCHW format)

**Input Parameters:**
- Image: Two-Dimensional (2D) (width, height) = (640, 640)
- Pre-processing:
  - Division by 255.0
  - Resize image to (640, 640) using bilinear interpolation, preserve aspect ratio, zero-padding
  - Mean normalization: [127.5, 127.5, 127.5]
  - Standard deviation: [128.0, 128.0, 128.0]

## Output(s)

**Output Type(s):**
For each detected face:
- Bounding boxes (x1, y1, x2, y2) in image space
- Confidence score
- 5 facial landmarks (x, y coordinates for each keypoint: eye centers, nose, mouth corners)

**Output Format(s):**
- Bounding Box: 4 fp32/fp16 values per detection
- Confidence score: 1 fp32/fp16 value per detection
- Landmarks: 10 fp32/fp16 values per detection (5 points × 2D coordinates)

**Output Parameters:**
- `bboxes`: Nx4 fp32/fp16 array (N detections, 4 coordinates each)
- `scores`: Nx1 fp32/fp16 array (N confidence scores)
- `landmarks`: Nx10 fp32/fp16 array (N detections, 10 landmark coordinates)

### Post-processing

- **Score Thresholding:** Applied to filter low-confidence detections (default: 0.5)
- **Non-Maximum Suppression (NMS):** Applied with default IoU threshold of 0.4
- **Landmark Refinement:** Direct landmark coordinate prediction in image space
- **Optional Face Selection:** Supports limiting detections to top-N faces by confidence or area

# Performance

### Inference Characteristics

- **Optimized Runtime:** TensorRT (NVIDIA), ONNX Runtime
- **Supported Hardware:** NVIDIA GPUs CC 7.5 and up with TensorRT support
- **Precision:** FP32 (supports FP16/INT8 optimization)
- **Typical Latency:** Real-time performance on modern NVIDIA GPUs (~5-10ms on RTX 3080)
- **Memory Footprint:** Lightweight design optimized for edge and datacenter deployment

### Detection Metrics

- **Default Confidence Threshold:** 0.50
- **Default IoU Threshold:** 0.40 (NMS)
- **Detection Capabilities:** Multiple face detection per frame with landmarks
- **Landmark Points:** 5 keypoints (left eye, right eye, nose tip, left mouth corner, right mouth corner)
- **Face Selection Modes:**
  - `max`: Select faces by maximum area
  - `center`: Select faces closest to image center with area weighting

## Limitations

### Known Constraints

- **Occlusion Sensitivity:** Detection and landmark accuracy may degrade with partial face occlusions (masks, sunglasses, hands)
- **Lighting Conditions:** Reduced accuracy in extreme low-light or high-contrast scenarios
- **Face Pose:** Optimized for frontal and near-frontal faces; extreme profile views (>60° yaw) may have lower detection rates and less accurate landmarks
- **Face Size:** Performance varies based on face size in the image; very small faces (<20×20 pixels) may not be detected reliably
- **Landmark Accuracy:** 5-point landmarks are sufficient for alignment but not for detailed facial analysis requiring dense landmarks

### Bias and Fairness Considerations

- Model performance may vary across different demographic groups depending on training data composition
- Users should evaluate model performance on their specific target populations
- Consider using diverse test datasets to assess fairness metrics across age, gender, ethnicity, and skin tone

## Training Data

### Dataset Characteristics

The model has been trained on diverse face detection and landmark datasets including:
- Multiple age groups (children, adults, elderly)
- Various ethnicities and skin tones
- Different lighting conditions (indoor, outdoor, natural, artificial)
- Indoor and outdoor scenarios
- Various face poses and expressions
- Occluded and non-occluded faces

Data Collection Method by dataset
- Hybrid: Human, Synthetic images and videos

Labeling Method by dataset
- Hybrid: Human annotators, Automatic/Sensors

**Note:** Training typically involves publicly available datasets such as WIDER FACE, and additional proprietary datasets.

## Inference
- Acceleration Engine: TensorRT 10.9 - 10.13, ONNX Runtime 1.15+
- Test Hardware: Tesla T4, A100, GeForce RTX 3080, GeForce RTX 4090, L40, GH100, Jetson AGX Orin

## Key Considerations

- **Privacy:** Ensure compliance with applicable privacy laws and regulations (GDPR, CCPA, BIPA, etc.)
- **Consent:** Obtain necessary consent for face detection and biometric data collection in applicable jurisdictions
- **Bias Mitigation:** Regularly evaluate and monitor for demographic performance disparities
- **Transparency:** Inform end-users when face detection and landmark extraction technology is in use
- **Data Retention:** Establish policies for retention and deletion of facial data

## References

### Technical Papers

- **SCRFD:** Guo, J., Deng, J., Lattas, A., & Zafeiriou, S. (2021). "Sample and Computation Redistribution for Efficient Face Detection." *arXiv preprint arXiv:2105.04714*. [Paper Link](https://arxiv.org/abs/2105.04714)

### Related Resources

- [InsightFace GitHub Repository](https://github.com/deepinsight/insightface)
- [InsightFace SCRFD Documentation](https://github.com/deepinsight/insightface/tree/master/detection/scrfd)
- [NVIDIA TensorRT Documentation](https://docs.nvidia.com/deeplearning/tensorrt/)
- [NVIDIA NGC Catalog](https://catalog.ngc.nvidia.com/)
- [NVIDIA AI Enterprise](https://www.nvidia.com/en-us/data-center/products/ai-enterprise/)

### Biometric Data Considerations
This model extracts facial landmarks which may be considered biometric data under certain regulations (e.g., BIPA in Illinois). Users must:
- Obtain informed consent before collecting biometric data
- Clearly disclose the purpose and duration of data storage
- Implement appropriate security measures to protect biometric data
- Provide mechanisms for data subject rights (access, deletion)

---

## SyncDiscriminator

### Model Overview:

The SyncDiscriminator model determines whether a visible person in a video frame is actively speaking, using both audio and visual cues. The model processes face crops from video frames alongside corresponding audio Mel-Frequency Cepstral Coefficient (MFCC) features to produce a per-frame speaking detection score.

This model is ready for commercial/non-commercial use.

### License/Terms of Use

GOVERNING TERMS: Use of this model is governed by the [NVIDIA Open Model License](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license/). Additional Information: [MIT](https://github.com/Junhua-Liao/LR-ASD/blob/main/LICENSE).

### Deployment Geography:

Global

### Use Case:

NVIDIA AR SDK developers building video communication and content creation applications that require identifying which person in a scene is currently speaking.

### Release Date:

NGC - 03/12/2026 via [URL](https://catalog.ngc.nvidia.com/orgs/nvidia/teams/maxine/models/nvaractivespeakerdetection)

### References(s):

* [NVIDIA AR SDK Developer Page](https://developer.nvidia.com/ai-for-media)

## Model Architecture:

**Architecture Type:** Convolutional Neural Network (CNN), Recurrent Neural Network (RNN)

**Network Architecture:** 3D CNN, 2D CNN, Gated Recurrent Unit (GRU)

- This model was developed based on a lightweight audio-visual architecture with separate visual and audio encoders, gated concatenation fusion, and a bidirectional GRU temporal detector.
- Number of model parameters 8.4 x 10^5

## Input(s):

**Input Type(s):** Video (Face Crops), Audio

**Input Format(s):**

- Video: Grayscale
- Audio: MFCC (Mel-Frequency Cepstral Coefficients)

**Input Parameters:**

- Video: Three-Dimensional (3D)
- Audio: Two-Dimensional (2D)

**Other Properties Related to Input:** Video: Grayscale face crops resized to 112x112 pixels with zero-centered pixel intensity normalization; variable length up to 6 seconds, variable frame rates supported. Audio: MFCC coefficients extracted to yield 4 MFCC frames per video frame.

## Output(s):

**Output Type(s):** Score

**Output Format(s):**

- Float32

**Output Parameters:**

- One-Dimensional (1D)

**Other Properties Related to Output:** Per-frame active speaker detection score (raw logit). A score greater than 0.0 indicates the person is speaking. One score is produced per input video frame.

Our AI models are designed and/or optimized to run on NVIDIA GPU-accelerated systems. By leveraging NVIDIA's hardware (e.g. GPU cores) and software frameworks (e.g., CUDA libraries), the model achieves faster training and inference times compared to CPU-only solutions.

## Training and Evaluation Datasets:

- The total size (in number of data points): 28,726 training tracks and 7,753 validation tracks (AVA-ActiveSpeaker), plus 6,635 evaluation clips (VoxCeleb2/TalkSet) and Columbia ASD (5 speakers)
- Total number of datasets: 4 (AVA-ActiveSpeaker train, AVA-ActiveSpeaker validation, Columbia ASD, VoxCeleb2/TalkSet)
- Dataset partition: Training [79%], evaluation [21%] (AVA train/val split; Columbia ASD and VoxCeleb2/TalkSet are evaluation-only datasets)

### Training Dataset:

- AVA-ActiveSpeaker Dataset

**Data Collection Method by dataset**
Hybrid: Human and Automated

**Labeling Method by dataset**
Hybrid: Human and Automated

**Properties:**
The AVA-ActiveSpeaker dataset contains face tracks and corresponding audio from Hollywood movie clips. Each face track is annotated with a binary speaking/not-speaking label at the frame level. The training set contains approximately 3.6 million entity-level annotations across 120 15-minute movie segments. Face crops are extracted using S3face detection and tracking.

**Data Modality**

- Video
- Audio

**Video Training Data Size**

- Less than 10,000 Hours

### Evaluation Dataset:

- AVA-ActiveSpeaker Validation Set
- Columbia ASD Dataset
- VoxCeleb2/TalkSet Validation Set

**Benchmark Score:**

AVA validation: mAP = 94.44%. Columbia ASD: F1 = 87.23% (averaged across 5 speakers, evaluated with 3-second duration).

**Data Collection Method by dataset**
Hybrid: Human and Automated

**Labeling Method by dataset**
Hybrid: Human and Automated

**Properties:**
AVA validation set contains 7,753 tracks across ~33 movie segments with frame-level annotations. Columbia ASD contains panel discussion videos with 5 speakers. VoxCeleb2/TalkSet validation set contains 6,635 clips (TAudio: 2,494, FAudio: 2,072, TFAudio: 2,069) derived from VoxCeleb2 celebrity interview videos with constructed speaking/non-speaking scenarios.

---

# Software Integration:

**Runtime Engine(s):**

NVIDIA AR SDK

**Supported Hardware Microarchitecture Compatability:**

* NVIDIA Ampere <br>
* NVIDIA Blackwell <br>
* NVIDIA Hopper <br>
* NVIDIA Lovelace <br>
* NVIDIA Turing <br>

**Preferred/Supported Operating System(s):**

* Ubuntu 20.04 <br>
* Ubuntu 22.04 <br>
* Ubuntu 24.04 <br>
* Debian 12 <br>
* Rocky/RHEL 8.* <br>
* Rocky/RHEL 9.* <br>
* Windows 10 <br>
* Windows 11 <br>

## Inference:
**Engine:** [TensorRT](https://developer.nvidia.com/tensorrt), [Triton](https://developer.nvidia.com/triton-inference-server) <br>
**Test Hardware:**
Desktops and Servers with following GPU architectures:
* NVIDIA Blackwell <br>
* NVIDIA Hopper <br>
* NVIDIA Lovelace <br>
* NVIDIA Ampere <br>
* NVIDIA Turing <br>

# Ethical Considerations:
NVIDIA believes Trustworthy AI is a shared responsibility and we have established policies and practices to enable development for a wide array of AI applications.  When downloaded or used in accordance with our terms of service, developers should work with their supporting model team to ensure this model meets requirements for the relevant industry and use case and addresses unforeseen product misuse.

For more detailed information on ethical considerations for this model, please see the Model Card++ Bias, Explainability, Safety & Security, and Privacy Subcards.

Please report model quality, risk, security vulnerabilities or NVIDIA AI Concerns [here](https://www.nvidia.com/en-us/support/submit-security-vulnerability/).

## Contact and Support

For questions, issues, or support:
- **NVIDIA NGC Support:** [https://ngc.nvidia.com/support](https://ngc.nvidia.com/support)
- **NVIDIA Developer Forums:** [https://forums.developer.nvidia.com/](https://forums.developer.nvidia.com/)

## Get Help
### Enterprise Support
Get access to knowledge base articles and support cases or [submit a ticket](nvidia.com/en-us/data-center/products/ai-enterprise-suite/support/).51:T14d6,# Face and Landmark Detector:
Field                                                                                                  |  Response
:------------------------------------------------------------------------------------------------------|:---------------------------------------------------------------------------------
Intended Domain:                                                                                       |  Human face detection and facial landmark localization in images and videos
Model Type:                                                                                            |  CNN with ResNet-inspired backbone using SCRFD architecture
Intended Users:                                                                                        |  Media and Entertainment, Academics/Researchers, Video analytics, Security, Biometrics
Output:                                                                                                |  Bounding box per face detected plus 5 facial keypoints (eyes, nose, mouth corners)
Describe how the model works:                                                                          |  Image input is analyzed by SCRFD model that outputs face bounding boxes with confidence scores and 5 facial landmarks per face. NMS post-processing filters overlapping detections.
Name the adversely impacted groups this has been tested to deliver comparable outcomes regardless of:  |  Not Applicable
Technical Limitations:                                                                                 |  The model may struggle in poorly lit conditions, with small faces (<20 pixels), extreme head orientations (>60° yaw/pitch), heavy occlusions, and may have reduced landmark accuracy for profile faces.
Verified to have met prescribed NVIDIA quality standards:                                              |  Yes
Performance Metrics:                                                                                   |  mAP (mean Average Precision), NME (Normalized Mean Error) for landmarks
Potential Known Risks:                                                                                 |  The model may fail to detect some faces or provide inaccurate landmarks in instances with poor lighting, small faces, extreme poses, or heavy occlusions. Performance may vary across demographic groups.
Licensing:                                                                                             |  GOVERNING TERMS: Use of this model is governed by the [NVIDIA Open Model License](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license/).

# SyncDiscriminator:
Field                                                                                                  |  Response
:------------------------------------------------------------------------------------------------------|:---------------------------------------------------------------------------------
Intended Task/Domain:                                                                   |  Video Communication and Content Creation
Model Type:                                                                                            |  Audio-Visual Convolutional and Recurrent Neural Networks (CNN + RNN).
Intended Users:                                                                                        |  This model is intended for developers building video communication and content creation applications that require active speaker detection.
Output:                                                                                                |  Per-frame active speaker detection score (raw logit, threshold 0.0)
Describe how the model works:                                                                          |  The model takes grayscale face crops and audio MFCC features as input. Visual and audio features are extracted through separate CNN encoders, fused via gated concatenation, and processed by a bidirectional GRU detector to produce per-frame speaking scores.
Name the adversely impacted groups this has been tested to deliver comparable outcomes regardless of:  |  Age, Gender, Race, Skin color.
Technical Limitations & Mitigation:                                                                    |  This model may not perform well with extreme audio noise, heavily occluded faces, very small face regions, or when multiple overlapping speakers are present.
Verified to have met prescribed NVIDIA quality standards:  |  Yes
Performance Metrics:                                                                                   |  Mean Average Precision (mAP), F1 Score, Latency, Throughput
Potential Known Risks:                                                                                 |  This model may produce incorrect speaking predictions in noisy environments or when face detection quality is poor, potentially leading to incorrect speaker attribution.
Licensing:                                                                                             |  GOVERNING TERMS: Use of this model is governed by the [NVIDIA Open Model License](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license/). Additional Information: [MIT](https://github.com/Junhua-Liao/LR-ASD/blob/main/LICENSE).52:T13ab,# Face and Landmark Detector:
Field                                                                                                                              |  Response
:----------------------------------------------------------------------------------------------------------------------------------|:-----------------------------------------------
Generatable or reverse engineerable personal data?                                                     |  Potentially: Facial landmarks can be considered biometric identifiers under certain regulations
Personal data used to create this model?                                                                                       |  No
Was consent obtained for any personal data used?                                                                                             |  Yes
How often is dataset reviewed?                                                                                                     |  Before Every Release
Is a mechanism in place to honor data subject right of access or deletion of personal data?                                        |  Yes
If personal data was collected for the development of the model, was it collected directly by NVIDIA?                                            |  No
If personal data was collected for the development of the model by NVIDIA, do you maintain or have access to disclosures made to data subjects?  |  N/A
If personal data was collected for the development of this AI model, was it minimized to only what was required?                                 |  N/A
Is there provenance for all datasets used in training?                                                                                |  Yes
Does data labeling (annotation, metadata) comply with privacy laws?                                                                |  Yes
Is data compliant with data subject requests for data correction or removal, if such a request was made?                           |  No, not possible with externally-sourced data.
| Applicable Privacy Policy                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |  [NVIDIA Privacy Policy](https://www.nvidia.com/en-us/about-nvidia/privacy-policy/)                                                                |

# SyncDiscriminator:
Field                                                                                                                              |  Response
:----------------------------------------------------------------------------------------------------------------------------------|:-----------------------------------------------
Generatable or reverse engineerable personal data?                                                     |  No
Personal data used to create this model?                                                                                       |  Yes
Was consent obtained for any personal data used?                                                                                             |  Unknown (Externally-Sourced Data)
How often is dataset reviewed?                                                                                                     |  At the onset of the project and when needed during the development.
Is a mechanism in place to honor data subject right of access or deletion of personal data?                                        |  Unknown (Externally-Sourced Data)
If personal data was collected for the development of the model, was it collected directly by NVIDIA?                                            | No
If personal data was collected for the development of the model by NVIDIA, do you maintain or have access to disclosures made to data subjects?  | Not Applicable
If personal data was collected for the development of this AI model, was it minimized to only what was required?                                 |  Unknown (Externally-Sourced Data)
Was data from user interactions with the AI model (e.g. user input and prompts) used to train the model?                                         |  No
Is there provenance for all datasets used in training?                                                                                |  Yes
Does data labeling (annotation, metadata) comply with privacy laws?                                                                |  Yes
Is data compliant with data subject requests for data correction or removal, if such a request was made?                           |  No, not possible with externally-sourced data
Applicable Privacy Policy        |  https://www.nvidia.com/en-us/about-nvidia/privacy-policy/53:T85a,# Face and Landmark Detector:
Field                                               |  Response
:---------------------------------------------------|:----------------------------------
Model Application(s):                               |  The model detects faces and facial landmarks in inputs that can be video, single or multiple images. The output includes bounding boxes (4 2D image coordinates) and 5 facial keypoints (10 2D coordinates) per detected face.
Describe the life critical impact (if present).   |  Not Applicable
Use Case Restrictions:                              |  GOVERNING TERMS: Use of this model is governed by the [NVIDIA Open Model License](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license/). Users must comply with applicable biometric data regulations (e.g., BIPA, GDPR Article 9) when using landmark detection features.
Model and dataset restrictions:            |  The Principle of least privilege (PoLP) is applied limiting access for dataset generation and model development. Restrictions enforce dataset access during training, and dataset license constraints adhered to. Facial landmark data is considered biometric information in many jurisdictions.

# SyncDiscriminator:
Field                                               |  Response
:---------------------------------------------------|:----------------------------------
Model Application Field(s):                               |  Video Communication, Content Creation
Describe the life critical impact (if present).   |  Not Applicable <br>
Use Case Restrictions:                              |   GOVERNING TERMS: Use of this model is governed by the [NVIDIA Open Model License](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license/). Additional Information: [MIT](https://github.com/Junhua-Liao/LR-ASD/blob/main/LICENSE).
Model and dataset restrictions:            |  The Principle of least privilege (PoLP) is applied limiting access for dataset generation and model development. Restrictions enforce dataset access during training, and dataset license constraints adhered to.49:[["$","div",".3",{"className":"relative","children":[["$","div",null,{"className":"relative flex min-h-[194px] w-full flex-col overflow-hidden p-md sm:p-ml bg-manitoulinLightBlack","children":[["$","$L4c",null,{"alt":"","className":"object-cover object-center !left-1/2 z-10 !w-1/2 brightness-20 lg:brightness-75","fill":true,"priority":true,"src":"https://assets.ngc.nvidia.com/products/api-catalog/images/active-speaker-detection.jpg","style":{"maskImage":"linear-gradient(to left, rgba(0,0,0,1), rgba(0,0,0,0))"}}],["$","div",null,{"className":"z-30 mx-auto flex w-full max-w-screen-xl min-w-0 flex-1 flex-col items-start justify-between gap-md lg:flex-row lg:gap-ml","children":["$","section",null,{"aria-describedby":"resource-description","aria-labelledby":"resource-name","className":"flex w-full min-w-0 flex-col lg:flex-1","children":["$","div",null,{"className":"flex flex-col gap-1.5 whitespace-pre-wrap","children":[["$","$L4d",null,{"className":"w-fit text-ml text-n300 lowercase hover:text-n050","href":"/nvidia","children":"NVIDIA"}],["$","div",null,{"className":"flex flex-col items-start gap-3 lg:flex-row lg:items-center","children":[["$","h1",null,{"className":"max-w-full text-lg leading-heading font-medium break-words text-primary","data-testid":"resource-name","id":"resource-name","children":"Active Speaker Detection"}],["$","$L4e",null,{"artifact":{"artifactType":"ENDPOINT","name":"active-speaker-detection","displayName":"Active Speaker Detection","publisher":"nvidia","shortDescription":"Detect and track speaker identities across video frames.","logo":"https://assets.ngc.nvidia.com/products/api-catalog/images/active-speaker-detection.jpg","labels":["2110","broadcast","broadcast-logging","dubbing","localization","nimType:endpoint:nim_type_preview","nimType:endpoint:nim_type_run_anywhere","nvidia ai for media","nvidia holoscan for media","smpte","speaker detection"],"attributes":[{"key":"AVAILABLE","value":"true"},{"key":"PREVIEW","value":"true"},{"key":"last_month_api_invocation_count","value":"1419"},{"key":"last_month_download_count","value":"0"}],"updatedDate":"2026-04-16T18:32:58.699Z","bias":"$4f","canGuestDownload":true,"createdDate":"2026-04-16T18:32:58.698Z","description":"$50","explainability":"$51","isPublic":true,"isReadOnly":true,"orgName":"qc69jvmznzxy","privacy":"$52","safetyAndSecurity":"$53"}}],"$undefined"]}],"$L54","$L55"]}]}]}],"$L56"]}],"$L57"]}]]
59:T807,## Getting Started

  NVIDIA Active Speaker Detection NIM uses gRPC APIs for inferencing requests. Following instructions demonstrate the usage of Active Speaker Detection NIM model using Python client.

  ### Prerequisites

  You will need a system with `git` and `Python 3.10+` installed.

  ###  Download the NVIDIA Active Speaker Detection NIM Python client

  Download code by cloning the [gRPC Client Repository](https://github.com/NVIDIA-Maxine/nim-clients.git):

  ```bash
  git clone https://github.com/NVIDIA-Maxine/nim-clients.git
  cd nim-clients/active-speaker-detection/
  ``` 

  Install the dependencies for the NVIDIA Active Speaker Detection NIM Python client:

  ```bash
  sudo apt-get install python3-pip
  pip install -r requirements.txt
  ```

  ### Run Python Client

  #### Navigate to the scripts directory
  ```bash
  cd scripts
  ```

  #### Send gRPC request
  Open a command terminal and execute below command to send gRPC request. If you have generated the API key, it will be auto-populated in the command.

  ```bash
  python active_speaker_detection.py --preview-mode \
  --target grpc.nvcf.nvidia.com:443 \
  --function-id <%- nvcfFunctionId %> \
  --api-key <%- apiKey %> \
  --video-input <input videofile path> \
  --audio-input <input audio file path> \
  --diarization-input <input diarization file path> \
  --output <output file path>
  ```

  #### Example command with sample input:
  ```bash
 python active_speaker_detection.py --preview-mode \
  --target grpc.nvcf.nvidia.com:443 \
  --function-id <%- nvcfFunctionId %> \
  --api-key <%- apiKey %> \
  --video-input ../assets/sample_video_streamable.mp4 \
  --audio-input ../assets/sample_audio.wav \
  --diarization-input ../assets/sample_diarization.json \
  --output out.mp4
  ```

  ####  Note the requirements for input file:

  - The supported file type is mp4 with H.264 codec.
  - The size limit for input file is 500 MB.

  Refer this [documentation](https://docs.nvidia.com/nim/maxine/active-speaker-detection/latest/index.html) for more information.
5a:T1ab5,## Step 1. Generate API Key

::generate-api-key

## Step 2. Pull and Run the NIM

```bash
$ docker login nvcr.io
Username: $oauthtoken
Password: <PASTE_API_KEY_HERE>
```

NVIDIA Active Speaker Detection NIM uses gRPC APIs for inferencing requests.

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

The following command launches the NVIDIA Active Speaker Detection NIM with the gRPC service. Find reference to runtime parameters for the container [here](https://docs.nvidia.com/nim/maxine/active-speaker-detection/latest/getting-started.html).

```bash
docker run -it --rm --name=active-speaker-detection-nim \
  --runtime=nvidia \
  --gpus all \
  --shm-size=8GB \
  -e NGC_API_KEY=$NGC_API_KEY \
  -e NIM_MANIFEST_PROFILE=$MANIFEST_PROFILE_ID \
  -e NIM_HTTP_API_PORT=8000 \
  -e NIM_GRPC_API_PORT=8001 \
  -p 8000:8000 \
  -p 8001:8001 \
  nvcr.io/nim/nvidia/active-speaker-detection:latest
```

Ensure you use the appropriate `MANIFEST_PROFILE_ID` for your GPU. For more information about `MANIFEST_PROFILE_ID`, refer to the the [Model Manifest Profiles  Table](https://docs.nvidia.com/nim/maxine/active-speaker-detection/latest/overview.html).

```{note}
`MANIFEST_PROFILE_ID` is an optional parameter. If the manifest profile ID is not supplied, the NIM automatically selects a matching profile ID based on the target hardware architecture.

However, if `MANIFEST_PROFILE_ID` is used, ensure that the associated GPU architecture is compatible with the target hardware. If an incorrect manifest profile ID is used, a deserialization error occurs on inference.
```

Please note, the flag --gpus all is used to assign all available GPUs to the docker container. This fails on multiple GPU unless all GPUs are same. To assign specific GPU to the docker container (in case of different multiple GPUs available in your machine) use --gpus '"device=0,1,2..."'

If the command runs successfully, you will get an output ending similar to the following:

```bash
I1027 22:31:44.952125 123 grpc_server.cc:2560] "Started GRPCInferenceService at 127.0.0.1:9001"
I1027 22:31:44.952247 123 http_server.cc:4755] "Started HTTPService at 127.0.0.1:9000"
I1027 22:31:44.993329 123 http_server.cc:358] "Started Metrics Service at 127.0.0.1:9002"
Triton server is ready
[INFO AI4M BASE LOGGER 2026-03-11 10:55:57.487 PID:195] Listening to 0.0.0.0:8001
```

By default, the Active Speaker Detection NIM gRPC service is hosted on port `8001`. You must use this port for inferencing requests. The port is configurable via the `NIM_GRPC_API_PORT` environment variable.

We have provided a sample client script file in our GitHub repo.
The script could be used to invoke the Docker container using the following instructions.

Download the Active Speaker Detection NIM client code by cloning the gRPC client repository ([NVIDIA-Maxine/nim-clients](https://github.com/NVIDIA-Maxine/nim-clients)):

   ```bash
   git clone https://github.com/NVIDIA-Maxine/nim-clients.git

   # Go to the 'active-speaker-detection' folder
   cd nim-clients/active-speaker-detection/
   ```

Install the required dependencies.

For the Python client:
```bash
# Install Python on Linux
sudo apt-get install python3-pip
pip install -r requirements.txt
```



```bash
cd scripts

python active_speaker_detection.py \
    --target 127.0.0.1:8001 \
    --video-input ../assets/sample_video_streamable.mp4 \
    --audio-input ../assets/sample_audio.wav \
    --diarization-input ../assets/sample_diarization.json \
    --output speaker_detection_output.mp4
```

The output video will have green bounding boxes on speaking faces and red on non-speaking faces.

To skip sending a separate audio stream (use audio embedded in the video):

```bash
python active_speaker_detection.py \
    --target 127.0.0.1:8001 \
    --video-input ../assets/sample_video_streamable.mp4 \
    --diarization-input ../assets/sample_diarization.json \
    --skip-audio
```

### Command Line Arguments

| Argument              | Description                                                                 | Default                              |
|-----------------------|-----------------------------------------------------------------------------|--------------------------------------|
| `--target`            | IP:port of gRPC service.                                                    | `127.0.0.1:8001`                     |
| `--video-input`       | Path to input video file (MP4 format).                                      | `../assets/sample_video_streamable.mp4`    |
| `--audio-input`       | Path to input audio file (WAV/MP3/OPUS format).                             | `../assets/sample_audio.wav`         |
| `--diarization-input` | Path to diarization JSON file with word-level speaker info.                 | `../assets/sample_diarization.json`  |
| `--output`            | Path for the output video file with speaker bounding boxes.                 | `speaker_detection_output.mp4`       |
| `--skip-audio`        | Skip sending separate audio; use audio embedded in the video stream.        | `False`                              |
| `--preview-mode`      | Send request to the preview NVCF NIM server.                                | `False`                              |
| `--api-key`           | NGC API key for authentication. Required in preview mode.                   | `None`                               |
| `--function-id`       | NVCF function ID for the service. Required in preview mode.                 | `None`                               |
| `--ssl-mode`          | SSL mode: `DISABLED`, `TLS`, or `MTLS`.                                    | `DISABLED`                           |
| `--ssl-key`           | Path to SSL private key (required for MTLS).                                | `../ssl_key/ssl_key_client.pem`      |
| `--ssl-cert`          | Path to SSL certificate chain (required for MTLS).                          | `../ssl_key/ssl_cert_client.pem`     |
| `--ssl-root-cert`     | Path to SSL root certificate (required for TLS/MTLS).                       | `../ssl_key/ssl_ca_cert.pem`         |


Refer to the [docs](https://docs.nvidia.com/nim/maxine/active-speaker-detection/latest/index.html) for more information.
5b:T1980,## Step 1. Apply for Access

This NIM is available through [Apply to Self-Host](https://www.nvidia.com/en-us/ai/nim-notifyme/).
Access gives you an NGC API key with access to the Active Speaker Detection images, Helm charts, and models.

## Step 2. Prerequisites

Before deployment, make sure your environment is prepared for Holoscan for Media and/or SMPTE ST 2110:

- Kubernetes cluster with a GPU node.
- Rivermax license and runtime support.
- High-speed network attachment (`NetworkAttachmentDefinition`) for ST 2110 traffic.
- NGC API key and Kubernetes secrets for image pull and model download.

For full prerequisite details, refer to [Getting Started](https://docs.nvidia.com/nim/maxine/active-speaker-detection-h4m/latest/getting-started.html).

Note the name of your `NetworkAttachmentDefinition` and your GPU node's hostname now — you will need both in Step 4.

```bash
kubectl get network-attachment-definitions
kubectl get nodes -o wide
```

## Step 3. Pull the Helm Chart

Authenticate and pull the sample Helm chart:

```bash
export NGC_API_KEY=<PASTE_API_KEY_HERE>

helm repo add nim-repo \
  https://helm.ngc.nvidia.com/nim/nvidia/ \
  --username='$oauthtoken' \
  --password=$NGC_API_KEY

helm repo update

helm pull nim-repo/nvidia-active-speaker-detection-h4m-sample --version 1.0.0
```

## Step 4. Install the ST 2110 Static Mode Pipeline

This deployment installs the complete pipeline consisting of sender, Active Speaker Detection NIM service, and receiver components. The primary output is per-frame active speaker metadata delivered as SMPTE ST 2110-40 ancillary data. Additionally, the receiver exposes an SRT video stream with bounding box overlays (disabled by default; enable via `testFrameOverlayMode`) that can be previewed in VLC or other SRT players.

This sample uses **static ST 2110 mode**, where multicast addresses, destination IPs, and ST 2110 ports are predefined in `values-st2110.yaml` unless overridden during installation.

---

### Minimal Installation Using Global Configuration

If all services use the same GPU node, network attachment, and image pull secret, configure them globally instead of per component:

```bash
helm install nvidia-asd-h4m-sample nvidia-active-speaker-detection-h4m-sample-1.0.0.tgz \
  -f <(tar -xOf nvidia-active-speaker-detection-h4m-sample-1.0.0.tgz \
      nvidia-active-speaker-detection-h4m-sample/values-st2110.yaml) \
  --set global.nodeSelector.hostname=<gpu-node-hostname> \
  --set global.image.secret=<image-pull-secret> \
  --set global.network.name=<multus-net-attach-def> \
  --set nvidia-active-speaker-detection-h4m-service.ngcModelDownload.secretName=<model-download-secret>
```

This applies the same configuration across the sender, receiver, and Active Speaker Detection NIM service.

---

### Optional: Install Using Per-Component Configuration

Use this option when components require different GPU nodes, network attachments, or secrets.

```bash
helm install nvidia-asd-h4m-sample nvidia-active-speaker-detection-h4m-sample-1.0.0.tgz \
  -f <(tar -xOf nvidia-active-speaker-detection-h4m-sample-1.0.0.tgz \
      nvidia-active-speaker-detection-h4m-sample/values-st2110.yaml) \
  --set sender.nodeSelector.hostname=<gpu-node-hostname> \
  --set receiver.nodeSelector.hostname=<gpu-node-hostname> \
  --set nvidia-active-speaker-detection-h4m-service.nodeSelector.hostname=<gpu-node-hostname>
```

---

### Optional: Configure Network Attachment Per-Component

Only required if not using the default `media-a-tx-net` network attachment.

Append the following to the install command:

```bash
  --set sender.network.name=<multus-net-attach-def> \
  --set receiver.network.name=<multus-net-attach-def> \
  --set nvidia-active-speaker-detection-h4m-service.network.name=<multus-net-attach-def>
```

---

### Optional: Configure Image Pull and Model Download Secrets Per-Component

Only required if your cluster does not use the default secrets:

- `ngc-api-key` for image pull
- `ngc-model-pull-api-key` for model download

Append the following to the install command:

```bash
  --set sender.image.secret=<image-pull-secret> \
  --set receiver.image.secret=<image-pull-secret> \
  --set nvidia-active-speaker-detection-h4m-service.image.secret=<image-pull-secret> \
  --set nvidia-active-speaker-detection-h4m-service.ngcModelDownload.secretName=<model-download-secret>
```

---

### Other Configuration Parameters

For advanced tuning options such as multicast addresses, ports, FPS, and resolution, see
[Configuration Reference](https://docs.nvidia.com/nim/maxine/active-speaker-detection-h4m/latest/configuration.html).

## Step 5. Verify Deployment and View Output

Check pod status:

```bash
kubectl get pods
```

Confirm sender, NIM, and receiver pods are `Running` and `READY 1/1`.

### View Ancillary Data Output

The receiver decodes the SMPTE ST 2110-40 ancillary stream and logs detection results as JSON. To view it:

```bash
kubectl logs deploy/<receiver-deployment>
```

Each log line contains the active speaker ancillary metadata for one frame, including:

- **`detections`** — array of detected faces, each with a bounding box (`x`, `y`, `w`, `h` in pixels), `is_speaking` flag, confidence `score`, `track_id`, and associated `audio_id`
- **`frame_idx`** — zero-based frame counter
- **`rtp_timestamp`** — RTP timestamp of the corresponding input video frame
- **`timestamp`** — wall-clock time of the frame

### View Output via SRT

> **Note:** The SRT video output stream shows bounding box overlays only when `testFrameOverlayMode` is enabled in the NIM service configuration. By default this is `false`.

To enable the video overlay output, both the NIM service overlay mode and the receiver video mode must be enabled. Add the following to your install command:

```bash
  --set nvidia-active-speaker-detection-h4m-service.pipeline.testFrameOverlayMode=true \
  --set receiver.receiverType=video
```

To preview the SRT stream:

```bash
kubectl get nodes -o wide
```

Open **VLC** → **Media** → **Open Network Stream**, then paste `srt://<internal-ip>:30889`.

`30889` is the default SRT NodePort exposed by the Helm chart and can be configured during installation.

## Step 6. Uninstall and Cleanup

Remove the release:

```bash
helm uninstall nvidia-asd-h4m-sample
```

For additional deployment options (NMOS mode, operator, standalone NIM service), and advanced configuration, refer to the [documentation](https://docs.nvidia.com/nim/maxine/active-speaker-detection-h4m/latest/index.html).
4a:["$","$L58",null,{"spec":{"namespace":"qc69jvmznzxy","updatedDate":"2026-09-30T16:46:42.526Z","nvcfFunctionId":"f286f937-05c4-454b-8312-fba67a2a6fa7","createdDate":"2026-04-16T18:32:59.037Z","attributes":{"apiDocsUrl":"https://docs.nvidia.com/nim/maxine/active-speaker-detection/latest/overview.html","termsOfUse":"<b>GOVERNING TERMS</b>: This trial service is governed by the <a href=\"https://assets.ngc.nvidia.com/products/api-catalog/legal/NVIDIA%20API%20Trial%20Terms%20of%20Service.pdf\" rel=\"noreferrer\" target=\"_blank\">NVIDIA API Trial Terms of Service</a>. Use of the models is governed by the <a href=\"https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license/\" rel=\"noreferrer\" target=\"_blank\"> NVIDIA Open Model License</a>. Additional Information: <a href=\"https://github.com/Junhua-Liao/LR-ASD/blob/main/LICENSE\" rel=\"noreferrer\" target=\"_blank\">MIT</a>.\n","showUnavailableBanner":false,"cta":{"text":"Apply to Self-Host","url":"https://www.nvidia.com/en-us/ai/nim-notifyme/","nim_available_override_url":"https://catalog.ngc.nvidia.com/orgs/nim/teams/nvidia/containers/active-speaker-detection"},"usage":"$59","deploy":[{"label":"Linux with Docker","filename":"linux.md","contents":"$5a"},{"label":"Deploy on Holoscan for Media Platform","filename":"h4m.md","contents":"$5b"}],"modelCapability":{"functionCalling":false}},"artifactName":"active-speaker-detection"}}]
5c:I[299632,["/_next/static/chunks/04d712ydf7vwt.js","/_next/static/chunks/3ibd-wdn1muo9.js","/_next/static/chunks/1q5xb__jylra0.js","/_next/static/chunks/1z_-bqrzptsiz.js","/_next/static/chunks/1la1pzs9j8idc.js","/_next/static/chunks/00eq9bqnkbpfo.js","/_next/static/chunks/1tjzqakl0-ac_.js","/_next/static/chunks/3r5yd4k4rms8-.js","/_next/static/chunks/1qasf48lwbczr.js","/_next/static/chunks/0iqwvdhi-o1pr.js","/_next/static/chunks/3-dupjzg004ft.js","/_next/static/chunks/1p8p6uesfmfc2.js","/_next/static/chunks/3c_tmnbt9nfb3.js","/_next/static/chunks/2lofudtwqsrwt.js","/_next/static/chunks/36qm3961yv116.js","/_next/static/chunks/342zpu2i9tat1.js","/_next/static/chunks/2tmwf_2axyd0y.js","/_next/static/chunks/3v9fr1qimf7lj.js","/_next/static/chunks/364lrnu5opng7.js","/_next/static/chunks/3kdaun3epyv7g.js","/_next/static/chunks/13fah1s8gxrn0.js","/_next/static/chunks/2tkz_ff5gjl4a.js","/_next/static/chunks/2_n0f-hh3ea4l.js","/_next/static/chunks/0czpc-f8wjri8.js","/_next/static/chunks/3761ezb6xysq0.js","/_next/static/chunks/24_gg9g_4g22i.js","/_next/static/chunks/1_3y3ily4zuo1.js","/_next/static/chunks/1a2o19d1j4nvx.js","/_next/static/chunks/1kci6kpi29km9.js","/_next/static/chunks/1hhq3s9jcti5r.js","/_next/static/chunks/2mr_uzqfq-mid.js","/_next/static/chunks/3o73dbhryidg8.js","/_next/static/chunks/278imbrkq3abd.js","/_next/static/chunks/2h5y8zqkl5tg7.js","/_next/static/chunks/0tqq_6ft6mlt2.js","/_next/static/chunks/1qibxep3kn6qx.js","/_next/static/chunks/2960tspz292yr.js","/_next/static/chunks/00jw9q5dp3jlz.js","/_next/static/chunks/1q5ewy8bee9p6.js","/_next/static/chunks/2pqhypz2vo8mu.js"],"default"]
5d:I[400402,["/_next/static/chunks/04d712ydf7vwt.js","/_next/static/chunks/3ibd-wdn1muo9.js","/_next/static/chunks/1q5xb__jylra0.js","/_next/static/chunks/1z_-bqrzptsiz.js","/_next/static/chunks/1la1pzs9j8idc.js","/_next/static/chunks/00eq9bqnkbpfo.js","/_next/static/chunks/1tjzqakl0-ac_.js","/_next/static/chunks/3r5yd4k4rms8-.js","/_next/static/chunks/1qasf48lwbczr.js","/_next/static/chunks/0iqwvdhi-o1pr.js","/_next/static/chunks/3-dupjzg004ft.js","/_next/static/chunks/1p8p6uesfmfc2.js","/_next/static/chunks/3c_tmnbt9nfb3.js","/_next/static/chunks/2lofudtwqsrwt.js","/_next/static/chunks/36qm3961yv116.js","/_next/static/chunks/342zpu2i9tat1.js","/_next/static/chunks/2tmwf_2axyd0y.js","/_next/static/chunks/3v9fr1qimf7lj.js","/_next/static/chunks/364lrnu5opng7.js","/_next/static/chunks/3kdaun3epyv7g.js","/_next/static/chunks/13fah1s8gxrn0.js","/_next/static/chunks/2tkz_ff5gjl4a.js","/_next/static/chunks/2_n0f-hh3ea4l.js","/_next/static/chunks/0czpc-f8wjri8.js","/_next/static/chunks/3761ezb6xysq0.js","/_next/static/chunks/24_gg9g_4g22i.js","/_next/static/chunks/1_3y3ily4zuo1.js","/_next/static/chunks/1a2o19d1j4nvx.js","/_next/static/chunks/1kci6kpi29km9.js","/_next/static/chunks/1hhq3s9jcti5r.js","/_next/static/chunks/2mr_uzqfq-mid.js","/_next/static/chunks/3o73dbhryidg8.js","/_next/static/chunks/278imbrkq3abd.js","/_next/static/chunks/2h5y8zqkl5tg7.js","/_next/static/chunks/0tqq_6ft6mlt2.js","/_next/static/chunks/1qibxep3kn6qx.js","/_next/static/chunks/2960tspz292yr.js","/_next/static/chunks/00jw9q5dp3jlz.js","/_next/static/chunks/1q5ewy8bee9p6.js","/_next/static/chunks/2pqhypz2vo8mu.js"],"EndpointCTA"]
5e:I[331699,["/_next/static/chunks/04d712ydf7vwt.js","/_next/static/chunks/3ibd-wdn1muo9.js","/_next/static/chunks/1q5xb__jylra0.js","/_next/static/chunks/1z_-bqrzptsiz.js","/_next/static/chunks/1la1pzs9j8idc.js","/_next/static/chunks/00eq9bqnkbpfo.js","/_next/static/chunks/1tjzqakl0-ac_.js","/_next/static/chunks/3r5yd4k4rms8-.js","/_next/static/chunks/1qasf48lwbczr.js","/_next/static/chunks/0iqwvdhi-o1pr.js","/_next/static/chunks/3-dupjzg004ft.js","/_next/static/chunks/1p8p6uesfmfc2.js","/_next/static/chunks/3c_tmnbt9nfb3.js","/_next/static/chunks/2lofudtwqsrwt.js","/_next/static/chunks/36qm3961yv116.js","/_next/static/chunks/342zpu2i9tat1.js","/_next/static/chunks/2tmwf_2axyd0y.js","/_next/static/chunks/3v9fr1qimf7lj.js","/_next/static/chunks/364lrnu5opng7.js","/_next/static/chunks/3kdaun3epyv7g.js","/_next/static/chunks/13fah1s8gxrn0.js","/_next/static/chunks/2tkz_ff5gjl4a.js","/_next/static/chunks/2_n0f-hh3ea4l.js","/_next/static/chunks/0czpc-f8wjri8.js","/_next/static/chunks/3761ezb6xysq0.js","/_next/static/chunks/24_gg9g_4g22i.js","/_next/static/chunks/1_3y3ily4zuo1.js","/_next/static/chunks/1a2o19d1j4nvx.js","/_next/static/chunks/1kci6kpi29km9.js","/_next/static/chunks/1hhq3s9jcti5r.js","/_next/static/chunks/2mr_uzqfq-mid.js","/_next/static/chunks/3o73dbhryidg8.js","/_next/static/chunks/278imbrkq3abd.js","/_next/static/chunks/2h5y8zqkl5tg7.js","/_next/static/chunks/0tqq_6ft6mlt2.js","/_next/static/chunks/1qibxep3kn6qx.js","/_next/static/chunks/2960tspz292yr.js","/_next/static/chunks/00jw9q5dp3jlz.js","/_next/static/chunks/1q5ewy8bee9p6.js","/_next/static/chunks/2pqhypz2vo8mu.js"],"ModelContent"]
5f:I[420143,["/_next/static/chunks/04d712ydf7vwt.js","/_next/static/chunks/3ibd-wdn1muo9.js","/_next/static/chunks/1q5xb__jylra0.js","/_next/static/chunks/1z_-bqrzptsiz.js","/_next/static/chunks/1la1pzs9j8idc.js","/_next/static/chunks/00eq9bqnkbpfo.js","/_next/static/chunks/1tjzqakl0-ac_.js","/_next/static/chunks/3r5yd4k4rms8-.js","/_next/static/chunks/1qasf48lwbczr.js","/_next/static/chunks/0iqwvdhi-o1pr.js","/_next/static/chunks/3-dupjzg004ft.js","/_next/static/chunks/1p8p6uesfmfc2.js","/_next/static/chunks/3c_tmnbt9nfb3.js","/_next/static/chunks/2lofudtwqsrwt.js","/_next/static/chunks/36qm3961yv116.js","/_next/static/chunks/342zpu2i9tat1.js","/_next/static/chunks/2tmwf_2axyd0y.js","/_next/static/chunks/3v9fr1qimf7lj.js","/_next/static/chunks/364lrnu5opng7.js","/_next/static/chunks/3kdaun3epyv7g.js","/_next/static/chunks/13fah1s8gxrn0.js","/_next/static/chunks/2tkz_ff5gjl4a.js","/_next/static/chunks/2_n0f-hh3ea4l.js","/_next/static/chunks/0czpc-f8wjri8.js","/_next/static/chunks/3761ezb6xysq0.js","/_next/static/chunks/24_gg9g_4g22i.js","/_next/static/chunks/1_3y3ily4zuo1.js","/_next/static/chunks/1a2o19d1j4nvx.js","/_next/static/chunks/1kci6kpi29km9.js","/_next/static/chunks/1hhq3s9jcti5r.js","/_next/static/chunks/2mr_uzqfq-mid.js","/_next/static/chunks/3o73dbhryidg8.js","/_next/static/chunks/278imbrkq3abd.js","/_next/static/chunks/2h5y8zqkl5tg7.js","/_next/static/chunks/0tqq_6ft6mlt2.js","/_next/static/chunks/1qibxep3kn6qx.js","/_next/static/chunks/2960tspz292yr.js","/_next/static/chunks/00jw9q5dp3jlz.js","/_next/static/chunks/1q5ewy8bee9p6.js","/_next/static/chunks/2pqhypz2vo8mu.js"],"default"]
54:["$","p",null,{"className":"max-w-[85ch] text-ms text-primary","id":"resource-description","children":"Detect and track speaker identities across video frames."}]
55:["$","div",null,{"className":"flex w-full flex-col items-start gap-md lg:flex-row lg:items-end lg:justify-between","children":[["$","div",null,{"className":"flex w-full min-w-0 flex-wrap gap-sm lg:flex-1","children":["$","$L5c",null,{"artifactType":"ENDPOINT","density":"standard","labels":"$49:0:props:children:0:props:children:1:props:children:props:children:props:children:1:props:children:1:props:artifact:labels","searchRoutePath":"/models"}]}],["$","div",null,{"className":"z-30 flex w-full flex-row justify-start gap-ms sm:justify-end lg:w-auto lg:shrink-0","children":["$undefined",["$","$L5d",null,{"cta":"$4a:props:spec:attributes:cta","isNIMAccessRestricted":"$undefined","isNIMAvailable":true}]]}]]}]
56:["$","div",null,{"className":"pointer-events-none absolute right-0 bottom-0 left-0 z-20 h-30 bg-gradient-to-t to-transparent from-manitoulinLightBlack via-manitoulinLightBlack/70"}]
57:["$","div",null,{"className":"px-4 mx-auto flex max-w-screen-xl flex-col pt-0 lg:px-0","data-body-background":"light-black","children":["$","section",null,{"className":"flex w-full flex-col justify-between rounded-4 border-manitoulinBorderColor bg-manitoulinDarkBlack sm:rounded-6 lg:rounded-8 p-ms lg:p-lg","children":["$","$L5e",null,{"apiReferenceEnabled":false,"artifact":"$49:0:props:children:0:props:children:1:props:children:props:children:props:children:1:props:children:1:props:artifact","endpointName":"active-speaker-detection","endpointSpec":"$4a:props:spec","isLoginRequired":true,"playgroundElement":"$5f","publisherName":"nvidia","searchParams":{},"tabs":[{"label":"Experience","bare":true,"icon":"play","kind":"default","id":"experience","href":"/nvidia/active-speaker-detection","aliases":["/nvidia/active-speaker-detection/experience"]},{"label":"Model Card","icon":"book","kind":"default","id":"modelcard","href":"/nvidia/active-speaker-detection/modelcard","aliases":"$undefined"},{"label":"Try API","kind":"default","id":"api","href":"/nvidia/active-speaker-detection/api","aliases":"$undefined"},{"label":"Deploy","kind":"default","id":"deploy","href":"/nvidia/active-speaker-detection/deploy","aliases":"$undefined"}]}]}]}]
