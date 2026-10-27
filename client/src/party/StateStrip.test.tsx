import { render, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { Character, Encounter } from '../contract/index.ts'
import { StateStrip } from './StateStrip.tsx'

const party: Character[] = [
  ['brann', 'Brann', 17, 28, 5],
  ['mira', 'Mira', 0, 9, 0],
].map(([id, name, current, max, temporary]) => ({
  id: id as string,
  name: name as string,
  character_class: 'Fighter',
  level: 3,
  armour_class: 16,
  max_hit_points: max as number,
  current_hit_points: current as number,
  temporary_hit_points: temporary as number,
  conditions: [],
}))

const ogre: Encounter = {
  opponent_name: 'Ogre',
  round: 3,
  turn_order: [
    { kind: 'character', id: 'brann', name: 'Brann' },
    { kind: 'opponent', id: 'ogre', name: 'Ogre' },
    { kind: 'character', id: 'mira', name: 'Mira' },
  ],
  current_turn: 0,
  outcome: null,
}

function chips(): HTMLElement[] {
  return within(screen.getByRole('list', { name: 'Characters' })).getAllByRole('listitem')
}

describe('StateStrip', () => {
  it('says whose turn it is and the round on one line', () => {
    render(<StateStrip party={party} encounter={ogre} />)

    expect(screen.getByText(/Round 3/).textContent).toBe('Brann on turn · Round 3')
  })

  it("names the opponent when it is the opponent's turn", () => {
    render(<StateStrip party={party} encounter={{ ...ogre, current_turn: 1 }} />)

    expect(screen.getByText(/Round 3/).textContent).toBe('Ogre on turn · Round 3')
  })

  it('shows one chip per character with name and hit points', () => {
    render(<StateStrip party={party} encounter={ogre} />)

    expect(chips().map((chip) => chip.textContent)).toEqual(['Brann17/28 +5', 'Mira0/9'])
  })

  it('marks the acting character and sets apart one at 0 hit points', () => {
    render(<StateStrip party={party} encounter={ogre} />)

    const [brann, mira] = chips()
    expect(brann.getAttribute('aria-current')).toBe('true')
    expect(mira.hasAttribute('aria-current')).toBe(false)
    expect(mira.classList).toContain('down')
  })

  it('shows the party alone outside an encounter', () => {
    render(<StateStrip party={party} encounter={null} />)

    expect(screen.queryByText(/Round/)).toBeNull()
    expect(chips()).toHaveLength(2)
  })
})
