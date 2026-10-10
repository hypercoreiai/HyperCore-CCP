---
title: "streampetr"
publisher: "nvidia"
type: "endpoint"
updated: "2025-11-13T05:51:34.923Z"
description: "StreamPETR offers efficient 3D object detection for autonomous driving by propagating sparse object queries temporally."
canonical: "https://build.nvidia.com/nvidia/streampetr"
---

# streamPetr Overview

## Description
streamPetr is an efficient multi-view 3D object detection model that introduces object-centric temporal modeling for streaming video input. Designed for autonomous driving scenarios, streamPetr propagates long-term historical information through object queries across frames, enabling online frame-by-frame 3D predictions while maintaining minimal storage and computational overhead. By utilizing TensorRT, streamPetr delivers fast, efficient inference tailored for real-time deployment in advanced autonomous driving systems.

*This model is ready for commercial/non-commercial use.*

## Third-Party Community Consideration:
This model is not owned or developed by NVIDIA. This model has been developed and built to a third-party's requirements for this application and use case; see link to Non-NVIDIA [streamPetr Model Card](https://github.com/exiawsh/StreamPETR)

## License and Terms of Use:
**Governing Terms:** The trial service is governed by the [NVIDIA API Trial Terms of Service](https://assets.ngc.nvidia.com/products/api-catalog/legal/NVIDIA%20API%20Trial%20Terms%20of%20Service.pdf). Use of this model is governed by the [NVIDIA Open Model License Agreement](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license/). ADDITIONAL INFORMATION: [Apache 2.0 License](https://www.apache.org/licenses/LICENSE-2.0).

## Deployment Geography:
**Deployment Geography:** Global

## Use Case:
Researchers and developers in the field of autonomous driving and motion forecasting, specifically those working on end-to-end model development and deployment.

## Release Date:
11/12/2025 via https://build.nvidia.com/nvidia/streampetr

## Reference(s):
**References:** [GitHub Repository](https://github.com/NVIDIA/DL4AGX/tree/master/AV-Solutions/streampetr-trt), [arXiv Paper](https://arxiv.org/pdf/2303.11926), [Original streamPetr Repository](https://github.com/exiawsh/StreamPETR)

## Model Architecture:
**Architecture Type:** CNN backbone + Sparse Query-Based Transformer  
**Network Architecture:** streamPetr utilizes a standard image backbone (ResNet50 or Vision Transformer in varying configurations) to extract multi-view features from input camera images. These features are then processed by a Transformer-based detection head, which follows a sparse query design inherited from the PETR series. The architecture innovates with several modules:
- **Object-Centric Temporal Module:** Object queries encode and propagate object-specific information across frames, efficiently accumulating long-term temporal context for online 3D detection with minimal memory or computational cost.
- **Motion-Aware Layer Normalization:** A unique normalization layer encodes the dynamics of moving objects and the ego-vehicle, reducing error build-up and improving detection stability over time in streaming video.
- **Detection Transformer Head:** Multi-view features and propagated object queries are processed by transformer decoder layers, modeling spatial-temporal interactions to directly produce 3D object locations and attributes.

**Total Parameters:** Undisclosed   
**Base Model:** ResNet50/Vision Transformer

### Input:
**Input Types:** Multi-view camera images, camera intrinsics and extrinsics, ego vehicle state
**Input Formats:** Python Dictionary/JSON  
**Input Parameters:** 6x stacked Two-Dimensional (2D) RGB images (shape: 3 x 256 x 704), 6x 2D camera Intrinsic (4x4) matrix, 6x 2D camera Extrinsic (4x4) matrix, One-Dimensional (1D) ego vehicle state vector (Dimension 12) <br>  
**Other Input Properties:**
- Model performs best given a sequence of images from the same "scene", e.g. a 20 second scene from NuScenes dataset
- Image Resolution: 256 x 704 (HxW)
- Pre-Processing Requirements: None
- Sensor Calibration Data: Camera Intrinsics, Camera Extrinsics
- Ego Motion Data: Position, Orientation, Velocity

**Input Context Length (ISL):** 20 seconds scene duration

### Output:
**Output Types:** Arrays of detected 3D bounding boxes, predicted 3D attributes for agents, bird's-eye view embedding tensor
**Output Format:** Python Dictionary/JSON

**Output Parameters:**
- Array of detected objects per frame [Class label, 3D box coordinates, orientation, velocity if available, size & confidence score]
- BEV embedding (used for visualization)
- Per-frame detection video (camera and BEV rendered as mp4/avi base64-encoded)

**Other Output Properties:**
- Confidence/probability score with every detection
- Up to 300 objects per frame

**Output Context Length (OSL):** Real-time frame-by-frame processing <br>

Our AI models are designed and/or optimized to run on NVIDIA GPU-accelerated systems. By leveraging NVIDIA's hardware (e.g. GPU cores) and software frameworks (e.g., CUDA libraries), the model achieves faster training and inference times compared to CPU-only solutions.

## Software Integration:
**Runtime Engines:** TensorRT  
**Supported Hardware Microarchitecture Compatibility:** NVIDIA CUDA & TensorRT compliant GPU  
**Operating Systems:** Docker OS: Ubuntu 24.04.1 LTS (Noble Numbat) <br>

The integration of foundation and fine-tuned models into AI systems requires additional testing using use-case-specific data to ensure safe and effective deployment. Following the V-model methodology, iterative testing and validation at both unit and system levels are essential to mitigate risks, meet technical and functional requirements, and ensure compliance with safety and ethical standards before deployment.

## Model Version(s)
**Model Name:** streamPetr  

# Training, Testing, and Evaluation Datasets:

## Training Dataset
**Link: [nuScenes dataset](https://www.nuscenes.org/)** <br>
**Training Data Collection:** Human  
**Training Labeling:** Human  
**Training Properties:** The nuScenes dataset (pronounced /nuːsiːnz/) is a public large-scale dataset for autonomous driving developed by the team at Motional (formerly nuTonomy). nuScenes dataset collects approximately 15h of driving data in Boston and Singapore. Driving routes are carefully chosen to capture challenging scenarios. nuScenes aims for a diverse set of locations, times and weather conditions. To balance the class frequency distribution, nuScenes includes more scenes with rare classes (such as bicycles). Using these criteria, data was manually selected to include 1000 scenes of 20s duration each. Link: [nuScenes dataset](https://www.nuscenes.org/)  
**Data Modality:** Vision (Multi-view Camera Images)  
**Training Data Size:** ~15 hours of driving data, 1000 scenes of 20s duration each

## Testing Dataset
**Testing Data Collection:** Human  
**Testing Labeling:** Human  
**Testing Properties:** nuScenes dataset was used for testing. Annotation partner Scale is used for annotation. All objects in the nuScenes dataset come with a semantic category, as well as a 3D bounding box and attributes for each frame they occur in. Ground truth labels for 23 object classes are provided.

## Evaluation Dataset
**Evaluation Benchmark Score:** Undisclosed  
**Evaluation Data Collection:** Human  
**Evaluation Labeling:** Human  
**Evaluation Properties:** nuScenes dataset was used for evaluation. These scenes are carefully annotated using human experts.

## Inference
**Acceleration Engine:** TensorRT  
**Test Hardware:** 
- NVIDIA A100
- NVIDIA L40S
- NVIDIA H100

## Ethical Considerations
NVIDIA believes Trustworthy AI is a shared responsibility and we have established policies and practices to enable development for a wide array of AI applications. When downloaded or used in accordance with our terms of service, developers should work with their internal model team to ensure this model meets requirements for the relevant industry and use case and addresses unforeseen product misuse.

Please report model quality, risk, security vulnerabilities or NVIDIA AI Concerns [here](https://app.intigriti.com/programs/nvidia/nvidiavdp/detail)