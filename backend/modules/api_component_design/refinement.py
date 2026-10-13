from .schemas import APIOperation
from shared.models.common import ValidationIssue


class RefinementEngine:

    def refine(
        self,
        operations: list[APIOperation],
        issues: list[ValidationIssue],
    ) -> list[APIOperation]:

    
        return operations