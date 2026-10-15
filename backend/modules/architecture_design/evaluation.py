"""
Evaluation & Benchmarking Engine – Milestone 6.

Provides deterministic calculation of:
- Multi-label Quality Attribute classification metrics (Precision, Recall, Micro/Macro F1)
- Architecture style ranking metrics (Top-1 hit, Top-k hit, Mean Reciprocal Rank - MRR)
- Objective structural and traceability metrics
- Experiment serialization and CLI execution runner
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
from pathlib import Path
from typing import Any, List, Set

from .schemas import (
    ASRBatch,
    ASRInput,
    BenchmarkCase,
    ClassificationMetrics,
    EvaluationReport,
    HighLevelArchitectureDesign,
    LabelClassificationMetrics,
    QualityAttribute,
    RankingMetrics,
    StructuralMetrics,
)
from .service import ArchitectureDesignService
from .llm.provider import StubLLMProvider
from .retrieval.embedding_provider import SentenceTransformerEmbeddingProvider, StubEmbeddingProvider
from .retrieval.vector_store import InMemoryVectorStore
from .quality_classifier import BaseClassifier, KeywordClassifier, SemanticQualityClassifier
from .config import architecture_config


# ===========================================================================
# 1. Metric Computation Functions
# ===========================================================================

def compute_multilabel_metrics(
    predictions: List[Set[str]],
    ground_truths: List[Set[str]],
    all_labels: Set[str] | None = None,
) -> ClassificationMetrics:
    """
    Compute multi-label precision, recall, micro-F1, macro-F1, and per-label metrics.
    """
    if len(predictions) != len(ground_truths):
        raise ValueError("Predictions and ground truths must have the same length.")

    # Determine universe of labels
    if all_labels is None:
        all_labels = set()
        for p in predictions:
            all_labels.update(p)
        for g in ground_truths:
            all_labels.update(g)

    # Per-label confusion matrices
    tp_per_label: dict[str, int] = {label: 0 for label in all_labels}
    fp_per_label: dict[str, int] = {label: 0 for label in all_labels}
    fn_per_label: dict[str, int] = {label: 0 for label in all_labels}

    total_tp = 0
    total_fp = 0
    total_fn = 0

    for pred_set, gt_set in zip(predictions, ground_truths):
        for label in all_labels:
            in_pred = label in pred_set
            in_gt = label in gt_set

            if in_pred and in_gt:
                tp_per_label[label] += 1
                total_tp += 1
            elif in_pred and not in_gt:
                fp_per_label[label] += 1
                total_fp += 1
            elif not in_pred and in_gt:
                fn_per_label[label] += 1
                total_fn += 1

    # Micro-averaged metrics
    micro_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    micro_recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    micro_f1 = (
        (2 * micro_precision * micro_recall) / (micro_precision + micro_recall)
        if (micro_precision + micro_recall) > 0
        else 0.0
    )

    # Per-label and Macro-averaged metrics
    per_label_metrics: dict[str, LabelClassificationMetrics] = {}
    f1_list: list[float] = []

    for label in sorted(all_labels):
        tp = tp_per_label[label]
        fp = fp_per_label[label]
        fn = fn_per_label[label]
        support = tp + fn

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

        per_label_metrics[label] = LabelClassificationMetrics(
            precision=round(prec, 4),
            recall=round(rec, 4),
            f1=round(f1, 4),
            support=support,
        )

        # Include in macro average if the label was present in ground truth or predictions
        if support > 0 or (tp + fp) > 0:
            f1_list.append(f1)

    macro_f1 = sum(f1_list) / len(f1_list) if f1_list else 0.0

    return ClassificationMetrics(
        micro_precision=round(micro_precision, 4),
        micro_recall=round(micro_recall, 4),
        micro_f1=round(micro_f1, 4),
        macro_f1=round(macro_f1, 4),
        per_label=per_label_metrics,
    )


def compute_ranking_metrics(
    ranked_predictions: List[List[str]],
    acceptable_styles: List[List[str]],
    k: int = 3,
) -> RankingMetrics:
    """
    Compute architecture ranking metrics: Top-1 hit rate, Top-k hit rate, and MRR.
    Supports multiple acceptable architecture styles per case.
    """
    if len(ranked_predictions) != len(acceptable_styles):
        raise ValueError("Ranked predictions and acceptable styles must have equal length.")

    if not ranked_predictions:
        return RankingMetrics(top1_hit_rate=0.0, top3_hit_rate=0.0, mean_reciprocal_rank=0.0)

    top1_hits = 0
    topk_hits = 0
    reciprocal_ranks: list[float] = []

    for preds, acceptable in zip(ranked_predictions, acceptable_styles):
        acceptable_set = set(acceptable)

        # Top-1 Hit
        if preds and preds[0] in acceptable_set:
            top1_hits += 1

        # Top-k Hit
        if any(p in acceptable_set for p in preds[:k]):
            topk_hits += 1

        # Reciprocal Rank: 1 / rank of first acceptable hit (1-indexed)
        rr = 0.0
        for rank_idx, pred_style in enumerate(preds, start=1):
            if pred_style in acceptable_set:
                rr = 1.0 / rank_idx
                break
        reciprocal_ranks.append(rr)

    total = len(ranked_predictions)
    return RankingMetrics(
        top1_hit_rate=round(top1_hits / total, 4),
        top3_hit_rate=round(topk_hits / total, 4),
        mean_reciprocal_rank=round(sum(reciprocal_ranks) / total, 4),
    )


def compute_structural_metrics(
    designs: List[HighLevelArchitectureDesign],
    batches: List[ASRBatch],
) -> StructuralMetrics:
    """
    Compute objective structural metrics verifying requirement and QA traceability.
    """
    total_req_links = 0
    valid_req_links = 0
    total_qa_links = 0
    valid_qa_links = 0
    total_connections = 0
    valid_connections = 0
    unsupported_components = 0

    valid_qa_names = {qa.value for qa in QualityAttribute}

    for design, batch in zip(designs, batches):
        valid_batch_req_ids = {asr.requirement_id for asr in batch.asrs}
        comp_id_set = {c.component_id for c in design.components}

        for comp in design.components:
            # Requirement traceability
            for req in comp.related_requirements:
                total_req_links += 1
                if req in valid_batch_req_ids:
                    valid_req_links += 1

            # Quality attribute traceability
            for qa in comp.related_quality_attributes:
                total_qa_links += 1
                qa_val = getattr(qa, "value", str(qa))
                if qa_val in valid_qa_names:
                    valid_qa_links += 1

            # Unsupported business components check
            if comp.grounding_type == "requirement_derived" and not comp.related_requirements:
                unsupported_components += 1

        # Connection integrity
        for conn in design.connections:
            total_connections += 1
            if conn.source in comp_id_set and conn.target in comp_id_set:
                valid_connections += 1

    req_ratio = valid_req_links / total_req_links if total_req_links > 0 else 1.0
    qa_ratio = valid_qa_links / total_qa_links if total_qa_links > 0 else 1.0
    conn_ratio = valid_connections / total_connections if total_connections > 0 else 1.0

    return StructuralMetrics(
        requirement_traceability_ratio=round(req_ratio, 4),
        qa_traceability_ratio=round(qa_ratio, 4),
        valid_connection_ratio=round(conn_ratio, 4),
        unsupported_component_count=unsupported_components,
    )


# ===========================================================================
# 2. Benchmark Case Loader
# ===========================================================================

def load_benchmark_cases(file_path: str | Path) -> List[BenchmarkCase]:
    """Load benchmark cases from a JSON file into validated BenchmarkCase models."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Benchmark file not found at: {path.resolve()}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Benchmark JSON must contain a top-level list of cases.")

    return [BenchmarkCase.model_validate(item) for item in data]


