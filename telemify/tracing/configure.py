from opentelemetry import trace
from opentelemetry.instrumentation.starlette import StarletteInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from starlette.applications import Starlette

from telemify.settings import APP_NAME, OTLP_GRPC_ENDPOINT


def _enable_exporter(tracer: TracerProvider):
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
        OTLPSpanExporter,
    )
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    tracer.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=OTLP_GRPC_ENDPOINT))
    )


def _enable_instrumentors(
    app: Starlette,
    tracer: TracerProvider,
    instrument_httpx: bool = False,
    instrument_sqlalchemy: bool = False,
    instrument_celery: bool = False,
    instrument_botocore: bool = False,
    instrument_jinja2: bool = False,
    db_engine=None,
):
    StarletteInstrumentor.instrument_app(app, tracer_provider=tracer)

    if instrument_httpx:
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

        HTTPXClientInstrumentor().instrument(tracer_provider=tracer)

    if instrument_sqlalchemy:
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

        sync_engine = getattr(db_engine, "sync_engine", None) or db_engine

        SQLAlchemyInstrumentor().instrument(
            tracer_provider=tracer, enable_commenter=True, engine=sync_engine
        )

    if instrument_celery:
        from opentelemetry.instrumentation.celery import CeleryInstrumentor

        CeleryInstrumentor().instrument(tracer_provider=tracer)

    if instrument_botocore:
        from opentelemetry.instrumentation.botocore import BotocoreInstrumentor
        from opentelemetry.instrumentation.threading import ThreadingInstrumentor

        BotocoreInstrumentor().instrument(tracer_provider=tracer)
        # This propagates trace context within threads.
        # As boto runs separate threads this is required,
        # to preserve main thread's tracing context.
        ThreadingInstrumentor().instrument(tracer_provider=tracer)

    if instrument_jinja2:
        from opentelemetry.instrumentation.jinja2 import Jinja2Instrumentor

        Jinja2Instrumentor().instrument(tracer_provider=tracer)


def configure(
    app: Starlette,
    instrument_httpx: bool = False,
    instrument_sqlalchemy: bool = False,
    instrument_celery: bool = False,
    instrument_botocore: bool = False,
    instrument_jinja2: bool = False,
    db_engine=None,
):
    """Configure Tracing

    Arguments:
    app -- FastApi/Starlette application to instrument
    instrument_x -- enable instrumentation x client to propagate trace context
    db_engine -- sqlalchemy db engine, required if SQLALCHEMY instrumentor is chosen
    """
    # Setting OpenTelemetry
    # set the service name to show in traces
    resource = Resource.create(attributes={"service.name": APP_NAME})

    # set the tracer provider
    tracer = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer)

    if OTLP_GRPC_ENDPOINT:
        _enable_exporter(tracer)

    _enable_instrumentors(
        app,
        tracer,
        instrument_httpx,
        instrument_sqlalchemy,
        instrument_celery,
        instrument_botocore,
        instrument_jinja2,
        db_engine,
    )
