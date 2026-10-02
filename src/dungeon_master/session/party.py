"""The party: what the system holds of each character.

Exactly the fields ADR-0004 assigns to the system. Everything else about a
character stays on the player's paper sheet.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

# The SRD conditions, plus the two states docs/domain/combat.md adds for a
# character at 0 hit points.
Condition = Literal[
    "blinded",
    "charmed",
    "deafened",
    "exhaustion",
    "frightened",
    "grappled",
    "incapacitated",
    "invisible",
    "paralyzed",
    "petrified",
    "poisoned",
    "prone",
    "restrained",
    "stunned",
    "unconscious",
    "stable",
    "dead",
]


class Character(BaseModel):
    """One player character, as the system holds it (ADR-0004)."""

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        json_schema_serialization_defaults_required=True,
    )

    id: str = Field(
        pattern=r"^[a-z0-9][a-z0-9-]*$",
        description="Stable identity within the session; tools address the character by it.",
    )
    name: str = Field(min_length=1)
    character_class: str = Field(min_length=1, description="For narration only.")
    level: int = Field(ge=1, le=20, description="For narration only.")
    armour_class: int = Field(ge=0)
    max_hit_points: int = Field(ge=1)
    current_hit_points: int = Field(ge=0)
    temporary_hit_points: int = Field(default=0, ge=0)
    conditions: list[Condition] = Field(default_factory=list)

    @model_validator(mode="after")
    def _current_within_maximum(self) -> "Character":
        if self.current_hit_points > self.max_hit_points:
            raise ValueError("current_hit_points cannot exceed max_hit_points")
        return self
