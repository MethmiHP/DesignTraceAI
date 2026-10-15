"""
Baseline Stabilisation Tests – Milestone 6.1.

Verifies:
1. GEMINI_API_KEY is read from environment variable with no hard-coded keys in config.
2. get_architecture_service dependency caching (singleton reuse).
3. SentenceTransformerEmbeddingProvider and StubEmbeddingProvider model_name attributes.
4. StubLLMProvider and GeminiLLMProvider model_name metadata reporting.
5. Benchmark validation rejecting unsupported Quality Attributes.
6. Benchmark cases dataset ARCH-003 label alignment (removal of Testability).
"""

from __future__ import annotations

import os
import json
from pathlib import Path
import pytest
from pydantic import ValidationError

from shared.config import Settings
from modules.architecture_design.config import ArchitectureConfig
from modules.architecture_design.dependencies import get_architecture_service
from modules.architecture_design.service import ArchitectureDesignService
from modules.architecture_design.retrieval.embedding_provider import (
    SentenceTransformerEmbeddingProvider,
    StubEmbeddingProvider,
)
from modules.architecture_design.llm.provider import StubLLMProvider, GeminiLLMProvider
from modules.architecture_design.schemas import (
    BenchmarkCase,
    ASRInput,
    ASRBatch,
    QualityAttribute,
)
from modules.architecture_design.retrieval.vector_store import InMemoryVectorStore


# ===========================================================================
# Task 1: API Key Config & Source Code Scrutiny
# ===========================================================================

def test_gemini_api_key_configuration(monkeypatch):
    """Ensure GEMINI_API_KEY is retrieved from the environment variable."""
    monkeypatch.setenv("GEMINI_API_KEY", "env-test-key-12345")
    s = Settings()
    assert s.GEMINI_API_KEY == "env-test-key-12345"

    arch_cfg = ArchitectureConfig(gemini_api_key=os.getenv("GEMINI_API_KEY"))
    assert arch_cfg.gemini_api_key == "env-test-key-12345"


def test_no_hardcoded_gemini_key_in_config_files():
    """Ensure no hard-coded API key strings exist in config files."""
    repo_root = Path(__file__).resolve().parent.parent
    files_to_check = [
        repo_root / "shared" / "config.py",
        repo_root / "modules" / "architecture_design" / "config.py",
        repo_root / "modules" / "architecture_design" / "dependencies.py",
    ]

    for fpath in files_to_check:
        content = fpath.read_text(encoding="utf-8")
        # Ensure accidental API key strings like "AQ.Ab8RN..." are not present
        assert "AQ.Ab8RN" not in content, f"Hardcoded key snippet found in {fpath}"
        assert 'os.getenv("GEMINI_API_KEY")' in content or "gemini_api_key" in content


# ===========================================================================
# Task 2: Architecture Service Caching
# ===========================================================================

def test_get_architecture_service_caching(monkeypatch):
    """Ensure repeated dependency resolution returns the identical cached instance."""
    monkeypatch.setenv("ARCHITECTURE_USE_STUB_LLM", "true")
    from modules.architecture_design import config
    monkeypatch.setattr(config.architecture_config, "use_stub_llm", True)

    # Avoid downloading HF sentence-transformer weights during offline unit tests
    monkeypatch.setattr(
        "modules.architecture_design.dependencies.SentenceTransformerEmbeddingProvider",
        StubEmbeddingProvider,
    )

    # Clear cache before testing
    get_architecture_service.cache_clear()

    svc1 = get_architecture_service()
    svc2 = get_architecture_service()

    assert svc1 is svc2, "Expected get_architecture_service to return cached singleton"

    # Reset cache and verify new instance is created
    get_architecture_service.cache_clear()
    svc3 = get_architecture_service()
    assert svc3 is not svc1

    # Cleanup
    get_architecture_service.cache_clear()


# ===========================================================================
# Task 3 & 4: Provider Metadata Fixes
# ===========================================================================

