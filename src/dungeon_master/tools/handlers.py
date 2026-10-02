"""What each tool does to the session state.

Only the conditions are real so far: they involve no arithmetic. Every tool
that computes refuses with the issue that will make it deterministic, so the
model learns that the code cannot do it yet rather than inventing a result.
"""

from ..session.party import Character
from ..session.state import SessionState
from . import schemas
from .result import ToolResult

COMBAT_ARRIVES = "Deterministic combat is not implemented yet (#29)."
OPPONENT_ARRIVES = "The opponent is not implemented yet (#31)."


def _not_yet(reason: str):
    def handler(state: SessionState, args: schemas.Arguments) -> ToolResult:
        return ToolResult.refused(reason)

    return handler


start_encounter = _not_yet(f"{OPPONENT_ARRIVES} {COMBAT_ARRIVES}")
record_initiative = _not_yet(COMBAT_ARRIVES)
resolve_player_attack = _not_yet(f"{OPPONENT_ARRIVES} {COMBAT_ARRIVES}")
opponent_saving_throw = _not_yet(f"{OPPONENT_ARRIVES} {COMBAT_ARRIVES}")
opponent_attack = _not_yet(f"{OPPONENT_ARRIVES} {COMBAT_ARRIVES}")
apply_damage = _not_yet(COMBAT_ARRIVES)
heal = _not_yet(COMBAT_ARRIVES)
set_temporary_hit_points = _not_yet(COMBAT_ARRIVES)
end_turn = _not_yet(COMBAT_ARRIVES)
end_encounter = _not_yet(COMBAT_ARRIVES)
update_plan = _not_yet("The plan is not implemented yet (#34).")


def _character_target(state: SessionState, target: str) -> Character | ToolResult:
    if target == schemas.OPPONENT:
        return ToolResult.refused(OPPONENT_ARRIVES)
    character = state.character(target)
    if character is None:
        known = ", ".join(c.id for c in state.party) or "none"
        return ToolResult.refused(f"No character {target!r}. Characters: {known}.")
    return character


def add_condition(state: SessionState, args: schemas.AddCondition) -> ToolResult:
    character = _character_target(state, args.target)
    if isinstance(character, ToolResult):
        return character
    if args.condition not in character.conditions:
        character.conditions = [*character.conditions, args.condition]
    return ToolResult.done(target=character.id, conditions=list(character.conditions))


def remove_condition(state: SessionState, args: schemas.RemoveCondition) -> ToolResult:
    character = _character_target(state, args.target)
    if isinstance(character, ToolResult):
        return character
    character.conditions = [c for c in character.conditions if c != args.condition]
    return ToolResult.done(target=character.id, conditions=list(character.conditions))
