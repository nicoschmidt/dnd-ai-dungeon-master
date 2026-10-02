"""The arguments of every tool the dungeon master may call in iteration 001.

Their meaning is docs/domain/combat.md's; the descriptions here are what the
model reads, so they say what to pass rather than how the code works.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from ..session.party import Condition
from ..session.state import Outcome

Mode = Literal["normal", "advantage", "disadvantage"]
Ability = Literal["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]
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

OPPONENT = "opponent"
TARGET_DESCRIPTION = f"A character's id, or {OPPONENT!r} for the opponent."


class Arguments(BaseModel):
    model_config = ConfigDict(extra="forbid")


class StartEncounter(Arguments):
    opponent_id: str = Field(description="The opponent's identity in the adventure.")


class RecordInitiative(Arguments):
    character_id: str
    total: int = Field(description="The initiative total the player reported.")


class ResolvePlayerAttack(Arguments):
    character_id: str = Field(description="The attacking character.")
    total: int = Field(description="The attack total the player reported.")
    natural_roll: int | None = Field(
        default=None,
        ge=1,
        le=20,
        description="The d20 as it fell, when the player reported a natural 1 or 20.",
    )


class OpponentSavingThrow(Arguments):
    ability: Ability
    dc: int = Field(ge=1, description="The spell save DC the player named.")
    mode: Mode = "normal"


class OpponentAttack(Arguments):
    attack: str = Field(description="The name of one of the opponent's declared attacks.")
    target_id: str = Field(description="The character the opponent attacks.")
    mode: Mode = "normal"


class ApplyDamage(Arguments):
    target: str = Field(description=TARGET_DESCRIPTION)
    amount: int = Field(ge=0, description="The damage total the player reported.")
    damage_type: DamageType
    halved_on_save: bool = Field(
        default=False,
        description="True when the target saved against an effect that deals half damage. "
        "Pass the full amount; the code halves it.",
    )
    critical: bool = Field(default=False, description="True when the damage came from a critical hit.")


class Heal(Arguments):
    character_id: str
    amount: int = Field(ge=0, description="The healing the player reported.")


class SetTemporaryHitPoints(Arguments):
    character_id: str
    amount: int = Field(ge=0)


class AddCondition(Arguments):
    target: str = Field(description=TARGET_DESCRIPTION)
    condition: Condition


class RemoveCondition(Arguments):
    target: str = Field(description=TARGET_DESCRIPTION)
    condition: Condition


class EndTurn(Arguments):
    pass


class EndEncounter(Arguments):
    outcome: Outcome


class UpdatePlan(Arguments):
    plan: str = Field(
        min_length=1,
        description="What you intend next, what you are holding back, and what you "
        "expect the party to do. Replaces the previous plan.",
    )
