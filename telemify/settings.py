import logging

from starlette.config import Config

config = Config()

APP_NAME = config("APP_NAME", cast=str, default="unknown")

LOG_LEVEL: str = config("LOG_LEVEL", cast=str, default="info")
STATUS_4XX_LOG_LEVEL: int = logging.getLevelName(
    config("STATUS_4XX_LOG_LEVEL", cast=str.upper, default="warning")
)

OTLP_GRPC_ENDPOINT = config("OTLP_GRPC_ENDPOINT", cast=str, default="")
