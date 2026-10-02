"""The turn order and its tie rules (docs/domain/combat.md)."""

import pytest

from dungeon_master.rules.initiative import InitiativeEntry, turn_order


def character(id: str, total: int, dex: int = 0) -> InitiativeEntry:
    return InitiativeEntry(id, "character", total, dex)


def opponent(total: int, dex: int = 0) -> InitiativeEntry:
    return InitiativeEntry("ogre", "opponent", total, dex)


def ids(entries) -> list[str]:
    return [e.id for e in turn_order(entries)]


def test_highest_total_goes_first() -> None:
    assert ids([character("a", 8), opponent(15), character("b", 21)]) == ["b", "ogre", "a"]


def test_tied_characters_keep_the_order_they_were_reported_in() -> None:
    assert ids([character("a", 12, dex=1), character("b", 12, dex=4)]) == ["a", "b"]


def test_a_tie_with_the_opponent_goes_to_the_higher_dexterity_modifier() -> None:
    assert ids([character("a", 12, dex=3), opponent(12, dex=-1)]) == ["a", "ogre"]
    assert ids([character("a", 12, dex=-1), opponent(12, dex=3)]) == ["ogre", "a"]


def test_a_tie_on_dexterity_too_goes_to_the_character() -> None:
    assert ids([opponent(12, dex=2), character("a", 12, dex=2)]) == ["a", "ogre"]


def test_in_a_three_way_tie_each_character_is_placed_against_the_opponent() -> None:
    # a would go before b by reporting order, but only b beats the opponent.
    entries = [character("a", 12, dex=1), character("b", 12, dex=5), opponent(12, dex=3)]

    assert ids(entries) == ["b", "ogre", "a"]


def test_more_than_one_opponent_is_not_iteration_001() -> None:
    with pytest.raises(ValueError):
        turn_order([opponent(10), opponent(12)])
