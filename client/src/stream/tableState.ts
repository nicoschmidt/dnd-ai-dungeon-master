import type {
  Character,
  DeclaredAction,
  Encounter,
  TableError,
  TableEvent,
} from '../contract/index.ts'

export interface Turn {
  id: string
  action: DeclaredAction
  narration: string
  finished: boolean
}

// What the table shows, built from the stream's events and from nothing else.
export interface TableState {
  turns: Turn[]
  party: Character[]
  encounter: Encounter | null
  error: TableError | null
  busy: boolean
}

export const initialTableState: TableState = {
  turns: [],
  party: [],
  encounter: null,
  error: null,
  busy: false,
}

export function applyEvent(state: TableState, event: TableEvent): TableState {
  switch (event.type) {
    case 'turn_started':
      return {
        ...state,
        busy: true,
        error: null,
        turns: [
          ...state.turns,
          { id: event.turn_id, action: event.action, narration: '', finished: false },
        ],
      }
    case 'narration_delta':
      return {
        ...state,
        turns: state.turns.map((turn) =>
          turn.id === event.turn_id ? { ...turn, narration: turn.narration + event.text } : turn,
        ),
      }
    case 'turn_finished':
      return {
        ...state,
        busy: false,
        turns: state.turns.map((turn) =>
          turn.id === event.turn_id ? { ...turn, finished: true } : turn,
        ),
      }
    case 'party_updated':
      return { ...state, party: event.party }
    case 'encounter_updated':
      return { ...state, encounter: event.encounter }
    case 'error':
      return { ...state, error: event }
  }
}
