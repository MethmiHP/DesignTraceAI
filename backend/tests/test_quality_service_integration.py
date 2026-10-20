from datetime import datetime

import pytest

from modules.quality_evaluation.llm.structured_schemas import (
    LLMQualityAssessment,
)
from modules.quality_evaluation.llm.stub_provider import (
    StubQualityLLMProvider,
)
from modules.quality_evaluation.schemas import (
    QualityEvaluationRequest,
    RuleStatus,
)
from modules.quality_evaluation.service import (
    QualityEvaluationService,
)


def build_request() -> QualityEvaluationRequest:

    payload = {
        "project_id": "QUALITY-INTEGRATION-001",
        "functional_requirements": [
            {
                "requirement_id": "FR-001",
                "statement": (
                    "A customer shall submit "
                    "a bank transfer."
                ),
                "priority": "High",
            },
            {
                "requirement_id": "FR-002",
                "statement": (
                    "A customer shall view "
                    "all transfers."
                ),
                "priority": "Medium",
            },
        ],
        "non_functional_requirements": [
            {
                "requirement_id": "NFR-SEC-001",
                "statement": (
                    "Protected API operations "
                    "shall require authentication."
                ),
                "category": "Security",
                "priority": "High",
            },
            {
                "requirement_id": "NFR-SCAL-001",
                "statement": (
                    "The system shall support "
                    "growth in transfer volume."
                ),
                "category": "Scalability",
                "priority": "High",
            },
        ],
        "architecture": {
            "architecture_id": "ARCH-001",
            "selected_architecture": (
                "Modular Architecture"
            ),
            "elements": [
                {
                    "element_id": "COMP-001",
                    "name": "Transfer Service",
                    "type": "Service",
                    "main_responsibility": (
                        "Manage bank transfers."
                    ),
                }
            ],
        },
        "database": {
            "entities": [
                {
                    "entity_id": "DB-001",
                    "name": "Transfer",
                    "attributes": [
                        "transfer_id",
                        "source_account_id",
                        "destination_account_id",
                        "amount",
                    ],
                    "primary_key": (
                        "transfer_id"
                    ),
                    "foreign_keys": [],
                    "constraints": [],
                }
            ],
            "relationships": [],
            "constraints": [],
        },
        "api_component_design": {
            "responsibilities": [
                {
                    "requirement_id": "FR-001",
                    "element_id": "COMP-001",
                    "element_name": (
                        "Transfer Service"
                    ),
                    "detailed_responsibility": (
                        "Submit and manage "
                        "bank transfers."
                    ),
                    "mapping_reason": (
                        "Mapped from the "
                        "transfer requirement."
                    ),
                }
            ],
            "api_operations": [
                {
                    "operation_id": (
                        "submitTransfer"
                    ),
                    "requirement_id": "FR-001",
                    "element_id": "COMP-001",
                    "method": "POST",
                    "path": "/transfers",
                    "request_schema": {
                        "amount": "number",
                    },
                    "response_schema": {
                        "transfer_id": "string",
                    },
                    "error_responses": {},
                },
                {
                    "operation_id": (
                        "listTransfers"
                    ),
                    "requirement_id": "FR-002",
                    "element_id": "COMP-001",
                    "method": "GET",
                    "path": "/transfers",
                    "request_schema": {},
                    "response_schema": {
                        "transfer_id": "string",
                    },
                    "error_responses": {},
                },
            ],
            "openapi_document": {
                "openapi": "3.1.0",
                "info": {
                    "title": "Transfer API",
                    "version": "1.0.0",
                },
                "paths": {
                    "/transfers": {
                        "post": {
                            "operationId": (
                                "submitTransfer"
                            ),
                            "responses": {
                                "200": {
                                    "description": (
                                        "Transfer submitted"
                                    ),
                                }
                            },
                        },
                        "get": {
                            "operationId": (
                                "listTransfers"
                            ),
                            "responses": {
                                "200": {
                                    "description": (
                                        "Transfers returned"
                                    ),
                                }
                            },
                        },
                    }
                },
            },
        },
    }

    return (
        QualityEvaluationRequest
        .model_validate(
            payload
        )
    )


