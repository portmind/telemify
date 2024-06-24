import time
from functools import wraps

from opentelemetry import trace
from starlette.requests import Request
from starlette.routing import Match
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from telemify.metrics import metrics
from telemify.settings import APP_NAME


class PrometheusMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        metrics.INFO.labels(app_name=APP_NAME).inc()

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        request = Request(scope)
        method = request.method
        path = self.get_route(request)

        if path is None:
            return await self.app(scope, receive, send)

        @wraps(send)
        async def send_wrapper(message: Message):
            if message["type"] == "http.response.start":
                metrics.RESPONSES.labels(
                    method=method,
                    path=path,
                    status_code=message["status"],
                    app_name=APP_NAME,
                ).inc()

            await send(message)

        metrics.REQUESTS_IN_PROGRESS.labels(
            method=method, path=path, app_name=APP_NAME
        ).inc()
        metrics.REQUESTS.labels(method=method, path=path, app_name=APP_NAME).inc()
        before_time = time.perf_counter()
        try:
            await self.app(scope, receive, send_wrapper)

            after_time = time.perf_counter()
            span = trace.get_current_span()
            trace_id = trace.format_trace_id(span.get_span_context().trace_id)
            metrics.REQUESTS_PROCESSING_TIME.labels(
                method=method, path=path, app_name=APP_NAME
            ).observe(after_time - before_time, exemplar={"TraceID": trace_id})
        except BaseException as e:
            metrics.EXCEPTIONS.labels(
                method=method,
                path=path,
                exception_type=type(e).__name__,
                app_name=APP_NAME,
            ).inc()
            raise e
        finally:
            metrics.REQUESTS_IN_PROGRESS.labels(
                method=method, path=path, app_name=APP_NAME
            ).dec()

    @staticmethod
    def get_route(request: Request) -> str | None:
        """
        Returns the target path as defined in the router.

        Example: /api/users/{user_id} instead of /api/users/1
        """
        for route in request.app.routes:
            match, _ = route.matches(request.scope)
            if match == Match.FULL:
                return route.path

        return None
