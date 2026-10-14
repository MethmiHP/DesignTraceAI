import re
from pathlib import Path

import torch

from transformers import (
    AutoTokenizer,
    AutoModelForTokenClassification,
)

from .semantic_extractor import (
    BaseSemanticExtractor,
)

from .schemas import (
    SemanticExtraction,
)


class BertSemanticExtractor(
    BaseSemanticExtractor
):

    def __init__(self):

      
        # MODEL PATH
     
        backend_dir = (
            Path(__file__)
            .resolve()
            .parents[2]
        )

        self.model_dir = (
            backend_dir
            / "datasets"
            / "api_semantic_bert"
        )


        if not self.model_dir.exists():

            raise FileNotFoundError(
                "BERT semantic model not found at: "
                f"{self.model_dir}"
            )


       
        # DEVICE
       

        if torch.cuda.is_available():

            self.device = (
                torch.device("cuda")
            )

        elif (
            hasattr(
                torch.backends,
                "mps",
            )
            and torch.backends.mps.is_available()
        ):

            self.device = (
                torch.device("mps")
            )

        else:

            self.device = (
                torch.device("cpu")
            )


   
        # TOKENIZER
     

        self.tokenizer = (
            AutoTokenizer
            .from_pretrained(
                self.model_dir,
                use_fast=True,
            )
        )


        
        # MODEL
      

        self.model = (
            AutoModelForTokenClassification
            .from_pretrained(
                self.model_dir
            )
        )

        self.model.to(
            self.device
        )

        self.model.eval()


  
    # SIMPLE WORD TOKENIZATION


    @staticmethod
    def _tokenize_requirement(
        text: str,
    ) -> list[str]:

        return re.findall(
            r"\w+(?:[-']\w+)*|[^\w\s]",
            text,
        )


   
    # BIO LABELS -> ENTITY SPANS


    @staticmethod
    def _extract_entities(
        tokens: list[str],
        labels: list[str],
    ) -> dict[str, list[str]]:

        entities = {
            "ACTOR": [],
            "ACTION": [],
            "RESOURCE": [],
        }

        current_type = None
        current_tokens = []


        def save_current():

            nonlocal current_type
            nonlocal current_tokens

            if (
                current_type is not None
                and current_tokens
            ):

                entities[
                    current_type
                ].append(
                    " ".join(
                        current_tokens
                    )
                )

            current_type = None
            current_tokens = []


        for token, label in zip(
            tokens,
            labels,
        ):

            if label == "O":

                save_current()
                continue


            if "-" not in label:

                save_current()
                continue


            prefix, entity_type = (
                label.split(
                    "-",
                    1,
                )
            )


            if (
                entity_type
                not in entities
            ):

                save_current()
                continue


            if prefix == "B":

                save_current()

                current_type = (
                    entity_type
                )

                current_tokens = [
                    token
                ]


            elif prefix == "I":

                if (
                    current_type
                    == entity_type
                ):

                    current_tokens.append(
                        token
                    )

                else:

                    # Recover orphan I-tag
                    save_current()

                    current_type = (
                        entity_type
                    )

                    current_tokens = [
                        token
                    ]


        save_current()

        return entities



    # BERT PREDICTION
  

    def _predict(
        self,
        statement: str,
    ):

        tokens = (
            self._tokenize_requirement(
                statement
            )
        )


        if not tokens:

            return (
                tokens,
                [],
                {
                    "ACTOR": [],
                    "ACTION": [],
                    "RESOURCE": [],
                },
            )


        encoding = self.tokenizer(
            tokens,
            is_split_into_words=True,
            return_tensors="pt",
            truncation=True,
            max_length=128,
        )


        word_ids = encoding.word_ids(
            batch_index=0
        )


        model_inputs = {
            key: value.to(
                self.device
            )
            for key, value
            in encoding.items()
        }


        with torch.no_grad():

            outputs = self.model(
                **model_inputs
            )


        prediction_ids = (
            torch.argmax(
                outputs.logits,
                dim=-1,
            )[0]
            .cpu()
            .tolist()
        )


        predicted_labels = []

        previous_word_id = None


        for (
            token_index,
            word_id,
        ) in enumerate(
            word_ids
        ):

            if word_id is None:
                continue


            # Only use first BERT
            # sub-token for each word
            if (
                word_id
                != previous_word_id
            ):

                prediction_id = (
                    prediction_ids[
                        token_index
                    ]
                )


                label = (
                    self.model
                    .config
                    .id2label[
                        prediction_id
                    ]
                )


                predicted_labels.append(
                    label
                )


            previous_word_id = (
                word_id
            )


        entities = (
            self._extract_entities(
                tokens,
                predicted_labels,
            )
        )


        return (
            tokens,
            predicted_labels,
            entities,
        )



    # PUBLIC EXTRACTION METHOD
   

    def extract(
        self,
        requirement_id: str,
        statement: str,
    ) -> SemanticExtraction:

        (
            _,
            _,
            entities,
        ) = self._predict(
            statement
        )


        actor = (
            entities["ACTOR"][0]
            if entities["ACTOR"]
            else None
        )


        action = (
            entities["ACTION"][0]
            if entities["ACTION"]
            else None
        )


        resource = (
            entities["RESOURCE"][0]
            if entities["RESOURCE"]
            else None
        )


      
        # Keep extracted wording,
        # but standardize casing expected by
        # downstream API module logic.
        #
        # No spelling correction is done here.
    

        if actor:

            actor = actor.title()


        if action:

            action = action.lower()


        if resource:

            resource = resource.title()


        return SemanticExtraction(
            requirement_id=requirement_id,
            actor=actor,
            action=action,
            resource=resource,
            confidence=None,
        )