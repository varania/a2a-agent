"""Tests for the Agent Card."""

from __future__ import annotations

from a2a_agent.config import Settings
from a2a_agent.server.card import build_agent_card


def test_card_matches_settings(settings: Settings) -> None:
    card = build_agent_card(settings)

    assert card.name == "Test Agent"
    assert card.description == "Agent used in the test suite"
    assert card.version == settings.agent_version
    assert card.capabilities.streaming is True
    assert card.capabilities.push_notifications is False
    assert card.default_input_modes == ["text/plain"]


def test_card_advertises_both_http_transports(settings: Settings) -> None:
    card = build_agent_card(settings)

    interfaces = {i.protocol_binding: i for i in card.supported_interfaces}
    assert set(interfaces) == {"JSONRPC", "HTTP+JSON"}
    for interface in interfaces.values():
        assert interface.url == "http://127.0.0.1:1234/"
        assert interface.protocol_version == "1.0"


def test_public_url_overrides_bind_address(settings: Settings) -> None:
    custom = settings.model_copy(update={"public_url": "https://agents.example.com/"})

    card = build_agent_card(custom)

    assert card.supported_interfaces[0].url == "https://agents.example.com/"


def test_card_exposes_a_skill(settings: Settings) -> None:
    card = build_agent_card(settings)

    skill = card.skills[0]
    assert skill.id == "general_assistant"
    assert "general" in skill.tags
