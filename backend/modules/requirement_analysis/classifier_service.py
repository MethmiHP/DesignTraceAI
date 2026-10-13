from pathlib import Path

# Provides the runtime requirement-classification service using the selected
# trained models. It first classifies each requirement as FR or NFR and,
# when classified as NFR, predicts its quality attribute and confidence.

import torch

from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
)


# PATHS

BASE_DIR = Path(
    __file__
).resolve().parents[2]


TRAINED_MODEL_DIR = (
    BASE_DIR
    / "trained_models"
    / "requirement_analysis"
)


FR_NFR_MODEL_PATH = (
    TRAINED_MODEL_DIR
    / "fr_nfr"
    / "roberta"
    / "final"
)


NFR_CATEGORY_MODEL_PATH = (
    TRAINED_MODEL_DIR
    / "nfr_category"
    / "roberta"
    / "final"
)


# CLASSIFIER SERVICE

class RequirementClassifierService:

    def __init__(self):

        print(
            "Loading Requirement Analysis classifiers..."
        )


        # FR / NFR MODEL

        self.fr_nfr_tokenizer = (
            AutoTokenizer.from_pretrained(
                FR_NFR_MODEL_PATH
            )
        )


        self.fr_nfr_model = (
            AutoModelForSequenceClassification
            .from_pretrained(
                FR_NFR_MODEL_PATH
            )
        )


        self.fr_nfr_model.eval()


        # NFR CATEGORY MODEL

        self.nfr_tokenizer = (
            AutoTokenizer.from_pretrained(
                NFR_CATEGORY_MODEL_PATH
            )
        )


        self.nfr_model = (
            AutoModelForSequenceClassification
            .from_pretrained(
                NFR_CATEGORY_MODEL_PATH
            )
        )


        self.nfr_model.eval()


        print(
            "Requirement Analysis classifiers loaded."
        )


    # FR / NFR CLASSIFICATION

    def classify_requirement_type(
        self,
        text: str
    ) -> dict:

        inputs = self.fr_nfr_tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=128,
        )


        with torch.no_grad():

            outputs = self.fr_nfr_model(
                **inputs
            )


        probabilities = torch.softmax(
            outputs.logits,
            dim=-1
        )


        predicted_id = torch.argmax(
            probabilities,
            dim=-1
        ).item()


        confidence = probabilities[
            0
        ][
            predicted_id
        ].item()


        label = (
            self.fr_nfr_model
            .config
            .id2label[
                predicted_id
            ]
        )


        return {

            "requirement_type":
                label,

            "confidence":
                round(
                    confidence,
                    4
                )
        }


    # NFR CATEGORY CLASSIFICATION

    def classify_nfr_category(
        self,
        text: str
    ) -> dict:

        inputs = self.nfr_tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=128,
        )


        with torch.no_grad():

            outputs = self.nfr_model(
                **inputs
            )


        probabilities = torch.softmax(
            outputs.logits,
            dim=-1
        )


        predicted_id = torch.argmax(
            probabilities,
            dim=-1
        ).item()


        confidence = probabilities[
            0
        ][
            predicted_id
        ].item()


        label = (
            self.nfr_model
            .config
            .id2label[
                predicted_id
            ]
        )


        return {

            "quality_attribute":
                label,

            "confidence":
                round(
                    confidence,
                    4
                )
        }


    # COMPLETE CLASSIFICATION

    def classify(
        self,
        text: str
    ) -> dict:

        """
        First classify the requirement as FR or NFR.

        If predicted as NFR, also classify the
        NFR quality attribute.
        """

        type_result = (
            self.classify_requirement_type(
                text
            )
        )


        requirement_type = (
            type_result[
                "requirement_type"
            ]
        )


        result = {

            "requirement_type":
                requirement_type,

            "type_confidence":
                type_result[
                    "confidence"
                ],

            "quality_attribute":
                None,

            "quality_confidence":
                None,
        }


        # Only classify NFR category when predicted as NFR
        if requirement_type == "NFR":

            category_result = (
                self.classify_nfr_category(
                    text
                )
            )


            result[
                "quality_attribute"
            ] = category_result[
                "quality_attribute"
            ]


            result[
                "quality_confidence"
            ] = category_result[
                "confidence"
            ]


        return result


# CACHED CLASSIFIER INSTANCE

_classifier_instance = None


def get_requirement_classifier():

    """
    Load the trained classifiers only once.

    This prevents the RoBERTa models from being
    reloaded every time RequirementAnalysisService
    is created.
    """

    global _classifier_instance


    if _classifier_instance is None:

        _classifier_instance = (
            RequirementClassifierService()
        )


    return _classifier_instance