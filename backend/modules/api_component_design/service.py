import logging
import os


from .bert_semantic_extractor import (
    BertSemanticExtractor,
)

from .preprocessing import Preprocessor
from .responsibility_mapper import ResponsibilityMapper
from .database_context import DatabaseContextBuilder
from .api_generator import BaselineAPIGenerator
from .openapi_builder import OpenAPIBuilder
from .validator import APIDesignValidator
from .refinement import RefinementEngine
from .semantic_normalizer import SemanticNormalizer
from .security import apply_security, security_configuration_gaps

from .llm.provider import (
    BaseLLMProvider,
)

from .llm.fallback_provider import FallbackLLMProvider

from .llm.llm_api_generator import (
    LLMAPIGenerator,
)

from .schemas import (
    APIComponentDesignRequest,
    APIComponentDesignResponse,
    ResponsibilityDesign,
    RequirementAPIMapping,
)

from shared.models.common import (
    ValidationResult,
    ValidationIssue,
)
from shared.utils.output_store import save_outputs


logger = logging.getLogger(__name__)


class APIComponentDesignService:

    def __init__(
        self,
        llm_provider: BaseLLMProvider | None = None,
        enable_llm: bool | None = None,
    ):

        # Module components

        self.preprocessor = Preprocessor()

        # Requirement understanding using fine-tuned BERT

        self.semantic_extractor = (
            BertSemanticExtractor()
        )

        # Semantic normalization and passive actor recovery

        self.semantic_normalizer = (
            SemanticNormalizer()
        )

        # Architecture and responsibility mapping

        self.responsibility_mapper = (
            ResponsibilityMapper()
        )

        # Database context integration

        self.database_context_builder = (
            DatabaseContextBuilder()
        )

        # Deterministic baseline generator used for
        # fallback, offline testing and research comparison

        self.baseline_api_generator = (
            BaselineAPIGenerator()
        )

        # LLM API generator

        if enable_llm is None:

            enable_llm = (
                os.environ.get(
                    "API_COMPONENT_ENABLE_LLM",
                    "false",
                ).lower()
                == "true"
            )

        self.llm_enabled = enable_llm

        self.llm_api_generator = None

        if self.llm_enabled:

            provider = (
                llm_provider
                if llm_provider is not None
                else FallbackLLMProvider()
            )

            self.llm_api_generator = (
                LLMAPIGenerator(
                    llm_provider=provider
                )
            )

        # OpenAPI, validation and refinement

        self.openapi_builder = (
            OpenAPIBuilder()
        )

        self.validator = (
            APIDesignValidator()
        )

        self.refinement_engine = (
            RefinementEngine()
        )


    async def design(
        self,
        request: APIComponentDesignRequest,
    ) -> APIComponentDesignResponse:

        semantic_results = []
        raw_semantic_results = []
        database_context_results = []
        responsibilities = []
        operations = []
        mappings = []

        issues: list[
            ValidationIssue
        ] = []

        # 1. Preprocessing and input validation

        (
            request,
            preprocessing_issues,
        ) = self.preprocessor.process(
            request
        )

        issues.extend(
            preprocessing_issues
        )

        security_gaps = security_configuration_gaps(request)
        if security_gaps:
            response = APIComponentDesignResponse(
                project_id=request.project_id,
                semantic_extractions=[], responsibilities=[], api_operations=[],
                requirement_to_api_mapping=[],
                validation=ValidationResult(valid=False, issues=[*issues, *security_gaps]),
            )
            save_outputs(request.project_id, {
                'request': request.model_dump(mode='json'),
                'response': response.model_dump(mode='json'),
            })
            return response

        # Process each functional requirement

        for requirement in (
            request.functional_requirements
        ):

            # 2. Requirement understanding using BERT

            raw_semantic = (
                self.semantic_extractor.extract(
                    requirement.requirement_id,
                    requirement.statement,
                )
            )
            raw_semantic_results.append(raw_semantic.model_dump(mode="json"))

            # 2.1 Semantic normalization

            semantic = (
                self.semantic_normalizer.normalize(
                    raw_semantic,
                    requirement.statement,
                )
            )

            semantic_results.append(
                semantic
            )

            # 3. Architecture mapping

            architecture_element = (
                self.responsibility_mapper
                .map_to_architecture(
                    semantic,
                    request,
                )
            )

            if architecture_element is None:

                issues.append(
                    ValidationIssue(
                        code=(
                            "ARCHITECTURE_MAPPING_FAILED"
                        ),
                        message=(
                            "Could not map requirement "
                            f"{requirement.requirement_id} "
                            "to an architecture element."
                        ),
                        severity="ERROR",
                    )
                )

                # API generation requires an architecture owner

                continue

            # 4. Detailed responsibility identification

            detailed_responsibility = (
                self.responsibility_mapper
                .generate_detailed_responsibility(
                    semantic
                )
            )

            responsibility = (
                ResponsibilityDesign(
                    requirement_id=(
                        requirement.requirement_id
                    ),
                    element_id=(
                        architecture_element.element_id
                    ),
                    element_name=(
                        architecture_element.name
                    ),
                    detailed_responsibility=(
                        detailed_responsibility
                    ),
                    mapping_reason=(
                        "Mapped using requirement "
                        "resource/action and architecture "
                        "responsibility."
                    ),
                )
            )

            responsibilities.append(
                responsibility
            )

            # 5. Database context integration

            database_context = (
                self.database_context_builder
                .build(
                    semantic,
                    request,
                )
            )
            database_context_results.append({
                "requirement_id": requirement.requirement_id,
                "entities": [entity.model_dump(mode="json") for entity in database_context],
            })

            # 6. API operation generation

            operation = None
            security_policy = requirement.security or request.security

            # 6.1 Try context-grounded LLM generation

            if (
                self.llm_enabled
                and self.llm_api_generator
                is not None
            ):

                try:

                    operation = (
                        self.llm_api_generator
                        .generate(
                            requirement_statement=(
                                requirement.statement
                            ),
                            security_policy=security_policy,
                            semantic=semantic,
                            architecture_element=(
                                architecture_element
                            ),
                            database_context=(
                                database_context
                            ),
                        )
                    )

                except Exception:

                    logger.warning(
                        "[API %s] LLM failed; using rule-based fallback",
                        requirement.requirement_id,
                    )

                    issues.append(
                        ValidationIssue(
                            code=(
                                "LLM_API_GENERATION_FAILED"
                            ),
                            message=(
                                "LLM API generation failed "
                                "for requirement "
                                f"{requirement.requirement_id}. "
                                "The deterministic baseline "
                                "generator was used as a "
                                "fallback."
                            ),
                            severity="WARNING",
                        )
                    )

            # 6.2 Use deterministic baseline as fallback

            if operation is None:

                operation = (
                    self.baseline_api_generator
                    .generate(
                        semantic=semantic,
                        element_id=(
                            architecture_element.element_id
                        ),
                        database_context=(
                            database_context
                        ),
                    )
                )

                if operation is not None:
                    operation.generation_source = "rule-based"

            if operation is not None:
                apply_security(operation, security_policy)

            # 6.3 Store generated operation

            if operation is not None:

                operations.append(
                    operation
                )

                mappings.append(
                    RequirementAPIMapping(
                        requirement_id=(
                            requirement.requirement_id
                        ),
                        operation_id=(
                            operation.operation_id
                        ),
                    )
                )

            else:

                issues.append(
                    ValidationIssue(
                        code=(
                            "API_GENERATION_FAILED"
                        ),
                        message=(
                            "Could not generate an API "
                            "operation for requirement "
                            f"{requirement.requirement_id}."
                        ),
                        severity="WARNING",
                    )
                )

        # 7. Build initial OpenAPI document

        openapi_document = (
            self.openapi_builder.build(
                operations
            )
        )

        # 8. Initial API design validation

        design_validation = (
            self.validator.validate(
                request=request,
                responsibilities=(
                    responsibilities
                ),
                operations=operations,
            )
        )

        # Combine generation and validation issues
        # before refinement

        refinement_issues = [
            *issues,
            *design_validation.issues,
        ]

        # Snapshot before refinement, which can mutate the operation models.
        initial_operations = [operation.model_dump(mode="json") for operation in operations]
        initial_openapi_document = openapi_document

        # 9. Deterministic refinement

        refined_operations = (
            self.refinement_engine.refine(
                operations=operations,
                issues=refinement_issues,
            )
        )

        # Rebuild OpenAPI from refined operations

        openapi_document = (
            self.openapi_builder.build(
                refined_operations
            )
        )

        # 10. Final validation

        final_design_validation = (
            self.validator.validate(
                request=request,
                responsibilities=(
                    responsibilities
                ),
                operations=(
                    refined_operations
                ),
            )
        )

        # Keep preprocessing, generation and
        # final validation issues

        final_issues = [
            *issues,
            *final_design_validation.issues,
        ]

        has_errors = any(
            issue.severity == "ERROR"
            for issue in final_issues
        )

        final_validation = (
            ValidationResult(
                valid=not has_errors,
                issues=final_issues,
            )
        )

        # 11. Return final module output

        response = APIComponentDesignResponse(
            project_id=request.project_id,
            semantic_extractions=(
                semantic_results
            ),
            responsibilities=(
                responsibilities
            ),
            api_operations=(
                refined_operations
            ),
            requirement_to_api_mapping=(
                mappings
            ),
            openapi_document=(
                openapi_document
            ),
            validation=(
                final_validation
            ),
        )

        response_data = response.model_dump(mode="json")
        output_path = save_outputs(request.project_id, {
            "request": request.model_dump(mode="json"),
            "raw_semantic_extractions": raw_semantic_results,
            "database_context": database_context_results,
            "preprocessing_issues": [issue.model_dump(mode="json") for issue in preprocessing_issues],
            "initial_api_operations": initial_operations,
            "initial_openapi_document": initial_openapi_document,
            "initial_validation": design_validation.model_dump(mode="json"),
            "refinement_issues": [issue.model_dump(mode="json") for issue in refinement_issues],
            **{name: value for name, value in response_data.items() if name != "project_id"},
            "response": response_data,
        })
        logger.info("Saved API design outputs to %s", output_path)
        return response
