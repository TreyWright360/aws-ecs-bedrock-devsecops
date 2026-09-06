import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "region" in data
    assert "timestamp" in data


def test_analyze_summarize():
    payload = {
        "text": "Cloud computing allows organizations to scale workloads dynamically without managing physical data centers.",
        "task": "summarize"
    }
    response = client.post("/api/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["task"] == "summarize"
    assert len(data["result"]) > 0
    assert data["source"] in ["aws-bedrock", "simulation-fallback"]


def test_analyze_invalid_input():
    # Empty string should fail Pydantic validation (422)
    response = client.post("/api/analyze", json={"text": "hi", "task": "summarize"})
    assert response.status_code == 422
