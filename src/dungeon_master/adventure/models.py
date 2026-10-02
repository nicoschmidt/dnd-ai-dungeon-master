"""What an adventure holds about an opponent, and the fight it frames.

Field names are snake_case with their unit in the name, so that the monster
entry of the v1 adventure schema (#4) can adopt them as they are. The values
of a stat block are the book's fixed ones: hit points are not rolled.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ..rules.attacks import AttackProfile
from ..rules.damage import DamageType, Defences

ID_PATTERN = r"^[a-z0-9][a-z0-9-]*$"


class _Content(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class MonsterAttack(_Content):
    name: str = Field(min_length=1)
    attack_bonus: int
    damage_dice: int = Field(ge=1, description="How many damage dice: the 2 in 2d8 + 4.")
    damage_die: Literal[4, 6, 8, 10, 12, 20] = Field(description="Their sides: the 8 in 2d8 + 4.")
    damage_modifier: int = Field(description="The 4 in 2d8 + 4.")
    damage_type: DamageType


class SavingThrows(_Content):
    """Saving throw modifiers, all six, as a stat block lists them."""

    strength: int
    dexterity: int
    constitution: int
    intelligence: int
    wisdom: int
    charisma: int


class Monster(_Content):
    """An opponent's stat block: what docs/domain/combat.md needs of it, and no more."""

    id: str = Field(pattern=ID_PATTERN)
    name: str = Field(min_length=1)
    armour_class: int = Field(ge=0)
    hit_points: int = Field(ge=1, description="The stat block's fixed value, not rolled.")
    dexterity_modifier: int = Field(description="For initiative, and a tie in it.")
    saving_throws: SavingThrows
    attacks: tuple[MonsterAttack, ...] = Field(min_length=1)
    attacks_per_turn: int = Field(ge=1)
    resistances: tuple[DamageType, ...] = ()
    vulnerabilities: tuple[DamageType, ...] = ()
    immunities: tuple[DamageType, ...] = ()

    def attack(self, name: str) -> AttackProfile:
        """One of the declared attacks, for the rules core. Fails naming the ones there are."""
        for attack in self.attacks:
            if attack.name.casefold() == name.casefold():
                return AttackProfile(
                    name=attack.name,
                    bonus=attack.attack_bonus,
                    damage_dice=attack.damage_dice,
                    damage_sides=attack.damage_die,
                    damage_modifier=attack.damage_modifier,
                    damage_type=attack.damage_type,
                )
        known = ", ".join(a.name for a in self.attacks)
        raise KeyError(f"{self.name} has no attack {name!r}. Attacks: {known}.")

    @property
    def defences(self) -> Defences:
        return Defences(
            resistances=frozenset(self.resistances),
            vulnerabilities=frozenset(self.vulnerabilities),
            immunities=frozenset(self.immunities),
        )


class EncounterSetup(_Content):
    """The fight before it starts: who the opponent is, and where and why it happens."""

    id: str = Field(pattern=ID_PATTERN)
    opponent_id: str = Field(pattern=ID_PATTERN)
    premise: str = Field(
        min_length=1,
        description="Two or three sentences the dungeon master narrates from. Never read aloud verbatim.",
    )
