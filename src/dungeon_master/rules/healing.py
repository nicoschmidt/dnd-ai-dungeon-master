"""Healing and temporary hit points, on a character."""

from collections.abc import Set
from dataclasses import dataclass

from .damage import HitPoints
from .results import Refused


@dataclass(frozen=True)
class HealingResult:
    healed: int
    """What was actually restored, after the cap at the maximum."""
    hit_points: HitPoints
    conditions: frozenset[str]


def heal(hit_points: HitPoints, conditions: Set[str], amount: int) -> HealingResult | Refused:
    """Never above the maximum. Coming up from 0 ends `unconscious` and `stable`."""
    if amount < 0:
        return Refused("Healing cannot be negative.")
    if "dead" in conditions:
        return Refused("A dead character cannot be healed.")

    current = min(hit_points.maximum, hit_points.current + amount)
    after = set(conditions)
    if hit_points.current == 0 and current > 0:
        after -= {"unconscious", "stable"}
    return HealingResult(
        healed=current - hit_points.current,
        hit_points=HitPoints(current, hit_points.maximum, hit_points.temporary),
        conditions=frozenset(after),
    )


def set_temporary_hit_points(hit_points: HitPoints, amount: int) -> HitPoints | Refused:
    """Temporary hit points do not stack: the higher value is kept."""
    if amount < 0:
        return Refused("Temporary hit points cannot be negative.")
    return HitPoints(
        hit_points.current, hit_points.maximum, max(hit_points.temporary, amount)
    )
