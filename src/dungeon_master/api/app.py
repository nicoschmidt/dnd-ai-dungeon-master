"""The ASGI application: the API and, at the table, the built client.

At the table this is the one process the players' browser talks to
(ADR-0005). While developing, the Vite dev server serves the client instead
and proxies `/api` here, so a missing client build is not an error.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import APIRouter, FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ..adventure.builtin import iteration_001_repository
from ..adventure.repository import AdventureRepository
from ..orchestration.agent import DungeonMaster
from ..orchestration.agent_sdk import AgentSdkDungeonMaster
from ..orchestration.credentials import CredentialSwitch
from ..orchestration.session import TableSession
from ..orchestration.stand_in import StandInDungeonMaster
from ..settings import Settings
from . import session

logger = logging.getLogger(__name__)



class Health(BaseModel):
    status: str


router = APIRouter(prefix="/api")


@router.get("/health")
def health() -> Health:
    return Health(status="ok")


def create_app(
    client_dist: Path | None = None,
    dungeon_master: DungeonMaster | None = None,
    adventure: AdventureRepository | None = None,
    *,
    settings: Settings | None = None,
    credentials: CredentialSwitch | None = None,
) -> FastAPI:
    """Build the application, with one session for the one table.

    Configuration comes from `Settings`: `DM_` environment variables or `.env`.
    `client_dist` is the directory of the built client, `DM_CLIENT_DIST` unless
    given. The dungeon master is the Claude agent, or the stand-in with
    `DM_DUNGEON_MASTER=stand_in`; tests pass their own. `adventure` defaults to
    iteration 001's built-in fight. `credentials` is the one switch the API
    and the dungeon master share; pass it with a dungeon master that uses it.
    """
    settings = settings or Settings()
    client_dist = client_dist or settings.client_dist
    adventure = adventure or iteration_001_repository()
    credentials = credentials or CredentialSwitch(settings)
    if dungeon_master is None:
        dungeon_master = (
            AgentSdkDungeonMaster(settings, credentials, adventure)
            if settings.dungeon_master == "agent"
            else StandInDungeonMaster()
        )

    table = TableSession(dungeon_master, adventure=adventure, redact=credentials.redact)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        yield
        # uvicorn runs this only after every connection has closed, and a
        # browser never closes the table's stream: run it with
        # `--timeout-graceful-shutdown`, as the README does, or it waits forever.
        await table.close()

    app = FastAPI(title="AI Dungeon Master", lifespan=lifespan)
    app.state.session = table
    app.state.credentials = credentials
    app.include_router(router)
    app.include_router(session.router)

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
