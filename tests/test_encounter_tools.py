"""The encounter and opponent tools (#49), through the ToolBox, on fixed dice.

The opponent is built here rather than taken from the built-in fixture, so the
tests say every number they depend on.
"""

import json

import pytest
from fakes import FixedDice, ScriptedDungeonMaster

from dungeon_master.adventure.models import Monster, MonsterAttack, SavingThrows
from dungeon_master.adventure.repository import InMemoryAdventureRepository
from dungeon_master.events.contract import EncounterUpdated, PartyUpdated
from dungeon_master.orchestration.session import TableSession
from dungeon_master.session.party import Character
from dungeon_master.session.state import Encounter, SessionState
from dungeon_master.tools.toolbox import ToolBox

BRUTE = Monster(
    id="brute",
    name="Brute",
    armour_class=14,
    hit_points=30,
    dexterity_modifier=1,
    saving_throws=SavingThrows(
        strength=3, dexterity=1, constitution=2, intelligence=-1, wisdom=0, charisma=-1
    ),
    attacks=(
        MonsterAttack(
            name="Club",
            attack_bonus=5,
            damage_dice=1,
            damage_die=8,
            damage_modifier=3,
            damage_type="bludgeoning",
        ),
        MonsterAttack(
            name="Claws",
            attack_bonus=5,
            damage_dice=1,
            damage_die=6,
            damage_modifier=3,
            damage_type="slashing",
        ),
    ),
    attacks_per_turn=2,
    resistances=("fire",),
    vulnerabilities=("radiant",),
    immunities=("poison",),
)


def character(id: str, name: str, armour_class: int, hit_points: int) -> Character:
    return Character(
        id=id,
        name=name,
        character_class="Fighter",
        level=2,
        armour_class=armour_class,
        max_hit_points=hit_points,
        current_hit_points=hit_points,
    )


class Table:
    """A session's state and tool box, with the dice and the events in reach."""

    def __init__(self) -> None:
        self.state = SessionState(
            party=[character("brann", "Brann", 16, 28), character("mira", "Mira", 12, 9)]
        )
        self.dice = FixedDice()
        self.published: list = []
        self.tools = ToolBox(
            self.state,
            self.published.append,
            adventure=InMemoryAdventureRepository([BRUTE]),
            dice=self.dice,
        )

    def call(self, tool: str, **arguments):
        return self.tools.call(tool, arguments)

    def start(self, initiative_die: int = 10):
        self.dice.then(initiative_die)
        return self.call("start_encounter", opponent_id="brute")

    def fight(self, brann: int = 15, mira: int = 5, initiative_die: int = 10):
        """Start and fix the order. With the defaults: Brann (15), Brute (11), Mira (5)."""
        self.start(initiative_die)
        self.call("record_initiative", character_id="brann", total=brann, dexterity_modifier=2)
        return self.call("record_initiative", character_id="mira", total=mira, dexterity_modifier=0)

    def brutes_turn(self):
        self.fight()
        self.call("end_turn")

    @property
    def encounter(self) -> Encounter:
        assert self.state.encounter is not None
        return self.state.encounter

    def events(self, kind: type) -> list:
        return [e for e in self.published if isinstance(e, kind)]


@pytest.fixture
def table() -> Table:
    return Table()


# Starting the encounter.


def test_starting_holds_the_opponent_hidden_and_tells_the_table_its_name(table: Table) -> None:
    result = table.start(initiative_die=10)

    assert result.ok
    assert table.state.opponent.current_hit_points == 30
    assert table.state.opponent.initiative.total == 11
    assert table.published == [EncounterUpdated(encounter=Encounter(opponent_name="Brute"))]
    assert result.data["attacks"] == ["Club", "Claws"]
    assert result.data["rolls"][0]["purpose"] == "Brute: initiative"
    assert result.data["rolls"][0]["dice"] == (10,)


