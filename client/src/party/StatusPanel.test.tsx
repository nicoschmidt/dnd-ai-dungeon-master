import { render, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { Character, TableEvent } from '../contract/index.ts'
import { applyEvent, initialTableState, type TableState } from '../stream/tableState.ts'
import { StatusPanel } from './StatusPanel.tsx'

const brann: Character = {
  id: 'brann',
  name: 'Brann',
  character_class: 'Fighter',
  level: 3,
  armour_class: 16,
  max_hit_points: 28,
  current_hit_points: 17,
  temporary_hit_points: 5,
  conditions: ['prone', 'poisoned'],
}

const mira: Character = {
  ...brann,
  id: 'mira',
  name: 'Mira',
  character_class: 'Wizard',
  current_hit_points: 9,
  max_hit_points: 9,
  temporary_hit_points: 0,
  conditions: [],
}

function stateFrom(...events: TableEvent[]): TableState {
  return events.reduce(applyEvent, initialTableState)
}

function renderPanel(state: TableState) {
  return render(<StatusPanel party={state.party} encounter={state.encounter} />)
}

describe('StatusPanel', () => {
  it('shows the party exactly as party_updated carries it', () => {
    renderPanel(stateFrom({ type: 'party_updated', party: [brann, mira] }))

    const first = screen.getAllByRole('listitem')[0]
    expect(within(first).getByText('17 / 28 HP')).toBeTruthy()
    expect(within(first).getByText(/\+5 temporary/)).toBeTruthy()
    expect(within(first).getByText(/prone, poisoned/)).toBeTruthy()
    const second = screen.getAllByRole('listitem')[1]
    expect(within(second).getByText('9 / 9 HP')).toBeTruthy()
    expect(within(second).queryByText(/temporary/)).toBeNull()
  })

  it('shows the latest party_updated, not a merge of earlier ones', () => {
    renderPanel(
      stateFrom(
        { type: 'party_updated', party: [brann, mira] },
        { type: 'party_updated', party: [{ ...brann, current_hit_points: 4, conditions: [] }] },
      ),
    )

    expect(screen.getAllByRole('listitem')).toHaveLength(1)
    expect(screen.getByText('4 / 28 HP')).toBeTruthy()
    expect(screen.queryByText(/prone/)).toBeNull()
  })

  it('shows the round and whose turn it is from encounter_updated', () => {
    renderPanel(
      stateFrom(
        { type: 'party_updated', party: [brann, mira] },
        {
          type: 'encounter_updated',
          encounter: {
            opponent_name: 'Ogre',
            round: 2,
            turn_order: [
              { kind: 'character', id: 'brann', name: 'Brann' },
              { kind: 'opponent', id: 'ogre', name: 'Ogre' },
              { kind: 'character', id: 'mira', name: 'Mira' },
            ],
            current_turn: 2,
            outcome: null,
          },
        },
      ),
    )

    expect(screen.getByText("Round 2 — Mira's turn")).toBeTruthy()
    const acting = screen.getAllByRole('listitem').find((item) => item.getAttribute('aria-current'))
    expect(acting?.textContent).toContain('Mira')
  })

  it('says so when there is nobody yet', () => {
    renderPanel(initialTableState)

    expect(screen.getByText('No characters yet.')).toBeTruthy()
  })
})
