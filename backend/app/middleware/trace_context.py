"""Middleware to propagate trace context (request_id, trace_id) to response headers."""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.observability.logging import get_request_id, get_trace_id, set_request_id, set_trace_id
import uuid


class TraceContextMiddleware(BaseHTTPMiddleware):
    """Set request_id and trace_id in context and add them to response headers."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        set_request_id(request_id)
        trace_id = ""
        if "traceparent" in request.headers:
            parts = request.headers["traceparent"].split("-")
            if len(parts) >= 2:
                trace_id = parts[1]
        if not trace_id:
            trace_id = str(uuid.uuid4()).replace("-", "")[:16]
        set_trace_id(trace_id)

        response = await call_next(request)
        response.headers["x-request-id"] = request_id
        response.headers["x-trace-id"] = trace_id
        return response
