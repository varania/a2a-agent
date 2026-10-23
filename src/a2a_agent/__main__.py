"""``python -m a2a_agent`` / ``a2a-agent`` entry point."""

from __future__ import annotations

import argparse
import os

import uvicorn

from a2a_agent import __version__
from a2a_agent.config import get_settings
from a2a_agent.logging import configure_logging


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="a2a-agent",
        description="Run the A2A agent server.",
    )
    parser.add_argument("--host", help="Bind address (env: A2A_HOST).")
    parser.add_argument("--port", type=int, help="Bind port (env: A2A_PORT).")
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Reload on code changes (development only).",
    )
    parser.add_argument("--version", action="version", version=__version__)
    return parser


def main() -> None:
    args = build_parser().parse_args()

    # CLI flags take precedence over environment variables. They are exported
    # before the app module is imported so the Agent Card advertises the right
    # public URL as well.
    if args.host:
        os.environ["A2A_HOST"] = args.host
    if args.port:
        os.environ["A2A_PORT"] = str(args.port)

    get_settings.cache_clear()
    settings = get_settings()
    configure_logging(settings.log_level)

    uvicorn.run(
        "a2a_agent.server.app:app",
        host=args.host or settings.host,
        port=args.port or settings.port,
        reload=args.reload,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
