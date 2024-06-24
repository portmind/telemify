from opentelemetry import trace
from structlog.types import EventDict


def drop_color_message_key(_, __, event_dict: EventDict) -> EventDict:
    """
    Uvicorn logs the message a second time in the extra `color_message`, but we don't
    need it. This processor drops the key from the event dict if it exists.
    """
    event_dict.pop("color_message", None)
    return event_dict


def add_open_telemetry_spans(_, __, event_dict):
    span = trace.get_current_span()
    if not span.is_recording():
        return event_dict

    ctx = span.get_span_context()
    parent = getattr(span, "parent", None)

    event_dict["span_id"] = trace.format_span_id(ctx.span_id)
    event_dict["trace_id"] = trace.format_trace_id(ctx.trace_id)
    event_dict["parent_span_id"] = (
        None if not parent else trace.format_span_id(parent.span_id)
    )

    event_dict["service"] = None
    if resource := getattr(trace.get_tracer_provider(), "resource", None):
        if service_name := resource.attributes.get("service.name", None):
            event_dict["service"] = service_name

    return event_dict
