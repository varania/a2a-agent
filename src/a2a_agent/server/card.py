"""Agent Card: the public description of the agent (A2A discovery)."""

from __future__ import annotations

from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentSkill,
)

from a2a_agent.config import Settings

DEFAULT_INPUT_MODES = ["text/plain"]
DEFAULT_OUTPUT_MODES = ["text/plain"]

SKILLS = [
    AgentSkill(
        id="general_assistant",
        name="General assistant",
        description=(
            "Answers general questions, performs exact arithmetic with the "
            "calculator tool and reports the current date/time in any time zone."
        ),
        tags=["general", "assistant", "langchain", "calculator", "datetime"],
        examples=[
            "What is (120 * 3) / 4?",
            "What time is it in Europe/Madrid?",
            "Summarise the A2A protocol in three bullets.",
        ],
        input_modes=DEFAULT_INPUT_MODES,
        output_modes=DEFAULT_OUTPUT_MODES,
    )
]


def build_agent_card(settings: Settings) -> AgentCard:
    """Build the public :class:`AgentCard` for this deployment.

    The card advertises both supported HTTP transports (JSON-RPC and
    HTTP+JSON/REST), so any A2A-compliant client can talk to the agent.
    """
    base_url = f"{settings.base_url}/"

    return AgentCard(
        name=settings.agent_name,
        description=settings.agent_description,
        version=settings.agent_version,
        supported_interfaces=[
            AgentInterface(
                url=base_url,
                protocol_binding="JSONRPC",
                protocol_version="1.0",
            ),
            AgentInterface(
                url=base_url,
                protocol_binding="HTTP+JSON",
                protocol_version="1.0",
            ),
        ],
        capabilities=AgentCapabilities(
            streaming=settings.streaming,
            push_notifications=False,
        ),
        default_input_modes=DEFAULT_INPUT_MODES,
        default_output_modes=DEFAULT_OUTPUT_MODES,
        skills=SKILLS,
    )
