"""Structured logging configuration for FieldMind.

Configures the root `fieldmind` logger to emit JSON-formatted records in
production and a human-friendly format in development.  Call
`configure_logging()` once at application startup.
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any


class _JsonFormatter(logging.Formatter):
    """Emit each log record as a single JSON line."""

    _ALWAYS_FIELDS = (
        "levelname",
        "name",
        "message",
        "exc_info",
    )

    def format(self, record: logging.LogRecord) -> str:
        record.message = record.getMessage()

        payload: dict[str, Any] = {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.message,
        }

        # Attach any extra fields the caller supplied
        for key, value in record.__dict__.items():
            if key in (
                "args",
                "asctime",
                "created",
                "exc_info",
                "exc_text",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "message",
                "module",
                "msecs",
                "msg",
                "name",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "stack_info",
                "thread",
                "threadName",
                "taskName",
            ):
                continue
            payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


class _DevFormatter(logging.Formatter):
    """Human-readable formatter for local development."""

    _FMT = "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s"
    _DATE = "%H:%M:%S"

    def __init__(self) -> None:
        super().__init__(fmt=self._FMT, datefmt=self._DATE)


def configure_logging(level: str = "INFO", json_format: bool = False) -> None:
    """Set up the `fieldmind` logger hierarchy.

    Args:
        level:       Logging level string, e.g. ``"DEBUG"`` or ``"INFO"``.
        json_format: Emit JSON lines instead of the dev-friendly format.
                     Automatically enabled when ``FIELDMIND_ENV=production``.
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    formatter: logging.Formatter = (
        _JsonFormatter() if json_format else _DevFormatter()
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Configure the root fieldmind logger
    root = logging.getLogger("fieldmind")
    root.setLevel(numeric_level)
    root.handlers.clear()
    root.addHandler(handler)
    root.propagate = False

    # Quieten noisy third-party loggers in production
    for noisy in ("uvicorn.access", "httpx", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
