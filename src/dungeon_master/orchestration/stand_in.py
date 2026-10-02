"""A dungeon master that is not there yet.

Until the agent runs on a model (#32), the backend answers every action with
this: it says so, word by word, so the stream and the page can be seen working
at the table — and with `curl -N` — without a model or a credential.
"""

import asyncio
import re
from collections.abc import AsyncIterator

from ..events.contract import DeclaredAction
from ..tools.toolbox import ToolBox


class StandInDungeonMaster:
    def __init__(self, delay: float = 0.05) -> None:
        self._delay = delay

    async def take_turn(self, action: DeclaredAction, tools: ToolBox) -> AsyncIterator[str]:
        text = f"No dungeon master is connected yet. You declared: {action.text}"
        for word in re.findall(r"\S+\s*", text):
            await asyncio.sleep(self._delay)
            yield word
