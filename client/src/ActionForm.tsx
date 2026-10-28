import { type FormEvent, type KeyboardEvent, useRef, useState } from 'react'

import type { Character, DeclaredAction, Encounter } from './contract/index.ts'
import { DiceBlock } from './dice/DiceBlock.tsx'
import { appendLine } from './dice/dice.ts'
import { useStrings } from './language/strings.ts'
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
  const t = useStrings()
  const acting = actingCharacterId(encounter)
  const [text, setText] = useState('')
  const [selection, setSelection] = useState({ acting, chosen: acting ?? '' })
  const actorButtons = useRef<(HTMLButtonElement | null)[]>([])
  const textField = useRef<HTMLTextAreaElement>(null)

  // A new turn preselects its character, replacing whatever was picked before.
  if (selection.acting !== acting) {
    setSelection({ acting, chosen: acting ?? '' })
  }
  const chosen = party.some((c) => c.id === selection.chosen) ? selection.chosen : ''

  // '' is the whole table: an action nobody in particular declares.
  const actors = [{ id: '', name: t.action.table }, ...party]

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

  // A roll from the dice block joins the text, on a line of its own, and the
  // text field takes the focus so it can be changed or declared.
  function addRoll(line: string) {
    setText((current) => appendLine(current, line))
    textField.current?.focus()
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
    <form className="action" aria-label={t.action.form} onSubmit={declare}>
      <div className="column">
        <div className="actors" role="radiogroup" aria-labelledby="actors-label">
          <span id="actors-label" className="label">
            {t.action.whoActs}
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
                  <span className="tag">{t.state.onTurn}</span>
                </>
              )}
            </button>
          ))}
        </div>
        <div className="entry">
          <div className="compose">
            <textarea
              ref={textField}
              rows={2}
              aria-label={t.action.field}
              aria-describedby="action-hint"
              placeholder={t.action.placeholder}
              value={text}
              onChange={(event) => setText(event.target.value)}
              onKeyDown={onTextKey}
            />
            <button type="submit" className="primary" disabled={busy || !text.trim()}>
              {t.action.declare}
            </button>
          </div>
          {/* A roll belongs to whoever acts: a new choice starts the block afresh. */}
          <DiceBlock key={chosen} disabled={chosen === ''} onLine={addRoll} />
        </div>
        <p id="action-hint" className="hint">
          {t.action.hint}
        </p>
      </div>
    </form>
  )
}
