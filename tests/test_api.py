"""API endpoint tests using FastAPI TestClient."""

import pytest
from fastapi.testclient import TestClient

from src.api.routes import create_app
from src.services.research_service import ResearchService


@pytest.fixture
def client():
    # Use mock service for fast, deterministic API tests
    service = ResearchService(mock_mode=True)
    app = create_app(service=service)
    return TestClient(app)


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "primary_model" in data
    assert len(data["available_models"]) >= 1


def test_models_endpoint(client):
    response = client.get("/models")
    assert response.status_code == 200
    data = response.json()
    assert "primary_model" in data
    assert "fallback_models" in data
    assert "all_models" in data


def test_research_endpoint_success(client):
    payload = {
        "question": "What is the economic impact of AI automation in logistics?",
        "max_iterations": 2,
    }
    response = client.post("/research", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "report" in data
    assert data["sources_count"] >= 2
    assert data["evidence_count"] >= 2
    assert "metadata" in data
    assert data["metadata"]["iterations"] >= 1


def test_research_endpoint_validation_error(client):
    # Test request with invalid / too short question
    payload = {"question": "Hi"}
    response = client.post("/research", json=payload)
    assert response.status_code == 422
