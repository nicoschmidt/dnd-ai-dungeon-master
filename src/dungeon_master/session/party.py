"""The party: what the system holds of each character, and how it is entered.

Exactly the fields ADR-0004 assigns to the system. Everything else about a
character stays on the player's paper sheet.
"""

import re
import unicodedata
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


class CharacterEntry(BaseModel):
    """One character as the group types it in before the encounter."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        json_schema_serialization_defaults_required=True,
    )

    name: str = Field(min_length=1)
    character_class: str = Field(min_length=1)
    level: int = Field(ge=1, le=20)
    armour_class: int = Field(ge=0)
    max_hit_points: int = Field(ge=1)
    current_hit_points: int | None = Field(
        default=None, ge=0, description="Leave empty for the maximum."
    )
    temporary_hit_points: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def _current_within_maximum(self) -> "CharacterEntry":
        if self.current_hit_points is not None and self.current_hit_points > self.max_hit_points:
            raise ValueError("current_hit_points cannot exceed max_hit_points")
        return self


class PartyEntry(BaseModel):
    """The whole party as the group types it in. Replaces the party held so far."""

    model_config = ConfigDict(extra="forbid", json_schema_serialization_defaults_required=True)

    characters: list[CharacterEntry]

    @model_validator(mode="after")
    def _names_are_unique(self) -> "PartyEntry":
        seen: set[str] = set()
        for character in self.characters:
            key = character.name.casefold()
            if key in seen:
                raise ValueError(f"two characters are called {character.name!r}")
            seen.add(key)
        return self


def character_id(name: str, taken: set[str], position: int) -> str:
    """A stable id from the name: `Jörg Weiß` becomes `jorg-weiss`."""
    folded = unicodedata.normalize("NFKD", name.replace("ß", "ss"))
    slug = re.sub(r"[^a-z0-9]+", "-", folded.encode("ascii", "ignore").decode().lower()).strip("-")
    base = slug or f"character-{position}"
    candidate, n = base, 1
    while candidate in taken:
        n += 1
        candidate = f"{base}-{n}"
    return candidate


def build_party(entry: PartyEntry, existing: list[Character]) -> list[Character]:
    """The party the entry describes. A character entered again keeps its conditions."""
    conditions = {c.id: list(c.conditions) for c in existing}
    party: list[Character] = []
    taken: set[str] = set()
    for position, character in enumerate(entry.characters, start=1):
        id = character_id(character.name, taken, position)
        taken.add(id)
        fields = character.model_dump()
        if fields["current_hit_points"] is None:
            fields["current_hit_points"] = fields["max_hit_points"]
        party.append(Character(id=id, conditions=conditions.get(id, []), **fields))
    return party
