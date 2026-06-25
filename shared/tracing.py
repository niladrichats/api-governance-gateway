import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.zipkin.json import ZipkinExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource


def setup_tracing(app, service_name: str):
    ZIPKIN_ENDPOINT = os.getenv("ZIPKIN_ENDPOINT", "http://localhost:9411/api/v2/spans")

    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)

    exporter = ZipkinExporter(endpoint=ZIPKIN_ENDPOINT)
    processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(processor)

    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app)

    print(f"Tracing enabled for {service_name} → {ZIPKIN_ENDPOINT}", flush=True)

    return trace.get_tracer(service_name)
