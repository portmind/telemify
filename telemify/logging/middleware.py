import json
import logging
import uuid
import zlib
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
        body_chunks = []

        @wraps(send)
        async def send_wrapper(message: Message):
            nonlocal response
            nonlocal body_chunks

            if message["type"] == "http.response.start":
                response = message
            elif response and message["type"] == "http.response.body":
                body_chunks.append(message.get("body", b""))
                if not message.get("more_body", False):
                    response["body"] = b"".join(body_chunks)
                    self._handle_response(request, response)

            await send(message)

        try:
            self._handle_request(request)
            await self.app(scope, receive, send_wrapper)
        except Exception as exception:
            status = HTTP_500_INTERNAL_SERVER_ERROR
            if isinstance(exception, HTTPException):
                status = exception.status_code
            self._handle_exception(request, status)
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
                status=response["status"],
                body=self._parse_body(response),
            )
            return

        # if not a cricital error
        logger_args = {
            "status": response["status"],
            "request": self._format_request(request),
        }
        if response["status"] >= 400:
            level = STATUS_4XX_LOG_LEVEL
            logger_args["body"] = self._parse_body(response)
        else:
            level = logging.INFO

        logger.log(level, "request_finished", **logger_args)
        structlog.contextvars.clear_contextvars()

    def _handle_exception(self, request, status, **kwargs):
        logger.exception(
            "request_failed",
            status=status,
            request=self._format_request(request),
            **kwargs,
        )
        structlog.contextvars.clear_contextvars()

    @staticmethod
    def _parse_body(response: Message):
        content_type = LoggerMiddleware._get_header(response, b"content-type")

        body = ""
        if content_type is not None:
            decompressed_body = LoggerMiddleware._decompress_body(response)
            if content_type == b"application/json":
                body = json.loads(decompressed_body)
            elif content_type == b"application/msgpack":
                body = msgpack.loads(decompressed_body)
            else:
                body = decompressed_body.decode()

        return body

    @staticmethod
    def _decompress_body(response: Message) -> bytes:
        """Decompress body if it has passed the Gzip middleware"""

        content_encoding = LoggerMiddleware._get_header(response, b"content-encoding")
        if content_encoding is not None and b"gzip" in content_encoding:
            return zlib.decompress(response["body"], 16 + zlib.MAX_WBITS)

        return response["body"]

    @staticmethod
    def _get_header(response: Message, header_key: bytes) -> bytes | None:
        return next(
            (value for key, value in response["headers"] if key == header_key),
            None,
        )

    @staticmethod
    def _format_request(request):
        return f"{request.method} {request.url.path}"
