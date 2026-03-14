"""Prometheus metrics for the support ticket API."""
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

# HTTP metrics
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)
HTTP_ERRORS_TOTAL = Counter(
    "http_errors_total",
    "Total HTTP errors",
    ["method", "endpoint", "error_type"],
)

# Business metrics
ACTIVE_USERS = Gauge(
    "active_users",
    "Number of currently active (logged-in) users (set by app)",
)
_active_users_count = 0


def active_users_inc() -> None:
    """Call on successful login. Keeps gauge and internal count in sync."""
    global _active_users_count
    _active_users_count += 1
    ACTIVE_USERS.set(_active_users_count)


def active_users_dec() -> None:
    """Call on logout. Never goes below zero."""
    global _active_users_count
    _active_users_count = max(0, _active_users_count - 1)
    ACTIVE_USERS.set(_active_users_count)


LOGINS_TOTAL = Counter(
    "logins_total",
    "Total successful logins",
)
TICKETS_CREATED_TOTAL = Counter(
    "tickets_created_total",
    "Total tickets created",
)
TICKETS_BY_STATUS = Gauge(
    "tickets_by_status",
    "Tickets count by status",
    ["status"],
)
DB_QUERY_DURATION_SECONDS = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    ["operation"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5),
)
DB_ERRORS_TOTAL = Counter(
    "db_errors_total",
    "Database errors total",
    ["operation"],
)


def get_metrics() -> bytes:
    """Return Prometheus exposition format."""
    return generate_latest()


def get_metrics_content_type() -> str:
    return CONTENT_TYPE_LATEST
