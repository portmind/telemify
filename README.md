# telemify

Seamless instrumentation of tracing, logging, and metrics in FastAPI and Starlette applications, using opentelemetry, structlog, and prometheus-client.

![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11-brightgreen)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v2.json)](https://github.com/charliermarsh/ruff)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-%23FE5196?logo=conventionalcommits&logoColor=white)](https://conventionalcommits.org)


## Installation
```shell
$ pip install telemify
```

## Usage
```python
import uvicorn
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine
from starlette.config import Config
from telemify.logging.configure import configure as configure_logger
from telemify.logging.filters import (
    ExceptionASGIApplicationFilter,
    MetricsEndpointFilter,
)
from telemify.logging.middleware import LoggerMiddleware
from telemify.logging.processors import add_open_telemetry_spans, drop_color_message_key
from telemify.metrics.configure import configure as configure_metrics
from telemify.metrics.middleware import PrometheusMiddleware
from telemify.tracing.configure import configure as configure_tracing

config = Config()
LOG_LEVEL: str = config("LOG_LEVEL", cast=str, default="info")

engine = create_async_engine("sqlite+aiosqlite:///test.db")


def configure_telemetry(app: FastAPI):
    configure_logger(
        json_logs=False,
        additional_processors=[drop_color_message_key, add_open_telemetry_spans],
        loggers_to_disable=["uvicorn.access"],
        loggers_to_propagate=["uvicorn", "uvicorn.error", "sqlalchemy.engine.Engine"],
        filters={
            "uvicorn.error": [
                ExceptionASGIApplicationFilter(),
            ],
            "telemify.logging.middleware": [MetricsEndpointFilter()],
        },
    )
    configure_metrics(app)
    configure_tracing(
        app,
        instrument_httpx=True,
        instrument_sqlalchemy=True,
        instrument_celery=True,
        instrument_botocore=True,
        instrument_jinja2=True,
        db_engine=engine,
    )


app = FastAPI()

app.add_middleware(LoggerMiddleware)
app.add_middleware(PrometheusMiddleware)
configure_telemetry(app)

if __name__ == "__main__":
    uvicorn.run(
        app,
        log_level=LOG_LEVEL,
    )
```

## Environment variables
```shell
# Application name to be used to mark signals
export APP_NAME=unknown

export LOG_LEVEL=info
export STATUS_4XX_LOG_LEVEL=warning

# Url to send the tracing data. It can be any tool that supports the OpenTelemetry protocol.
# ex. Grafana Tempo, Jaeger, etc.
export OTLP_GRPC_ENDPOINT=http://tempo-distributor.monitoring:4317

# Comma separated string to exclude certain urls from tracking.
# ex. "client/.*/info,healthcheck":
# This will exclude requests such as `https://site/client/123/info` and `https://site/xyz/healthcheck`.
export OTEL_PYTHON_EXCLUDED_URLS="client/.*/info,healthcheck"
```


## Tests

To run the tests, use the following command:

```shell
$ poetry run pytest
```


## Reference
1. [FastAPI with Observability](https://github.com/blueswen/fastapi-observability)
