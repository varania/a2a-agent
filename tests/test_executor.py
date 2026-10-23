"""Tests for the A2A ⇄ LangChain executor."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import pytest
from a2a.helpers import get_artifact_text, new_text_message
from a2a.server.agent_execution import RequestContext
from a2a.server.context import ServerCallContext
from a2a.server.events import EventQueue
from a2a.types import (
    InvalidParamsError,
    Role,
    SendMessageRequest,
    Task,
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatusUpdateEvent,
)

from a2a_agent.agent import AgentChunk
from a2a_agent.server.executor import LangChainAgentExecutor


class FakeAgent:
    """Stand-in for :class:`LangChainAgent` with deterministic output."""

    def __init__(self, chunks: list[str] | None = None, error: Exception | None = None):
        self.chunks = chunks or []
        self.error = error

    async def astream(self, query: str, context_id: str) -> AsyncIterator[AgentChunk]:
        if self.error is not None:
            raise self.error
        for text in self.chunks:
            yield AgentChunk(text=text)


class CollectingEventQueue(EventQueue):
    """Event queue that records everything published by the executor."""

    def __init__(self) -> None:
        self.events: list[Any] = []

    async def enqueue_event(self, event: Any) -> None:
        self.events.append(event)


def make_context(text: str = "hello") -> RequestContext:
    request = SendMessageRequest(
        message=new_text_message(text, role=Role.ROLE_USER),
    )
    return RequestContext(call_context=ServerCallContext(), request=request)


def executor_for(agent: FakeAgent) -> LangChainAgentExecutor:
    # FakeAgent implements the only method used by the executor.
    return LangChainAgentExecutor(agent)  # type: ignore[arg-type]


async def test_executor_publishes_task_and_completed_status() -> None:
    queue = CollectingEventQueue()

    await executor_for(FakeAgent(["Hello", " world"])).execute(make_context(), queue)

    tasks = [event for event in queue.events if isinstance(event, Task)]
    statuses = [
        event for event in queue.events if isinstance(event, TaskStatusUpdateEvent)
    ]

    assert len(tasks) == 1
    assert tasks[0].context_id == tasks[0].context_id  # generated and consistent
    assert statuses[0].status.state == TaskState.TASK_STATE_WORKING
    assert statuses[-1].status.state == TaskState.TASK_STATE_COMPLETED


async def test_executor_streams_artifacts_as_chunks() -> None:
    queue = CollectingEventQueue()

    await executor_for(FakeAgent(["Hello", " world"])).execute(make_context(), queue)

    artifacts = [
        event for event in queue.events if isinstance(event, TaskArtifactUpdateEvent)
    ]

    assert [artifact.append for artifact in artifacts] == [False, True]
    assert artifacts[-1].last_chunk is True
    assert "".join(get_artifact_text(a.artifact) for a in artifacts) == "Hello world"


async def test_executor_handles_empty_model_output() -> None:
    queue = CollectingEventQueue()

    await executor_for(FakeAgent([])).execute(make_context(), queue)

    artifacts = [
        event for event in queue.events if isinstance(event, TaskArtifactUpdateEvent)
    ]
    assert get_artifact_text(artifacts[0].artifact)


async def test_executor_marks_task_failed_on_agent_error() -> None:
    queue = CollectingEventQueue()

    await executor_for(FakeAgent(error=RuntimeError("boom"))).execute(
        make_context(), queue
    )

    statuses = [
        event for event in queue.events if isinstance(event, TaskStatusUpdateEvent)
    ]
    assert statuses[-1].status.state == TaskState.TASK_STATE_FAILED
    failure_message = statuses[-1].status.message
    assert "boom" in failure_message.parts[0].text
    assert failure_message.parts[0].media_type == ""


async def test_executor_rejects_empty_messages() -> None:
    queue = CollectingEventQueue()

    with pytest.raises(InvalidParamsError):
        await executor_for(FakeAgent(["never used"])).execute(
            make_context("   "), queue
        )
