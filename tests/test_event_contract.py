"""The table's event contract serialises as the client expects it (ADR-0005)."""

import json

import pytest
from pydantic import ValidationError

from dungeon_master.events import schema
from dungeon_master.events.contract import (
    DeclaredAction,
    EncounterUpdated,
    NarrationDelta,
    PartyUpdated,
    TableError,
    TurnFinished,
    TurnStarted,
    table_event_adapter,
)
from dungeon_master.session.party import Character
from dungeon_master.session.state import Combatant, Encounter


def _character(**overrides) -> Character:
    fields = {
        "id": "brann",
        "name": "Brann",
        "character_class": "Fighter",
        "level": 3,
        "armour_class": 16,
        "max_hit_points": 28,
        "current_hit_points": 28,
    }
    return Character(**(fields | overrides))


EVENTS = [
    TurnStarted(turn_id="t1", action=DeclaredAction(text="I attack, 17", character_id="brann")),
    NarrationDelta(turn_id="t1", text="Der Oger "),
    TurnFinished(turn_id="t1"),
    PartyUpdated(party=[_character(current_hit_points=17, conditions=["prone"])]),
    EncounterUpdated(
        encounter=Encounter(
            opponent_name="Ogre",
            round=1,
            turn_order=[
                Combatant(kind="character", id="brann", name="Brann"),
                Combatant(kind="opponent", id="ogre", name="Ogre"),
            ],
            current_turn=0,
        )
    ),
    EncounterUpdated(encounter=None),
    TableError(code="agent_failed", message="Declare the action again.", turn_id="t1"),
]


@pytest.mark.parametrize("event", EVENTS, ids=lambda e: e.type)
def test_every_event_survives_the_wire(event) -> None:
    wire = event.model_dump_json()

    assert table_event_adapter.validate_json(wire) == event


@pytest.mark.parametrize("event", EVENTS, ids=lambda e: e.type)
def test_every_field_is_on_the_wire_even_when_it_has_its_default(event) -> None:
    on_the_wire = json.loads(event.model_dump_json())

    assert set(on_the_wire) == set(type(event).model_fields)


def test_the_event_type_is_named_on_the_wire() -> None:
    wire = json.loads(NarrationDelta(turn_id="t1", text="Der ").model_dump_json())

    assert wire == {"type": "narration_delta", "turn_id": "t1", "text": "Der "}


def test_an_unknown_event_type_is_rejected() -> None:
    with pytest.raises(ValidationError):
        table_event_adapter.validate_python({"type": "opponent_updated", "hit_points": 12})


def test_an_event_with_an_unknown_field_is_rejected() -> None:
    with pytest.raises(ValidationError):
        table_event_adapter.validate_python(
            {"type": "narration_delta", "turn_id": "t1", "text": "x", "armour_class": 15}
        )


def test_a_character_cannot_have_more_hit_points_than_its_maximum() -> None:
    with pytest.raises(ValidationError):
        _character(current_hit_points=29)


def test_a_declared_action_needs_text() -> None:
    with pytest.raises(ValidationError):
        DeclaredAction(text="")


def test_the_committed_schema_is_current() -> None:
    committed = schema.DEFAULT_OUTPUT

    assert committed.is_file() and committed.read_text() == schema.render(), (
        f"{committed.name} is stale. Run `python -m dungeon_master.events.schema`, "
        "then `npm run contract` in client/."
    )
