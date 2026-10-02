// The table's event contract. The types are generated from the backend's
// Pydantic models: run `python -m dungeon_master.events.schema` in the
// repository root, then `npm run contract` here. See docs/event-contract.md.
import type { TableEvent } from './table-events.ts'

export type * from './table-events.ts'

// A record rather than a list, so the compiler fails when an event type is
// added to the contract and not listened for here — or listed here and not in
// the contract.
const LISTENED_FOR: Record<TableEvent['type'], true> = {
  turn_started: true,
  narration_delta: true,
  turn_finished: true,
  party_updated: true,
  encounter_updated: true,
  error: true,
}

export const TABLE_EVENT_TYPES = Object.keys(LISTENED_FOR) as TableEvent['type'][]
