"""The port behind which the dungeon master runs.

Model-dependent behaviour lives behind this interface so that everything above
and around it is testable without a model. The Claude Agent SDK adapter (#32)
implements it; tests use a scripted fake; until #32 the backend runs a
stand-in.
"""

from collections.abc import AsyncIterator
from typing import Protocol

from ..events.contract import DeclaredAction
from ..tools.toolbox import ToolBox


class DungeonMaster(Protocol):
    def take_turn(self, action: DeclaredAction, tools: ToolBox) -> AsyncIterator[str]:
        """Answer one declared action.

        Yields the narration piece by piece, as it is written. Every change to
        durable state goes through `tools`, which tells the table about it.
        """
        ...
