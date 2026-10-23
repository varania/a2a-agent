"""Command line A2A client.

Usage:
    uv run a2a-agent-client "What is (120 * 3) / 4?"
    uv run a2a-agent-client --url http://localhost:9999 --context-id demo "hi"
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from a2a.client import create_client
from a2a.helpers import get_stream_response_text, new_text_message
from a2a.types import Role, SendMessageRequest

DEFAULT_URL = "http://127.0.0.1:9999"


async def send_message(url: str, text: str, context_id: str | None = None) -> int:
    """Send one message and print the streamed answer. Returns an exit code."""
    client = await create_client(url)
    try:
        request = SendMessageRequest(
            message=new_text_message(
                text,
                context_id=context_id,
                role=Role.ROLE_USER,
            )
        )
        async for response in client.send_message(request):
            chunk = get_stream_response_text(response)
            if chunk:
                print(chunk, end="", flush=True)
        print()
    finally:
        await client.close()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="a2a-agent-client",
        description="Send a message to an A2A agent and print the response.",
    )
    parser.add_argument("message", nargs="+", help="Message to send.")
    parser.add_argument(
        "--url",
        default=DEFAULT_URL,
        help=f"Agent base URL (default: {DEFAULT_URL}).",
    )
    parser.add_argument(
        "--context-id",
        default=None,
        help="Reuse an A2A context id to continue a conversation.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    message = " ".join(args.message)
    try:
        raise SystemExit(asyncio.run(send_message(args.url, message, args.context_id)))
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    main()
