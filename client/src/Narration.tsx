import { useLayoutEffect, useRef } from 'react'

import type { Character } from './contract/index.ts'
import type { Turn } from './stream/tableState.ts'

interface Props {
  turns: Turn[]
  party: Character[]
}

// How close to the end, in pixels, still counts as reading at the end. A
// little slack absorbs rounding; a turn of the mouse wheel is well beyond it.
const AT_END = 16

// The story so far. It follows new text while the reader is at its end, and
// stays where it is while the reader has scrolled up to read something again.
export function Narration({ turns, party }: Props) {
  const pane = useRef<HTMLElement>(null)
  const following = useRef(true)

  function noteWhereTheReaderIs() {
    const el = pane.current
    if (el) following.current = el.scrollHeight - el.scrollTop - el.clientHeight <= AT_END
  }

  useLayoutEffect(() => {
    const el = pane.current
    if (el && following.current) el.scrollTop = el.scrollHeight
  }, [turns])

  return (
    <section
      ref={pane}
      className="narration"
      aria-label="Narration"
      aria-live="polite"
      onScroll={noteWhereTheReaderIs}
    >
      {turns.length === 0 && <p className="empty">The story begins with what you do.</p>}
      {turns.map((turn) => {
        const speaker = party.find((c) => c.id === turn.action.character_id)
        return (
          <article key={turn.id}>
            <p className="declared">
              {speaker ? `${speaker.name}: ` : ''}
              {turn.action.text}
            </p>
            <p className="told">{turn.narration}</p>
          </article>
        )
      })}
    </section>
  )
}
