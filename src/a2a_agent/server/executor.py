"""Bridge between the A2A protocol and the LangChain agent."""

from __future__ import annotations

import logging
import uuid

from a2a.helpers import new_task_from_user_message, new_text_message, new_text_part
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import InvalidParamsError, UnsupportedOperationError

from a2a_agent.agent import LangChainAgent

logger = logging.getLogger(__name__)

ARTIFACT_NAME = "response"
EMPTY_RESPONSE = "The agent did not produce an answer."


class LangChainAgentExecutor(AgentExecutor):
    """Execute A2A tasks with :class:`~a2a_agent.agent.LangChainAgent`.

    Streaming responses are published as incremental artifact chunks
    (``append=True``) followed by a final one (``last_chunk=True``). This is
    what A2A ``message/stream`` clients consume to render tokens as they are
    generated.
    """

    def __init__(self, agent: LangChainAgent) -> None:
        self.agent = agent

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        query = (context.get_user_input() or "").strip()
        if not query:
            raise InvalidParamsError(message="The request does not contain any text.")

        task = context.current_task
        if task is None:
            message = context.message
            if message is None:
                raise InvalidParamsError(
                    message="The request does not contain a message."
                )
            task = new_task_from_user_message(message)
            await event_queue.enqueue_event(task)

        updater = TaskUpdater(event_queue, task.id, task.context_id)
        await updater.start_work()

        artifact_id = uuid.uuid4().hex
        first_chunk = True
        pending: str | None = None

        try:
            async for chunk in self.agent.astream(query, task.context_id):
                # One-chunk lookahead so the final chunk can be flagged
                # ``last_chunk=True``.
                if pending is not None:
                    await self._append_text(
                        updater, artifact_id, pending, first=first_chunk
                    )
                    first_chunk = False
                pending = chunk.text

            if pending is None:
                pending = EMPTY_RESPONSE
            await self._append_text(
                updater, artifact_id, pending, first=first_chunk, last=True
            )
            await updater.complete()
        except Exception as exc:
            logger.exception("Agent execution failed for task %s", task.id)
            await updater.failed(
                new_text_message(
                    f"Agent error: {exc}",
                    context_id=task.context_id,
                    task_id=task.id,
                )
            )

    @staticmethod
    async def _append_text(
        updater: TaskUpdater,
        artifact_id: str,
        text: str,
        *,
        first: bool = False,
        last: bool = False,
    ) -> None:
        await updater.add_artifact(
            parts=[new_text_part(text)],
            artifact_id=artifact_id,
            name=ARTIFACT_NAME,
            append=not first,
            last_chunk=last,
        )

    async def cancel(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        raise UnsupportedOperationError(message="Cancellation is not supported.")
