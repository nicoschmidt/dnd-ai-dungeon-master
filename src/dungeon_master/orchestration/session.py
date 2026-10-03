"""One session at the table: its state, its event log, its tools and its turns."""

import random
import secrets
from collections.abc import Callable

from ..adventure.builtin import iteration_001_repository
from ..adventure.repository import AdventureRepository
from ..events.contract import DeclaredAction, PartyUpdated
from ..events.log import EventLog
from ..session.party import Character, PartyEntry, build_party
from ..session.state import SessionState
from ..tools.toolbox import ToolBox
from .agent import DungeonMaster
from .turn import TurnRunner


class PartyLocked(Exception):
    """The encounter has started: from now on only tools change the party."""


class UnknownCharacter(Exception):
    """A declared action names a character the party does not have."""


class TableSession:
    """One table's session.

    `seed` seeds the dice the code rolls for the opponent, so a session's rolls
    can be reproduced; it is drawn at random unless given, and readable for
    the journal (#33). `adventure` is where opponents come from: iteration
    001's built-in fight unless another is given.
    """

    def __init__(
        self,
        dungeon_master: DungeonMaster,
        *,
        adventure: AdventureRepository | None = None,
        seed: int | None = None,
        redact: Callable[[str], str] = lambda text: text,
    ) -> None:
        self.seed = secrets.randbits(64) if seed is None else seed
        self.state = SessionState()
        self.events = EventLog()
        self.tools = ToolBox(
            self.state,
            self.events.publish,
            adventure=adventure or iteration_001_repository(),
            dice=random.Random(self.seed),
        )
        self.turns = TurnRunner(dungeon_master, self.tools, self.events.publish, redact)

    def enter_party(self, entry: PartyEntry) -> list[Character]:
        """Replace the party with what the group typed in, until the encounter starts.

        The players' action rather than the agent's, so it does not go through
        the tools; the table hears of it the same way, as `party_updated`.
        """
        if self.state.encounter is not None:
            raise PartyLocked()
        self.state.party = build_party(entry, self.state.party)
        self.events.publish(PartyUpdated(party=[c.model_copy(deep=True) for c in self.state.party]))
        return self.state.party

    def declare_action(self, action: DeclaredAction) -> str:
        """Start a turn. Returns its id."""
        if action.character_id is not None and self.state.character(action.character_id) is None:
            raise UnknownCharacter(action.character_id)
        return self.turns.start(action)

    async def close(self) -> None:
        """Stop a running turn and end every open stream."""
        await self.turns.cancel()
        self.events.close()
