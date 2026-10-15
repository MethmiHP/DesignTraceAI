# Calculates semantic similarity between requirements and design artifacts
# and generates candidate traceability links.


import numpy as np

from modules.traceability.schemas import (
    TraceabilityRequest,
    CandidateTraceLink,
    NormalizedArtifact,
)

from modules.traceability.normalizer import (
    normalize_requirement_text,
)

from modules.traceability.embedding_service import (
    get_traceability_embedding_service,
)


class TraceabilitySimilarityService:

    def __init__(
        self,
        similarity_threshold: float = 0.40
    ):
        self.similarity_threshold = (
            similarity_threshold
        )

        self.embedding_service = (
            get_traceability_embedding_service()
        )


    def cosine_similarity(
        self,
        vector_a,
        vector_b
    ) -> float:
        
        # Calculates cosine similarity between
        # two embedding vectors.
        

        denominator = (
            np.linalg.norm(vector_a)
            *
            np.linalg.norm(vector_b)
        )

        if denominator == 0:
            return 0.0

        similarity = (
            np.dot(
                vector_a,
                vector_b
            )
            /
            denominator
        )

        return float(similarity)


    def generate_candidate_links(
        self,
        request: TraceabilityRequest,
        artifacts: list[NormalizedArtifact]
    ) -> list[CandidateTraceLink]:
       
        # Compares every requirement with every normalized design artifact.

        #Only links meeting the similarity threshold are returned as candidate trace links.
       

        candidate_links = []

        if not request.requirements:
            return candidate_links

        if not artifacts:
            return candidate_links



        # CREATE ARTIFACT EMBEDDINGS ONCE

        artifact_texts = [
            artifact.normalized_text
            for artifact in artifacts
        ]

        artifact_embeddings = (
            self.embedding_service.encode_texts(
                artifact_texts
            )
        )



        # PROCESS EACH REQUIREMENT

        for requirement in request.requirements:

            requirement_text = (
                normalize_requirement_text(
                    requirement_id=
                        requirement.requirement_id,

                    statement=
                        requirement.statement,

                    requirement_type=
                        requirement.requirement_type,

                    asr=
                        requirement.asr
                )
            )

            requirement_embedding = (
                self.embedding_service.encode_text(
                    requirement_text
                )
            )



            # COMPARE WITH EVERY ARTIFACT

            for artifact, artifact_embedding in zip(
                artifacts,
                artifact_embeddings
            ):

                similarity = (
                    self.cosine_similarity(
                        requirement_embedding,
                        artifact_embedding
                    )
                )



                # THRESHOLD FILTER

                if (
                    similarity
                    >= self.similarity_threshold
                ):

                    candidate_links.append(
                        CandidateTraceLink(

                            requirement_id=
                                requirement.requirement_id,

                            artifact_id=
                                artifact.artifact_id,

                            artifact_type=
                                artifact.artifact_type,

                            semantic_similarity=
                                round(
                                    similarity,
                                    4
                                )
                        )
                    )


        # SORT STRONGEST LINKS FIRST

        candidate_links.sort(
            key=lambda link:
                link.semantic_similarity,
            reverse=True
        )

        return candidate_links