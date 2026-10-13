# Manually tests the RequirementClassifierService using sample requirements
# and prints the predicted FR/NFR type, NFR quality attribute, and confidence
# scores to verify that the trained models work correctly at runtime.

from modules.requirement_analysis.classifier_service import (
    RequirementClassifierService
)


classifier = RequirementClassifierService()


examples = [
    "The system shall allow patients to book appointments.",

    "The system shall respond within 2 seconds.",

    "The system shall encrypt all patient information.",

    "The user interface shall be easy to use.",

    "The system shall be available 99.9 percent of the time.",
]


for text in examples:

    print(
        "\n--------------------------------"
    )

    print(
        "Requirement:"
    )

    print(
        text
    )

    result = classifier.classify(
        text
    )

    print(
        "Prediction:"
    )

    print(
        result
    )