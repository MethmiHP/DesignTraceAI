from modules.quality_evaluation.llm.structured_schemas import (
    LLMQualityAssessment,
)
from modules.quality_evaluation.llm.stub_provider import (
    StubQualityLLMProvider,
)
from modules.quality_evaluation.rule_repository import (
    QualityRuleRepository,
)
from modules.quality_evaluation.schemas import (
    NFRCategory,
    QualityEvaluationRequest,
    RuleStatus,
)
from modules.quality_evaluation.semantic_evaluator import (
    SemanticEvaluator,
)
from modules.quality_evaluation.service import (
    QualityEvaluationService,
)


def get_base_request():
    return {
        "project_id": "banking-001",

        "functional_requirements": [
            {
                "requirement_id": "FR-001",
                "statement": (
                    "A customer shall submit a "
                    "transfer between bank accounts."
                ),
                "priority": "High",
            }
        ],

        "non_functional_requirements": [],

        "architecture": {
            "architecture_id": "ARCH-001",
            "selected_architecture": (
                "Modular Architecture"
            ),
            "elements": [
                {
                    "element_id": (
                        "COMP-TRANSFER"
                    ),
                    "name": (
                        "Transfer Service"
                    ),
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
                    "entity_id": (
                        "DB-TRANSFER"
                    ),
                    "name": "Transfer",
                    "attributes": [
                        "transfer_id",
                        "source_account_id",
                        "destination_account_id",
                        "amount",
                        "status",
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
                    "requirement_id": (
                        "FR-001"
                    ),
                    "element_id": (
                        "COMP-TRANSFER"
                    ),
                    "element_name": (
                        "Transfer Service"
                    ),
                    "detailed_responsibility": (
                        "Allow customers to "
                        "submit transfers."
                    ),
                }
            ],

            "api_operations": [
                {
                    "operation_id": (
                        "submitTransfer"
                    ),
                    "requirement_id": (
                        "FR-001"
                    ),
                    "element_id": (
                        "COMP-TRANSFER"
                    ),
                    "method": "POST",
                    "path": "/transfers",
                    "request_schema": {
                        "source_account_id":
                            "string",
                        "destination_account_id":
                            "string",
                        "amount":
                            "number",
                    },
                    "response_schema": {
                        "transfer_id":
                            "string",
                        "status":
                            "string",
                    },
                    "error_responses": {
                        "400":
                            "Invalid request",
                    },
                }
            ],

            "openapi_document": {
                "openapi": "3.1.0",
                "info": {
                    "title": "Banking API",
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
                                        "Success"
                                    )
                                },
                                "400": {
                                    "description": (
                                        "Invalid request"
                                    )
                                },
                            },
                        }
                    }
                },
            },
        },
    }


def test_all_11_nfr_categories_are_supported():

    assert len(
        list(
            NFRCategory
        )
    ) == 11


def test_basic_quality_evaluation_runs():

    request = (
        QualityEvaluationRequest(
            **get_base_request()
        )
    )

    service = (
        QualityEvaluationService(
            enable_llm=False
        )
    )

    result = service.evaluate(
        request
    )

    assert (
        result.project_id
        == "banking-001"
    )

    assert (
        result.metrics
        .total_applicable_rules
        > 0
    )


def test_security_nfr_without_openapi_security_fails():

    payload = get_base_request()

    payload[
        "non_functional_requirements"
    ] = [
        {
            "requirement_id":
                "NFR-SEC-001",
            "statement":
                (
                    "Protected API operations "
                    "shall require authentication."
                ),
            "category":
                "Security",
        }
    ]

    request = QualityEvaluationRequest(
        **payload
    )

    service = QualityEvaluationService(
        enable_llm=False
    )

    result = service.evaluate(
        request
    )

    finding_rule_ids = {
        finding.rule_id
        for finding
        in result.findings
    }

    assert (
        "SEC-002"
        in finding_rule_ids
    )


def test_scalability_detects_missing_pagination():

    payload = get_base_request()

    payload[
        "non_functional_requirements"
    ] = [
        {
            "requirement_id":
                "NFR-SCAL-001",
            "statement":
                (
                    "The API shall support "
                    "growth in transfer volume."
                ),
            "category":
                "Scalability",
        }
    ]

    payload[
        "api_component_design"
    ][
        "api_operations"
    ] = [
        {
            "operation_id":
                "listTransfers",
            "requirement_id":
                "FR-001",
            "element_id":
                "COMP-TRANSFER",
            "method":
                "GET",
            "path":
                "/transfers",
            "request_schema":
                {},
            "response_schema":
                {},
            "error_responses":
                {},
        }
    ]

    payload[
        "api_component_design"
    ][
        "openapi_document"
    ][
        "paths"
    ] = {
        "/transfers": {
            "get": {
                "operationId":
                    "listTransfers",
                "responses": {
                    "200": {
                        "description":
                            "Success"
                    }
                },
            }
        }
    }

    request = QualityEvaluationRequest(
        **payload
    )

    service = QualityEvaluationService(
        enable_llm=False
    )

    result = service.evaluate(
        request
    )

    assert any(
        finding.rule_id
        == "SCAL-001"
        for finding
        in result.findings
    )


def test_invalid_database_foreign_key_detected():

    payload = get_base_request()

    payload[
        "database"
    ][
        "entities"
    ][0][
        "foreign_keys"
    ] = [
        (
            "customer_id -> "
            "MissingCustomer"
        )
    ]

    request = QualityEvaluationRequest(
        **payload
    )

    service = QualityEvaluationService(
        enable_llm=False
    )

    result = service.evaluate(
        request
    )

    assert any(
        finding.rule_id
        == "OPS-002"
        for finding
        in result.findings
    )


def test_semantic_evaluator_uses_structured_provider():

    request = QualityEvaluationRequest(
        **get_base_request()
    )

    rules = (
        QualityRuleRepository()
        .load_rules()
    )

    security_rule = next(
        rule
        for rule in rules
        if rule.rule_id
        == "SEC-001"
    )

    response = LLMQualityAssessment(
        status="FAIL",
        evidence=[
            (
                "POST /transfers performs "
                "a customer bank transfer."
            )
        ],
        rationale=(
            "The operation appears sensitive "
            "and no explicit security "
            "requirement is supplied."
        ),
        affected_nfr_ids=[],
        confidence=0.90,
        recommendation=(
            "Define authentication and "
            "authorization requirements."
        ),
    )

    provider = (
        StubQualityLLMProvider(
            response
        )
    )

    evaluator = SemanticEvaluator(
        provider
    )

    result = evaluator.evaluate(
        security_rule,
        request,
    )

    assert (
        result.status
        == RuleStatus.FAIL
    )

    assert (
        result.provider
        == "stub"
    )

    assert (
        provider.last_prompt
        is not None
    )


def test_quality_metrics_include_all_categories():

    request = QualityEvaluationRequest(
        **get_base_request()
    )

    service = QualityEvaluationService(
        enable_llm=False
    )

    result = service.evaluate(
        request
    )

    categories = {
        summary.category
        for summary
        in (
            result
            .metrics
            .category_summaries
        )
    }

    assert categories == set(
        NFRCategory
    )