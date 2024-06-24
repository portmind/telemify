import logging

import structlog
import urllib3
from structlog.types import Processor

from telemify.settings import LOG_LEVEL


def configure(
    json_logs: bool = False,
    additional_processors: list[Processor] | None = None,
    loggers_to_disable: list[str] | None = None,
    loggers_to_propagate: list[str] | None = None,
    filters: dict[str, list[logging.Filter]] | None = None,
):
    """Configure logging.

    Arguments:
    json_logs -- generate json logs
    additional_processors: specify additional log processors
    loggers_to_disable: name of the loggers to be disabled
    loggers_to_propagate: names of the loggers to propagate logs
        which will be caught by our root logger and formatted correctly by structlog
    filters: specify filters to which to remove particular logs from particular logger
        ex. {"uvicorn.error": [MetricsEndpointFilter()]}
    """

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    additional_processors = additional_processors or []
    loggers_to_propagate = loggers_to_propagate or []
    loggers_to_disable = loggers_to_disable or []
    filters = filters or {}

    shared_processors: list[Processor] = (
        [
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.stdlib.ExtraAdder(),
        ]
        + additional_processors
        + [
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
        ]
    )

    structlog.configure(
        processors=shared_processors
        + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    log_renderers: list[Processor]
    if json_logs:
        log_renderers = [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]
    else:
        log_renderers = [
            structlog.dev.ConsoleRenderer(
                exception_formatter=structlog.dev.RichTracebackFormatter()
            )
        ]

    formatter = structlog.stdlib.ProcessorFormatter(
        # These run ONLY on `logging` entries that do NOT originate within
        # structlog.
        foreign_pre_chain=shared_processors,
        # These run on ALL entries after the pre_chain is done.
        processors=[structlog.stdlib.ProcessorFormatter.remove_processors_meta]
        + log_renderers,
    )

    handler = logging.StreamHandler()
    # Use OUR `ProcessorFormatter` to format all `logging` entries.
    handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(LOG_LEVEL.upper())

    for logger in loggers_to_propagate:
        logging.getLogger(logger).handlers.clear()
        logging.getLogger(logger).propagate = True

    for logger in loggers_to_disable:
        logging.getLogger(logger).handlers.clear()
        logging.getLogger(logger).propagate = False

    for logger, current_filters in filters.items():
        logger_obj = logging.getLogger(logger)
        for filter in current_filters:
            logger_obj.addFilter(filter)
