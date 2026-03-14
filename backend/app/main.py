"""Support Ticket API - observability-focused FastAPI application."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from app.config import get_settings
from app.database import init_db
from app.observability.metrics import get_metrics, get_metrics_content_type
from app.observability.logging import get_logger, set_service_name
from app.observability.tracing import setup_tracing
from app.controllers import auth_controller, ticket_controller, users_controller
from app.middleware.request_metrics import RequestMetricsMiddleware
from app.middleware.trace_context import TraceContextMiddleware

logger = get_logger(__name__)
set_service_name(get_settings().app_name)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield
    # shutdown


app = FastAPI(
    title="Support Ticket API",
    description="Observability-focused hackathon API: metrics, logs, traces",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS for frontend (Vite dev server or static origin)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Order: trace context first (set request_id/trace_id), then metrics
app.add_middleware(TraceContextMiddleware)
app.add_middleware(RequestMetricsMiddleware)

app.include_router(auth_controller.router)
app.include_router(users_controller.router)
app.include_router(ticket_controller.router)


@app.get("/")
def root():
    """Root endpoint - links to API docs and health."""
    return JSONResponse(
        status_code=200,
        content={
            "service": "Support Ticket API",
            "docs": "/docs",
            "redoc": "/redoc",
            "health": "/health",
            "openapi": "/openapi.json",
        },
    )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    """Prometheus scrape endpoint."""
    return Response(content=get_metrics(), media_type=get_metrics_content_type())


# Initialize OpenTelemetry after app is created (instrumentation adds middleware)
setup_tracing(app)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
