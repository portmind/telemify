import logging


class ExceptionASGIApplicationFilter(logging.Filter):
    """Remove logs of exceptions raised by uvicorn as structlog also logs them."""

    def filter(self, record: logging.LogRecord) -> bool:
        return "Exception in ASGI application" not in record.getMessage()


class EndpointFilter(logging.Filter):
    """Remove logs of particular endpoint."""

    def __init__(self, endpoint: str):
        self._endpoint = endpoint

    # Endpoint access log filter
    def filter(self, record: logging.LogRecord) -> bool:
        return self._endpoint not in record.getMessage()


class MetricsEndpointFilter(EndpointFilter):
    """Remove logs of /metrics endpoint."""

    def __init__(self):
        super().__init__("GET /metrics")
