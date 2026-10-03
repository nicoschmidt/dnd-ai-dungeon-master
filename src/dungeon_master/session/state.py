"""The state of one session at the table.

One table, one session, held in memory: surviving a restart is out of scope
for iteration 001. Only tools change what is held here.

Some of it is public — the party and the `Encounter` — and reaches the table
as events. The rest is hidden: the opponent's state and the initiative behind
the turn order. Nothing sends that to the table's stream; the game master view
(#34) will show it.
"""

from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ..adventure.models import Monster
from ..rules.dice import RollRecord
from ..rules.encounter import Outcome
from ..rules.initiative import InitiativeEntry
from .party import Character, Condition


class Combatant(BaseModel):
    """One place in the turn order."""

    model_config = ConfigDict(extra="forbid", json_schema_serialization_defaults_required=True)

    kind: Literal["character", "opponent"]
    id: str
    name: str


class Encounter(BaseModel):
    """What the table may know about the encounter (docs/domain/combat.md).

    The opponent's numbers are not here: they are hidden from the table and
    belong to the opponent's own state (#31).
    """

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        json_schema_serialization_defaults_required=True,
    )

    opponent_name: str
    round: int = Field(default=0, ge=0, description="0 until the turn order is fixed.")
    turn_order: list[Combatant] = Field(default_factory=list)
    current_turn: int | None = Field(
        default=None, ge=0, description="Index into turn_order of whoever acts now."
    )
    outcome: Outcome | None = Field(default=None, description="Set when the encounter has ended.")


@dataclass
class OpponentState:
    """The opponent during the encounter. Hidden from the table."""

    monster: Monster
    current_hit_points: int
    initiative: RollRecord
    conditions: list[Condition] = field(default_factory=list)
    attacks_this_turn: int = 0


@dataclass
class SessionState:
    """Everything durable about the session."""

    party: list[Character] = field(default_factory=list)
    encounter: Encounter | None = None
    opponent: OpponentState | None = None
    initiative: dict[str, InitiativeEntry] = field(default_factory=dict)
    """The characters' reported initiative, in the order it was reported."""

    def character(self, character_id: str) -> Character | None:
        return next((c for c in self.party if c.id == character_id), None)
