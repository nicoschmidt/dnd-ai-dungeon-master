"""The tool surface: named, schema-checked, and heard by the table when it changes state."""

import pytest
from fakes import FixedDice

from dungeon_master.adventure.repository import InMemoryAdventureRepository
from dungeon_master.events.contract import EncounterUpdated, PartyUpdated
from dungeon_master.session.party import Character
from dungeon_master.session.state import Encounter, SessionState
from dungeon_master.tools import schemas
from dungeon_master.tools.context import ToolContext
from dungeon_master.tools.registry import TOOLS, ToolSpec
from dungeon_master.tools.result import ToolResult
from dungeon_master.tools.toolbox import ToolBox

NO_ADVENTURE = InMemoryAdventureRepository([])

# docs/domain/combat.md, "The tools this implies", plus the plan of ADR-0006.
NAMED_IN_THE_SPECIFICATION = {
    "start_encounter",
    "record_initiative",
    "resolve_player_attack",
    "opponent_saving_throw",
    "opponent_attack",
    "apply_damage",
    "heal",
    "set_temporary_hit_points",
    "add_condition",
    "remove_condition",
    "end_turn",
    "end_encounter",
    "update_plan",
}


def _brann() -> Character:
    return Character(
        id="brann",
        name="Brann",
        character_class="Fighter",
        level=3,
        armour_class=16,
        max_hit_points=28,
        current_hit_points=28,
    )


@pytest.fixture
def state() -> SessionState:
    return SessionState(party=[_brann()])


@pytest.fixture
def published() -> list:
    return []


@pytest.fixture
def toolbox(state: SessionState, published: list) -> ToolBox:
    return ToolBox(state, published.append, adventure=NO_ADVENTURE, dice=FixedDice())


def test_the_surface_is_the_one_the_specification_names() -> None:
    assert {tool.name for tool in TOOLS} == NAMED_IN_THE_SPECIFICATION


@pytest.mark.parametrize("tool", TOOLS, ids=lambda t: t.name)
def test_every_tool_has_a_description_and_an_argument_schema(tool: ToolSpec) -> None:
    schema = tool.arguments.model_json_schema()

    assert tool.description
    assert schema["type"] == "object"
    assert schema.get("additionalProperties") is False


def test_a_state_change_publishes_the_whole_party_once(
    toolbox: ToolBox, state: SessionState, published: list
) -> None:
    result = toolbox.call("add_condition", {"target": "brann", "condition": "prone"})

    assert result.ok
    assert published == [PartyUpdated(party=[_brann().model_copy(update={"conditions": ["prone"]})])]


def test_a_published_party_does_not_change_with_later_state(
    toolbox: ToolBox, state: SessionState, published: list
) -> None:
    toolbox.call("add_condition", {"target": "brann", "condition": "prone"})
    toolbox.call("remove_condition", {"target": "brann", "condition": "prone"})

    assert [event.party[0].conditions for event in published] == [["prone"], []]


def test_a_call_that_changes_nothing_publishes_nothing(
    toolbox: ToolBox, published: list
) -> None:
    result = toolbox.call("remove_condition", {"target": "brann", "condition": "prone"})

    assert result.ok
    assert published == []


def test_an_unknown_tool_is_refused_with_the_list_of_tools(toolbox: ToolBox) -> None:
    result = toolbox.call("roll_for_the_player", {})

    assert not result.ok
    assert "add_condition" in result.reason


@pytest.mark.parametrize(
    "arguments",
    [
        {"target": "brann"},
        {"target": "brann", "condition": "on fire"},
        {"target": "brann", "condition": "prone", "hit_points": 3},
    ],
)
def test_arguments_that_do_not_fit_the_schema_are_refused(
    toolbox: ToolBox, published: list, arguments: dict
) -> None:
    result = toolbox.call("add_condition", arguments)

    assert not result.ok
    assert result.reason.startswith("Invalid arguments for add_condition")
    assert published == []


def test_an_unknown_character_is_refused_with_the_known_ones(toolbox: ToolBox) -> None:
    result = toolbox.call("add_condition", {"target": "mira", "condition": "prone"})

    assert not result.ok
    assert "brann" in result.reason


def test_a_tool_not_yet_implemented_refuses_and_names_its_issue(
    toolbox: ToolBox, published: list
) -> None:
    result = toolbox.call("update_plan", {"plan": "Let the ogre bargain first."})

    assert not result.ok
    assert "#34" in result.reason
    assert published == []


def test_damage_to_the_opponent_needs_an_encounter(toolbox: ToolBox, published: list) -> None:
    result = toolbox.call(
        "apply_damage", {"target": "opponent", "amount": 7, "damage_type": "slashing"}
    )

    assert not result.ok
    assert result.reason == "No encounter has started."
    assert published == []


