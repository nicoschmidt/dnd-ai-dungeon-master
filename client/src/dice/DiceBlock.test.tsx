import { fireEvent, render, screen, within } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { DiceBlock } from './DiceBlock.tsx'

function renderBlock(roll = vi.fn((sides: number) => sides)) {
  const onLine = vi.fn()
  render(<DiceBlock disabled={false} onLine={onLine} roll={roll} />)
  return { onLine, roll }
}

function block() {
  return within(screen.getByRole('group', { name: 'Dice' }))
}

function click(name: string) {
  fireEvent.click(block().getByRole('button', { name }))
}

function buttonNames(): string[] {
  return block()
    .getAllByRole('button')
    .map((button) => button.getAttribute('aria-label') ?? button.textContent ?? '')
}

describe('DiceBlock', () => {
  it('offers the dice from d4 to d20', () => {
    renderBlock()

    expect(buttonNames()).toEqual(['d4', 'd6', 'd8', 'd10', 'd12', 'd20'])
  })

  it('shows the faces of the chosen die, a roll button and a way back', () => {
    renderBlock()

    click('d6')

    expect(buttonNames()).toEqual(['Back to the dice', '1', '2', '3', '4', '5', '6', 'Roll'])
    expect(document.activeElement?.textContent).toBe('1')
  })

  it('goes from the face to the modifiers, from −5 to +15', () => {
    renderBlock()

    click('d20')
    click('14')

    expect(block().getByText('d20: 14 · modifier?')).toBeTruthy()
    const names = buttonNames()
    expect(names[0]).toBe('Back to the faces')
    expect(names.slice(1)).toHaveLength(21)
    expect([names[1], names.at(-1)]).toEqual(['−5', '+15'])
    expect(document.activeElement?.textContent).toBe('+0')
  })

  it('hands over the line and starts again at the dice', () => {
    const { onLine } = renderBlock()

    click('d20')
    click('14')
    click('+5')

    expect(onLine).toHaveBeenCalledWith('d20: 14 + 5 = 19')
    expect(buttonNames()).toEqual(['d4', 'd6', 'd8', 'd10', 'd12', 'd20'])
  })

  it('makes the line for a negative modifier and for +0', () => {
    const { onLine } = renderBlock()

    click('d20')
    click('14')
    click('−1')
    click('d8')
    click('6')
    click('+0')

    expect(onLine.mock.calls).toEqual([['d20: 14 − 1 = 13'], ['d8: 6']])
  })

  it('rolls the chosen die on the screen, and goes on as if the face had been clicked', () => {
    const roll = vi.fn().mockReturnValueOnce(1).mockReturnValueOnce(20)
    const { onLine } = renderBlock(roll)

    click('d20')
    click('Roll')
    expect(roll).toHaveBeenCalledWith(20)
    expect(block().getByText('d20: 1 · modifier?')).toBeTruthy()
    click('+3')

    click('d20')
    click('Roll')
    click('+0')

    expect(onLine.mock.calls).toEqual([['d20: 1 + 3 = 4'], ['d20: 20']])
  })

  it('steps back with the back buttons', () => {
    renderBlock()

    click('d12')
    click('7')
    click('Back to the faces')
    expect(block().getByText('d12: what came up?')).toBeTruthy()

    click('Back to the dice')
    expect(buttonNames()).toEqual(['d4', 'd6', 'd8', 'd10', 'd12', 'd20'])
    expect(document.activeElement?.getAttribute('aria-label')).toBe('d12')
  })

  it('steps back with Escape', () => {
    renderBlock()

    click('d10')
    click('3')
    fireEvent.keyDown(document.activeElement!, { key: 'Escape' })
    expect(block().getByText('d10: what came up?')).toBeTruthy()
    fireEvent.keyDown(document.activeElement!, { key: 'Escape' })

    expect(buttonNames()).toEqual(['d4', 'd6', 'd8', 'd10', 'd12', 'd20'])
  })

  it('takes no focus when it first appears', () => {
    renderBlock()

    expect(document.activeElement).toBe(document.body)
  })

  it('cannot be used while disabled', () => {
    render(<DiceBlock disabled onLine={vi.fn()} />)

    for (const button of block().getAllByRole('button')) {
      expect((button as HTMLButtonElement).disabled).toBe(true)
    }
  })
})
