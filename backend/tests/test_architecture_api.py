"""FastAPI Router Tests – Architecture Decision Agent Milestone 7.3."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app import app
from modules.architecture_design.dependencies import get_architecture_service
from modules.architecture_design.service import ArchitectureDesignService
from modules.architecture_design.retrieval.embedding_provider import StubEmbeddingProvider
from modules.architecture_design.retrieval.vector_store import InMemoryVectorStore
from modules.architecture_design.llm.provider import StubLLMProvider
from modules.architecture_design.schemas import (
    ArchitectureRecommendation,
    HighLevelArchitectureDesign,
    ArchitectureComponent,
)


@pytest.fixture
def stub_service() -> ArchitectureDesignService:
    stub_rec = ArchitectureRecommendation(
        selected_style="Event-Driven Architecture",
        score=92.5,
        rationale="Decoupled streaming for high throughput.",
        key_quality_attributes=["Scalability", "Reliability"],
        strengths=["High scalability", "Fault isolation"],
        weaknesses=["Eventual consistency overhead"],
        tradeoffs=["Asynchronous complexity"],
        rejected_alternatives=[],
        evidence_ids=["KB-001"],
        review_required=False,
    )

    stub_design = HighLevelArchitectureDesign(
        style="Event-Driven Architecture",
        components=[
            ArchitectureComponent(
                component_id="event_ingestor",
                name="Event Ingestion Worker",
                responsibility="Ingests incoming order streams",
                component_type="service",
                grounding_type="requirement_derived",
                related_requirements=["REQ-01"],
                related_quality_attributes=["Scalability"],
            )
        ],
        connections=[],
        design_rationale="High throughput reactive design.",
        evidence_ids=["KB-001"],
    )

    llm = StubLLMProvider()
    original_generate_structured = llm.generate_structured

    def mock_structured(prompt: str, schema):
        if schema.__name__ == "ArchitectureRecommendation":
            return stub_rec
        if schema.__name__ == "HighLevelArchitectureDesign":
            return stub_design
        return original_generate_structured(prompt, schema)

    llm.generate_structured = mock_structured

    return ArchitectureDesignService(
        embedding_provider=StubEmbeddingProvider(),
        vector_store=InMemoryVectorStore(),
        llm_provider=llm,
    )


@pytest.fixture
def client(stub_service: ArchitectureDesignService) -> TestClient:
    app.dependency_overrides[get_architecture_service] = lambda: stub_service
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_asr_payload() -> dict:
    return {
        "project_id": "TEST-PROJ",
        "asrs": [
            {
                "requirement_id": "REQ-01",
                "statement": "The system must scale to process 20,000 concurrent events per second.",
            },
            {
                "requirement_id": "REQ-02",
                "statement": "Service outages in reporting must not halt transaction recording or cause system failure.",
            },
        ],
    }


@pytest.fixture
def sample_project_payload() -> dict:
    return {
        "project_id": "TEST-PROJ",
        "requirements": [
            {
                "requirement_id": "REQ-01",
                "statement": "The system must scale to process 20,000 concurrent events per second.",
                "requirement_type": "non_functional",
            },
            {
                "requirement_id": "REQ-02",
                "statement": "Service outages in reporting must not halt transaction recording or cause system failure.",
                "requirement_type": "non_functional",
            },
            {
                "requirement_id": "FR-01",
                "statement": "The system shall ingest and process incoming order events.",
                "requirement_type": "functional",
            },
        ],
        "asrs": [
            {
                "requirement_id": "REQ-01",
                "statement": "The system must scale to process 20,000 concurrent events per second.",
            },
            {
                "requirement_id": "REQ-02",
                "statement": "Service outages in reporting must not halt transaction recording or cause system failure.",
            },
        ],
    }


def test_classify_endpoint(client: TestClient, sample_asr_payload: dict):
    response = client.post("/api/architecture/classify", json=sample_asr_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["project_id"] == "TEST-PROJ"
    assert len(data["classifications"]) == 2
    assert "quality_profile" in data
    assert data["quality_profile"]["Scalability"] >= 1


def test_evaluate_endpoint(client: TestClient, sample_asr_payload: dict):
    response = client.post("/api/architecture/evaluate", json=sample_asr_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["project_id"] == "TEST-PROJ"
    assert len(data["architecture_evaluations"]) > 0
    assert data["architecture_evaluations"][0]["rank"] == 1


def test_retrieve_endpoint(client: TestClient, sample_asr_payload: dict):
    response = client.post("/api/architecture/retrieve?top_k=3", json=sample_asr_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["project_id"] == "TEST-PROJ"
    assert len(data["evidence"]) <= 3
    assert all("knowledge_id" in item for item in data["evidence"])


def test_recommend_endpoint(client: TestClient, sample_asr_payload: dict):
    response = client.post("/api/architecture/recommend?top_k=2", json=sample_asr_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["project_id"] == "TEST-PROJ"
    assert data["recommendation"]["selected_style"] == "Event-Driven Architecture"
    assert "rationale" in data["recommendation"]


def test_design_endpoint(client: TestClient, sample_project_payload: dict):
    response = client.post("/api/architecture/design?top_k=2", json=sample_project_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["project_id"] == "TEST-PROJ"
    assert "design" in data
    assert "plantuml" in data
    assert "@startuml" in data["plantuml"]
    assert "@enduml" in data["plantuml"]
    component = data["design"]["components"][0]
    assert component["grounding_type"] == "requirement_derived"
    assert component["related_requirements"] == ["REQ-01"]


def test_analyze_endpoint(client: TestClient, sample_project_payload: dict):
    response = client.post("/api/architecture/analyze?top_k=2", json=sample_project_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["project_id"] == "TEST-PROJ"
    assert "classification" in data
    assert "scoring" in data
    assert "retrieval" in data
    assert "result" in data
    assert "metadata" in data
    assert data["metadata"]["pipeline_version"] == "M7.3"
    assert data["metadata"]["execution_time_ms"] >= 0.0
    assert data["metadata"]["llm_provider"] == "StubLLMProvider"
    assert data["metadata"]["llm_model"] == "stub"
    assert data["metadata"]["embedding_model"] == "stub-keyword-embedding"
    assert data["result"]["recommendation"]["selected_style"] == "Event-Driven Architecture"


def test_empty_asr_batch_rejected_by_schema(client: TestClient):
    payload = {"project_id": "TEST-PROJ", "asrs": []}
    response = client.post("/api/architecture/classify", json=payload)
    assert response.status_code == 422


def test_invalid_schema_returns_422(client: TestClient):
    payload = {"project_id": "TEST-PROJ", "asrs": "not-a-list"}
    response = client.post("/api/architecture/classify", json=payload)
    assert response.status_code == 422


def test_design_requires_all_requirements(client: TestClient, sample_asr_payload: dict):
    response = client.post("/api/architecture/design", json=sample_asr_payload)
    assert response.status_code == 422


def test_analyze_rejects_asr_not_present_in_requirements(client: TestClient):
    payload = {
        "project_id": "TEST-PROJ",
        "requirements": [
            {
                "requirement_id": "FR-01",
                "statement": "Users can submit orders.",
                "requirement_type": "functional",
            }
        ],
        "asrs": [
            {
                "requirement_id": "NFR-99",
                "statement": "The system must scale horizontally.",
            }
        ],
    }
    response = client.post("/api/architecture/analyze", json=payload)
    assert response.status_code == 422


def test_internal_error_does_not_leak_secrets(client: TestClient, sample_asr_payload: dict):
    class FailingService:
        def run(self, batch):
            raise RuntimeError(
                "Database connection string: postgresql://admin:secretpass@db.prod:5432/db"
            )

    app.dependency_overrides[get_architecture_service] = lambda: FailingService()
    response = client.post("/api/architecture/classify", json=sample_asr_payload)
    assert response.status_code == 500
    data = response.json()
    assert data["detail"]["error"] == "INTERNAL_PIPELINE_ERROR"
    assert "secretpass" not in response.text
    assert "postgresql://" not in response.text
