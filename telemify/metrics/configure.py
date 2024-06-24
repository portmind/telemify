from prometheus_client import REGISTRY
from prometheus_client.openmetrics.exposition import (
    CONTENT_TYPE_LATEST,
    generate_latest,
)
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response


def _metrics(_: Request) -> Response:
    return Response(
        generate_latest(REGISTRY), headers={"Content-Type": CONTENT_TYPE_LATEST}
    )


def configure(app: Starlette):
    app.add_route("/metrics", _metrics)
