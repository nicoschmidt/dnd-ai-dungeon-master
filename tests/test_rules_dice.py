"""Dice the code rolls, on fixed sequences."""

import random

import pytest
from fakes import FixedDice

from dungeon_master.rules.dice import roll_d20, roll_dice


def test_a_normal_d20_keeps_its_one_die() -> None:
    roll = roll_d20(FixedDice(14), "test", 5)

    assert (roll.dice, roll.kept, roll.total, roll.expression) == ((14,), (14,), 19, "1d20+5")


def test_advantage_rolls_two_and_keeps_the_higher() -> None:
    roll = roll_d20(FixedDice(4, 17), "test", 2, "advantage")

    assert (roll.dice, roll.kept, roll.total, roll.expression) == ((4, 17), (17,), 19, "2d20kh1+2")


def test_disadvantage_rolls_two_and_keeps_the_lower() -> None:
    roll = roll_d20(FixedDice(4, 17), "test", -1, "disadvantage")

    assert (roll.dice, roll.kept, roll.total, roll.expression) == ((4, 17), (4,), 3, "2d20kl1-1")


def test_damage_dice_add_the_modifier_once() -> None:
    roll = roll_dice(FixedDice(3, 8), "test", 2, 8, 4)

    assert (roll.dice, roll.total, roll.expression) == ((3, 8), 15, "2d8+4")


def test_a_roll_records_its_purpose_and_mode() -> None:
    roll = roll_d20(FixedDice(10), "Greatclub: attack", 6)

    assert (roll.purpose, roll.mode, roll.modifier) == ("Greatclub: attack", "normal", 6)


def test_the_same_seed_rolls_the_same_dice() -> None:
    first = roll_dice(random.Random(42), "t", 10, 20).dice
    second = roll_dice(random.Random(42), "t", 10, 20).dice

    assert first == second


def test_fixed_dice_refuse_a_value_the_die_cannot_show() -> None:
    with pytest.raises(AssertionError):
        roll_dice(FixedDice(9), "t", 1, 8)
