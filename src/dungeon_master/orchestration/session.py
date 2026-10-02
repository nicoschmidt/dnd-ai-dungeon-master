"""One session at the table: its state, its event log, its tools and its turns."""

from ..events.log import EventLog
from ..session.state import SessionState
from ..tools.toolbox import ToolBox
from .agent import DungeonMaster
from .turn import TurnRunner


class TableSession:
    def __init__(self, dungeon_master: DungeonMaster) -> None:
        self.state = SessionState()
        self.events = EventLog()
        self.tools = ToolBox(self.state, self.events.publish)
        self.turns = TurnRunner(dungeon_master, self.tools, self.events.publish)

    async def close(self) -> None:
        """Stop a running turn and end every open stream."""
        await self.turns.cancel()
        self.events.close()
