"""The dungeon master's tool surface: every tool, its arguments and its handler.

The names and meanings are docs/domain/combat.md's. Which tools change state
is not declared here: the `ToolBox` compares the state before and after every
call, so a handler cannot change the party without the table hearing of it.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from . import handlers, schemas
from .context import ToolContext
from .result import ToolResult


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    arguments: type[schemas.Arguments]
    handler: Callable[[ToolContext, Any], ToolResult]


TOOLS: tuple[ToolSpec, ...] = (
    ToolSpec(
        "start_encounter",
        "Start the encounter against the named opponent. The code rolls the opponent's initiative.",
        schemas.StartEncounter,
        handlers.start_encounter,
    ),
    ToolSpec(
        "record_initiative",
        "Record a character's initiative total and Dexterity modifier, as the player reported them. "
        "One call per character.",
        schemas.RecordInitiative,
        handlers.record_initiative,
    ),
    ToolSpec(
        "resolve_player_attack",
        "Resolve a character's attack against the opponent from the reported total. "
        "Returns hit, miss or critical hit. Ask for damage only on a hit.",
        schemas.ResolvePlayerAttack,
        handlers.resolve_player_attack,
    ),
    ToolSpec(
        "opponent_saving_throw",
        "Roll the opponent's saving throw against the DC a player named. Returns success or failure.",
        schemas.OpponentSavingThrow,
        handlers.opponent_saving_throw,
    ),
    ToolSpec(
        "opponent_attack",
        "Make one of the opponent's attacks against a character. The code rolls, compares "
        "with the character's armour class and applies the damage. One call per attack.",
        schemas.OpponentAttack,
        handlers.opponent_attack,
    ),
    ToolSpec(
        "apply_damage",
        "Apply damage a player reported to the opponent or a character.",
        schemas.ApplyDamage,
        handlers.apply_damage,
    ),
    ToolSpec(
        "heal",
        "Heal a character by the amount the player reported. Never above the maximum.",
        schemas.Heal,
        handlers.heal,
    ),
    ToolSpec(
        "set_temporary_hit_points",
        "Give a character temporary hit points. The higher of old and new is kept.",
        schemas.SetTemporaryHitPoints,
        handlers.set_temporary_hit_points,
    ),
    ToolSpec(
        "add_condition",
        "Give the opponent or a character a condition.",
        schemas.AddCondition,
        handlers.add_condition,
    ),
    ToolSpec(
        "remove_condition",
        "Remove a condition from the opponent or a character.",
        schemas.RemoveCondition,
        handlers.remove_condition,
    ),
    ToolSpec(
        "end_turn",
        "End the current combatant's turn. The next one in the order acts.",
        schemas.EndTurn,
        handlers.end_turn,
    ),
    ToolSpec(
        "end_encounter",
        "End the encounter with an outcome. Refused when the outcome contradicts the state.",
        schemas.EndEncounter,
        handlers.end_encounter,
    ),
    ToolSpec(
        "update_plan",
        "Write down your current plan. It is shown only in the game master view, never to the table.",
        schemas.UpdatePlan,
        handlers.update_plan,
    ),
)
