"""Structured JSON logging.

Deliberately not named logging.py: that would shadow the standard library module.
"""

import json
import logging
from datetime import datetime, timezone

_STANDARD_ATTRS = set(logging.LogRecord("", 0, "", 0, "", (), None).__dict__) | {"message", "asctime"}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Anything passed via `extra=` becomes a top-level field.
        payload.update({k: v for k, v in record.__dict__.items() if k not in _STANDARD_ATTRS})
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging(level: str = "INFO") -> None:
    """Attach one JSON handler to the `app` logger. Safe to call more than once."""
    logger = logging.getLogger("app")
    logger.setLevel(level.upper())
    if not any(getattr(h, "_app_json", False) for h in logger.handlers):
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        handler._app_json = True  # type: ignore[attr-defined]
        logger.addHandler(handler)
