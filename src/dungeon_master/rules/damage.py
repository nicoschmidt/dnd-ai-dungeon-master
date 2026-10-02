"""Damage, applied in the order docs/domain/combat.md gives, whoever the target is."""

from collections.abc import Set
from dataclasses import dataclass, field
from typing import Literal

from .results import Refused

DamageType = Literal[
    "acid",
    "bludgeoning",
    "cold",
    "fire",
    "force",
    "lightning",
    "necrotic",
    "piercing",
    "poison",
    "psychic",
    "radiant",
    "slashing",
    "thunder",
]

Kind = Literal["character", "opponent"]


@dataclass(frozen=True)
class Defences:
    resistances: frozenset[DamageType] = field(default_factory=frozenset)
    vulnerabilities: frozenset[DamageType] = field(default_factory=frozenset)
    immunities: frozenset[DamageType] = field(default_factory=frozenset)


NO_DEFENCES = Defences()


@dataclass(frozen=True)
class HitPoints:
    current: int
    maximum: int
    temporary: int = 0


@dataclass(frozen=True)
class DamageResult:
    reported: int
    """The damage as reported or rolled."""
    taken: int
    """After halving on a save, and after resistance, vulnerability or immunity."""
    absorbed: int
    """The part of `taken` the temporary hit points absorbed."""
    hit_points: HitPoints
    conditions: frozenset[str]
    death_save_failures: int
    """Failed death saves the player marks on the sheet: damage at 0 hit points."""
    killed: bool
    """A character whose remaining damage reached its maximum hit points."""
    defeated: bool
    """The opponent at 0 hit points."""


def apply_damage(
    hit_points: HitPoints,
    conditions: Set[str],
    amount: int,
    damage_type: DamageType,
    *,
    kind: Kind,
    defences: Defences = NO_DEFENCES,
    halved_on_save: bool = False,
    critical: bool = False,
) -> DamageResult | Refused:
    if amount < 0:
        return Refused("Damage cannot be negative.")
    if "dead" in conditions:
        return Refused("The target is dead.")

    taken = amount // 2 if halved_on_save else amount
    if damage_type in defences.immunities:
        taken = 0
    else:
        if damage_type in defences.resistances:
            taken //= 2
        if damage_type in defences.vulnerabilities:
            taken *= 2

    absorbed = min(hit_points.temporary, taken)
    remaining = taken - absorbed
    current = max(0, hit_points.current - remaining)
    # The damage left over once current hit points reach 0. For a target
    # already at 0, that is all of it.
    left_over = max(0, remaining - hit_points.current)

    after = set(conditions)
    death_save_failures = 0
    killed = False
    if kind == "character" and remaining > 0:
        if current == 0 and left_over >= hit_points.maximum:
            killed = True
            after -= {"unconscious", "stable"}
            after.add("dead")
        elif hit_points.current == 0:
            death_save_failures = 2 if critical else 1
            after.discard("stable")
        elif current == 0:
            after.add("unconscious")

    return DamageResult(
        reported=amount,
        taken=taken,
        absorbed=absorbed,
        hit_points=HitPoints(current, hit_points.maximum, hit_points.temporary - absorbed),
        conditions=frozenset(after),
        death_save_failures=death_save_failures,
        killed=killed,
        defeated=kind == "opponent" and current == 0,
    )
