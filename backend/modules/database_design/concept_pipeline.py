"""
DesignTrace AI - Database Concept Pipeline

Supports:
1. Existing rule-based concept extraction
2. Trained RoBERTa concept extraction
"""

from pydantic import BaseModel, Field

from shared.models.project import ProjectInput

from modules.database_design.concept_extractor import (
    ExtractedConcepts,
    extract_project_concepts,
)

from modules.database_design.roberta_concept_extractor import (
    RobertaConceptExtractor,
)


class ConceptPipelineResult(BaseModel):
    project_id: str

    requirement_concepts: list[ExtractedConcepts] = Field(
        default_factory=list
    )

    candidate_entities: list[str] = Field(default_factory=list)
    candidate_attributes: list[str] = Field(default_factory=list)
    candidate_actions: list[str] = Field(default_factory=list)


def run_concept_pipeline(
    project: ProjectInput,
    method: str = "rule_based",
) -> ConceptPipelineResult:
    """
    Extract database concepts using the selected NLP method.
    """

    if method not in {"rule_based", "roberta"}:
        raise ValueError(
            "method must be 'rule_based' or 'roberta'"
        )

    if method == "rule_based":

        extracted = extract_project_concepts(
            project.requirements
        )

    else:

        extractor = RobertaConceptExtractor()

        extracted = []

        for requirement in project.requirements:

            if not requirement.database_relevant:
                continue

            concepts = extractor.extract(
                requirement.requirement_text
            )

            extracted.append(
                ExtractedConcepts(
                    requirement_id=requirement.requirement_id,
                    entities=concepts["entities"],
                    attributes=concepts["attributes"],
                    actions=concepts["actions"],
                )
            )

    entities = set()
    attributes = set()
    actions = set()

    for result in extracted:
        entities.update(result.entities)
        attributes.update(result.attributes)
        actions.update(result.actions)

    return ConceptPipelineResult(
        project_id=project.project_id,
        requirement_concepts=extracted,
        candidate_entities=sorted(entities),
        candidate_attributes=sorted(attributes),
        candidate_actions=sorted(actions),
    )
