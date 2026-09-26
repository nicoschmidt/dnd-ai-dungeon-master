"""The ASGI application: the API and, at the table, the built client.

At the table this is the one process the players' browser talks to
(ADR-0005). While developing, the Vite dev server serves the client instead
and proxies `/api` here, so a missing client build is not an error.
"""

import logging
import os
from pathlib import Path

from fastapi import APIRouter, FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

logger = logging.getLogger(__name__)

DEFAULT_CLIENT_DIST = Path("client") / "dist"


class Health(BaseModel):
    status: str


router = APIRouter(prefix="/api")


@router.get("/health")
def health() -> Health:
    return Health(status="ok")


def create_app(client_dist: Path | None = None) -> FastAPI:
    """Build the application.

    `client_dist` is the directory of the built client. It defaults to
    `DM_CLIENT_DIST` from the environment, else `client/dist` relative to the
    working directory.
    """
    if client_dist is None:
        client_dist = Path(os.environ.get("DM_CLIENT_DIST", DEFAULT_CLIENT_DIST))

    app = FastAPI(title="AI Dungeon Master")
    app.include_router(router)

    # Mounted last: a mount at "/" would otherwise shadow the API routes.
    if client_dist.is_dir():
        app.mount("/", StaticFiles(directory=client_dist, html=True), name="client")
    else:
        logger.warning(
            "No client build at %s; serving the API only. "
            "Run `npm run build` in client/ to play at the table.",
            client_dist.resolve(),
        )

    return app


app = create_app()
