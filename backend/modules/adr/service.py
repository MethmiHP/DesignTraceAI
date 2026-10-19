"""
ADR service orchestration.

This service connects ML-based significance detection,
deterministic significance fallback, evidence aggregation,
AI-assisted ADR generation, deterministic ADR fallback generation,
validation, repository storage, and lifecycle-ready output into one
end-to-end workflow.
"""

from modules.adr.adr_generator import ADRGenerator
from modules.adr.adr_validator import ADRValidator
from modules.adr.evidence_aggregator import ADREvidenceAggregator
from modules.adr.llm.llm_adr_generator import LLMADRGenerator
from modules.adr.ml_significance_classifier import (
    MLSignificanceClassifier,
)
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

    Significance detection:
        Primary   -> TF-IDF + Logistic Regression classifier
        Fallback  -> deterministic rule-based detector

    ADR generation:
        Primary   -> LLM-assisted generation when enabled
        Fallback  -> deterministic ADR generation
    """

    def __init__(
        self,
        repository: ADRRepository | None = None,
        llm_provider: LLMProvider | None = None,
        use_llm: bool = False,
    ):
        # ---------------------------------------------------------
        # Deterministic significance detector
        # ---------------------------------------------------------

        self.rule_detector = ADRSignificanceDetector()

        # ---------------------------------------------------------
        # ML significance classifier
        #
        # If the trained model is unavailable, the service can still
        # operate using deterministic significance detection.
        # ---------------------------------------------------------

        try:
            self.ml_detector = MLSignificanceClassifier()

        except Exception:
            self.ml_detector = None

        # ---------------------------------------------------------
        # ADR workflow components
        # ---------------------------------------------------------

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

    def _evaluate_significance(
        self,
        decision,
    ):
        """
        Evaluate whether a design decision is significant enough
        to require an ADR.

        The trained TF-IDF + Logistic Regression model is the
        primary classifier.

        If the model is unavailable or inference fails, the
        deterministic rule-based detector is used as a fallback.
        """

        if self.ml_detector is not None:
            try:
                return self.ml_detector.evaluate(
                    decision
                )

            except Exception:
                pass

        return self.rule_detector.evaluate(
            decision
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

        Significance detection uses the trained ML classifier first
        and deterministic rules as a fallback.

        When enabled, LLM-assisted ADR generation is attempted first.
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
                significance = self._evaluate_significance(
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
            #
            # Primary:
            # TF-IDF + Logistic Regression
            #
            # Fallback:
            # deterministic significance rules
            # ---------------------------------------------------------

            significance = self._evaluate_significance(
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