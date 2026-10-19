import pickle
from pathlib import Path

from modules.adr.schemas import (
    DesignDecision,
    SignificanceCriteria,
    SignificanceResult,
)


class MLSignificanceClassifier:
    """
    TF-IDF + Logistic Regression classifier for ADR significance detection.

    Input:
        title + context + decision

    Output:
        SignificanceResult compatible with the ADR workflow.
    """

    DEFAULT_THRESHOLD = 0.50

    def __init__(
        self,
        model_path: str | Path | None = None,
        threshold: float = DEFAULT_THRESHOLD,
    ):
        self.threshold = threshold

        if model_path is None:
            backend_dir = Path(__file__).resolve().parents[2]

            model_path = (
                backend_dir
                / "datasets"
                / "adr_significance"
                / "models"
                / "tfidf_logreg_reduced"
                / "model.pkl"
            )

        self.model_path = Path(model_path)
        self.model = None

        self._load_model()

    def _load_model(self):
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"ADR significance model not found: "
                f"{self.model_path}"
            )

        with self.model_path.open("rb") as file:
            self.model = pickle.load(file)

    @staticmethod
    def _build_text(
        decision: DesignDecision,
    ) -> str:
        """
        Must match the representation used during training:
        title + context + decision.
        """

        return " ".join(
            [
                decision.title or "",
                decision.context or "",
                decision.decision or "",
            ]
        ).strip()

    def evaluate(
        self,
        decision: DesignDecision,
    ) -> SignificanceResult:
        text = self._build_text(decision)

        probability = float(
            self.model.predict_proba(
                [text]
            )[0][1]
        )

        significant = (
            probability >= self.threshold
        )

        reasons = [
            (
                "ML significance probability "
                f"{probability:.4f} "
                f"{'>=' if significant else '<'} "
                f"threshold {self.threshold:.2f}."
            )
        ]

        return SignificanceResult(
            decision_id=decision.decision_id,
            significant=significant,
            score=probability,
            criteria=SignificanceCriteria(),
            reasons=reasons,
        )