def test_starting_needs_a_party(table: Table) -> None:
    table.state.party = []

    result = table.start()

    assert not result.ok
    assert table.published == []


def test_an_unknown_opponent_is_refused_with_the_known_ones(table: Table) -> None:
    result = table.call("start_encounter", opponent_id="dragon")

    assert not result.ok
    assert "brute" in result.reason


def test_a_running_encounter_cannot_be_started_again(table: Table) -> None:
    table.start()

    result = table.call("start_encounter", opponent_id="brute")

    assert not result.ok
    assert "already running" in result.reason


def test_an_ended_encounter_can_be_followed_by_a_new_one(table: Table) -> None:
    table.fight()
    table.call("end_encounter", outcome="parley")

    result = table.start()

    assert result.ok
    assert table.encounter.outcome is None
    assert table.state.initiative == {}


# Initiative and the turn order.


def test_the_order_waits_for_every_character(table: Table) -> None:
    table.start()

    result = table.call("record_initiative", character_id="brann", total=15, dexterity_modifier=2)

    assert result.data["waiting_for"] == ["Mira"]
    assert table.encounter.round == 0


def test_once_everyone_has_initiative_round_one_begins_in_order(table: Table) -> None:
    result = table.fight()

    assert [c.name for c in table.encounter.turn_order] == ["Brann", "Brute", "Mira"]
    assert (table.encounter.round, table.encounter.current_turn) == (1, 0)
    assert result.data["acting"] == "Brann"
    assert table.encounter.turn_order[1].id == "opponent"


def test_a_tie_with_the_opponent_goes_by_dexterity(table: Table) -> None:
    # The Brute rolls 10 + 1 = 11. Mira ties it with a lower modifier, Brann with the same.
    table.start(initiative_die=10)
    table.call("record_initiative", character_id="brann", total=11, dexterity_modifier=1)
    table.call("record_initiative", character_id="mira", total=11, dexterity_modifier=0)

    assert [c.name for c in table.encounter.turn_order] == ["Brann", "Brute", "Mira"]


def test_initiative_can_be_corrected_until_the_order_is_fixed(table: Table) -> None:
    table.start()
    table.call("record_initiative", character_id="mira", total=5, dexterity_modifier=0)
    table.call("record_initiative", character_id="mira", total=19, dexterity_modifier=0)
    table.call("record_initiative", character_id="brann", total=15, dexterity_modifier=2)

    assert table.encounter.turn_order[0].name == "Mira"

    result = table.call("record_initiative", character_id="mira", total=1, dexterity_modifier=0)
    assert not result.ok


def test_initiative_needs_an_encounter(table: Table) -> None:
    result = table.call("record_initiative", character_id="brann", total=15, dexterity_modifier=2)

    assert result.reason == "No encounter has started."


def test_fight_tools_wait_for_the_turn_order(table: Table) -> None:
    table.start()

    result = table.call("resolve_player_attack", character_id="brann", total=20)

    assert not result.ok
    assert "Brann, Mira" in result.reason


# A player's attack, against the hidden armour class.


@pytest.mark.parametrize(
    ("total", "natural", "outcome"),
    [(14, None, "hit"), (13, None, "miss"), (25, 1, "miss"), (8, 20, "critical_hit")],
)
def test_a_player_attack_is_decided_against_the_hidden_armour_class(
    table: Table, total: int, natural: int | None, outcome: str
) -> None:
    table.fight()

    result = table.call(
        "resolve_player_attack", character_id="brann", total=total, natural_roll=natural
    )

    assert result.data["outcome"] == outcome
    assert "14" not in json.dumps(result.data)  # the armour class stays with the code


# The opponent's saving throw.


def test_the_opponent_saves_with_its_own_modifier(table: Table) -> None:
    table.fight()
    table.dice.then(12)

    result = table.call("opponent_saving_throw", ability="dexterity", dc=13)

    assert result.data["success"] is True  # 12 + 1
    assert result.data["rolls"][0]["modifier"] == 1


