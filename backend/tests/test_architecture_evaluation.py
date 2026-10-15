"""
Architecture Evaluation Unit Tests – Milestone 6.

Validates the evaluation metric computations, ranking/MRR logic,
structural traceability metrics, benchmark loading, and experiment execution.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
import pytest

from modules.architecture_design.evaluation import (
    compute_multilabel_metrics,
    compute_ranking_metrics,
    compute_structural_metrics,
    load_benchmark_cases,
    run_evaluation,
)
from modules.architecture_design.schemas import (
    ASRBatch,
    ASRInput,
    HighLevelArchitectureDesign,
    ArchitectureComponent,
    ArchitectureConnection,
    QualityAttribute,
)


def test_multilabel_metrics_exact_match():
    preds = [{"Scalability", "Reliability"}]
    gt = [{"Scalability", "Reliability"}]
    metrics = compute_multilabel_metrics(preds, gt)

    assert metrics.micro_precision == 1.0
    assert metrics.micro_recall == 1.0
    assert metrics.micro_f1 == 1.0
    assert metrics.macro_f1 == 1.0


def test_multilabel_metrics_partial_match():
    preds = [{"Scalability", "Performance"}, {"Security"}]
    gt = [{"Scalability", "Reliability"}, {"Security", "Maintainability"}]
    metrics = compute_multilabel_metrics(preds, gt)

    # Preds: 3 total labels. GT: 4 total labels. TP: Scalability, Security = 2.
    # FP: Performance = 1. FN: Reliability, Maintainability = 2.
    assert metrics.micro_precision == round(2 / 3, 4)
    assert metrics.micro_recall == round(2 / 4, 4)
    assert 0.0 < metrics.micro_f1 < 1.0
    assert "Scalability" in metrics.per_label
    assert metrics.per_label["Scalability"].precision == 1.0


def test_multilabel_metrics_empty():
    preds = [set()]
    gt = [set()]
    metrics = compute_multilabel_metrics(preds, gt)
    assert metrics.micro_f1 == 0.0
    assert metrics.macro_f1 == 0.0


def test_ranking_metrics_top1_and_mrr():
    # Case 1: First prediction matches (Rank 1 -> RR = 1.0)
    # Case 2: Second prediction matches (Rank 2 -> RR = 0.5)
    # Case 3: No prediction matches (RR = 0.0)
    preds = [
        ["Event-Driven Architecture", "Microservices", "Layered Architecture"],
        ["Modular Monolith", "Microservices", "Layered Architecture"],
        ["Pipeline", "Space-Based", "Layered Architecture"],
    ]
    acceptable = [
        ["Event-Driven Architecture"],
        ["Microservices"],
        ["Service-Oriented Architecture"],
    ]

    metrics = compute_ranking_metrics(preds, acceptable, k=3)
    # Top 1 hit: case 1 (1/3 = 0.3333)
    assert metrics.top1_hit_rate == round(1 / 3, 4)
    # Top 3 hits: case 1 and case 2 (2/3 = 0.6667)
    assert metrics.top3_hit_rate == round(2 / 3, 4)
    # MRR: (1.0 + 0.5 + 0.0) / 3 = 0.5
    assert metrics.mean_reciprocal_rank == round(1.5 / 3, 4)


def test_structural_metrics_traceability():
    batch = ASRBatch(
        project_id="PROJ-1",
        asrs=[
            ASRInput(requirement_id="REQ-01", statement="High scalability requirement"),
        ],
    )
    design = HighLevelArchitectureDesign(
        style="Microservices",
        components=[
            ArchitectureComponent(
                component_id="worker_svc",
                name="Worker Service",
                responsibility="Process events",
                component_type="service",
                grounding_type="requirement_derived",
                related_requirements=["REQ-01"],
                related_quality_attributes=["Scalability"],
            ),
            ArchitectureComponent(
                component_id="orphan_svc",
                name="Orphan Service",
                responsibility="Unknown",
                component_type="service",
                grounding_type="requirement_derived",
                related_requirements=[],  # Unsupported business component
                related_quality_attributes=[QualityAttribute.SECURITY],
            ),
        ],
        connections=[
            ArchitectureConnection(
                source="worker_svc",
                target="orphan_svc",
                relationship="calls",
            )
        ],
        design_rationale="Test structural metrics.",
        evidence_ids=[],
    )

    metrics = compute_structural_metrics([design], [batch])
    assert metrics.requirement_traceability_ratio == 1.0
    assert metrics.qa_traceability_ratio == 1.0
    assert metrics.valid_connection_ratio == 1.0
    assert metrics.unsupported_component_count == 1


def test_load_benchmark_cases():
    bench_file = Path(__file__).resolve().parent.parent / "datasets" / "architecture_decision" / "benchmark_cases.json"
    cases = load_benchmark_cases(bench_file)
    assert len(cases) >= 5
    assert cases[0].case_id == "ARCH-001"
    assert len(cases[0].asrs) > 0
    assert len(cases[0].expected_quality_attributes) > 0
    assert len(cases[0].expected_preferred_styles) > 0


def test_run_evaluation_end_to_end():
    bench_file = Path(__file__).resolve().parent.parent / "datasets" / "architecture_decision" / "benchmark_cases.json"
    with tempfile.TemporaryDirectory() as tmpdir:
        report, logs = run_evaluation(
            benchmark_path=bench_file,
            output_dir=tmpdir,
            save_report=True,
            evaluate_design=False,
        )

        assert report.total_cases >= 5
        assert report.ranking_metrics.top1_hit_rate >= 0.0
        assert report.ranking_metrics.mean_reciprocal_rank >= 0.0
        assert "case_predictions" in logs
        assert len(logs["case_predictions"]) == report.total_cases

        # Verify output json file was written
        out_files = list(Path(tmpdir).glob("architecture_eval_*.json"))
        assert len(out_files) == 1
