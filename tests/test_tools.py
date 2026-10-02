"""The tool surface: named, schema-checked, and heard by the table when it changes state."""

import pytest

from dungeon_master.events.contract import EncounterUpdated, PartyUpdated
from dungeon_master.session.party import Character
from dungeon_master.session.state import Encounter, SessionState
from dungeon_master.tools import schemas
from dungeon_master.tools.registry import TOOLS, ToolSpec
from dungeon_master.tools.result import ToolResult
from dungeon_master.tools.toolbox import ToolBox

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
    return ToolBox(state, published.append)


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


def test_a_tool_not_yet_deterministic_refuses_and_names_its_issue(
    toolbox: ToolBox, published: list
) -> None:
    result = toolbox.call(
        "apply_damage", {"target": "brann", "amount": 7, "damage_type": "slashing"}
    )

    assert not result.ok
    assert "#29" in result.reason
    assert published == []


def test_an_encounter_change_publishes_the_public_encounter(
    state: SessionState, published: list
) -> None:
    def start(state: SessionState, args: schemas.StartEncounter) -> ToolResult:
        state.encounter = Encounter(opponent_name="Ogre")
        return ToolResult.done()

    toolbox = ToolBox(
        state,
        published.append,
        [ToolSpec("start_encounter", "test", schemas.StartEncounter, start)],
    )

    toolbox.call("start_encounter", {"opponent_id": "ogre"})

    assert published == [EncounterUpdated(encounter=Encounter(opponent_name="Ogre"))]


def test_a_change_is_published_even_when_the_handler_then_refuses(
    state: SessionState, published: list
) -> None:
    def half_done(state: SessionState, args: schemas.Heal) -> ToolResult:
        state.party[0].current_hit_points = 20
        return ToolResult.refused("something else went wrong")

    toolbox = ToolBox(state, published.append, [ToolSpec("heal", "test", schemas.Heal, half_done)])

    toolbox.call("heal", {"character_id": "brann", "amount": 1})

    assert [event.party[0].current_hit_points for event in published] == [20]
