# Copyright 2025 Lincoln Institute of Land Policy
# SPDX-License-Identifier: MIT

import asyncio
import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
)
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
import requests
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor
import threading

"""
This file contains initialization code and global vars that are
used throughout the entire integration
"""

print(
    f"Starting server with env var OTEL_SDK_DISABLED set to '{os.environ.get('OTEL_SDK_DISABLED')}'"
)


def init_otel():
    """Initialize the open telemetry config"""
    resource = Resource(attributes={"service.name": "iodh"})
    provider = TracerProvider(resource=resource)
    COLLECTOR_ENDPOINT = os.environ.get("COLLECTOR_ENDPOINT", "127.0.0.1")
    COLLECTOR_GRPC_PORT = os.environ.get("COLLECTOR_GRPC_PORT", 4317)

    processor = BatchSpanProcessor(
        OTLPSpanExporter(endpoint=f"http://{COLLECTOR_ENDPOINT}:{COLLECTOR_GRPC_PORT}")
    )
    provider.add_span_processor(processor)

    # Sets the global default tracer provider
    trace.set_tracer_provider(provider)

    AioHttpClientInstrumentor().instrument()
    print("Initialized open telemetry")


init_otel()
requests.packages.urllib3.util.connection.HAS_IPV6 = False  # type: ignore

TRACER = trace.get_tracer("iodh_tracer")

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

iodh_event_loop = asyncio.new_event_loop()


def loop_forever():
    try:
        iodh_event_loop.run_forever()
    finally:
        iodh_event_loop.run_until_complete(iodh_event_loop.shutdown_asyncgens())
        iodh_event_loop.close()


loop_thread = threading.Thread(target=loop_forever)
loop_thread.daemon = True
loop_thread.start()
