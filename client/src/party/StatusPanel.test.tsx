import { render, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { Character, Encounter, TableEvent } from '../contract/index.ts'
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

const ogre: Encounter = {
  opponent_name: 'Ogre',
  round: 2,
  turn_order: [
    { kind: 'character', id: 'brann', name: 'Brann' },
    { kind: 'opponent', id: 'ogre', name: 'Ogre' },
    { kind: 'character', id: 'mira', name: 'Mira' },
  ],
  current_turn: 2,
  outcome: null,
}

function renderPanel(state: TableState) {
  return render(<StatusPanel party={state.party} encounter={state.encounter} />)
}

function cards(): HTMLElement[] {
  return within(screen.getByRole('list', { name: 'Characters' })).getAllByRole('listitem')
}

function turnOrder(): HTMLElement[] {
  return within(screen.getByRole('list', { name: 'Turn order' })).getAllByRole('listitem')
}

function nameOf(item: HTMLElement): string {
  return item.querySelector('.name')?.textContent ?? ''
}

function marked(items: HTMLElement[]): string[] {
  return items.filter((item) => item.hasAttribute('aria-current')).map(nameOf)
}

function segment(card: HTMLElement, name: string): string {
  return (card.querySelector(`.bar > .${name}`) as HTMLElement).style.width
}

describe('StatusPanel', () => {
  it('shows each character exactly as party_updated carries it', () => {
    renderPanel(stateFrom({ type: 'party_updated', party: [brann, mira] }))

    const [first, second] = cards()
    expect(nameOf(first)).toBe('Brann')
    expect(within(first).getByText('Fighter · level 3')).toBeTruthy()
    expect(within(first).getByTitle('Armour class').textContent).toBe('AC16')
    expect(within(first).getByText('17').tagName).toBe('STRONG')
    expect(within(first).getByText('/ 28')).toBeTruthy()
    expect(within(first).getByText('+5 temp.')).toBeTruthy()
    const conditions = within(first).getByLabelText('Conditions').children
    expect([...conditions].map((c) => c.textContent)).toEqual(['prone', 'poisoned'])
    expect(within(second).getByText('/ 9')).toBeTruthy()
    expect(within(second).queryByText(/temp\./)).toBeNull()
    expect(within(second).queryByLabelText('Conditions')).toBeNull()
  })

  it('draws the hit point bar with a segment for temporary hit points', () => {
    renderPanel(stateFrom({ type: 'party_updated', party: [brann, mira] }))

    const [first, second] = cards()
    expect(segment(first, 'current')).toBe(`${(17 / 33) * 100}%`)
    expect(segment(first, 'temporary-segment')).toBe(`${(5 / 33) * 100}%`)
    expect(segment(second, 'current')).toBe('100%')
    expect(within(first).getByRole('img').getAttribute('aria-label')).toBe(
      '17 of 28 hit points, 5 temporary',
    )
  })

  it('sets a character at 0 hit points apart, with their condition in view', () => {
    renderPanel(
      stateFrom({
        type: 'party_updated',
        party: [{ ...brann, current_hit_points: 0, conditions: ['unconscious'] }, mira],
      }),
    )

    const [first, second] = cards()
    expect(first.classList).toContain('down')
    expect(within(first).getByText('unconscious')).toBeTruthy()
    expect(second.classList).not.toContain('down')
  })

  it('shows the latest party_updated, not a merge of earlier ones', () => {
    renderPanel(
      stateFrom(
        { type: 'party_updated', party: [brann, mira] },
        { type: 'party_updated', party: [{ ...brann, current_hit_points: 4, conditions: [] }] },
      ),
    )

    expect(cards()).toHaveLength(1)
    expect(screen.getByText('4')).toBeTruthy()
    expect(screen.queryByText('prone')).toBeNull()
  })

  it('shows the round and the turn order from encounter_updated', () => {
    renderPanel(
      stateFrom(
        { type: 'party_updated', party: [brann, mira] },
        { type: 'encounter_updated', encounter: ogre },
      ),
    )

    const fight = within(screen.getByRole('region', { name: 'Fight' }))
    expect(fight.getByText('Round 2')).toBeTruthy()
    expect(turnOrder().map(nameOf)).toEqual(['Brann', 'Ogre', 'Mira'])
  })

  it('shows the opponent by name only, marked as the opponent', () => {
    renderPanel(stateFrom({ type: 'encounter_updated', encounter: ogre }))

    expect(turnOrder()[1].textContent).toBe('2Ogreopponent')
  })

  it('marks the current combatant in the turn order, and their card', () => {
    renderPanel(
      stateFrom(
        { type: 'party_updated', party: [brann, mira] },
        { type: 'encounter_updated', encounter: ogre },
      ),
    )

    expect(marked(turnOrder())).toEqual(['Mira'])
    expect(within(turnOrder()[2]).getByText('on turn')).toBeTruthy()
    expect(marked(cards())).toEqual(['Mira'])
    expect(within(cards()[1]).getByText('on turn')).toBeTruthy()
    expect(within(cards()[0]).queryByText('on turn')).toBeNull()
  })

  it('marks the opponent in the turn order on its turn, and no card', () => {
    renderPanel(
      stateFrom(
        { type: 'party_updated', party: [brann, mira] },
        { type: 'encounter_updated', encounter: { ...ogre, current_turn: 1 } },
      ),
    )

    expect(marked(turnOrder())).toEqual(['Ogre'])
    expect(marked(cards())).toEqual([])
  })

  it('marks nobody once the encounter has ended', () => {
    renderPanel(
      stateFrom(
        { type: 'party_updated', party: [brann, mira] },
        { type: 'encounter_updated', encounter: { ...ogre, outcome: 'opponent_defeated' } },
      ),
    )

    expect(screen.getByText('Ended')).toBeTruthy()
    expect(marked(turnOrder())).toEqual([])
    expect(marked(cards())).toEqual([])
  })

  it('says so when there is nobody yet', () => {
    renderPanel(initialTableState)

    expect(screen.getByText('No characters yet.')).toBeTruthy()
  })
})
