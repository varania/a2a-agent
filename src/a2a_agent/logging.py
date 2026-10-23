"""Logging helpers."""

from __future__ import annotations

import logging

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def configure_logging(level: str = "INFO") -> None:
    """Configure root logging once, with sane defaults for third parties."""
    logging.basicConfig(
        level=level.upper(),
        format=_LOG_FORMAT,
        datefmt=_DATE_FORMAT,
        force=True,
    )
    # HTTP clients are very chatty at INFO level.
    for noisy in ("httpx", "httpcore", "urllib3"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a namespaced logger."""
    return logging.getLogger(name)
