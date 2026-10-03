# The table's event contract

What the shared screen receives from the backend, and what it sends back.
[ADR-0005](adr/0005-concrete-web-stack.md) decided the shape — Server-Sent
Events for narration and state, an ordinary `POST` for the declared action, a
contract typed at both ends. This document says what each part means.

The authoritative declaration is the code: the Pydantic models in
`src/dungeon_master/events/contract.py`. From them,
`python -m dungeon_master.events.schema` writes
`client/src/contract/table-events.schema.json`, and `npm run contract` in
`client/` turns that into `client/src/contract/table-events.ts`. All three are
committed. A test fails when the schema is stale, and CI fails when the
TypeScript is.

The contract is versioned (`CONTRACT_VERSION`, currently 1) and changed
deliberately, like the adventure schema. The version goes up when an existing
shape changes — a field renamed, removed or given a new meaning. An addition
that every existing reader can ignore does not change it.

## Endpoints

| Route | Does |
| --- | --- |
| `GET /api/session/stream` | The table's event stream, `text/event-stream`. Opened once by the page and kept open. |
| `POST /api/session/actions` | Declare an action. Body: a `DeclaredAction`. Answers `202` with the `turn_id`; everything the turn produces arrives on the stream. `409` while a turn is still running — interrupting the dungeon master is deliberately not possible (ADR-0005). `422` for a body that does not fit, or a `character_id` that is not in the party. |
| `PUT /api/session/party` | Enter the party. Body: a `PartyEntry`. Replaces the whole party, answers `200` with it, and publishes `party_updated`. `409` once the encounter has started: from then on only the dungeon master's tools change the party. `422` for a party that does not fit. |

One table, one session, in one process. The session lives as long as the
backend does.

### Event ids and reconnecting

Every event has an id of the form `<session id>:<sequence number>`, starting at
1. The browser's `EventSource` remembers the last id it received, reconnects on
its own after a dropped connection, and sends that id as `Last-Event-ID`. The
stream then begins with the first event after it, so nothing is missed and
nothing arrives twice.

Without `Last-Event-ID` — a fresh page, a reload, `curl -N` — the stream begins
with the first event of the session, so a reloaded page rebuilds its narration
log and party state. An id from another session means the backend has restarted
since; that client is also sent the whole of the new session.

The whole session is held in memory. For one evening that is small; bounding it
is a refinement for when it is not. While no event is due, the stream sends an
SSE comment line every 15 seconds to keep the connection alive.

The client keeps its state in `client/src/stream/`: a reducer that builds the
table's state from events alone, and a hook that listens for every event type
by name. It notices a backend restart by the changed session id in the event
ids, and rebuilds its state instead of appending to it.

The status panel (`client/src/party/StatusPanel.tsx`) renders the party and
the encounter from that state, which is to say from `party_updated` and
`encounter_updated` and nothing else. The input preselects the character whose
turn `encounter_updated` says it is.

## Events

Every event names its type twice: as the SSE `event:` field, so the client
listens for it by name, and as `type` inside the JSON payload, so a payload is
self-describing on its own. Every field is always present; a field without a
value is `null`.

The list is closed. `TableEvent` is a discriminated union, and an event that is
not on it cannot be built, let alone sent. Hidden information — the opponent's
numbers, roll records, tool calls, the plan — has no event type here at all; it
belongs to the game master's stream
([ADR-0006](adr/0006-game-master-view-and-session-journal.md)).

| Event | Carries | Meaning |
| --- | --- | --- |
| `turn_started` | `turn_id`, `action` | A declared action was accepted. `action` is the `DeclaredAction` exactly as the player sent it. |
| `narration_delta` | `turn_id`, `text` | The next piece of narration, in the order the model wrote it. Concatenating the deltas of a turn gives its narration. |
| `turn_finished` | `turn_id` | The dungeon master is done with this turn. The next action may be declared. Sent after every `turn_started`, also when the turn failed. |
| `party_updated` | `party` | The whole party, after a tool changed it. Never a difference: the latest event is the truth. |
| `encounter_updated` | `encounter` | The public state of the encounter after a tool changed it, or `null` when there is none. |
| `error` | `code`, `message`, `turn_id` | Something the table should know went wrong. `message` is written for the table and never carries an exception's text. |

