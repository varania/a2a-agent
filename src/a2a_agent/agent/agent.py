"""LangChain agent built with ``create_agent`` (LangGraph under the hood)."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk
from langgraph.checkpoint.memory import InMemorySaver

from a2a_agent.agent.prompts import SYSTEM_PROMPT
from a2a_agent.config import Settings
from a2a_agent.tools import TOOLS

logger = logging.getLogger(__name__)


@dataclass(slots=True, frozen=True)
class AgentChunk:
    """A piece of streamed assistant output."""

    text: str


class LangChainAgent:
    """Thin async wrapper around a compiled LangGraph agent.

    The graph (and therefore the LLM client) is created lazily so that the
    server can boot, expose its Agent Card and be tested without credentials.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._checkpointer = InMemorySaver()
        self._graph: Any = None

    # ------------------------------------------------------------------
    # Graph construction
    # ------------------------------------------------------------------
    @property
    def graph(self) -> Any:
        """Return the compiled agent graph, building it on first use."""
        if self._graph is None:
            self._graph = self._build_graph()
        return self._graph

    def _build_model(self) -> BaseChatModel:
        kwargs: dict[str, Any] = {"temperature": self._settings.temperature}
        if self._settings.max_tokens is not None:
            kwargs["max_tokens"] = self._settings.max_tokens
        logger.info("Initialising model %r", self._settings.model)
        return init_chat_model(self._settings.model, **kwargs)

    def _build_graph(self) -> Any:
        return create_agent(
            model=self._build_model(),
            tools=TOOLS,
            system_prompt=SYSTEM_PROMPT,
            checkpointer=self._checkpointer,
        )

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------
    async def astream(self, query: str, context_id: str) -> AsyncIterator[AgentChunk]:
        """Stream the assistant answer for ``query``.

        Conversation state is kept per ``context_id`` (A2A context), which maps
        to a LangGraph checkpoint ``thread_id``. This gives the agent memory
        across the different messages of the same A2A context.
        """
        graph = self.graph
        config = {"configurable": {"thread_id": context_id}}
        inputs = {"messages": [{"role": "user", "content": query}]}

        emitted = False
        async for chunk, _metadata in graph.astream(
            inputs, config=config, stream_mode="messages"
        ):
            if not isinstance(chunk, AIMessageChunk) or chunk.tool_call_chunks:
                continue
            text = chunk.text
            if text:
                emitted = True
                yield AgentChunk(text=text)

        # Models that do not stream (or providers that ignore streaming) still
        # produce a final message in the graph state.
        if not emitted:
            state = await graph.aget_state(config)
            messages = state.values.get("messages", [])
            if messages and isinstance(messages[-1], AIMessage):
                text = messages[-1].text
                if text:
                    yield AgentChunk(text=text)
