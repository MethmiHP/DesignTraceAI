import json
import random
from pathlib import Path

import torch
from torch.utils.data import Dataset, DataLoader

from transformers import (
    AutoTokenizer,
    AutoModelForTokenClassification,
)



# PATHS


BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "prepared"

TRAIN_FILE = DATA_DIR / "train.json"
VALIDATION_FILE = DATA_DIR / "validation.json"

MODEL_OUTPUT_DIR = BASE_DIR / "frozen_model"



# LABELS


LABELS = [
    "O",
    "B-ACTOR",
    "I-ACTOR",
    "B-ACTION",
    "I-ACTION",
    "B-RESOURCE",
    "I-RESOURCE",
]


label2id = {
    label: index
    for index, label in enumerate(LABELS)
}


id2label = {
    index: label
    for label, index in label2id.items()
}



# SETTINGS


MODEL_NAME = "google-bert/bert-base-uncased"

MAX_LENGTH = 128

BATCH_SIZE = 8

EPOCHS = 10

LEARNING_RATE = 5e-4

SEED = 42



# LOAD JSON


def load_json(path: Path):

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)



# DATASET


class BertSemanticDataset(Dataset):

    def __init__(
        self,
        records,
        tokenizer,
    ):

        self.records = records
        self.tokenizer = tokenizer

    def __len__(self):

        return len(self.records)

    def __getitem__(self, index):

        record = self.records[index]

        tokens = record["tokens"]
        labels = record["labels"]

        encoding = self.tokenizer(
            tokens,
            is_split_into_words=True,
            truncation=True,
            padding="max_length",
            max_length=MAX_LENGTH,
        )

        word_ids = encoding.word_ids()

        aligned_labels = []

        previous_word_id = None

        for word_id in word_ids:

            # Special tokens and padding
            if word_id is None:

                aligned_labels.append(-100)

            # Only label the first BERT sub-token
            elif word_id != previous_word_id:

                aligned_labels.append(
                    label2id[
                        labels[word_id]
                    ]
                )

            # Ignore additional sub-tokens
            else:

                aligned_labels.append(-100)

            previous_word_id = word_id

        encoding["labels"] = aligned_labels

        return {
            key: torch.tensor(
                value,
                dtype=torch.long,
            )
            for key, value
            in encoding.items()
        }



# BIO LABELS -> ENTITY SPANS


def bio_to_entities(labels):

    entities = []

    current_type = None
    start_index = None

    for index, label in enumerate(labels):

   
        # Outside any entity
      

        if label == "O":

            if current_type is not None:

                entities.append(
                    (
                        start_index,
                        index,
                        current_type,
                    )
                )

                current_type = None
                start_index = None

            continue

        # Example:
        # B-ACTOR -> B, ACTOR
        prefix, entity_type = label.split(
            "-",
            1,
        )

    
        # Beginning of entity
   

        if prefix == "B":

            if current_type is not None:

                entities.append(
                    (
                        start_index,
                        index,
                        current_type,
                    )
                )

            current_type = entity_type
            start_index = index

      
        # Inside entity
       

        elif prefix == "I":

            # Invalid I-tag after another entity type.
            # Treat it as the beginning of a new entity.
            if current_type != entity_type:

                if current_type is not None:

                    entities.append(
                        (
                            start_index,
                            index,
                            current_type,
                        )
                    )

                current_type = entity_type
                start_index = index

   
    # Close final entity if required
   

    if current_type is not None:

        entities.append(
            (
                start_index,
                len(labels),
                current_type,
            )
        )

    return set(entities)


# VALIDATION


