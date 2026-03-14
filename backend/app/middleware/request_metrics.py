"""Middleware to record request metrics (count, duration, errors)."""
import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.observability.metrics import (
    HTTP_REQUESTS_TOTAL,
    HTTP_REQUEST_DURATION_SECONDS,
    HTTP_ERRORS_TOTAL,
)
from app.observability.logging import set_request_id, set_trace_id, get_logger

logger = get_logger(__name__)


def get_path_template(request: Request) -> str:
    """Return route path template for metrics (e.g. /tickets/{id})."""
    if request.scope.get("route"):
        return request.scope["route"].path
    return request.url.path


class RequestMetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        set_request_id(request_id)
        trace_id = request.headers.get("traceparent", "").split("-")[1] if "traceparent" in request.headers else ""
        if trace_id:
            set_trace_id(trace_id)

        method = request.method
        path = get_path_template(request)
        start = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception as e:
            logger.exception("request_failed", extra={"path": path, "error": str(e)})
            HTTP_ERRORS_TOTAL.labels(method=method, endpoint=path, error_type=type(e).__name__).inc()
            raise
        finally:
            duration = time.perf_counter() - start
            HTTP_REQUESTS_TOTAL.labels(method=method, endpoint=path, status=status_code).inc()
            HTTP_REQUEST_DURATION_SECONDS.labels(method=method, endpoint=path).observe(duration)
            if status_code >= 400:
                HTTP_ERRORS_TOTAL.labels(method=method, endpoint=path, error_type="http").inc()