def build_stub_provider():

    response = (
        LLMQualityAssessment(
            status="FAIL",
            evidence=[
                (
                    "FR-001 describes a "
                    "security-sensitive "
                    "bank transfer operation."
                ),
                (
                    "POST /transfers has no "
                    "explicit security "
                    "declaration."
                ),
            ],
            rationale=(
                "The supplied design contains "
                "a security-sensitive operation "
                "without explicit access-control "
                "evidence."
            ),
            affected_nfr_ids=[
                "NFR-SEC-001"
            ],
            confidence=0.95,
            recommendation=(
                "Define explicit authentication "
                "and authorization requirements "
                "for the protected operation."
            ),
        )
    )

    return (
        StubQualityLLMProvider(
            response=response
        )
    )


@pytest.fixture(scope="module")
def evaluation_response():

    service = (
        QualityEvaluationService(
            llm_provider=(
                build_stub_provider()
            ),
            enable_llm=True,
        )
    )

    return service.evaluate(
        build_request()
    )


def test_service_returns_complete_response(
    evaluation_response,
):

    response = evaluation_response

    assert (
        response.project_id
        == "QUALITY-INTEGRATION-001"
    )

    assert response.evaluation_id.startswith(
        "QE-"
    )

    assert len(
        response.evaluation_id
    ) == 15

    assert response.generated_at

    generated_at = (
        datetime.fromisoformat(
            response.generated_at
        )
    )

    assert (
        generated_at.tzinfo
        is not None
    )

    assert response.summary


def test_service_selects_expected_rules(
    evaluation_response,
):

    response = evaluation_response

    expected_rule_ids = {
        "OPS-001",
        "MAIN-001",
        "USE-001",
        "SEC-001",
        "SCAL-001",
        "SEC-002",
        "SEC-003",
        "SEC-004",
        "SEC-005",
        "SEC-006",
        "SEC-007",
        "SEC-008",
    }

    assert set(
        response.applicable_rule_ids
    ) == expected_rule_ids

    assert len(
        response.rule_results
    ) == 12


def test_service_returns_expected_rule_statuses(
    evaluation_response,
):

    response = evaluation_response

    results_by_id = {
        result.rule_id: result
        for result
        in response.rule_results
    }

    assert (
        results_by_id[
            "OPS-001"
        ].status
        == RuleStatus.PASS
    )

    assert (
        results_by_id[
            "MAIN-001"
        ].status
        == RuleStatus.PASS
    )

    assert (
        results_by_id[
            "USE-001"
        ].status
        == RuleStatus.PASS
    )

    assert (
        results_by_id[
            "SEC-001"
        ].status
        == RuleStatus.FAIL
    )

    assert (
        results_by_id[
            "SCAL-001"
        ].status
        == RuleStatus.FAIL
    )

    assert (
        results_by_id[
            "SEC-002"
        ].status
        == RuleStatus.FAIL
    )


def test_service_creates_expected_findings(
    evaluation_response,
):
    # The fixture intentionally returns FAIL for every semantic rule;
    # these counts test orchestration, not real LLM judgments.

    response = evaluation_response

    assert len(
        response.findings
    ) == 9

    finding_rule_ids = {
        finding.rule_id
        for finding
        in response.findings
    }

    assert finding_rule_ids == {
        "SEC-001",
        "SCAL-001",
        "SEC-002",
        "SEC-003",
        "SEC-004",
        "SEC-005",
        "SEC-006",
        "SEC-007",
        "SEC-008",
    }

    assert all(
        finding.finding_id.startswith(
            "QF-"
        )
        for finding
        in response.findings
    )


def test_service_preserves_semantic_recommendation(
    evaluation_response,
):

    response = evaluation_response

    security_finding = next(
        finding
        for finding
        in response.findings
        if finding.rule_id
        == "SEC-001"
    )

    assert (
        security_finding.recommendation
        == (
            "Define explicit authentication "
            "and authorization requirements "
            "for the protected operation."
        )
    )

    assert (
        "NFR-SEC-001"
        in security_finding
        .affected_nfr_ids
    )


def test_service_groups_related_security_findings(
    evaluation_response,
):

    response = evaluation_response

    assert len(
        response.finding_groups
    ) == 1

    group = (
        response.finding_groups[0]
    )

    assert (
        group.group_key
        == "API_ACCESS_CONTROL"
    )

    assert (
        group.quality_attribute
        == "Security"
    )

    assert set(
        group.rule_ids
    ) == {
        "SEC-001",
        "SEC-002",
        "SEC-003",
        "SEC-005",
    }

    assert len(
        group.finding_ids
    ) == 4

    assert (
        "NFR-SEC-001"
        in group.affected_nfr_ids
    )


