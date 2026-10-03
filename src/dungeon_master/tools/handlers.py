"""What each tool does to the session state.

Handlers translate between the session's state and the rules core, and write
the rules' result back. They do no arithmetic of their own. Every roll the
code makes goes back to the model in the result, under `rolls`, so the journal
(#33) can record it.

The opponent's state is hidden: handlers change it, but the `ToolBox` never
publishes it, and results that only concern the opponent change nothing the
table sees.
"""

from collections.abc import Set
from dataclasses import asdict

from ..adventure.repository import UnknownContent
from ..rules import attacks, damage, healing, saving_throws
from ..rules.dice import RollRecord, roll_d20
from ..rules.encounter import CharacterStatus, check_attack_allowed, check_outcome, next_turn
from ..rules.initiative import InitiativeEntry, turn_order
from ..rules.results import Refused
from ..session.party import Character
from ..session.state import Combatant, Encounter, OpponentState, SessionState
from . import schemas
from .context import ToolContext
from .result import ToolResult

OPPONENT_COMBATANT_ID = schemas.OPPONENT


def update_plan(context: ToolContext, args: schemas.UpdatePlan) -> ToolResult:
    return ToolResult.refused("The plan is not implemented yet (#34).")


# Looking things up, with the reason a lookup fails.


def _rolls(*records: RollRecord | None) -> list[dict]:
    return [asdict(r) for r in records if r is not None]


def _character(state: SessionState, character_id: str) -> Character | ToolResult:
    character = state.character(character_id)
    if character is None:
        known = ", ".join(c.id for c in state.party) or "none"
        return ToolResult.refused(f"No character {character_id!r}. Characters: {known}.")
    return character


def _opponent(state: SessionState) -> OpponentState | ToolResult:
    """The opponent of an encounter that has started and not ended."""
    if state.encounter is None or state.opponent is None:
        return ToolResult.refused("No encounter has started.")
    if state.encounter.outcome is not None:
        return ToolResult.refused("The encounter has ended.")
    return state.opponent


def _fight(state: SessionState) -> tuple[Encounter, OpponentState] | ToolResult:
    """An encounter whose turn order is fixed: the fight itself."""
    opponent = _opponent(state)
    if isinstance(opponent, ToolResult):
        return opponent
    assert state.encounter is not None
    if state.encounter.round == 0:
        missing = ", ".join(c.name for c in state.party if c.id not in state.initiative)
        return ToolResult.refused(
            f"The turn order is not fixed yet. Initiative still missing for: {missing}."
        )
    return state.encounter, opponent


def _acting(encounter: Encounter) -> Combatant:
    assert encounter.current_turn is not None
    return encounter.turn_order[encounter.current_turn]


# Characters: hit points and conditions.


def _hit_points(character: Character) -> damage.HitPoints:
    return damage.HitPoints(
        character.current_hit_points,
        character.max_hit_points,
        character.temporary_hit_points,
    )


def _ordered(current: list, after: Set[str]) -> list:
    # Existing conditions keep their order; new ones follow, sorted, so the
    # party snapshot does not depend on set iteration order.
    return [c for c in current if c in after] + sorted(c for c in after if c not in current)


def _write_back(
    character: Character, hit_points: damage.HitPoints, conditions: Set[str] | None = None
) -> None:
    character.temporary_hit_points = hit_points.temporary
    character.current_hit_points = hit_points.current
    if conditions is not None:
        character.conditions = _ordered(character.conditions, conditions)


def _state_of(character: Character) -> dict:
    return {
        "target": character.id,
        "current_hit_points": character.current_hit_points,
        "max_hit_points": character.max_hit_points,
        "temporary_hit_points": character.temporary_hit_points,
        "conditions": list(character.conditions),
    }


def _state_of_opponent(opponent: OpponentState) -> dict:
    return {
        "target": OPPONENT_COMBATANT_ID,
        "current_hit_points": opponent.current_hit_points,
        "max_hit_points": opponent.monster.hit_points,
        "conditions": list(opponent.conditions),
        "defeated": opponent.current_hit_points == 0,
    }


def _damage_character(
    character: Character, amount: int, damage_type: damage.DamageType, **flags: bool
) -> damage.DamageResult | Refused:
    result = damage.apply_damage(
        _hit_points(character),
        set(character.conditions),
        amount,
        damage_type,
        kind="character",
        **flags,
    )
    if not isinstance(result, Refused):
        _write_back(character, result.hit_points, result.conditions)
    return result


def _damage_report(result: damage.DamageResult) -> dict:
    return {
        "damage_taken": result.taken,
        "absorbed_by_temporary_hit_points": result.absorbed,
        "death_save_failures": result.death_save_failures,
        "killed": result.killed,
    }