# ===========================================================================
# 3. Evaluation Runner
# ===========================================================================

def run_evaluation(
    benchmark_path: str | Path,
    service: ArchitectureDesignService | None = None,
    output_dir: str | Path | None = None,
    save_report: bool = True,
    evaluate_design: bool = False,
    classifier: BaseClassifier | None = None,
) -> tuple[EvaluationReport, dict[str, Any]]:
    """
    Run evaluation on the benchmark cases and generate metrics and experiment logs.
    """
    cases = load_benchmark_cases(benchmark_path)
    if not cases:
        raise ValueError("Benchmark dataset contains no cases.")

    # Fallback to stubbed service for offline determinism if none provided
    if service is None:
        service = ArchitectureDesignService(
            classifier=classifier or KeywordClassifier(),
            embedding_provider=StubEmbeddingProvider(),
            vector_store=InMemoryVectorStore(),
            llm_provider=StubLLMProvider(),
        )

    predicted_qas: list[set[str]] = []
    expected_qas: list[set[str]] = []

    predicted_rankings: list[list[str]] = []
    acceptable_rankings: list[list[str]] = []

    generated_designs: list[HighLevelArchitectureDesign] = []
    batches: list[ASRBatch] = []

    case_logs: list[dict[str, Any]] = []

    for case in cases:
        batch = ASRBatch(project_id=case.project_id, asrs=case.asrs)
        batches.append(batch)

        # M1 Classification
        m1_out = service.run(batch)
        profile_qas = {qa for qa, count in m1_out.quality_profile.model_dump().items() if count > 0}
        predicted_qas.append(profile_qas)
        expected_qas.append(set(case.expected_quality_attributes))

        # M2 Architecture Scoring & Ranking
        m2_out = service.evaluate(batch)
        ranked_styles = [e.style.value for e in sorted(m2_out.architecture_evaluations, key=lambda x: x.rank)]
        predicted_rankings.append(ranked_styles)
        acceptable_rankings.append(case.expected_preferred_styles)

        # Optional M5 Design evaluation
        design_output = None
        if evaluate_design:
            design_res = service.generate_design(batch)
            design_output = design_res.design
            generated_designs.append(design_output)

        # Per-case log item
        top1_hit = bool(ranked_styles and ranked_styles[0] in set(case.expected_preferred_styles))
        case_logs.append({
            "case_id": case.case_id,
            "project_id": case.project_id,
            "title": case.title,
            "predicted_qas": sorted(profile_qas),
            "expected_qas": sorted(case.expected_quality_attributes),
            "predicted_rank_1": ranked_styles[0] if ranked_styles else None,
            "acceptable_styles": case.expected_preferred_styles,
            "top1_hit": top1_hit,
        })

    # Compute metrics
    classification_metrics = compute_multilabel_metrics(predicted_qas, expected_qas)
    ranking_metrics = compute_ranking_metrics(predicted_rankings, acceptable_rankings)
    structural_metrics = (
        compute_structural_metrics(generated_designs, batches) if evaluate_design else None
    )

    report = EvaluationReport(
        total_cases=len(cases),
        classification_metrics=classification_metrics,
        ranking_metrics=ranking_metrics,
        structural_metrics=structural_metrics,
        pipeline_version="M7",
    )

    # Prepare experiment log dictionary
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
    classifier_name = type(service._classifier).__name__
    experiment_data = {
        "timestamp": timestamp,
        "pipeline_version": "M7",
        "classifier_name": classifier_name,
        "benchmark_file": str(Path(benchmark_path).name),
        "total_cases": len(cases),
        "metrics": report.model_dump(),
        "case_predictions": case_logs,
    }

    # Save to outputs directory if requested
    if save_report:
        if output_dir is None:
            output_dir = Path(__file__).resolve().parent.parent.parent / "outputs" / "architecture_evaluation"
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        file_name = out_path / f"architecture_eval_{timestamp}.json"
        with open(file_name, "w", encoding="utf-8") as f:
            json.dump(experiment_data, f, indent=2)

    return report, experiment_data


