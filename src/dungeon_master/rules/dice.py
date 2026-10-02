"""The dice the code rolls, and the record of every roll.

The code rolls only for the opponent, never for a player character
(docs/domain/combat.md). The random source is injected: seeded per session at
the table, a fixed sequence in tests.
"""

from dataclasses import dataclass
from typing import Literal, Protocol

Mode = Literal["normal", "advantage", "disadvantage"]


class RandomSource(Protocol):
    """Anything that rolls like `random.Random.randint`, inclusive at both ends."""

    def randint(self, a: int, b: int) -> int: ...


@dataclass(frozen=True)
class RollRecord:
    """One roll, complete enough to check it by hand."""

    purpose: str
    expression: str
    dice: tuple[int, ...]
    """Every die as it fell."""
    kept: tuple[int, ...]
    """The dice that count: with advantage or disadvantage, one of two."""
    modifier: int
    mode: Mode
    total: int


def _with_modifier(dice: str, modifier: int) -> str:
    return f"{dice}{modifier:+d}" if modifier else dice


def roll_d20(
    source: RandomSource, purpose: str, modifier: int, mode: Mode = "normal"
) -> RollRecord:
    """A d20 test: one die, or the higher or lower of two."""
    if mode == "normal":
        dice = (source.randint(1, 20),)
        kept = dice
        expression = "1d20"
    else:
        dice = (source.randint(1, 20), source.randint(1, 20))
        kept = (max(dice),) if mode == "advantage" else (min(dice),)
        expression = "2d20kh1" if mode == "advantage" else "2d20kl1"
    return RollRecord(
        purpose=purpose,
        expression=_with_modifier(expression, modifier),
        dice=dice,
        kept=kept,
        modifier=modifier,
        mode=mode,
        total=kept[0] + modifier,
    )


def roll_dice(
    source: RandomSource, purpose: str, count: int, sides: int, modifier: int = 0
) -> RollRecord:
    """`count` dice of `sides` sides, summed, plus the modifier once."""
    dice = tuple(source.randint(1, sides) for _ in range(count))
    return RollRecord(
        purpose=purpose,
        expression=_with_modifier(f"{count}d{sides}", modifier),
        dice=dice,
        kept=dice,
        modifier=modifier,
        mode="normal",
        total=sum(dice) + modifier,
    )
