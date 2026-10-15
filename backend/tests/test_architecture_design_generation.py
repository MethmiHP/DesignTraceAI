import pytest
from modules.architecture_design.schemas import (
    ASRBatch,
    ASRInput,
    HighLevelArchitectureDesign,
    ArchitectureComponent,
    ArchitectureConnection,
    ArchitectureRecommendation,
    RecommendationOutput,
    ArchitectureEvaluation,
)
from modules.architecture_design.service import ArchitectureDesignService
from modules.architecture_design.retrieval.embedding_provider import BaseEmbeddingProvider
from modules.architecture_design.retrieval.vector_store import InMemoryVectorStore
from modules.architecture_design.llm.provider import BaseLLMProvider


class MockEmbedder(BaseEmbeddingProvider):
    def embed(self, texts: list[str]) -> list[list[float]]:
        # Dummy 2D vectors
        return [[1.0, 0.0] for _ in texts]


class MockDesignLLMProvider(BaseLLMProvider):
    def __init__(self, raw_design: HighLevelArchitectureDesign):
        self.raw_design = raw_design

    def generate(self, prompt: str) -> str:
        return ""

    def generate_structured(self, prompt: str, schema_class: type) -> any:
        if schema_class == HighLevelArchitectureDesign:
            return self.raw_design
        if schema_class == ArchitectureRecommendation:
            return ArchitectureRecommendation(
                selected_style="Microservices",
                score=1.0,
                rationale="Mock",
                key_quality_attributes=[],
                strengths=[],
                weaknesses=[],
                tradeoffs=[],
                rejected_alternatives=[],
                evidence_ids=[],
                review_required=False
            )
        return None


@pytest.fixture
def sample_batch() -> ASRBatch:
    return ASRBatch(
        project_id="P-TEST",
        asrs=[
            ASRInput(requirement_id="REQ-1", statement="Must scale."),
            ASRInput(requirement_id="REQ-2", statement="Must be secure.")
        ]
    )


def test_guardrails_remove_hallucinated_requirements(sample_batch: ASRBatch) -> None:
    """If the LLM invents entirely fake requirement IDs, they should be stripped."""
    bad_comp = ArchitectureComponent(
        component_id="api_gw",
        name="API Gateway",
        responsibility="Routes traffic",
        component_type="gateway",
        grounding_type="architecture_structural",
        related_requirements=["REQ-1", "REQ-999_FAKE"],
    )
    mock_design = HighLevelArchitectureDesign(
        style="Microservices",
        components=[bad_comp],
        connections=[],
        design_rationale="Tested rationale.",
        evidence_ids=[]
    )
    
    svc = ArchitectureDesignService(
        embedding_provider=MockEmbedder(),
        vector_store=InMemoryVectorStore(),
        llm_provider=MockDesignLLMProvider(mock_design)
    )
    
    out = svc.generate_design(sample_batch)
    comp = out.design.components[0]
    
    assert "REQ-1" in comp.related_requirements
    assert "REQ-999_FAKE" not in comp.related_requirements


def test_guardrails_drop_invalid_connections(sample_batch: ASRBatch) -> None:
    """If the LLM draws a connection to a non-existent component, it must be dropped."""
    c1 = ArchitectureComponent(
        component_id="db",
        name="Database",
        responsibility="Stores data",
        component_type="database",
        grounding_type="architecture_structural",
    )
    
    # Connection target 'cache' does not exist in components list!
    bad_conn = ArchitectureConnection(source="db", target="cache", relationship="reads")
    
    mock_design = HighLevelArchitectureDesign(
        style="Microservices",
        components=[c1],
        connections=[bad_conn],
        design_rationale="Tested rationale."
    )
    
    svc = ArchitectureDesignService(
        embedding_provider=MockEmbedder(),
        vector_store=InMemoryVectorStore(),
        llm_provider=MockDesignLLMProvider(mock_design)
    )
    
    out = svc.generate_design(sample_batch)
    assert len(out.design.connections) == 0, "Invalid connection was not dropped."


def test_plantuml_generation_is_deterministic(sample_batch: ASRBatch) -> None:
    """Ensure PlantUML wrapper strings and safe aliases are created accurately."""
    c1 = ArchitectureComponent(
        component_id="web-ui",
        name="Web Application",
        responsibility="UI",
        component_type="component",
        grounding_type="architecture_structural",
    )
    c2 = ArchitectureComponent(
        component_id="db_main",
        name="Main DB",
        responsibility="Data",
        component_type="database",
        grounding_type="architecture_structural",
    )
    valid_conn = ArchitectureConnection(source="web-ui", target="db_main", relationship="reads DB")
    
    mock_design = HighLevelArchitectureDesign(
        style="Microservices",
        components=[c1, c2],
        connections=[valid_conn],
        design_rationale="Tested."
    )
    
    svc = ArchitectureDesignService(
        embedding_provider=MockEmbedder(),
        vector_store=InMemoryVectorStore(),
        llm_provider=MockDesignLLMProvider(mock_design)
    )
    
    out = svc.generate_design(sample_batch)
    puml = out.plantuml
    
    assert puml.startswith("@startuml")
    assert puml.endswith("@enduml")
    assert "database \"Main DB\" as dbmain" in puml
    assert "component \"Web Application\" as webui" in puml
    assert "webui --> dbmain : reads DB" in puml


def test_guardrails_drop_unsupported_business_components(sample_batch: ASRBatch) -> None:
    """If a component is requirement_derived but ends up with no valid requirements, it is dropped."""
    c1 = ArchitectureComponent(
        component_id="auth",
        name="Auth Service",
        responsibility="Auth",
        component_type="service",
        grounding_type="requirement_derived",
        related_requirements=["REQ-FAKE"], # Will be stripped
        related_quality_attributes=[],
    )
    
    mock_design = HighLevelArchitectureDesign(
        style="Microservices",
        components=[c1],
        connections=[],
        design_rationale="Tested rationale."
    )
    
    svc = ArchitectureDesignService(
        embedding_provider=MockEmbedder(),
        vector_store=InMemoryVectorStore(),
        llm_provider=MockDesignLLMProvider(mock_design)
    )
    
    out = svc.generate_design(sample_batch)
    
    # The component should have been completely dropped because it lost all its related_requirements
    assert len(out.design.components) == 0, "Domain component without valid ASRs was not dropped."
