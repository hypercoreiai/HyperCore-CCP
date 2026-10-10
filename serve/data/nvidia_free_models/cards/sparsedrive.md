---
title: "sparsedrive"
publisher: "nvidia"
type: "endpoint"
updated: "2025-07-20T16:35:32.947Z"
description: "End-to-end autonomous driving stack integrating perception, prediction, and planning with sparse scene representations for efficiency and safety."
canonical: "https://build.nvidia.com/nvidia/sparsedrive"
---

## SparseDrive Model Overview

## Description   
SparseDrive is an end-to-end autonomous driving model that performs motion prediction and planning simultaneously, outputting a safe planning trajectory. It first encodes multi-view images into feature maps, then learns sparse scene representation through symmetric sparse perception, and finally performs motion prediction and planning in a parallel manner. 

This NIM previews an end-to-end example of deploying [SparseDrive](https://github.com/swc-17/SparseDrive) based on the [paper](https://arxiv.org/abs/2405.19620) with explicit quantization with [NVIDIA's ModelOpt Toolkit](https://github.com/NVIDIA/TensorRT-Model-Optimizer). 

This model is ready for commercial/non-commercial use.

## Third-Party Community Consideration  
This model is not owned or developed by NVIDIA. It has been developed and built to a third-party’s requirements for this application and use case; see link to [SparseDrive](https://github.com/swc-17/SparseDrive). 

## License  
**GOVERNING TERMS:** The trial service is governed by the [NVIDIA API Trial Terms of Service](https://assets.ngc.nvidia.com/products/api-catalog/legal/NVIDIA%20API%20Trial%20Terms%20of%20Service.pdf). Use of this model is governed by the [NVIDIA Community Model License](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-community-models-license/). ADDITIONAL INFORMATION: [MIT License](https://github.com/swc-17/SparseDrive/blob/main/LICENSE).

## Deployment Geography:
Global

## Use Case   
Researchers and developers in the field of autonomous driving and motion forecasting, specifically those working with 3D object detection and tracking, would be expected to use this system for tasks such as object detection, tracking, motion prediction, and planning.

## Release Date   
03/18/2025 via [https://build.nvidia.com/nvidia/sparsedrive](https://build.nvidia.com/nvidia/sparsedrive)

## Model Architecture

* **Architecture Type:**  CNN backbone \+ Multiple Transformers  
* **Network Architecture:**  SparseDrive uses a Resnet50 backbone for image feature extraction.  The multi-head transformer-based architecture consists of:   
* Sparse Perception Transformers: Symmetric Object Detection and Tracking and Online Mapping submodules  
* Motion Planning Transformer: Parallel Motion Planner for multi-modal trajectory planning and selection

## Input/Output Specifications
### Input
* **Input Type(s):** Multi-view camera images, cameras’ intrinsics and extrinsics, Ego vehicle state  
* **Input Format(s):** Python Dictionary/JSON  
* **Input Parameters:** 6x stacked 2D RGB images, 6x 2D camera projection (4x4) matrix, 6x 2D camera extrinsics (4x4) matrix, 1D (length 12\) ego vehicle state vector  
* **Other Properties Related to Input:**   
* Model performs best given a sequence of images from the same “scene”, e.g. a 20 second scene from NuScenes dataset  
* Image Resolution: 256 x 704 (HxW)  
* Pre-Processing Requirements:  None  
* Sensor Calibration Data: Camera Intrinsics, Camera Extrinsics  
* Ego Motion Data: Position, Orientation, Velocity

### Output  
* **Output Type(s):** Ordered arrays of labeled bounding boxes and trajectory predictions  
* **Output Format:** Python Dictionary/JSON  
* **Output Parameters:**   
* Array of detected 3D object labels (NuScenes dynamic object classes)  
* Array of 3D Bounding Boxes per 3D object instance (each a vector of length 7: translation, size, yaw angle)  
* Array of 2D Predicted Trajectories per 3D object instance   
* Array of Predicted 2D map elements and labels (NuScenes static object classes, road boundaries)  
* Predicted planned 2D trajectory for ego vehicle  
* **Other Properties Related to Output:**  
* Confidence Score: Each detected object and trajectory prediction includes confidence level  
* Motion prediction for next 6 sec of scene @2Hz  

## Software Integration

* Runtime Engine(s): TensorRT  
* Supported Hardware Compatibility:   
* NVIDIA Ampere   
* NVIDIA Ada Lovelace  
* Operating System(s):   
* Docker OS: 24.04.1 LTS (Noble Numbat)

## Model Version(s)
- **Model Name:** sparsedrive\_trt\_model\_fp16  
- **Tag/Version**: 0.1.1

## Training, Testing, and Evaluation Datasets  
### Overview
[nuScenes](https://www.nuscenes.org/nuscenes) dataset was used for training, testing and evaluation (see details below).

The nuScenes dataset (pronounced /nuːsiːnz/) is a public large-scale dataset for autonomous driving developed by the team at [Motional](https://www.motional.com/) (formerly nuTonomy). Motional is making driverless vehicles a safe, reliable, and accessible reality.

### Data Collection Method: Human

[nuScenes](https://www.nuscenes.org/nuscenes) dataset collects approximately 15h of driving data in Boston and Singapore. Driving routes are carefully chosen to capture challenging scenarios. nuScenes aims for a diverse set of locations, times and weather conditions. To balance the class frequency distribution, nuScenes includes more scenes with rare classes (such as bicycles). Using these criteria, data was manually selected to include 1000 scenes of 20s duration each. These scenes are carefully annotated using human experts. 

### Labeling Method: Human

Annotation partner [Scale](https://scaleapi.com/) is used for annotation. All objects in the nuScenes dataset come with a semantic category, as well as a 3D bounding box and attributes for each frame they occur in. Ground truth labels for 23 object classes are provided. 

## Inference  
Engine: Tensor(RT)  
Test Hardware: 

* A6000  
* L40S

## Ethical Considerations  
Ethical considerations and guidelines. NVIDIA believes Trustworthy AI is a shared responsibility and we have established policies and practices to enable development for a wide array of AI applications.  When downloaded or used in accordance with our terms of service, developers should work with their internal model team to ensure this model meets requirements for the relevant industry and use case and addresses unforeseen product misuse.  

Please report security vulnerabilities or NVIDIA AI Concerns [here](https://www.nvidia.com/en-us/support/submit-security-vulnerability/).