# Coordinates the complete Requirement Analysis workflow.
#
# Pipeline:
# 1. Preprocess raw project description
# 2. Run deterministic requirement-quality rules
# 3. Ask LLM to extract and analyse atomic requirements
# 4. Use fine-tuned RoBERTa models for:
#       - FR/NFR classification
#       - NFR quality-attribute classification
# 5. Merge deterministic + LLM quality analysis
# 6. Assign deterministic requirement IDs
# 7. Generate summary and SRS
# 8. Validate final structured output


from modules.requirement_analysis.schemas import (
    RequirementAnalysisRequest,
    RequirementAnalysisResponse,
    AnalyzedRequirement,
    RequirementQualityIssues,
    IssueDetail,
    RequirementSummary,
    RequirementValidationResult,
)

from modules.requirement_analysis.nlp import (
    preprocess_text
)

from modules.requirement_analysis.rules import (
    run_quality_rules
)

from modules.requirement_analysis.prompt import (
    build_requirement_analysis_prompt
)

from modules.requirement_analysis.classifier_service import (
    get_requirement_classifier
)

from shared.llm.factory import (
    get_llm_provider
)


# REQUIREMENT ANALYSIS SERVICE

class RequirementAnalysisService:

    def __init__(self, llm=None, classifier=None):

        self.llm = llm or get_llm_provider()

        self.classifier = (
            classifier or get_requirement_classifier()
        )


  
    # MAIN ANALYSIS PIPELINE

    async def analyze(
        self,
        request: RequirementAnalysisRequest
    ) -> RequirementAnalysisResponse:

        
        # STEP 1 - PREPROCESS RAW TEXT

        preprocessing = preprocess_text(
            request.raw_description
        )

        cleaned_text = preprocessing[
            "cleaned_text"
        ]

        sentences = preprocessing[
            "sentences"
        ]


        # STEP 2 - RUN DETERMINISTIC QUALITY RULES

        sentence_rule_results = []

        for sentence in sentences:

            result = run_quality_rules(
                sentence
            )

            sentence_rule_results.append({
                "sentence": sentence,
                "result": result
            })


        
        # STEP 3 - BUILD LLM PROMPT

        prompt = build_requirement_analysis_prompt(
            raw_description=cleaned_text,

            project_context=(
                request
                .project_context
                .model_dump()
            ),

            rule_findings={
                "sentence_results":
                    sentence_rule_results
            }
        )


     
        # STEP 4 - ASK LLM FOR STRUCTURED ANALYSIS

        llm_result = (
            await self.llm.generate_structured(

                prompt=prompt,

                response_schema={
                    "type": "object",

                    "properties": {

                        "requirements": {
                            "type": "array",

                            "items": {
                                "type": "object",

                                "properties": {

                                    "original_text": {
                                        "type": "string"
                                    },

                                    "normalized_statement": {
                                        "type": "string"
                                    },

                                    "requirement_type": {
                                        "type": "string"
                                    },

                                    "quality_attribute": {
                                        "type": "string"
                                    },

                                    "asr": {
                                        "type": "boolean"
                                    },

                                    "quality_issues": {
                                        "type": "object",

                                        "properties": {

                                            "ambiguous": {
                                                "type": "boolean"
                                            },

                                            "incomplete": {
                                                "type": "boolean"
                                            },

                                            "conflicting": {
                                                "type": "boolean"
                                            },

                                            "potentially_missing": {
                                                "type": "boolean"
                                            }
                                        },

                                        "required": [
                                            "ambiguous",
                                            "incomplete",
                                            "conflicting",
                                            "potentially_missing"
                                        ]
                                    },

                                    "issue_details": {
                                        "type": "array",

                                        "items": {
                                            "type": "object",

                                            "properties": {

                                                "issue_type": {
                                                    "type": "string"
                                                },

                                                "evidence": {
                                                    "type": "string"
                                                },

                                                "rationale": {
                                                    "type": "string"
                                                },

                                                "recommendation": {
                                                    "type": "string"
                                                }
                                            }
                                        }
                                    }
                                },

                                "required": [
                                    "original_text",
                                    "normalized_statement",
                                    "asr",
                                    "quality_issues",
                                    "issue_details"
                                ]
                            }
                        }
                    },

                    "required": [
                        "requirements"
                    ]
                },

                temperature=0.0
            )
        )

        raw_requirements = (
            llm_result.get(
                "requirements",
                []
            )
        )


        
        # STEP 5 - PROCESS EACH EXTRACTED REQUIREMENT

        requirements = []

        for index, item in enumerate(
            raw_requirements,
            start=1
        ):

            # Deterministic requirement ID

            requirement_id = (
                f"REQ-{index:03d}"
            )


            # Requirement text

            original_text = item.get(
                "original_text",
                item.get(
                    "normalized_statement",
                    ""
                )
            )

            normalized_statement = (
                item.get(
                    "normalized_statement",
                    original_text
                )
            )

            if not normalized_statement:

                normalized_statement = (
                    original_text
                )


            # STEP 5A - FINE-TUNED MODEL CLASSIFICATION

            # classification = (
            #     self.classifier.classify(
            #         normalized_statement
            #     )
            # )

            classification = (
                 self.classifier.classify(
                    original_text
                )
            )

            requirement_type = (
                classification[
                    "requirement_type"
                ]
            )

            type_confidence = (
                classification[
                    "type_confidence"
                ]
            )

            quality_attribute = (
                classification[
                    "quality_attribute"
                ]
            )

            quality_confidence = (
                classification[
                    "quality_confidence"
                ]
            )


            # STEP 5B - CLASSIFICATION CONFIDENCE

            if (
                requirement_type == "NFR"
                and
                quality_confidence is not None
            ):

                classification_confidence = min(
                    type_confidence,
                    quality_confidence
                )

            else:

                classification_confidence = (
                    type_confidence
                )


       
            # STEP 5C - LLM QUALITY ANALYSIS
            quality_data = item.get(
                "quality_issues",
                {}
            )


            # STEP 5D - DETERMINISTIC QUALITY ANALYSIS
            deterministic_quality = run_quality_rules(
                original_text
            )


        
            # STEP 5E - PRESERVE ORIGINAL SOURCE RULE RESULTS

            source_rule_quality = {}

            # If the raw input had only one sentence,
            # it corresponds to this extracted requirement.
            if len(sentence_rule_results) == 1:

                source_rule_quality = (
                    sentence_rule_results[0][
                        "result"
                    ]
                )

            else:

                candidate_text = (
                    original_text
                    .strip()
                    .lower()
                )

                for sentence_result in (
                    sentence_rule_results
                ):

                    source_sentence = (
                        sentence_result[
                            "sentence"
                        ]
                        .strip()
                        .lower()
                    )

                    if (
                        candidate_text
                        in source_sentence
                        or
                        source_sentence
                        in candidate_text
                    ):

                        source_rule_quality = (
                            sentence_result[
                                "result"
                            ]
                        )

                        break


  
            # STEP 5F - MERGE QUALITY RESULTS

            final_ambiguous = (
                quality_data.get(
                    "ambiguous",
                    False
                )
                or
                deterministic_quality.get(
                    "ambiguous",
                    False
                )
                or
                source_rule_quality.get(
                    "ambiguous",
                    False
                )
            )


            final_incomplete = (
                quality_data.get(
                    "incomplete",
                    False
                )
                or
                deterministic_quality.get(
                    "incomplete",
                    False
                )
                or
                source_rule_quality.get(
                    "incomplete",
                    False
                )
            )


            final_conflicting = (
                quality_data.get(
                    "conflicting",
                    False
                )
            )


            final_potentially_missing = (
                quality_data.get(
                    "potentially_missing",
                    False
                )
            )

            # STEP 5G - ISSUE DETAILS

            issue_details = []

            for issue in item.get(
                "issue_details",
                []
            ):

                try:

                    issue_details.append(
                        IssueDetail(

                            issue_type=issue.get(
                                "issue_type"
                            ),

                            evidence=issue.get(
                                "evidence"
                            ),

                            rationale=issue.get(
                                "rationale",
                                "No rationale provided."
                            ),

                            recommendation=issue.get(
                                "recommendation"
                            )
                        )
                    )

                except Exception:

                    continue


            # STEP 5H - CREATE FINAL REQUIREMENT

            requirement = (
                AnalyzedRequirement(

                    requirement_id=
                        requirement_id,

                    original_text=
                        original_text,

                    normalized_statement=
                        normalized_statement,


                    # These come from trained RoBERTa models

                    requirement_type=
                        requirement_type,

                    quality_attribute=
                        quality_attribute,


                    # ASR comes from Gemini

                    asr=item.get(
                        "asr",
                        False
                    ),


                    # Final quality result combines:
                    # LLM + deterministic rules +
                    # original source rule findings

                    quality_issues=(
                        RequirementQualityIssues(

                            ambiguous=
                                final_ambiguous,

                            incomplete=
                                final_incomplete,

                            conflicting=
                                final_conflicting,

                            potentially_missing=
                                final_potentially_missing,
                        )
                    ),

                    issue_details=
                        issue_details,

                    confidence=float(
                        classification_confidence
                    )
                )
            )

            requirements.append(
                requirement
            )


  
        # STEP 6 - CREATE SUMMARY

        summary = self._create_summary(
            requirements
        )


        # STEP 7 - GENERATE SRS
        generated_srs = (
            self._generate_srs(

                project_id=
                    request.project_id,

                requirements=
                    requirements
            )
        )


        # STEP 8 - VALIDATE FINAL OUTPUT

        validation = (
            self._validate_requirements(
                requirements
            )
        )



        # FINAL RESPONSE

        return RequirementAnalysisResponse(

            project_id=
                request.project_id,

            requirements=
                requirements,

            summary=
                summary,

            generated_srs=
                generated_srs,

            validation=
                validation
        )



    # SUMMARY

    def _create_summary(
        self,
        requirements: list[
            AnalyzedRequirement
        ]
    ) -> RequirementSummary:

        return RequirementSummary(

            total_requirements=
                len(
                    requirements
                ),

            functional_requirements=
                sum(
                    1
                    for r in requirements
                    if (
                        r.requirement_type
                        == "FR"
                    )
                ),

            non_functional_requirements=
                sum(
                    1
                    for r in requirements
                    if (
                        r.requirement_type
                        == "NFR"
                    )
                ),

            asr_count=
                sum(
                    1
                    for r in requirements
                    if r.asr
                ),

            ambiguous_count=
                sum(
                    1
                    for r in requirements
                    if (
                        r
                        .quality_issues
                        .ambiguous
                    )
                ),

            incomplete_count=
                sum(
                    1
                    for r in requirements
                    if (
                        r
                        .quality_issues
                        .incomplete
                    )
                ),

            conflict_count=
                sum(
                    1
                    for r in requirements
                    if (
                        r
                        .quality_issues
                        .conflicting
                    )
                ),

            potentially_missing_count=
                sum(
                    1
                    for r in requirements
                    if (
                        r
                        .quality_issues
                        .potentially_missing
                    )
                )
        )


    # VALIDATION

    def _validate_requirements(
        self,
        requirements: list[
            AnalyzedRequirement
        ]
    ) -> RequirementValidationResult:

        issues = []


        if not requirements:

            issues.append(
                "No requirements were extracted."
            )


        ids = [
            requirement.requirement_id
            for requirement in requirements
        ]

        if len(ids) != len(set(ids)):

            issues.append(
                "Duplicate requirement IDs detected."
            )


        for requirement in requirements:

            if not (
                requirement
                .normalized_statement
            ):

                issues.append(
                    f"{requirement.requirement_id}: "
                    "normalized statement is empty."
                )


            if (
                requirement.requirement_type
                == "NFR"
                and
                not requirement.quality_attribute
            ):

                issues.append(
                    f"{requirement.requirement_id}: "
                    "NFR has no quality attribute."
                )


        return RequirementValidationResult(

            valid=
                len(issues) == 0,

            issues=
                issues
        )


    # SRS GENERATION

    def _generate_srs(
        self,
        project_id: str,
        requirements: list[
            AnalyzedRequirement
        ]
    ) -> str:

        functional = [
            requirement
            for requirement in requirements
            if (
                requirement.requirement_type
                == "FR"
            )
        ]

        non_functional = [
            requirement
            for requirement in requirements
            if (
                requirement.requirement_type
                == "NFR"
            )
        ]

        asrs = [
            requirement
            for requirement in requirements
            if requirement.asr
        ]


        lines = []


        lines.append(
            f"SOFTWARE REQUIREMENTS "
            f"SPECIFICATION - "
            f"{project_id}"
        )


    
        # FUNCTIONAL REQUIREMENTS

        lines.append("")

        lines.append(
            "1. FUNCTIONAL REQUIREMENTS"
        )

        for requirement in functional:

            lines.append(
                f"{requirement.requirement_id}: "
                f"{requirement.normalized_statement}"
            )


        # NON-FUNCTIONAL REQUIREMENTS

        lines.append("")

        lines.append(
            "2. NON-FUNCTIONAL REQUIREMENTS"
        )

        for requirement in non_functional:

            lines.append(
                f"{requirement.requirement_id}: "
                f"{requirement.normalized_statement} "
                f"[{requirement.quality_attribute}]"
            )



        # ARCHITECTURALLY SIGNIFICANT REQUIREMENTS

        lines.append("")

        lines.append(
            "3. ARCHITECTURALLY "
            "SIGNIFICANT REQUIREMENTS"
        )

        for requirement in asrs:

            lines.append(
                f"{requirement.requirement_id}: "
                f"{requirement.normalized_statement}"
            )


        return "\n".join(
            lines
        )