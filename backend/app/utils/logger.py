import json
import logging
import sys
from contextlib import contextmanager
from contextvars import ContextVar, Token
from datetime import datetime, timezone
from typing import Any


request_id_context: ContextVar[str | None] = ContextVar("request_id", default=None)
session_id_context: ContextVar[str | None] = ContextVar("session_id", default=None)

_RESERVED_RECORD_FIELDS = {
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
    "module",
    "msecs",
    "message",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "thread",
    "threadName",
}


def set_request_id(request_id: str) -> Token:
    return request_id_context.set(request_id)


def reset_request_id(token: Token) -> None:
    request_id_context.reset(token)


def get_request_id() -> str | None:
    return request_id_context.get()


def set_session_id(session_id: str) -> Token:
    return session_id_context.set(session_id)


def reset_session_id(token: Token) -> None:
    session_id_context.reset(token)


def get_session_id() -> str | None:
    return session_id_context.get()


@contextmanager
def logging_context(
    *,
    request_id: str | None = None,
    session_id: str | None = None,
):
    request_token: Token | None = None
    session_token: Token | None = None

    try:
        if request_id is not None:
            request_token = set_request_id(request_id)
        if session_id is not None:
            session_token = set_session_id(session_id)
        yield
    finally:
        if session_token is not None:
            reset_session_id(session_token)
        if request_token is not None:
            reset_request_id(request_token)


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "event": getattr(record, "event", record.getMessage()),
            "request_id": getattr(record, "request_id", None) or get_request_id(),
            "session_id": getattr(record, "session_id", None) or get_session_id(),
            "duration_ms": getattr(record, "duration_ms", None),
            "status": getattr(record, "status", None),
        }

        for key, value in record.__dict__.items():
            if key.startswith("_") or key in _RESERVED_RECORD_FIELDS:
                continue
            if key in payload or key in {"request_id", "session_id"}:
                continue
            payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


class StructuredLogger:
    def __init__(self, logger: logging.Logger):
        self._logger = logger

    def debug(self, event: str, **fields: Any) -> None:
        self._log(logging.DEBUG, event, **fields)

    def info(self, event: str, **fields: Any) -> None:
        self._log(logging.INFO, event, **fields)

    def warning(self, event: str, **fields: Any) -> None:
        self._log(logging.WARNING, event, **fields)

    def error(self, event: str, **fields: Any) -> None:
        self._log(logging.ERROR, event, **fields)

    def exception(self, event: str, **fields: Any) -> None:
        self._log(logging.ERROR, event, exc_info=True, **fields)

    def _log(self, level: int, event: str, **fields: Any) -> None:
        request_id = fields.pop("request_id", None) or get_request_id()
        session_id = fields.pop("session_id", None) or get_session_id()
        duration_ms = fields.pop("duration_ms", None)
        status = fields.pop("status", None)
        exc_info = fields.pop("exc_info", False)

        extra = {
            "event": event,
            "request_id": request_id,
            "session_id": session_id,
            "duration_ms": duration_ms,
            "status": status,
            **fields,
        }
        self._logger.log(level, event, extra=extra, exc_info=exc_info)


def get_logger(name: str) -> StructuredLogger:
    return StructuredLogger(logging.getLogger(name))


def configure_logging(level: int = logging.INFO) -> None:
    root_logger = logging.getLogger()
    if getattr(root_logger, "_watch_party_logging_configured", False):
        root_logger.setLevel(level)
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonLogFormatter())

    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(level)
    root_logger._watch_party_logging_configured = True
