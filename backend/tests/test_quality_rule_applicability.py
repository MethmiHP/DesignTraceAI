from copy import deepcopy

from modules.quality_evaluation.rule_repository import (
    QualityRuleRepository,
)
from modules.quality_evaluation.rule_selector import (
    ApplicableRuleSelector,
)
from modules.quality_evaluation.schemas import (
    QualityEvaluationRequest,
)


def build_request() -> dict:
    return {
        "project_id": "QUALITY-APPLICABILITY-TEST",
        "functional_requirements": [
            {
                "requirement_id": "FR-001",
                "statement": (
                    "A customer shall submit "
                    "a bank transfer."
                ),
                "priority": "High",
            }
        ],
        "non_functional_requirements": [],
        "architecture": {
            "architecture_id": "ARCH-001",
            "selected_architecture": "Modular Architecture",
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
                        "account_id",
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
                        "Submit bank transfers."
                    ),
                    "mapping_reason": (
                        "Mapped from transfer requirement."
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
                    "request_schema": {},
                    "response_schema": {},
                    "error_responses": {
                        "400": "Invalid request",
                    },
                }
            ],
            "openapi_document": {
                "openapi": "3.1.0",
                "info": {
                    "title": "Test API",
                    "version": "1.0.0",
                },
                "paths": {
                    "/transfers": {
                        "post": {
                            "operationId": "submitTransfer",
                            "responses": {
                                "200": {
                                    "description": "Success",
                                },
                                "400": {
                                    "description": "Invalid request",
                                },
                            },
                        }
                    }
                },
            },
        },
    }


def selected_rule_ids(
    payload: dict,
) -> set[str]:

    context = QualityEvaluationRequest.model_validate(
        payload
    )

    repository = QualityRuleRepository()

    rules = repository.load_rules()

    selector = ApplicableRuleSelector()

    selected = selector.select(
        context,
        rules,
    )

    return {
        rule.rule_id
        for rule in selected
    }


def test_ops_002_not_selected_without_foreign_keys():
    payload = build_request()

    rule_ids = selected_rule_ids(
        payload
    )

    assert "OPS-002" not in rule_ids


def test_ops_002_selected_when_foreign_key_exists():
    payload = build_request()

    payload["database"]["entities"].append(
        {
            "entity_id": "DB-002",
            "name": "Account",
            "attributes": [
                "account_id",
            ],
            "primary_key": "account_id",
            "foreign_keys": [],
            "constraints": [],
        }
    )

    payload[
        "database"
    ][
        "entities"
    ][0][
        "foreign_keys"
    ] = [
        "account_id -> Account.account_id"
    ]

    rule_ids = selected_rule_ids(
        payload
    )

    assert "OPS-002" in rule_ids


def test_sec_002_selected_for_authentication_nfr():
    payload = build_request()

    payload[
        "non_functional_requirements"
    ] = [
        {
            "requirement_id": "NFR-SEC-001",
            "statement": (
                "Protected API operations shall "
                "require authentication."
            ),
            "category": "Security",
            "priority": "High",
        }
    ]

    rule_ids = selected_rule_ids(
        payload
    )

    assert "SEC-002" in rule_ids


def test_sec_002_not_selected_for_encryption_only_nfr():
    payload = build_request()

    payload[
        "non_functional_requirements"
    ] = [
        {
            "requirement_id": "NFR-SEC-001",
            "statement": (
                "Stored customer information shall "
                "be encrypted at rest."
            ),
            "category": "Security",
            "priority": "High",
        }
    ]

    rule_ids = selected_rule_ids(
        payload
    )

    assert "SEC-002" not in rule_ids


def test_scal_001_not_selected_without_collection_get():
    payload = build_request()

    payload[
        "non_functional_requirements"
    ] = [
        {
            "requirement_id": "NFR-SCAL-001",
            "statement": (
                "The system shall support growth "
                "in transaction volume."
            ),
            "category": "Scalability",
            "priority": "High",
        }
    ]

    rule_ids = selected_rule_ids(
        payload
    )

    assert "SCAL-001" not in rule_ids


def test_scal_001_selected_with_collection_get():
    payload = build_request()

    payload[
        "non_functional_requirements"
    ] = [
        {
            "requirement_id": "NFR-SCAL-001",
            "statement": (
                "The system shall support growth "
                "in transaction volume."
            ),
            "category": "Scalability",
            "priority": "High",
        }
    ]

    payload[
        "api_component_design"
    ][
        "openapi_document"
    ][
        "paths"
    ][
        "/transfers"
    ][
        "get"
    ] = {
        "operationId": "listTransfers",
        "responses": {
            "200": {
                "description": "Success",
            }
        },
    }

    rule_ids = selected_rule_ids(
        payload
    )

    assert "SCAL-001" in rule_ids