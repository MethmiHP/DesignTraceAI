import logging
import os

from datetime import (
    datetime,
    timezone,
)
from uuid import uuid4

from .deterministic_evaluator import (
    DeterministicEvaluator,
)
from .knowledge_base_validator import (
    QualityKnowledgeBaseValidator,
)
from .llm.provider import (
    BaseQualityLLMProvider,
    build_default_quality_llm_provider,
)
from .metrics_calculator import (
    QualityMetricsCalculator,
)
from .preprocessing import (
    QualityInputPreprocessor,
)
from .recommendation_generator import (
    RecommendationGenerator,
)
from .report_builder import (
    QualityReportBuilder,
)
from .rule_repository import (
    QualityRuleRepository,
)
from .rule_selector import (
    ApplicableRuleSelector,
)
from .schemas import (
    CheckType,
    QualityEvaluationRequest,
    QualityEvaluationResponse,
    QualityFinding,
    RuleStatus,
)
from .semantic_evaluator import (
    SemanticEvaluator,
)
from .severity_classifier import (
    SeverityClassifier,
)


logger = logging.getLogger(__name__)


class QualityEvaluationService:

    def __init__(
        self,
        llm_provider: (
            BaseQualityLLMProvider
            | None
        ) = None,
        enable_llm: bool | None = None,
    ):

        # Normalizes Coordinator input before evaluation
        self.preprocessor = (
            QualityInputPreprocessor()
        )

        # Loads rules from the quality knowledge base
        self.rule_repository = (
            QualityRuleRepository()
        )

        # Validates the quality knowledge base
        self.knowledge_base_validator = (
            QualityKnowledgeBaseValidator()
        )

        # Selects applicable quality rules
        self.rule_selector = (
            ApplicableRuleSelector()
        )

        # Executes deterministic checks
        self.deterministic_evaluator = (
            DeterministicEvaluator()
        )

        # Read LLM configuration from environment
        if enable_llm is None:
            enable_llm = (
                os.environ.get(
                    "QUALITY_EVALUATION_ENABLE_LLM",
                    "false",
                )
                .strip()
                .lower()
                == "true"
            )

        self.llm_enabled = enable_llm

        provider = llm_provider

        # Initialize Gemini and Groq providers
        # when semantic evaluation is enabled
        if (
            self.llm_enabled
            and provider is None
        ):
            try:
                provider = (
                    build_default_quality_llm_provider()
                )

            except Exception:
                logger.exception(
                    (
                        "Quality LLM providers "
                        "could not be initialized."
                    )
                )

                provider = None

        # Executes semantic LLM checks
        self.semantic_evaluator = (
            SemanticEvaluator(
                provider=provider
            )
        )

        # Classifies finding severity
        self.severity_classifier = (
            SeverityClassifier()
        )

        # Generates finding recommendations
        self.recommendation_generator = (
            RecommendationGenerator()
        )

        # Calculates quality metrics
        self.metrics_calculator = (
            QualityMetricsCalculator()
        )

        # Builds the final report summary
        self.report_builder = (
            QualityReportBuilder()
        )

    def evaluate(
        self,
        request: QualityEvaluationRequest,
    ) -> QualityEvaluationResponse:

        # Normalize supplied artifacts
        context = (
            self.preprocessor.normalize(
                request
            )
        )

        # Load all knowledge-base rules
        all_rules = (
            self.rule_repository
            .load_rules()
        )

        # Validate the complete knowledge base
        self.knowledge_base_validator.validate(
            all_rules
        )

        # Select rules that genuinely apply
        # to the current artifacts and NFRs
        applicable_rules = (
            self.rule_selector.select(
                context,
                all_rules,
            )
        )

        results = []

        # Route each rule according
        # to its predefined check type
        for rule in applicable_rules:

            if (
                rule.check_type
                == CheckType.DETERMINISTIC
            ):
                result = (
                    self
                    .deterministic_evaluator
                    .evaluate(
                        rule,
                        context,
                    )
                )

            else:
                result = (
                    self
                    .semantic_evaluator
                    .evaluate(
                        rule,
                        context,
                    )
                )

            results.append(
                result
            )

        findings = []

        finding_number = 1

        # Create rule lookup by ID
        rules_by_id = {
            rule.rule_id: rule
            for rule
            in applicable_rules
        }

        # Convert failed evaluations
        # into quality findings
        for result in results:

            if (
                result.status
                != RuleStatus.FAIL
            ):
                continue

            rule = rules_by_id[
                result.rule_id
            ]

            # Determine finding severity
            severity = (
                self
                .severity_classifier
                .classify(
                    rule,
                    result,
                )
            )

            if severity is None:
                continue

            # Prefer the semantic LLM recommendation
            # when one was returned
            recommendation = (
                self
                .recommendation_generator
                .generate(
                    rule,
                    result,
                    result.recommendation,
                )
            )

            # Use MULTI when the rule
            # evaluates more than one artifact type
            artifact_type = (
                rule.artifact_types[0]
                if len(
                    rule.artifact_types
                ) == 1
                else "MULTI"
            )

            findings.append(
                QualityFinding(
                    finding_id=(
                        f"QF-{finding_number:03d}"
                    ),
                    rule_id=(
                        rule.rule_id
                    ),
                    artifact_type=(
                        artifact_type
                    ),
                    quality_attribute=(
                        rule.quality_attribute
                    ),
                    check_type=(
                        rule.check_type
                    ),
                    severity=(
                        severity
                    ),
                    affected_nfr_ids=(
                        result
                        .affected_nfr_ids
                    ),
                    evidence=(
                        result.evidence
                    ),
                    rationale=(
                        result.rationale
                    ),
                    recommendation=(
                        recommendation
                    ),
                )
            )

            finding_number += 1

        # Calculate Quality Pass,
        # NFR coverage and category summaries
        metrics = (
            self.metrics_calculator
            .calculate(
                context,
                applicable_rules,
                results,
            )
        )

        # Build final summary text
        summary = (
            self.report_builder
            .build_summary(
                metrics,
                findings,
            )
        )

        # Generate evaluation identifier
        evaluation_id = (
            "QE-"
            + uuid4().hex[
                :12
            ].upper()
        )

        # Return complete quality report
        return QualityEvaluationResponse(
            project_id=(
                context.project_id
            ),
            evaluation_id=(
                evaluation_id
            ),
            applicable_rule_ids=[
                rule.rule_id
                for rule
                in applicable_rules
            ],
            rule_results=(
                results
            ),
            findings=(
                findings
            ),
            metrics=(
                metrics
            ),
            summary=(
                summary
            ),
            generated_at=(
                datetime.now(
                    timezone.utc
                )
                .isoformat()
            ),
        )