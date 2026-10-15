import json
from pathlib import Path

from .schemas import QualityRule


class QualityRuleRepository:

    def __init__(
        self,
        rule_file: Path | None = None,
    ):
        if rule_file is None:
            rule_file = (
                Path(__file__).parent
                / "knowledge_base"
                / "quality_rules.json"
            )

        self.rule_file = rule_file

    def load_rules(
        self,
    ) -> list[QualityRule]:

        with self.rule_file.open(
            "r",
            encoding="utf-8",
        ) as file:
            raw_rules = json.load(file)

        return [
            QualityRule.model_validate(rule)
            for rule in raw_rules
        ]