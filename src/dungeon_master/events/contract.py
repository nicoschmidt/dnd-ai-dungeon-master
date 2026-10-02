"""The events on the table's stream, and the declared action that starts a turn.

Narration and state are separate event types (ADR-0005, commitment 2): a
number on the status panel arrives as `party_updated`, never inside
`narration_delta`. The set of event types is closed by construction, because
`TableEvent` is a discriminated union on `type`.

The wire format is versioned. Change it deliberately: bump `CONTRACT_VERSION`,
regenerate the schema and the client's types, and describe the change in
docs/domain/event-contract.md.
"""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

from ..session.party import Character
from ..session.state import Encounter

CONTRACT_VERSION = 1


class _Model(BaseModel):
    # In the serialisation schema, fields with defaults are always present, so
    # the generated TypeScript types do not make `type` optional.
    model_config = ConfigDict(extra="forbid", json_schema_serialization_defaults_required=True)


class DeclaredAction(_Model):
    """What a player typed: the declared action and the dice they rolled."""

    text: str = Field(min_length=1, max_length=2000)
    character_id: str | None = Field(
        default=None, description="The acting character, when the client knows it."
    )


class TurnStarted(_Model):
    """A declared action was accepted, and the dungeon master is answering it."""

    type: Literal["turn_started"] = "turn_started"
    turn_id: str
    action: DeclaredAction


class NarrationDelta(_Model):
    """The next piece of narration, as the model writes it."""

    type: Literal["narration_delta"] = "narration_delta"
    turn_id: str
    text: str


class TurnFinished(_Model):
    """The dungeon master has finished answering; the next action may be declared."""

    type: Literal["turn_finished"] = "turn_finished"
    turn_id: str


class PartyUpdated(_Model):
    """The whole party as the backend holds it, after a tool changed it."""

    type: Literal["party_updated"] = "party_updated"
    party: list[Character]


class EncounterUpdated(_Model):
    """The public state of the encounter, after a tool changed it."""

    type: Literal["encounter_updated"] = "encounter_updated"
    encounter: Encounter | None


ErrorCode = Literal["agent_failed"]


class TableError(_Model):
    """Something went wrong that the table should know about.

    The message is written for the table. It never carries an exception's
    text, which could carry a credential (ADR-0007).
    """

    type: Literal["error"] = "error"
    code: ErrorCode
    message: str
    turn_id: str | None = None


TableEvent = Annotated[
    TurnStarted | NarrationDelta | TurnFinished | PartyUpdated | EncounterUpdated | TableError,
    Field(discriminator="type"),
]

table_event_adapter: TypeAdapter[TableEvent] = TypeAdapter(TableEvent)
