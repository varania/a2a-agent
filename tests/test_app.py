"""Tests for the FastAPI application and its A2A routes."""

from __future__ import annotations

from fastapi.testclient import TestClient

from a2a_agent.config import Settings
from a2a_agent.server.app import create_app


def test_health_endpoint(settings: Settings) -> None:
    with TestClient(create_app(settings)) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "agent": "Test Agent",
        "version": settings.agent_version,
    }


def test_agent_card_is_published(settings: Settings) -> None:
    with TestClient(create_app(settings)) as client:
        response = client.get("/.well-known/agent-card.json")

    assert response.status_code == 200
    card = response.json()
    assert card["name"] == "Test Agent"
    assert any(
        interface["protocolBinding"] == "JSONRPC"
        for interface in card["supportedInterfaces"]
    )


def test_openapi_schema_is_available(settings: Settings) -> None:
    with TestClient(create_app(settings)) as client:
        response = client.get("/openapi.json")

    assert response.status_code == 200
    assert response.json()["info"]["title"] == "Test Agent"
