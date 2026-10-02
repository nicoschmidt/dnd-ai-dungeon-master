"""Healing and temporary hit points (docs/domain/combat.md)."""

from dungeon_master.rules.damage import HitPoints
from dungeon_master.rules.healing import heal, set_temporary_hit_points
from dungeon_master.rules.results import Refused


def test_healing_adds_to_current_hit_points() -> None:
    result = heal(HitPoints(10, 28), set(), 7)

    assert (result.healed, result.hit_points) == (7, HitPoints(17, 28))


def test_healing_past_the_maximum_stops_at_it() -> None:
    result = heal(HitPoints(25, 28), set(), 10)

    assert (result.healed, result.hit_points.current) == (3, 28)


def test_healing_from_zero_ends_unconscious_and_stable() -> None:
    result = heal(HitPoints(0, 28), {"unconscious", "stable", "prone"}, 1)

    assert result.conditions == {"prone"}


def test_healing_leaves_temporary_hit_points_alone() -> None:
    assert heal(HitPoints(10, 28, 4), set(), 3).hit_points.temporary == 4


def test_a_dead_character_cannot_be_healed() -> None:
    assert isinstance(heal(HitPoints(0, 28), {"dead"}, 5), Refused)


def test_temporary_hit_points_do_not_stack_the_higher_value_is_kept() -> None:
    assert set_temporary_hit_points(HitPoints(10, 28, 5), 8).temporary == 8
    assert set_temporary_hit_points(HitPoints(10, 28, 8), 5).temporary == 8


def test_negative_amounts_are_refused() -> None:
    assert isinstance(heal(HitPoints(10, 28), set(), -1), Refused)
    assert isinstance(set_temporary_hit_points(HitPoints(10, 28), -1), Refused)
