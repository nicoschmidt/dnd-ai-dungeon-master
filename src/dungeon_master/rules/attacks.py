"""Attacks: the player's, reported as a total, and the opponent's, rolled by the code."""

from dataclasses import dataclass
from typing import Literal

from .damage import DamageType
from .dice import Mode, RandomSource, RollRecord, roll_d20, roll_dice

AttackOutcome = Literal["miss", "hit", "critical_hit"]


def resolve_player_attack(
    total: int, natural_roll: int | None, armour_class: int
) -> AttackOutcome:
    """A natural 1 misses and a natural 20 is a critical hit, whatever the total."""
    if natural_roll == 1:
        return "miss"
    if natural_roll == 20:
        return "critical_hit"
    return "hit" if total >= armour_class else "miss"


@dataclass(frozen=True)
class AttackProfile:
    """One of the opponent's attacks, as its stat block declares it."""

    name: str
    bonus: int
    damage_dice: int
    damage_sides: int
    damage_modifier: int
    damage_type: DamageType


@dataclass(frozen=True)
class OpponentAttackResult:
    outcome: AttackOutcome
    attack_roll: RollRecord
    damage_roll: RollRecord | None

    @property
    def damage(self) -> int:
        """The damage before the target's temporary hit points. Never negative."""
        return max(0, self.damage_roll.total) if self.damage_roll else 0

    @property
    def rolls(self) -> tuple[RollRecord, ...]:
        return (self.attack_roll,) + ((self.damage_roll,) if self.damage_roll else ())


def opponent_attack(
    source: RandomSource,
    attack: AttackProfile,
    target_armour_class: int,
    mode: Mode = "normal",
) -> OpponentAttackResult:
    """Roll to hit and, on a hit, damage: the dice twice on a critical hit, the modifier once."""
    attack_roll = roll_d20(source, f"{attack.name}: attack", attack.bonus, mode)
    outcome = resolve_player_attack(attack_roll.total, attack_roll.kept[0], target_armour_class)
    if outcome == "miss":
        return OpponentAttackResult(outcome, attack_roll, None)
    dice = attack.damage_dice * (2 if outcome == "critical_hit" else 1)
    damage_roll = roll_dice(
        source, f"{attack.name}: damage", dice, attack.damage_sides, attack.damage_modifier
    )
    return OpponentAttackResult(outcome, attack_roll, damage_roll)
