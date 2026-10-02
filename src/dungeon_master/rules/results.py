"""What a rule gives back when it will not do what was asked."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Refused:
    """A refusal is a value, not an exception, so the model can be told why."""

    reason: str