# The encounter.


def start_encounter(context: ToolContext, args: schemas.StartEncounter) -> ToolResult:
    state = context.state
    if not state.party:
        return ToolResult.refused("The party has not been entered yet: there is nobody to fight.")
    if state.encounter is not None and state.encounter.outcome is None:
        return ToolResult.refused(
            f"An encounter against {state.encounter.opponent_name} is already running."
        )
    try:
        monster = context.adventure.monster(args.opponent_id)
    except UnknownContent as error:
        return ToolResult.refused(str(error))

    initiative = roll_d20(context.dice, f"{monster.name}: initiative", monster.dexterity_modifier)
    state.opponent = OpponentState(monster, monster.hit_points, initiative)
    state.initiative = {}
    state.encounter = Encounter(opponent_name=monster.name)
    return ToolResult.done(
        opponent=monster.name,
        attacks=[a.name for a in monster.attacks],
        attacks_per_turn=monster.attacks_per_turn,
        waiting_for_initiative=[c.name for c in state.party],
        rolls=_rolls(initiative),
    )


def record_initiative(context: ToolContext, args: schemas.RecordInitiative) -> ToolResult:
    state = context.state
    opponent = _opponent(state)
    if isinstance(opponent, ToolResult):
        return opponent
    encounter = state.encounter
    assert encounter is not None
    if encounter.round > 0:
        return ToolResult.refused("The turn order is already fixed for this encounter.")
    character = _character(state, args.character_id)
    if isinstance(character, ToolResult):
        return character

    state.initiative[character.id] = InitiativeEntry(
        character.id, "character", args.total, args.dexterity_modifier
    )
    missing = [c.name for c in state.party if c.id not in state.initiative]
    if missing:
        return ToolResult.done(recorded=character.name, waiting_for=missing)

    names = {c.id: c.name for c in state.party} | {OPPONENT_COMBATANT_ID: opponent.monster.name}
    order = turn_order(
        [
            *(state.initiative[c.id] for c in state.party if c.id in state.initiative),
            InitiativeEntry(
                OPPONENT_COMBATANT_ID,
                "opponent",
                opponent.initiative.total,
                opponent.monster.dexterity_modifier,
            ),
        ]
    )
    current, round = next_turn(len(order), None, 0)
    encounter.turn_order = [Combatant(kind=e.kind, id=e.id, name=names[e.id]) for e in order]
    encounter.current_turn = current
    encounter.round = round
    opponent.attacks_this_turn = 0
    return ToolResult.done(
        recorded=character.name,
        turn_order=[c.name for c in encounter.turn_order],
        round=round,
        acting=_acting(encounter).name,
    )


def end_turn(context: ToolContext, args: schemas.EndTurn) -> ToolResult:
    fight = _fight(context.state)
    if isinstance(fight, ToolResult):
        return fight
    encounter, opponent = fight
    current, round = next_turn(len(encounter.turn_order), encounter.current_turn, encounter.round)
    encounter.current_turn = current
    encounter.round = round
    opponent.attacks_this_turn = 0
    return ToolResult.done(round=round, acting=_acting(encounter).name)


def end_encounter(context: ToolContext, args: schemas.EndEncounter) -> ToolResult:
    state = context.state
    opponent = _opponent(state)
    if isinstance(opponent, ToolResult):
        return opponent
    refused = check_outcome(
        args.outcome,
        opponent.current_hit_points,
        [CharacterStatus(c.name, c.current_hit_points, set(c.conditions)) for c in state.party],
    )
    if refused:
        return ToolResult.refused(refused.reason)
    assert state.encounter is not None
    state.encounter.outcome = args.outcome
    return ToolResult.done(outcome=args.outcome)


# Attacks and saving throws.


def resolve_player_attack(context: ToolContext, args: schemas.ResolvePlayerAttack) -> ToolResult:
    fight = _fight(context.state)
    if isinstance(fight, ToolResult):
        return fight
    _, opponent = fight
    character = _character(context.state, args.character_id)
    if isinstance(character, ToolResult):
        return character
    outcome = attacks.resolve_player_attack(
        args.total, args.natural_roll, opponent.monster.armour_class
    )
    return ToolResult.done(attacker=character.name, outcome=outcome)


def opponent_saving_throw(context: ToolContext, args: schemas.OpponentSavingThrow) -> ToolResult:
    fight = _fight(context.state)
    if isinstance(fight, ToolResult):
        return fight
    _, opponent = fight
    result = saving_throws.opponent_saving_throw(
        context.dice,
        args.ability,
        getattr(opponent.monster.saving_throws, args.ability),
        args.dc,
        args.mode,
    )
    return ToolResult.done(success=result.success, rolls=_rolls(result.roll))


