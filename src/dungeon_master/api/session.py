"""The table's two routes: the event stream out, the declared action in.

Thin by intent (ADR-0005, commitment 4): each handler translates HTTP into one
call on the session and back.
"""

from collections.abc import AsyncIterable
from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, Request, status
from fastapi.sse import EventSourceResponse, ServerSentEvent
from pydantic import BaseModel

from ..events.contract import DeclaredAction
from ..orchestration.session import TableSession
from ..orchestration.turn import TurnInProgress

router = APIRouter(prefix="/api/session")


class TurnAccepted(BaseModel):
    turn_id: str


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
        turn_id = _session(request).turns.start(action)
    except TurnInProgress:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "The dungeon master is still answering the last action."
        ) from None
    return TurnAccepted(turn_id=turn_id)