def compare_classifiers(
    benchmark_path: str | Path,
    output_dir: str | Path | None = None,
    threshold: float = 0.50,
    use_sentence_transformers: bool = True,
) -> tuple[dict[str, Any], EvaluationReport, EvaluationReport]:
    """
    Run baseline KeywordClassifier and SemanticQualityClassifier on the exact same
    benchmark cases and produce a direct comparative evaluation report.
    """
    cases = load_benchmark_cases(benchmark_path)
    if not cases:
        raise ValueError("Benchmark dataset contains no cases.")

    # 1. Setup Keyword Classifier Service
    kw_classifier = KeywordClassifier()
    kw_service = ArchitectureDesignService(
        classifier=kw_classifier,
        embedding_provider=StubEmbeddingProvider(),
        vector_store=InMemoryVectorStore(),
        llm_provider=StubLLMProvider(),
    )
    kw_report, kw_log = run_evaluation(
        benchmark_path=benchmark_path,
        service=kw_service,
        save_report=False,
    )

    # 2. Setup Semantic Classifier Service
    if use_sentence_transformers:
        try:
            emb_provider = SentenceTransformerEmbeddingProvider(
                model_name=architecture_config.embedding_model
            )
        except Exception:
            emb_provider = StubEmbeddingProvider()
    else:
        emb_provider = StubEmbeddingProvider()

    sem_classifier = SemanticQualityClassifier(
        embedding_provider=emb_provider,
        threshold=threshold,
    )
    sem_service = ArchitectureDesignService(
        classifier=sem_classifier,
        embedding_provider=emb_provider,
        vector_store=InMemoryVectorStore(),
        llm_provider=StubLLMProvider(),
    )
    sem_report, sem_log = run_evaluation(
        benchmark_path=benchmark_path,
        service=sem_service,
        save_report=False,
    )

    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")

    kw_cm = kw_report.classification_metrics
    kw_rm = kw_report.ranking_metrics
    sem_cm = sem_report.classification_metrics
    sem_rm = sem_report.ranking_metrics

    comparison_summary = {
        "micro_precision": {"keyword": kw_cm.micro_precision, "semantic": sem_cm.micro_precision},
        "micro_recall": {"keyword": kw_cm.micro_recall, "semantic": sem_cm.micro_recall},
        "micro_f1": {"keyword": kw_cm.micro_f1, "semantic": sem_cm.micro_f1},
        "macro_f1": {"keyword": kw_cm.macro_f1, "semantic": sem_cm.macro_f1},
        "top1_hit_rate": {"keyword": kw_rm.top1_hit_rate, "semantic": sem_rm.top1_hit_rate},
        "top3_hit_rate": {"keyword": kw_rm.top3_hit_rate, "semantic": sem_rm.top3_hit_rate},
        "mean_reciprocal_rank": {"keyword": kw_rm.mean_reciprocal_rank, "semantic": sem_rm.mean_reciprocal_rank},
    }

    comparison_data = {
        "timestamp": timestamp,
        "pipeline_version": "M7",
        "benchmark_file": str(Path(benchmark_path).name),
        "total_cases": len(cases),
        "classifiers": {
            "keyword": {
                "classifier_name": "KeywordClassifier",
                "metrics": kw_report.model_dump(),
                "case_predictions": kw_log["case_predictions"],
            },
            "semantic": {
                "classifier_name": "SemanticQualityClassifier",
                "embedding_model": getattr(emb_provider, "model_name", "unknown"),
                "threshold": threshold,
                "metrics": sem_report.model_dump(),
                "case_predictions": sem_log["case_predictions"],
            },
        },
        "comparison_summary": comparison_summary,
    }

    if output_dir is None:
        output_dir = Path(__file__).resolve().parent.parent.parent / "outputs" / "architecture_evaluation"
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    comparison_file = out_path / f"architecture_comparison_{timestamp}.json"
    with open(comparison_file, "w", encoding="utf-8") as f:
        json.dump(comparison_data, f, indent=2)

    return comparison_data, kw_report, sem_report


