"""
DesignTrace AI - RoBERTa Database Concept Extractor

Uses the trained RoBERTa NER model to extract
ENTITY, ATTRIBUTE, and ACTION concepts.
"""

from pathlib import Path

import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification


BASE_DIR = Path(__file__).resolve().parents[2]

MODEL_PATH = (
    BASE_DIR
    / "outputs"
    / "nlp_models"
    / "roberta_project_split"
)


class RobertaConceptExtractor:

    def __init__(self):
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"RoBERTa model not found: {MODEL_PATH}"
            )

        self.tokenizer = AutoTokenizer.from_pretrained(
            str(MODEL_PATH),
            use_fast=True,
            add_prefix_space=True,
        )

        self.model = AutoModelForTokenClassification.from_pretrained(
            str(MODEL_PATH)
        )

        self.model.eval()

        self.device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )

        self.model.to(self.device)

    def extract(self, text: str) -> dict:
        """
        Extract database concepts from one requirement.
        """

        words = text.split()

        if not words:
            return {
                "entities": [],
                "attributes": [],
                "actions": [],
            }

        encoded = self.tokenizer(
            words,
            is_split_into_words=True,
            return_tensors="pt",
            truncation=True,
            max_length=128,
        )

        word_ids = encoded.word_ids(batch_index=0)

        inputs = {
            key: value.to(self.device)
            for key, value in encoded.items()
        }

        with torch.no_grad():
            outputs = self.model(**inputs)

        predictions = (
            outputs.logits.argmax(dim=-1)[0].tolist()
        )

        labels = self.model.config.id2label

        word_labels = []
        previous_word_id = None

        for index, word_id in enumerate(word_ids):

            if word_id is None:
                continue

            if word_id == previous_word_id:
                continue

            label = labels[predictions[index]]

            word_labels.append(label)

            previous_word_id = word_id

        concepts = {
            "entities": [],
            "attributes": [],
            "actions": [],
        }

        current_words = []
        current_type = None

        def save_current():
            if not current_words or not current_type:
                return

            value = " ".join(current_words)

            key = {
                "ENTITY": "entities",
                "ATTRIBUTE": "attributes",
                "ACTION": "actions",
            }.get(current_type)

            if key and value not in concepts[key]:
                concepts[key].append(value)

        for word, label in zip(words, word_labels):

            if label.startswith("B-"):
                save_current()
                current_type = label[2:]
                current_words = [word]

            elif label.startswith("I-"):
                entity_type = label[2:]

                if current_type == entity_type:
                    current_words.append(word)
                else:
                    save_current()
                    current_type = entity_type
                    current_words = [word]

            else:
                save_current()
                current_type = None
                current_words = []

        save_current()

        return concepts
