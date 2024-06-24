import logging

from starlette.config import Config

config = Config()

LOG_LEVEL: str = config("LOG_LEVEL", cast=str, default="info")
STATUS_4XX_LOG_LEVEL: int = logging.getLevelName(
    config("STATUS_4XX_LOG_LEVEL", cast=str.upper, default="warning")
)
