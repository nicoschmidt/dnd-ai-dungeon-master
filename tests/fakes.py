"""A dungeon master that follows a script, so turns are testable without a model."""

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any

from dungeon_master.events.contract import DeclaredAction
from dungeon_master.tools.result import ToolResult
from dungeon_master.tools.toolbox import ToolBox


@dataclass
class Say:
    text: str


@dataclass
class Call:
    tool: str
    arguments: dict[str, Any] = field(default_factory=dict)


@dataclass
class Hold:
    """Wait until the test releases the turn."""

    release: asyncio.Event


@dataclass
class Fail:
    message: str = "the model went away"


class ScriptedDungeonMaster:
    def __init__(self, *steps: Say | Call | Hold | Fail) -> None:
        self.steps = steps
        self.actions: list[DeclaredAction] = []
        self.results: list[ToolResult] = []

    async def take_turn(self, action: DeclaredAction, tools: ToolBox) -> AsyncIterator[str]:
        self.actions.append(action)
        for step in self.steps:
            match step:
                case Say(text):
                    yield text
                case Call(tool, arguments):
                    self.results.append(tools.call(tool, arguments))
                case Hold(release):
                    await release.wait()
                case Fail(message):
                    raise RuntimeError(message)


class FixedDice:
    """A random source that hands out a fixed sequence, and fails loudly.

    It fails when the sequence runs out, or when a value could not come from
    the die asked for, so a test cannot pass on dice it did not mean to roll.
    """

    def __init__(self, *values: int) -> None:
        self._values = list(values)

    def randint(self, a: int, b: int) -> int:
        if not self._values:
            raise AssertionError(f"the dice ran out: randint({a}, {b})")
        value = self._values.pop(0)
        if not a <= value <= b:
            raise AssertionError(f"{value} cannot come from randint({a}, {b})")
        return value

    @property
    def unused(self) -> list[int]:
        return list(self._values)
