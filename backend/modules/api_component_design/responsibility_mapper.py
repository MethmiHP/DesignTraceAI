#Move architecture mapping and responsibility identification here

from .schemas import (
    APIComponentDesignRequest,
    ArchitectureElement,
    SemanticExtraction,
)


class ResponsibilityMapper:

    def map_to_architecture(
        self,
        semantic: SemanticExtraction,
        request: APIComponentDesignRequest,
    ) -> ArchitectureElement | None:

        resource = (semantic.resource or "").strip().lower()
        action = (semantic.action or "").strip().lower()

        if not resource:
            return None

        best_match = None
        best_score = 0

        for element in request.architecture.elements:

            architecture_text = (
                f"{element.name} "
                f"{element.main_responsibility}"
            ).lower()

            # A shared action such as "manage" does not establish ownership
            # of the resource. Only rank components that mention it.
            if resource not in architecture_text:
                continue

            score = 2

            if action and action in architecture_text:
                score += 1

            if score > best_score:
                best_score = score
                best_match = element

        return best_match

    def generate_detailed_responsibility(
        self,
        semantic: SemanticExtraction,
    ) -> str:

        actor = semantic.actor or "User"
        action = semantic.action or "manage"
        resource = semantic.resource or "resource"

        if (
            action == "book"
            and resource == "Appointment"
        ):
            return (
                "Reserve an available doctor slot and "
                "create an appointment for the "
                "authenticated patient."
            )

        if (
            action == "reschedule"
            and resource == "Appointment"
        ):
            return (
                "Move an eligible appointment to another "
                "available consultation slot."
            )

        if (
            action == "cancel"
            and resource == "Appointment"
        ):
            return (
                "Cancel an eligible appointment according "
                "to the configured cancellation policy."
            )

        return (
            f"Allow {actor} to {action} the {resource}."
        )
