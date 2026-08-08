# AI and machine-learning workflow

## Current implementation

JobHunt MU does not currently train or ship a proprietary machine-learning model. The matching layer is a deterministic, explainable system using extracted text, normalized skills, aliases, title evidence, and weighted scoring. This choice supports auditability while the product lacks a consented labelled dataset.

## Current pipeline

```mermaid
flowchart LR
    A[Resume PDF or DOCX] --> B[Text extraction]
    B --> C[Known-skill detection]
    D[Opportunity fields] --> E[Requirement normalization]
    C --> F[Weighted matcher]
    E --> F
    F --> G[Score and confidence]
    F --> H[Matched and missing evidence]
    G --> I[Ranked recommendations]
    H --> I
```

## Future ML lifecycle

```mermaid
flowchart TD
    C[Consent and data governance] --> D[Anonymized labelled dataset]
    D --> S[Train, validation, and test split]
    S --> B[Baseline deterministic matcher]
    S --> M[Candidate semantic or learning-to-rank model]
    B --> E[Offline evaluation]
    M --> E
    E --> R[Human review and risk assessment]
    R --> F[Feature-flagged deployment]
    F --> O[Quality, drift, fairness, latency monitoring]
    O --> V[Versioning and rollback]
```

## Required artifacts before a trained model

- data sheet describing provenance, consent, retention, and exclusions;
- model card describing purpose, metrics, limitations, and prohibited uses;
- reproducible training configuration and fixed evaluation set;
- feature and label definitions;
- fairness and subgroup evaluation plan;
- threshold and rollback policy;
- human-review requirements;
- evidence that generated documents do not fabricate facts.

## Appropriate metrics

Use skill extraction precision/recall/F1, ranking precision@k, nDCG, human agreement, calibration where probabilities exist, latency, and unsupported-claim rate. Do not use application success alone as a clean ground-truth label because hiring outcomes contain confounding factors and historical bias.
