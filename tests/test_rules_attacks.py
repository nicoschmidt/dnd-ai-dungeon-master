"""Attacks and saving throws (docs/domain/combat.md), on fixed dice."""

from fakes import FixedDice

from dungeon_master.rules.attacks import AttackProfile, opponent_attack, resolve_player_attack
from dungeon_master.rules.saving_throws import opponent_saving_throw

GREATCLUB = AttackProfile(
    name="Greatclub",
    bonus=6,
    damage_dice=2,
    damage_sides=8,
    damage_modifier=4,
    damage_type="bludgeoning",
)


# The player's attack: a reported total against the hidden armour class.


def test_a_total_that_reaches_the_armour_class_hits() -> None:
    assert resolve_player_attack(15, None, 15) == "hit"
    assert resolve_player_attack(14, None, 15) == "miss"


def test_a_natural_20_is_a_critical_hit_even_below_the_armour_class() -> None:
    assert resolve_player_attack(22, 20, 25) == "critical_hit"


def test_a_natural_1_misses_even_with_a_total_that_would_hit() -> None:
    assert resolve_player_attack(18, 1, 11) == "miss"


# The opponent's attack: rolled by the code.


def test_the_opponents_attack_hits_and_rolls_damage() -> None:
    dice = FixedDice(10, 3, 5)

    result = opponent_attack(dice, GREATCLUB, target_armour_class=16)

    assert result.outcome == "hit"
    assert result.attack_roll.total == 16
    assert result.damage_roll.dice == (3, 5)
    assert result.damage == 12
    assert dice.unused == []


def test_a_miss_rolls_no_damage() -> None:
    dice = FixedDice(9)

    result = opponent_attack(dice, GREATCLUB, target_armour_class=16)

    assert (result.outcome, result.damage_roll, result.damage) == ("miss", None, 0)
    assert result.rolls == (result.attack_roll,)


def test_a_critical_hit_rolls_the_damage_dice_twice_and_the_modifier_once() -> None:
    result = opponent_attack(FixedDice(20, 1, 2, 3, 4), GREATCLUB, target_armour_class=30)

    assert result.outcome == "critical_hit"
    assert result.damage_roll.dice == (1, 2, 3, 4)
    assert result.damage == 1 + 2 + 3 + 4 + 4


def test_the_opponents_natural_1_misses_whatever_the_bonus() -> None:
    result = opponent_attack(FixedDice(1), GREATCLUB, target_armour_class=5)

    assert result.outcome == "miss"


def test_advantage_keeps_the_higher_die_for_the_attack() -> None:
    result = opponent_attack(FixedDice(3, 12, 4, 4), GREATCLUB, 16, mode="advantage")

    assert result.attack_roll.dice == (3, 12)
    assert result.outcome == "hit"


def test_disadvantage_keeps_the_lower_die_for_the_attack() -> None:
    result = opponent_attack(FixedDice(18, 3), GREATCLUB, 16, mode="disadvantage")

    assert result.attack_roll.kept == (3,)
    assert result.outcome == "miss"


def test_damage_is_never_negative() -> None:
    feeble = AttackProfile("Slap", 0, 1, 4, -3, "bludgeoning")

    result = opponent_attack(FixedDice(15, 1), feeble, target_armour_class=10)

    assert result.damage_roll.total == -2
    assert result.damage == 0


# The opponent's saving throw.


def test_a_saving_throw_succeeds_when_it_reaches_the_dc() -> None:
    assert opponent_saving_throw(FixedDice(11), "dexterity", 2, 13).success
    assert not opponent_saving_throw(FixedDice(10), "dexterity", 2, 13).success


def test_a_saving_throw_records_its_roll_in_the_given_mode() -> None:
    result = opponent_saving_throw(FixedDice(15, 6), "wisdom", -1, 13, "disadvantage")

    assert (result.roll.dice, result.roll.total, result.success) == ((15, 6), 5, False)
