# Gemini client used by the Traceability Module.

import os
import time

from dotenv import load_dotenv
from google import genai

load_dotenv()

class TraceabilityLLMClient:

    MODEL_NAME = "gemini-3.5-flash-lite"

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY is not configured."
            )

        self.client = genai.Client(
            api_key=api_key
        )

    def generate(
        self,
        prompt: str,
        max_retries: int = 3
    ) -> str:

        for attempt in range(max_retries):

            try:

                response = (
                    self.client.models.generate_content(
                        model=self.MODEL_NAME,
                        contents=prompt
                    )
                )

                if not response.text:
                    raise ValueError(
                        "Gemini returned an empty response."
                    )

                return response.text.strip()

            except Exception as error:

                error_message = str(error)

                
                # QUOTA / RATE LIMIT

                if (
                    "429" in error_message
                    or
                    "RESOURCE_EXHAUSTED"
                    in error_message
                ):

                    raise RuntimeError(
                        "Gemini quota or rate limit reached. "
                        "Traceability validation stopped."
                    ) from error


                # TEMPORARY SERVER ERROR

                if (
                    "503" in error_message
                    or
                    "UNAVAILABLE" in error_message
                    or
                    "high demand" in error_message.lower()
                ):

                    if attempt < max_retries - 1:

                        wait_seconds = 2 ** attempt

                        print(
                            f"Gemini temporarily unavailable. "
                            f"Retrying in {wait_seconds} seconds..."
                        )

                        time.sleep(
                            wait_seconds
                        )

                        continue

                raise

        raise RuntimeError(
            "Gemini request failed after retries."
        )


_traceability_llm_client = None


def get_traceability_llm_client():
    ""
    # Returns one shared TraceabilityLLMClient instance
    # within the current Python process.
    
    global _traceability_llm_client

    if _traceability_llm_client is None:

        _traceability_llm_client = (
            TraceabilityLLMClient()
        )

    return _traceability_llm_client