def evaluate(
    model,
    data_loader,
    device,
):

    model.eval()

    entity_types = [
        "ACTOR",
        "ACTION",
        "RESOURCE",
    ]

    counts = {
        entity_type: {
            "tp": 0,
            "fp": 0,
            "fn": 0,
        }
        for entity_type in entity_types
    }

    exact_matches = 0
    total_sequences = 0

    with torch.no_grad():

        for batch in data_loader:

            labels = batch[
                "labels"
            ].to(device)

            model_inputs = {
                key: value.to(device)
                for key, value
                in batch.items()
                if key != "labels"
            }

            outputs = model(
                **model_inputs
            )

            predictions = torch.argmax(
                outputs.logits,
                dim=-1,
            )

            predictions = (
                predictions
                .cpu()
                .tolist()
            )

            labels = (
                labels
                .cpu()
                .tolist()
            )

            for predicted_row, label_row in zip(
                predictions,
                labels,
            ):

                true_labels = []
                predicted_labels = []

              
                # Remove ignored tokens
             

                for predicted_id, label_id in zip(
                    predicted_row,
                    label_row,
                ):

                    if label_id == -100:
                        continue

                    true_labels.append(
                        id2label[
                            label_id
                        ]
                    )

                    predicted_labels.append(
                        id2label[
                            predicted_id
                        ]
                    )

              
                # Convert BIO sequences into entities
            

                gold_entities = bio_to_entities(
                    true_labels
                )

                predicted_entities = bio_to_entities(
                    predicted_labels
                )

              
                # Exact match
            

                if gold_entities == predicted_entities:

                    exact_matches += 1

                total_sequences += 1

       
                # TP / FP / FN
          

                for entity_type in entity_types:

                    gold_for_type = {
                        entity
                        for entity in gold_entities
                        if entity[2] == entity_type
                    }

                    predicted_for_type = {
                        entity
                        for entity in predicted_entities
                        if entity[2] == entity_type
                    }

                    counts[
                        entity_type
                    ]["tp"] += len(
                        gold_for_type
                        & predicted_for_type
                    )

                    counts[
                        entity_type
                    ]["fp"] += len(
                        predicted_for_type
                        - gold_for_type
                    )

                    counts[
                        entity_type
                    ]["fn"] += len(
                        gold_for_type
                        - predicted_for_type
                    )

  
    # CALCULATE METRICS
   

    report = {}

    macro_f1_values = []

    for entity_type in entity_types:

        tp = counts[
            entity_type
        ]["tp"]

        fp = counts[
            entity_type
        ]["fp"]

        fn = counts[
            entity_type
        ]["fn"]

        precision = (
            tp / (tp + fp)
            if (tp + fp)
            else 0.0
        )

        recall = (
            tp / (tp + fn)
            if (tp + fn)
            else 0.0
        )

        f1 = (
            2
            * precision
            * recall
            / (precision + recall)
            if (precision + recall)
            else 0.0
        )

        report[entity_type] = {
            "precision": precision,
            "recall": recall,
            "f1-score": f1,
        }

        macro_f1_values.append(
            f1
        )

    macro_f1 = (
        sum(macro_f1_values)
        / len(macro_f1_values)
    )

    exact_match = (
        exact_matches
        / total_sequences
        if total_sequences
        else 0.0
    )

    report["exact_match"] = (
        exact_match
    )

    return (
        macro_f1,
        report,
    )



# TRAIN


