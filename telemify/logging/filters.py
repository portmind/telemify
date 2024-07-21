import logging


class ExceptionASGIApplicationFilter(logging.Filter):
    """Remove logs of exceptions raised by uvicorn as structlog also logs them."""

    def filter(self, record: logging.LogRecord) -> bool:
        return "Exception in ASGI application" not in record.getMessage()


class EndpointFilter(logging.Filter):
    """Remove logs of particular endpoint."""

    def __init__(self, endpoint: str, allowed: list[str] | None = None):
        self._endpoint = endpoint
        self._allowed = allowed or []

    # Endpoint access log filter
    def filter(self, record: logging.LogRecord) -> bool:
        return self._endpoint not in record.getMessage() or any(
            allow in record.getMessage() for allow in self._allowed
        )


class MetricsEndpointFilter(EndpointFilter):
    """Remove logs of /metrics endpoint."""

    def __init__(self):
        super().__init__("GET /metrics")
