#This checks whether the Coordinator sent usable input

from .schemas import APIComponentDesignRequest

from shared.models.common import ValidationIssue


class Preprocessor:

    def process(
        self,
        request: APIComponentDesignRequest,
    ) -> tuple[
        APIComponentDesignRequest,
        list[ValidationIssue],
    ]:

        issues: list[ValidationIssue] = []

        # Functional requirements
        if not request.functional_requirements:
            issues.append(
                ValidationIssue(
                    code="NO_FUNCTIONAL_REQUIREMENTS",
                    message="No functional requirements were provided.",
                    severity="ERROR",
                    field="functional_requirements",
                )
            )

        # Architecture
        if not request.architecture.elements:
            issues.append(
                ValidationIssue(
                    code="NO_ARCHITECTURE_ELEMENTS",
                    message="No architecture elements were provided.",
                    severity="ERROR",
                    field="architecture.elements",
                )
            )

        # Database
        if not request.database.entities:
            issues.append(
                ValidationIssue(
                    code="NO_DATABASE_ENTITIES",
                    message="No database entities were provided.",
                    severity="ERROR",
                    field="database.entities",
                )
            )

        # Duplicate requirement IDs
        requirement_ids = [
            requirement.requirement_id
            for requirement in request.functional_requirements
        ]

        if len(requirement_ids) != len(set(requirement_ids)):
            issues.append(
                ValidationIssue(
                    code="DUPLICATE_REQUIREMENT_ID",
                    message="Duplicate functional requirement IDs found.",
                    severity="ERROR",
                    field="functional_requirements",
                )
            )

        # Empty statements
        for requirement in request.functional_requirements:

            if not requirement.statement.strip():
                issues.append(
                    ValidationIssue(
                        code="EMPTY_REQUIREMENT",
                        message=(
                            f"{requirement.requirement_id} "
                            "contains an empty requirement statement."
                        ),
                        severity="ERROR",
                    )
                )

        return request, issues