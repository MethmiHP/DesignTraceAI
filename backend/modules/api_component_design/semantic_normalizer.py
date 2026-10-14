import re

from .schemas import SemanticExtraction


class SemanticNormalizer:

    ACTION_NORMALIZATION = {
        # Appointment-related
        "booked": "book",
        "booking": "book",

        "cancelled": "cancel",
        "canceled": "cancel",
        "cancelling": "cancel",
        "canceling": "cancel",

        "rescheduled": "reschedule",
        "rescheduling": "reschedule",

        # Common CRUD / business actions
        "created": "create",
        "creating": "create",

        "updated": "update",
        "updating": "update",

        "deleted": "delete",
        "deleting": "delete",

        "managed": "manage",
        "managing": "manage",

        "approved": "approve",
        "approving": "approve",

        "rejected": "reject",
        "rejecting": "reject",

        "confirmed": "confirm",
        "confirming": "confirm",

        "notified": "notify",
        "notifying": "notify",

        "scheduled": "schedule",
        "scheduling": "schedule",

        "assigned": "assign",
        "assigning": "assign",

        "generated": "generate",
        "generating": "generate",

        "submitted": "submit",
        "submitting": "submit",

        "uploaded": "upload",
        "uploading": "upload",

        "downloaded": "download",
        "downloading": "download",

        "issued": "issue",
        "issuing": "issue",

        "processed": "process",
        "processing": "process",

        "viewed": "view",
        "viewing": "view",

        "retrieved": "retrieve",
        "retrieving": "retrieve",
    }


    
    # ACTION NORMALIZATION
  

    def _normalize_action(
        self,
        action: str | None,
    ) -> str | None:

        if not action:
            return None

        action_lower = action.lower()

        return self.ACTION_NORMALIZATION.get(
            action_lower,
            action_lower,
        )



    # PASSIVE ACTOR RECOVERY
    #
    # Example:
    #
    # "An appointment shall be cancelled by a patient."
    #
    # BERT:
    # actor = None
    #
    # Recovery:
    # actor = Patient


    def _recover_passive_actor(
        self,
        statement: str,
    ) -> str | None:

        if not statement:
            return None


        # Look for a phrase at the end of the sentence
        # beginning with "by".
        #
        # Examples:
        # by a patient
        # by the doctor
        # by an administrator
        # by a warehouse manager

        match = re.search(
            r"\bby\s+"
            r"(?:(?:a|an|the)\s+)?"
            r"([A-Za-z][A-Za-z'-]*"
            r"(?:\s+[A-Za-z][A-Za-z'-]*){0,3})"
            r"\s*[.!?]?$",
            statement,
            flags=re.IGNORECASE,
        )


        if not match:
            return None


        actor = match.group(1).strip()

        if not actor:
            return None


        return actor.title()



    # PUBLIC NORMALIZATION METHOD


    def normalize(
        self,
        semantic: SemanticExtraction,
        statement: str | None = None,
    ) -> SemanticExtraction:


        # Normalize action
     

        normalized_action = (
            self._normalize_action(
                semantic.action
            )
        )


     
        # Keep BERT actor if available.
        #
        # Only attempt deterministic passive recovery when
        # BERT did not detect an actor.
  

        actor = semantic.actor

        if (
            actor is None
            and statement
        ):

            recovered_actor = (
                self._recover_passive_actor(
                    statement
                )
            )

            if recovered_actor:

                actor = recovered_actor


        # Return normalized semantic result


        return SemanticExtraction(
            requirement_id=(
                semantic.requirement_id
            ),
            actor=actor,
            action=normalized_action,
            resource=semantic.resource,
            confidence=semantic.confidence,
        )