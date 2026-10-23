"""Tests for the LangChain agent wrapper (no LLM calls involved)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from types import SimpleNamespace
from typing import Any

from langchain_core.messages import AIMessage, AIMessageChunk

from a2a_agent.agent import LangChainAgent
from a2a_agent.config import Settings


class FakeGraph:
    """Minimal stand-in for a compiled LangGraph agent."""

    def __init__(
        self,
        chunks: list[AIMessageChunk] | None = None,
        final_text: str | None = None,
    ) -> None:
        self.chunks = chunks or []
        self.final_text = final_text

    async def astream(
        self, inputs: Any, config: Any = None, stream_mode: str = "messages"
    ) -> AsyncIterator[tuple[AIMessageChunk, dict[str, Any]]]:
        for chunk in self.chunks:
            yield chunk, {}

    async def aget_state(self, config: Any) -> SimpleNamespace:
        messages = [AIMessage(content=self.final_text)] if self.final_text else []
        return SimpleNamespace(values={"messages": messages})


async def test_astream_forwards_model_text(settings: Settings) -> None:
    agent = LangChainAgent(settings)
    agent._graph = FakeGraph(
        chunks=[AIMessageChunk(content="Hello"), AIMessageChunk(content=" world")]
    )

    chunks = [chunk.text async for chunk in agent.astream("hi", "ctx-1")]

    assert chunks == ["Hello", " world"]


async def test_astream_ignores_tool_call_chunks(settings: Settings) -> None:
    agent = LangChainAgent(settings)
    tool_chunk = AIMessageChunk(
        content="",
        tool_call_chunks=[{"name": "calculator", "args": "{}", "id": "1", "index": 0}],
    )
    agent._graph = FakeGraph(chunks=[tool_chunk, AIMessageChunk(content="42")])

    chunks = [chunk.text async for chunk in agent.astream("hi", "ctx-1")]

    assert chunks == ["42"]


async def test_astream_falls_back_to_final_state(settings: Settings) -> None:
    agent = LangChainAgent(settings)
    agent._graph = FakeGraph(final_text="final answer")

    chunks = [chunk.text async for chunk in agent.astream("hi", "ctx-1")]

    assert chunks == ["final answer"]
