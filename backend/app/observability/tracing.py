"""OpenTelemetry tracing - all imports lazy to avoid pkg_resources at startup."""
import os

from app.config import get_settings
from app.observability.logging import get_logger

logger = get_logger(__name__)

# No opentelemetry imports at module level so app starts even if setuptools/pkg_resources missing


def setup_tracing(app=None):
    """Initialize OpenTelemetry and optionally instrument FastAPI and SQLAlchemy."""
    if not (os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT") or get_settings().otlp_endpoint):
        logger.info("tracing_disabled_no_endpoint")
        return
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource, SERVICE_NAME

        endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT") or get_settings().otlp_endpoint
        if endpoint.startswith("http"):
            endpoint = endpoint.replace("http://", "").replace("https://", "").rstrip("/")

        resource = Resource.create({SERVICE_NAME: "support-ticket-api"})
        provider = TracerProvider(resource=resource)
        exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)

        try:
            import pkg_resources  # noqa: F401 - ensure setuptools loaded before instrumentors
        except ImportError:
            logger.debug("auto_instrumentation_skipped_no_setuptools")
        else:
            try:
                from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
                if app:
                    FastAPIInstrumentor.instrument_app(app)
            except Exception as e:
                if "pkg_resources" not in str(e):
                    logger.warning("fastapi_instrumentation_skipped", extra={"error": str(e)})
            try:
                from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
                from app.database import engine
                SQLAlchemyInstrumentor().instrument(engine=engine)
            except Exception as e:
                if "pkg_resources" not in str(e):
                    logger.warning("sqlalchemy_instrumentation_skipped", extra={"error": str(e)})

        logger.info("tracing_initialized", extra={"endpoint": endpoint})
    except Exception as e:
        logger.warning("tracing_init_failed", extra={"error": str(e)})


def get_tracer(name: str):
    """Return a tracer; no-op if OpenTelemetry not available."""
    try:
        from opentelemetry import trace
        return trace.get_tracer(name, "1.0.0")
    except Exception:
        return _noop_tracer(name)


class _NoopSpan:
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass
    def set_attribute(self, *args, **kwargs):
        pass


class _NoopTracer:
    def start_as_current_span(self, name, **kwargs):
        return _NoopSpan()


def _noop_tracer(name: str):
    return _NoopTracer()
