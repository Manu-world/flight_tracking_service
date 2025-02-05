from typing import Any
from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from prometheus_client import start_http_server
import sentry_sdk
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from app.core.config import Settings

def setup_monitoring(app: FastAPI, settings: Settings) -> None:
    """Configure application monitoring and tracing."""
    
    # Set up OpenTelemetry tracing
    resource = Resource.create({"service.name": settings.PROJECT_NAME})
    tracer_provider = TracerProvider(resource=resource)
    
    jaeger_exporter = JaegerExporter(
        agent_host_name="localhost",
        agent_port=6831,
    )
    
    tracer_provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
    trace.set_tracer_provider(tracer_provider)
    
    
    FastAPIInstrumentor.instrument_app(app, server_request_hook=None, client_request_hook=None)
    
    httpx_instrumentor = HTTPXClientInstrumentor()
    httpx_instrumentor.instrument()
    
    # Start Prometheus metrics server
    start_http_server(port=9090)
    
    # Configure Sentry if DSN is provided
    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            traces_sample_rate=1.0,
            environment="production",
        )
        app.add_middleware(SentryAsgiMiddleware)
