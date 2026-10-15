import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    APP_NAME: str = "DesignTrace AI"

    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "mock")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "mock-model")

    OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
    GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY")

    # Architecture Decision Agent Settings
    ARCHITECTURE_LLM_MODEL: str = os.getenv("ARCHITECTURE_LLM_MODEL", "gemini-2.5-flash")
    ARCHITECTURE_EMBEDDING_MODEL: str = os.getenv("ARCHITECTURE_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    ARCHITECTURE_RETRIEVAL_TOP_K: int = int(os.getenv("ARCHITECTURE_RETRIEVAL_TOP_K", "5"))
    ARCHITECTURE_USE_STUB_LLM: bool = os.getenv("ARCHITECTURE_USE_STUB_LLM", "false").lower() in ("true", "1", "yes")
    ARCHITECTURE_QA_CLASSIFIER: str = os.getenv("ARCHITECTURE_QA_CLASSIFIER", "keyword")
    ARCHITECTURE_QA_SEMANTIC_THRESHOLD: float = float(os.getenv("ARCHITECTURE_QA_SEMANTIC_THRESHOLD", "0.50"))

    def __init__(self) -> None:
        self.LLM_PROVIDER = os.getenv("LLM_PROVIDER", self.LLM_PROVIDER)
        self.LLM_MODEL = os.getenv("LLM_MODEL", self.LLM_MODEL)
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        self.ARCHITECTURE_LLM_MODEL = os.getenv("ARCHITECTURE_LLM_MODEL", self.ARCHITECTURE_LLM_MODEL)
        self.ARCHITECTURE_EMBEDDING_MODEL = os.getenv("ARCHITECTURE_EMBEDDING_MODEL", self.ARCHITECTURE_EMBEDDING_MODEL)
        self.ARCHITECTURE_RETRIEVAL_TOP_K = int(os.getenv("ARCHITECTURE_RETRIEVAL_TOP_K", str(self.ARCHITECTURE_RETRIEVAL_TOP_K)))
        self.ARCHITECTURE_USE_STUB_LLM = os.getenv("ARCHITECTURE_USE_STUB_LLM", "false").lower() in ("true", "1", "yes")
        self.ARCHITECTURE_QA_CLASSIFIER = os.getenv("ARCHITECTURE_QA_CLASSIFIER", self.ARCHITECTURE_QA_CLASSIFIER)
        self.ARCHITECTURE_QA_SEMANTIC_THRESHOLD = float(os.getenv("ARCHITECTURE_QA_SEMANTIC_THRESHOLD", str(self.ARCHITECTURE_QA_SEMANTIC_THRESHOLD)))


settings = Settings()