# The opponent's attack.


def test_a_hit_lands_on_the_character_and_the_table_hears_of_it(table: Table) -> None:
    table.brutes_turn()
    table.published.clear()
    table.dice.then(12, 5)  # 12 + 5 = 17 against AC 16; 1d8 = 5, + 3

    result = table.call("opponent_attack", attack="Club", target_id="brann")

    assert (result.data["outcome"], result.data["damage_taken"]) == ("hit", 8)
    assert table.state.party[0].current_hit_points == 20
    assert [e.party[0].current_hit_points for e in table.events(PartyUpdated)] == [20]
    assert [r["purpose"] for r in result.data["rolls"]] == ["Club: attack", "Club: damage"]


def test_a_miss_changes_nothing(table: Table) -> None:
    table.brutes_turn()
    table.published.clear()
    table.dice.then(10)  # 15 against AC 16

    result = table.call("opponent_attack", attack="Club", target_id="brann")

    assert result.data["outcome"] == "miss"
    assert table.published == []


def test_a_critical_hit_doubles_the_dice(table: Table) -> None:
    table.brutes_turn()
    table.dice.then(20, 4, 6)

    result = table.call("opponent_attack", attack="Club", target_id="brann")

    assert result.data["damage_taken"] == 4 + 6 + 3


def test_a_hit_that_drops_a_character_makes_it_unconscious(table: Table) -> None:
    table.brutes_turn()
    table.dice.then(15, 8)  # 11 damage against Mira's 9

    result = table.call("opponent_attack", attack="Club", target_id="mira")

    assert table.state.party[1].conditions == ["unconscious"]
    assert result.data["killed"] is False


def test_the_opponent_attacks_no_more_often_than_its_stat_block_allows(table: Table) -> None:
    table.brutes_turn()
    table.dice.then(1, 1)  # two misses

    first = table.call("opponent_attack", attack="Club", target_id="brann")
    second = table.call("opponent_attack", attack="claws", target_id="brann")
    third = table.call("opponent_attack", attack="Club", target_id="brann")

    assert first.ok and second.ok
    assert not third.ok
    assert "2" in third.reason


def test_the_opponent_attacks_only_on_its_turn(table: Table) -> None:
    table.fight()  # Brann's turn

    result = table.call("opponent_attack", attack="Club", target_id="mira")

    assert result.reason == "It is Brann's turn, not Brute's."


def test_an_unknown_attack_is_refused_with_the_ones_there_are(table: Table) -> None:
    table.brutes_turn()

    result = table.call("opponent_attack", attack="Bite", target_id="brann")

    assert "Club, Claws" in result.reason


def test_a_dead_character_cannot_be_attacked(table: Table) -> None:
    table.brutes_turn()
    table.state.party[1].current_hit_points = 0
    table.state.party[1].conditions = ["dead"]

    result = table.call("opponent_attack", attack="Club", target_id="mira")

    assert not result.ok
    assert table.dice.unused == []


# Damage and conditions on the opponent: hidden from the table.


@pytest.mark.parametrize(
    ("damage_type", "taken"), [("slashing", 10), ("fire", 5), ("radiant", 20), ("poison", 0)]
)
def test_damage_to_the_opponent_goes_through_its_defences(
    table: Table, damage_type: str, taken: int
) -> None:
    table.fight()
    table.published.clear()

    result = table.call("apply_damage", target="opponent", amount=10, damage_type=damage_type)

    assert result.data["damage_taken"] == taken
    assert table.state.opponent.current_hit_points == 30 - taken
    assert table.published == []


def test_the_opponent_at_zero_is_defeated(table: Table) -> None:
    table.fight()

    result = table.call("apply_damage", target="opponent", amount=40, damage_type="slashing")

    assert result.data["defeated"] is True
    assert table.state.opponent.current_hit_points == 0


