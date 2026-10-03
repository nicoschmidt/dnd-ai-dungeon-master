"""Entering the party (#30): validation, ids, and the event the table receives."""

import json
from pathlib import Path

import pytest
from fakes import ScriptedDungeonMaster
from pydantic import ValidationError
from table_client import client, frames

from dungeon_master.api.app import create_app
from dungeon_master.orchestration.stand_in import StandInDungeonMaster
from dungeon_master.session.party import Character, CharacterEntry, PartyEntry, build_party
from dungeon_master.session.state import Encounter

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def entry(name: str = "Brann", **overrides) -> dict:
    fields = {
        "name": name,
        "character_class": "Fighter",
        "level": 3,
        "armour_class": 16,
        "max_hit_points": 28,
    }
    return fields | overrides


def party(*entries: dict) -> PartyEntry:
    return PartyEntry(characters=[CharacterEntry(**e) for e in entries])


# Building the party from what was typed in.


def test_current_hit_points_default_to_the_maximum() -> None:
    [brann] = build_party(party(entry()), [])

    assert (brann.current_hit_points, brann.temporary_hit_points) == (28, 0)


def test_current_hit_points_can_be_entered() -> None:
    [brann] = build_party(party(entry(current_hit_points=17)), [])

    assert brann.current_hit_points == 17


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Brann", "brann"),
        ("Jörg Weiß", "jorg-weiss"),
        ("  Mira the Bold! ", "mira-the-bold"),
        ("李", "character-1"),
    ],
)
def test_the_id_comes_from_the_name(name: str, expected: str) -> None:
    [character] = build_party(party(entry(name)), [])

    assert character.id == expected


def test_names_that_fold_to_the_same_id_get_distinct_ids() -> None:
    ids = [c.id for c in build_party(party(entry("Jörg"), entry("Jorg!")), [])]

    assert ids == ["jorg", "jorg-2"]


def test_no_character_takes_the_id_the_tools_use_for_the_opponent() -> None:
    [character] = build_party(party(entry("Opponent")), [])

    assert character.id == "opponent-2"


def test_a_character_entered_again_keeps_its_conditions() -> None:
    before = build_party(party(entry()), [])
    before[0].conditions = ["poisoned"]

    [after] = build_party(party(entry(armour_class=18)), before)

    assert (after.armour_class, after.conditions) == (18, ["poisoned"])


# Validation: the backend's half of "validated at both ends".


@pytest.mark.parametrize(
    "overrides",
    [
        {"current_hit_points": 29},
        {"level": 0},
        {"level": 21},
        {"max_hit_points": 0},
        {"armour_class": -1},
        {"temporary_hit_points": -1},
        {"name": "   "},
        {"character_class": ""},
        {"conditions": ["prone"]},
    ],
)
def test_an_invalid_character_is_rejected(overrides: dict) -> None:
    with pytest.raises(ValidationError):
        CharacterEntry(**entry(**overrides))


def test_two_characters_with_the_same_name_are_rejected() -> None:
    with pytest.raises(ValidationError):
        party(entry("Brann"), entry("brann"))


# Over HTTP, and on the table's stream.


def _app(tmp_path: Path, dungeon_master=None):
    return create_app(tmp_path / "no-build", dungeon_master or ScriptedDungeonMaster())


async def test_entering_the_party_produces_exactly_one_party_updated(tmp_path: Path) -> None:
    app = _app(tmp_path)
    table = app.state.session

    async with client(app) as http:
        response = await http.put(
            "/api/session/party", json={"characters": [entry(), entry("Mira", max_hit_points=9)]}
        )
        table.events.close()
        stream = await http.get("/api/session/stream")

    assert response.status_code == 200
    assert [c["id"] for c in response.json()] == ["brann", "mira"]
    received = frames(stream.text)
    assert [f["event"] for f in received] == ["party_updated"]
    sent = [Character.model_validate(c) for c in json.loads(received[0]["data"])["party"]]
    assert sent == table.state.party


async def test_an_invalid_party_changes_nothing(tmp_path: Path) -> None:
    app = _app(tmp_path)

    async with client(app) as http:
        response = await http.put(
            "/api/session/party", json={"characters": [entry(current_hit_points=99)]}
        )

    assert response.status_code == 422
    assert app.state.session.state.party == []


async def test_the_party_is_fixed_once_the_encounter_has_started(tmp_path: Path) -> None:
    app = _app(tmp_path)
    app.state.session.state.encounter = Encounter(opponent_name="Ogre")

    async with client(app) as http:
        response = await http.put("/api/session/party", json={"characters": [entry()]})

    assert response.status_code == 409
    assert app.state.session.state.party == []


async def test_an_action_for_a_character_not_in_the_party_is_rejected(tmp_path: Path) -> None:
    app = _app(tmp_path)

    async with client(app) as http:
        response = await http.post(
            "/api/session/actions", json={"text": "I attack", "character_id": "nobody"}
        )

    assert response.status_code == 422


async def test_the_acting_character_reaches_the_dungeon_master(tmp_path: Path) -> None:
    app = _app(tmp_path, StandInDungeonMaster(delay=0))
    table = app.state.session

    async with client(app) as http:
        await http.put("/api/session/party", json={"characters": [entry()]})
        response = await http.post(
            "/api/session/actions", json={"text": "I attack, 17", "character_id": "brann"}
        )
        await table.turns.wait()
        table.events.close()
        stream = await http.get("/api/session/stream")

    assert response.status_code == 202
    narration = "".join(
        json.loads(f["data"])["text"] for f in frames(stream.text) if f["event"] == "narration_delta"
    )
    assert narration.endswith("You declared, Brann: I attack, 17")
