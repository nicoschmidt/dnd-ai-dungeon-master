import { type FormEvent, type KeyboardEvent, useRef, useState } from 'react'

import type { Character, DeclaredAction, Encounter } from './contract/index.ts'
import { actingCharacterId } from './stream/tableState.ts'

interface Props {
  party: Character[]
  encounter: Encounter | null
  busy: boolean
  onDeclare: (action: DeclaredAction) => Promise<boolean>
}

const NEXT_KEYS = ['ArrowRight', 'ArrowDown']
const PREVIOUS_KEYS = ['ArrowLeft', 'ArrowUp']

// The one input of the table: a declared action and the dice rolled for it,
// sent with the acting character. Whoever's turn it is is preselected and
// marked; the table can pick someone else, or nobody.
export function ActionForm({ party, encounter, busy, onDeclare }: Props) {
  const acting = actingCharacterId(encounter)
  const [text, setText] = useState('')
  const [selection, setSelection] = useState({ acting, chosen: acting ?? '' })
  const actorButtons = useRef<(HTMLButtonElement | null)[]>([])

  // A new turn preselects its character, replacing whatever was picked before.
  if (selection.acting !== acting) {
    setSelection({ acting, chosen: acting ?? '' })
  }
  const chosen = party.some((c) => c.id === selection.chosen) ? selection.chosen : ''

  // '' is the whole table: an action nobody in particular declares.
  const actors = [{ id: '', name: 'The table' }, ...party]

  async function declare(event?: FormEvent) {
    event?.preventDefault()
    const action: DeclaredAction = { text: text.trim(), character_id: chosen || null }
    if (!action.text || busy) return
    if (await onDeclare(action)) setText('')
  }

  // Enter declares, Shift+Enter adds a line. Not while an input method is
  // still composing a character: that Enter belongs to it.
  function onTextKey(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault()
      void declare()
    }
  }

  // The arrow keys move the choice within the group, as in any radio group.
  function onActorKey(event: KeyboardEvent<HTMLButtonElement>, index: number) {
    const step = NEXT_KEYS.includes(event.key) ? 1 : PREVIOUS_KEYS.includes(event.key) ? -1 : 0
    if (step === 0) return
    event.preventDefault()
    const next = (index + step + actors.length) % actors.length
    setSelection({ acting, chosen: actors[next].id })
    actorButtons.current[next]?.focus()
  }

  return (
    <form className="action" aria-label="Declare an action" onSubmit={declare}>
      <div className="column">
        <div className="actors" role="radiogroup" aria-labelledby="actors-label">
          <span id="actors-label" className="label">
            Who acts?
          </span>
          {actors.map(({ id, name }, index) => (
            <button
              key={id}
              ref={(button) => {
                actorButtons.current[index] = button
              }}
              type="button"
              role="radio"
              aria-checked={id === chosen}
              tabIndex={id === chosen ? 0 : -1}
              onClick={() => setSelection({ acting, chosen: id })}
              onKeyDown={(event) => onActorKey(event, index)}
            >
              {name}
              {id !== '' && id === acting && (
                <>
                  {' '}
                  <span className="tag">on turn</span>
                </>
              )}
            </button>
          ))}
        </div>
        <div className="entry">
          <textarea
            rows={2}
            aria-label="Declared action"
            aria-describedby="action-hint"
            placeholder="What do you do? Include what you rolled."
            value={text}
            onChange={(event) => setText(event.target.value)}
            onKeyDown={onTextKey}
          />
          <button type="submit" className="primary" disabled={busy || !text.trim()}>
            Declare
          </button>
        </div>
        <p id="action-hint" className="hint">
          Enter declares · Shift+Enter for a new line
        </p>
      </div>
    </form>
  )
}