def test_conditions_on_the_opponent_are_hidden(table: Table) -> None:
    table.fight()
    table.published.clear()

    table.call("add_condition", target="opponent", condition="prone")

    assert table.state.opponent.conditions == ["prone"]
    assert table.published == []

    table.call("remove_condition", target="opponent", condition="prone")
    assert table.state.opponent.conditions == []


# Turns, rounds, and the end.


def test_ending_turns_walks_the_order_and_starts_a_new_round(table: Table) -> None:
    table.fight()

    actors = [table.call("end_turn").data["acting"] for _ in range(3)]

    assert actors == ["Brute", "Mira", "Brann"]
    assert table.encounter.round == 2


def test_a_new_turn_gives_the_opponent_its_attacks_back(table: Table) -> None:
    table.brutes_turn()
    table.dice.then(1, 1)
    table.call("opponent_attack", attack="Club", target_id="brann")
    table.call("opponent_attack", attack="Club", target_id="brann")
    for _ in range(3):
        table.call("end_turn")
    table.dice.then(1)

    assert table.call("opponent_attack", attack="Club", target_id="brann").ok


def test_opponent_defeated_is_refused_while_it_stands(table: Table) -> None:
    table.fight()

    refused = table.call("end_encounter", outcome="opponent_defeated")
    table.call("apply_damage", target="opponent", amount=30, damage_type="slashing")
    accepted = table.call("end_encounter", outcome="opponent_defeated")

    assert not refused.ok and "30" in refused.reason
    assert accepted.ok
    assert table.encounter.outcome == "opponent_defeated"


def test_party_defeated_is_refused_while_anyone_is_conscious(table: Table) -> None:
    table.fight()
    for member in table.state.party:
        member.current_hit_points = 0
        member.conditions = ["unconscious"]
    table.state.party[0].conditions = []
    table.state.party[0].current_hit_points = 3

    refused = table.call("end_encounter", outcome="party_defeated")

    assert not refused.ok and "Brann" in refused.reason


def test_after_the_end_the_fight_tools_refuse(table: Table) -> None:
    table.fight()
    table.call("end_encounter", outcome="party_fled")

    result = table.call("end_turn")

    assert result.reason == "The encounter has ended."


# What the table's stream carries.


def test_a_whole_fight_never_puts_the_opponents_numbers_on_the_table(table: Table) -> None:
    table.brutes_turn()
    table.dice.then(15, 6, 12)
    table.call("opponent_attack", attack="Club", target_id="brann")
    table.call("opponent_saving_throw", ability="wisdom", dc=12)
    table.call("end_turn")
    table.call("apply_damage", target="opponent", amount=30, damage_type="slashing")
    table.call("add_condition", target="opponent", condition="prone")
    table.call("end_encounter", outcome="opponent_defeated")

    for event in table.published:
        wire = json.loads(event.model_dump_json())
        if wire["type"] == "encounter_updated":
            assert set(wire["encounter"]) == set(Encounter.model_fields)
            assert all(set(c) == {"kind", "id", "name"} for c in wire["encounter"]["turn_order"])
        else:
            assert wire["type"] == "party_updated"
            assert {c["id"] for c in wire["party"]} == {"brann", "mira"}
    assert table.encounter.outcome == "opponent_defeated"


# The session's dice.


def test_the_session_rolls_from_a_seed_it_keeps() -> None:
    first = TableSession(ScriptedDungeonMaster(), seed=1234)
    second = TableSession(ScriptedDungeonMaster(), seed=1234)
    rolls = []
    for session in (first, second):
        session.state.party.append(character("brann", "Brann", 16, 28))
        rolls.append(session.tools.call("start_encounter", {"opponent_id": "ogre"}).data["rolls"])

    assert first.seed == 1234
    assert rolls[0] == rolls[1]


def test_a_session_without_a_given_seed_draws_one() -> None:
    assert isinstance(TableSession(ScriptedDungeonMaster()).seed, int)
