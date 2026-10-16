"""
ADR service orchestration.

This service connects significance detection, evidence aggregation,
AI-assisted ADR generation, deterministic fallback generation,
validation, repository storage, and lifecycle-ready output into one
end-to-end workflow.
"""

from modules.adr.adr_generator import ADRGenerator
from modules.adr.adr_validator import ADRValidator
from modules.adr.evidence_aggregator import ADREvidenceAggregator
from modules.adr.llm.llm_adr_generator import LLMADRGenerator
from modules.adr.repository import ADRRepository
from modules.adr.schemas import (
    ADRGenerationMethod,
    ADRGenerationRequest,
    ADRGenerationResponse,
    ADRGenerationResult,
)
from modules.adr.significance_detector import ADRSignificanceDetector
from shared.llm.base import LLMProvider


class ADRService:
    """
    Main orchestration service for the ADR module.

    The service supports deterministic and LLM-assisted generation.

    If LLM-assisted generation fails, deterministic generation is used
    automatically as a safe fallback.
    """

    def __init__(
        self,
        repository: ADRRepository | None = None,
        llm_provider: LLMProvider | None = None,
        use_llm: bool = False,
    ):
        self.detector = ADRSignificanceDetector()

        self.aggregator = ADREvidenceAggregator()

        self.generator = ADRGenerator()

        self.validator = ADRValidator()

        self.repository = (
            repository
            or ADRRepository()
        )

        self.use_llm = use_llm

        self.llm_generator = (
            LLMADRGenerator(
                provider=llm_provider
            )
            if llm_provider is not None
            else None
        )

    async def generate_adrs(
        self,
        request: ADRGenerationRequest,
    ) -> ADRGenerationResponse:
        """
        Process all incoming design decisions.

        Significant decisions are converted into validated ADRs.

        Non-significant decisions are skipped.

        Duplicate source decisions are not regenerated.

        When enabled, LLM-assisted generation is attempted first.
        Provider or generation failures trigger deterministic fallback.
        """

        results: list[ADRGenerationResult] = []

        generated_count = 0
        skipped_count = 0

        for decision in request.decisions:

            # ---------------------------------------------------------
            # Prevent duplicate ADR generation
            # ---------------------------------------------------------

            existing_adr = (
                self.repository.find_by_source_decision_id(
                    decision.decision_id
                )
            )

            if existing_adr is not None:
                significance = self.detector.evaluate(
                    decision
                )

                skipped_count += 1

                results.append(
                    ADRGenerationResult(
                        decision=decision,
                        significance=significance,
                        adr=existing_adr,
                    )
                )

                continue

            # ---------------------------------------------------------
            # Significance detection
            # ---------------------------------------------------------

            significance = self.detector.evaluate(
                decision
            )

            if not significance.significant:
                skipped_count += 1

                results.append(
                    ADRGenerationResult(
                        decision=decision,
                        significance=significance,
                        adr=None,
                    )
                )

                continue

            # ---------------------------------------------------------
            # Evidence aggregation
            # ---------------------------------------------------------

            evidence = self.aggregator.aggregate(
                decision,
                significance,
            )

            existing_adrs = (
                self.repository.list_by_project(
                    request.project_id
                )
            )

            adr_number = (
                len(existing_adrs) + 1
            )

            # ---------------------------------------------------------
            # ADR generation
            # ---------------------------------------------------------

            adr = await self._generate_adr(
                evidence=evidence,
                adr_number=adr_number,
            )

            # ---------------------------------------------------------
            # ADR validation
            # ---------------------------------------------------------

            validation = self.validator.validate(
                adr,
                decision,
            )

            if not validation.valid:
                raise ValueError(
                    f"Generated ADR '{adr.adr_id}' "
                    f"failed validation: "
                    + "; ".join(
                        validation.errors
                    )
                )

            # ---------------------------------------------------------
            # Repository storage
            # ---------------------------------------------------------

            self.repository.save(
                adr
            )

            generated_count += 1

            results.append(
                ADRGenerationResult(
                    decision=decision,
                    significance=significance,
                    adr=adr,
                )
            )

        return ADRGenerationResponse(
            project_id=request.project_id,
            results=results,
            generated_adr_count=generated_count,
            skipped_decision_count=skipped_count,
        )

    async def _generate_adr(
        self,
        evidence,
        adr_number: int,
    ):
        """
        Generate an ADR using the configured generation strategy.

        LLM succeeds:
            generation_method = llm

        LLM fails:
            generation_method = deterministic_fallback

        LLM disabled:
            generation_method = deterministic
        """

        if (
            self.use_llm
            and self.llm_generator is not None
        ):
            try:
                return await self.llm_generator.generate(
                    evidence=evidence,
                    adr_number=adr_number,
                )

            except Exception:
                fallback_adr = self.generator.generate(
                    evidence=evidence,
                    adr_number=adr_number,
                )

                return fallback_adr.model_copy(
                    update={
                        "generation_method": (
                            ADRGenerationMethod.DETERMINISTIC_FALLBACK
                        )
                    }
                )

        return self.generator.generate(
            evidence=evidence,
            adr_number=adr_number,
        )