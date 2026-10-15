from __future__ import annotations

from pathlib import Path

import torch
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
)

from modules.architecture_design.quality_classifier import BaseClassifier
from modules.architecture_design.schemas import (
    QualityAttribute,
    QualityHit,
)


LABEL_LIST = [
    "Security",
    "Scalability",
    "Performance",
    "Reliability",
    "Maintainability",
    "Availability",
]


class SupervisedTransformerQualityClassifier(BaseClassifier):
    """
    Fine-tuned RoBERTa classifier for multi-label Quality Attribute
    classification.

    Input:
        Requirement statement as plain text.

    Output:
        List of QualityHit objects.

    This intentionally follows the same BaseClassifier interface used by
    KeywordClassifier and SemanticQualityClassifier so it can be injected
    into ArchitectureDesignService without changing the service pipeline.

    Confidence values are sigmoid probabilities produced by the fine-tuned
    RoBERTa classification head.

    The current operating threshold is 0.50.

    Milestone 7.2 identified 0.80 as validation-optimal, but that threshold
    did not improve held-out test performance. Therefore 0.50 is retained
    provisionally pending stronger validation.
    """

    def __init__(
        self,
        model_path: str | Path,
        threshold: float = 0.50,
        max_length: int = 128,
    ) -> None:

        self.model_path = Path(model_path)

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Fine-tuned RoBERTa model not found: "
                f"{self.model_path}"
            )

        self.threshold = threshold
        self.max_length = max_length

        self.device = torch.device(
            "cuda"
            if torch.cuda.is_available()
            else "cpu"
        )

        self.tokenizer = AutoTokenizer.from_pretrained(
            str(self.model_path),
            local_files_only=True,
        )

        self.model = (
            AutoModelForSequenceClassification.from_pretrained(
                str(self.model_path),
                local_files_only=True,
            )
        )

        self.model.to(self.device)
        self.model.eval()

        self.model_name = "fine-tuned-roberta-base"

    def classify(
        self,
        text: str,
    ) -> list[QualityHit]:
        """
        Classify one ASR statement into zero or more quality attributes.

        Args:
            text:
                Natural-language ASR statement.

        Returns:
            Quality hits whose sigmoid probability is greater than or equal
            to the configured decision threshold.
        """

        if not isinstance(text, str) or not text.strip():
            return []

        encoded = self.tokenizer(
            text,
            truncation=True,
            padding=True,
            max_length=self.max_length,
            return_tensors="pt",
        )

        encoded = {
            key: value.to(self.device)
            for key, value in encoded.items()
        }

        with torch.no_grad():

            outputs = self.model(**encoded)

            probabilities = (
                torch.sigmoid(outputs.logits)
                .squeeze(0)
                .cpu()
                .tolist()
            )

        hits: list[QualityHit] = []

        for index, probability in enumerate(probabilities):

            if probability >= self.threshold:

                hits.append(
                    QualityHit(
                        name=QualityAttribute(
                            LABEL_LIST[index]
                        ),
                        confidence=round(
                            float(probability),
                            4,
                        ),
                    )
                )

        hits.sort(
            key=lambda hit: hit.confidence,
            reverse=True,
        )

        return hits