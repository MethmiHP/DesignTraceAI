import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    APP_NAME: str = "DesignTrace AI"

    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "mock")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "mock-model")

    OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
    GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY")


settings = Settings()