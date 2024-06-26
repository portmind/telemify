import json
import logging
import uuid
from functools import wraps

import msgpack
import structlog
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from telemify.settings import STATUS_4XX_LOG_LEVEL

logger = structlog.stdlib.get_logger(__name__)


class LoggerMiddleware:
    """
    ``LoggerMiddleware`` automatically logs request and response related metadata
    """

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        request = Request(scope)
        response: Message = {}
        response_body_chunks = []

        @wraps(send)
        async def send_wrapper(message: Message):
            nonlocal response
            nonlocal response_body_chunks

            if message["type"] == "http.response.start":
                response = message
            elif response and message["type"] == "http.response.body":
                response_body_chunks.append(message.get("body", b""))
                if not message.get("more_body", False):
                    response["body"] = b"".join(response_body_chunks)
                    self._handle_response(request, response)

            await send(message)

        try:
            self._handle_request(request)
            await self.app(scope, receive, send_wrapper)
        except Exception as exception:
            status_code = HTTP_500_INTERNAL_SERVER_ERROR
            if isinstance(exception, HTTPException):
                status_code = exception.status_code
            self._handle_exception(request, status_code)
            raise exception

    def _handle_request(self, request: Request):
        request_id = request.headers.get(
            "x-request-id", request.headers.get("HTTP_X_REQUEST_ID")
        ) or str(uuid.uuid4())
        correlation_id = request.headers.get(
            "x-correlation-id", request.headers.get("HTTP_X_CORRELATION_ID")
        )
        structlog.contextvars.bind_contextvars(request_id=request_id)
        if correlation_id:
            structlog.contextvars.bind_contextvars(correlation_id=correlation_id)
        address = request.client
        logger.info(
            "request_started",
            ip=None if address is None else address.host,
            request=self._format_request(request),
            user_agent=request.headers.get("user-agent"),
        )

    def _handle_response(self, request: Request, response: Message):
        if (
            response["status"] >= 500
            or response["status"] >= 400
            and STATUS_4XX_LOG_LEVEL == logging.ERROR
        ):
            self._handle_exception(
                request,
                status_code=response["status"],
                response_body=self._parse_body(response),
            )
            return

        # if not a cricital error
        logger_args = {
            "code": response["status"],
            "request": self._format_request(request),
        }
        if response["status"] >= 400:
            level = STATUS_4XX_LOG_LEVEL
            logger_args["response_body"] = self._parse_body(response)
        else:
            level = logging.INFO

        logger.log(level, "request_finished", **logger_args)
        structlog.contextvars.clear_contextvars()

    def _handle_exception(self, request, status_code, **kwargs):
        logger.exception(
            "request_failed",
            code=status_code,
            request=self._format_request(request),
            **kwargs,
        )
        structlog.contextvars.clear_contextvars()

    @staticmethod
    def _parse_body(response: Message):
        content_type = next(
            (value for key, value in response["headers"] if key == b"content-type"),
            None,
        )

        body = ""
        if content_type is not None:
            if content_type == b"application/json":
                body = json.loads(response["body"])
            elif content_type == b"application/msgpack":
                body = msgpack.loads(response["body"])
            else:
                body = response["body"].decode()

        return body

    @staticmethod
    def _format_request(request):
        return f"{request.method} {request.url.path}"
