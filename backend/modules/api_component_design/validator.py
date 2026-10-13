#This performs your first deterministic validation

from .schemas import (
    APIComponentDesignRequest,
    APIOperation,
    ResponsibilityDesign,
)

from shared.models.common import (
    ValidationIssue,
    ValidationResult,
)


class APIDesignValidator:

    ALLOWED_METHODS = {
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
    }

    def validate(
        self,
        request: APIComponentDesignRequest,
        responsibilities: list[ResponsibilityDesign],
        operations: list[APIOperation],
    ) -> ValidationResult:

        issues: list[ValidationIssue] = []

        requirement_ids = {
            requirement.requirement_id
            for requirement
            in request.functional_requirements
        }

        architecture_ids = {
            element.element_id
            for element
            in request.architecture.elements
        }

        operation_ids = set()
        method_paths = set()

        for operation in operations:

            # HTTP method
            if operation.method.upper() not in self.ALLOWED_METHODS:

                issues.append(
                    ValidationIssue(
                        code="INVALID_HTTP_METHOD",
                        message=(
                            f"{operation.operation_id} has an "
                            "unsupported HTTP method."
                        ),
                        severity="ERROR",
                    )
                )

            # Requirement mapping
            if (
                operation.requirement_id
                not in requirement_ids
            ):

                issues.append(
                    ValidationIssue(
                        code="UNKNOWN_REQUIREMENT",
                        message=(
                            f"{operation.operation_id} references "
                            "an unknown requirement."
                        ),
                        severity="ERROR",
                    )
                )

            # Architecture mapping
            if (
                operation.element_id
                not in architecture_ids
            ):

                issues.append(
                    ValidationIssue(
                        code="UNKNOWN_ARCHITECTURE_ELEMENT",
                        message=(
                            f"{operation.operation_id} references "
                            "an unknown architecture element."
                        ),
                        severity="ERROR",
                    )
                )

            # Duplicate operation ID
            if operation.operation_id in operation_ids:

                issues.append(
                    ValidationIssue(
                        code="DUPLICATE_OPERATION_ID",
                        message=(
                            f"Duplicate operation ID: "
                            f"{operation.operation_id}"
                        ),
                        severity="ERROR",
                    )
                )

            operation_ids.add(
                operation.operation_id
            )

            # Duplicate method + path
            key = (
                operation.method.upper(),
                operation.path,
            )

            if key in method_paths:

                issues.append(
                    ValidationIssue(
                        code="DUPLICATE_ENDPOINT",
                        message=(
                            f"Duplicate endpoint: "
                            f"{operation.method} "
                            f"{operation.path}"
                        ),
                        severity="ERROR",
                    )
                )

            method_paths.add(key)

            # Path format
            if not operation.path.startswith("/"):

                issues.append(
                    ValidationIssue(
                        code="INVALID_PATH",
                        message=(
                            f"{operation.operation_id} path "
                            "must start with '/'."
                        ),
                        severity="ERROR",
                    )
                )

        has_errors = any(
            issue.severity == "ERROR"
            for issue in issues
        )

        return ValidationResult(
            valid=not has_errors,
            issues=issues,
        )