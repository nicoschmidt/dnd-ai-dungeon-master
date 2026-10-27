import { type FormEvent, useState } from 'react'

import type { Character, DeclaredAction, Encounter } from './contract/index.ts'
import { actingCharacterId } from './stream/tableState.ts'

interface Props {
  party: Character[]
  encounter: Encounter | null
  busy: boolean
  onDeclare: (action: DeclaredAction) => Promise<boolean>
}

// The one input of the table: a declared action and the dice rolled for it,
// sent with the acting character. Whoever's turn it is is preselected and
// marked; the table can pick someone else, or nobody.
export function ActionForm({ party, encounter, busy, onDeclare }: Props) {
  const acting = actingCharacterId(encounter)
  const [text, setText] = useState('')
  const [selection, setSelection] = useState({ acting, chosen: acting ?? '' })

  // A new turn preselects its character, replacing whatever was picked before.
  if (selection.acting !== acting) {
    setSelection({ acting, chosen: acting ?? '' })
  }
  const chosen = party.some((c) => c.id === selection.chosen) ? selection.chosen : ''

  async function declare(event: FormEvent) {
    event.preventDefault()
    const action: DeclaredAction = { text: text.trim(), character_id: chosen || null }
    if (!action.text) return
    if (await onDeclare(action)) setText('')
  }

  // '' is the whole table: an action nobody in particular declares.
  const actors = [{ id: '', name: 'The table' }, ...party]

  return (
    <form className="action" onSubmit={declare}>
      <div className="actors" role="group" aria-label="Acting character">
        {actors.map(({ id, name }) => (
          <button
            key={id}
            type="button"
            aria-pressed={id === chosen}
            aria-current={id !== '' && id === acting ? 'true' : undefined}
            onClick={() => setSelection({ acting, chosen: id })}
          >
            {name}
          </button>
        ))}
      </div>
      <div className="declare">
        <input
          aria-label="Declared action"
          placeholder="What do you do? Include what you rolled."
          value={text}
          onChange={(event) => setText(event.target.value)}
        />
        <button type="submit" disabled={busy || !text.trim()}>
          Declare
        </button>
      </div>
    </form>
  )
}
