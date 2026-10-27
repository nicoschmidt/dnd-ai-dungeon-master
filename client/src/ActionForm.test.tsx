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

function actors() {
  return within(screen.getByRole('radiogroup', { name: 'Who acts?' })).getAllByRole('radio')
}

// The name on the checked radio, without its tag: who the action is sent with.
function chosen(): string {
  const checked = actors().find((radio) => radio.getAttribute('aria-checked') === 'true')
  return checked?.firstChild?.textContent ?? ''
}

function markedAsTheirTurn(): string[] {
  return actors()
    .filter((radio) => within(radio).queryByText('on turn'))
    .map((radio) => radio.firstChild?.textContent ?? '')
}

function actor(name: string): HTMLElement {
  return actors().find((radio) => radio.firstChild?.textContent === name)!
}

function type(text: string) {
  fireEvent.change(screen.getByLabelText('Declared action'), { target: { value: text } })
}

describe('ActionForm', () => {
  it('preselects the character whose turn it is', () => {
    renderForm(turnOf(2))

    expect(chosen()).toBe('Mira')
  })

  it('offers one choice per character and one for the whole table', () => {
    renderForm(null)

    expect(actors().map((radio) => radio.textContent)).toEqual(['The table', 'Brann', 'Mira'])
  })

  it('marks the character whose turn it is, also when the table picks someone else', () => {
    renderForm(turnOf(0))
    expect(markedAsTheirTurn()).toEqual(['Brann'])

    fireEvent.click(actor('Mira'))
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

  it('moves the choice with the arrow keys, as a radio group does', () => {
    renderForm(turnOf(0))

    fireEvent.keyDown(actor('Brann'), { key: 'ArrowRight' })
    expect(chosen()).toBe('Mira')
    expect(document.activeElement).toBe(actor('Mira'))

    fireEvent.keyDown(actor('Mira'), { key: 'ArrowRight' })
    expect(chosen()).toBe('The table')
  })

  it('lets only the chosen one be reached with Tab', () => {
    renderForm(turnOf(2))

    expect(actors().map((radio) => radio.tabIndex)).toEqual([-1, -1, 0])
  })

  it('sends the acting character with the declared action', async () => {
    const { onDeclare } = renderForm(turnOf(0))

    type('I attack the ogre, 17')
    fireEvent.submit(screen.getByLabelText('Declared action'))

    await vi.waitFor(() => expect(onDeclare).toHaveBeenCalled())
    expect(onDeclare.mock.calls[0][0]).toEqual<DeclaredAction>({
      text: 'I attack the ogre, 17',
      character_id: 'brann',
    })
  })

  it('lets the table pick someone else', async () => {
    const { onDeclare } = renderForm(turnOf(0))

    fireEvent.click(actor('Mira'))
    type('I help')
    fireEvent.submit(screen.getByLabelText('Declared action'))

    await vi.waitFor(() => expect(onDeclare).toHaveBeenCalled())
    expect(onDeclare.mock.calls[0][0].character_id).toBe('mira')
  })

  it('declares on Enter', async () => {
    const { onDeclare } = renderForm(turnOf(0))

    type('I attack the ogre, 17')
    fireEvent.keyDown(screen.getByLabelText('Declared action'), { key: 'Enter' })

    await vi.waitFor(() => expect(onDeclare).toHaveBeenCalled())
    expect(onDeclare.mock.calls[0][0].text).toBe('I attack the ogre, 17')
  })

  it('does not declare on Shift+Enter, which adds a line', () => {
    const { onDeclare } = renderForm(turnOf(0))

    type('I attack the ogre')
    const kept = fireEvent.keyDown(screen.getByLabelText('Declared action'), {
      key: 'Enter',
      shiftKey: true,
    })

    expect(kept).toBe(true)
    expect(onDeclare).not.toHaveBeenCalled()
  })

  it('appends a roll from the dice block to the text, and focuses the text', () => {
    renderForm(turnOf(0))
    const field = screen.getByLabelText('Declared action') as HTMLTextAreaElement
    type('I attack the ogre.')

    const dice = within(screen.getByRole('group', { name: 'Dice' }))
    fireEvent.click(dice.getByRole('button', { name: 'd20' }))
    fireEvent.click(dice.getByRole('button', { name: '14' }))
    fireEvent.click(dice.getByRole('button', { name: '+5' }))

    expect(field.value).toBe('I attack the ogre.\nd20: 14 + 5 = 19')
    expect(document.activeElement).toBe(field)
  })

  it('declares the roll only on Declare', async () => {
    const { onDeclare } = renderForm(turnOf(0))

    const dice = within(screen.getByRole('group', { name: 'Dice' }))
    fireEvent.click(dice.getByRole('button', { name: 'd20' }))
    fireEvent.click(dice.getByRole('button', { name: '17' }))
    fireEvent.click(dice.getByRole('button', { name: '+2' }))
    expect(onDeclare).not.toHaveBeenCalled()

    fireEvent.submit(screen.getByLabelText('Declared action'))
    await vi.waitFor(() => expect(onDeclare).toHaveBeenCalled())
    expect(onDeclare.mock.calls[0][0]).toEqual<DeclaredAction>({
      text: 'd20: 17 + 2 = 19',
      character_id: 'brann',
    })
  })

  it('offers the dice to a chosen character before the turn order is fixed', () => {
    renderForm({ ...turnOf(0), round: 0, current_turn: null })

    fireEvent.click(actor('Mira'))

    const d20 = within(screen.getByRole('group', { name: 'Dice' })).getByRole('button', {
      name: 'd20',
    })
    expect((d20 as HTMLButtonElement).disabled).toBe(false)
  })

  it('disables the dice for the whole table', () => {
    renderForm(turnOf(1))

    const dice = within(screen.getByRole('group', { name: 'Dice' })).getAllByRole('button')
    expect(dice.every((button) => (button as HTMLButtonElement).disabled)).toBe(true)
  })

  it('starts the dice afresh when someone else is chosen', () => {
    renderForm(turnOf(0))

    const dice = () => within(screen.getByRole('group', { name: 'Dice' }))
    fireEvent.click(dice().getByRole('button', { name: 'd20' }))
    fireEvent.click(actor('Mira'))

    expect(dice().getByRole('button', { name: 'd20' })).toBeTruthy()
    expect(dice().queryByRole('button', { name: '14' })).toBeNull()
  })

  it('does not declare on Enter while the dungeon master is still answering', () => {
    const onDeclare = vi.fn(async () => true)
    render(<ActionForm party={party} encounter={turnOf(0)} busy onDeclare={onDeclare} />)

    type('I attack again')
    fireEvent.keyDown(screen.getByLabelText('Declared action'), { key: 'Enter' })

    expect(onDeclare).not.toHaveBeenCalled()
  })
})
