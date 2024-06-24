# telemify

Seamless instrumentation of tracing, logging, and metrics in FastAPI and Starlette applications, using opentelemetry, structlog, and prometheus-client.

![Python](https://img.shields.io/badge/Python-3.11-brightgreen)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v2.json)](https://github.com/charliermarsh/ruff)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-%23FE5196?logo=conventionalcommits&logoColor=white)](https://conventionalcommits.org)


## Installation
```shell
$ pip install telemify==0.1.0
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
