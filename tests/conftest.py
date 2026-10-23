"""Shared pytest fixtures."""

from __future__ import annotations

import pytest

from a2a_agent.config import Settings


@pytest.fixture
def settings() -> Settings:
    """Deterministic settings isolated from the developer environment."""
    return Settings(
        _env_file=None,
        agent_name="Test Agent",
        agent_description="Agent used in the test suite",
        host="127.0.0.1",
        port=1234,
        public_url=None,
        model="openai:test-model",
        log_level="WARNING",
    )
