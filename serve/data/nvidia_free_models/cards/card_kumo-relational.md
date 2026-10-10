]
52:T19eb,# Model Overview

## Description
NVIDIA Kumo Relational is a structured-data foundation model for prediction over relational, multi-table data. It uses declared schemas, relationships, entity tables, fact tables, context rows, and prediction rows without requiring callers to flatten connected tables into a single feature table.

The NVIDIA Kumo Relational Inference Microservice (NIM), release 1.0.0, accepts JSON arrays-format relational payloads through a structured-data API, validates the task, schema, context, and prediction contract, and invokes the Kumo Relational driver for synchronous inference.

This model is ready for commercial or non-commercial use.

## License and Terms of Use:
**GOVERNING TERMS:** The NIM container is governed by the [NVIDIA Software License Agreement](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-software-license-agreement/) and the [Product-Specific Terms for NVIDIA AI Products](https://www.nvidia.com/en-us/agreements/enterprise-software/product-specific-terms-for-ai-products/); and the use of the model is governed by the [NVIDIA Open Model License Agreement](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license/).

## Deployment Geography:
Global

## Use Case:
**Use Case:** NVIDIA Kumo Relational is designed for binary classification, multiclass classification, regression, forecasting, and temporal link prediction over structured relational data. It supports one-shot prediction and session-based workflows that reuse the same model, task, schema, and context across prediction requests.

## Release Date:
**NGC:** 08/18/2026 via `nvcr.io/nim/nvidia/kumo-relational:1.0.0`
**Source announcement:** 04/14/2025 via [KumoRFM-2: Scaling Foundation Models for Relational Learning](https://arxiv.org/abs/2604.12596)

## Reference(s):
**References:**
- [KumoRFM whitepaper](https://arxiv.org/abs/2604.12596)

## Model Architecture:
**Architecture Type:** Transformer
**Network Architecture:** NVIDIA Kumo Relational 1.0.0 uses a table-invariant row encoder and exchanges information across connected tables and context labels with a Relational Graph Transformer.
**Total Parameters:** 3.1*10^7

### Input:
**Input Types:** Tabular
**Input Formats:** JSON arrays-format relational tables
**Input Parameters:** One Dimensional (1D)
**Other Properties Related to Input:** Requests declare an instance table, optional related tables, relationships, task metadata, labeled context rows, and prediction rows. Binary classification, multiclass classification, regression, and forecasting require exactly one entity table. Temporal link prediction requires source and target entity tables.

### Output:
**Output Types:** Tabular
**Output Format:** JSON prediction results
**Output Parameters:** One Dimensional (1D)
**Other Properties Related to Output:** Task-dependent outputs include predictions, probabilities, scores, rankings, quantiles, embeddings, and single-row diagnostic explanations.

__Our AI models are designed and/or optimized to run on NVIDIA GPU-accelerated systems. By leveraging NVIDIA's hardware (e.g. GPU cores) and software frameworks (e.g., CUDA libraries), the model achieves faster training and inference times compared to CPU-only solutions.__

## Software Integration:
**Runtime Engines:**
Kumo Relational driver, release 1.0.0

**Supported Hardware Microarchitecture Compatibility:**
- NVIDIA A10G Tensor Core GPU
- NVIDIA H100 Tensor Core GPU
- NVIDIA L4 Tensor Core GPU
- NVIDIA L40S GPU

**Supported Operating System:** Linux

__The integration of foundation and fine-tuned models into AI systems requires additional testing using use-case-specific data to ensure safe and effective deployment. Following the V-model methodology, iterative testing and validation at both unit and system levels are essential to mitigate risks, meet technical and functional requirements, and ensure compliance with safety and ethical standards before deployment.__

## Model Version(s)
1.0.0

## Training, Testing, and Evaluation Datasets:

### Training Dataset
**Data Modality:** Tabular
**Training Data Size:** 38 million tables across 6.4 million graphs
**Data Collection Method by dataset:** [Hybrid: Automated, Synthetic]
**Labeling Method by dataset:** [Automated]
**Properties:** Kumo Relational was pretrained on synthetic tabular and relational data. Linguistic characteristics are not applicable for tabular data.

### Testing Dataset
**Data Collection Method by dataset:** [Hybrid: Automated, Manually-Collected]
**Labeling Method by dataset:** [Hybrid: Automated, Manually-Labeled]
**Properties:** Release testing uses real-world tabular and relational benchmark data. The combined testing and evaluation data includes approximately 100 tables and 2 billion rows across 15 graphs. Linguistic characteristics are not applicable for tabular data.

### Evaluation Dataset
**Evaluation Benchmark Score:** Undisclosed
**Data Collection Method by dataset:** [Hybrid: Automated, Manually-Collected]
**Labeling Method by dataset:** [Hybrid: Automated, Manually-Labeled]
**Properties:** Evaluation uses real-world tabular and relational benchmark data. The combined testing and evaluation data includes approximately 100 tables and 2 billion rows across 15 graphs. Linguistic characteristics are not applicable for tabular data. Kumo Relational was not trained or tuned on these datasets or tasks.

## Inference
**Acceleration Engine:** Kumo Relational driver, release 1.0.0
**Supported Tasks:** Binary classification, multiclass classification, regression, forecasting, and temporal link prediction
**API Endpoints:** `POST /v1/predictions`, `POST /v1/sessions`, `POST /v1/sessions/{session_id}/predictions`, and `DELETE /v1/sessions/{session_id}`
**Test Hardware:**
- NVIDIA A10G Tensor Core GPU
- NVIDIA H100 Tensor Core GPU
- NVIDIA L4 Tensor Core GPU
- NVIDIA L40S GPU

## Ethical Considerations
NVIDIA believes Trustworthy AI is a shared responsibility and we have established policies and practices to enable development for a wide array of AI applications. Developers should work with their internal developer team to ensure these software components meet requirements for the relevant industry and use case and address unforeseen product misuse.

Users are responsible for model inputs and outputs. Users are responsible for ensuring safe integration of this model, including implementing guardrails as well as other safety mechanisms, prior to deployment.

Please report model quality, risk, security vulnerabilities or NVIDIA AI Concerns [here](https://www.nvidia.com/en-us/support/submit-security-vulnerability/).53:T871,| Field | Response |
| :---- | :---- |
| Intended Task/Domain: | Binary classification, multiclass classification, regression, forecasting, and temporal link prediction over relational, multi-table structured data. |
| Model Type: | Transformer-based relational foundation model. |
| Intended Users: | Developers and data scientists building structured-data prediction applications. |
| Output: | Task-dependent predictions, probabilities, scores, rankings, quantiles, embeddings, and single-row diagnostic explanations. |
| Describe how the model works: | NVIDIA Kumo Relational 1.0.0 encodes rows with a table-invariant row encoder and exchanges information across related tables and context labels with a Relational Graph Transformer. |
| Name the adversely impacted groups this has been tested to deliver comparable outcomes regardless of: | No protected-class parity evaluation was reported. |
| Technical Limitations & Mitigation: | Performance depends on the declared schema, relationships, context examples, and data used in the deployment. Validate the model on data representative of your specific use case before deployment. |
| Verified to have met prescribed NVIDIA quality standards: | Yes |
| Performance Metrics: | Refer to the [KumoRFM whitepaper](https://arxiv.org/abs/2604.12596) for published benchmark metrics across 30 predictive tasks from seven public RelBench datasets. |
| Potential Known Risks: | Incorrect schemas, relationships, context labels, or nonrepresentative data can produce inaccurate predictions. Do not use outputs without use-case-specific validation and appropriate human oversight. |
| Licensing | **GOVERNING TERMS:** The NIM container is governed by the [NVIDIA Software License Agreement](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-software-license-agreement/) and the [Product-Specific Terms for NVIDIA AI Products](https://www.nvidia.com/en-us/agreements/enterprise-software/product-specific-terms-for-ai-products/); and the use of the model is governed by the [NVIDIA Open Model License Agreement](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license/). |54:Tfbc,import json

import requests


payload = {
    "model": "kumo-relational",
    "task": {
        "kind": "binary_classification",
        "target": {
            "column_name": "label",
            "dtype": "bool",
            "classes": ["false", "true"],
            "positive_class": "true",
        },
        "entity_table_names": ["accounts"],
        "anchor_time_column": "anchor_time",
    },
    "schema": {
        "instance_table": {
            "columns": {
                "instance_id": {
                    "dtype": "int64",
                    "stype": "ID",
                    "nullable": False,
                },
                "anchor_time": {
                    "dtype": "timestamp[us]",
                    "stype": "timestamp",
                    "nullable": False,
                },
                "account_id": {
                    "dtype": "int64",
                    "stype": "ID",
                    "nullable": False,
                },
                "label": {
                    "dtype": "bool",
                    "stype": "categorical",
                },
            },
            "primary_key": "instance_id",
        },
        "related_tables": {
            "accounts": {
                "columns": {
                    "instance_id": {
                        "dtype": "int64",
                        "stype": "ID",
                        "nullable": False,
                    },
                    "account_id": {
                        "dtype": "int64",
                        "stype": "ID",
                        "nullable": False,
                    },
                    "amount": {
                        "dtype": "float64",
                        "stype": "numerical",
                    },
                    "segment": {
                        "dtype": "string",
                        "stype": "categorical",
                    },
                },
                "primary_key": ["instance_id", "account_id"],
            }
        },
        "relationships": [
            {
                "source_columns": ["instance_id", "account_id"],
                "target_table": "accounts",
                "target_columns": ["instance_id", "account_id"],
            }
        ],
    },
    "context": {
        "instance_table": {
            "format": "arrays",
            "columns": ["instance_id", "anchor_time", "account_id", "label"],
            "rows": [
                [0, "2025-01-01T00:00:00Z", 100, False],
                [1, "2025-01-01T00:00:00Z", 101, True],
                [2, "2025-01-02T00:00:00Z", 102, False],
                [3, "2025-01-02T00:00:00Z", 103, True],
            ],
        },
        "related_tables": {
            "accounts": {
                "format": "arrays",
                "columns": ["instance_id", "account_id", "amount", "segment"],
                "rows": [
                    [0, 100, 10.5, "small"],
                    [1, 101, 250.0, "enterprise"],
                    [2, 102, 12.0, "small"],
                    [3, 103, 300.0, "enterprise"],
                ],
            }
        },
    },
    "predict": {
        "instance_table": {
            "format": "arrays",
            "columns": ["instance_id", "anchor_time", "account_id"],
            "rows": [[4, "2025-02-01T00:00:00Z", 104]],
        },
        "related_tables": {
            "accounts": {
                "format": "arrays",
                "columns": ["instance_id", "account_id", "amount", "segment"],
                "rows": [[4, 104, 275.0, "enterprise"]],
            }
        },
    },
    "output": {"fields": ["prediction", "probabilities"]},
}

response = requests.post(
    "https://ai.api.nvidia.com/v1/structured-data/nvidia/kumo-relational/predictions",
    headers={
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": "Bearer $NVIDIA_API_KEY",
    },
    json=payload,
)
response.raise_for_status()

print(json.dumps(response.json(), indent=2))
55:Tde5,async function main() {
  const payload = {
    model: "kumo-relational",
    task: {
      kind: "binary_classification",
      target: {
        column_name: "label",
        dtype: "bool",
        classes: ["false", "true"],
        positive_class: "true",
      },
      entity_table_names: ["accounts"],
      anchor_time_column: "anchor_time",
    },
    schema: {
      instance_table: {
        columns: {
          instance_id: {
            dtype: "int64",
            stype: "ID",
            nullable: false,
          },
          anchor_time: {
            dtype: "timestamp[us]",
            stype: "timestamp",
            nullable: false,
          },
          account_id: {
            dtype: "int64",
            stype: "ID",
            nullable: false,
          },
          label: {
            dtype: "bool",
            stype: "categorical",
          },
        },
        primary_key: "instance_id",
      },
      related_tables: {
        accounts: {
          columns: {
            instance_id: {
              dtype: "int64",
              stype: "ID",
              nullable: false,
            },
            account_id: {
              dtype: "int64",
              stype: "ID",
              nullable: false,
            },
            amount: {
              dtype: "float64",
              stype: "numerical",
            },
            segment: {
              dtype: "string",
              stype: "categorical",
            },
          },
          primary_key: ["instance_id", "account_id"],
        },
      },
      relationships: [
        {
          source_columns: ["instance_id", "account_id"],
          target_table: "accounts",
          target_columns: ["instance_id", "account_id"],
        },
      ],
    },
    context: {
      instance_table: {
        format: "arrays",
        columns: ["instance_id", "anchor_time", "account_id", "label"],
        rows: [
          [0, "2025-01-01T00:00:00Z", 100, false],
          [1, "2025-01-01T00:00:00Z", 101, true],
          [2, "2025-01-02T00:00:00Z", 102, false],
          [3, "2025-01-02T00:00:00Z", 103, true],
        ],
      },
      related_tables: {
        accounts: {
          format: "arrays",
          columns: ["instance_id", "account_id", "amount", "segment"],
          rows: [
            [0, 100, 10.5, "small"],
            [1, 101, 250.0, "enterprise"],
            [2, 102, 12.0, "small"],
            [3, 103, 300.0, "enterprise"],
          ],
        },
      },
    },
    predict: {
      instance_table: {
        format: "arrays",
        columns: ["instance_id", "anchor_time", "account_id"],
        rows: [[4, "2025-02-01T00:00:00Z", 104]],
      },
      related_tables: {
        accounts: {
          format: "arrays",
          columns: ["instance_id", "account_id", "amount", "segment"],
          rows: [[4, 104, 275.0, "enterprise"]],
        },
      },
    },
    output: {
      fields: ["prediction", "probabilities"],
    },
  };

  const response = await fetch(
    "https://ai.api.nvidia.com/v1/structured-data/nvidia/kumo-relational/predictions",
    {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        Authorization: "Bearer $NVIDIA_API_KEY",
      },
      body: JSON.stringify(payload),
    },
  );

  if (!response.ok) {
    throw new Error(
      `Request failed: ${response.status} ${await response.text()}`,
    );
  }

  const result = await response.json();
  console.log(JSON.stringify(result, null, 2));
}

main();
56:Tb03,curl "https://ai.api.nvidia.com/v1/structured-data/nvidia/kumo-relational/predictions" \
  -H "Authorization: Bearer $NVIDIA_API_KEY" \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "kumo-relational",
    "task": {
      "kind": "binary_classification",
      "target": {"column_name": "label", "dtype": "bool", "classes": ["false", "true"], "positive_class": "true"},
      "entity_table_names": ["accounts"],
      "anchor_time_column": "anchor_time"
    },
    "schema": {
      "instance_table": {
        "columns": {
          "instance_id": {"dtype": "int64", "stype": "ID", "nullable": false},
          "anchor_time": {"dtype": "timestamp[us]", "stype": "timestamp", "nullable": false},
          "account_id": {"dtype": "int64", "stype": "ID", "nullable": false},
          "label": {"dtype": "bool", "stype": "categorical"}
        },
        "primary_key": "instance_id"
      },
      "related_tables": {
        "accounts": {
          "columns": {
            "instance_id": {"dtype": "int64", "stype": "ID", "nullable": false},
            "account_id": {"dtype": "int64", "stype": "ID", "nullable": false},
            "amount": {"dtype": "float64", "stype": "numerical"},
            "segment": {"dtype": "string", "stype": "categorical"}
          },
          "primary_key": ["instance_id", "account_id"]
        }
      },
      "relationships": [{
        "source_columns": ["instance_id", "account_id"],
        "target_table": "accounts",
        "target_columns": ["instance_id", "account_id"]
      }]
    },
    "context": {
      "instance_table": {
        "format": "arrays",
        "columns": ["instance_id", "anchor_time", "account_id", "label"],
        "rows": [
          [0, "2025-01-01T00:00:00Z", 100, false],
          [1, "2025-01-01T00:00:00Z", 101, true],
          [2, "2025-01-02T00:00:00Z", 102, false],
          [3, "2025-01-02T00:00:00Z", 103, true]
        ]
      },
      "related_tables": {
        "accounts": {
          "format": "arrays",
          "columns": ["instance_id", "account_id", "amount", "segment"],
          "rows": [
            [0, 100, 10.5, "small"],
            [1, 101, 250.0, "enterprise"],
            [2, 102, 12.0, "small"],
            [3, 103, 300.0, "enterprise"]
          ]
        }
      }
    },
    "predict": {
      "instance_table": {
        "format": "arrays",
        "columns": ["instance_id", "anchor_time", "account_id"],
        "rows": [[4, "2025-02-01T00:00:00Z", 104]]
      },
      "related_tables": {
        "accounts": {
          "format": "arrays",
          "columns": ["instance_id", "account_id", "amount", "segment"],
          "rows": [[4, 104, 275.0, "enterprise"]]
        }
      }
    },
    "output": {"fields": ["prediction", "probabilities"]}
  }'
49:[["$","$L34",".0",{"state":{"mutations":[],"queries":[{"dehydratedAt":1791535161221,"state":{"data":"$2b:props:state:queries:0:state:data","dataUpdateCount":1,"dataUpdatedAt":1791535161161,"error":null,"errorUpdateCount":0,"errorUpdatedAt":0,"fetchFailureCount":0,"fetchFailureReason":null,"fetchMeta":null,"isInvalidated":false,"status":"success","fetchStatus":"idle"},"queryKey":"$2b:props:state:queries:0:queryKey","queryHash":"[\"search\",\"labelsets\",\"ENDPOINT\"]"},{"dehydratedAt":1791535161221,"state":{"data":"$2b:props:state:queries:1:state:data","dataUpdateCount":1,"dataUpdatedAt":1791535161162,"error":null,"errorUpdateCount":0,"errorUpdatedAt":0,"fetchFailureCount":0,"fetchFailureReason":null,"fetchMeta":null,"isInvalidated":false,"status":"success","fetchStatus":"idle"},"queryKey":"$2b:props:state:queries:1:queryKey","queryHash":"[\"endpoints\",\"license\",\"kumo-relational\"]"},{"dehydratedAt":1791535161221,"state":{"data":null,"dataUpdateCount":1,"dataUpdatedAt":1791535161162,"error":null,"errorUpdateCount":0,"errorUpdatedAt":0,"fetchFailureCount":0,"fetchFailureReason":null,"fetchMeta":null,"isInvalidated":false,"status":"success","fetchStatus":"idle"},"queryKey":"$2b:props:state:queries:2:queryKey","queryHash":"[\"killswitches/riva-magpie-2.enabled\"]"},{"dehydratedAt":1791535161221,"state":{"data":"$2b:props:state:queries:3:state:data","dataUpdateCount":1,"dataUpdatedAt":1791535161163,"error":null,"errorUpdateCount":0,"errorUpdatedAt":0,"fetchFailureCount":0,"fetchFailureReason":null,"fetchMeta":null,"isInvalidated":false,"status":"success","fetchStatus":"idle"},"queryKey":"$2b:props:state:queries:3:queryKey","queryHash":"[\"killswitches/media/select-example.models.yaml\"]"},{"dehydratedAt":1791535161221,"state":{"data":"$2b:props:state:queries:4:state:data","dataUpdateCount":1,"dataUpdatedAt":1791535161162,"error":null,"errorUpdateCount":0,"errorUpdatedAt":0,"fetchFailureCount":0,"fetchFailureReason":null,"fetchMeta":null,"isInvalidated":false,"status":"success","fetchStatus":"idle"},"queryKey":"$2b:props:state:queries:4:queryKey","queryHash":"[\"content/legal/model-terms-of-service.yaml\"]"},{"dehydratedAt":1791535161221,"state":{"data":"$2b:props:state:queries:5:state:data","dataUpdateCount":1,"dataUpdatedAt":1791535161163,"error":null,"errorUpdateCount":0,"errorUpdatedAt":0,"fetchFailureCount":0,"fetchFailureReason":null,"fetchMeta":null,"isInvalidated":false,"status":"success","fetchStatus":"idle"},"queryKey":"$2b:props:state:queries:5:queryKey","queryHash":"[\"content/legal/playground-disclaimers.yaml\"]"}]},"children":["$","$L51",null,{"initialState":{"artifact":{"artifactType":"ENDPOINT","name":"kumo-relational","displayName":"Kumo Relational","publisher":"nvidia","shortDescription":"A relational foundation model for prediction over structured, multi-table data.","logo":"https://assets.ngc.nvidia.com/products/api-catalog/images/kumo-relational.jpg","labels":["Graph Learning","Prediction","Relational Models","Structured Data","nimType:endpoint:nim_type_preview","nimType:endpoint:nim_type_run_anywhere"],"attributes":[{"key":"AVAILABLE","value":"true"},{"key":"PREVIEW","value":"true"}],"updatedDate":"2026-09-15T21:56:35.043Z","bias":"| Field | Response |\n| :---- | :---- |\n| Participation considerations from adversely impacted groups [protected classes](https://www.senate.ca.gov/content/protected-classes) in model design and testing: | None |\n| Measures taken to mitigate against unwanted bias: | No protected-class-specific mitigation measures were reported; users should evaluate deployment-specific data for disparate outcomes. |","canGuestDownload":true,"createdDate":"2026-09-15T21:56:35.043Z","description":"$52","explainability":"$53","isPublic":true,"isReadOnly":true,"orgName":"qc69jvmznzxy","privacy":"| Field | Response |\n| :---- | :---- |\n| Generatable or reverse engineerable personal data? | No |\n| Personal data used to create this model? | No |\n| Was consent obtained for any personal data used? | No personal data was used to create the model, so consent was not required. |\n| How often is dataset reviewed? | Before Release |\n| Was data from user interactions with the AI model (e.g. user input and prompts) used to train the model? | No |\n| Is there provenance for all datasets used in training? | Yes |\n| Does data labeling (annotation, metadata) comply with privacy laws? | Yes |\n| Is data compliant with data subject requests for data correction or removal, if such a request was made? | No personal data was used to create the model; correction or removal requests therefore do not apply to the training data. |\n| Applicable privacy policy | [NVIDIA Privacy Policy](https://www.nvidia.com/en-us/about-nvidia/privacy-policy/) |","safetyAndSecurity":"| Field | Response |\n| :---- | :---- |\n| Model Application Fields: | Not Applicable |\n| Describe the life critical impact: | Not Applicable |\n| Use Case Restrictions: | Use of the NIM container must comply with the [NVIDIA Software License Agreement](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-software-license-agreement/) and the [Product-Specific Terms for NVIDIA AI Products](https://www.nvidia.com/en-us/agreements/enterprise-software/product-specific-terms-for-ai-products/). Use of the model must comply with the [NVIDIA Open Model License Agreement](https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license/). |\n| Model and dataset restrictions: | The Principle of least privilege (PoLP) is applied limiting access for dataset generation and model development. Restrictions enforce dataset access during training, and dataset license constraints adhered to. |"},"specAttributes":"$4a:props:spec:attributes","modelPath":"/nvidia/kumo-relational","openApiSpec":{"openapi":"3.1.0","info":{"title":"NVIDIA Kumo Relational","description":"Universal TFM API for the NVIDIA Kumo Relational NIM.","version":"1.0.0","termsOfService":"https://www.nvidia.com/en-us/data-center/products/nvidia-ai-enterprise/eula/","contact":{"name":"NVIDIA Enterprise Support","url":"https://www.nvidia.com/en-us/support/enterprise/"},"license":{"name":"NVIDIA Proprietary","url":"https://www.nvidia.com/en-us/data-center/products/nvidia-ai-enterprise/eula/"}},"servers":[{"url":"https://ai.api.nvidia.com"}],"tags":[{"name":"Kumo Relational","description":"Relational foundation model prediction endpoints over multi-table data."}],"paths":{"/v1/structured-data/nvidia/kumo-relational/models":{"get":{"tags":["Kumo Relational"],"summary":"List available models","operationId":"nvidia-kumo-relational-infer","responses":{"200":{"description":"Available models","content":{"application/json":{"schema":{"type":"object","properties":{"object":{"type":"string","example":"list"},"data":{"type":"array","items":{"type":"object","properties":{"id":{"type":"string","example":"kumo-relational"},"object":{"type":"string","example":"model"},"created":{"type":"integer"},"owned_by":{"type":"string","example":"nvidia"}},"additionalProperties":true}}},"additionalProperties":true}}}}},"x-nvai-meta":{"name":"List models","path":"retrieve"}}},"/v1/structured-data/nvidia/kumo-relational/predictions":{"post":{"tags":["Kumo Relational"],"summary":"Run a Kumo Relational prediction","description":"Accepts labeled context examples and the entity to score across one or more related tables in the Universal TFM request envelope. Predictive queries are compiled into this request by the NVIDIA Kumo Predict SDK; the original query is preserved in metadata.source_query.","operationId":"nvidia-kumo-relational-statuspolling","requestBody":{"required":true,"content":{"application/json":{"schema":{"type":"object","required":["model","task","schema","context","predict","output"],"properties":{"model":{"type":"string","enum":["kumo-relational"],"description":"TFM model family requested by the caller."},"task":{"type":"object","required":["kind","target"],"properties":{"kind":{"type":"string","description":"Prediction problem type.","enum":["classification","binary_classification","multiclass_classification","regression"]},"target":{"type":"object","required":["dtype"],"properties":{"column_name":{"type":"string","description":"Target label column for context rows."},"table_name":{"type":"string","description":"Table that holds the target column, when it is not the instance table."},"dtype":{"type":"string","description":"Logical dtype of the target value.","example":"bool"},"classes":{"type":"array","items":{"type":"string"}},"positive_class":{"type":"string"}},"additionalProperties":true},"entity_table_names":{"type":"array","description":"The single entity table that predictions are made for.","minItems":1,"maxItems":1,"uniqueItems":true,"items":{"type":"string"}},"anchor_time_column":{"type":"string","description":"Instance-table timestamp column defining the prediction anchor time."}},"additionalProperties":true},"schema":{"type":"object","required":["instance_table"],"properties":{"instance_table":{"type":"object","required":["columns","primary_key"],"properties":{"columns":{"type":"object","additionalProperties":{"type":"object","required":["dtype"],"properties":{"dtype":{"type":"string","description":"Logical dtype such as int64, float32, string, bool, or timestamp[us]."},"stype":{"type":"string","description":"Semantic type such as ID, numerical, categorical, timestamp, or text."},"nullable":{"type":"boolean","default":true}},"additionalProperties":true}},"primary_key":{"oneOf":[{"type":"string"},{"type":"array","minItems":1,"items":{"type":"string"}}],"description":"One or more primary key columns. Kumo Relational requires the instance table primary key to be instance_id, and every related table to include an instance_id column."}},"additionalProperties":false},"related_tables":{"type":"object","description":"Related table schemas keyed by table name (entity and fact tables).","additionalProperties":{"type":"object","required":["columns","primary_key"],"properties":{"columns":{"type":"object","additionalProperties":{"type":"object","required":["dtype"],"properties":{"dtype":{"type":"string","description":"Logical dtype such as int64, float32, string, bool, or timestamp[us]."},"stype":{"type":"string","description":"Semantic type such as ID, numerical, categorical, timestamp, or text."},"nullable":{"type":"boolean","default":true}},"additionalProperties":true}},"primary_key":{"oneOf":[{"type":"string"},{"type":"array","minItems":1,"items":{"type":"string"}}],"description":"One or more primary key columns. Kumo Relational requires the instance table primary key to be instance_id, and every related table to include an instance_id column."}},"additionalProperties":false}},"relationships":{"type":"array","description":"Relationships linking the instance, entity, and fact tables.","items":{"type":"object","required":["source_columns","target_table","target_columns"],"properties":{"source_table":{"type":"string","description":"Source table name. Defaults to the instance table when omitted."},"source_columns":{"type":"array","items":{"type":"string"}},"target_table":{"type":"string"},"target_columns":{"type":"array","items":{"type":"string"}}},"additionalProperties":true}}},"additionalProperties":false},"context":{"type":"object","required":["instance_table"],"properties":{"instance_table":{"oneOf":[{"type":"object","required":["format","columns","rows"],"properties":{"format":{"type":"string","enum":["arrays"]},"columns":{"type":"array","minItems":1,"description":"Column order for arrays-format rows.","items":{"type":"string"}},"rows":{"type":"array","description":"Arrays-format table rows. Each row follows the order in columns.","items":{"type":"array","items":{"anyOf":[{"type":"string"},{"type":"number"},{"type":"integer"},{"type":"boolean"},{"type":"null"}]}}}},"additionalProperties":false}],"description":"Table payload descriptor. Arrays are the supported table payload format."},"related_tables":{"type":"object","description":"Related table payloads keyed by table name (entity and fact tables).","additionalProperties":{"oneOf":[{"type":"object","required":["format","columns","rows"],"properties":{"format":{"type":"string","enum":["arrays"]},"columns":{"type":"array","minItems":1,"description":"Column order for arrays-format rows.","items":{"type":"string"}},"rows":{"type":"array","description":"Arrays-format table rows. Each row follows the order in columns.","items":{"type":"array","items":{"anyOf":[{"type":"string"},{"type":"number"},{"type":"integer"},{"type":"boolean"},{"type":"null"}]}}}},"additionalProperties":false}],"description":"Table payload descriptor. Arrays are the supported table payload format."}},"metadata":{"type":"object","additionalProperties":true}},"additionalProperties":false},"predict":{"type":"object","required":["instance_table"],"properties":{"instance_table":{"oneOf":[{"type":"object","required":["format","columns","rows"],"properties":{"format":{"type":"string","enum":["arrays"]},"columns":{"type":"array","minItems":1,"description":"Column order for arrays-format rows.","items":{"type":"string"}},"rows":{"type":"array","description":"Arrays-format table rows. Each row follows the order in columns.","items":{"type":"array","items":{"anyOf":[{"type":"string"},{"type":"number"},{"type":"integer"},{"type":"boolean"},{"type":"null"}]}}}},"additionalProperties":false}],"description":"Table payload descriptor. Arrays are the supported table payload format."},"related_tables":{"type":"object","description":"Related table payloads keyed by table name (entity and fact tables).","additionalProperties":{"oneOf":[{"type":"object","required":["format","columns","rows"],"properties":{"format":{"type":"string","enum":["arrays"]},"columns":{"type":"array","minItems":1,"description":"Column order for arrays-format rows.","items":{"type":"string"}},"rows":{"type":"array","description":"Arrays-format table rows. Each row follows the order in columns.","items":{"type":"array","items":{"anyOf":[{"type":"string"},{"type":"number"},{"type":"integer"},{"type":"boolean"},{"type":"null"}]}}}},"additionalProperties":false}],"description":"Table payload descriptor. Arrays are the supported table payload format."}},"metadata":{"type":"object","additionalProperties":true}},"additionalProperties":false},"output":{"type":"object","required":["fields"],"properties":{"fields":{"type":"array","minItems":1,"items":{"type":"string","enum":["prediction","probabilities","scores","rankings","embeddings","quantiles","explanation"]}},"prediction_statistic":{"type":"string","example":"mean"},"quantile_levels":{"type":"array","items":{"type":"number"}}},"additionalProperties":true},"inference":{"type":"object","properties":{"run_mode":{"type":"string","description":"Inference run mode such as fast, normal, or best.","example":"best"},"use_prediction_time":{"type":"boolean","default":false},"inference_config":{"type":"object","additionalProperties":true}},"additionalProperties":true},"metadata":{"type":"object","properties":{"request_id":{"type":"string"},"trace_id":{"type":"string"},"source_query":{"type":"string","description":"Original Kumo Relational predictive query that produced this request."}},"additionalProperties":true}},"additionalProperties":false},"examples":{"multitable_binary_classification":{"summary":"Multi-table binary classification (users + orders)","value":{"model":"kumo-relational","task":{"kind":"binary_classification","target":{"column_name":"TARGET","dtype":"bool","classes":["false","true"],"positive_class":"true"},"entity_table_names":["users"],"anchor_time_column":"__kumo_anchor_time"},"schema":{"instance_table":{"columns":{"instance_id":{"dtype":"int64","stype":"ID","nullable":false},"__kumo_entity_ref_0":{"dtype":"int64","stype":"ID"},"__kumo_anchor_time":{"dtype":"timestamp[us]","stype":"timestamp","nullable":false},"TARGET":{"dtype":"bool","stype":"categorical"}},"primary_key":"instance_id"},"related_tables":{"users":{"columns":{"instance_id":{"dtype":"int64","stype":"ID","nullable":false},"age":{"dtype":"int64","stype":"numerical"},"country":{"dtype":"string","stype":"categorical"},"user_id":{"dtype":"int64","nullable":false},"plan":{"dtype":"string","stype":"categorical"}},"primary_key":["instance_id","user_id"]},"orders":{"columns":{"instance_id":{"dtype":"int64","stype":"ID","nullable":false},"__node_id":{"dtype":"int64","stype":"ID","nullable":false},"amount":{"dtype":"float64","stype":"numerical"},"order_date":{"dtype":"timestamp[us]","stype":"timestamp"},"category":{"dtype":"string","stype":"categorical"},"user_id":{"dtype":"int64","stype":"ID"}},"primary_key":["instance_id","__node_id"]}},"relationships":[{"source_columns":["__kumo_entity_ref_0"],"target_table":"users","target_columns":["user_id"]},{"source_table":"orders","source_columns":["user_id"],"target_table":"users","target_columns":["user_id"]}]},"context":{"instance_table":{"format":"arrays","columns":["instance_id","__kumo_entity_ref_0","__kumo_anchor_time","TARGET"],"rows":[[0,3,"2024-12-02T00:00:00.000000Z",false],[1,2,"2024-12-02T00:00:00.000000Z",false],[2,1,"2024-12-02T00:00:00.000000Z",false],[3,1,"2024-11-02T00:00:00.000000Z",true],[4,3,"2024-11-02T00:00:00.000000Z",false],[5,2,"2024-11-02T00:00:00.000000Z",false],[6,2,"2024-10-03T00:00:00.000000Z",true],[7,3,"2024-10-03T00:00:00.000000Z",true],[8,1,"2024-10-03T00:00:00.000000Z",true]]},"related_tables":{"users":{"format":"arrays","columns":["instance_id","age","country","user_id","plan"],"rows":[[0,39,"GB",3,"free"],[1,54,"DE",2,"enterprise"],[2,24,"US",1,"pro"],[3,24,"US",1,"pro"],[4,39,"GB",3,"free"],[5,54,"DE",2,"enterprise"],[6,54,"DE",2,"enterprise"],[7,39,"GB",3,"free"],[8,24,"US",1,"pro"]]},"orders":{"format":"arrays","columns":["instance_id","__node_id","amount","order_date","category","user_id"],"rows":[[0,0,52.69,"2024-10-15T00:00:00.000000Z","electronics",3],[1,1,91.86,"2024-09-20T00:00:00.000000Z","toys",2],[1,2,159.76,"2024-11-01T00:00:00.000000Z","toys",2],[2,3,95.5,"2024-09-10T00:00:00.000000Z","books",1],[2,4,162.75,"2024-10-05T00:00:00.000000Z","electronics",1],[2,5,113.64,"2024-12-01T00:00:00.000000Z","food",1],[3,6,95.5,"2024-09-10T00:00:00.000000Z","books",1],[3,7,162.75,"2024-10-05T00:00:00.000000Z","electronics",1],[4,8,52.69,"2024-10-15T00:00:00.000000Z","electronics",3],[5,9,91.86,"2024-09-20T00:00:00.000000Z","toys",2],[5,10,159.76,"2024-11-01T00:00:00.000000Z","toys",2],[6,11,91.86,"2024-09-20T00:00:00.000000Z","toys",2],[8,12,95.5,"2024-09-10T00:00:00.000000Z","books",1]]}}},"predict":{"instance_table":{"format":"arrays","columns":["instance_id","__kumo_entity_ref_0","__kumo_anchor_time"],"rows":[[9,1,"2025-01-01T00:00:00.000000Z"]]},"related_tables":{"users":{"format":"arrays","columns":["instance_id","age","country","user_id","plan"],"rows":[[9,24,"US",1,"pro"]]},"orders":{"format":"arrays","columns":["instance_id","__node_id","amount","order_date","category","user_id"],"rows":[[9,13,95.5,"2024-09-10T00:00:00.000000Z","books",1],[9,14,162.75,"2024-10-05T00:00:00.000000Z","electronics",1],[9,15,113.64,"2024-12-01T00:00:00.000000Z","food",1]]}}},"output":{"fields":["prediction","probabilities"]},"inference":{"run_mode":"fast","use_prediction_time":false,"inference_config":{"kind":"classification","num_estimators":1,"column_shuffle":false,"category_shuffle":false,"hop_shuffle":false,"class_shuffle":false}},"metadata":{"request_id":"kumo-relational-catalog-demo-001","source_query":"PREDICT COUNT(orders.*, 0, 30, days) > 0 FOR users.user_id=1"}}}}}}},"responses":{"200":{"description":"Prediction response","content":{"application/json":{"schema":{"type":"object","required":["id","model","predictions","metadata"],"properties":{"id":{"type":"string"},"model":{"type":"string","example":"kumo-relational"},"predictions":{"type":"array","items":{"type":"object","required":["row_index"],"properties":{"id":{"type":"string"},"row_index":{"type":"integer","minimum":0},"prediction":{"anyOf":[{"type":"string"},{"type":"number"},{"type":"integer"},{"type":"boolean"},{"type":"null"}]},"probabilities":{"type":"object","additionalProperties":{"type":"number"}},"scores":{"type":"array","items":{"type":"number"}},"rankings":{"type":"array","items":{"type":"object","required":["id","score"],"properties":{"id":{"type":"string"},"score":{"type":"number"}},"additionalProperties":false}},"embeddings":{"type":"array","items":{"type":"number"}},"quantiles":{"type":"object","additionalProperties":{"type":"number"}},"explanation":{"type":"object","required":["format"],"minProperties":2,"properties":{"format":{"type":"string","description":"Discriminator naming the model-defined explanation shape."}},"additionalProperties":true},"metadata":{"type":"object","additionalProperties":true}},"additionalProperties":true}},"metadata":{"type":"object","required":["task_kind"],"properties":{"task_kind":{"type":"string"},"output_type":{"type":"string"},"adapter":{"type":"string"},"normalized_request_kind":{"type":"string"},"stub_backend":{"type":"boolean"}},"additionalProperties":true}},"additionalProperties":false},"examples":{"multitable_binary_classification":{"summary":"Binary classification response","value":{"id":"pred_kumo_relational_001","model":"kumo-relational","predictions":[{"id":"9","row_index":0,"prediction":true,"probabilities":{"false":0.18,"true":0.82},"metadata":{"backend_status":"driver"}}],"metadata":{"task_kind":"binary_classification","adapter":"kumo_relational","backend_status":"driver"}}}}}}},"400":{"description":"Problem details for a failed request","content":{"application/problem+json":{"schema":{"type":"object","required":["type","status","title","detail","code"],"properties":{"type":{"type":"string","format":"uri-reference","description":"URI identifying the problem type."},"status":{"type":"integer","minimum":100,"maximum":599,"description":"HTTP status code for this occurrence of the problem."},"title":{"type":"string","description":"Short, human-readable summary of the problem."},"detail":{"type":"string","description":"Human-readable explanation specific to this occurrence."},"code":{"type":"string","maxLength":1024,"description":"Stable application-specific code identifying the precise failure."},"instance":{"type":"string","format":"uri-reference","description":"URI identifying this specific problem occurrence."}},"additionalProperties":true,"example":{"type":"/problems/validation-failed","status":422,"title":"Validation failed","detail":"Prediction request contains invalid table data.","code":"VALIDATION_FAILED"}}}}},"413":{"description":"Problem details for a failed request","content":{"application/problem+json":{"schema":{"type":"object","required":["type","status","title","detail","code"],"properties":{"type":{"type":"string","format":"uri-reference","description":"URI identifying the problem type."},"status":{"type":"integer","minimum":100,"maximum":599,"description":"HTTP status code for this occurrence of the problem."},"title":{"type":"string","description":"Short, human-readable summary of the problem."},"detail":{"type":"string","description":"Human-readable explanation specific to this occurrence."},"code":{"type":"string","maxLength":1024,"description":"Stable application-specific code identifying the precise failure."},"instance":{"type":"string","format":"uri-reference","description":"URI identifying this specific problem occurrence."}},"additionalProperties":true,"example":{"type":"/problems/validation-failed","status":422,"title":"Validation failed","detail":"Prediction request contains invalid table data.","code":"VALIDATION_FAILED"}}}}},"415":{"description":"Problem details for a failed request","content":{"application/problem+json":{"schema":{"type":"object","required":["type","status","title","detail","code"],"properties":{"type":{"type":"string","format":"uri-reference","description":"URI identifying the problem type."},"status":{"type":"integer","minimum":100,"maximum":599,"description":"HTTP status code for this occurrence of the problem."},"title":{"type":"string","description":"Short, human-readable summary of the problem."},"detail":{"type":"string","description":"Human-readable explanation specific to this occurrence."},"code":{"type":"string","maxLength":1024,"description":"Stable application-specific code identifying the precise failure."},"instance":{"type":"string","format":"uri-reference","description":"URI identifying this specific problem occurrence."}},"additionalProperties":true,"example":{"type":"/problems/validation-failed","status":422,"title":"Validation failed","detail":"Prediction request contains invalid table data.","code":"VALIDATION_FAILED"}}}}},"422":{"description":"Problem details for a failed request","content":{"application/problem+json":{"schema":{"type":"object","required":["type","status","title","detail","code"],"properties":{"type":{"type":"string","format":"uri-reference","description":"URI identifying the problem type."},"status":{"type":"integer","minimum":100,"maximum":599,"description":"HTTP status code for this occurrence of the problem."},"title":{"type":"string","description":"Short, human-readable summary of the problem."},"detail":{"type":"string","description":"Human-readable explanation specific to this occurrence."},"code":{"type":"string","maxLength":1024,"description":"Stable application-specific code identifying the precise failure."},"instance":{"type":"string","format":"uri-reference","description":"URI identifying this specific problem occurrence."}},"additionalProperties":true,"example":{"type":"/problems/validation-failed","status":422,"title":"Validation failed","detail":"Prediction request contains invalid table data.","code":"VALIDATION_FAILED"}}}}},"429":{"description":"Problem details for a failed request","content":{"application/problem+json":{"schema":{"type":"object","required":["type","status","title","detail","code"],"properties":{"type":{"type":"string","format":"uri-reference","description":"URI identifying the problem type."},"status":{"type":"integer","minimum":100,"maximum":599,"description":"HTTP status code for this occurrence of the problem."},"title":{"type":"string","description":"Short, human-readable summary of the problem."},"detail":{"type":"string","description":"Human-readable explanation specific to this occurrence."},"code":{"type":"string","maxLength":1024,"description":"Stable application-specific code identifying the precise failure."},"instance":{"type":"string","format":"uri-reference","description":"URI identifying this specific problem occurrence."}},"additionalProperties":true,"example":{"type":"/problems/validation-failed","status":422,"title":"Validation failed","detail":"Prediction request contains invalid table data.","code":"VALIDATION_FAILED"}}}}},"500":{"description":"Problem details for a failed request","content":{"application/problem+json":{"schema":{"type":"object","required":["type","status","title","detail","code"],"properties":{"type":{"type":"string","format":"uri-reference","description":"URI identifying the problem type."},"status":{"type":"integer","minimum":100,"maximum":599,"description":"HTTP status code for this occurrence of the problem."},"title":{"type":"string","description":"Short, human-readable summary of the problem."},"detail":{"type":"string","description":"Human-readable explanation specific to this occurrence."},"code":{"type":"string","maxLength":1024,"description":"Stable application-specific code identifying the precise failure."},"instance":{"type":"string","format":"uri-reference","description":"URI identifying this specific problem occurrence."}},"additionalProperties":true,"example":{"type":"/problems/validation-failed","status":422,"title":"Validation failed","detail":"Prediction request contains invalid table data.","code":"VALIDATION_FAILED"}}}}},"503":{"description":"Problem details for a failed request","content":{"application/problem+json":{"schema":{"type":"object","required":["type","status","title","detail","code"],"properties":{"type":{"type":"string","format":"uri-reference","description":"URI identifying the problem type."},"status":{"type":"integer","minimum":100,"maximum":599,"description":"HTTP status code for this occurrence of the problem."},"title":{"type":"string","description":"Short, human-readable summary of the problem."},"detail":{"type":"string","description":"Human-readable explanation specific to this occurrence."},"code":{"type":"string","maxLength":1024,"description":"Stable application-specific code identifying the precise failure."},"instance":{"type":"string","format":"uri-reference","description":"URI identifying this specific problem occurrence."}},"additionalProperties":true,"example":{"type":"/problems/validation-failed","status":422,"title":"Validation failed","detail":"Prediction request contains invalid table data.","code":"VALIDATION_FAILED"}}}}}},"x-nvai-meta":{"name":"Create prediction","returns":"Returns prediction rows and response metadata.","path":"create","templates":[{"title":"Predictions API","requestEjs":{"python":"$54","node.js":"$55","curl":"$56"}}]}}}},"security":[{"Token":[]}],"components":{"securitySchemes":{"Token":{"type":"http","scheme":"bearer"}},"responses":{"Problem":{"description":"Problem details for a failed request","content":{"application/problem+json":{"schema":{"type":"object","required":["type","status","title","detail","code"],"properties":{"type":{"type":"string","format":"uri-reference","description":"URI identifying the problem type."},"status":{"type":"integer","minimum":100,"maximum":599,"description":"HTTP status code for this occurrence of the problem."},"title":{"type":"string","description":"Short, human-readable summary of the problem."},"detail":{"type":"string","description":"Human-readable explanation specific to this occurrence."},"code":{"type":"string","maxLength":1024,"description":"Stable application-specific code identifying the precise failure."},"instance":{"type":"string","format":"uri-reference","description":"URI identifying this specific problem occurrence."}},"additionalProperties":true,"example":{"type":"/problems/validation-failed","status":422,"title":"Validation failed","detail":"Prediction request contains invalid table data.","code":"VALIDATION_FAILED"}}}}}},"schemas":{"ModelListResponse":{"type":"object","properties":{"object":{"type":"string","example":"list"},"data":{"type":"array","items":{"type":"object","properties":{"id":{"type":"string","example":"kumo-relational"},"object":{"type":"string","example":"model"},"created":{"type":"integer"},"owned_by":{"type":"string","example":"nvidia"}},"additionalProperties":true}}},"additionalProperties":true},"PredictionRequest":{"type":"object","required":["model","task","schema","context","predict","output"],"properties":{"model":{"type":"string","enum":["kumo-relational"],"description":"TFM model family requested by the caller."},"task":{"type":"object","required":["kind","target"],"properties":{"kind":{"type":"string","description":"Prediction problem type.","enum":["classification","binary_classification","multiclass_classification","regression"]},"target":{"type":"object","required":["dtype"],"properties":{"column_name":{"type":"string","description":"Target label column for context rows."},"table_name":{"type":"string","description":"Table that holds the target column, when it is not the instance table."},"dtype":{"type":"string","description":"Logical dtype of the target value.","example":"bool"},"classes":{"type":"array","items":{"type":"string"}},"positive_class":{"type":"string"}},"additionalProperties":true},"entity_table_names":{"type":"array","description":"The single entity table that predictions are made for.","minItems":1,"maxItems":1,"uniqueItems":true,"items":{"type":"string"}},"anchor_time_column":{"type":"string","description":"Instance-table timestamp column defining the prediction anchor time."}},"additionalProperties":true},"schema":{"type":"object","required":["instance_table"],"properties":{"instance_table":{"type":"object","required":["columns","primary_key"],"properties":{"columns":{"type":"object","additionalProperties":{"type":"object","required":["dtype"],"properties":{"dtype":{"type":"string","description":"Logical dtype such as int64, float32, string, bool, or timestamp[us]."},"stype":{"type":"string","description":"Semantic type such as ID, numerical, categorical, timestamp, or text."},"nullable":{"type":"boolean","default":true}},"additionalProperties":true}},"primary_key":{"oneOf":[{"type":"string"},{"type":"array","minItems":1,"items":{"type":"string"}}],"description":"One or more primary key columns. Kumo Relational requires the instance table primary key to be instance_id, and every related table to include an instance_id column."}},"additionalProperties":false},"related_tables":{"type":"object","description":"Related table schemas keyed by table name (entity and fact tables).","additionalProperties":{"type":"object","required":["columns","primary_key"],"properties":{"columns":{"type":"object","additionalProperties":{"type":"object","required":["dtype"],"properties":{"dtype":{"type":"string","description":"Logical dtype such as int64, float32, string, bool, or timestamp[us]."},"stype":{"type":"string","description":"Semantic type such as ID, numerical, categorical, timestamp, or text."},"nullable":{"type":"boolean","default":true}},"additionalProperties":true}},"primary_key":{"oneOf":[{"type":"string"},{"type":"array","minItems":1,"items":{"type":"string"}}],"description":"One or more primary key columns. Kumo Relational requires the instance table primary key to be instance_id, and every related table to include an instance_id column."}},"additionalProperties":false}},"relationships":{"type":"array","description":"Relationships linking the instance, entity, and fact tables.","items":{"type":"object","required":["source_columns","target_table","target_columns"],"properties":{"source_table":{"type":"string","description":"Source table name. Defaults to the instance table when omitted."},"source_columns":{"type":"array","items":{"type":"string"}},"target_table":{"type":"string"},"target_columns":{"type":"array","items":{"type":"string"}}},"additionalProperties":true}}},"additionalProperties":false},"context":{"type":"object","required":["instance_table"],"properties":{"instance_table":{"oneOf":[{"type":"object","required":["format","columns","rows"],"properties":{"format":{"type":"string","enum":["arrays"]},"columns":{"type":"array","minItems":1,"description":"Column order for arrays-format rows.","items":{"type":"string"}},"rows":{"type":"array","description":"Arrays-format table rows. Each row follows the order in columns.","items":{"type":"array","items":{"anyOf":[{"type":"string"},{"type":"number"},{"type":"integer"},{"type":"boolean"},{"type":"null"}]}}}},"additionalProperties":false}],"description":"Table payload descriptor. Arrays are the supported table payload format."},"related_tables":{"type":"object","description":"Related table payloads keyed by table name (entity and fact tables).","additionalProperties":{"oneOf":[{"type":"object","required":["format","columns","rows"],"properties":{"format":{"type":"string","enum":["arrays"]},"columns":{"type":"array","minItems":1,"description":"Column order for arrays-format rows.","items":{"type":"string"}},"rows":{"type":"array","description":"Arrays-format table rows. Each row follows the order in columns.","items":{"type":"array","items":{"anyOf":[{"type":"string"},{"type":"number"},{"type":"integer"},{"type":"boolean"},{"type":"null"}]}}}},"additionalProperties":false}],"description":"Table payload descriptor. Arrays are the supported table payload format."}},"metadata":{"type":"object","additionalProperties":true}},"additionalProperties":false},"predict":{"type":"object","required":["instance_table"],"properties":{"instance_table":{"oneOf":[{"type":"object","required":["format","columns","rows"],"properties":{"format":{"type":"string","enum":["arrays"]},"columns":{"type":"array","minItems":1,"description":"Column order for arrays-format rows.","items":{"type":"string"}},"rows":{"type":"array","description":"Arrays-format table rows. Each row follows the order in columns.","items":{"type":"array","items":{"anyOf":[{"type":"string"},{"type":"number"},{"type":"integer"},{"type":"boolean"},{"type":"null"}]}}}},"additionalProperties":false}],"description":"Table payload descriptor. Arrays are the supported table payload format."},"related_tables":{"type":"object","description":"Related table payloads keyed by table name (entity and fact tables).","additionalProperties":{"oneOf":[{"type":"object","required":["format","columns","rows"],"properties":{"format":{"type":"string","enum":["arrays"]},"columns":{"type":"array","minItems":1,"description":"Column order for arrays-format rows.","items":{"type":"string"}},"rows":{"type":"array","description":"Arrays-format table rows. Each row follows the order in columns.","items":{"type":"array","items":{"anyOf":[{"type":"string"},{"type":"number"},{"type":"integer"},{"type":"boolean"},{"type":"null"}]}}}},"additionalProperties":false}],"description":"Table payload descriptor. Arrays are the supported table payload format."}},"metadata":{"type":"object","additionalProperties":true}},"additionalProperties":false},"output":{"type":"object","required":["fields"],"properties":{"fields":{"type":"array","minItems":1,"items":{"type":"string","enum":["prediction","probabilities","scores","rankings","embeddings","quantiles","explanation"]}},"prediction_statistic":{"type":"string","example":"mean"},"quantile_levels":{"type":"array","items":{"type":"number"}}},"additionalProperties":true},"inference":{"type":"object","properties":{"run_mode":{"type":"string","description":"Inference run mode such as fast, normal, or best.","example":"best"},"use_prediction_time":{"type":"boolean","default":false},"inference_config":{"type":"object","additionalProperties":true}},"additionalProperties":true},"metadata":{"type":"object","properties":{"request_id":{"type":"string"},"trace_id":{"type":"string"},"source_query":{"type":"string","description":"Original Kumo Relational predictive query that produced this request."}},"additionalProperties":true}},"additionalProperties":false},"TaskSpec":{"type":"object","required":["kind","target"],"properties":{"kind":{"type":"string","description":"Prediction problem type.","enum":["classification","binary_classification","multiclass_classification","regression"]},"target":{"type":"object","required":["dtype"],"properties":{"column_name":{"type":"string","description":"Target label column for context rows."},"table_name":{"type":"string","description":"Table that holds the target column, when it is not the instance table."},"dtype":{"type":"string","description":"Logical dtype of the target value.","example":"bool"},"classes":{"type":"array","items":{"type":"string"}},"positive_class":{"type":"string"}},"additionalProperties":true},"entity_table_names":{"type":"array","description":"The single entity table that predictions are made for.","minItems":1,"maxItems":1,"uniqueItems":true,"items":{"type":"string"}},"anchor_time_column":{"type":"string","description":"Instance-table timestamp column defining the prediction anchor time."}},"additionalProperties":true},"TargetSpec":{"type":"object","required":["dtype"],"properties":{"column_name":{"type":"string","description":"Target label column for context rows."},"table_name":{"type":"string","description":"Table that holds the target column, when it is not the instance table."},"dtype":{"type":"string","description":"Logical dtype of the target value.","example":"bool"},"classes":{"type":"array","items":{"type":"string"}},"positive_class":{"type":"string"}},"additionalProperties":true},"StructuredSchema":{"type":"object","required":["instance_table"],"properties":{"instance_table":{"type":"object","required":["columns","primary_key"],"properties":{"columns":{"type":"object","additionalProperties":{"type":"object","required":["dtype"],"properties":{"dtype":{"type":"string","description":"Logical dtype such as int64, float32, string, bool, or timestamp[us]."},"stype":{"type":"string","description":"Semantic type such as ID, numerical, categorical, timestamp, or text."},"nullable":{"type":"boolean","default":true}},"additionalProperties":true}},"primary_key":{"oneOf":[{"type":"string"},{"type":"array","minItems":1,"items":{"type":"string"}}],"description":"One or more primary key columns. Kumo Relational requires the instance table primary key to be instance_id, and every related table to include an instance_id column."}},"additionalProperties":false},"related_tables":{"type":"object","description":"Related table schemas keyed by table name (entity and fact tables).","additionalProperties":{"type":"object","required":["columns","primary_key"],"properties":{"columns":{"type":"object","additionalProperties":{"type":"object","required":["dtype"],"properties":{"dtype":{"type":"string","description":"Logical dtype such as int64, float32, string, bool, or timestamp[us]."},"stype":{"type":"string","description":"Semantic type such as ID, numerical, categorical, timestamp, or text."},"nullable":{"type":"boolean","default":true}},"additionalProperties":true}},"primary_key":{"oneOf":[{"type":"string"},{"type":"array","minItems":1,"items":{"type":"string"}}],"description":"One or more primary key columns. Kumo Relational requires the instance table primary key to be instance_id, and every related table to include an instance_id column."}},"additionalProperties":false}},"relationships":{"type":"array","description":"Relationships linking the instance, entity, and fact tables.","items":{"type":"object","required":["source_columns","target_table","target_columns"],"properties":{"source_table":{"type":"string","description":"Source table name. Defaults to the instance table when omitted."},"source_columns":{"type":"array","items":{"type":"string"}},"target_table":{"type":"string"},"target_columns":{"type":"array","items":{"type":"string"}}},"additionalProperties":true}}},"additionalProperties":false},"Relationship":{"type":"object","required":["source_columns","target_table","target_columns"],"properties":{"source_table":{"type":"string","description":"Source table name. Defaults to the instance table when omitted."},"source_columns":{"type":"array","items":{"type":"string"}},"target_table":{"type":"string"},"target_columns":{"type":"array","items":{"type":"string"}}},"additionalProperties":true},"TableSchema":{"type":"object","required":["columns","primary_key"],"properties":{"columns":{"type":"object","additionalProperties":{"type":"object","required":["dtype"],"properties":{"dtype":{"type":"string","description":"Logical dtype such as int64, float32, string, bool, or timestamp[us]."},"stype":{"type":"string","description":"Semantic type such as ID, numerical, categorical, timestamp, or text."},"nullable":{"type":"boolean","default":true}},"additionalProperties":true}},"primary_key":{"oneOf":[{"type":"string"},{"type":"array","minItems":1,"items":{"type":"string"}}],"description":"One or more primary key columns. Kumo Relational requires the instance table primary key to be instance_id, and every related table to include an instance_id column."}},"additionalProperties":false},"ColumnSpec":{"type":"object","required":["dtype"],"properties":{"dtype":{"type":"string","description":"Logical dtype such as int64, float32, string, bool, or timestamp[us]."},"stype":{"type":"string","description":"Semantic type such as ID, numerical, categorical, timestamp, or text."},"nullable":{"type":"boolean","default":true}},"additionalProperties":true},"BatchSplit":{"type":"object","required":["instance_table"],"properties":{"instance_table":{"oneOf":[{"type":"object","required":["format","columns","rows"],"properties":{"format":{"type":"string","enum":["arrays"]},"columns":{"type":"array","minItems":1,"description":"Column order for arrays-format rows.","items":{"type":"string"}},"rows":{"type":"array","description":"Arrays-format table rows. Each row follows the order in columns.","items":{"type":"array","items":{"anyOf":[{"type":"string"},{"type":"number"},{"type":"integer"},{"type":"boolean"},{"type":"null"}]}}}},"additionalProperties":false}],"description":"Table payload descriptor. Arrays are the supported table payload format."},"related_tables":{"type":"object","description":"Related table payloads keyed by table name (entity and fact tables).","additionalProperties":{"oneOf":[{"type":"object","required":["format","columns","rows"],"properties":{"format":{"type":"string","enum":["arrays"]},"columns":{"type":"array","minItems":1,"description":"Column order for arrays-format rows.","items":{"type":"string"}},"rows":{"type":"array","description":"Arrays-format table rows. Each row follows the order in columns.","items":{"type":"array","items":{"anyOf":[{"type":"string"},{"type":"number"},{"type":"integer"},{"type":"boolean"},{"type":"null"}]}}}},"additionalProperties":false}],"description":"Table payload descriptor. Arrays are the supported table payload format."}},"metadata":{"type":"object","additionalProperties":true}},"additionalProperties":false},"TableData":{"oneOf":[{"type":"object","required":["format","columns","rows"],"properties":{"format":{"type":"string","enum":["arrays"]},"columns":{"type":"array","minItems":1,"description":"Column order for arrays-format rows.","items":{"type":"string"}},"rows":{"type":"array","description":"Arrays-format table rows. Each row follows the order in columns.","items":{"type":"array","items":{"anyOf":[{"type":"string"},{"type":"number"},{"type":"integer"},{"type":"boolean"},{"type":"null"}]}}}},"additionalProperties":false}],"description":"Table payload descriptor. Arrays are the supported table payload format."},"ArraysTableData":{"type":"object","required":["format","columns","rows"],"properties":{"format":{"type":"string","enum":["arrays"]},"columns":{"type":"array","minItems":1,"description":"Column order for arrays-format rows.","items":{"type":"string"}},"rows":{"type":"array","description":"Arrays-format table rows. Each row follows the order in columns.","items":{"type":"array","items":{"anyOf":[{"type":"string"},{"type":"number"},{"type":"integer"},{"type":"boolean"},{"type":"null"}]}}}},"additionalProperties":false},"OutputSpec":{"type":"object","required":["fields"],"properties":{"fields":{"type":"array","minItems":1,"items":{"type":"string","enum":["prediction","probabilities","scores","rankings","embeddings","quantiles","explanation"]}},"prediction_statistic":{"type":"string","example":"mean"},"quantile_levels":{"type":"array","items":{"type":"number"}}},"additionalProperties":true},"InferenceSpec":{"type":"object","properties":{"run_mode":{"type":"string","description":"Inference run mode such as fast, normal, or best.","example":"best"},"use_prediction_time":{"type":"boolean","default":false},"inference_config":{"type":"object","additionalProperties":true}},"additionalProperties":true},"RequestMetadata":{"type":"object","properties":{"request_id":{"type":"string"},"trace_id":{"type":"string"},"source_query":{"type":"string","description":"Original Kumo Relational predictive query that produced this request."}},"additionalProperties":true},"PredictionResponse":{"type":"object","required":["id","model","predictions","metadata"],"properties":{"id":{"type":"string"},"model":{"type":"string","example":"kumo-relational"},"predictions":{"type":"array","items":{"type":"object","required":["row_index"],"properties":{"id":{"type":"string"},"row_index":{"type":"integer","minimum":0},"prediction":{"anyOf":[{"type":"string"},{"type":"number"},{"type":"integer"},{"type":"boolean"},{"type":"null"}]},"probabilities":{"type":"object","additionalProperties":{"type":"number"}},"scores":{"type":"array","items":{"type":"number"}},"rankings":{"type":"array","items":{"type":"object","required":["id","score"],"properties":{"id":{"type":"string"},"score":{"type":"number"}},"additionalProperties":false}},"embeddings":{"type":"array","items":{"type":"number"}},"quantiles":{"type":"object","additionalProperties":{"type":"number"}},"explanation":{"type":"object","required":["format"],"minProperties":2,"properties":{"format":{"type":"string","description":"Discriminator naming the model-defined explanation shape."}},"additionalProperties":true},"metadata":{"type":"object","additionalProperties":true}},"additionalProperties":true}},"metadata":{"type":"object","required":["task_kind"],"properties":{"task_kind":{"type":"string"},"output_type":{"type":"string"},"adapter":{"type":"string"},"normalized_request_kind":{"type":"string"},"stub_backend":{"type":"boolean"}},"additionalProperties":true}},"additionalProperties":false},"PredictionItem":{"type":"object","required":["row_index"],"properties":{"id":{"type":"string"},"row_index":{"type":"integer","minimum":0},"prediction":{"anyOf":[{"type":"string"},{"type":"number"},{"type":"integer"},{"type":"boolean"},{"type":"null"}]},"probabilities":{"type":"object","additionalProperties":{"type":"number"}},"scores":{"type":"array","items":{"type":"number"}},"rankings":{"type":"array","items":{"type":"object","required":["id","score"],"properties":{"id":{"type":"string"},"score":{"type":"number"}},"additionalProperties":false}},"embeddings":{"type":"array","items":{"type":"number"}},"quantiles":{"type":"object","additionalProperties":{"type":"number"}},"explanation":{"type":"object","required":["format"],"minProperties":2,"properties":{"format":{"type":"string","description":"Discriminator naming the model-defined explanation shape."}},"additionalProperties":true},"metadata":{"type":"object","additionalProperties":true}},"additionalProperties":true},"RankingItem":{"type":"object","required":["id","score"],"properties":{"id":{"type":"string"},"score":{"type":"number"}},"additionalProperties":false},"Explanation":{"type":"object","required":["format"],"minProperties":2,"properties":{"format":{"type":"string","description":"Discriminator naming the model-defined explanation shape."}},"additionalProperties":true},"ResponseMetadata":{"type":"object","required":["task_kind"],"properties":{"task_kind":{"type":"string"},"output_type":{"type":"string"},"adapter":{"type":"string"},"normalized_request_kind":{"type":"string"},"stub_backend":{"type":"boolean"}},"additionalProperties":true},"ProblemDetails":{"type":"object","required":["type","status","title","detail","code"],"properties":{"type":{"type":"string","format":"uri-reference","description":"URI identifying the problem type."},"status":{"type":"integer","minimum":100,"maximum":599,"description":"HTTP status code for this occurrence of the problem."},"title":{"type":"string","description":"Short, human-readable summary of the problem."},"detail":{"type":"string","description":"Human-readable explanation specific to this occurrence."},"code":{"type":"string","maxLength":1024,"description":"Stable application-specific code identifying the precise failure."},"instance":{"type":"string","format":"uri-reference","description":"URI identifying this specific problem occurrence."}},"additionalProperties":true,"example":{"type":"/problems/validation-failed","status":422,"title":"Validation failed","detail":"Prediction request contains invalid table data.","code":"VALIDATION_FAILED"}},"CellValue":{"anyOf":[{"type":"string"},{"type":"number"},{"type":"integer"},{"type":"boolean"},{"type":"null"}]}}}},"pageLayout":"v3"},"children":["$L57","$L58","$L59"]}]}]]
5a:I[388958,["/_next/static/chunks/04d712ydf7vwt.js","/_next/static/chunks/3ibd-wdn1muo9.js","/_next/static/chunks/1q5xb__jylra0.js","/_next/static/chunks/1z_-bqrzptsiz.js","/_next/static/chunks/1la1pzs9j8idc.js","/_next/static/chunks/00eq9bqnkbpfo.js","/_next/static/chunks/1tjzqakl0-ac_.js","/_next/static/chunks/3r5yd4k4rms8-.js","/_next/static/chunks/1qasf48lwbczr.js","/_next/static/chunks/0iqwvdhi-o1pr.js","/_next/static/chunks/3-dupjzg004ft.js","/_next/static/chunks/1p8p6uesfmfc2.js","/_next/static/chunks/3c_tmnbt9nfb3.js","/_next/static/chunks/2lofudtwqsrwt.js","/_next/static/chunks/36qm3961yv116.js","/_next/static/chunks/342zpu2i9tat1.js","/_next/static/chunks/2tmwf_2axyd0y.js","/_next/static/chunks/3v9fr1qimf7lj.js","/_next/static/chunks/364lrnu5opng7.js","/_next/static/chunks/3kdaun3epyv7g.js","/_next/static/chunks/13fah1s8gxrn0.js","/_next/static/chunks/2tkz_ff5gjl4a.js","/_next/static/chunks/2_n0f-hh3ea4l.js","/_next/static/chunks/0czpc-f8wjri8.js","/_next/static/chunks/3761ezb6xysq0.js","/_next/static/chunks/24_gg9g_4g22i.js","/_next/static/chunks/1_3y3ily4zuo1.js","/_next/static/chunks/1a2o19d1j4nvx.js","/_next/static/chunks/1kci6kpi29km9.js","/_next/static/chunks/1hhq3s9jcti5r.js","/_next/static/chunks/2mr_uzqfq-mid.js","/_next/static/chunks/3o73dbhryidg8.js","/_next/static/chunks/278imbrkq3abd.js","/_next/static/chunks/3-ngy7l0vx9s-.js","/_next/static/chunks/1q5ewy8bee9p6.js","/_next/static/chunks/2pqhypz2vo8mu.js","/_next/static/chunks/2960tspz292yr.js","/_next/static/chunks/00jw9q5dp3jlz.js","/_next/static/chunks/0p-09baxevld1.js","/_next/static/chunks/0tqq_6ft6mlt2.js"],"NebulaCloud"]
5b:I[919548,["/_next/static/chunks/04d712ydf7vwt.js","/_next/static/chunks/3ibd-wdn1muo9.js","/_next/static/chunks/1q5xb__jylra0.js","/_next/static/chunks/1z_-bqrzptsiz.js","/_next/static/chunks/1la1pzs9j8idc.js","/_next/static/chunks/00eq9bqnkbpfo.js","/_next/static/chunks/1tjzqakl0-ac_.js","/_next/static/chunks/3r5yd4k4rms8-.js","/_next/static/chunks/1qasf48lwbczr.js","/_next/static/chunks/0iqwvdhi-o1pr.js","/_next/static/chunks/3-dupjzg004ft.js","/_next/static/chunks/1p8p6uesfmfc2.js","/_next/static/chunks/3c_tmnbt9nfb3.js","/_next/static/chunks/2lofudtwqsrwt.js","/_next/static/chunks/36qm3961yv116.js","/_next/static/chunks/342zpu2i9tat1.js","/_next/static/chunks/2tmwf_2axyd0y.js","/_next/static/chunks/3v9fr1qimf7lj.js","/_next/static/chunks/364lrnu5opng7.js","/_next/static/chunks/3kdaun3epyv7g.js","/_next/static/chunks/13fah1s8gxrn0.js","/_next/static/chunks/2tkz_ff5gjl4a.js","/_next/static/chunks/2_n0f-hh3ea4l.js","/_next/static/chunks/0czpc-f8wjri8.js","/_next/static/chunks/3761ezb6xysq0.js","/_next/static/chunks/24_gg9g_4g22i.js","/_next/static/chunks/1_3y3ily4zuo1.js","/_next/static/chunks/1a2o19d1j4nvx.js","/_next/static/chunks/1kci6kpi29km9.js","/_next/static/chunks/1hhq3s9jcti5r.js","/_next/static/chunks/2mr_uzqfq-mid.js","/_next/static/chunks/3o73dbhryidg8.js","/_next/static/chunks/278imbrkq3abd.js","/_next/static/chunks/3-ngy7l0vx9s-.js","/_next/static/chunks/1q5ewy8bee9p6.js","/_next/static/chunks/2pqhypz2vo8mu.js","/_next/static/chunks/2960tspz292yr.js","/_next/static/chunks/00jw9q5dp3jlz.js","/_next/static/chunks/0p-09baxevld1.js","/_next/static/chunks/0tqq_6ft6mlt2.js"],"default"]
5c:I[472683,["/_next/static/chunks/04d712ydf7vwt.js","/_next/static/chunks/3ibd-wdn1muo9.js","/_next/static/chunks/1q5xb__jylra0.js","/_next/static/chunks/1z_-bqrzptsiz.js","/_next/static/chunks/1la1pzs9j8idc.js","/_next/static/chunks/00eq9bqnkbpfo.js","/_next/static/chunks/1tjzqakl0-ac_.js","/_next/static/chunks/3r5yd4k4rms8-.js","/_next/static/chunks/1qasf48lwbczr.js","/_next/static/chunks/0iqwvdhi-o1pr.js","/_next/static/chunks/3-dupjzg004ft.js","/_next/static/chunks/1p8p6uesfmfc2.js","/_next/static/chunks/3c_tmnbt9nfb3.js","/_next/static/chunks/2lofudtwqsrwt.js","/_next/static/chunks/36qm3961yv116.js","/_next/static/chunks/342zpu2i9tat1.js","/_next/static/chunks/2tmwf_2axyd0y.js","/_next/static/chunks/3v9fr1qimf7lj.js","/_next/static/chunks/364lrnu5opng7.js","/_next/static/chunks/3kdaun3epyv7g.js","/_next/static/chunks/13fah1s8gxrn0.js","/_next/static/chunks/2tkz_ff5gjl4a.js","/_next/static/chunks/2_n0f-hh3ea4l.js","/_next/static/chunks/0czpc-f8wjri8.js","/_next/static/chunks/3761ezb6xysq0.js","/_next/static/chunks/24_gg9g_4g22i.js","/_next/static/chunks/1_3y3ily4zuo1.js","/_next/static/chunks/1a2o19d1j4nvx.js","/_next/static/chunks/1kci6kpi29km9.js","/_next/static/chunks/1hhq3s9jcti5r.js","/_next/static/chunks/2mr_uzqfq-mid.js","/_next/static/chunks/3o73dbhryidg8.js","/_next/static/chunks/278imbrkq3abd.js","/_next/static/chunks/3-ngy7l0vx9s-.js","/_next/static/chunks/1q5ewy8bee9p6.js","/_next/static/chunks/2pqhypz2vo8mu.js","/_next/static/chunks/2960tspz292yr.js","/_next/static/chunks/00jw9q5dp3jlz.js","/_next/static/chunks/0p-09baxevld1.js","/_next/static/chunks/0tqq_6ft6mlt2.js"],"default"]
5d:I[543711,["/_next/static/chunks/04d712ydf7vwt.js","/_next/static/chunks/3ibd-wdn1muo9.js","/_next/static/chunks/1q5xb__jylra0.js","/_next/static/chunks/1z_-bqrzptsiz.js","/_next/static/chunks/1la1pzs9j8idc.js","/_next/static/chunks/00eq9bqnkbpfo.js","/_next/static/chunks/1tjzqakl0-ac_.js","/_next/static/chunks/3r5yd4k4rms8-.js","/_next/static/chunks/1qasf48lwbczr.js","/_next/static/chunks/0iqwvdhi-o1pr.js","/_next/static/chunks/3-dupjzg004ft.js","/_next/static/chunks/1p8p6uesfmfc2.js","/_next/static/chunks/3c_tmnbt9nfb3.js","/_next/static/chunks/2lofudtwqsrwt.js","/_next/static/chunks/36qm3961yv116.js","/_next/static/chunks/342zpu2i9tat1.js","/_next/static/chunks/2tmwf_2axyd0y.js","/_next/static/chunks/3v9fr1qimf7lj.js","/_next/static/chunks/364lrnu5opng7.js","/_next/static/chunks/3kdaun3epyv7g.js","/_next/static/chunks/13fah1s8gxrn0.js","/_next/static/chunks/2tkz_ff5gjl4a.js","/_next/static/chunks/2_n0f-hh3ea4l.js","/_next/static/chunks/0czpc-f8wjri8.js","/_next/static/chunks/3761ezb6xysq0.js","/_next/static/chunks/24_gg9g_4g22i.js","/_next/static/chunks/1_3y3ily4zuo1.js","/_next/static/chunks/1a2o19d1j4nvx.js","/_next/static/chunks/1kci6kpi29km9.js","/_next/static/chunks/1hhq3s9jcti5r.js","/_next/static/chunks/2mr_uzqfq-mid.js","/_next/static/chunks/3o73dbhryidg8.js","/_next/static/chunks/278imbrkq3abd.js","/_next/static/chunks/3-ngy7l0vx9s-.js","/_next/static/chunks/1q5ewy8bee9p6.js","/_next/static/chunks/2pqhypz2vo8mu.js","/_next/static/chunks/2960tspz292yr.js","/_next/static/chunks/00jw9q5dp3jlz.js","/_next/static/chunks/0p-09baxevld1.js","/_next/static/chunks/0tqq_6ft6mlt2.js"],"default"]
57:["$","$L5a",null,{"direction":"top"}]
58:["$","$L5a",null,{"direction":"bottom"}]
59:["$","div",null,{"className":"relative","data-page-layout":"v3","children":[["$","$L5b",null,{"apiReferenceEnabled":false,"artifact":"$49:0:props:children:props:initialState:artifact","attributes":"$4a:props:spec:attributes","tabs":[{"label":"Build","bare":true,"icon":"code","kind":"default","id":"build","href":"/nvidia/kumo-relational","aliases":["/nvidia/kumo-relational/build"]},{"label":"Playground","icon":"play","kind":"default","id":"playground","href":"/nvidia/kumo-relational/playground","aliases":"$undefined"},{"label":"Model Card","icon":"book","kind":"default","id":"modelcard","href":"/nvidia/kumo-relational/modelcard","aliases":"$undefined"}]}],["$","$L5c",null,{"endpointData":{"artifact":"$49:0:props:children:props:initialState:artifact","requestStatus":{"statusCode":"SUCCESS","requestId":"44b64343-2688678"}},"endpointName":"kumo-relational","endpointSpec":"$4a:props:spec","isDeprecated":false,"isLoginRequired":true,"playgroundElement":"$5d","publisherName":"nvidia","searchParams":{},"tabs":"$59:props:children:0:props:tabs"}]]}]
