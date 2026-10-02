"""Attacks per turn, the next turn, and an outcome the state must not contradict."""

from dungeon_master.rules.encounter import (
    CharacterStatus,
    check_attack_allowed,
    check_outcome,
    next_turn,
)
from dungeon_master.rules.results import Refused

UP = CharacterStatus("Brann", 12, frozenset())
DOWN = CharacterStatus("Mira", 0, frozenset({"unconscious"}))
DEAD = CharacterStatus("Tov", 0, frozenset({"dead"}))


def test_the_opponent_may_attack_as_often_as_its_stat_block_declares() -> None:
    assert check_attack_allowed(0, 2) is None
    assert check_attack_allowed(1, 2) is None
    assert isinstance(check_attack_allowed(2, 2), Refused)


def test_the_first_turn_starts_round_one() -> None:
    assert next_turn(3, None, 0) == (0, 1)


def test_the_turn_passes_down_the_order() -> None:
    assert next_turn(3, 0, 1) == (1, 1)


def test_after_the_last_combatant_a_new_round_begins() -> None:
    assert next_turn(3, 2, 1) == (0, 2)


def test_opponent_defeated_is_refused_while_it_has_hit_points() -> None:
    assert isinstance(check_outcome("opponent_defeated", 3, [UP]), Refused)
    assert check_outcome("opponent_defeated", 0, [UP]) is None


def test_party_defeated_is_refused_while_anyone_is_conscious() -> None:
    refused = check_outcome("party_defeated", 30, [DOWN, UP, DEAD])

    assert isinstance(refused, Refused)
    assert "Brann" in refused.reason
    assert check_outcome("party_defeated", 30, [DOWN, DEAD]) is None


def test_fleeing_and_parley_are_the_models_judgement() -> None:
    for outcome in ("opponent_fled", "party_fled", "parley"):
        assert check_outcome(outcome, 30, [UP]) is None
