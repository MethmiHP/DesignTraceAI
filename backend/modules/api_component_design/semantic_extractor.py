from abc import ABC, abstractmethod

from .schemas import SemanticExtraction



# BASE INTERFACE

class BaseSemanticExtractor(ABC):
    """
    Common interface for all semantic extraction approaches.

    Future implementations can include:
    - RuleBasedSemanticExtractor
    - SpacySemanticExtractor
    - BertSemanticExtractor
    - RobertaSemanticExtractor
    """

    @abstractmethod
    def extract(
        self,
        requirement_id: str,
        statement: str,
    ) -> SemanticExtraction:
        pass



# RULE-BASED BASELINE


class RuleBasedSemanticExtractor(BaseSemanticExtractor):
    """
    Simple deterministic baseline.

    This is NOT the final NLP solution.
    It will later be compared with spaCy, BERT,
    RoBERTa, DeBERTa, etc.
    """

    def extract(
        self,
        requirement_id: str,
        statement: str,
    ) -> SemanticExtraction:

        text = statement.lower().strip()

        actor = self._extract_actor(text)
        action = self._extract_action(text)
        resource = self._extract_resource(text)

        return SemanticExtraction(
            requirement_id=requirement_id,
            actor=actor,
            action=action,
            resource=resource,
            confidence=None,
        )

    
    # ACTOR EXTRACTION
   

    def _extract_actor(
        self,
        text: str,
    ) -> str | None:

        actor_terms = {
            "patient": "Patient",
            "doctor": "Doctor",
            "administrator": "Administrator",
            "admin": "Administrator",
            "system": "System",
        }

        for keyword, actor in actor_terms.items():

            if keyword in text:
                return actor

        return None

    # ACTION EXTRACTION


    def _extract_action(
        self,
        text: str,
    ) -> str | None:

        action_keywords = [
            "book",
            "reschedule",
            "cancel",
            "search",
            "create",
            "update",
            "pay",
            "review",
            "notify",
            "confirm",
        ]

        for action in action_keywords:

            if action in text:
                return action

        return None

   
    # RESOURCE EXTRACTION
  

    def _extract_resource(
        self,
        text: str,
    ) -> str | None:

        resource_terms = {
            "appointment": "Appointment",
            "prescription": "Prescription",
            "payment": "Payment",
            "notification": "Notification",
            "audit": "Audit Event",
        }

        for keyword, resource in resource_terms.items():

            if keyword in text:
                return resource

        # Special case:
        # "search doctor" should identify Doctor
        # as the resource.
        if (
            "doctor" in text
            and "search" in text
        ):
            return "Doctor"

        return None