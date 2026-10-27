import { fireEvent, render, screen, within } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { ActionForm } from './ActionForm.tsx'
import type { Character, DeclaredAction, Encounter } from './contract/index.ts'

const party: Character[] = ['Brann', 'Mira'].map((name) => ({
  id: name.toLowerCase(),
  name,
  character_class: 'Fighter',
  level: 1,
  armour_class: 15,
  max_hit_points: 10,
  current_hit_points: 10,
  temporary_hit_points: 0,
  conditions: [],
}))

function turnOf(current: number): Encounter {
  return {
    opponent_name: 'Ogre',
    round: 1,
    turn_order: [
      { kind: 'character', id: 'brann', name: 'Brann' },
      { kind: 'opponent', id: 'ogre', name: 'Ogre' },
      { kind: 'character', id: 'mira', name: 'Mira' },
    ],
    current_turn: current,
    outcome: null,
  }
}

function renderForm(
  encounter: Encounter | null,
  onDeclare = vi.fn(async (_action: DeclaredAction) => true),
) {
  const view = render(
    <ActionForm party={party} encounter={encounter} busy={false} onDeclare={onDeclare} />,
  )
  return { ...view, onDeclare }
}

// The name on the pressed button: the character the action will be sent with.
function chosen(): string {
  const actors = within(screen.getByRole('group', { name: 'Acting character' }))
  return actors.getByRole('button', { pressed: true }).textContent ?? ''
}

function markedAsTheirTurn(): string[] {
  return screen
    .getAllByRole('button')
    .filter((button) => button.getAttribute('aria-current') === 'true')
    .map((button) => button.textContent ?? '')
}

describe('ActionForm', () => {
  it('preselects the character whose turn it is', () => {
    renderForm(turnOf(2))

    expect(chosen()).toBe('Mira')
  })

  it('offers one button per character and one for the whole table', () => {
    renderForm(null)

    const actors = within(screen.getByRole('group', { name: 'Acting character' }))
    expect(actors.getAllByRole('button').map((b) => b.textContent)).toEqual([
      'The table',
      'Brann',
      'Mira',
    ])
  })

  it('marks the character whose turn it is, also when the table picks someone else', () => {
    renderForm(turnOf(0))
    expect(markedAsTheirTurn()).toEqual(['Brann'])

    fireEvent.click(screen.getByRole('button', { name: 'Mira' }))
    expect(chosen()).toBe('Mira')
    expect(markedAsTheirTurn()).toEqual(['Brann'])
  })

  it("preselects nobody on the opponent's turn or outside an encounter", () => {
    const { rerender } = renderForm(turnOf(1))
    expect(chosen()).toBe('The table')
    expect(markedAsTheirTurn()).toEqual([])

    rerender(<ActionForm party={party} encounter={null} busy={false} onDeclare={vi.fn()} />)
    expect(chosen()).toBe('The table')
  })

  it('moves the preselection when the turn passes', () => {
    const { rerender, onDeclare } = renderForm(turnOf(0))
    expect(chosen()).toBe('Brann')

    rerender(<ActionForm party={party} encounter={turnOf(2)} busy={false} onDeclare={onDeclare} />)
    expect(chosen()).toBe('Mira')
  })

  it('sends the acting character with the declared action', async () => {
    const { onDeclare } = renderForm(turnOf(0))

    fireEvent.change(screen.getByLabelText('Declared action'), {
      target: { value: 'I attack the ogre, 17' },
    })
    fireEvent.submit(screen.getByLabelText('Declared action'))

    await vi.waitFor(() => expect(onDeclare).toHaveBeenCalled())
    expect(onDeclare.mock.calls[0][0]).toEqual<DeclaredAction>({
      text: 'I attack the ogre, 17',
      character_id: 'brann',
    })
  })

  it('lets the table pick someone else', async () => {
    const { onDeclare } = renderForm(turnOf(0))

    fireEvent.click(screen.getByRole('button', { name: 'Mira' }))
    fireEvent.change(screen.getByLabelText('Declared action'), { target: { value: 'I help' } })
    fireEvent.submit(screen.getByLabelText('Declared action'))

    await vi.waitFor(() => expect(onDeclare).toHaveBeenCalled())
    expect(onDeclare.mock.calls[0][0].character_id).toBe('mira')
  })
})
