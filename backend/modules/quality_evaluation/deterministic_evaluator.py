import re
from collections import Counter

from .schemas import (
    CheckType,
    QualityEvaluationRequest,
    QualityRule,
    RuleEvaluationResult,
    RuleStatus,
)


class DeterministicEvaluator:

    def evaluate(
        self,
        rule: QualityRule,
        context: QualityEvaluationRequest,
    ) -> RuleEvaluationResult:

        if not rule.handler:
            return self._result(
                rule=rule,
                status=RuleStatus.SKIPPED,
                rationale=(
                    "The deterministic rule has no "
                    "configured handler."
                ),
            )

        handlers = {
            "openapi_version_is_3":
                self._openapi_version_is_3,

            "unique_operation_ids":
                self._unique_operation_ids,

            "database_foreign_keys_resolve":
                self._database_foreign_keys_resolve,

            "operation_ids_are_camel_case":
                self._operation_ids_are_camel_case,

            "api_has_error_responses":
                self._api_has_error_responses,

            "collection_get_has_pagination":
                self._collection_get_has_pagination,

            "security_declaration_present":
                self._security_declaration_present,
        }

        handler = handlers.get(
            rule.handler
        )

        if handler is None:
            return self._result(
                rule=rule,
                status=RuleStatus.SKIPPED,
                rationale=(
                    f"Unknown deterministic handler: "
                    f"{rule.handler}"
                ),
            )

        return handler(
            rule,
            context,
        )

    def _matching_nfr_ids(
        self,
        rule: QualityRule,
        context: QualityEvaluationRequest,
    ) -> list[str]:

        categories = set(
            rule.nfr_categories
        )

        return [
            nfr.requirement_id
            for nfr
            in context.non_functional_requirements
            if nfr.category in categories
        ]

    def _result(
        self,
        rule: QualityRule,
        status: RuleStatus,
        rationale: str,
        evidence: list[str] | None = None,
        affected_nfr_ids: list[str] | None = None,
    ) -> RuleEvaluationResult:

        return RuleEvaluationResult(
            rule_id=rule.rule_id,
            quality_attribute=(
                rule.quality_attribute
            ),
            check_type=(
                CheckType.DETERMINISTIC
            ),
            status=status,
            evidence=evidence or [],
            rationale=rationale,
            affected_nfr_ids=(
                affected_nfr_ids or []
            ),
        )

    def _openapi_version_is_3(
        self,
        rule: QualityRule,
        context: QualityEvaluationRequest,
    ) -> RuleEvaluationResult:

        document = (
            context
            .api_component_design
            .openapi_document
        )

        version = str(
            document.get(
                "openapi",
                "",
            )
        ).strip()

        if version.startswith("3."):
            return self._result(
                rule,
                RuleStatus.PASS,
                "The API contract declares OpenAPI 3.x.",
                [
                    f"openapi={version}"
                ],
            )

        return self._result(
            rule,
            RuleStatus.FAIL,
            (
                "The API contract does not declare "
                "an OpenAPI 3.x version."
            ),
            [
                f"openapi={version or 'missing'}"
            ],
        )

    def _unique_operation_ids(
        self,
        rule: QualityRule,
        context: QualityEvaluationRequest,
    ) -> RuleEvaluationResult:

        operation_ids = [
            operation.operation_id
            for operation
            in context
            .api_component_design
            .api_operations
            if operation.operation_id
        ]

        duplicates = [
            operation_id
            for operation_id, count
            in Counter(operation_ids).items()
            if count > 1
        ]

        if not duplicates:
            return self._result(
                rule,
                RuleStatus.PASS,
                (
                    "No duplicate API operation "
                    "identifiers were found."
                ),
            )

        return self._result(
            rule,
            RuleStatus.FAIL,
            (
                "Duplicate API operation identifiers "
                "were detected."
            ),
            [
                f"Duplicate operationId: {value}"
                for value in duplicates
            ],
        )

    def _database_foreign_keys_resolve(
        self,
        rule: QualityRule,
        context: QualityEvaluationRequest,
    ) -> RuleEvaluationResult:

        entity_names = {
            entity.name.casefold()
            for entity
            in context.database.entities
        }

        invalid_references: list[str] = []

        checked_references = 0

        for entity in context.database.entities:

            for foreign_key in entity.foreign_keys:

                if "->" not in foreign_key:
                    continue

                checked_references += 1

                target = (
                    foreign_key
                    .split("->", 1)[1]
                    .strip()
                )

                target = (
                    target
                    .split(".", 1)[0]
                    .split("(", 1)[0]
                    .strip()
                    .casefold()
                )

                if target not in entity_names:
                    invalid_references.append(
                        (
                            f"{entity.name}: "
                            f"{foreign_key}"
                        )
                    )

        if invalid_references:
            return self._result(
                rule,
                RuleStatus.FAIL,
                (
                    "One or more foreign keys reference "
                    "database entities that are not "
                    "present in the supplied database "
                    "design."
                ),
                invalid_references,
            )

        return self._result(
            rule,
            RuleStatus.PASS,
            (
                "All resolvable foreign-key targets "
                "refer to supplied database entities."
            ),
            [
                (
                    "Foreign-key references checked: "
                    f"{checked_references}"
                )
            ],
        )

    def _operation_ids_are_camel_case(
        self,
        rule: QualityRule,
        context: QualityEvaluationRequest,
    ) -> RuleEvaluationResult:

        invalid = []

        pattern = re.compile(
            r"^[a-z][A-Za-z0-9]*$"
        )

        for operation in (
            context
            .api_component_design
            .api_operations
        ):
            if not pattern.fullmatch(
                operation.operation_id
            ):
                invalid.append(
                    operation.operation_id
                )

        if not invalid:
            return self._result(
                rule,
                RuleStatus.PASS,
                (
                    "API operation identifiers use "
                    "a consistent lower-camel-case "
                    "format."
                ),
            )

        return self._result(
            rule,
            RuleStatus.FAIL,
            (
                "One or more operation identifiers "
                "do not follow the expected readable "
                "format."
            ),
            [
                f"Invalid operationId: {value}"
                for value in invalid
            ],
        )

    def _iter_openapi_operations(
        self,
        context: QualityEvaluationRequest,
    ):

        document = (
            context
            .api_component_design
            .openapi_document
        )

        paths = document.get(
            "paths",
            {},
        )

        allowed_methods = {
            "get",
            "post",
            "put",
            "patch",
            "delete",
        }

        for path, path_item in paths.items():

            if not isinstance(
                path_item,
                dict,
            ):
                continue

            for method, operation in (
                path_item.items()
            ):

                if (
                    method.lower()
                    not in allowed_methods
                ):
                    continue

                if not isinstance(
                    operation,
                    dict,
                ):
                    continue

                yield (
                    path,
                    method.lower(),
                    operation,
                    path_item,
                )

    def _api_has_error_responses(
        self,
        rule: QualityRule,
        context: QualityEvaluationRequest,
    ) -> RuleEvaluationResult:

        affected_nfr_ids = (
            self._matching_nfr_ids(
                rule,
                context,
            )
        )

        missing: list[str] = []

        checked = 0

        changing_methods = {
            "post",
            "put",
            "patch",
            "delete",
        }

        for (
            path,
            method,
            operation,
            _,
        ) in self._iter_openapi_operations(
            context
        ):

            if method not in changing_methods:
                continue

            checked += 1

            responses = operation.get(
                "responses",
                {},
            )

            has_error = any(
                str(status).startswith(
                    ("4", "5")
                )
                for status in responses
            )

            if not has_error:
                missing.append(
                    f"{method.upper()} {path}"
                )

        if missing:
            return self._result(
                rule,
                RuleStatus.FAIL,
                (
                    "Some state-changing API "
                    "operations do not define "
                    "failure responses."
                ),
                [
                    (
                        "No 4xx/5xx response: "
                        f"{operation}"
                    )
                    for operation in missing
                ],
                affected_nfr_ids,
            )

        return self._result(
            rule,
            RuleStatus.PASS,
            (
                "State-changing operations define "
                "failure responses."
            ),
            [
                (
                    "State-changing operations "
                    f"checked: {checked}"
                )
            ],
            affected_nfr_ids,
        )

    def _collection_get_has_pagination(
        self,
        rule: QualityRule,
        context: QualityEvaluationRequest,
    ) -> RuleEvaluationResult:

        affected_nfr_ids = (
            self._matching_nfr_ids(
                rule,
                context,
            )
        )

        pagination_names = {
            "page",
            "limit",
            "offset",
            "cursor",
            "page_size",
            "pagesize",
            "per_page",
            "perpage",
        }

        missing: list[str] = []

        checked = 0

        for (
            path,
            method,
            operation,
            path_item,
        ) in self._iter_openapi_operations(
            context
        ):

            if method != "get":
                continue

            if "{" in path:
                continue

            checked += 1

            parameters = []

            path_parameters = (
                path_item.get(
                    "parameters",
                    [],
                )
            )

            operation_parameters = (
                operation.get(
                    "parameters",
                    [],
                )
            )

            if isinstance(
                path_parameters,
                list,
            ):
                parameters.extend(
                    path_parameters
                )

            if isinstance(
                operation_parameters,
                list,
            ):
                parameters.extend(
                    operation_parameters
                )

            query_parameter_names = {
                str(
                    parameter.get(
                        "name",
                        "",
                    )
                ).casefold()
                for parameter
                in parameters
                if isinstance(
                    parameter,
                    dict,
                )
                and parameter.get(
                    "in"
                ) == "query"
            }

            if not (
                query_parameter_names
                & pagination_names
            ):
                missing.append(
                    f"GET {path}"
                )

        if missing:
            return self._result(
                rule,
                RuleStatus.FAIL,
                (
                    "One or more collection GET "
                    "operations do not expose a "
                    "bounded retrieval parameter."
                ),
                [
                    (
                        "Missing pagination controls: "
                        f"{operation}"
                    )
                    for operation in missing
                ],
                affected_nfr_ids,
            )

        return self._result(
            rule,
            RuleStatus.PASS,
            (
                "Collection retrieval operations "
                "provide bounded retrieval controls, "
                "or no collection GET operations "
                "were present."
            ),
            [
                (
                    "Collection GET operations "
                    f"checked: {checked}"
                )
            ],
            affected_nfr_ids,
        )

    def _security_declaration_present(
        self,
        rule: QualityRule,
        context: QualityEvaluationRequest,
    ) -> RuleEvaluationResult:

        affected_nfr_ids = (
            self._matching_nfr_ids(
                rule,
                context,
            )
        )

        document = (
            context
            .api_component_design
            .openapi_document
        )

        components = document.get(
            "components",
            {},
        )

        if not isinstance(
            components,
            dict,
        ):
            components = {}

        schemes = components.get(
            "securitySchemes",
            {},
        )

        has_scheme = bool(
            schemes
        )

        has_security_usage = bool(
            document.get(
                "security"
            )
        )

        if not has_security_usage:

            for (
                _,
                _,
                operation,
                _,
            ) in self._iter_openapi_operations(
                context
            ):
                if operation.get(
                    "security"
                ):
                    has_security_usage = True
                    break

        if (
            has_scheme
            and has_security_usage
        ):
            return self._result(
                rule,
                RuleStatus.PASS,
                (
                    "The OpenAPI document contains "
                    "an explicit security scheme and "
                    "applies a security declaration."
                ),
                affected_nfr_ids=(
                    affected_nfr_ids
                ),
            )

        evidence = []

        if not has_scheme:
            evidence.append(
                (
                    "OpenAPI components.securitySchemes "
                    "is missing or empty."
                )
            )

        if not has_security_usage:
            evidence.append(
                (
                    "No top-level or operation-level "
                    "security declaration was found."
                )
            )

        return self._result(
            rule,
            RuleStatus.FAIL,
            (
                "A Security NFR exists but the "
                "generated API contract does not "
                "contain sufficient explicit security "
                "declarations."
            ),
            evidence,
            affected_nfr_ids,
        )