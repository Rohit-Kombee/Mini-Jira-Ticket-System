"""Structured JSON logging with trace_id and request_id."""
import json
import logging
import os
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

# Context vars for trace_id and request_id (set by middleware)
trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")
request_id_var: ContextVar[str] = ContextVar("request_id", default="")
service_name_var: ContextVar[str] = ContextVar("service_name", default="ticket-service")


def get_trace_id() -> str:
    return trace_id_var.get()


def get_request_id() -> str:
    return request_id_var.get()


def set_trace_id(value: str) -> None:
    trace_id_var.set(value)


def set_request_id(value: str) -> None:
    request_id_var.set(value)


def set_service_name(value: str) -> None:
    service_name_var.set(value)


class JsonFormatter(logging.Formatter):
    """Format log records as JSON for Loki."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname.lower(),
            "service": service_name_var.get(),
            "message": record.getMessage(),
            "trace_id": trace_id_var.get() or (getattr(record, "trace_id", None) or ""),
            "request_id": request_id_var.get() or (getattr(record, "request_id", None) or ""),
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        # Include extra fields from record
        for key, value in record.__dict__.items():
            if key not in ("name", "msg", "args", "created", "filename", "funcName", "levelname", "levelno", "lineno", "module", "msecs", "pathname", "process", "processName", "relativeCreated", "stack_info", "exc_info", "message", "taskName"):
                if value is not None:
                    log_data[key] = value
        return json.dumps(log_data)


def get_logger(name: str) -> logging.Logger:
    """Return a logger with JSON formatting; writes to stdout and optionally to a file for Promtail."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
        log_file = os.environ.get("LOG_FILE_PATH")
        if log_file:
            try:
                os.makedirs(os.path.dirname(log_file) or ".", exist_ok=True)
                file_handler = logging.FileHandler(log_file, encoding="utf-8")
                file_handler.setFormatter(JsonFormatter())
                logger.addHandler(file_handler)
            except OSError:
                pass
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger
