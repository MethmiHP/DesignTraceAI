# Cleans and preprocesses raw requirement text by normalizing whitespace,
# handling common bullet symbols, and splitting the text into individual sentences.
import re

def clean_text(text: str) -> str:
    """
    Basic deterministic text cleaning.
    """

    if not text:
        return ""

    text = text.strip()

    # Replace multiple spaces/tabs/newlines with one space
    text = re.sub(r"\s+", " ", text)

    # Normalize common bullet symbols
    text = text.replace("•", ". ")

    return text


def split_sentences(text: str) -> list[str]:
    """
    Simple sentence segmentation.

    Later this can be replaced or supported by spaCy.
    """

    cleaned = clean_text(text)

    if not cleaned:
        return []

    sentences = re.split(
        r"(?<=[.!?])\s+",
        cleaned
    )

    return [
        sentence.strip()
        for sentence in sentences
        if sentence.strip()
    ]


def preprocess_text(text: str) -> dict:
    """
    Main preprocessing method.
    """

    cleaned_text = clean_text(text)

    sentences = split_sentences(cleaned_text)

    return {
        "cleaned_text": cleaned_text,
        "sentences": sentences
    }