"""OpenTelemetry configuration and setup.

This module handles the configuration and initialization of OpenTelemetry tracing.
"""

import os
import platform

from opentelemetry import trace
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import ParentBasedTraceIdRatio

from src.api.config import settings


# Initialize optional OpenTelemetry components
HAS_OTEL_INSTRUMENTATION = False
OTLPSpanExporter = None
FastAPIInstrumentor = None
RequestsInstrumentor = None
SQLAlchemyInstrumentor = None

try:
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.requests import RequestsInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

    HAS_OTEL_INSTRUMENTATION = True
except ImportError:
    pass


def setup_opentelemetry(app) -> None:
    """Configure OpenTelemetry with FastAPI integration.

    Args:
        app: FastAPI application instance
    """
    if not HAS_OTEL_INSTRUMENTATION:
        return

    # Create a resource with service information and enhanced attributes
    resource = Resource.create(
        {
            SERVICE_NAME: settings.PROJECT_NAME,
            "service.version": settings.VERSION,
            "deployment.environment": settings.ENVIRONMENT,
            "deployment.region": settings.DEPLOYMENT_REGION,
            "host.name": os.uname().nodename,
            "process.pid": os.getpid(),
            "process.runtime.name": "python",
            "process.runtime.version": platform.python_version(),
        }
    )

    # Configure sampling based on environment
    if settings.ENVIRONMENT == "development":
        sampler = ParentBasedTraceIdRatio(1.0)
    else:
        sampler = ParentBasedTraceIdRatio(0.1)

    # Set up the tracer provider
    tracer_provider = TracerProvider(
        resource=resource,
        sampler=sampler,
    )

    # Configure the OTLP exporter for Jaeger 2.2 with batch processing options
    otlp_exporter = OTLPSpanExporter(
        endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT,
        insecure=settings.OTEL_EXPORTER_OTLP_INSECURE,
    )
    span_processor = BatchSpanProcessor(
        otlp_exporter,
        max_queue_size=512,
        max_export_batch_size=64,
        schedule_delay_millis=5000,
    )
    tracer_provider.add_span_processor(span_processor)

    # Set the tracer provider
    trace.set_tracer_provider(tracer_provider)

    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(
        app,
        tracer_provider=tracer_provider,
        excluded_urls="health,metrics",
    )

    # Instrument other libraries
    RequestsInstrumentor().instrument()
    SQLAlchemyInstrumentor().instrument(
        tracer_provider=tracer_provider,
        enable_commenter=True,
        commenter_options={},
    )
