"""
Validation for generated Architecture Decision Records.

The validator checks structural completeness, traceability,
source-decision consistency, and basic ADR quality before
a record can be stored in the repository.
"""

from pydantic import BaseModel, Field

from modules.adr.schemas import (
    ADRRecord,
    DesignDecision,
)


class ADRValidationResult(BaseModel):
    """
    Result returned after validating a generated ADR.
    """

    adr_id: str

    valid: bool

    completeness_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
    )

    errors: list[str] = Field(default_factory=list)

    warnings: list[str] = Field(default_factory=list)


class ADRValidator:
    """
    Validates a generated ADR before persistence.
    """

    REQUIRED_TEXT_FIELDS = (
        "title",
        "context",
        "decision",
        "rationale",
    )

    def validate(
        self,
        adr: ADRRecord,
        source_decision: DesignDecision,
    ) -> ADRValidationResult:
        """
        Validate an ADR against structural and source-consistency rules.
        """

        errors: list[str] = []
        warnings: list[str] = []

        self._validate_required_text(
            adr,
            errors,
        )

        self._validate_ids(
            adr,
            source_decision,
            errors,
        )

        self._validate_source_consistency(
            adr,
            source_decision,
            errors,
        )

        self._validate_traceability(
            adr,
            source_decision,
            warnings,
        )

        self._validate_decision_evidence(
            adr,
            warnings,
        )

        completeness_score = self._calculate_completeness(
            adr
        )

        valid = len(errors) == 0

        return ADRValidationResult(
            adr_id=adr.adr_id,
            valid=valid,
            completeness_score=completeness_score,
            errors=errors,
            warnings=warnings,
        )

    def _validate_required_text(
        self,
        adr: ADRRecord,
        errors: list[str],
    ) -> None:
        """
        Ensure mandatory ADR text fields are present.
        """

        for field_name in self.REQUIRED_TEXT_FIELDS:
            value = getattr(adr, field_name)

            if not value or not value.strip():
                errors.append(
                    f"Required ADR field '{field_name}' is empty."
                )

    @staticmethod
    def _validate_ids(
        adr: ADRRecord,
        source_decision: DesignDecision,
        errors: list[str],
    ) -> None:
        """
        Validate project and source decision identifiers.
        """

        if adr.project_id != source_decision.project_id:
            errors.append(
                "ADR project ID does not match source decision project ID."
            )

        if (
            source_decision.decision_id
            not in adr.traceability.source_decision_ids
        ):
            errors.append(
                "Source decision ID is missing from ADR traceability."
            )

    @staticmethod
    def _validate_source_consistency(
        adr: ADRRecord,
        source_decision: DesignDecision,
        errors: list[str],
    ) -> None:
        """
        Ensure the ADR represents the original source decision.
        """

        if adr.decision.strip() != source_decision.decision.strip():
            errors.append(
                "ADR decision does not match the original source decision."
            )

        if (
            source_decision.source_module
            not in adr.traceability.source_modules
        ):
            errors.append(
                "ADR source module does not match the original decision source."
            )

    @staticmethod
    def _validate_traceability(
        adr: ADRRecord,
        source_decision: DesignDecision,
        warnings: list[str],
    ) -> None:
        """
        Check whether expected requirement and design links are preserved.
        """

        missing_requirements = set(
            source_decision.requirement_ids
        ) - set(
            adr.traceability.requirement_ids
        )

        if missing_requirements:
            warnings.append(
                "ADR is missing requirement links: "
                + ", ".join(sorted(missing_requirements))
            )

        missing_design_elements = set(
            source_decision.design_element_ids
        ) - set(
            adr.traceability.design_element_ids
        )

        if missing_design_elements:
            warnings.append(
                "ADR is missing design element links: "
                + ", ".join(sorted(missing_design_elements))
            )

    @staticmethod
    def _validate_decision_evidence(
        adr: ADRRecord,
        warnings: list[str],
    ) -> None:
        """
        Check important explanatory fields.
        """

        if not adr.alternatives:
            warnings.append(
                "No alternative solutions are recorded."
            )

        if not adr.trade_offs:
            warnings.append(
                "No trade-offs are recorded."
            )

        if not adr.consequences:
            warnings.append(
                "No consequences are recorded."
            )

        if not adr.benefits:
            warnings.append(
                "No benefits are recorded."
            )

        if not adr.risks:
            warnings.append(
                "No risks are recorded."
            )

        if not adr.evidence:
            warnings.append(
                "No supporting evidence is recorded."
            )

    @staticmethod
    def _calculate_completeness(
        adr: ADRRecord,
    ) -> float:
        """
        Calculate ADR field completeness.

        Completeness =
        completed expected fields / total expected fields.
        """

        values = [
            adr.title,
            adr.context,
            adr.decision,
            adr.rationale,
            adr.alternatives,
            adr.rejected_alternative_reasons,
            adr.decision_criteria,
            adr.benefits,
            adr.risks,
            adr.consequences,
            adr.trade_offs,
            adr.evidence,
            adr.traceability.requirement_ids,
            adr.traceability.design_element_ids,
            adr.traceability.source_decision_ids,
            adr.traceability.source_modules,
        ]

        completed = sum(
            1
            for value in values
            if bool(value)
        )

        return round(
            completed / len(values),
            4,
        )