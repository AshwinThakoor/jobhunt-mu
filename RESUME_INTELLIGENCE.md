# JobHunt MU — Resume Intelligence Engine

> 🚧 **Status: Currently Being Built**
>
> Development milestone: **Phase 1.6 — Resume Intelligence Engine V3**

## Purpose

Resume Intelligence is being developed as a core JobHunt MU capability.

Its purpose is not simply to generate an arbitrary ATS-style percentage.

The system is intended to analyze evidence from a candidate's resume against structured evidence extracted from a job description and produce an explainable compatibility assessment.

## Target Pipeline

```mermaid
flowchart TD
    A[Resume Upload] --> B[Document Parsing]
    B --> C[Section Detection]
    C --> D[Structured Resume Evidence]

    E[Job Description] --> F[Requirement Extraction]
    F --> G[Structured Job Requirements]

    D --> H[Skill & Evidence Normalization]
    G --> I[Requirement Classification]

    H --> J[Compatibility Engine]
    I --> J

    J --> K[Mandatory Blocker Detection]
    J --> L[Confidence Engine]
    J --> M[Explainability Engine]

    K --> N[Final Compatibility Assessment]
    L --> N
    M --> N

    N --> O[Resume Improvement Recommendations]
    N --> P[Application Studio]