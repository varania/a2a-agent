"""FastAPI application factory for the A2A server."""

from __future__ import annotations

import logging

from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import (
    add_a2a_routes_to_fastapi,
    create_agent_card_routes,
    create_jsonrpc_routes,
    create_rest_routes,
)
from a2a.server.tasks import InMemoryTaskStore
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from a2a_agent.agent import LangChainAgent
from a2a_agent.config import Settings, get_settings
from a2a_agent.logging import configure_logging
from a2a_agent.server.card import build_agent_card
from a2a_agent.server.executor import LangChainAgentExecutor

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build and configure the FastAPI application.

    Args:
        settings: Optional settings override, mostly useful for tests.
    """
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    agent_card = build_agent_card(settings)

    request_handler = DefaultRequestHandler(
        agent_executor=LangChainAgentExecutor(LangChainAgent(settings)),
        task_store=InMemoryTaskStore(),
        agent_card=agent_card,
    )

    app = FastAPI(
        title=settings.agent_name,
        description=settings.agent_description,
        version=settings.agent_version,
        docs_url="/docs",
        redoc_url=None,
    )

    # Mount the three A2A surfaces:
    #   * GET  /.well-known/agent-card.json  (discovery)
    #   * POST /                             (JSON-RPC 2.0)
    #   * POST /v1/message:send, ...         (HTTP+JSON / REST)
    add_a2a_routes_to_fastapi(
        app,
        agent_card_routes=create_agent_card_routes(agent_card),
        jsonrpc_routes=create_jsonrpc_routes(
            request_handler, "/", enable_v0_3_compat=True
        ),
        rest_routes=create_rest_routes(request_handler),
    )

    @app.get("/health", tags=["ops"], summary="Liveness probe")
    async def health() -> dict[str, str]:
        return {
            "status": "ok",
            "agent": settings.agent_name,
            "version": settings.agent_version,
        }

    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    logger.info(
        "A2A agent %r ready on %s (model=%s)",
        settings.agent_name,
        settings.base_url,
        settings.model,
    )
    return app


# ASGI entry point: `uvicorn a2a_agent.server.app:app`
app = create_app()
