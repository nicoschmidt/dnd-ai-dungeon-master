import { fireEvent, render, screen } from '@testing-library/react'
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

function chosen(): string {
  return (screen.getByLabelText('Acting character') as HTMLSelectElement).value
}

describe('ActionForm', () => {
  it('preselects the character whose turn it is', () => {
    renderForm(turnOf(2))

    expect(chosen()).toBe('mira')
  })

  it("preselects nobody on the opponent's turn or outside an encounter", () => {
    const { rerender } = renderForm(turnOf(1))
    expect(chosen()).toBe('')

    rerender(<ActionForm party={party} encounter={null} busy={false} onDeclare={vi.fn()} />)
    expect(chosen()).toBe('')
  })

  it('moves the preselection when the turn passes', () => {
    const { rerender, onDeclare } = renderForm(turnOf(0))
    expect(chosen()).toBe('brann')

    rerender(<ActionForm party={party} encounter={turnOf(2)} busy={false} onDeclare={onDeclare} />)
    expect(chosen()).toBe('mira')
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

    fireEvent.change(screen.getByLabelText('Acting character'), { target: { value: 'mira' } })
    fireEvent.change(screen.getByLabelText('Declared action'), { target: { value: 'I help' } })
    fireEvent.submit(screen.getByLabelText('Declared action'))

    await vi.waitFor(() => expect(onDeclare).toHaveBeenCalled())
    expect(onDeclare.mock.calls[0][0].character_id).toBe('mira')
  })
})
