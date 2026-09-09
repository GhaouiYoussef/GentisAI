from __future__ import annotations

import json
import logging
import re
import time


_REDACTIONS = (
    (re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.I), "[UUID]"),
    (re.compile(r"[\w.+-]+@[\w.-]+\.[a-z]{2,}", re.I), "[EMAIL]"),
    (re.compile(r"\bBearer\s+[^\s\"'<>]+", re.I), "Bearer [REDACTED]"),
)


def redact_log_text(text: str) -> str:
    """Mask common identifiers; this is not a general PHI sanitizer."""
    for pattern, replacement in _REDACTIONS:
        text = pattern.sub(replacement, text)
    return text


class RedactingFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return redact_log_text(super().format(record))


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created)),
            "level": record.levelname,
            "logger": redact_log_text(record.name),
            "message": redact_log_text(record.getMessage()),
        }
        if record.exc_info:
            payload["exception"] = redact_log_text(self.formatException(record.exc_info))
        return json.dumps(payload)


def configure_logging(level: int = logging.INFO, json_logs: bool = True) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter() if json_logs else RedactingFormatter())
    logging.basicConfig(level=level, handlers=[handler], force=True)