def test_damage_lands_on_the_character_and_the_table_hears_of_it(
    toolbox: ToolBox, state: SessionState, published: list
) -> None:
    state.party[0].temporary_hit_points = 5

    result = toolbox.call(
        "apply_damage", {"target": "brann", "amount": 12, "damage_type": "bludgeoning"}
    )

    assert result.ok
    assert result.data["absorbed_by_temporary_hit_points"] == 5
    assert (state.party[0].current_hit_points, state.party[0].temporary_hit_points) == (21, 0)
    assert [(e.party[0].current_hit_points, e.party[0].temporary_hit_points) for e in published] == [
        (21, 0)
    ]


def test_damage_to_zero_makes_the_character_unconscious(
    toolbox: ToolBox, state: SessionState
) -> None:
    state.party[0].conditions = ["prone"]

    result = toolbox.call(
        "apply_damage", {"target": "brann", "amount": 30, "damage_type": "slashing"}
    )

    assert result.ok
    assert state.party[0].current_hit_points == 0
    assert state.party[0].conditions == ["prone", "unconscious"]


def test_a_critical_hit_at_zero_reports_two_failed_death_saves(
    toolbox: ToolBox, state: SessionState
) -> None:
    state.party[0].current_hit_points = 0
    state.party[0].conditions = ["unconscious", "stable"]

    result = toolbox.call(
        "apply_damage",
        {"target": "brann", "amount": 4, "damage_type": "piercing", "critical": True},
    )

    assert result.data["death_save_failures"] == 2
    assert state.party[0].conditions == ["unconscious"]


def test_halving_on_a_save_is_the_codes_arithmetic(
    toolbox: ToolBox, state: SessionState
) -> None:
    result = toolbox.call(
        "apply_damage",
        {"target": "brann", "amount": 9, "damage_type": "fire", "halved_on_save": True},
    )

    assert result.data["damage_taken"] == 4
    assert state.party[0].current_hit_points == 24


def test_healing_from_zero_wakes_the_character_and_stops_at_the_maximum(
    toolbox: ToolBox, state: SessionState, published: list
) -> None:
    state.party[0].current_hit_points = 0
    state.party[0].conditions = ["unconscious", "stable"]

    result = toolbox.call("heal", {"character_id": "brann", "amount": 40})

    assert result.data["healed"] == 28
    assert (state.party[0].current_hit_points, state.party[0].conditions) == (28, [])
    assert len(published) == 1


def test_a_dead_character_cannot_be_healed(
    toolbox: ToolBox, state: SessionState, published: list
) -> None:
    state.party[0].current_hit_points = 0
    state.party[0].conditions = ["dead"]

    result = toolbox.call("heal", {"character_id": "brann", "amount": 5})

    assert not result.ok
    assert published == []


def test_temporary_hit_points_keep_the_higher_value(
    toolbox: ToolBox, state: SessionState, published: list
) -> None:
    toolbox.call("set_temporary_hit_points", {"character_id": "brann", "amount": 8})
    toolbox.call("set_temporary_hit_points", {"character_id": "brann", "amount": 5})

    assert state.party[0].temporary_hit_points == 8
    assert [e.party[0].temporary_hit_points for e in published] == [8]


def test_an_encounter_change_publishes_the_public_encounter(
    state: SessionState, published: list
) -> None:
    def start(context: ToolContext, args: schemas.StartEncounter) -> ToolResult:
        context.state.encounter = Encounter(opponent_name="Ogre")
        return ToolResult.done()

    toolbox = ToolBox(
        state,
        published.append,
        adventure=NO_ADVENTURE,
        dice=FixedDice(),
        tools=[ToolSpec("start_encounter", "test", schemas.StartEncounter, start)],
    )

    toolbox.call("start_encounter", {"opponent_id": "ogre"})

    assert published == [EncounterUpdated(encounter=Encounter(opponent_name="Ogre"))]


def test_a_change_is_published_even_when_the_handler_then_refuses(
    state: SessionState, published: list
) -> None:
    def half_done(context: ToolContext, args: schemas.Heal) -> ToolResult:
        context.state.party[0].current_hit_points = 20
        return ToolResult.refused("something else went wrong")

    toolbox = ToolBox(
        state,
        published.append,
        adventure=NO_ADVENTURE,
        dice=FixedDice(),
        tools=[ToolSpec("heal", "test", schemas.Heal, half_done)],
    )

    toolbox.call("heal", {"character_id": "brann", "amount": 1})

    assert [event.party[0].current_hit_points for event in published] == [20]
