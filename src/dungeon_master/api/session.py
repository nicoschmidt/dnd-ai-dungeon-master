"""The table's routes: the event stream out; the declared action, the party and the credential mode in.

Thin by intent (ADR-0005, commitment 4): each handler translates HTTP into one
call on the session and back.
"""

from collections.abc import AsyncIterable
from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, Request, status
from fastapi.sse import EventSourceResponse, ServerSentEvent
from pydantic import BaseModel

from ..events.contract import Character, DeclaredAction, PartyEntry
from ..orchestration.credentials import CredentialSwitch, NoApiKey
from ..orchestration.session import PartyLocked, TableSession, UnknownCharacter
from ..orchestration.turn import TurnInProgress
from ..settings import CredentialMode

router = APIRouter(prefix="/api/session")


class TurnAccepted(BaseModel):
    turn_id: str


class Credentials(BaseModel):
    """The credential mode in use. Never the credential itself (ADR-0007)."""

    mode: CredentialMode
    api_key_configured: bool


class CredentialChoice(BaseModel):
    mode: CredentialMode


def _session(request: Request) -> TableSession:
    return request.app.state.session


@router.get("/stream", response_class=EventSourceResponse)
async def stream(
    request: Request,
    last_event_id: Annotated[str | None, Header()] = None,
) -> AsyncIterable[ServerSentEvent]:
    """Every table event after `Last-Event-ID`, then each new one as it happens.

    Without `Last-Event-ID` — a fresh page — the whole session so far.
    """
    async for event_id, event in _session(request).events.subscribe(last_event_id):
        yield ServerSentEvent(event=event.type, id=event_id, data=event)


@router.post("/actions", status_code=status.HTTP_202_ACCEPTED)
async def declare_action(request: Request, action: DeclaredAction) -> TurnAccepted:
    """Start a turn. Its narration and state changes arrive on the stream."""
    try:
        turn_id = _session(request).declare_action(action)
    except UnknownCharacter as error:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, f"No character {error.args[0]!r} in the party."
        ) from None
    except TurnInProgress:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "The dungeon master is still answering the last action."
        ) from None
    return TurnAccepted(turn_id=turn_id)


@router.put("/party")
async def enter_party(request: Request, entry: PartyEntry) -> list[Character]:
    """Replace the party, until the encounter starts. The table hears of it on the stream."""
    try:
        return _session(request).enter_party(entry)
    except PartyLocked:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "The encounter has started. Only the dungeon master's tools change the party now.",
        ) from None


def _credentials(request: Request) -> Credentials:
    switch: CredentialSwitch = request.app.state.credentials
    return Credentials(mode=switch.mode, api_key_configured=switch.api_key_configured)


@router.get("/credentials")
async def credentials(request: Request) -> Credentials:
    """Which credential the dungeon master runs on."""
    return _credentials(request)


@router.put("/credentials")
async def switch_credentials(request: Request, choice: CredentialChoice) -> Credentials:
    """Switch between the subscription and the API key. Takes effect at the next turn."""
    try:
        request.app.state.credentials.switch(choice.mode)
    except NoApiKey as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from None
    return _credentials(request)
