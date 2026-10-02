"""The turn order, from the reported and the rolled initiative."""

from collections.abc import Sequence
from dataclasses import dataclass
from itertools import groupby
from typing import Literal


@dataclass(frozen=True)
class InitiativeEntry:
    id: str
    kind: Literal["character", "opponent"]
    total: int
    dexterity_modifier: int


def turn_order(entries: Sequence[InitiativeEntry]) -> list[InitiativeEntry]:
    """Highest total first. `entries` lists the characters in the order reported.

    Ties between characters keep the order they were reported in. In a tie
    with the opponent, a character goes first when its Dexterity modifier is
    at least the opponent's, and after it otherwise. Within a tie that holds
    the opponent, the characters who go first keep their reported order among
    themselves, and so do the characters who go after.
    """
    opponents = [e for e in entries if e.kind == "opponent"]
    if len(opponents) > 1:
        raise ValueError("iteration 001 has one opponent")

    by_total = sorted(entries, key=lambda e: -e.total)  # stable: keeps reported order
    order: list[InitiativeEntry] = []
    for _, tied in groupby(by_total, key=lambda e: e.total):
        group = list(tied)
        opponent = next((e for e in group if e.kind == "opponent"), None)
        if opponent is None:
            order.extend(group)
            continue
        characters = [e for e in group if e.kind == "character"]
        order.extend(c for c in characters if c.dexterity_modifier >= opponent.dexterity_modifier)
        order.append(opponent)
        order.extend(c for c in characters if c.dexterity_modifier < opponent.dexterity_modifier)
    return order
