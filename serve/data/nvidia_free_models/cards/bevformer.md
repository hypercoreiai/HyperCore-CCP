---
title: "bevformer"
publisher: "nvidia"
type: "endpoint"
updated: "2025-07-20T16:35:28.946Z"
description: "Advanced transformer for multi-frame bird's-eye-view 3D perception in autonomous driving."
canonical: "https://build.nvidia.com/nvidia/bevformer"
---

# BEVFormer Model Overview

## Description
BEVFormer is a transformer-based model that combines multi-frame camera data into a unified bird's-eye-view (BEV) representation for 3D perception. BEVFormer learns these representations using spatiotemporal transformers. This approach allows the system to exploit both spatial and temporal information by interacting with spatial and temporal spaces through predefined grid-shaped BEV queries.

This NIM previews an example of deploying [BEVFormer](https://arxiv.org/abs/2203.17270) with explicit quantization with [NVIDIA's ModelOpt Toolkit](https://github.com/NVIDIA/TensorRT-Model-Optimizer).

This model is ready for commercial/non-commercial use.

## Third-Party Community Consideration
This model is not owned or developed by NVIDIA. It has been developed and built to a third-party's requirements for this application and use case; see link to [BEVFormer](https://github.com/fundamentalvision/BEVFormer).

## License
**GOVERNING TERMS:** The trial service is governed by the [NVIDIA API Trial Terms of Service](https://assets.ngc.nvidia.com/products/api-catalog/legal/NVIDIA%20API%20Trial%20Terms%20of%20Service.pdf). Use of this model is governed by the [NVIDIA Community Model License](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-community-models-license/). ADDITIONAL INFORMATION: [Apache 2.0](https://github.com/DerryHub/BEVFormer_tensorrt/blob/main/LICENCE).

## Deployment Geography
Global

## Use Case
BEVFormer is most suitable for Physical AI developers, especially ADAS and AV developers working on Perception tasks.

## Release Date
03/18/2025 via [https://build.nvidia.com/nvidia/bevformer](https://build.nvidia.com/nvidia/bevformer)

## Model Architecture
- **Architecture Type:** CNN + Transformer
- **Network Architecture:** ResNet-101 Backbone + BEVFormer Encoder (six layers with BEV queries, spatial cross-attention, and temporal self-attention) + Dual Heads (3D detection and map segmentation)

## Input
- **Input Types:** Multi-view Camera images captured from various angles around the vehicle, Vehicle State Data, Camera extrinsics
- **Input Formats:** Images (Red, Green, Blue), Vehicle State Data (json), and Camera extrinsics (json)
- **Input Parameters:** RGB images (2D), Vehicle State Data (1D), and Camera extrinsics (2D)
- **Other Properties Related to Input:**
- Image Resolution: 450*800
- Pre-Processing Requirements: Normalization, Data Augmentation
- Vehicle State Data: Position, Orientation, Velocity, Rotation rate
- Sensor Calibration Data: Camera Intrinsics, Camera Extrinsics

## Output
- **Output Types:** Labels
- **Output Formats:** Labels: Text String
- **Output Parameters:** 1D
- **Other Properties Related to Output:** Category Label(s) and Bounding boxes of the perceived objects around the vehicle.
- Object Classes: Vehicles, Pedestrians, Cyclists, Traffic cones, Barriers
- Confidence Score: Each detected object and trajectory prediction includes confidence level

## Software Integration
- **Runtime Engine(s):** TensorRT
- **Hardware Compatibility:**
- NVIDIA Ampere
- NVIDIA Ada Lovelace
- **Operating System(s):**
- Docker image OS: Ubuntu 22.04.5 LTS (Jammy Jellyfish)

## Model Version(s)
- **Model Name:** bevformer_trt_model_int8
- **Tag/Version:** 0.1.2

## Training, Testing, and Evaluation Datasets

### Overview
[nuScenes](https://www.nuscenes.org/nuscenes) dataset was used for training, testing and evaluation (see details below).

The nuScenes dataset (pronounced /nuːsiːnz/) is a public large-scale dataset for autonomous driving developed by the team at [Motional](https://www.motional.com/) (formerly nuTonomy). Motional is making driverless vehicles a safe, reliable, and accessible reality.

### Data Collection Method: Human
[nuScenes](https://www.nuscenes.org/nuscenes) dataset collects approximately 15h of driving data in Boston and Singapore. Driving routes are carefully chosen to capture challenging scenarios. nuScenes aims for a diverse set of locations, times and weather conditions. To balance the class frequency distribution, nuScenes includes more scenes with rare classes (such as bicycles). Using these criteria, data was manually selected to include 1000 scenes of 20s duration each. These scenes are carefully annotated using human experts.

### Labeling Method: Human
Annotation partner [Scale](https://scaleapi.com/) is used for annotation. All objects in the nuScenes dataset come with a semantic category, as well as a 3D bounding box and attributes for each frame they occur in. Ground truth labels for 23 object classes are provided.

## Inference
- **Engine:** TensorRT
- **Test Hardware:**
- A30
- A6000
- L40
- L40S
- L40G

## Ethical Considerations
NVIDIA believes Trustworthy AI is a shared responsibility and we have established policies and practices to enable development for a wide array of AI applications. When downloaded or used in accordance with our terms of service, developers should work with their internal model team to ensure this model meets requirements for the relevant industry and use case and addresses unforeseen product misuse.

Please report security vulnerabilities or NVIDIA AI Concerns [here](https://www.nvidia.com/en-us/support/submit-security-vulnerability/).