"""One turn: a declared action in, narration and state events out."""

import asyncio
import logging
import traceback
from collections.abc import Callable
from uuid import uuid4

from ..events.contract import (
    DeclaredAction,
    NarrationDelta,
    TableError,
    TableEvent,
    TurnFinished,
    TurnStarted,
)
from ..tools.toolbox import ToolBox
from .agent import DungeonMaster, DungeonMasterError

logger = logging.getLogger(__name__)

AGENT_FAILED_MESSAGE = (
    "The dungeon master could not finish this turn. Declare the action again."
)


class TurnInProgress(Exception):
    """A turn is running. Interrupting it is deliberately not possible (ADR-0005)."""


class TurnRunner:
    """Runs one turn at a time and publishes what happens in it.

    Every `turn_started` is followed by a `turn_finished`, also when the
    dungeon master fails; the failure is an `error` event in between.
    """

    def __init__(
        self,
        dungeon_master: DungeonMaster,
        tools: ToolBox,
        publish: Callable[[TableEvent], object],
        redact: Callable[[str], str] = lambda text: text,
    ) -> None:
        self._dungeon_master = dungeon_master
        self._tools = tools
        self._publish = publish
        self._redact = redact
        self._task: asyncio.Task[None] | None = None

    @property
    def busy(self) -> bool:
        return self._task is not None and not self._task.done()

    def start(self, action: DeclaredAction) -> str:
        """Accept an action and run the turn in the background. Returns the turn id."""
        if self.busy:
            raise TurnInProgress()
        turn_id = uuid4().hex[:12]
        self._publish(TurnStarted(turn_id=turn_id, action=action))
        self._task = asyncio.create_task(self._run(turn_id, action))
        return turn_id

    async def wait(self) -> None:
        """Wait until the current turn, if any, has finished."""
        if self._task is not None:
            await asyncio.shield(self._task)

    async def cancel(self) -> None:
        if self._task is not None and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _run(self, turn_id: str, action: DeclaredAction) -> None:
        try:
            async for text in self._dungeon_master.take_turn(action, self._tools):
                if text:
                    self._publish(NarrationDelta(turn_id=turn_id, text=text))
        except DungeonMasterError as error:
            logger.warning("turn %s failed: %s", turn_id, self._redact(error.message))
            self._publish(TableError(code=error.code, message=error.message, turn_id=turn_id))
        except Exception:
            # The exception's text stays in the log, never in the event, and
            # passes through redaction first: it may carry a credential.
            logger.error("turn %s failed:\n%s", turn_id, self._redact(traceback.format_exc()))
            self._publish(
                TableError(code="agent_failed", message=AGENT_FAILED_MESSAGE, turn_id=turn_id)
            )
        finally:
            self._publish(TurnFinished(turn_id=turn_id))
