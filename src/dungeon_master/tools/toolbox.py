"""The one door through which the dungeon master changes durable state."""

from collections.abc import Callable, Iterable, Mapping
from typing import Any

from pydantic import ValidationError

from ..adventure.repository import AdventureRepository
from ..events.contract import EncounterUpdated, PartyUpdated, TableEvent
from ..rules.dice import RandomSource
from ..session.party import Character
from ..session.state import SessionState
from .context import ToolContext
from .registry import TOOLS, ToolSpec
from .result import ToolResult


class ToolBox:
    """Runs tools against the session state and tells the table what changed.

    Every call is checked, run and compared: arguments that do not fit the
    tool's schema are refused before the handler sees them, and when the party
    or the encounter differs afterwards, the matching state event is
    published. That is what makes ADR-0002's third commitment checkable: no
    number reaches the status panel except through here.

    The opponent's state is deliberately not compared: it is hidden, so no
    change to it can reach the table's stream from here.
    """

    def __init__(
        self,
        state: SessionState,
        publish: Callable[[TableEvent], object],
        *,
        adventure: AdventureRepository,
        dice: RandomSource,
        tools: Iterable[ToolSpec] = TOOLS,
    ) -> None:
        self._state = state
        self._context = ToolContext(state, adventure, dice)
        self._publish = publish
        self._tools = {tool.name: tool for tool in tools}

    @property
    def specs(self) -> tuple[ToolSpec, ...]:
        return tuple(self._tools.values())

    def party(self) -> list[Character]:
        """The party, to read. A copy: changes go through `call`."""
        return [c.model_copy(deep=True) for c in self._state.party]

    def call(self, name: str, arguments: Mapping[str, Any]) -> ToolResult:
        tool = self._tools.get(name)
        if tool is None:
            return ToolResult.refused(f"No tool {name!r}. Tools: {', '.join(self._tools)}.")
        try:
            args = tool.arguments.model_validate(arguments)
        except ValidationError as error:
            problems = "; ".join(
                f"{'.'.join(map(str, e['loc'])) or 'arguments'}: {e['msg']}" for e in error.errors()
            )
            return ToolResult.refused(f"Invalid arguments for {name}: {problems}.")

        party_before = self._party_snapshot()
        encounter_before = self._encounter_snapshot()
        result = tool.handler(self._context, args)

        # Published whatever the result, so the table never sees stale state
        # even if a handler changed something and then refused.
        if self._party_snapshot() != party_before:
            self._publish(PartyUpdated(party=[c.model_copy(deep=True) for c in self._state.party]))
        if self._encounter_snapshot() != encounter_before:
            encounter = self._state.encounter
            self._publish(
                EncounterUpdated(encounter=encounter.model_copy(deep=True) if encounter else None)
            )
        return result

    def _party_snapshot(self) -> list[dict[str, Any]]:
        return [c.model_dump() for c in self._state.party]

    def _encounter_snapshot(self) -> dict[str, Any] | None:
        encounter = self._state.encounter
        return encounter.model_dump() if encounter else None