def main():

  
    # RANDOM SEED


    random.seed(SEED)

    torch.manual_seed(SEED)

    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(SEED)


    # DEVICE


    if torch.cuda.is_available():

        device = torch.device(
            "cuda"
        )

    elif torch.backends.mps.is_available():

        device = torch.device(
            "mps"
        )

    else:

        device = torch.device(
            "cpu"
        )

    print(
        f"Using device: {device}"
    )

    if device.type == "cuda":

        print(
            "GPU:",
            torch.cuda.get_device_name(0),
        )


    # LOAD DATA


    train_records = load_json(
        TRAIN_FILE
    )

    validation_records = load_json(
        VALIDATION_FILE
    )

    print(
        f"Train examples: "
        f"{len(train_records)}"
    )

    print(
        f"Validation examples: "
        f"{len(validation_records)}"
    )

    
    # TOKENIZER
  

    tokenizer = (
        AutoTokenizer
        .from_pretrained(
            MODEL_NAME,
            use_fast=True,
        )
    )


    # MODEL


    model = (
        AutoModelForTokenClassification
        .from_pretrained(
            MODEL_NAME,
            num_labels=len(LABELS),
            id2label=id2label,
            label2id=label2id,
        )
    )


    # FREEZE BERT BACKBONE
   

    for parameter in (
        model.base_model.parameters()
    ):

        parameter.requires_grad = False

    # ONLY CLASSIFICATION HEAD IS TRAINABLE
 

    trainable_parameters = [
        parameter
        for parameter
        in model.parameters()
        if parameter.requires_grad
    ]

    total_parameters = sum(
        parameter.numel()
        for parameter
        in model.parameters()
    )

    trainable_parameter_count = sum(
        parameter.numel()
        for parameter
        in trainable_parameters
    )

    print()
    print(
        "BERT backbone frozen."
    )

    print(
        "Only token-classification "
        "head will be trained."
    )

    print(
        f"Total parameters: "
        f"{total_parameters:,}"
    )

    print(
        f"Trainable parameters: "
        f"{trainable_parameter_count:,}"
    )

    model.to(device)


    # DATASETS

    train_dataset = BertSemanticDataset(
        train_records,
        tokenizer,
    )

    validation_dataset = (
        BertSemanticDataset(
            validation_records,
            tokenizer,
        )
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
    )

    validation_loader = DataLoader(
        validation_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
    )


    # OPTIMIZER


    optimizer = torch.optim.AdamW(
        trainable_parameters,
        lr=LEARNING_RATE,
    )

    best_macro_f1 = -1.0

  
    # TRAINING LOOP


    for epoch in range(
        1,
        EPOCHS + 1,
    ):

        model.train()

        total_loss = 0.0

        for batch in train_loader:

            optimizer.zero_grad()

            batch = {
                key: value.to(device)
                for key, value
                in batch.items()
            }

            outputs = model(
                **batch
            )

            loss = outputs.loss

            loss.backward()

            optimizer.step()

            total_loss += (
                loss.item()
            )

        average_loss = (
            total_loss
            / len(train_loader)
        )

        # VALIDATE
   

        macro_f1, report = evaluate(
            model,
            validation_loader,
            device,
        )

        actor_f1 = report[
            "ACTOR"
        ]["f1-score"]

        action_f1 = report[
            "ACTION"
        ]["f1-score"]

        resource_f1 = report[
            "RESOURCE"
        ]["f1-score"]

        exact_match = report[
            "exact_match"
        ]

        print()

        print(
            f"Epoch {epoch:02d}"
        )

        print(
            f"Loss:        "
            f"{average_loss:.4f}"
        )

        print(
            f"Actor F1:    "
            f"{actor_f1:.4f}"
        )

        print(
            f"Action F1:   "
            f"{action_f1:.4f}"
        )

        print(
            f"Resource F1: "
            f"{resource_f1:.4f}"
        )

        print(
            f"Macro F1:    "
            f"{macro_f1:.4f}"
        )

        print(
            f"Exact Match: "
            f"{exact_match:.4f}"
        )


        # SAVE BEST MODEL


        if macro_f1 > best_macro_f1:

            best_macro_f1 = (
                macro_f1
            )

            MODEL_OUTPUT_DIR.mkdir(
                parents=True,
                exist_ok=True,
            )

            model.save_pretrained(
                MODEL_OUTPUT_DIR
            )

            tokenizer.save_pretrained(
                MODEL_OUTPUT_DIR
            )

            print(
                "-> Best model saved"
            )

    # FINISHED
   

    print()

    print(
        "Frozen BERT training complete."
    )

    print(
        f"Best validation Macro F1: "
        f"{best_macro_f1:.4f}"
    )

    print(
        f"Model saved to: "
        f"{MODEL_OUTPUT_DIR}"
    )


if __name__ == "__main__":
    main()