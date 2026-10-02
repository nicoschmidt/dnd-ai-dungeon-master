"""The opponent through the adventure port (#31, ADR-0003)."""

import copy
import json
import re
from importlib.resources import files

import pytest
from fakes import FixedDice
from pydantic import ValidationError

from dungeon_master.adventure.builtin import ITERATION_001, iteration_001_repository
from dungeon_master.adventure.models import EncounterSetup, Monster
from dungeon_master.adventure.repository import InMemoryAdventureRepository, UnknownContent
from dungeon_master.rules.attacks import AttackProfile, opponent_attack
from dungeon_master.rules.damage import Defences

OGRE_JSON = files("dungeon_master.adventure").joinpath(
    "fixtures", ITERATION_001, "monsters", "ogre.json"
)


@pytest.fixture
def ogre_data() -> dict:
    return json.loads(OGRE_JSON.read_text(encoding="utf-8"))


@pytest.fixture
def repository() -> InMemoryAdventureRepository:
    return iteration_001_repository()


# The port returns the opponent.


def test_the_port_returns_the_ogre_as_srd_5_2_1_gives_it(repository) -> None:
    ogre = repository.monster("ogre")

    # SRD 5.2.1, page 312.
    assert (ogre.name, ogre.armour_class, ogre.hit_points) == ("Ogre", 11, 68)
    assert ogre.dexterity_modifier == -1
    assert ogre.saving_throws.model_dump() == {
        "strength": 4,
        "dexterity": -1,
        "constitution": 3,
        "intelligence": -3,
        "wisdom": -2,
        "charisma": -2,
    }
    assert ogre.attacks_per_turn == 1
    assert [a.name for a in ogre.attacks] == ["Greatclub", "Javelin"]


def test_an_attack_bridges_to_the_rules_core(repository) -> None:
    greatclub = repository.monster("ogre").attack("greatclub")

    assert greatclub == AttackProfile("Greatclub", 6, 2, 8, 4, "bludgeoning")


def test_the_ogre_has_no_defences(repository) -> None:
    assert repository.monster("ogre").defences == Defences()


def test_the_rules_core_rolls_the_ogres_attack(repository) -> None:
    dice = FixedDice(10, 3, 5)

    result = opponent_attack(dice, repository.monster("ogre").attack("Greatclub"), 16)

    assert (result.outcome, result.attack_roll.total, result.damage) == ("hit", 16, 3 + 5 + 4)
    assert result.damage_roll.expression == "2d8+4"


# Unknown content fails, naming what was asked for.


def test_an_unknown_monster_fails_with_a_message_that_names_it(repository) -> None:
    with pytest.raises(UnknownContent, match="'owlbear'.*Known: ogre"):
        repository.monster("owlbear")


def test_an_unknown_attack_fails_with_the_attacks_there_are(repository) -> None:
    with pytest.raises(KeyError, match="Greatclub, Javelin"):
        repository.monster("ogre").attack("Bite")


def test_an_encounter_whose_opponent_is_missing_is_refused_at_load() -> None:
    setup = EncounterSetup(id="fight", opponent_id="owlbear", premise="A fight.")

    with pytest.raises(UnknownContent, match="owlbear"):
        InMemoryAdventureRepository([], [setup])


# The premise.


def test_the_built_in_fight_is_against_an_opponent_that_exists(repository) -> None:
    setup = repository.encounter_setup(ITERATION_001)

    assert repository.monster(setup.opponent_id).name == "Ogre"


def test_the_premise_is_two_or_three_sentences(repository) -> None:
    premise = repository.encounter_setup(ITERATION_001).premise

    assert 2 <= len(re.findall(r"[.!?](\s|$)", premise)) <= 3


# The model rejects broken content.


@pytest.mark.parametrize(
    "breakage",
    [
        lambda d: d.pop("armour_class"),
        lambda d: d["attacks"][0].update(damage_die=7),
        lambda d: d["attacks"][0].update(damage_type="sonic"),
        lambda d: d.update(attacks_per_turn=0),
        lambda d: d.update(attacks=[]),
        lambda d: d.update(hit_points=0),
        lambda d: d["saving_throws"].pop("wisdom"),
        lambda d: d.update(id="Ogre The Great"),
        lambda d: d.update(challenge_rating=2),
    ],
    ids=[
        "missing field",
        "no d7",
        "unknown damage type",
        "no attacks per turn",
        "no attacks",
        "no hit points",
        "missing save",
        "id not a slug",
        "unknown field",
    ],
)
def test_broken_monster_data_is_rejected(ogre_data: dict, breakage) -> None:
    broken = copy.deepcopy(ogre_data)
    breakage(broken)

    with pytest.raises(ValidationError):
        Monster.model_validate(broken)


def test_content_cannot_be_changed_once_loaded(repository) -> None:
    with pytest.raises(ValidationError):
        repository.monster("ogre").hit_points = 1  # type: ignore[misc]
