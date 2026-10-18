from copy import deepcopy

import pytest

from modules.quality_evaluation.deterministic_evaluator import (
    DeterministicEvaluator,
)
from modules.quality_evaluation.llm.structured_schemas import (
    LLMQualityAssessment,
)
from modules.quality_evaluation.llm.stub_provider import (
    StubQualityLLMProvider,
)
from modules.quality_evaluation.rule_repository import (
    QualityRuleRepository,
)
from modules.quality_evaluation.rule_selector import (
    ApplicableRuleSelector,
)
from modules.quality_evaluation.schemas import (
    QualityEvaluationRequest,
    RuleStatus,
)
from modules.quality_evaluation.semantic_evaluator import (
    SemanticEvaluator,
)


def build_base_payload() -> dict:
    return {
        "project_id": "QUALITY-NFR-SCENARIO-TEST",
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
        "non_functional_requirements": [],
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
                    "primary_key": "transfer_id",
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
                    "element_name": "Transfer Service",
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
                    "operation_id": "submitTransfer",
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
                    "operation_id": "listTransfers",
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


def build_context(
    category: str,
    statement: str,
) -> QualityEvaluationRequest:

    payload = build_base_payload()

    payload[
        "non_functional_requirements"
    ] = [
        {
            "requirement_id": "NFR-001",
            "statement": statement,
            "category": category,
            "priority": "High",
        }
    ]

    return (
        QualityEvaluationRequest
        .model_validate(
            payload
        )
    )


def load_rules():
    repository = (
        QualityRuleRepository()
    )

    return repository.load_rules()


def get_rule(
    rule_id: str,
):
    rules = load_rules()

    return next(
        rule
        for rule in rules
        if rule.rule_id == rule_id
    )


@pytest.mark.parametrize(
    (
        "category",
        "statement",
        "expected_rule_id",
    ),
    [
        (
            "Availability",
            (
                "The system shall remain "
                "available during normal "
                "service operation."
            ),
            "AVAIL-001",
        ),
        (
            "Fault Tolerance",
            (
                "The system shall handle "
                "service failures without "
                "losing requests."
            ),
            "FT-001",
        ),
        (
            "Legal",
            (
                "The system shall support "
                "the documented legal "
                "data-handling requirement."
            ),
            "LEGAL-001",
        ),
        (
            "Look and Feel",
            (
                "The user interface shall "
                "use a consistent visual "
                "presentation."
            ),
            "LAF-001",
        ),
        (
            "Maintainability",
            (
                "The design shall remain "
                "easy to modify and maintain."
            ),
            "MAIN-002",
        ),
        (
            "Operational",
            (
                "The system shall support "
                "operational monitoring."
            ),
            "OPER-001",
        ),
        (
            "Performance",
            (
                "Collection retrieval shall "
                "remain efficient as data "
                "volume increases."
            ),
            "PERF-001",
        ),
        (
            "Portability",
            (
                "The system shall support "
                "deployment across different "
                "environments."
            ),
            "PORT-001",
        ),
        (
            "Scalability",
            (
                "The system shall support "
                "growth in transfer volume."
            ),
            "SCAL-001",
        ),
        (
            "Security",
            (
                "Protected API operations "
                "shall require authentication."
            ),
            "SEC-002",
        ),
        (
            "Usability",
            (
                "Consumer-facing API "
                "operations shall be clear "
                "and consistent."
            ),
            "USE-002",
        ),
    ],
)
def test_nfr_category_selects_expected_rule(
    category: str,
    statement: str,
    expected_rule_id: str,
):
    context = build_context(
        category,
        statement,
    )

    selector = (
        ApplicableRuleSelector()
    )

    selected = selector.select(
        context,
        load_rules(),
    )

    selected_ids = {
        rule.rule_id
        for rule in selected
    }

    assert (
        expected_rule_id
        in selected_ids
    )


@pytest.mark.parametrize(
    (
        "category",
        "statement",
        "rule_id",
    ),
    [
        (
            "Fault Tolerance",
            (
                "The system shall handle "
                "failures of state-changing "
                "operations."
            ),
            "FT-001",
        ),
        (
            "Performance",
            (
                "Collection retrieval shall "
                "remain efficient as data "
                "volume increases."
            ),
            "PERF-001",
        ),
        (
            "Scalability",
            (
                "The system shall support "
                "growth in transfer volume."
            ),
            "SCAL-001",
        ),
        (
            "Security",
            (
                "Protected API operations "
                "shall require authentication."
            ),
            "SEC-002",
        ),
    ],
)
def test_known_deterministic_issues_are_detected(
    category: str,
    statement: str,
    rule_id: str,
):
    context = build_context(
        category,
        statement,
    )

    rule = get_rule(
        rule_id
    )

    evaluator = (
        DeterministicEvaluator()
    )

    result = evaluator.evaluate(
        rule,
        context,
    )

    assert (
        result.status
        == RuleStatus.FAIL
    )

    assert result.evidence


@pytest.mark.parametrize(
    (
        "category",
        "statement",
        "rule_id",
    ),
    [
        (
            "Availability",
            (
                "The system shall remain "
                "available during normal "
                "service operation."
            ),
            "AVAIL-001",
        ),
        (
            "Legal",
            (
                "The system shall support "
                "the documented legal "
                "data-handling requirement."
            ),
            "LEGAL-001",
        ),
        (
            "Maintainability",
            (
                "The design shall remain "
                "easy to modify and maintain."
            ),
            "MAIN-002",
        ),
        (
            "Operational",
            (
                "The system shall support "
                "operational monitoring."
            ),
            "OPER-001",
        ),
        (
            "Portability",
            (
                "The system shall support "
                "deployment across different "
                "environments."
            ),
            "PORT-001",
        ),
        (
            "Usability",
            (
                "Consumer-facing API "
                "operations shall be clear "
                "and consistent."
            ),
            "USE-002",
        ),
    ],
)
def test_semantic_rules_return_structured_result(
    category: str,
    statement: str,
    rule_id: str,
):
    context = build_context(
        category,
        statement,
    )

    rule = get_rule(
        rule_id
    )

    response = (
        LLMQualityAssessment(
            status="FAIL",
            evidence=[
                (
                    "The supplied artifacts "
                    "do not contain enough "
                    "supporting design evidence."
                )
            ],
            rationale=(
                "The supplied design does "
                "not provide sufficient "
                "evidence for the NFR."
            ),
            affected_nfr_ids=[
                "NFR-001"
            ],
            confidence=0.90,
            recommendation=(
                "Add explicit supporting "
                "design evidence."
            ),
        )
    )

    provider = (
        StubQualityLLMProvider(
            response=response
        )
    )

    evaluator = (
        SemanticEvaluator(
            provider=provider
        )
    )

    result = evaluator.evaluate(
        rule,
        context,
    )

    assert (
        result.status
        == RuleStatus.FAIL
    )

    assert result.evidence

    assert (
        result.affected_nfr_ids
        == ["NFR-001"]
    )

    assert result.confidence == 0.90


def test_look_and_feel_can_be_skipped_without_ui_artifact():
    context = build_context(
        "Look and Feel",
        (
            "The user interface shall use "
            "a consistent visual style."
        ),
    )

    rule = get_rule(
        "LAF-001"
    )

    response = (
        LLMQualityAssessment(
            status="SKIPPED",
            evidence=[],
            rationale=(
                "No UI or presentation "
                "artifact was supplied."
            ),
            affected_nfr_ids=[
                "NFR-001"
            ],
            confidence=0.95,
            recommendation=None,
        )
    )

    provider = (
        StubQualityLLMProvider(
            response=response
        )
    )

    evaluator = (
        SemanticEvaluator(
            provider=provider
        )
    )

    result = evaluator.evaluate(
        rule,
        context,
    )

    assert (
        result.status
        == RuleStatus.SKIPPED
    )


def test_security_semantic_rule_can_use_fr_context():
    context = build_context(
        "Security",
        (
            "Protected API operations "
            "shall require authentication."
        ),
    )

    rule = get_rule(
        "SEC-001"
    )

    response = (
        LLMQualityAssessment(
            status="FAIL",
            evidence=[
                (
                    "FR-001 describes a "
                    "bank transfer operation."
                ),
                (
                    "POST /transfers has no "
                    "security declaration."
                ),
            ],
            rationale=(
                "The transfer operation is "
                "security-sensitive but has "
                "no explicit protection."
            ),
            affected_nfr_ids=[
                "NFR-001"
            ],
            confidence=0.95,
            recommendation=(
                "Define explicit security "
                "requirements."
            ),
        )
    )

    provider = (
        StubQualityLLMProvider(
            response=response
        )
    )

    evaluator = (
        SemanticEvaluator(
            provider=provider
        )
    )

    result = evaluator.evaluate(
        rule,
        context,
    )

    assert (
        result.status
        == RuleStatus.FAIL
    )

    assert (
        result.affected_nfr_ids
        == ["NFR-001"]
    )


def test_semantic_recommendation_is_preserved():
    context = build_context(
        "Maintainability",
        (
            "The design shall remain "
            "easy to modify and maintain."
        ),
    )

    rule = get_rule(
        "MAIN-002"
    )

    expected_recommendation = (
        "Separate unrelated responsibilities "
        "into focused components."
    )

    response = (
        LLMQualityAssessment(
            status="FAIL",
            evidence=[
                (
                    "The supplied component "
                    "contains unrelated "
                    "responsibilities."
                )
            ],
            rationale=(
                "The component mixes "
                "multiple unrelated concerns."
            ),
            affected_nfr_ids=[
                "NFR-001"
            ],
            confidence=0.91,
            recommendation=(
                expected_recommendation
            ),
        )
    )

    provider = (
        StubQualityLLMProvider(
            response=response
        )
    )

    evaluator = (
        SemanticEvaluator(
            provider=provider
        )
    )

    result = evaluator.evaluate(
        rule,
        context,
    )

    assert (
        result.recommendation
        == expected_recommendation
    )
