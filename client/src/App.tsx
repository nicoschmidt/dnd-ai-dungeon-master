import { type FormEvent, useState } from 'react'

import type { DeclaredAction } from './contract/index.ts'
import { type Connection, useTableStream } from './stream/useTableStream.ts'

const CONNECTION_LABEL: Record<Connection, string> = {
  connecting: 'connecting…',
  open: 'connected',
  reconnecting: 'connection lost, reconnecting…',
  closed: 'disconnected — reload the page',
}

function App() {
  const { state, connection } = useTableStream()
  const [text, setText] = useState('')
  const [sendError, setSendError] = useState<string | null>(null)

  async function declare(event: FormEvent) {
    event.preventDefault()
    const action: DeclaredAction = { text: text.trim(), character_id: null }
    if (!action.text) return

    const response = await fetch('/api/session/actions', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(action),
    }).catch(() => null)

    if (response?.status === 202) {
      setText('')
      setSendError(null)
    } else if (response?.status === 409) {
      setSendError('The dungeon master is still answering the last action.')
    } else {
      setSendError('The action did not reach the dungeon master. Try again.')
    }
  }

  return (
    <main>
      <header>
        <h1>AI Dungeon Master</h1>
        <p className="connection">{CONNECTION_LABEL[connection]}</p>
      </header>

      <section className="narration" aria-label="Narration" aria-live="polite">
        {state.turns.map((turn) => (
          <article key={turn.id}>
            <p className="declared">{turn.action.text}</p>
            <p>{turn.narration}</p>
          </article>
        ))}
      </section>

      {state.error && <p role="alert">{state.error.message}</p>}
      {sendError && <p role="alert">{sendError}</p>}

      <form onSubmit={declare}>
        <input
          aria-label="Declared action"
          placeholder="What do you do? Include what you rolled."
          value={text}
          onChange={(event) => setText(event.target.value)}
        />
        <button type="submit" disabled={state.busy || !text.trim()}>
          Declare
        </button>
      </form>
    </main>
  )
}

export default App
