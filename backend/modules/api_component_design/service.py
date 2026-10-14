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


class APIComponentDesignService:

    def __init__(self):

       
        # MODULE COMPONENTS


        self.preprocessor = Preprocessor()

        # Selected semantic extraction model:
        # Fine-tuned BERT
        self.semantic_extractor = (
            BertSemanticExtractor()
        )

        # Semantic post-processing / normalization
        self.semantic_normalizer = (
            SemanticNormalizer()
        )

        self.responsibility_mapper = (
            ResponsibilityMapper()
        )

        self.database_context_builder = (
            DatabaseContextBuilder()
        )

        self.api_generator = (
            BaselineAPIGenerator()
        )

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
        responsibilities = []
        operations = []
        mappings = []

        issues: list[
            ValidationIssue
        ] = []


        # 1. PREPROCESSING / INPUT VALIDATION


        (
            request,
            preprocessing_issues,
        ) = self.preprocessor.process(
            request
        )

        issues.extend(
            preprocessing_issues
        )


        # PROCESS EACH FUNCTIONAL REQUIREMENT
    

        for requirement in (
            request.functional_requirements
        ):

          
            # 2. REQUIREMENT UNDERSTANDING
            #
            # Fine-tuned BERT extracts:
            # Actor
            # Action
            # Resource


            raw_semantic = (
                self.semantic_extractor.extract(
                    requirement.requirement_id,
                    requirement.statement,
                )
            )


   
            # 2.1 SEMANTIC NORMALIZATION
            #
            # Examples:
            # cancelled -> cancel
            # rescheduled -> reschedule
            # booked -> book
            #
            # Also supports deterministic passive
            # actor recovery using the original
            # requirement statement.
  

            semantic = (
                self.semantic_normalizer.normalize(
                    raw_semantic,
                    requirement.statement,
                )
            )

            semantic_results.append(
                semantic
            )


   
            # 3. RESPONSIBILITY / ARCHITECTURE MAPPING


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

                # Cannot safely generate an API
                # without an architecture owner.
                continue


         
            # 4. DETAILED RESPONSIBILITY IDENTIFICATION
          

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


       
            # 5. DATABASE CONTEXT INTEGRATION
   

            database_context = (
                self.database_context_builder
                .build(
                    semantic,
                    request,
                )
            )


   
            # 6. API OPERATION GENERATION
          

            operation = (
                self.api_generator.generate(
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
                            "No baseline API rule exists "
                            "for requirement "
                            f"{requirement.requirement_id}."
                        ),
                        severity="WARNING",
                    )
                )



        # 7. BUILD INITIAL OPENAPI DOCUMENT
       

        openapi_document = (
            self.openapi_builder.build(
                operations
            )
        )


      
        # 8. INITIAL API DESIGN VALIDATION
    

        design_validation = (
            self.validator.validate(
                request=request,
                responsibilities=(
                    responsibilities
                ),
                operations=operations,
            )
        )


        # Issues supplied to refinement
        refinement_issues = [
            *issues,
            *design_validation.issues,
        ]


    
        # 9. REFINEMENT
     

        refined_operations = (
            self.refinement_engine.refine(
                operations=operations,
                issues=refinement_issues,
            )
        )


        # Rebuild OpenAPI document
        # using refined operations
        openapi_document = (
            self.openapi_builder.build(
                refined_operations
            )
        )


     
        # 10. FINAL VALIDATION
     

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


        # Keep preprocessing / architecture /
        # API generation issues and final
        # design validation issues
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


        # 11. RETURN FINAL MODULE OUTPUT
    

        return APIComponentDesignResponse(
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