import os
from opentelemetry import trace, propagate
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.zipkin.json import ZipkinExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.propagators.b3 import B3MultiFormat


def setup_tracing(app, service_name: str):
    ZIPKIN_ENDPOINT = os.getenv("ZIPKIN_ENDPOINT", "http://localhost:9411/api/v2/spans")

    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)

    exporter = ZipkinExporter(endpoint=ZIPKIN_ENDPOINT)
    processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(processor)

    trace.set_tracer_provider(provider)

    propagate.set_global_textmap(B3MultiFormat())

    FastAPIInstrumentor.instrument_app(app)
    HTTPXClientInstrumentor().instrument()

    print(f"Tracing enabled for {service_name} → {ZIPKIN_ENDPOINT}", flush=True)

    return trace.get_tracer(service_name)
