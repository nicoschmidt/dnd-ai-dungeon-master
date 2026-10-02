"""The opponent's saving throws against a player's effect."""

from dataclasses import dataclass
from typing import Literal

from .dice import Mode, RandomSource, RollRecord, roll_d20

Ability = Literal["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]


@dataclass(frozen=True)
class SavingThrowResult:
    success: bool
    roll: RollRecord


def opponent_saving_throw(
    source: RandomSource, ability: Ability, modifier: int, dc: int, mode: Mode = "normal"
) -> SavingThrowResult:
    """Succeeds when the total reaches the DC. A natural 1 or 20 has no special effect."""
    roll = roll_d20(source, f"{ability} saving throw against DC {dc}", modifier, mode)
    return SavingThrowResult(success=roll.total >= dc, roll=roll)
