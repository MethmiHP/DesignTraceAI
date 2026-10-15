# Normalizes requirements and design artifacts into a common
# text representation for semantic similarity comparison.

import re

from modules.traceability.schemas import (
    TraceabilityRequest,
    NormalizedArtifact,
)


def normalize_text(text: str) -> str:
    
    # Basic deterministic text normalization.
    

    if not text:
        return ""

    text = text.strip().lower()

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text


def normalize_requirement_text(
    requirement_id: str,
    statement: str,
    requirement_type: str,
    asr: bool,
) -> str:
    
    # Creates the semantic text used for requirement embeddings.

    # Requirement IDs, FR/NFR type, and ASR status are kept as
    # metadata and are not included in the SBERT embedding text.
    

    return normalize_text(
        statement
    )

def normalize_artifacts(
    request: TraceabilityRequest
) -> list[NormalizedArtifact]:
    
    # Converts architecture, database, API, and component
    # artifacts into one common normalized structure.
    

    artifacts = []


    # ARCHITECTURE

    for artifact in request.architecture.elements:

        normalized_text = normalize_text(
            f"{artifact.name}. "
            f"{artifact.type}. "
            f"{artifact.description}"
        )

        artifacts.append(
            NormalizedArtifact(
                artifact_id=artifact.artifact_id,
                artifact_type="architecture",
                name=artifact.name,
                description=artifact.description,
                normalized_text=normalized_text
            )
        )



    # DATABASE

    for artifact in request.database.entities:

        normalized_text = normalize_text(
            f"{artifact.name}. "
            f"Database entity. "
            f"{artifact.description}"
        )

        artifacts.append(
            NormalizedArtifact(
                artifact_id=artifact.artifact_id,
                artifact_type="database",
                name=artifact.name,
                description=artifact.description,
                normalized_text=normalized_text
            )
        )


    # API

    for artifact in request.api.operations:

        api_name = (
            f"{artifact.method} "
            f"{artifact.path}"
        )

        normalized_text = normalize_text(
            f"{api_name}. "
            f"API operation. "
            f"{artifact.description}"
        )

        artifacts.append(
            NormalizedArtifact(
                artifact_id=artifact.artifact_id,
                artifact_type="api",
                name=api_name,
                description=artifact.description,
                normalized_text=normalized_text
            )
        )


    # COMPONENTS

    for artifact in request.components:

        normalized_text = normalize_text(
            f"{artifact.name}. "
            f"Software component. "
            f"{artifact.description}"
        )

        artifacts.append(
            NormalizedArtifact(
                artifact_id=artifact.artifact_id,
                artifact_type="component",
                name=artifact.name,
                description=artifact.description,
                normalized_text=normalized_text
            )
        )

    return artifacts