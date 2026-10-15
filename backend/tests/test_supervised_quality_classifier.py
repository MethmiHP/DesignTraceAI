from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import torch

from modules.architecture_design.supervised_quality_classifier import (
    SupervisedTransformerQualityClassifier,
)


# =========================================================
# Test 1: Fast unit test using mocked tokenizer and model
# =========================================================

@patch(
    "modules.architecture_design.supervised_quality_classifier."
    "AutoModelForSequenceClassification.from_pretrained"
)
@patch(
    "modules.architecture_design.supervised_quality_classifier."
    "AutoTokenizer.from_pretrained"
)
def test_supervised_classifier_returns_expected_quality_attributes(
    mock_tokenizer_loader,
    mock_model_loader,
    tmp_path,
):
    # Fake model directory
    model_dir = tmp_path / "best_model"
    model_dir.mkdir()

    # Mock tokenizer
    mock_tokenizer = MagicMock()

    mock_tokenizer.return_value = {
        "input_ids": torch.tensor([[1, 2, 3]]),
        "attention_mask": torch.tensor([[1, 1, 1]]),
    }

    mock_tokenizer_loader.return_value = mock_tokenizer

    # Mock model
    mock_model = MagicMock()

    # LABEL_LIST order:
    # 0 Security
    # 1 Scalability
    # 2 Performance
    # 3 Reliability
    # 4 Maintainability
    # 5 Availability
    #
    # Positive logits -> sigmoid probability > 0.50
    # Negative logits -> sigmoid probability < 0.50
    mock_output = MagicMock()

    mock_output.logits = torch.tensor(
        [[-2.0, 3.0, 3.5, -2.0, -2.0, -2.0]]
    )

    mock_model.return_value = mock_output
    mock_model_loader.return_value = mock_model

    # Create classifier
    classifier = SupervisedTransformerQualityClassifier(
        model_path=model_dir,
        threshold=0.50,
    )

    # Run classification
    results = classifier.classify(
        "The system shall support many concurrent users "
        "while maintaining low response times."
    )

    names = [result.name.value for result in results]

    # Check expected labels
    assert "Scalability" in names
    assert "Performance" in names

    # Check unwanted labels are excluded
    assert "Security" not in names
    assert "Reliability" not in names
    assert "Maintainability" not in names
    assert "Availability" not in names

    # Confirm exactly two labels were returned
    assert len(results) == 2

    # Confirm results are sorted by confidence descending
    assert results[0].confidence >= results[1].confidence


# =========================================================
# Test 2: Real fine-tuned RoBERTa smoke test
# =========================================================

def test_real_roberta_model_smoke():
    backend_dir = Path(__file__).resolve().parents[1]

    model_path = (
        backend_dir
        / "datasets"
        / "roberta"
        / "best_model"
    )

    # Skip this integration test if the large model artifact
    # is not available in the local environment.
    if not model_path.exists():
        pytest.skip("Fine-tuned RoBERTa model is not available.")

    classifier = SupervisedTransformerQualityClassifier(
        model_path=model_path,
        threshold=0.50,
    )

    results = classifier.classify(
        "The platform shall support 100,000 concurrent users "
        "while maintaining API response times below 250 milliseconds."
    )

    names = [result.name.value for result in results]

    # This ASR should be recognised as both a scalability
    # and performance requirement by the trained model.
    assert "Scalability" in names
    assert "Performance" in names

    # Make sure the classifier actually returned results
    assert len(results) >= 2