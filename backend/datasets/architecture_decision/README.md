# Architecture Decision Benchmark Dataset

## Overview
This benchmark dataset contains representative software requirement engineering scenarios for evaluating the **Architecture Decision Agent** in DesignTrace AI.

Each case specifies:
- Requirement statements (ASRs)
- Expected multi-label Quality Attributes (e.g., Scalability, Security, Reliability)
- Acceptable / Preferred Architecture Styles (e.g., Event-Driven Architecture, Microservices, Modular Monolith)

## Scientific & Research Notice
> [!IMPORTANT]
> **Status: Prototype / Developer-Authored / Pending Expert Validation**
>
> The current Architecture Decision Agent evaluates six quality attributes: **Security, Scalability, Performance, Reliability, Maintainability, and Availability**. Benchmark gold labels must remain inside this supported label space.
>
> The cases and gold labels in this directory are preliminary benchmark cases developed to test and baseline the evaluation harness. In architectural design, multiple architecture styles may be acceptable trade-offs depending on organizational constraints.
>
> As part of future research validation:
> - Ground truth labels must be validated by external domain architects and literature meta-analyses.
> - The `KeywordClassifier` serves as the baseline model against which future learned/transformer models will be compared.
> - Architecture ranking metrics evaluate whether acceptable styles are retrieved in Top-1 or Top-k recommendations.

## Files
- `benchmark_cases.json`: Formatted benchmark items ready for ingestion by `modules.architecture_design.evaluation`.
- `gold_labels.json`: Annotations and architectural rationale references.
