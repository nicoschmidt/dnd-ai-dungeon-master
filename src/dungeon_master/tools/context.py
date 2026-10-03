"""What a tool handler works with."""

from dataclasses import dataclass

from ..adventure.repository import AdventureRepository
from ..rules.dice import RandomSource
from ..session.state import SessionState


@dataclass(frozen=True)
class ToolContext:
    """The session's state, the adventure it draws on, and the dice the code rolls.

    The dice are the session's seeded random source: the code rolls only for
    the opponent, and every roll goes back to the model in the tool's result.
    """

    state: SessionState
    adventure: AdventureRepository
    dice: RandomSource
