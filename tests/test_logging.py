import io
import json
import logging

import pytest

from gentis_ai.observability.logging import JsonFormatter, configure_logging


@pytest.mark.parametrize("json_logs", [True, False])
def test_configured_logs_redact_identifiers_and_exception_text(json_logs):
    root = logging.getLogger()
    previous_handlers, previous_level = root.handlers[:], root.level
    output = io.StringIO()
    try:
        configure_logging(json_logs=json_logs)
        root.handlers[0].setStream(output)
        try:
            raise RuntimeError("person@example.com 123e4567-e89b-12d3-a456-426614174000")
        except RuntimeError:
            logging.exception("Request failed: %s", "Bearer secret-token")
        text = output.getvalue()
        for sensitive in ("person@example.com", "123e4567-e89b-12d3-a456-426614174000", "secret-token"):
            assert sensitive not in text
        assert "RuntimeError" in text
        assert "Request failed" in text
        if json_logs:
            assert json.loads(text)["level"] == "ERROR"
    finally:
        root.handlers = previous_handlers
        root.setLevel(previous_level)


def test_json_formatter_preserves_ordinary_diagnostics():
    record = logging.LogRecord("test", logging.INFO, __file__, 1, "Processed %s turns", (3,), None)
    assert json.loads(JsonFormatter().format(record))["message"] == "Processed 3 turns"
