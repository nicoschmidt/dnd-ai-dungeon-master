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
deliberately, like the adventure schema.

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
dice they rolled in their own words, and `character_id`, the acting character
when the client knows it (from #30 on), else `null`.
