#This finds relevant database information for the requirement.

from .schemas import (
    APIComponentDesignRequest,
    DatabaseEntity,
    SemanticExtraction,
)


class DatabaseContextBuilder:

    def build(
        self,
        semantic: SemanticExtraction,
        request: APIComponentDesignRequest,
    ) -> list[DatabaseEntity]:

        relevant_entities: list[DatabaseEntity] = []

        resource = (
            semantic.resource or ""
        ).lower().replace(" ", "")

        actor = (
            semantic.actor or ""
        ).lower().replace(" ", "")

        # Find the main resource entity
        for entity in request.database.entities:

            entity_name = (
                entity.name
                .lower()
                .replace(" ", "")
            )

            if (
                resource
                and (
                    resource == entity_name
                    or resource in entity_name
                    or entity_name in resource
                )
            ):
                relevant_entities.append(entity)

        # Add actor-related entity when useful
        for entity in request.database.entities:

            entity_name = (
                entity.name
                .lower()
                .replace(" ", "")
            )

            if actor and actor == entity_name:

                if entity not in relevant_entities:
                    relevant_entities.append(entity)

        # Find entities referenced through foreign keys
        for entity in list(relevant_entities):

            for foreign_key in entity.foreign_keys:

                # Example:
                # doctor_id -> doctor
                possible_name = (
                    foreign_key
                    .lower()
                    .split("->")[0]
                    .strip()
                    .replace("_id", "")
                )

                for candidate in request.database.entities:

                    candidate_name = (
                        candidate.name
                        .lower()
                        .replace(" ", "")
                    )

                    if possible_name == candidate_name:

                        if candidate not in relevant_entities:
                            relevant_entities.append(candidate)

        return relevant_entities