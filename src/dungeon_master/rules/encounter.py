"""The encounter's bookkeeping: attacks per turn, the next turn, and the outcome."""

from collections.abc import Sequence, Set
from dataclasses import dataclass
from typing import Literal

from .results import Refused

Outcome = Literal[
    "opponent_defeated",
    "opponent_fled",
    "party_fled",
    "party_defeated",
    "parley",
]


def check_attack_allowed(attacks_made: int, attacks_per_turn: int) -> Refused | None:
    """A multiattack is one call per attack, and no more than the stat block declares."""
    if attacks_made >= attacks_per_turn:
        return Refused(
            f"The opponent has made all {attacks_per_turn} of its attacks this turn."
        )
    return None


def next_turn(order_length: int, current: int | None, round: int) -> tuple[int, int]:
    """(next combatant's index, round). After the last combatant a new round begins."""
    if current is None:
        return 0, max(round, 1)
    if current + 1 >= order_length:
        return 0, round + 1
    return current + 1, round


@dataclass(frozen=True)
class CharacterStatus:
    name: str
    current_hit_points: int
    conditions: Set[str]

    @property
    def conscious(self) -> bool:
        return self.current_hit_points > 0 and not {"unconscious", "dead"} & set(self.conditions)


def check_outcome(
    outcome: Outcome, opponent_hit_points: int, party: Sequence[CharacterStatus]
) -> Refused | None:
    """Refuse an outcome the state contradicts, so the two cannot disagree."""
    if outcome == "opponent_defeated" and opponent_hit_points > 0:
        return Refused(f"The opponent still has {opponent_hit_points} hit points.")
    if outcome == "party_defeated":
        conscious = [c.name for c in party if c.conscious]
        if conscious:
            return Refused(f"Still conscious: {', '.join(conscious)}.")
    return None