**Party state** is exactly what
[ADR-0004](adr/0004-character-state-ownership.md) assigns to the system: `id`,
`name`, `character_class` and `level` for narration, `armour_class`,
`max_hit_points`, `current_hit_points`, `temporary_hit_points` and
`conditions`. The status panel renders from `party_updated` and from nothing
else (ADR-0005, commitment 2).

**The encounter** carries what [docs/domain/combat.md](domain/combat.md)
makes public: the opponent's name, the round (0 until the turn order is fixed),
the turn order as a list of combatants, the index of whoever acts now, and the
outcome once it has ended. The opponent's armour class and hit points are not
in it.

**Error codes** so far: `agent_failed` — the dungeon master could not finish
the turn; the action can be declared again. #32 adds the credential errors.

## The declared action

`DeclaredAction` is what a player sends: `text`, the declared action with the
dice they rolled in their own words, and `character_id`, the acting character,
or `null` when the action is the table's rather than one character's. The
client preselects whoever's turn it is.

## Entering the party

`PartyEntry` is the party as the group types it in before the fight
([ADR-0004](adr/0004-character-state-ownership.md): once per campaign; without
persistence, once per session). Each `CharacterEntry` has the fields the system
owns except `id` and `conditions`. `current_hit_points` may be `null`, meaning
the maximum. Names must be unique, ignoring case.

The backend derives each `id` from the name — lower case, accents folded to
ASCII, `ß` to `ss`, everything else to `-` (`Jörg Weiß` becomes
`jorg-weiss`); a collision gets `-2`. A character entered again under the
same name keeps its id and its conditions.

The same constraints are checked in the client before sending
(`client/src/party/validateParty.ts`) and by Pydantic on arrival. The
backend's answer is the one that counts; the client shows its messages too.

## The dungeon master's tools

The tools the agent may call in iteration 001. Their meaning is
[docs/domain/combat.md](domain/combat.md)'s; their argument schemas are the
Pydantic models in `src/dungeon_master/tools/schemas.py`, and the list itself
is `src/dungeon_master/tools/registry.py`. Every schema forbids arguments it
does not name.

| Tool | Arguments |
| --- | --- |
| `start_encounter` | `opponent_id` |
| `record_initiative` | `character_id`, `total`, `dexterity_modifier` |
| `resolve_player_attack` | `character_id`, `total`, `natural_roll` (1 or 20, optional) |
| `opponent_saving_throw` | `ability`, `dc`, `mode` |
| `opponent_attack` | `attack`, `target_id`, `mode` |
| `apply_damage` | `target`, `amount`, `damage_type`, `halved_on_save`, `critical` |
| `heal` | `character_id`, `amount` |
| `set_temporary_hit_points` | `character_id`, `amount` |
| `add_condition`, `remove_condition` | `target`, `condition` |
| `end_turn` | — |
| `end_encounter` | `outcome` |
| `update_plan` | `plan` — refuses until #34 |

`target` is a character's id or `opponent`. `mode` is `normal`, `advantage` or
`disadvantage`. `damage_type`, `ability`, `condition` and `outcome` take the
SRD's names, in lower case.

**Every call goes through the `ToolBox`.** It refuses an unknown tool or
arguments that do not fit the schema before any handler runs, and it compares
the party and the encounter before and after the handler. When either differs,
it publishes `party_updated` or `encounter_updated` with the new state. No
tool declares what it changes, so none can forget to say so.

**The opponent's state is hidden.** Its hit points, conditions, initiative and
the attacks it has made this turn are session state the `ToolBox` does not
compare, so no change to them produces an event on the table's stream. The
table learns of the opponent from `encounter_updated` — its name and its place
in the turn order — and from the narration. Results go to the model, which is
the dungeon master and may know everything.

**Every roll the code makes is in the result**, under `rolls`: purpose,
expression, every die, the kept die, modifier, mode and total. The dice are
the session's, seeded when it starts (`TableSession.seed`), so a session's
opponent rolls can be reproduced. The journal (#33) records them; the table
never sees them.

**Handlers do no arithmetic.** They translate between the session's models and
the rules core in `src/dungeon_master/rules/`, which decides everything
[docs/domain/combat.md](domain/combat.md) gives to the code, and write the
result back. The result the model reads says what happened: damage taken, how
much the temporary hit points absorbed, failed death saves to mark, the new
hit points and conditions.

**A refusal is a result, not an error.** It carries a reason the model reads,
so the dungeon master can correct itself rather than narrate something the
state does not support.
