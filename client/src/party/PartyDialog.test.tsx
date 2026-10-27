import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { PartyDialog } from './PartyDialog.tsx'

describe('PartyDialog', () => {
  it('opens the party form as a dialog', () => {
    render(<PartyDialog party={[]} onClose={vi.fn()} />)

    const dialog = screen.getByRole('dialog', { name: 'The party' })
    expect((dialog as HTMLDialogElement).open).toBe(true)
    expect(screen.getByRole('button', { name: 'Save the party' })).toBeTruthy()
  })

  it('validates the party as the form does, and stays open', () => {
    const onClose = vi.fn()
    render(<PartyDialog party={[]} onClose={onClose} />)

    fireEvent.click(screen.getByRole('button', { name: 'Save the party' }))

    expect(screen.getAllByText(/./, { selector: '.error' }).length).toBeGreaterThan(0)
    expect(onClose).not.toHaveBeenCalled()
  })

  it('closes on Cancel, and when the browser closes it on Escape', () => {
    const onClose = vi.fn()
    render(<PartyDialog party={[]} onClose={onClose} />)

    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))
    fireEvent(screen.getByRole('dialog'), new Event('close'))

    expect(onClose).toHaveBeenCalledTimes(2)
  })
})
