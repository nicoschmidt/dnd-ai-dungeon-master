"""Every event the table has been sent this session, in order, with its id.

The stream endpoint reads from here, so a reconnecting client is given what it
missed and a reloaded page is given the whole session. Held in memory: one
table, one session, and surviving a restart is out of scope.
"""

import asyncio
from collections.abc import AsyncIterator
from uuid import uuid4

from .contract import TableEvent


class EventLog:
    """Append-only, with ids of the form `<session id>:<sequence number>`.

    The session id in every event id makes a restart detectable: a browser
    that reconnects with an id from an earlier process has seen nothing of
    this session and is sent all of it.
    """

    def __init__(self, session_id: str | None = None) -> None:
        self.session_id = session_id or uuid4().hex[:12]
        self._events: list[TableEvent] = []
        self._appended = asyncio.Event()
        self._closed = False

    def publish(self, event: TableEvent) -> str:
        """Append an event and wake every subscriber. Returns the event's id."""
        if self._closed:
            raise RuntimeError("the event log is closed")
        self._events.append(event)
        # Wake the current waiters, and give later ones a fresh event to wait on.
        self._appended.set()
        self._appended = asyncio.Event()
        return self._event_id(len(self._events))

    def close(self) -> None:
        """End every subscription once it has caught up. Used at shutdown."""
        self._closed = True
        self._appended.set()

    async def subscribe(
        self, last_event_id: str | None = None
    ) -> AsyncIterator[tuple[str, TableEvent]]:
        """Yield (id, event) for every event after `last_event_id`, then follow."""
        position = self._position_after(last_event_id)
        while True:
            while position < len(self._events):
                position += 1
                yield self._event_id(position), self._events[position - 1]
            if self._closed:
                return
            await self._appended.wait()

    def _event_id(self, sequence: int) -> str:
        return f"{self.session_id}:{sequence}"

    def _position_after(self, last_event_id: str | None) -> int:
        session_id, _, sequence = (last_event_id or "").partition(":")
        if session_id != self.session_id or not sequence.isdigit():
            return 0
        return min(int(sequence), len(self._events))
