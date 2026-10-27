import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { Narration } from './Narration.tsx'
import type { Turn } from './stream/tableState.ts'

function turn(narration: string): Turn {
  return {
    id: 't1',
    action: { text: 'I open the door', character_id: null },
    narration,
    finished: false,
  }
}

// jsdom lays nothing out. The pane is given a size, and its content a height
// that grows with the narration, so scrolling can be measured.
function renderPane() {
  const view = render(<Narration turns={[turn('The door')]} party={[]} />)
  const pane = screen.getByRole('region', { name: 'Narration' })
  let contentHeight = 1000
  Object.defineProperty(pane, 'clientHeight', { value: 400 })
  Object.defineProperty(pane, 'scrollHeight', { get: () => contentHeight })

  function narrate(narration: string, height: number) {
    contentHeight = height
    view.rerender(<Narration turns={[turn(narration)]} party={[]} />)
  }
  function scrollTo(top: number) {
    pane.scrollTop = top
    fireEvent.scroll(pane)
  }
  return { pane, narrate, scrollTo }
}

describe('Narration', () => {
  it('follows new text while the reader is at its end', () => {
    const { pane, narrate, scrollTo } = renderPane()
    scrollTo(600)

    narrate('The door creaks open', 1200)

    expect(pane.scrollTop).toBe(1200)
  })

  it('does not jump while the reader has scrolled up', () => {
    const { pane, narrate, scrollTo } = renderPane()
    scrollTo(200)

    narrate('The door creaks open', 1200)

    expect(pane.scrollTop).toBe(200)
  })

  it('follows again once the reader is back at the end', () => {
    const { pane, narrate, scrollTo } = renderPane()
    scrollTo(200)
    scrollTo(600)

    narrate('The door creaks open', 1200)

    expect(pane.scrollTop).toBe(1200)
  })
})