# ===========================================================================
# 4. CLI Entry Point
# ===========================================================================

def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate Architecture Decision Agent on Benchmark Datasets.")
    parser.add_argument(
        "--benchmark",
        type=str,
        default="datasets/architecture_decision/benchmark_cases.json",
        help="Path to benchmark JSON cases file.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="outputs/architecture_evaluation",
        help="Directory to save experiment JSON output.",
    )
    parser.add_argument(
        "--include-design",
        action="store_true",
        help="Also run M5 design generation and evaluate structural traceability.",
    )
    parser.add_argument(
        "--classifier",
        type=str,
        choices=["keyword", "semantic"],
        default="keyword",
        help="QA classifier to evaluate (keyword | semantic).",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.50,
        help="Cosine similarity threshold for SemanticQualityClassifier.",
    )
    parser.add_argument(
        "--compare-classifiers",
        action="store_true",
        help="Run baseline comparison evaluating KeywordClassifier vs SemanticQualityClassifier.",
    )

    args = parser.parse_args()

    # Resolve benchmark path relative to backend root if relative
    bench_path = Path(args.benchmark)
    if not bench_path.is_absolute():
        bench_path = Path(__file__).resolve().parent.parent.parent / args.benchmark

    out_dir = Path(args.output_dir)
    if not out_dir.is_absolute():
        out_dir = Path(__file__).resolve().parent.parent.parent / args.output_dir

    print(f"\n=======================================================")
    print(f"  Architecture Decision Agent – Benchmark Evaluation")
    print(f"=======================================================")
    print(f"Benchmark: {bench_path.name}")

    if args.compare_classifiers:
        print("Running comparative evaluation: KeywordClassifier vs SemanticQualityClassifier...")
        comparison_data, kw_report, sem_report = compare_classifiers(
            benchmark_path=bench_path,
            output_dir=out_dir,
            threshold=args.threshold,
        )

        kw_cm = kw_report.classification_metrics
        kw_rm = kw_report.ranking_metrics
        sem_cm = sem_report.classification_metrics
        sem_rm = sem_report.ranking_metrics

        print("\n-------------------------------------------------------")
        print(f"Cases Evaluated: {kw_report.total_cases}")
        print("-------------------------------------------------------")
        print("Classifier Comparison")
        print("-------------------------------------------------------")
        print(f"{'Metric':<22} {'Keyword':<12} {'Semantic':<12}")
        print(f"{'Micro Precision':<22} {kw_cm.micro_precision:<12.4f} {sem_cm.micro_precision:<12.4f}")
        print(f"{'Micro Recall':<22} {kw_cm.micro_recall:<12.4f} {sem_cm.micro_recall:<12.4f}")
        print(f"{'Micro F1':<22} {kw_cm.micro_f1:<12.4f} {sem_cm.micro_f1:<12.4f}")
        print(f"{'Macro F1':<22} {kw_cm.macro_f1:<12.4f} {sem_cm.macro_f1:<12.4f}")
        print(f"{'Top-1 Hit Rate':<22} {kw_rm.top1_hit_rate:<12.4f} {sem_rm.top1_hit_rate:<12.4f}")
        print(f"{'Top-3 Hit Rate':<22} {kw_rm.top3_hit_rate:<12.4f} {sem_rm.top3_hit_rate:<12.4f}")
        print(f"{'MRR':<22} {kw_rm.mean_reciprocal_rank:<12.4f} {sem_rm.mean_reciprocal_rank:<12.4f}")
        print("-------------------------------------------------------")
        print(f"Comparison report saved to: {out_dir}")
        print("=======================================================\n")
        return

    # Single classifier evaluation
    if args.classifier == "semantic":
        emb_provider = SentenceTransformerEmbeddingProvider(
            model_name=architecture_config.embedding_model
        )
        classifier = SemanticQualityClassifier(
            embedding_provider=emb_provider,
            threshold=args.threshold,
        )
        svc = ArchitectureDesignService(
            classifier=classifier,
            embedding_provider=emb_provider,
            vector_store=InMemoryVectorStore(),
            llm_provider=StubLLMProvider(),
        )
    else:
        classifier = KeywordClassifier()
        svc = ArchitectureDesignService(
            classifier=classifier,
            embedding_provider=StubEmbeddingProvider(),
            vector_store=InMemoryVectorStore(),
            llm_provider=StubLLMProvider(),
        )

    print(f"Running evaluation with classifier: {type(classifier).__name__}...")

    report, log_data = run_evaluation(
        benchmark_path=bench_path,
        service=svc,
        output_dir=out_dir,
        evaluate_design=args.include_design,
    )

    cm = report.classification_metrics
    rm = report.ranking_metrics

    print("\n-------------------------------------------------------")
    print(f"Cases Evaluated: {report.total_cases}")
    print("-------------------------------------------------------")
    print("QA Classification Metrics (Multi-label):")
    print(f"  Micro Precision: {cm.micro_precision:.4f}")
    print(f"  Micro Recall:    {cm.micro_recall:.4f}")
    print(f"  Micro F1:        {cm.micro_f1:.4f}")
    print(f"  Macro F1:        {cm.macro_f1:.4f}")
    print("\nArchitecture Ranking Metrics:")
    print(f"  Top-1 Hit Rate:  {rm.top1_hit_rate:.4f}")
    print(f"  Top-3 Hit Rate:  {rm.top3_hit_rate:.4f}")
    print(f"  MRR:             {rm.mean_reciprocal_rank:.4f}")

    if report.structural_metrics:
        sm = report.structural_metrics
        print("\nStructural Traceability Metrics:")
        print(f"  Requirement Traceability: {sm.requirement_traceability_ratio:.4f}")
        print(f"  QA Traceability:          {sm.qa_traceability_ratio:.4f}")
        print(f"  Valid Connections:        {sm.valid_connection_ratio:.4f}")
        print(f"  Unsupported Components:   {sm.unsupported_component_count}")

    print("-------------------------------------------------------")
    print("Evaluation completed successfully.")
    print("=======================================================\n")


if __name__ == "__main__":
    main()