def test_grouping_does_not_change_rule_results(
    evaluation_response,
):

    response = evaluation_response

    passed = [
        result
        for result
        in response.rule_results
        if result.status
        == RuleStatus.PASS
    ]

    failed = [
        result
        for result
        in response.rule_results
        if result.status
        == RuleStatus.FAIL
    ]

    skipped = [
        result
        for result
        in response.rule_results
        if result.status
        == RuleStatus.SKIPPED
    ]

    assert len(
        passed
    ) == 3

    assert len(
        failed
    ) == 9

    assert len(
        skipped
    ) == 0

    assert len(
        response.rule_results
    ) == 12

    assert len(
        response.findings
    ) == 9

    assert len(
        response.finding_groups
    ) == 1


def test_service_calculates_quality_pass(
    evaluation_response,
):

    response = evaluation_response

    assert (
        response
        .metrics
        .quality_pass_percentage
        == 25.0
    )


def test_service_calculates_nfr_coverage(
    evaluation_response,
):

    response = evaluation_response

    assert (
        response
        .metrics
        .nfr_coverage_percentage
        == 100.0
    )


def test_service_skips_semantic_rule_when_llm_is_disabled():

    service = (
        QualityEvaluationService(
            enable_llm=False,
        )
    )

    response = service.evaluate(
        build_request()
    )

    results_by_id = {
        result.rule_id: result
        for result
        in response.rule_results
    }

    # Semantic rule must not fabricate a result
    assert (
        results_by_id[
            "SEC-001"
        ].status
        == RuleStatus.SKIPPED
    )

    # No LLM provider should be reported
    assert (
        results_by_id[
            "SEC-001"
        ].provider
        is None
    )

    # No semantic finding should be created
    finding_rule_ids = {
        finding.rule_id
        for finding
        in response.findings
    }

    assert (
        "SEC-001"
        not in finding_rule_ids
    )

    # Deterministic failures should still be detected
    assert (
        "SCAL-001"
        in finding_rule_ids
    )

    assert (
        "SEC-002"
        in finding_rule_ids
    )

    # All seven selected semantic Security rules are skipped
    assert (
        response.metrics.skipped_rules
        == 7
    )

    assert (
        response.metrics.passed_rules
        == 3
    )

    assert (
        response.metrics.failed_rules
        == 2
    )

    # SEC-001 and SEC-002 cannot form a group
    # because SEC-001 was skipped
    assert (
        response.finding_groups
        == []
    )

def test_nfr_coverage_is_none_when_no_nfrs_exist():

    request = (
        build_request()
        .model_copy(
            deep=True
        )
    )

    request.non_functional_requirements = []

    service = (
        QualityEvaluationService(
            enable_llm=False,
        )
    )

    response = service.evaluate(
        request
    )

    assert (
        response.metrics.applicable_nfrs
        == 0
    )

    assert (
        response.metrics.evaluated_nfrs
        == 0
    )

    # No NFRs means coverage is not applicable,
    # not a successful 100 percent result
    assert (
        response
        .metrics
        .nfr_coverage_percentage
        is None
    )

    for category in (
        response
        .metrics
        .category_summaries
    ):

        if (
            category.applicable_nfrs
            == 0
        ):
            assert (
                category
                .nfr_coverage_percentage
                is None
            )

    assert "NFR Coverage: Not applicable." in response.summary
    assert response.model_dump(mode="json")["metrics"]["nfr_coverage_percentage"] is None


def test_service_handles_no_applicable_rules(
    monkeypatch,
):

    service = (
        QualityEvaluationService(
            enable_llm=False,
        )
    )

    # Simulate a project where no quality
    # rules are applicable
    monkeypatch.setattr(
        service.rule_selector,
        "select",
        lambda context, rules: [],
    )

    response = service.evaluate(
        build_request()
    )

    assert (
        response.applicable_rule_ids
        == []
    )

    assert (
        response.rule_results
        == []
    )

    assert (
        response.findings
        == []
    )

    assert (
        response.finding_groups
        == []
    )

    assert (
        response.metrics.total_applicable_rules
        == 0
    )

    assert (
        response.metrics.passed_rules
        == 0
    )

    assert (
        response.metrics.failed_rules
        == 0
    )

    assert (
        response.metrics.skipped_rules
        == 0
    )

    # No applicable rules means the
    # Quality Pass percentage is N/A
    assert (
        response
        .metrics
        .quality_pass_percentage
        is None
    )

    assert response.summary