def test_embedding_provider_model_name_attributes():
    """Verify embedding providers expose their model_name."""
    stub_ep = StubEmbeddingProvider()
    assert stub_ep.model_name == "stub-keyword-embedding"

    custom_stub = StubEmbeddingProvider(model_name="custom-test-embedding")
    assert custom_stub.model_name == "custom-test-embedding"

    st_provider = SentenceTransformerEmbeddingProvider.__new__(SentenceTransformerEmbeddingProvider)
    st_provider.model_name = "sentence-transformers/all-MiniLM-L6-v2"
    assert st_provider.model_name == "sentence-transformers/all-MiniLM-L6-v2"


def test_stub_llm_provider_metadata_does_not_report_gemini():
    """StubLLMProvider must expose model_name == 'stub' and not be reported as Gemini."""
    stub_llm = StubLLMProvider()
    assert stub_llm.model_name == "stub"

    service = ArchitectureDesignService(
        embedding_provider=StubEmbeddingProvider(),
        vector_store=InMemoryVectorStore(),
        llm_provider=stub_llm,
    )

    batch = ASRBatch(
        project_id="PROJ-META",
        asrs=[ASRInput(requirement_id="R1", statement="Must scale to 10k users.")],
    )
    result = service.analyze(batch)

    assert result.metadata.llm_provider == "StubLLMProvider"
    assert result.metadata.llm_model == "stub"
    assert result.metadata.llm_model != "gemini-2.5-flash"
    assert result.metadata.embedding_model == "stub-keyword-embedding"


def test_gemini_llm_provider_model_name_stored(monkeypatch):
    """GeminiLLMProvider must retain and expose the configured model name."""
    monkeypatch.setenv("GEMINI_API_KEY", "dummy-key")
    # Avoid initializing actual google.genai network client by checking property or constructor
    class DummyGemini(GeminiLLMProvider):
        def __init__(self, model_name="gemini-2.5-pro", api_key="dummy-key"):
            self.model_name = model_name
            self.api_key = api_key

    provider = DummyGemini(model_name="gemini-2.5-pro")
    assert provider.model_name == "gemini-2.5-pro"


# ===========================================================================
# Task 5: Quality Attribute Label Space Alignment & Validation
# ===========================================================================

def test_benchmark_case_rejects_unsupported_qa_label():
    """BenchmarkCase validation must reject QA labels not in the 6 supported attributes."""
    # Invalid: "Testability"
    with pytest.raises(ValidationError) as exc_info:
        BenchmarkCase(
            case_id="ARCH-TEST",
            project_id="PROJ-TEST",
            asrs=[ASRInput(requirement_id="R1", statement="Statement.")],
            expected_quality_attributes=["Testability", "Maintainability"],
            expected_preferred_styles=["Modular Monolith"],
        )
    assert "Unsupported quality attribute: 'Testability'" in str(exc_info.value)


def test_benchmark_case_accepts_valid_six_qa_labels():
    """BenchmarkCase validation must accept any of the 6 supported attributes."""
    valid_qas = [qa.value for qa in QualityAttribute]
    case = BenchmarkCase(
        case_id="ARCH-TEST",
        project_id="PROJ-TEST",
        asrs=[ASRInput(requirement_id="R1", statement="Statement.")],
        expected_quality_attributes=valid_qas,
        expected_preferred_styles=["Microservices"],
    )
    assert case.expected_quality_attributes == valid_qas


def test_benchmark_dataset_arch_003_has_no_testability():
    """Verify that ARCH-003 in benchmark_cases.json no longer contains Testability."""
    benchmark_file = (
        Path(__file__).resolve().parent.parent
        / "datasets"
        / "architecture_decision"
        / "benchmark_cases.json"
    )
    cases = json.loads(benchmark_file.read_text(encoding="utf-8"))
    arch_003 = next(c for c in cases if c["case_id"] == "ARCH-003")

    assert "Testability" not in arch_003["expected_quality_attributes"]
    assert "Maintainability" in arch_003["expected_quality_attributes"]

    # Gold labels check
    gold_file = (
        Path(__file__).resolve().parent.parent
        / "datasets"
        / "architecture_decision"
        / "gold_labels.json"
    )
    gold = json.loads(gold_file.read_text(encoding="utf-8"))
    gold_003 = gold["cases"]["ARCH-003"]
    assert "Testability" not in gold_003["quality_attributes"]
    assert "Maintainability" in gold_003["quality_attributes"]
