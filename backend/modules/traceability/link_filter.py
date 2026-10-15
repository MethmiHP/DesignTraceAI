# Applies deterministic filtering rules to Gemini-validated
# traceability links before final matrix generation.

from modules.traceability.schemas import (
    TraceLink,
    NormalizedArtifact,
)


class TraceLinkFilter:

    def __init__(
        self,
        minimum_confidence: float = 0.70,
    ):
        self.minimum_confidence = (
            minimum_confidence
        )

    def filter_links(
        self,
        links: list[TraceLink],
        artifacts: list[NormalizedArtifact],
    ) -> list[TraceLink]:
        
        # Keeps only valid, well-formed, sufficiently confident trace links.
     

        valid_artifact_ids = {
            artifact.artifact_id
            for artifact in artifacts
        }

        filtered_links = []

        seen_links = set()

        for link in links:


            # 1. REJECT INVALID ARTIFACT IDS

            if (
                link.artifact_id
                not in valid_artifact_ids
            ):
                continue


            # 2. KEEP ONLY GEMINI-VALIDATED LINKS

            if not link.link_valid:
                continue


            # 3. CONFIDENCE FILTER

            if (
                link.confidence
                < self.minimum_confidence
            ):
                continue


            # 4. REQUIRE A RATIONALE

            if not link.rationale.strip():
                continue


            # 5. REMOVE DUPLICATES

            link_key = (
                link.requirement_id,
                link.artifact_id,
            )

            if link_key in seen_links:
                continue

            seen_links.add(
                link_key
            )

            filtered_links.append(
                link
            )


        # SORT OUTPUT FOR CONSISTENCY

        filtered_links.sort(
            key=lambda link: (
                link.requirement_id,
                link.artifact_type,
                link.artifact_id,
            )
        )

        return filtered_links