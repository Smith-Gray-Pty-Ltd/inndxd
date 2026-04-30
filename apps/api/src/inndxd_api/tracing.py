"""OpenTelemetry tracing setup."""

from __future__ import annotations

import logging

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

logger = logging.getLogger(__name__)


def setup_tracing(service_name: str = "inndxd-api", otlp_endpoint: str | None = None):
    provider = TracerProvider()
    if otlp_endpoint:
        exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        logger.info("OTLP tracing enabled at %s", otlp_endpoint)
    trace.set_tracer_provider(provider)


def instrument_app(app):
    FastAPIInstrumentor.instrument_app(app)
