# The combat encounter

What iteration 001 has to adjudicate, and who adjudicates each part of it: the
code, the model, or the players with their paper sheets. This is a domain
document. The event payloads and tool argument schemas are defined in the event
contract (#23); this file defines what they mean.

It describes 5e mechanics in this project's own words. Rules material comes from
the System Reference Document under CC-BY-4.0, never from a book. See
`CLAUDE.md`.

## The situation

One party of player characters against **one opponent**. There is no map and
no distance: whether someone can reach someone else is a question of the
fiction, which the model answers. There is no adventure either — the encounter
is framed by a short, original premise that comes with the opponent (see
[The opponent](#the-opponent)).

The encounter ends when the opponent is defeated, the party is defeated, one
side flees, or the fight is talked out of.

## Who decides what

The line follows [ADR-0002](../adr/0002-application-form-factor.md): the model
narrates, decides and asks; code does the arithmetic and owns durable state;
[ADR-0004](../adr/0004-character-state-ownership.md) decides which numbers the
system holds at all.

| Question | Decided by |
| --- | --- |
| Does the player's attack hit the opponent? | **Code**, against the opponent's hidden armour class |
| Does the opponent's attack hit a character? | **Code**, which rolls for the opponent |
| How much damage, after resistances, temporary hit points and the 0 HP rule? | **Code** |
| Does the opponent succeed on a saving throw? | **Code**, which rolls for the opponent |
| Turn order | **Code**, from the reported and rolled initiative |
| The player's own modifiers, attack bonus, damage dice, spell save DC | **Player**, from the paper sheet |
| Death saving throws and their tally | **Player**, on the paper sheet's boxes |
| What the opponent does, whom it targets, when it flees | **Model** |
| Whether advantage or disadvantage applies | **Model**, from the fiction; code applies it |
| Whether an action needs a roll at all, and what a narrative action achieves | **Model** |
| How a declared action maps to the tools | **Model** |

Everything in the code column changes state only through a tool
([ADR-0002](../adr/0002-application-form-factor.md), commitment 3). Everything
in the model column is narration or a tool argument, never a state change on
its own.

## Dice

- The players roll their own dice and report **totals**, with the natural d20
  result when it is a 1 or a 20.
- The code rolls for the opponent. It never rolls for a player character.
- Every roll the code makes is a record: purpose, dice expression, the
  individual dice, the modifier, the total, and the mode (normal, advantage,
  disadvantage). It goes to the session journal and the game master view
  ([ADR-0006](../adr/0006-game-master-view-and-session-journal.md)), never to
  the table's stream.
- The random source is injected and seeded per session, and the seed is
  journaled. A session's opponent rolls are reproducible, and the rules core is
  tested with fixed sequences rather than with luck.

## The flow of an encounter

### 1. Start

The encounter is started with the opponent's identity. The model narrates the
premise and asks every player for **initiative**: a d20 plus their Dexterity
modifier, rolled and added at the table.

### 2. Initiative

Each reported total is recorded. The code rolls the opponent's initiative when
the encounter starts. Once every character has a value, the turn order is
fixed for the encounter:

- highest first
- a tie between a character and the opponent goes to the higher Dexterity
  modifier; if that ties too, the character goes first
- ties between characters are resolved in the order the players reported them;
  the table can reorder them before the first turn

The order and the current round are public. The opponent's initiative total is
not.

### 3. A character's turn

The acting character is preselected in the client, so the model knows who is
speaking. The player declares an action in free text. The model maps it to one
of the cases below, or handles it narratively.

**Attack roll.** The player reports the attack total, and the natural roll if
it was a 1 or a 20. The code compares with the opponent's armour class:

- natural 1: a miss, whatever the total
- natural 20: a hit and a **critical hit**, whatever the total
- otherwise: a hit when the total is at least the armour class

Only on a hit does the model ask for damage. On a critical hit it reminds the
player to roll the damage dice twice; doubling is the player's arithmetic,
because the damage dice live on the sheet. The player reports the damage total
and its type.

If a player reports attack and damage together, the damage is used only if the
attack hits.

**Spell or effect with a saving throw.** The player names the ability and their
spell save DC. The code rolls the opponent's saving throw with its modifier and
reports success or failure. On a failure the player reports the damage. On a
success, an effect that deals half damage is applied **halved, rounded down, by
the code**; the model says so in the tool call rather than halving in its head.

**Healing and temporary hit points** on a character: the player reports the
amount. Healing never raises current hit points above the maximum. Temporary
hit points do not stack: the higher value is kept.

**Anything else** — dashing, hiding, helping, dodging, talking, a skill check —
is adjudicated narratively by the model in iteration 001. It may set a
condition through a tool; it may not change a number by describing it.

The turn ends when the model ends it through a tool. The next combatant in the
order acts; after the last one, a new round starts.

### 4. The opponent's turn

The model decides what the opponent does and whom it targets — including
whether it attacks at all. For an attack it names one of the opponent's
declared attacks, the target character and the mode (normal, advantage,
disadvantage). The code then:

1. rolls the d20 in that mode and adds the attack's bonus
2. natural 1 misses, natural 20 is a critical hit, otherwise compare with the
   target's armour class, which the system holds
   ([ADR-0004](../adr/0004-character-state-ownership.md))
3. on a hit rolls the damage — the damage dice twice on a critical hit, the
   modifier once
4. applies it to the character as described under [Damage](#damage)

The result goes back to the model, which narrates it. The table learns the
outcome from the narration and from the status panel, not from a dice record.

A multiattack is the model calling the attack tool once per attack. The
opponent's stat block declares how many attacks it has; the code refuses more
than that in one turn.

### 5. End

The model ends the encounter with an outcome: `opponent_defeated`,
`opponent_fled`, `party_fled`, `party_defeated`, `parley`. The code refuses
`opponent_defeated` while the opponent has hit points left and
`party_defeated` while any character is conscious, so the outcome and the state
cannot disagree.

## Damage

Applied by the code, in this order, whoever the target is:

1. **Resistance or vulnerability** from the target's stat block: halved rounded
   down, or doubled. Immunity reduces the damage to 0. Characters declare none
   in iteration 001 — a player whose character resists a type says so, and the
   model reports the reduced amount.
2. **Temporary hit points** absorb damage first.
3. **Current hit points** take the rest, never below 0.

At 0 hit points:

- **The opponent** is defeated. Whether it dies, collapses or surrenders is
  narration.
- **A character** falls unconscious: the code sets the `unconscious` condition.
  If the damage left over after reaching 0 is at least the character's maximum
  hit points, the character dies outright, and the code sets `dead` instead.
- **Damage to a character already at 0** is a failed death saving throw — two
  on a critical hit. The model tells the player to mark it on the sheet.

Death saving throws stay on paper. The sheet has the boxes, the player rolls
and tallies, and nothing about them is arithmetic the system needs to
adjudicate anything else — by the rule in
[ADR-0004](../adr/0004-character-state-ownership.md), paper keeps them. The
player reports the outcome: stable (the model sets `stable`), dead (`dead`), or
a natural 20, which is healing of 1 hit point. Any healing on a character at 0
removes `unconscious` and `stable`.

## Conditions

The system holds active conditions for characters
([ADR-0004](../adr/0004-character-state-ownership.md)) and for the opponent.
Any condition name from the SRD can be set and removed through a tool, plus
`stable` and `dead`.

In iteration 001 the code **enforces** only what the damage rules above need:
`unconscious` at 0 hit points, `dead`, `stable`, and their removal by healing.
The mechanical effects of every other condition — advantage against a prone
target, disadvantage for a poisoned attacker — are the model's judgement,
passed as the mode of the roll. Moving an effect into code later changes no
tool contract, which is the point of designing the contracts from the domain.

## The opponent

One stat block, from **SRD 5.2** under CC-BY-4.0 with the attribution the
licence requires. The system holds, for the opponent:

- name, armour class, hit points (the stat block's fixed value, not rolled)
- Dexterity modifier for initiative, and saving throw modifiers
- attacks: name, attack bonus, damage dice, damage modifier, damage type
- number of attacks per turn
- resistances, vulnerabilities, immunities
- active conditions

It is loaded through the `AdventureRepository` port
([ADR-0003](../adr/0003-adventure-content-separation.md)), from an in-memory
implementation in iteration 001. From iteration 002 an opponent comes out of an
adventure package instead, and nothing above the port changes.

The premise that frames the fight — two or three sentences, where and why — is
original text written for this project and stored with the opponent's fixture.

Everything about the opponent except its name and what the narration reveals is
hidden from the table. The game master view shows all of it.

## What the table sees

| On the table's stream | Only on the game master's stream |
| --- | --- |
| Narration | The opponent's armour class, hit points, conditions |
| Party state: every field ADR-0004 assigns to the system | Every roll record |
| Whose turn it is, and the round | Every tool call, its arguments and its result |
| That an encounter started and ended, the opponent's name, the outcome | The model's plan |

## The tools this implies

Named here for their meaning; the schemas are the event contract's (#23).
Every tool that changes state produces an event; which stream carries it
follows the table above.

| Tool | Changes | Notes |
| --- | --- | --- |
| `start_encounter` | encounter, opponent | rolls the opponent's initiative |
| `record_initiative` | turn order | one call per character |
| `resolve_player_attack` | nothing | returns hit, miss or critical hit |
| `opponent_saving_throw` | nothing | returns success or failure |
| `opponent_attack` | the target character | rolls, compares, applies damage |
| `apply_damage` | the target | player-reported damage; halving on a save is a flag |
| `heal` | a character | capped at the maximum; clears `unconscious`, `stable` |
| `set_temporary_hit_points` | a character | keeps the higher value |
| `add_condition`, `remove_condition` | the target | |
| `end_turn` | turn order | advances to the next combatant, and the round |
| `end_encounter` | encounter | refused when the outcome contradicts the state |

A tool that refuses returns the reason to the model, so the model can correct
itself instead of narrating something the state does not support.

## Narration language

The table plays in German by default; the narration language is a configuration
value. Prompts, tool names, the journal and everything in this repository are
English.

## Deliberately not in iteration 001

- More than one opponent, and allies or summoned creatures
- Positions, distance, movement, reach, opportunity attacks — there is no map
- Reactions, legendary actions, lair actions, recharge abilities
- Spellcasting by the opponent
- Opponent hit points rolled from hit dice
- Mechanical effects of conditions beyond those listed under
  [Conditions](#conditions)
- Concentration
- Character resistances, and anything else a character computes from the sheet
- Surviving a restart in the middle of a fight
