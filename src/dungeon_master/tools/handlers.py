"""What each tool does to the session state.

Handlers translate between the session's models and the rules core, and write
the rules' result back. They do no arithmetic of their own. Tools that need
the opponent refuse until it exists (#31) and is connected (#49), so the model
learns that the code cannot do it yet rather than inventing a result.
"""

from collections.abc import Set

from ..rules import damage, healing
from ..rules.results import Refused
from ..session.party import Character
from ..session.state import SessionState
from . import schemas
from .result import ToolResult

NOT_CONNECTED = "Encounters and the opponent are not connected yet (#31, #49)."


def _not_yet(reason: str):
    def handler(state: SessionState, args: schemas.Arguments) -> ToolResult:
        return ToolResult.refused(reason)

    return handler


start_encounter = _not_yet(NOT_CONNECTED)
record_initiative = _not_yet(NOT_CONNECTED)
resolve_player_attack = _not_yet(NOT_CONNECTED)
opponent_saving_throw = _not_yet(NOT_CONNECTED)
opponent_attack = _not_yet(NOT_CONNECTED)
end_turn = _not_yet(NOT_CONNECTED)
end_encounter = _not_yet(NOT_CONNECTED)
update_plan = _not_yet("The plan is not implemented yet (#34).")


def _character_target(state: SessionState, target: str) -> Character | ToolResult:
    if target == schemas.OPPONENT:
        return ToolResult.refused(NOT_CONNECTED)
    character = state.character(target)
    if character is None:
        known = ", ".join(c.id for c in state.party) or "none"
        return ToolResult.refused(f"No character {target!r}. Characters: {known}.")
    return character


def _hit_points(character: Character) -> damage.HitPoints:
    return damage.HitPoints(
        character.current_hit_points,
        character.max_hit_points,
        character.temporary_hit_points,
    )


def _write_back(
    character: Character, hit_points: damage.HitPoints, conditions: Set[str] | None = None
) -> None:
    character.temporary_hit_points = hit_points.temporary
    character.current_hit_points = hit_points.current
    if conditions is not None:
        # Existing conditions keep their order; new ones follow, sorted, so the
        # party snapshot does not depend on set iteration order.
        kept = [c for c in character.conditions if c in conditions]
        added = sorted(c for c in conditions if c not in character.conditions)
        character.conditions = kept + added


def _state_of(character: Character) -> dict:
    return {
        "target": character.id,
        "current_hit_points": character.current_hit_points,
        "max_hit_points": character.max_hit_points,
        "temporary_hit_points": character.temporary_hit_points,
        "conditions": list(character.conditions),
    }


def apply_damage(state: SessionState, args: schemas.ApplyDamage) -> ToolResult:
    character = _character_target(state, args.target)
    if isinstance(character, ToolResult):
        return character
    result = damage.apply_damage(
        _hit_points(character),
        set(character.conditions),
        args.amount,
        args.damage_type,
        kind="character",
        halved_on_save=args.halved_on_save,
        critical=args.critical,
    )
    if isinstance(result, Refused):
        return ToolResult.refused(result.reason)
    _write_back(character, result.hit_points, result.conditions)
    return ToolResult.done(
        damage_taken=result.taken,
        absorbed_by_temporary_hit_points=result.absorbed,
        death_save_failures=result.death_save_failures,
        killed=result.killed,
        **_state_of(character),
    )


def heal(state: SessionState, args: schemas.Heal) -> ToolResult:
    character = _character_target(state, args.character_id)
    if isinstance(character, ToolResult):
        return character
    result = healing.heal(_hit_points(character), set(character.conditions), args.amount)
    if isinstance(result, Refused):
        return ToolResult.refused(result.reason)
    _write_back(character, result.hit_points, result.conditions)
    return ToolResult.done(healed=result.healed, **_state_of(character))


def set_temporary_hit_points(
    state: SessionState, args: schemas.SetTemporaryHitPoints
) -> ToolResult:
    character = _character_target(state, args.character_id)
    if isinstance(character, ToolResult):
        return character
    result = healing.set_temporary_hit_points(_hit_points(character), args.amount)
    if isinstance(result, Refused):
        return ToolResult.refused(result.reason)
    _write_back(character, result)
    return ToolResult.done(**_state_of(character))


def add_condition(state: SessionState, args: schemas.AddCondition) -> ToolResult:
    character = _character_target(state, args.target)
    if isinstance(character, ToolResult):
        return character
    if args.condition not in character.conditions:
        character.conditions = [*character.conditions, args.condition]
    return ToolResult.done(**_state_of(character))


def remove_condition(state: SessionState, args: schemas.RemoveCondition) -> ToolResult:
    character = _character_target(state, args.target)
    if isinstance(character, ToolResult):
        return character
    character.conditions = [c for c in character.conditions if c != args.condition]
    return ToolResult.done(**_state_of(character))
