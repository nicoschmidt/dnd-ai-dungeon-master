"""Damage, in the order docs/domain/combat.md gives, and the 0 hit point rules."""

from dungeon_master.rules.damage import Defences, HitPoints, apply_damage
from dungeon_master.rules.results import Refused


def to_character(hp: HitPoints, amount: int, conditions=(), **flags):
    return apply_damage(hp, set(conditions), amount, "slashing", kind="character", **flags)


def to_opponent(hp: HitPoints, amount: int, damage_type="fire", defences=Defences(), **flags):
    return apply_damage(hp, set(), amount, damage_type, kind="opponent", defences=defences, **flags)


def test_damage_comes_off_current_hit_points() -> None:
    result = to_character(HitPoints(28, 28), 7)

    assert result.hit_points == HitPoints(21, 28, 0)
    assert result.conditions == frozenset()


def test_temporary_hit_points_absorb_part_of_a_hit_first() -> None:
    result = to_character(HitPoints(20, 28, 5), 8)

    assert (result.absorbed, result.hit_points) == (5, HitPoints(17, 28, 0))


def test_temporary_hit_points_can_absorb_all_of_it() -> None:
    result = to_character(HitPoints(20, 28, 10), 8)

    assert (result.absorbed, result.hit_points) == (8, HitPoints(20, 28, 2))


def test_hit_points_never_fall_below_zero() -> None:
    result = to_opponent(HitPoints(5, 59), 12)

    assert result.hit_points.current == 0


def test_a_character_at_zero_falls_unconscious() -> None:
    result = to_character(HitPoints(6, 28), 10, conditions={"prone"})

    assert result.hit_points.current == 0
    assert result.conditions == {"prone", "unconscious"}
    assert not result.killed


def test_remaining_damage_exactly_equal_to_the_maximum_kills() -> None:
    result = to_character(HitPoints(6, 28), 6 + 28)

    assert result.killed
    assert result.conditions == {"dead"}


def test_remaining_damage_one_short_of_the_maximum_does_not_kill() -> None:
    result = to_character(HitPoints(6, 28), 6 + 27)

    assert not result.killed
    assert result.conditions == {"unconscious"}


def test_damage_at_zero_is_one_failed_death_save_and_ends_stable() -> None:
    result = to_character(HitPoints(0, 28), 4, conditions={"unconscious", "stable"})

    assert result.death_save_failures == 1
    assert result.conditions == {"unconscious"}


def test_a_critical_hit_at_zero_is_two_failed_death_saves() -> None:
    result = to_character(HitPoints(0, 28), 4, conditions={"unconscious"}, critical=True)

    assert result.death_save_failures == 2


def test_damage_at_zero_reaching_the_maximum_kills() -> None:
    result = to_character(HitPoints(0, 28), 28, conditions={"unconscious"})

    assert result.killed
    assert result.death_save_failures == 0
    assert result.conditions == {"dead"}


def test_damage_to_a_dead_target_is_refused() -> None:
    assert isinstance(to_character(HitPoints(0, 28), 4, conditions={"dead"}), Refused)


def test_negative_damage_is_refused() -> None:
    assert isinstance(to_character(HitPoints(10, 28), -1), Refused)


def test_the_opponent_at_zero_is_defeated() -> None:
    assert to_opponent(HitPoints(5, 59), 5).defeated
    assert not to_opponent(HitPoints(6, 59), 5).defeated


def test_the_opponent_gains_no_conditions_and_makes_no_death_saves() -> None:
    result = to_opponent(HitPoints(0, 59), 5)

    assert (result.conditions, result.death_save_failures) == (frozenset(), 0)


def test_resistance_halves_rounding_down() -> None:
    result = to_opponent(HitPoints(59, 59), 9, defences=Defences(resistances=frozenset({"fire"})))

    assert result.taken == 4


def test_vulnerability_doubles() -> None:
    result = to_opponent(HitPoints(59, 59), 9, defences=Defences(vulnerabilities=frozenset({"fire"})))

    assert result.taken == 18


def test_immunity_takes_nothing() -> None:
    result = to_opponent(HitPoints(59, 59), 9, defences=Defences(immunities=frozenset({"fire"})))

    assert (result.taken, result.hit_points.current) == (0, 59)


def test_a_defence_against_another_type_changes_nothing() -> None:
    result = to_opponent(HitPoints(59, 59), 9, defences=Defences(resistances=frozenset({"cold"})))

    assert result.taken == 9


def test_halving_on_a_save_comes_before_resistance() -> None:
    result = to_opponent(
        HitPoints(59, 59),
        11,
        defences=Defences(resistances=frozenset({"fire"})),
        halved_on_save=True,
    )

    assert result.taken == 2  # 11 // 2 = 5, then 5 // 2 = 2


def test_the_result_names_what_was_reported_and_what_was_taken() -> None:
    result = to_character(HitPoints(28, 28), 9, halved_on_save=True)

    assert (result.reported, result.taken) == (9, 4)