def opponent_attack(context: ToolContext, args: schemas.OpponentAttack) -> ToolResult:
    fight = _fight(context.state)
    if isinstance(fight, ToolResult):
        return fight
    encounter, opponent = fight
    monster = opponent.monster
    acting = _acting(encounter)
    if acting.kind != "opponent":
        return ToolResult.refused(f"It is {acting.name}'s turn, not {monster.name}'s.")
    try:
        profile = monster.attack(args.attack)
    except KeyError as error:
        return ToolResult.refused(error.args[0])
    refused = check_attack_allowed(opponent.attacks_this_turn, monster.attacks_per_turn)
    if refused:
        return ToolResult.refused(refused.reason)
    target = _character(context.state, args.target_id)
    if isinstance(target, ToolResult):
        return target
    if "dead" in target.conditions:
        return ToolResult.refused(f"{target.name} is dead.")

    result = attacks.opponent_attack(context.dice, profile, target.armour_class, args.mode)
    opponent.attacks_this_turn += 1
    report: dict = {"attack": profile.name, "outcome": result.outcome, "damage_rolled": result.damage}
    if result.damage_roll is not None:
        damaged = _damage_character(
            target,
            result.damage,
            profile.damage_type,
            critical=result.outcome == "critical_hit",
        )
        assert not isinstance(damaged, Refused)  # the target is alive and the damage not negative
        report |= _damage_report(damaged)
    return ToolResult.done(**report, **_state_of(target), rolls=_rolls(*result.rolls))


# Damage, healing and conditions.


def apply_damage(context: ToolContext, args: schemas.ApplyDamage) -> ToolResult:
    state = context.state
    if args.target == schemas.OPPONENT:
        opponent = _opponent(state)
        if isinstance(opponent, ToolResult):
            return opponent
        result = damage.apply_damage(
            damage.HitPoints(opponent.current_hit_points, opponent.monster.hit_points),
            set(opponent.conditions),
            args.amount,
            args.damage_type,
            kind="opponent",
            defences=opponent.monster.defences,
            halved_on_save=args.halved_on_save,
            critical=args.critical,
        )
        if isinstance(result, Refused):
            return ToolResult.refused(result.reason)
        opponent.current_hit_points = result.hit_points.current
        return ToolResult.done(damage_taken=result.taken, **_state_of_opponent(opponent))

    character = _character(state, args.target)
    if isinstance(character, ToolResult):
        return character
    result = _damage_character(
        character,
        args.amount,
        args.damage_type,
        halved_on_save=args.halved_on_save,
        critical=args.critical,
    )
    if isinstance(result, Refused):
        return ToolResult.refused(result.reason)
    return ToolResult.done(**_damage_report(result), **_state_of(character))


def heal(context: ToolContext, args: schemas.Heal) -> ToolResult:
    character = _character(context.state, args.character_id)
    if isinstance(character, ToolResult):
        return character
    result = healing.heal(_hit_points(character), set(character.conditions), args.amount)
    if isinstance(result, Refused):
        return ToolResult.refused(result.reason)
    _write_back(character, result.hit_points, result.conditions)
    return ToolResult.done(healed=result.healed, **_state_of(character))


def set_temporary_hit_points(
    context: ToolContext, args: schemas.SetTemporaryHitPoints
) -> ToolResult:
    character = _character(context.state, args.character_id)
    if isinstance(character, ToolResult):
        return character
    result = healing.set_temporary_hit_points(_hit_points(character), args.amount)
    if isinstance(result, Refused):
        return ToolResult.refused(result.reason)
    _write_back(character, result)
    return ToolResult.done(**_state_of(character))


def _change_conditions(context: ToolContext, target: str, change) -> ToolResult:
    if target == schemas.OPPONENT:
        opponent = _opponent(context.state)
        if isinstance(opponent, ToolResult):
            return opponent
        opponent.conditions = change(opponent.conditions)
        return ToolResult.done(**_state_of_opponent(opponent))
    character = _character(context.state, target)
    if isinstance(character, ToolResult):
        return character
    character.conditions = change(character.conditions)
    return ToolResult.done(**_state_of(character))


def add_condition(context: ToolContext, args: schemas.AddCondition) -> ToolResult:
    return _change_conditions(
        context,
        args.target,
        lambda current: current if args.condition in current else [*current, args.condition],
    )


def remove_condition(context: ToolContext, args: schemas.RemoveCondition) -> ToolResult:
    return _change_conditions(
        context, args.target, lambda current: [c for c in current if c != args.condition]
    )
