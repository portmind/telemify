from prometheus_client import Counter, Gauge, Histogram

INFO = Gauge("app_info", "Web application information.", ["app_name"])
REQUESTS = Counter(
    "app_requests_total",
    "Total count of requests by method and path.",
    ["method", "path", "app_name"],
)
RESPONSES = Counter(
    "app_responses_total",
    "Total count of responses by method, path and status codes.",
    ["method", "path", "status", "app_name"],
)
REQUESTS_PROCESSING_TIME = Histogram(
    "app_requests_duration_seconds",
    "Histogram of requests processing time by path (in seconds)",
    ["method", "path", "app_name"],
)
EXCEPTIONS = Counter(
    "app_exceptions_total",
    "Total count of exceptions raised by path and exception type",
    ["method", "path", "exception_type", "app_name"],
)
REQUESTS_IN_PROGRESS = Gauge(
    "app_requests_in_progress",
    "Gauge of requests by method and path currently being processed",
    ["method", "path", "app_name"],
)
