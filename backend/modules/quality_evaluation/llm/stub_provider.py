from pydantic import BaseModel

from .provider import (
    BaseQualityLLMProvider,
)


class StubQualityLLMProvider(
    BaseQualityLLMProvider
):

    name = "stub"

    def __init__(
        self,
        response: BaseModel,
    ):
        self.response = response

        self.last_prompt: (
            str | None
        ) = None

    def generate_structured(
        self,
        prompt: str,
        schema_class,
    ):
        self.last_prompt = prompt

        return self.response