# Generates semantic embeddings for requirements and design artifacts
# using a pretrained Sentence-BERT model.

from sentence_transformers import SentenceTransformer


class TraceabilityEmbeddingService:

    MODEL_NAME = (
        "sentence-transformers/"
        "all-MiniLM-L6-v2"
    )

    def __init__(self):
        print(
            "Loading Traceability SBERT model..."
        )

        self.model = SentenceTransformer(
            self.MODEL_NAME
        )

        print(
            "Traceability SBERT model loaded."
        )

    def encode_text(self, text: str):

        # Convert one text string into an embedding vector.

        return self.model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True
        )

    def encode_texts(
        self,
        texts: list[str]
    ):

        # Convert multiple text strings into embedding vectors.

        return self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True
        )


_embedding_service = None


def get_traceability_embedding_service():

    # Returns one shared SBERT instance so the model
    # does not reload for every request.

    global _embedding_service

    if _embedding_service is None:
        _embedding_service = (
            TraceabilityEmbeddingService()
        )

    return _embedding_service